# diag-013：采样性能波动定位与回退对照

用户要求：保持其他配置不变，先定位波动，再比较 top-k/top-p 接入回退前后的性能。本实验继续使用既有独立容器 `qwen3vl-p64k-opt-20261015`、GPU0/1、8111；源容器 `qwen3vl-flaggems-e2e-20261013`、8000、GPU4/5及其他负载不操作。正式精度按用户要求暂缓。

## 已定位的波动原因

上一轮 `op012` 的库调用恢复轮耗时 257.629764 秒，相邻快轮为 136.347682 秒，相差 121.282082 秒。慢轮收尾出现 56 个直方图及 448 个 radix sweep 新编译产物；两个 rank 的编译区间取并集为 119.595940 秒，与请求共同长停顿的重合时间也是 119.595940 秒，共同长停顿并集为 123.115217 秒。约 97% 的共同停顿与编译区间重合。编译区间是重叠 rank 的墙钟覆盖，不能相加当作设备计算时间。

实际采样 wrapper 将 `M` 标为 `tl.constexpr`。batch 收尾时请求陆续完成，出现新的 M，就会触发一个 histogram 加八个 sweep 的特化编译；普通满 batch 预热不能保证覆盖所有收尾 shape。底层 helper 的 runtime `m` 参与行号和地址计算，不能据此声称 M 没有用途。

独立、只编译不启动 kernel 的探针复现：首次 M8 约 4.90 秒，首次 M17 约 4.04 秒，同进程重复 M8 仅约 0.00015 秒。第二个全新进程仍重新编译；同 M 二进制相同，但函数/编译 key 不同。跨进程 key 变化的更底层原因尚未完整追踪，不将其臆断为某个 FlagTree 缺陷。不同 M 的二进制不同，亦不能直接删除 M 特化而不验证。

校正两项证据误区：实际编译缓存是容器私有的 `/tmp/qwen-vl/triton_cache`，此前查看 `/root/.triton/cache` 不能排除编译；`/public-flash` 文件时间相对主机墙钟约慢 203.57 秒，关联时采用原生结果内容时间及本地缓存时间，不能直接拼接两个文件系统的 mtime。慢轮 TTFT/常态 ITL 相近，新增损耗主要在 Decode 收尾并拖长整个 Mixed workload。此处 TTFT/ITL 是端到端代理指标，并非纯设备阶段时间。

## 冻结的对照方法

先定位原因后启动原生性能工具的 `targeted/performance_only` 对照：B=回退后原参考路径；C=回退前既有库接入；R=再次回退到原参考路径。顺序安排让最终保留用户要求的参考路径，避免完成后再启动一个未测服务。

冻结 `P4096/D1024/C64/N128`、seed42、temperature0.7、top_k20、top_p0.8，原生计划仍为三轮预热、两轮测量。TP2/BF16、maxseq64、graph64、memory0.91、关闭 prefix cache、原四仓库及 MoE JSON/gems-opt/sort int32/ATen 黑名单均不变，实际 KV 容量须为 562992 token。未关闭任何 FlagGems 算子，未加入 copy_/cumsum 黑名单。

每次服务完成原有生产 graph capture 后，以外部、有界验证 hook 对每个实际 worker 预热两条既有采样 API：M1..64、k int32/int64，以及 BF16 精确值/FP32 非精确值，共 512 次。该步骤不改变算子实现，不推进采样 RNG；在计时前恢复所有 hook，验证真实 HTTP 采样命中及生产 graph replay。三轮预热加两轮测量整个区间必须无新增采样编译产物，所有准入后的测量轮均保留。原生稳定性和 B/R 漂移阈值为 8%，延迟守护 10%，吞吐收益阈值 2%。这是补齐稳态准入，不将启动预热时间计为推理收益。

首个准备版本误挂到未使用的 vLLM GPUModelRunner，实际 Plugin 使用 ModelRunnerFL.capture_model；预热覆盖门禁在任何 benchmark 开始前拒绝该版本。证据保留，随后仅修正外部 hook 目标并使用独立 r2 产物命名，没有丢弃测量轮或修改产品代码。

## 对照结果

| 路径 | 两轮输出吞吐（token/s） | 中位数 | 轮间差幅 | 测量轮最大 ITL |
|---|---|---|---|---|
| B：回退后参考 | 903.453 / 901.364 | 902.409 | 0.231% | 0.595s |
| C：回退前库调用 | 964.194 / 961.011 | 962.603 | 0.331% | 0.588s |
| R：再次回退参考 | 902.216 / 902.045 | 902.131 | 0.019% | 0.592s |

原生比较状态 **passed**；C 库调用相对 B 参考吞吐变化 **+6.670%**，反向表达即回退后相对库调用 **-6.253%**。B/R 参考中位数漂移 **-0.031%**。三组全部三轮预热加两轮测量均无新增采样编译；各轮 128/128 请求成功。

