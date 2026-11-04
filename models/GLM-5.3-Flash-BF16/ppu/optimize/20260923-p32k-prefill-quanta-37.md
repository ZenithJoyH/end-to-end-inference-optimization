# 20260923-p32k-prefill-quanta-37：固定 MBT 的长 Prefill 调度

- 状态：`incomplete_reverted`；分类：`framework`；父场景：`p32768-d1024-c64-n128`。
- 单变量：保持 MBT32768、TP16/BF16、max-seqs64、graph、前缀缓存和源码组合不变，仅把现行 vLLM `--long-prefill-token-threshold` 从 0 改为 8192；若首探针提供方向但未通过，再按预冻结顺序测 4096，不追逐任意阈值。

## 证据与假设

当前 vLLM 0.24.0 调度源码在 running/waiting 两条路径均用该阈值限制每请求每迭代的 Prefill token，不需要改 vLLM 源码。P32K 旧 trace 有 63 个逐请求准入 Mixed 波；用户最新长 prompt 测试中 Prefill 活跃时 Decode 10 秒窗口输出速率由约 1000–1500 降至 10–18 tok/s，P16K/P32K P99 ITL 均超 3 秒。限制单步长 Prefill 可能缩短 Decode 空窗，但会增加调度/launch 波数，可能降低总吞吐和恶化 TTFT；均待测。

2026-09-23 运行源码只读核对：当前 `vllm/config/scheduler.py` 的默认 `long_prefill_token_threshold=0`、`enable_chunked_prefill=True`，默认 `max_num_partial_prefills=1`；`v1/core/sched/scheduler.py` 在 running 与 waiting 请求路径均以 `0 < threshold < num_new_tokens` 限制本次 token 数。该参数不会限制单 token Decode；但默认只允许 1 个部分 Prefill 并行，因此不能从阈值本身推断更高总吞吐，仍必须测 Mixed 队列和 ITL。

## 测试契约与停止条件

- 首个快速证伪里程碑（先于下列 D128）：`P32768/D32/C64/N64`、finite-batch、`/v1/completions`、seed42、temperature0、ignore EOS、2 轮预热+2 轮测量、每轮 timeout 3600 s。阶段为 Mixed，目标父场景仍是 `P32768/D1024/C64/N128`；相对正式场景只缩短输出、减少请求数，不能以本探针关闭 P32K。各臂独立服务、同一 workload 与 seed，预热末两轮 output throughput relative spread ≤5%，测量两轮 spread ≤5%，baseline→revert drift ≤3%，64/64 请求每轮有效。主指标 P99 ITL 降低至少 20%，输出吞吐退化不超过 3%，P99 TTFT 恶化不超过 20%；不达主目标或任一守护失败即回退并停止该阈值。若探针达标，再晋级下述 D128 `targeted`，不能把探针结果当最终收益。
- 性能 Skill `targeted`：同一 `P32768/D128/C64/N128` Mixed milestone 的 threshold0→8192→0 配对；若预冻结首探针方向成立但未达标，另立独立 0→4096→0，不与算子改动合并归因。
- 主目标：P99 ITL 降低至少 20%；守护：输出吞吐下降不得超过 3%，TTFT 恶化不得超过 20%，128/128 请求成功且预热稳态准入通过。TPOT、KV 压力、等待/运行队列和实际 chunk shape 同时报告。D128 成功仅能晋级 D1024 正式父场景，不构成完整验收。
- 每轮最小正确性回归、graph capture/两次 replay、C1/C8 与返回内容检查；源码不变但配置变化使旧正式精度 gate 不能自动用于正式性能。
- 最终结果：首个 D32 探针的候选未通过预冻结稳态准入，缺少 measured round，端到端比较为 `incomplete`；阈值8192不保留。远程命令目录为 `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/commands/p32k-prefill-quanta-37-20260923`。

## point36 后的实施准备

