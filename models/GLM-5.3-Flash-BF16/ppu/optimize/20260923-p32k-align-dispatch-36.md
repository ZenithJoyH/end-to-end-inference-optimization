# 20260923-p32k-align-dispatch-36：真实 MoE align 路径接入

- 状态：`reverted_failed_gain_gate`；分类：`operator/replace`；父场景：`p32768-d1024-c64-n128`。
- 主目标：固定 TP16/BF16、`max_num_seqs=64`、MBT32768、前缀缓存关闭与 `FULL_DECODE_ONLY`，证明 FlagGems-vllm 的 padded stage2 能在实际服务中命中，并改善 P32K Mixed 输出吞吐。

## 证据、假设和设计边界

[点33](20260922-p32k-moe-align-ep-33.md)的 FlagGems-vllm 内部微基准为 2.84×–3.12×，但当前 Plugin 的 `CachedOp("moe_align_block_size")` 走 `moe_align_block_size_flaggems → flag_gems.moe_align_block_size_triton`；旧 trace 中新 kernel 0 次。先比较当前真实 FlagGems 完整调用与候选，不能拿点33内部原路径作服务基线。

最窄改动位于 Plugin 现有 FlagGems backend adapter，不改 vLLM：仅在 PPU、topk8、E288、BM16、`expert_map` 存在、M10–64、目标 dtype/layout 的已验证条件下懒导入 `flaggems_vllm.ops.moe_align_block_size_no_tle`，启用 padded stage2；其他情况保持现行 FlagGems fallback。缺少可选库时不影响非目标平台导入；已选择候选后的运行错误不静默吞掉。候选不得根据模型路径、Host 或 served name 选择。Plugin、FlagGems-vllm 分别保存原文件、SHA、补丁和回退入口，保留已有 dirty 改动。

## 冻结的晋级与停止条件

1. 算子门禁：真实 Plugin baseline 与候选完整 align 调用，对 16 个代表性 EP map 及 M10/16/32/64 检查有效 `sorted_ids/expert_ids/num_tokens_post_pad`；覆盖 guard 两侧、非对齐/空输入适用范围与 fallback；目标 graph capture 和两次 replay。M64 完整调用至少 1.25× 才进入服务。
2. 运行门禁：目标 PPU 服务的 16/16 rank trace/等价计数均命中 `moe_align_block_size_stage2_padded_vec`，且 guarded shape 没有回退。启动日志仅证明选择，不算执行命中。
3. 无 profiler 性能 `targeted`：先测 `P32768/D128/C64/N128` Mixed，同配置 baseline/candidate/revert，稳态预热和测量契约执行前冻结，输出吞吐至少 +3%，全部请求成功，报告 TTFT/TPOT/P99 ITL 和资源守护。该 milestone 的 D128 不替代父场景 D1024；若晋级再测父场景。
4. 每点 `minimal-regression`；MoE 路由/backend 接入属于高风险，拟保留前需正式 GPQA `score >= 0.86` 的当前身份 gate。任何数值、graph、命中或稳定性失败立即停止并回退，不叠加调度实验。

## 当前运行事实与外部产物

- Host/容器：`PPU-13` / `glm5.3-flash-opt-20260911`；源适配容器 `glm5.3-flash` 未改动。既有镜像谱系与挂载一致性门禁见 baseline/state.yml；本轮修改前复核无漂移。
- 2026-09-23 预检：当前服务 PID 1499756、端口 8011、running/waiting 均 0；16 张 PPU 由该服务 worker 占用。Plugin HEAD `95b04f7`、FlagGems-vllm HEAD `f7443e7`、FlagGems HEAD `9c9bff3`；前两者有本任务既有 dirty 改动，FlagGems clean。真实导入目录为优化容器 `/workspace/e2e-opt/glm53-20260911/{vllm-plugin-FL,FlagGems-vllm,FlagGems}`。
- 用户远程工作根 `/mnt/nfs/users/jinghao/glm5.3-flash/optimize`，规范路径相同、root:root、`drwxr-xr-x`、剩余 8.6T；继续使用原案例子目录 `e2e-opt-20260911`，新增唯一命令/证据路径，不覆盖旧内容。
- 命令目录：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/commands/p32k-align-dispatch-36-20260923`。
- 证据目录：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p32768-d1024-c64-n128/operators/p32k-align-dispatch-36`。
- 初始建档时结果：`not_run`；服务当时尚未停止，本轮无源码/启动配置改动、无新性能数字。后续执行与最终决定见文末，不能用本条早期状态覆盖结果。

