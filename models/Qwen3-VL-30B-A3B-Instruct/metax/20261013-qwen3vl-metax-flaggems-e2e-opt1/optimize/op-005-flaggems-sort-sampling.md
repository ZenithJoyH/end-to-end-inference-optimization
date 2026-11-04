# op-005-flaggems-sort-sampling

operator/improve；依赖用户已保留的 op002 MoE JSON。D256 milestone 与原始 P1024/D1024/C64/N128 的 performance_only 对照均已通过；正式精度按用户指令暂缓。

## 瓶颈与修改

用户 bench 未指定 temperature，服务采用模型 generation_config：temperature=0.7、top_k=20、top_p=0.8。旧自有 temperature=0 的测试未覆盖随机采样，不能用于计算当前改动收益。新采样 trace 覆盖两 rank，P1K/D16 的 Prefill proxy 和 P1K/D256 的 Decode/Mixed probe。Decode rank0 radix sort 累计 GPU 活动约占25.23%，histogram 120次平均10138.57us、sweep 960次平均984.15us；这是 profiler 归因，不是关键路径占比或端到端提升。

FlagGems `ops/sort.py` 的 `compute_global_hist_kernel` 中，将 `acc = tl.zeros((TILE_R, TILE_N), dtype=tl.int64)` 改为 int32。CTA计数最多8192，当前入口限制 N<2^30，输出直方图本来就为int32。保留4bit radix、8passes、排序与采样语义。没有修改 Plugin/vLLM、没有新增黑名单，MoE JSON保持用户版本。

## 数值与 graph

完整sort（包含histogram、sweep、cumsum和分配）两seed×双排序方向的 M64/V151936 Gaussian 与原FG/CPU stable oracle一致；graph加速1.947–2.163倍，含Python的queued加速1.923–2.147倍，最大B/R漂移0.2033%。M8/16/32/48/64 tie/inf graph加速1.942–2.138倍；fp16/bf16/fp32/int32/int64、dim0/strided和NaN/signedzero/inf共12项检查通过，两次变化输入graph replay通过。

首轮特殊值fixture在原实现对CPU的signedzero bit/index检查失败，候选尚未参与该检查。恢复先证明差异只在正负零，再把普通tie fixture零统一为+0，signedzero/NaN另用原FG位级对照，保留原行为。原始失败和恢复证据均保留。未实测其他硬件或未覆盖dtype，不宣称全平台通过。

端到端各角色两worker实际加载的JIT源码分别证明int64/int32和FlagGems注册；每个服务通过16请求/C8健康、graph capture及两worker至少两次replay，观测hook测量前恢复。

## 无 profiler D256 milestone

targeted/performance_only；P1024/D256/C64/N128，temperature=0.7、模型默认top_k20/top_p0.8。每角色一个独立服务，5warm+3measure；末3warm吞吐spread≤5%，主吞吐提升≥5%，P99TTFT/TPOT回退≤5%、ITL≤10%，测量spread/B-R drift≤10%。所有测量轮保留。

| 中位数 | 基线 | int32候选 | 回退 |
|---|---:|---:|---:|
| output token/s | 977.8944 | 1127.8540 | 976.9091 |
| P99 TTFT/ms | 3750.2233 | 3663.7601 | 3710.0693 |
| P99 TPOT/ms | 63.4116 | 54.8485 | 63.4592 |
| P99 ITL/ms | 443.4572 | 433.1768 | 440.8864 |

native comparison `passed`，吞吐+15.33495%，P99TPOT降低13.5041%，B/R吞吐漂移-0.10076%。这只属于D256 milestone，不作为D1024或四场景验收。

## 原始目标与产物边界

新冻结 P1024/D1024/C64/N128 performance_only 对照：B/C/R各3warm+3measure、3round稳态窗口≤5%，其余门槛相同。独立full-D预热，不替换旧结果、不删除慢轮；native comparison passed。没有正式精度gate，不关闭四场景验收。

实验容器 `qwen3vl-flaggems-op003-20261014` GPU0/1、端口18430，镜像lineage和挂载一致性passed。用户 `qwen3vl-flaggems-e2e-20261013` /8000/GPU4/5 和源qwen-vl未修改或重启。

共享NFS满导致首个公共目录测量在发出任何round前失败，保留失败run-record。未删除共享数据、未增挂载；后续命令、日志和结果改存新容器私有writable layer（通过docker exec读取，非host bind路径）：

- D256：`/workspace/e2e-artifacts/20261013-qwen3vl-metax-flaggems-e2e-opt1/hist32-storage02`；native `results/hist32p-sampling-comparison.json` SHA256 `a2842ff73e0600256b601887cb016c0bb4bbeb7cde8a04d7b9f9df6cb02897af`。
- D1024：同一父目录 `hist32-full03`；预冻结plan SHA256 `2d71d79556c16e9c57aa4da349294e3b9ee408f1ac90333087c4136715668fbd`。
- 原型、trace和恢复数值：远端案例 `/public-flash/jinghao/qwen3-VL/20261013-qwen3vl-metax-flaggems-e2e-opt1/results/`，详见state链接。
- 私有 `patches/op005-sort-hist32.patch` 为单行补丁，before/after源码随存；sort.py before SHA256 `4f63aadbe42f7dbfab0f0fb295c9dea09d749e292ce1b1e61340f68978e8fab9`，after `06208cc0d074bd5a38a9ed84afa5870ccbea062fe3d244a1b438c2dc5df2e184`。恢复before并重启自有服务即可回退，不涉及用户服务。