点36 的原 Plugin 路由已按 SHA `a923d10ac1899ea76ee9ff7871383d05e71e758cd076aadc421e75ef17f483ba` 回退；其 P32K/D128 A/B/R 结果 `failed`，不是本点的基线。2026-09-23 只读预检确认目标 `PPU-13` 优化容器服务 running/waiting 均 0、源码仍为原 SHA，远端案例根规范路径为 `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911`、root:root、`drwxr-xr-x`，本点独立命令目录尚不存在。源适配容器不改动。实际运行前按下列受控顺序：

1. 仅在该案例根下用 Ansible 创建 `commands/p32k-prefill-quanta-37-20260923/` 和 `full-scenarios/p32768-d1024-c64-n128/framework/p32k-prefill-quanta-37/probe/`；复制已在本地通过 `bash -n`/JSON/比较契约 parser 校验的 `plan.json`、`comparison.json`、`launch-inside.sh`、`launch.sh`、`build-manifest.py`、`capture.sh`、`run.sh`、`compare.sh`、`sanity.sh`，逐项核 SHA 后执行。原始结果、日志和命令留在这个远端实验目录，本地只记录摘要/SHA。
2. 当前回退服务已空闲，调用点36 保存的 `stop-service.sh` 精确停止优化容器服务；源码保持原 SHA。启动独立 threshold0 baseline 服务，确认 graph 就绪，抓运行身份/关闭前缀缓存和编译缓存证据；先检查 dry-run，再执行 2+2 探针。
3. 仅在 baseline 原生有效后安全停服，启动 threshold8192 candidate；C1/C8 最小回归按精度 Skill 开/停 heartbeat 并保留原生结果，再抓身份、dry-run、执行同 workload。最后 threshold0 revert 同法测量，用同套 runner 的比较器形成三态结论。任何服务异常、warmup 不稳或语义回归均先停止并恢复 threshold0；不把诊断探针结果充作 D128/D1024 验收。

此前 `vllm serve --help=all` 在本容器确认 `--long-prefill-token-threshold` 存在。启动脚本对三臂均显式传入该参数，除 0/8192 值外保持 TP16、BF16、maxseq64、MBT32768、graph FULL_DECODE_ONLY、prefix caching 关闭和 Plugin/FlagGems 源码身份一致。原有项目文档中的 threshold0 默认值在本点被显式化，避免隐式默认漂移。

上述独立命令/证据目录经 Ansible `file --check --diff` 预览后创建。远端执行副本均与本地 SHA-256 一致，`bash -n`、Python AST、JSON 解析通过：`plan.json` `86d4a8b628b3e62557ef105e156c0498c981d122195a10ac04af472c57aec1a6`；`comparison.json` `b8fe235d866c1dfac3bccfd8ab86442a83e3920c7f194beab674e73a5bc0a686`；`launch-inside.sh` `1f955e41594f34ec3f46d38f4a7ae910b98625e7cadee4c3cef1ed36986eace3`；`launch.sh` `28df66cce34b45b78304e7466024dc54ac50207e9a81d78e88706a5696daf842`；`build-manifest.py` `251bbc72f6fa63f47706a37473703f9e54ad2ab5a50bfc37b7e6567accdc8cc2`；`capture.sh` `65deb1b23f22a9ea9b944e6dc97c14d1d7ab43e0b767c12acbbfb66c3400cadc`；`run.sh` `63db2adcc13fbd45cfa695fe33ff6d1298e6e012b96b03309e4f72274f29cc99`；`compare.sh` `f66405bcdfa7b8cd11d717ea1d15763d329e0ad635814442af6b32eea4425a68`；`sanity.sh` `cc6472a6573d143228b236804dd12620f028416f5ccda146b74fede2e47dcf47`。比较器使用与本次 runner 同套支持 `stage` 的版本，避免点36旧工具 schema 不匹配。

点36 回退服务 running/waiting 均 0 后，精确停止优化容器 PID 1855274，确认端口 8011 关闭；当前以原 Plugin SHA 启动本点 threshold0 baseline 服务，正在等待 graph/HTTP 就绪。尚未发送性能流量，结果仍是 `not_run`。