执行前记录的远程变更顺序：用限定 `PPU-13` 的 Ansible `file` 模块创建上述唯一命令/证据目录；用 `copy` 模块放入版本化的停服、比较、打补丁与回退脚本；逐个核对 SHA 和 dry-run；确认目标服务无 running/waiting 请求后，仅对精确识别的优化容器服务进程发送 TERM。不得修改源适配容器、共享挂载、vLLM 或其他服务。原始 Plugin 文件由 `docker cp` 保存到本实验命令目录，回退只复制该备份并重启原配置；候选服务遇到错误时优先回退，不把失败轮纳入收益。

已保存且语法校验通过的首批远程执行副本：`commands/p32k-align-dispatch-36-20260923/stop-service.sh` SHA-256 `17108fa7caaf0b0a20e5dbec9645e8c2bb901473bb8ce509ce4267fa2a8b588d`；`compare-current-vs-candidate.py` SHA-256 `68d1442a1dbb442da1dbb9c200f1effc35c0da9766a2d8fd1327e9520e809563`。脚本在真实算子基线对照前不改源码。

## 首轮算子门禁（2026-09-23）

空闲检查 `running=0/waiting=0` 后，仅对优化容器中 PID 1499756 的目标 `vllm serve` 发送 TERM；脚本确认进程退出且 8011 关闭。源适配容器未动。随后在空闲 PPU 上以当前 Plugin→FlagGems 完整 align 为 baseline，与 FlagGems-vllm padded-stage2 完整 align 做 16 EP maps × M10/16/32/64 精确有效输出比较和 graph capture/两次 replay，全部通过。seed93361、10 次配对 warmup、50 次交错配对 replay 的中位数：

| M | 当前 Plugin→FlagGems | 候选 FlagGems-vllm | 加速 |
|---:|---:|---:|---:|
| 10 | 0.07288 ms | 0.02428 ms | 3.0016× |
| 16 | 0.07342 ms | 0.02550 ms | 2.8792× |
| 32 | 0.07560 ms | 0.02752 ms | 2.7471× |
| 64 | 0.07600 ms | 0.02740 ms | 2.7737× |