| P99 守护项（ms，中位数） | B 参考 | C 库调用 | R 参考 | C 相对 B 改善，负值为退化 |
|---|---|---|---|---|
| TTFT | 18560.035 | 18438.515 | 18509.417 | +0.655% |
| TPOT | 69.779 | 65.202 | 69.838 | +6.559% |
| ITL | 585.217 | 580.302 | 584.356 | +0.840% |

两条路径的正式计时均已覆盖完整收尾，旧轮次现场编译造成的数秒停顿已被独立定位；本次数据用于评价充分预热后的稳态差异。未修改 kernel 或 FlagTree 版本；完整 shape 预热只存在外部验证脚本中，不能当作已经部署的算子优化。

按本轮既定计划保留原参考路径，使用已经测量的 R 服务，不再额外重启。四仓库指纹回到本次任务初始状态，MoE JSON/sort 保持，源容器四仓库保护通过；同一服务最终两个16 token请求通过。vLLM源码未修改。

每个新服务真实采样命中、17请求最小回归、生产 graph capture 及双 worker 各16次 replay 通过。旧 op012 独立采样 graph 超时仍为未确认项，不用生产 graph 结果冒充它通过。P16K/P64K 未重测，正式 GPQA 暂缓，未进行四场景最终验收。

规划复盘 `planning-sampling-variance-20261017`：当前没有新保留的实现改动；后续若降低 M 特化或追踪跨进程 key，须单独立项验证，不能假定既有二进制可复用或直接删参。历史 P64K +10.92% 不与本次 P4K 相加。

补充核验：三组分别新增 2/2/4 个通用 `reduce_then_scan_root_scan_kernel_row` 编译产物，均在首轮预热，编译区间并集约 0.128/0.148/0.264 秒；六轮测量均无这类新增编译，也无超过 900 ms 的 token 间隔。R 第三轮预热有 58 个请求遇到约 1 秒间隔，共同停顿并集 1.042 秒，无新扫描或采样编译重合；其更底层原因尚未归因。该轮原样保留，后两轮预热差幅 1.57% 通过既定 8% 阈值，两轮测量差幅 0.019%。不能把主因已定位解释为长期零波动。没有修改 `cumsum` 黑名单或重跑替换任何轮次。

## 证据与回退

远端案例根目录：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3`；命令及隔离编译探针在其 `commands/diag013-variance-20261017/`，原始性能在 `results/performance/diag013r2-{baseline,candidate,revert}-01/`，完整执行配置和 SHA 记录于 `optimize/state.yml`。

| 证据 | SHA256 |
|---|---|
| results/diag013-correlation01.json | e3ea3af3db83eef9683e3251fd11ddd5882d0c0323404be49b2048b1cf781273 |
| results/diag013-compile-probe.json | dae2218618d03ea286cd4005310aa5eac6710884500bade0ad795547b15a352c |
| results/diag013-cache-mechanism01.json | 8d139567f135ebb18205a6aa9a52b47eed627e238e53afdd1664f0e9fbe3bff2 |

自动回退和保护检查已通过，参考路径保留在同一 R 服务。完整验证、比较及最终服务身份见下列回执。

- 原生比较：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/diag013r2-comparison.json`，SHA256 `1033fd182b2f035fd56e86787f522baf3301d425a5af28cfdf8ab17965e94f20`。

- 最终源码/配置/服务保护：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/diag013r2-final-verification.json`，SHA256 `307ca3fa23a2c743a5c16838c583c564bbb0db0424f15080aae2b1589f79c5a4`。

- 保留服务：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/diag013r2-retained.json`，SHA256 `c86932a1787a37a3395693bb4e16354ddda3b5d85c07f3e308af6aec2ee3991e`。

- 证据索引：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/commands/diag013-variance-20261017/evidence-index.json`，SHA256 `dbcaf2e61ed506ecba432df667964ef7d9aa6dad2ee94f6d8e3b206b81357a45`。

- 补充扫描编译归因：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/diag013r2-scan-followup.json`，SHA256 `a5169ccd2345ed03fbf0947072fa23cf8967b3bd7d95815a4d37b9f7fc793cff`。

- 追加证据索引：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/commands/diag013-variance-20261017/evidence-index-v2.json`，SHA256 `c78b44c1ec8ce6e97e2edd71be7b3e3434693e9df15ce745df5a493a38072e72`，保留原索引并追加本次只读核验。

用户再次要求回退以自行测试时，重新只读核验：独立容器与 `qwen3vl-flaggems-e2e-20261013` 中对应采样文件都已与 Plugin HEAD 一致，SHA256 为 `30535591ccd3e909371d0f921bb71fe94774dd8a10f53fa8f745df21629a57f5`，均无 FlagGems-vllm 采样导入；两容器默认安装的 Plugin 也均解析到 `/workspace/vllm-plugin-FL`。没有重复修改或重启。8111 是已验证的同一 R 服务，model 为 `qwen3vl-opt5`；源8000现有服务的 model 为 `qwen3vl-opt3`，未对其注入运行时探针。MoE JSON/sort/gems-opt/黑名单及其他配置保持，后续完整端到端由用户执行。