Baseline 服务已就绪，身份 `PPU-13:glm5.3-flash-opt-20260911:1868097:288097068`；运行证据 SHA `a59288e011463c897087b64a5e3337cf73a977d31ee6a8021ee747d51fe5a842`、manifest SHA `8e52ba51bfc5f2aa3f41833dd90846d0e1e3f1bf57a82b9a5c332fcffc4f36f4`，含显式 threshold0、MBT32768、maxseq64、graph FULL_DECODE_ONLY、prefix cache disabled。原 Plugin 内容 SHA 与点36 revert 相同。维护版 runner dry-run 已核对 P32768/D32/C64/N64、2+2、seed391723–391726、plan/contract SHA，并保存 `probe/abr/baseline/dry-run.json`；`run.sh baseline execute` 正在运行，尚无有效性能数字。

本点 scheduler 语义边界补充最小正确性检查：性能 baseline 完成且服务空闲后，使用同一个已有 `/v1/completions` 接口对 8191/8192/8193 个明确 token ID 的 prompt 各发固定温度0、16输出的请求，保存 `usage.prompt_tokens`、输出和终止原因；候选服务同输入逐项比对，并用 C1/C8 检查普通 chat 行为。该探针只用于验证阈值 guard 两侧及服务 graph replay，非正式模型精度分数；执行脚本 `boundary.py` 将先保存到本点远端命令目录，SHA 核对后才运行，且不得与性能轮并发。

`commands/p32k-prefill-quanta-37-20260923/boundary.py` 已保存并通过 Python AST，SHA-256 `37fd7afc11d0c54ed1def2e507ddcf0978aae55635a6c2e3f8921638afa37b95`。输入 token pattern 来自当前 tokenizer 对“请回答：中国首都是哪里？”的实测编码；发送长度和 API `usage.prompt_tokens` 必须一致才认为跨阈值证据有效。

Threshold0 baseline 原生 `run-record.json` 状态 `complete`、SHA-256 `70aa7bdf77f3574c4436ea7a53397d7b88270e45e2fbf28b7888a3155d10dd4e`；2/2 预热有效，输出吞吐 8.833780/9.162018 tok/s，相对 spread 3.648%，满足 5% 准入。两轮正式测量 64/64 均有效，输出吞吐 9.159345/9.162076 tok/s，P99 ITL 3509.188/3511.054 ms，P99 TTFT 222553.725/222493.402 ms，P99 TPOT 3485.467/3485.246 ms；仅属于 D32 探针，不与 D128 历史数字直接比较。baseline 空闲时运行 `boundary.py`，8191/8192/8193 各自 API `usage.prompt_tokens` 精确等于发送 token ID 数、输出均 16 tokens/`finish_reason=length`；参考 `boundary.json` SHA-256 `80f202baf5a6df93b9500437a19f97a833df736b9387f128bb3ce08ad1081b2f`。本轮 `minimal-regression` 监控 `glm-p32k-prefill37-regression` 在执行前创建、结束后暂停，未发生首个 30 分钟 tick。

随后仅停止空闲优化容器服务 PID 1868097，确认 8011 关闭；使用同一启动脚本和原 Plugin SHA 启动 threshold8192 candidate。下一步待 graph/HTTP 就绪后先运行边界对照和 C1/C8，再抓取候选 manifest/dry-run/性能结果。候选目前无精度或性能结论。

Candidate 服务 graph/HTTP 就绪后重新激活同一 heartbeat `glm-p32k-prefill37-regression`；8191/8192/8193-token 边界逐项与 threshold0 输出/终止原因一致，结果 SHA `b35d4d1ebb78526b475c7d60f21118e4d11ee68783367bf42f8c4e60b7d84f4a`。初版 `sanity.sh` 因边界结果先创建 `accuracy/` 目录而在发送 C1/C8 请求前自检退出；其失败保留。新 `sanity-v2.sh` SHA `df41afa29914c640c3910495a40231081bcc87ba74cee7c6e30290ac51908a9c` 只检查目标文件不存在，不覆盖已有边界结果；C1 `1/1`、C8 `8/8` 均通过，原始结果 SHA 分别为 `245083bda574e0418c2b41a28b51fea028f4704de1b04695ee8ea35eb4fa5698`、`f871eae95690e818e48eb41f593ceec8d89cfc548a18241b96d6f6dbafc96131`。监控随后暂停。以上是 `minimal-regression`，不是正式 GPQA gate。