原始结果：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p32768-d1024-c64-n128/operators/p32k-align-dispatch-36/compare-current-vs-candidate.json`。截至本段记录尚未修改 Plugin，也没有服务命中/端到端收益结论。

已保存 `commands/p32k-align-dispatch-36-20260923/backup-source.sh`（SHA-256 `fe044e0e2a1688dd43714984bbedecae654ffbb764166a0fc1fd375ac20f79ba`），执行前检查服务已停、Plugin 源文件仍为 SHA `a923d10a...`，然后用 `docker cp` 保存唯一的 `plugin-fused-moe.before.py`；不覆盖现有文件。

原件已保存并核对 SHA `a923d10ac1899ea76ee9ff7871383d05e71e758cd076aadc421e75ef17f483ba`。最小候选只改 Plugin 的 `moe_align_block_size_flaggems`：在严格的 PPU/T-Head、int32 contiguous、M10–64/topk8/E288/BM16/EP map、`ignore_invalid_experts`、非 `pad_sorted_ids` 条件下懒导入 FlagGems-vllm 的 `moe_align_block_size_no_tle(..., use_padded_stage2_vec=True)`；其余保持旧实现。该 guard 不引用模型名、Host 或权重路径。安装脚本要求停服、旧 SHA 与候选 SHA 均匹配，并在安装出错时自动恢复；独立恢复脚本拒绝在线替换。

远程副本及 SHA-256：`plugin-fused-moe.candidate.py` `de5de641218515b31e783383594ffb6f0e9a2cb72c8e45c0cf86910a115eaed7`；`install-candidate.sh` `9815d8c2bc75f4e6bd0d457313a08949c2811702df01c874c69a53ef819c1eec`；`restore-source.sh` `dcd9bd593cfecbf77851d770dcb09199a90edf9b654681be139e216958b2c714`；`test-adapter.py` `006ce0d36cb47c8069f2e2fb7760ad815def576ac1fe491591fcf2a98533f47d`。执行顺序：安装→聚焦路由/fallback/graph 回归→服务 smoke/C8→trace 命中→无 profiler targeted；任何必要门禁失败先停服并运行回退脚本。

候选安装成功，容器内目标文件 SHA 与 `de5de641...` 一致。首版聚焦测试在执行任何目标调用前因 Python 把 `import flaggems_vllm.ops.moe_align_block_size as ...` 解析为包同名导出的函数而报 `AttributeError`；这是测试工具导入错误，原失败输出保留，不追认数值/graph 通过。新 `test-adapter-v2.py` 改用 `importlib.import_module`，SHA-256 `03b9ba7888fda225914998c0a736b8ef17db7a446fa77664631c0898c548cd67`，不覆盖首版。

v2 聚焦回归通过：M10/16/32/64 × 16 EP maps 均路由候选（计数 64 次），M0/9/65 与 `pad_sorted_ids=True` 回退原 FlagGems；目标 M64 的 Plugin adapter 在 graph capture 后 replay 两次。总计候选调用 65 次、fallback 4 次。原始回执为上述证据目录中的 `adapter-gate-v2.json`。这证明独立进程的路由与 graph，不等于 TP16 服务命中。

候选服务启动副本已保存：`launch-inside-container.sh` SHA-256 `9ee8e1c561ac1db9faaa39998b2147adf5e4a205cc279190e28057f2d64731c2`；`launch-candidate.sh` SHA-256 `179418501137a4fbf8adbb16103567ca5bf72c23ebfdc54928335d3fd42bce08`。后者确认服务/8011 未运行、Plugin SHA 与候选一致，再在唯一 `candidate-service-01` 目录写日志；容器内启动参数与原服务相同且显式关闭前缀缓存。

2026-09-23 14:31，候选 TP16/BF16 服务的 `/v1/models` 就绪，11 个 `FULL_DECODE_ONLY` graph capture 完成。随后按 `minimal-regression` 用预存 `run-kda-sanity-v1.py` 执行 C1/C8，`healthy=1/1`、`8/8`；原生结果和 SHA 位于 `candidate-service-01/accuracy/`。本次监控 `glm-p32k-align36-regression` 以 30 分钟 heartbeat 在评测前创建、评测结束后暂停；因短于首个 tick，没有发送虚假的定期进度。运行命令 `sanity.sh` SHA-256 `d1f167ac29c19569990dbc275ab03329072711fb58d23e1fb2fd315e00d3e51a`。该回归不构成正式 GPQA gate 或服务算子命中证明。

下一步执行 `inference-profiling/capture`，目标仅为 16/16 TP rank 的 `moe_align_block_size_stage2_padded_vec` 真实执行计数；现有请求级回归无法给出此证据。将先用本目录 `stop-service.sh` 动态解析并仅停止空闲的优化容器目标服务，再用已保存的 `launch-profile.sh`（SHA-256 `f8da1f0557fb0aa5cb82bddee4defac53262ab62c693207e6fce7c0a7b87b347`）启动只增加 torch profiler 配置的同参服务，最后运行 `run-trace.sh`（SHA-256 `95a29d585ae382aae9340aa0742e6ec71f10dc52ad21c4ed048057dff60c0153`）。trace 使用 P1024/D64/C64/N64、2 轮、1 轮 warmup、seed93302，独立输出目录 `candidate-trace-01/`，只用于命中诊断，不计端到端性能收益；缺 rank 或新 kernel 0 次即不晋级。

Profiler 服务就绪并完成一次 16-rank 采集。原生 runner `diagnostic.json` 为 `failed`，原因不是请求失败：64/64 请求成功，但随机输入重新分词后本轮总输入 token 为 65538，而严格预期为 65536；`p1024-d64-c64-r2-*.validation.json` 保存了两条 token 计数错误。客户端因此未进入下一轮。其已导出的 16 个非空 trace 独立解析成功，`kernel-hit-v2.json` 显示 rank0–15 各一份、每 rank 旧 `moe_align_block_size_stage2` 2772 次、新 `moe_align_block_size_stage2_padded_vec` 0 次。因新 kernel 未命中，point36 当前运行门禁失败，不能以已通过的聚焦 microbenchmark 或 C1/C8 推断端到端收益。与旧 point33 的同类 0 命中一致。此 trace 仅支持执行路径判断；原生 profiler 诊断仍明确保留 `failed`，且其 profiler-on 耗时不用于性能比较。

静态调用链表明 `TritonExpertsFL` 在当前启动命令未显式开启 expert parallel 时可能传 `expert_map=None`，而首版 guard 要求非空 EP map；这仍是待证假设。下一步只在停服状态安装临时参数记录版 `plugin-fused-moe.diagnostic.py`（SHA-256 `67883eac2f6a0b7ee944a7bb814b67d9c898c8e07d5c9a40fbd14beb99801ce1`），用 `install-diagnostic.sh`（`f3b53623e47a5c3db9f1c73110af423d0af7ca3a7b79b02fb78b3be2818c74aa`）核对当前候选 SHA 后原子替换，仅记录首次出现的形状/dtype/`expert_map` 元信息，至多 25 种/worker，不改变数值逻辑。短请求后停服并用 `restore-candidate.sh`（`4ef1a1e8b112429a11996162374bc5657df3af344e476948dc2fc49d409b8870`）恢复原候选，不能将诊断版用于性能测量。若假设确认，先补做 `expert_map=None` 的算子数值/graph/性能门禁，再考虑放宽 guard；否则按实际元信息定位。

诊断服务仅替换目标优化容器内的 Plugin 文件，源适配容器不变。实际 16-rank graph capture 日志已确认根因不止 EP map：Prefill `M32768/topk8/E288/BM128`，Decode capture `M16/24/32` 对应 BM16、`M40/48/56/64` 对应 BM32；所有观察到的调用均为 `torch.int32` contiguous、`expert_map=None`、`pad_sorted_ids=False`、`ignore_invalid_experts=False`。首版 guard 的 EP map、`ignore_invalid_experts=True` 和固定 BM16 三项与 Decode 不符；M64/BM16 的先前 micro 数据也不是实际 Decode shape。实际参数来自 `diagnostic-service-01/service.log` 的 `GLM_ALIGN_DIAGNOSTIC` 行，诊断源码 SHA 如上，且本轮不用于性能比较。

当前无 EP map 算子门禁脚本 `compare-noep-v2.py` 已保存，覆盖 `(M,BM)=(16,16),(24,16),(32,16),(40,32),(48,32),(56,32),(64,32)`、`ignore_invalid_experts=False`，对照当前 Plugin fallback 和 FlagGems-vllm padded stage2 的有效输出、graph capture/两次 replay 及配对稳态时间。诊断服务停掉并恢复候选源码后才执行；如果任一真实 shape 数值或 graph 失败，不放宽 guard，也不进行端到端候选测量。

诊断服务已安全停止，Plugin 恢复首版候选 SHA `de5de641...`。在空闲设备上运行 `compare-noep-v2.py`（seed93361、10 次配对预热、50 次交错配对 replay），上述 7 个真实 Decode 形状的有效输出完全一致，graph capture/两次 replay 通过；完整 Plugin fallback→FlagGems 对比 FlagGems-vllm candidate 的中位数分别为 `0.06472→0.01656`、`0.06490→0.01664`、`0.06552→0.01700`、`0.06632→0.01800`、`0.06484→0.01660`、`0.06536→0.01700`、`0.06530→0.01720` ms，分别约 3.91/3.90/3.85/3.68/3.91/3.84/3.80×。原始证据 `compare-noep-v2.json` SHA-256 `72e7d1f152d19b16e43178089544a7c40070390e11e57bcda11dcfc7eab8f66d`。这仍是算子证据，不是服务收益。

基于已验证集合准备 Plugin adapter v2 `plugin-fused-moe.candidate-v2.py` SHA-256 `2cc46caf18d9a8e549fba48a167a2e33764d184d7e17c2d7483a5bf89c4afeec`。其只额外允许 T-Head、int32 contiguous/topk8/E288、无 EP map、`ignore_invalid_experts=False`、非 padded、`(M16/24/32,BM16)` 或 `(M40/48/56/64,BM32)` 进入 candidate；首版已测 EP guard 与其他 fallback 不变。`install-v2.sh` 在停服和 v1 SHA 匹配时安装，失败自动恢复 v1；`restore-v1.sh` 提供精确回退。安装后先运行 `test-adapter-v3.py`，覆盖新增 7 个目标形状、BM/形状/`pad_sorted_ids` fallback、旧 EP 路径、graph capture/两次 replay，然后重启服务复测 16-rank 命中。未通过任一门禁不做端到端。

v2 已离线安装并核对源码 SHA；`test-adapter-v3.py` 通过：新增 7 组无 EP map 真实形状命中，M8/BM16、M32/BM32、M64/BM16、M65/BM32 和 `pad_sorted_ids=True` 均回退；旧 EP 路径维持通过；两种目标路径均 graph capture 并 replay 两次。原始 `adapter-gate-v3.json` SHA-256 `72eeca02fb9f2d5b2cbd635f48ed0d3429f4f477ec9aa438c136875a99f68087`，候选计数 73、fallback 9。下一步使用已保存 `launch-v2-profile.sh` 和 `run-v2-trace.sh` 启动同参 profiler 服务并以 P1024/D64/C64/N64 单轮采集 16 rank；此次 seed93302/run1 曾在前一轮 warmup 产生精确的 65536 输入 token，可避开 runner 的随机重分词计数失败。若再次发生 token 计数误差，保留原生失败并仅独立解释完整 trace，不修改/掩盖验证结果。

v2 的 `inference-profiling/capture` 原生 `diagnostic.json` 为 `complete`、64/64 请求成功、16/16 新 trace；独立 `kernel-hit-v2.json` 解析显示每 rank 新 `moe_align_block_size_stage2_padded_vec` 2646 次，旧 `moe_align_block_size_stage2` 126 次。旧次数与不满足 Decode guard 的 Prefill 调用并存；新 kernel 16-rank 真实执行已证实，但 trace 的 profiler-on 吞吐不是收益数据。当前可进入关闭 profiler 的同配置 `targeted` P32768/D128/C64/N128 Mixed A/B/R；MBT32768、TP16、max-num-seqs64、前缀缓存关闭和 graph 模式保持不变。需为各臂重新生成真实服务身份与源码 SHA，不能复用 point28 的旧 manifest 或旧 baseline 数字。

仅作热点量级诊断：同一短 trace 的 rank0 中，旧路径 `stage2` 累计 143.526 ms/2772 次；v2 路径旧 `stage2` 6.524 ms/126 次，加新 padded stage2 9.322 ms/2646 次。其他 stage1/3/4 调用总数仍各为 2772，累计时长相近。这个约 127.7 ms 的 kernel 活动差异不是互斥关键路径时间，且 profiler-on trace 不能作为端到端速度比较；它说明“算子快很多但 Mixed 未必显著”的可检验原因是算子在整个服务时间中的绝对占比有限。

该 v2 短 trace 的原生 64/64 请求耗时为 8.469 s（profiler-on），127.7 ms 仅相当于这一诊断窗口的约 1.5%；这是根据不同 trace 的 rank0 算子累计时长推得的粗量级，而非 Amdahl 精确上界，更不能代替关闭 profiler 的 P32K A/B/R。长 Prompt 的 Prefill/排队时间可能进一步稀释 Decode align 的贡献。

`inference-performance-evaluation/targeted` 测量前冻结：只覆盖父场景 `p32768-d1024-c64-n128` 的 D128 缩减 Mixed milestone `p32768-d128-c64-n128`，finite-batch、P32768/D128/C64/N128、`/v1/completions`、seed42、temperature0、ignore EOS、每臂 6 轮预热和 3 轮测量、每轮 5400 s timeout；预热末 3 轮 output throughput 相对 spread ≤5%，不在事后丢弃已准入慢轮。主指标 output throughput ≥3%，守护 P99 TTFT/TPOT/ITL 各退化不超过 5%，测量 spread ≤5%，baseline→revert 漂移 ≤3%，所有请求成功。Prefill/Decode 视图分别来自已记录的 P32K TTFT/输入吞吐和 M16–64 align trace，Mixed 用本轮 milestone；TTFT/TPOT 只作客户端阶段代理。D128 结果不能代替父场景 D1024。

冻结远程 `commands/p32k-align-dispatch-36-20260923/plan.json` SHA-256 `47af966322f8b835e6ae78a94507e1d72bd31c2615fec793a43fdb4c7faeaab1`，`comparison.json` SHA-256 `a9eff7acc94056590b28c6992f0ba9e6ccd2bbbb7c58a108c725ae5f9d38506c`。baseline/revert 使用原 Plugin 文件 SHA `a923d10...`，candidate 使用 v2 SHA `2cc46c...`，其他 Plugin/FlagGems-vllm/FlagGems 源码与配置固定；`switch-source.sh` 只在停服时走带 SHA 检查的 v2→v1→原件或逆向链，`launch-performance-inside.sh` 统一显式 `VLLM_DISABLE_COMPILE_CACHE=1`，前缀缓存关闭，其余同配置。每臂独立服务、唯一目录、`capture.sh` 收集当前 PID/start ticks/源码 content SHA/前缀缓存与编译缓存证据，`build-manifest.py` 生成对应 manifest，`run-performance.sh` 在 dry-run 后执行维护版 runner。诊断时间预算为每臂 90 分钟；超预算保留部分证据并标记 `deferred-too-slow/incomplete`，不把缩减测试当正式 P32K/D1024。

Baseline 已按 `switch-source.sh baseline` 精确恢复原 Plugin SHA `a923d10...` 并启用禁用编译缓存的无 profiler 服务。当前 `capture.sh baseline` 的身份/前缀缓存门禁通过，运行证据 SHA-256 `e6ddbaac45739bbf48e51892f5627c0e7defaedb0bcc36083d8caade9d8dde6f`、manifest SHA-256 `e062496b4d6880a47182d572832e2f39f75d33add057eded5c5307ffdedb7527`。`run-performance-v2.sh baseline dry-run` 已生成并人工核对 P32768/D128/C64/N128、6+3、seed391723 起、固定 plan/manifest/contract SHA；随后才执行 `baseline execute`。截至记录时第一轮长 Prefill 正在推进，`running` 从 4 增至 37、`waiting` 从 60 降至 27，尚无完成轮次；结果仍为 `running/not_run`，不能引用旧 point28 数字作为本轮 baseline。

2026-09-23 后续进度：baseline 6/6 预热轮通过，末 3 轮输出吞吐 36.184545/36.166770/36.190183 tok/s，相对 spread 约 0.065%，满足冻结的 5% 稳态准入。首个正式测量轮 128/128 有效，输出吞吐 36.177603 tok/s；尚余两轮，不能提前给 A/B 收益结论。候选 v2 的 C1/C8 独立命令已预存于 `commands/p32k-align-dispatch-36-20260923/sanity-v2.sh`，SHA-256 `ffbb50d79dd356cec77d05393dd7b2deb701d853fa1450bddd059dab5ba1d393`；输出将放在 `abr/candidate/service/accuracy/`，不会覆盖首版结果，也不会在 baseline 运行中执行。

Baseline 最终原生 `run-record.json` 状态 `complete`，SHA-256 `a2839a78081ee3b6f80904796e4af02a62e2854d233d7ea8fe37d22c28e38ea9`；9/9 轮原生校验有效，正式轮输出吞吐为 36.177603/36.195614/36.177648 tok/s，中位数 36.177648 tok/s。P99 TTFT 为 221540.17/221545.24/221565.90 ms，P99 TPOT 为 1729.99/1728.32/1729.91 ms，P99 ITL 为 3512.50/3503.80/3503.60 ms。该数字只属于 D128 milestone。

该 Mixed milestone 每轮输入 4,194,304 token、输出 16,384 token；P99 TTFT 约 221.5 s、单轮总时长约 453 s。Decode align 只影响输出期间的一部分工作，无法消除长 Prompt 的 Prefill、排队与阶段互扰；这是基于 workload 和阶段代理指标的瓶颈假设，尚待调度实验和 A/B/R 验证。

空闲检查通过后仅停止优化容器基线 PID 1817092，确认 8011 关闭；`switch-source.sh candidate` 从原文件 SHA `a923d10...` 经 v1 精确切换为 v2 SHA `2cc46c...`。候选使用相同无 profiler 启动脚本，`/v1/models` 就绪；C1/C8 原生回归通过 `1/1`、`8/8`，结果 SHA-256 分别为 `9b1c510b4ea8125d53d1e78b7efb3db9543d9f6d49759f27c169148dc9e95257`、`946679383425d1b65a9702cfc55389963e46a38cec8f663b709cbd782fac6343`，heartbeat `glm-p32k-align36-regression` 已在本次测试前激活、结束后暂停。候选身份/缓存门禁通过，runtime evidence SHA `90bf0ac8c7fdb54f4f135b332a245be0c3710280a0cdef2d21ce159354acf526`、manifest SHA `5e942e4153d4df19c6155fd93a3d73978e00b855c92306b34e12abef07565481`；candidate dry-run 与 baseline 的 plan/contract/seed/轮数/场景一致，服务身份和结果目录按 role 独立。候选 6+3 长测正在运行；仍不能据此宣布端到端收益。

候选最终原生 `run-record.json` 状态 `complete`，SHA-256 `9e38b244c38dfefaea43952587a92f291520e4b707e8238cf600b27b969464bc`；6/6 预热有效，末三轮输出吞吐 36.217590/36.213717/36.215959 tok/s，relative spread 约 0.011%，通过稳态准入。三轮正式测量 128/128 均有效，输出吞吐 36.197905/36.218702/36.207369 tok/s，中位数 36.207369 tok/s；与本次原路径 baseline 中位数 36.177648 tok/s 相比约 +0.0822%，未达到预冻结 +3% 门槛。候选 P99 TTFT 为 221493.29/221564.13/221572.01 ms，P99 TPOT 为 1729.46/1727.61/1728.87 ms，P99 ITL 为 3507.25/3509.07/3503.10 ms，均与基线同量级。该结果仅是 D128 milestone；未完成回退漂移检查前不签发最终 A/B/R 判定，也不宣称父场景 D1024 改善。

候选结束后确认 running/waiting 均 0，仅停止优化容器目标服务 PID 1837964；`switch-source.sh revert` 在停服状态将 Plugin v2 经 v1 恢复到原件 SHA `a923d10...`，回退服务已按同配置启动。下一步重新捕获服务身份、dry-run，然后完成回退 6+3 与三臂比较；因候选未过 +3% 门槛，point36 当前不作为保留候选。

回退原生 `run-record.json` 状态 `complete`，SHA-256 `0293ffdafbd265659809eec12764589371aa7054f2941c280799b06878d95821`；9/9 轮原生有效，正式轮输出吞吐 36.199152/36.198377/36.200181 tok/s，中位数 36.199152 tok/s。与 baseline 的吞吐漂移仅 +0.0594%，满足预冻结 3% 限额。三臂实际不同字段仅 `/plugin_sha256`，plan/contract/seed/轮数一致。

初次运行旧远端 `tools/evaluation/performance/compare_performance.py` 返回 `incomplete`，只因它的旧 `performance_plan.py` 不识别 runner 已绑定的 `cases[0].stage=mixed`；原始 `comparison-result.json` 保留，不涂改输入。与本次 runner 同目录的 `performance_plan.py` 支持该字段。新命令 `commands/p32k-align-dispatch-36-20260923/compare-v2.sh` SHA-256 `54940287fc1629c832e4bcaea19c0a8441c433bdb7e643dfa4698c79aa4e9a9e` 只切换到同套比较器，用未改动的三份 run-record 与冻结 contract 输出 `comparison-result-v2.json`，SHA-256 `9952f1ea853d9d8dd9cfeea3b1bc4f5ee772f70dc636b1d0f1ec791dc8d9eeab`。其原生结果为 `failed`，唯一 issue 是 `output_throughput` 主指标未达 +3%；实际 +0.0822%。P99 TTFT 相对变化为恶化 0.0085%，TPOT 改善 0.0600%，ITL 恶化 0.0983%；守护均通过。短 trace 与 micro 的 kernel 收益未转化为本 D128 Mixed 端到端可保留收益。未晋级父场景 D1024，也不触发这项高风险改动的正式 GPQA gate；候选源码保存在远程实验命令目录供后续研究，不作为当前运行代码。

## Plugin 兼容复核

| 范围 | 预期 | 状态 |
|---|---|---|
| 目标 PPU/BF16/EP/M10–64 | 候选命中、数值与 graph 正确 | 独立算子与 Plugin adapter gate 通过 |
| guard 外同模型 shape | 原 FlagGems 路径不变 | 聚焦 fallback 通过 |
| 非目标平台/缺少 FlagGems-vllm | 可导入并保持原选择 | 静态 guard/懒导入复核，未在其他硬件实测 |
| TP16 worker 与 graph replay | 16 rank 真实命中且无生命周期漂移 | v2 trace 16/16 rank 命中；服务 graph 启动和 C1/C8 通过 |

`pr_readiness=not_promoted`；端到端收益门槛失败，保留证据而回退代码，不提交、不推送。
