# env016：删除整层W8A8包装，仅保留量化编译边界

已部署到PPU-03 / hy4-preview实际安装`/workspace/vllm-plugin-FL`。本轮只修改两个既有文件：

| 文件 | 保留修改及必要性 |
|---|---|
| quantization/w8a8/linear.py | 删除整层opaque/fake、注册、PPU分支；恢复原量化CachedOp→直接FGV triton_scaled_mm，保留zero-token guard。其他类方法AST与官方一致。 |
| dispatch/backends/flaggems/impl/quantization.py | 当前FGV量化libentry仍不支持Dynamo展开，仅在此FGV量化入口保留一个Torch custom-op/fake边界；原量化数值、环境变量选择与fallback实现主体保持。 |

没有GEMM dispatch key、整层融合kernel或Gems源码修改，Plugin测试仍与官方一致。量化CachedOp仍为原dynamic_per_token_quant_int8/default.flagos。原有w8a8_dynamic_per_token_linear策略字符串保留，其对应整层Torch custom op已移除。

本轮两文件diff（历史路径当前不可用：`/tmp/hy4-wrapper-check-20261019-01/from-env015.patch`；须从原 revision 或远端证据恢复） · 完整diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env016/full-diff.md`） · 完整可应用补丁（历史路径当前不可用：`/tmp/hy4-wrapper-check-20261019-01/full.patch`；须从原 revision 或远端证据恢复）

固定官方HEAD `8b2033e417a535a828a1d7594d36bd33e36e3b57`；整体12文件（6新增/6修改）+1097/-16。新增一个已有量化文件的diff，是把必要边界从linear收回量化实现处；没有新增生产文件。完整patch SHA256 `4ab695213421fd78a9692e4c2941bab9f210af961ea4763d2e51ac5818a96575`，本轮delta SHA `9479517ec622d1ae1701e924131c55e072ab445080ebb9914135e0bebae3b614`。

当前硬件对照（device0，seed781，同一SDK/policy/blacklist、量化provider，两个gems-opt固定）：

| 路径 | 结果 |
|---|---|
| 当前整层包装 | 8例通过；7非空例各完成fullgraph、raw graph两次及compiled graph两次replay；另empty通过 |
| 无任何边界，直接CachedOp→GEMM | m1数值/raw graph通过；fullgraph失败 |
| 仅量化 | 相同fullgraph失败，定位FGV scaled_int8_quant.py:514→libentry.py:856的jit_function.params切片 |
| 仅GEMM | fullgraph及两类graph各两次replay通过 |
| 仅量化保留边界，GEMM直接调用 | 同一8例全部通过，包括BF16/FP32、bias、identity、非整齐shape、全零、非连续和empty |
| 安装后真实路径复核 | m1数值/fullgraph/两类graph各两次replay及empty通过；函数/源码SHA与实测候选一致 |

参考为CPU INT8累加，atol=rtol=.008，无graph break/suppress_errors。GPU allocator峰值约259MiB、reserved约352MiB，上限1%且启动时余量约5.27GiB。源码/两Gems/原服务身份在探针前后核对一致；安装变更只有上述两文件，615文件全量校验及权限/symlink检查通过。

结论：整层包装可以删除；当前FGV量化本身仍需要一个局部编译边界。没有用eager通过代替fullgraph，也没有降低容差。issue compat-009为执行模式问题，未观测模型分数下降；原失败候选与trace保留，修复结果仅证明当前算子范围。其他平台/TP16整模型启动、capture、C8/分页和完整GPQA未测，PR readiness仍待模型验证。

两个gems-opt的HEAD、分支、clean与tracked文件摘要始终不变：FGV46387d7f / FG3ba1d1d9。未重启服务、未发模型请求、未开始评测，heartbeat暂停；原service07仍为旧env011进程，health200不代表加载新源码，无当前87%正式gate。

证据根 `/workspace/.hy4-preview-migration-20261018-01/wrapper-check-20261019-01`：results/wrapped.json、direct.json、quant-only.json、mm-only.json、quant-boundary.json、installed.json；原始trace在logs，failure-sha256.json冻结失败证据。备份plugin-env015-before.tar.gz SHA `98bbc21876c162856e3ccb78cba91c13d5f5bb33c105cd5769c994a5ff8c7b91`；commands/rollback.py只恢复本轮两个文件，无服务操作。Skill e2e/accuracy选择minimal-regression（算子作用域通过、服务级incomplete），失败定位使用本地inference-accuracy-diagnosis。