候选运行证据 SHA `020660085805c891b5d77e9bf70eec2024e8abbeaa096f454ae4f4c9d9b563a6`、manifest SHA `2c42ab7ccd1fc32fdaa31cc3afdd9661863d5c864c3ddfffd3a189fdb771d6e6`，显示当前服务 threshold8192、MBT32768、maxseq64、原 Plugin 内容 SHA、相同 launch script SHA、prefix cache disabled。baseline/candidate dry-run 的 effective plan、contract SHA、seed 和 4 轮配置完全相同。`run.sh candidate execute` 已启动，无性能结果前不判断收益。

候选原生 runner 在正式测量前按冻结的稳态准入停止：两轮预热均 64/64 有效，但输出吞吐 8.570092/9.589113 tok/s，相对 spread 11.223%，超过 5%。`run-record.json` SHA-256 `0a380cc3c0bad0582ef7603caae15a6733917b5a39dee6b802739b3bfb283862`、原生 `status=failed`、错误 `did not stabilize within the fixed warmup budget`；只有 2 个 warmup round，没有 measured round。第二轮的 9.589 tok/s/P99 ITL 3449 ms 仅作方向诊断，不能与 baseline 的正式轮计算候选收益，也不允许事后丢掉较慢首轮。按 Skill 比较判定，缺候选正式轮使点37的 A/B/R 结论为 `incomplete`；不运行原本需要三臂正式轮的比较器伪造结果。

冻结停止条件触发后确认 candidate running/waiting 均 0，仅停止优化容器 PID 1890285，确认 8011 关闭；以相同原 Plugin 源码、MBT32768 和显式 threshold0 启动 revert 服务，正在等待就绪。该阈值不保留，正式 D128/D1024 不晋级。下一步只核验回退服务身份、graph 和短回归，不对无效候选做收益宣称。

## 回退核验与最终决定

回退服务实例 `PPU-13:glm5.3-flash-opt-20260911:1939768:288368789` 已就绪，`/health` 通过，日志显示 `FULL_DECODE_ONLY` graph 11/11 capture 完成，8191/8192/8193-token 三次请求完成解码。运行证据 `probe/abr/revert/service/runtime-evidence.txt` SHA-256 `f8f0e8e0bf7ea38524549ef41f1bc7b68838be1189bb6aee9969a39ab89be8b6`；manifest SHA-256 `825b74673bbe8f6f862710374a0b79f391958580b55d55c524a492707872cad2`。其模型、engine、Plugin、FlagGems/FlagGems-vllm SHA、镜像谱系与挂载校验均和本点 baseline 一致；threshold0、MBT32768、maxseq64、关闭前缀缓存、graph 模式也逐项一致。回退边界输出与 baseline 逐项相同，原始 `probe/abr/revert/service/accuracy/boundary.json` SHA-256 `b82386d536185e4873a33ea5c1b0fd2b9076cef13237fd679d9c1fa111358287`。`minimal-regression` heartbeat `glm-p32k-prefill37-regression` 在实际请求前激活、完成后暂停；一次误建的同名 `-2` monitor 在执行前暂停，未用于报告。

本点判定 `incomplete_reverted`：候选语义边界和 C1/C8 通过，但候选两轮预热吞吐相对离散 11.223% 超出预冻结 5%，性能 runner 在 measured 前停止；没有候选正式轮或有效 A/B/R，不能声称阈值8192改善或恶化端到端。未改变契约、未丢弃较慢轮、未执行 D128/D1024，也没有签发新的正式精度 gate。回退后的服务继续运行 threshold0，点36的原 Plugin 路由保持恢复。下一轮若再次研究调度，应先解释稳态波动来源并重新预冻结完整 A/B/R 契约，不沿用这次 warmup 数字计算收益。