## PR准备与决定

原始目标 performance_only 对照passed，决定保留私有候选。一般计数位宽改进放在FlagGems实现边界，不增加Plugin模型/平台特例；跨仓库依赖仍是当前op002 JSON。当前测试限定MetaX C550和上述shape/dtype；未提交、推送或创建PR。

## 原始 P1K/D1024 实测与最终保留（2026-10-15）

B/C/R各3warm+3measure，三组稳态准入spread分别2.1464%、2.4168%、2.5872%，均≤5%；native输入身份在测量前后核验通过。所有9轮测量保留、每轮128请求全部成功。

| 中位数 | 基线 | int32候选 | 回退 | 候选改善 |
|---|---:|---:|---:|---:|
| output token/s | 1133.5906 | 1357.2648 | 1130.6226 | 19.731% |
| P99 TTFT/ms | 3705.6467 | 3660.7055 | 3716.9910 | 1.213% |
| P99 TPOT/ms | 56.0880 | 46.8192 | 56.5902 | 16.525% |
| P99 ITL/ms | 56.5791 | 47.4034 | 56.9530 | 16.217% |

吞吐+19.73149%，P99TPOT降低16.52547%；B/R吞吐漂移-0.26182%。测量吞吐spread：baseline 0.8201%, candidate 1.2483%, revert 2.2444%。自动比较所有主指标、P99守护及稳定性门槛passed。仅一独立process/role，不宣称长期稳定性或四场景完成。

新容器已重新保留sort.py int32单行补丁，最终全FGtree为130b1746df5cb8f0817e9f7720f4e9fce35ae9731cbfe71b82c5863b96b84f77；FG-vllm JSON、Plugin/vLLM hash保持原值。自有18430服务已停止，GPU0/1释放。用户qwen3vl-flaggems-e2e-20261013四仓库hash与snapshot一致、8000仍返回qwen3vl-opt2-retry，未回写或重启用户服务。

full native comparison：`hist32-full03/results/hist32f-sampling-comparison.json` SHA256 `956a7410e2860e30e4296cd65f10d529860e512ecadc84fedcbea3f2b2ac3318`；最终源码保留和用户源码核验在同目录 `hist32f-retained-source.json`、`hist32f-user-source-audit.json`。所有路径在上述独立容器私有层，通过docker exec访问。基线/候选/回退run-record路径及SHA详见state。

本次收益只隔离op005对已保留op002 JSON的贡献，不能与旧greedy +8.30%、用户CSV趋势或micro加速比相加。按用户要求未执行正式模型精度；P4K/P16K/P32K尚未验证新组合，最终四场景验收incomplete。下一轮先对P4K采样契约建立Prefill/Decode/Mixed checkpoint，再根据当前组合的热点决定是否优化剩余radix sweep或MoE，拒绝无新证据的进一步MoE扫参。

## 用户授权回写与手动压测交接（2026-10-15）

用户明确要求将已验证sort优化回写到 `qwen3vl-flaggems-e2e-20261013`，保留其当前MoE JSON，并由用户运行端到端测试。已完成sort.py单行int64→int32回写；文件SHA256为 `06208cc0d074bd5a38a9ed84afa5870ccbea062fe3d244a1b438c2dc5df2e184`，与独立容器验证候选逐字节一致，语法检查通过。

前后四仓库文件清单对照确认只有 `FlagGems/src/flag_gems/ops/sort.py` 变化；FlagGems-vllm全仓库指纹仍为 `ef38f46c8a719c7f64ba7c51cc95c895b8667de6bcf9e40b9561c365b4bda99b`，包括用户所有现有修改。GEMM2 MoE JSON SHA256仍为 `ad5bf196af20be5f9bb2916527a9fd061172e7fbbc93ed329a3e925758654261`，Plugin/vLLM均未修改。

没有启动、停止或重启服务，没有在目标容器发起GPU测试/压测；回写时8000接口未运行。用户下次启动推理服务加载新代码。本次不把独立容器的+19.73%当成已在用户容器重新测得的收益。Agent进入手动交接状态，不自动追加远端变更或测试。

回退原文件：`/public-flash/jinghao/qwen3-VL/20261013-qwen3vl-metax-flaggems-e2e-opt1/patches/op005-sort-writeback-20261015-5521f25b/sort.before.py`；补丁：`/public-flash/jinghao/qwen3-VL/20261013-qwen3vl-metax-flaggems-e2e-opt1/patches/op005-sort-writeback-20261015-5521f25b/sort-hist32.patch`。回写回执：`/public-flash/jinghao/qwen3-VL/20261013-qwen3vl-metax-flaggems-e2e-opt1/results/op005-sort-writeback-20261015-5521f25b.json`，SHA256 `12ac31fb377276722e8fd10156c3593b2015e5b05c36265aa1991f8501458978`；回写脚本及SHA见state。以上“仅独立容器保留、用户源码未变”的内容描述回写前验证阶段，本节为最新部署事实。
