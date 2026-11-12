# plugin-slim-002 收敛BGE-M3 Plugin完整补丁

- 状态planned；用户明确要求进一步收敛Plugin适配代码；framework维护，不新增数值实现。保留现有FP16/FP32/native embedding/三头joint全部8种选择及literal PAD语义。

## 优化方向与瓶颈依据

当前完整diff为34 files/+2089/-3，SHA146758d9…，Git基线5463eae。生产运行时代码约500行，额外规模主要来自重复文档、独立示例benchmark和测试。不能用删除必要测试/数值护栏冒充实现收敛。

## 优化内容与适用边界

将独立vendor.metax.bge_m3后端别名及注册合回现有MacaBackend.attention_backend，以dtype/architecture/MLA/sparse能力限定FP32分支，其余原路径保持。移除冗余BGE dispatch YAML，改用平台默认metax.yaml；同步示例配置注入/文档/路由测试。自写joint benchmark是实验工具，移出Plugin补丁并保留远端原文，示例保留完整HTTP契约/native benchmark入口。精简重复说明，保留维护所需支持边界与依赖限制。

保留模型PAD修正、joint pooler/IOProcessor请求隔离与全部校验、BGE FP32 attention适配/公开FGV provider、单次执行与原IO hook、generic Worker异步pooling修复。暂不改FG/FGV/vLLM/权重。生产代码实际开发约束A1–A4/B1–B4/C1–C4/D1–D4/F1–F7/G1–G2已读，新增MetaX分支在既有平台边界，预执行选择、不新增数值kernel。

## 正确性与路径命中

先在独立当前状态容器bge-m3-1k-current-20261105-x4jxof0i验证，GPU3仍空闲；该容器基于有效源快照632f985…，此前mount_parity和image_lineage已通过，本轮变更前复核代码/挂载。先保存完整原文/patch/index与回退清单。源BGE-M3/8000服务不停止、不重启。验证通过才以SHA保护发布指定源仓库文件，保留完整回退。

复用已有unit tests与真实FP32 FGV数值链；新增/改写路由测试覆盖FP16、FP32、无模型、其他架构、MLA、sparse、FGV disabled、vendor deny和独立registry状态。已有模型/位置/Worker测试保留。FP16/FP32 controlled baseline/candidate均用相同max_num_seqs1避免合批形状引起伪差；原atol1e-5/rtol1e-4不放宽；正常C8单独检查形状/有限值/接口健康。eager保持当前发布支持边界，不声称模型graph/其他平台已验收。

## 性能效果

本轮不是性能优化验收，既有1K A/B/A证据为稳态未证实，不自动绑定到新候选。若实际执行路径改变影响吞吐，则仅以同配置短诊断记录，不据旧测量宣布收益。

## 决定、风险与回退

待验证。共享MetaX选择入口必须证明非目标分支不变；没有足够证据则保留原实现，不为少几行破坏分层。删掉的示例实验工具在远端原文备份中保存。源服务保留旧已加载版本，源码发布与运行生效状态分别报告，不静默重启。

## 外部证据

/public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261105-bge-m3-mx59-base-1k.x4jxof0i/plugin-slim-002/（准备工具将在执行前保存）；本地审阅只读快照/tmp/bgem3-plugin-converge-20261105.51mw5u47。

设计补充：单次执行保护收回OpManager.call_once（新增6行公开方法），由manager内部负责resolve/first-use/hooks；原call/fallback行为不变。模型仅调用公开call_once，删除独立execution.py，真实部分写入/不重试/IO hook测试完整保留并从模型入口接线。该共享类仅增加方法，验证扩到dispatch单元集。

候选已在私有容器应用：30 files/+1539/-3，patch SHA1f68a24bff51c88028f5b2764cca0b60a3e560089cd6f4eae63229b5826412bf。净减少550行/26.3%；Git HEAD仍5463eae，staged为空。完整模型/dispatch/Worker单元集363 passed（22.06s），包含真实FP32 FGV调用链与独立FP64 reference、执行错误不重试及原I/O hook。完整patch适用pre-commit覆盖31个现存文件（含恢复为原文的vendor register文件），全部通过且未修改候选文件；symlink钩子因无目标文件跳过，不是测试跳过。FP16/FP32模型对照进行中。

源代码已发布：30 files/+1539/-3，patch与隔离候选完全一致。完整diff净减少550行；运行时新增代码480→431行，其余主要是测试和必要示例。363项单测与pre-commit通过，127060个FP16/FP32/native/C8/joint数值逐位一致。运行证据：基线attention_backend为vendor.metax.bge_m3；候选FP16/FP32均为既有vendor.metax，FP32 encoder op仍为default.flagos→真实FGV。没有改模型/IO/Pooling/FG/FGV数值实现。

源8000进程保持运行，尚未重启，所以在线进程仍持有精简前已加载模块；本轮验收的是隔离容器的新进程与已发布的同字节源仓库，不把源码发布混称为在线代码已重载。旧1K性能数据属于patch146758…，不能绑定到新patch1f68…或据此宣称性能收益。

最终审计通过：源与测试候选代码相同、FG/FGV/安装和模型配置保持原状；原源服务PID/argv未变且health200，GPU3无任务进程。补丁中运行时新增480→431行，测试新增904行，其余文档/示例/构建204行，共1539。最终决定retained源码收敛；未签发正式精度/性能结论，跨平台硬件/多卡/模型graph未验证，公共配套依赖仍待固定，因此pr_readiness=experimental。

小型交付包`/public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261105-bge-m3-mx59-base-1k.x4jxof0i/plugin-slim-002/delivery.tar.gz`，SHA256 `2c2de7f5991da797fb63a00c4365a55b7abb2da62722b5e88a8da64505e51232`；含完整Plugin补丁、FINAL_REPORT和回退工具（回退原文仍在远端source-001/candidate-001）。完整产物SHA在SHA256SUMS.json。
