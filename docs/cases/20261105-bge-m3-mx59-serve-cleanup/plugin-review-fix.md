# fix-001：按完整 diff 审查修正 BGE-M3 实现

> 本文保留Plugin整改阶段的执行快照。用户随后追加整理两套算子库，最新Git基线、FG/FGV完整patch、显式metadata校验和FP16批次诊断结果见[算子库整理记录](operator-repositories.md)；本文旧FG companion SHA不代表当前最终三库组合。

用户于本对话明确要求修复 R1/R2/R3、去除不必要修改、保持现有功能并补齐验证。范围仅 mx-59 / BGE-M3 私有 Plugin、FlagGems 源码及必要测试/文档；不修改 vLLM、FlagTree、FGV、权重、共享副本、其他容器或服务，不提交推送。

**最终状态：`local_fix_validated`，R1/R2/R3 已修复并部署。** Plugin 80 项、FG 24 项测试及两仓库适用 pre-commit 全部通过；最终 FP16/FP32 功能对照通过。完整 Plugin diff 为34 files/+2089/-3（修改前35 files/+2311/-3）。配套 FG 尚未形成公开提交，当前是已验证的本地组合，`pr_readiness=experimental`；发布 PR 前须先交付 FG 改动并固定可公开获取的版本。下文保留各轮执行和失败诊断证据，最终结果见文末。

## 修改前事实与回退计划

- Plugin 根 `/workspace/bge-m3/tune-src/vllm-plugin-FL`，分支 `bge-m3-review` / HEAD `5463eae824b1fbaa3d331564ab2fb4c51f1b6e09`，完整 patch SHA `453043aea590d95f73e4bc2bbc22f9a75b2b208568b3adec2fe3ce8ee25bd897`，35 files/+2311/-3，尚无人工漂移。
- FG `/workspace/bge-m3/tune-src/FlagGems/src/flag_gems`，只有源码，无 `.git`；镜像记录基线 `4897cc306cd83390c95b83b50df28f7edb1684c5`、安装元数据 `0.0+g4897cc306`，另有镜像已交付的 guard 等改动，不能伪称干净公开基线。
- FGV `/workspace/bge-m3/tune-src/FlagGems-vllm/src/flaggems_vllm`，不修改；Plugin `0.0.0+gef7339f1.review20261104`、FGV `0.3.0.dev1`；真实导入已重新核验。
- 三个目录均不在 `/public-flash` 或 `/data` bind mount 下；容器主命令 `/bin/bash`，只见 Bash 进程，没有需重启的 BGE 服务。
- 已经由 `scripts/accelerator-check --limit mx-59` 与 `mx-smi -i 2 --show-process` 核验 GPU2 无进程占用；验证只限制这张卡，不争抢其他卡上的服务。
- 独占容器产物目录 `/tmp/bge-m3-review-fix-20261105.9La1x0`，由本轮安全创建。源码修改前备份每个目标原文件、权限/owner/group、原始 Git index/HEAD/status 与补丁，并记录文件 SHA；如遇漂移则停止覆盖。最终回退工具只恢复本轮目标源码，保留 Git index 供人工核对，不覆盖后续暂存操作、不重置其他源码或停止服务。
- 本地候选 `/var/folders/r4/vg8kl9yj2651_r2x_0xzn4tw0000gn/T/bgem3-review-fix-20261105-kvyl3g8v/{plugin,fg}`，原文留在同一临时目录 `{plugin-before,fg-before}`。控制工具保存本地 `/tmp` 与独占容器 commands 目录后再执行。

## 已冻结实现方案

1. 删除 Plugin 的 `configs/bge_m3_metax.py`、`models/bge_m3/linear.py`，清理模型构造绑定、两个 YAML 中的 Linear policy、两个 provider 中的 Linear 注册/launcher，保留 attention 和现有 FP32 joint/FP16 dense 功能。
2. FG 维持公开 `flag_gems.linear(input, weight, bias=None)`、原 ATen schema/注册。将原两个 FP32 候选移入 MetaX `tune_configs.yaml` 的内部调优 key `linear_small_fp32`；原 dtype/连续布局/shape/M<=1024 区域使用独立 tuner，其他输入保持默认 tuner。调优候选深拷贝，不修改默认候选或创建非 ATen 数值 API。算子性能选择按真实 shape，非模型名称。
3. BGE attention 在执行前选择实现，随后只调用一次，避免非 strict 策略在部分写入后进入通用 fallback 重试。初始方案使用 `resolve_op`；最终兼容性复核改为现有 OpManager 上的最窄 `call_op_once` 桥，保留首次命中日志和 I/O 诊断钩子；不修改原 CachedOp 或全局执行策略。
4. 增加原方法身份不变测试、FG 公开入口数值/注册/边界/两次 graph replay 测试、真实模型 attention adapter→OpManager→真实 FGV 的命中与独立 FP64 reference 测试，以及执行错误不重试测试；保留既有 IO/Worker/位置等测试。
5. 用户文档同步纠正归属，删除“Linear 调参应留在 Plugin”的表述。新的 FG 补丁尚无公开 commit，按 D3 明确标为本地实验性跨仓库组合，不能伪造 public pin 或擅自发布。

## 验证计划与已执行项

- 基线 CPU：容器内 `MACA_VISIBLE_DEVICES=2 CUDA_VISIBLE_DEVICES=2 GEMS_VENDOR=metax USE_FLAGGEMS=0 VLLM_PLUGINS=fl PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`，pytest 排除 gpu 标记，BGE 模型/dispatch 与 Worker 新契约测试：81 passed / 33 deselected，18.64s。原生结果 `baseline-cpu.xml`、`baseline-cpu.log` 位于上述独占目录。
- 后续在同一张空闲卡顺序执行目标单测、公开 FG Linear 数值/注册与 capture+两次新输入 replay、真实 FGV adapter 数值/命中，以及原有功能 smoke。必要测试工具装入独占 tools venv，不升级运行时依赖。
- 功能回归契约：先在未改源码上运行 `/tmp/bgem3-functional-smoke-20261105.py baseline`，修改后运行同一工具 `candidate`。在 GPU2 上依次启动本任务拥有的 FP16 dense 和 FP32 joint 服务，随机空闲 loopback 端口，TP1/eager、max_model_len128、max_num_seqs2、MBT256、gpu_memory_utilization0.15；每个服务 readiness 最长240s，单请求120s，完成后只结束其自身进程组。两条固定中英输入含 literal PAD，检查 native embeddings 的维度/有限值，以及 FP32 的全部8种联合输出选择、字段/null/batch维度；保存完整外部 JSON，以预先冻结 atol1e-5/rtol1e-4逐项对照 baseline/candidate，要求键、维度和禁用字段完全一致。不作吞吐或正式精度结论。工具和准确 argv 执行前写入独占 commands 目录；控制入口 `python3 /tmp/bgem3-run-container-20261105.py /tmp/bgem3-functional-smoke-20261105.py baseline`。
- formatter/linter/pre-commit 使用目标仓库配置及固定版本；任何自动修复仅限本补丁文件，修复后重新核验差异并回归。
- 本任务是实现维护与正确性回归，不运行固定四场景性能验收，不声明性能提升、正式精度 gate 或 graph 模型服务支持。

部署前验证：Plugin 与 FG 候选分别按原仓库配置执行完整 pre-commit，所有适用 hook 通过（无适用文件的 hook 正常 skipped）；未 autoupdate hook 或改运行时依赖。工具独立安装于本地 `/tmp/bgem3-review-fix-tools312-20261105`，缓存 `/tmp/bgem3-precommit-cache-20261105`。FG 的配置从其精确公开基线只读取得，不部署至运行源码。

未修改代码的功能基线已完成：FP16 native embeddings、FP32 native embeddings 和全部8种 joint 输出选择通过；两个任务服务均已结束，输出保存在 `baseline-functional.json`。首次本地控制包装命令自动审批超时，尚未执行；改用透明的直接 SSH 上传/执行已保存脚本后成功，无安全拒绝结论。首个上传因 commands 父目录尚不存在失败，随后只创建该任务子目录并重新上传；未影响生产源码。

候选 payload SHA256：`1f746712c928eaee0eb7d5618f17466fbd3d018fdbe16606f2ca66f81f6920bc`。远端执行副本已保存到 `/tmp/bge-m3-review-fix-20261105.9La1x0/commands/{fix-payload.tar,bgem3-deploy-fix-20261105.py}`。下一变更命令：`ssh mx-59 'docker exec BGE-M3 /flagos/bin/python /tmp/bge-m3-review-fix-20261105.9La1x0/commands/bgem3-deploy-fix-20261105.py'`。将先核对旧 patch/逐文件 SHA、完成全部备份，再替换11项 Plugin 文件（其中删除两项已备份的新添冗余模块）和3项 FG 文件；只对删除的 intent-to-add 路径做限定 `update-index --force-remove`，不 checkout/reset 或提交。

deploy-001 完成：11项 Plugin 与3项 FG 文件按清单修改，原文及 index 位于 `deploy-001/before` 和 `deploy-001/plugin-index-before`。导入绑定/HEAD不变，Plugin完整patch变为 `d18c8d0f9e94bb099dba3581d7cafe1ac696fdaa11c9a83ce3cd5ac4d4d26bd9`，33 files/+2056/-3；无提交、无已有服务重启。

首轮修复后 Plugin 回归：79 passed / 1 failed（`candidate-plugin.xml/log`）。新真实 FGV 测试实际注册表为空，原因是原 CPU harness 的 `USE_FLAGGEMS=0` 禁止了目标注册，尚未执行到 kernel 数值比较。修正该测试：显式临时启用 USE_FLAGGEMS/FGV、仅白名单该 op，以新建真实 OpManager 跑实际 builtin 注册；不替换生产 resolver/provider/kernel，不放宽数值断言。另给 FG ATen 注册测试增加实际 tuner 命中断言。两份测试修订再次通过各自原 pre-commit。失败原始 XML/log 将保留为 attempt1，不覆盖。

下一变更仅更新上述两份测试：通过 `test-refinement.tar` 和 `bgem3-deploy-test-refinement-20261105.py` 在 `deploy-002` 逐文件校验并备份后部署，保持生产实现不变。随后重跑完整回归。

阶段状态（deploy-002 时）：整改已部署，验证继续。执行结果如下。

deploy-002 后 Plugin 完整回归 80 passed（20.63s），其中包含真实 FGV/OpManager 数值与命中、部分写入后不重试、默认 Linear 方法身份、原有 IO/位置/Worker。Plugin完整patch SHA `303285170f1841383f88672128b9a3c14e5762a22e5f72eb1c436c628547e6d1`，33 files/+2059/-3。

FG 首轮 23 passed / 1 failed，110.35s；通过项已包括真实 ATen 命中与 capture+两次更新输入/哨兵 replay。失败是 K4096、非零 storage offset、无 bias 的 FP32 单元素绝对误差0.00023645略超新测试统一2e-4阈值（1/32768元素）。没有删除该输入、缩小随机数范围、修改生产 kernel 或直接放宽阈值。对同一 seed731/input/weight，通过已备份原实现进行诊断，`linear-roundoff-diagnosis.json` 证明原FG公开入口、原Plugin特化与新FG公开入口误差指标及失败点完全一致：max_abs0.0006596896，relative_L2 1.1504642e-6，同一位置值 -0.0237358585，独立FP64 reference -0.0239723127；三者都通过 FG 既有 `testing.assert_close(..., reduce_dim=4096)`。

据此纠正新增测试的比较逻辑（E5允许修正编写有误的测试）：采用目标库既有归约长度规则，同时额外要求相对L2误差 <= max(1e-5, 2*dtype_eps)，防止归约缩放绝对容差隐藏累加精度丢失；独立CPU FP64 reference、全部原输入、shape/布局/命中断言均保留。仅此一份FG测试通过 `fg-comparison-test.tar` / `bgem3-deploy-fg-comparison-20261105.py` 于 `deploy-003` 校验备份后更新；生产实现和 Plugin 不变。原 FG 失败 XML/log 保留为 attempt1。修订再次通过原FG完整pre-commit。诊断脚本、测试修订及执行命令均在 commands 保存后运行。

最终顺序验证命令已保存为 `commands/bgem3-final-validate-20261105.sh`，执行入口 `ssh mx-59 'docker exec BGE-M3 bash /tmp/bge-m3-review-fix-20261105.9La1x0/commands/bgem3-final-validate-20261105.sh'`：先补充三路逐位相同检查并保存独立 JSON，再部署单份测试、保留原 FG 失败记录、重跑FG24项，最后运行候选 FP16/FP32 功能对照。仍只使用GPU2，过程不并发跑模型与算子测试。

上述验证全部通过：FG24 passed（15.33s），两种模型profile与全部8种joint输出对照通过，110676个数值最大绝对差2.3841858e-7；三路roundoff对照逐位一致。首份 `FINAL_VALIDATION.json` SHA `32d24b8201418d111ca1f33f635ca37b0369c4dbadfa1995854542735fe2f2c1`。

最终兼容性复核发现直接 `resolve_op` 调用会绕过原 CachedOp 的 I/O 诊断钩子，故补充最窄执行桥 `dispatch/execution.py::call_op_once`：仍用原 OpManager 完成执行前选择、首次命中记录和 `_call_with_hooks`，唯一不同是数值执行异常不重试。只新增显式 opt-in API，不修改旧 manager、CachedOp、全局策略或其他模型路径。BGE adapter 改用此桥，原 partial-write 测试同时断言原钩子只执行一次并收到原输出对象。避免为触碰公共 `dispatch/__init__.py` 带入全文件无关 import 排序，该文件保持原文。

该兼容修订经原Plugin完整pre-commit通过，使用 `io-hook-preservation.tar` / `bgem3-deploy-io-hook-20261105.py` 在 `deploy-004` 校验备份后更新两处关联文件并新增桥文件；对新增桥使用意图添加，不暂存内容。随后保留上份回执，重跑Plugin80与两种模型功能对照。FG源码及其24项通过回执不变，无需重复未受影响的FG算子测试。

deploy-004 已部署：最终 Plugin 为34 files/+2089/-3，patch SHA `146758d9791c8e6ceb7bb51695925215ca4d50ba2563c7dfaa4f99d2e935db42`。Plugin80项再次全部通过（19.70s），包含钩子原输出身份/单次执行断言。两种模型功能复测正在完成，旧回执均以 `*-before-io-hook.*` 保存。最终 FG 配套 patch SHA `7754ff52816e1e8cab03300ec37ef94804b2c054954eb3bb5bbb9646f7c5dcce`。

## 最终整改与验证结论

| 发现/条款 | 最终处理与证据 |
|---|---|
| R1；Plugin A1/A4/B2、算子职责边界 | Plugin 中私有 FG kernel 解包、tuner/launcher、Linear vendor 注册及模型专属调优模块已删除。调优在 FG MetaX 公开 ATen Linear 内按 dtype/layout/shape 选择；默认配置不被修改，公开函数签名/注册和原 kernel 数值计算保持原样。Parameter 无复制视图在算子 wrapper 内处理。 |
| R2；D2/F5 | 移除无收益的模型 Linear 绑定、转发模块、两个 YAML policy 和对应 provider；默认 FP16 直接保留原层方法。构造测试检查方法身份、参数与 state，不只比较返回值。没有顺带格式化公共 dispatch 初始化文件。 |
| R3；B1/B4/F1/F2 | 真实 BGE attention adapter→真实 OpManager 注册/选择→真实 FGV kernel，验证实际命中、多文档 metadata 与独立 CPU FP64 reference。另验证部分写入后的错误只抛出一次、原 I/O hook 收到原输出对象。全局 manager/CachedOp 的其他调用行为不变。 |
| F2/F3/F4 | FG 公共入口22项数值场景覆盖四个特化shape、M=1/32/1024/1025、FP16/BF16/FP32、bias、Parameter、storage offset、非连续权重及范围外输入；加真实 ATen 命中与真实 capture/两次新输入和哨兵 replay，共24项通过。图测试仅声明32×1024×1024所测配置。两仓库适用 pre-commit 通过。 |
| D3；交付边界 | 公共 Linear API 未改变，但保持本次 FP32 调优需要配套 FG patch。两份补丁一同交付；没有虚构 public SHA、升级依赖或提交推送。发布前的“FG先公开交付→固定依赖版本”尚待执行，不能把本地通过写成可独立合入的 Plugin PR。 |

最终 `commands/bgem3-validate-io-hook-20261105.sh` 已完成：Plugin **80 passed（19.70s）**；FG 未再修改，使用其最终 **24 passed（15.33s）** 原生回执。最终候选再次通过 FP16 native embeddings、FP32 native embeddings 及所有8种 joint mask；键、形状、禁用字段/null、batch、维度及有限值一致。与未修改源码基线逐项对照110676个数值，最大绝对差 **2.384185791015625e-7**，满足预冻结 atol1e-5/rtol1e-4。不是正式精度或性能验收，未验证其他平台硬件、模型服务 graph 或多卡。

最终封存工具 `commands/bgem3-final-report-v2-20261105.py` 对四轮 manifest 中所有目标源码逐项复核 SHA、安装绑定不变、HEAD/原分支不变、空 staged 内容、diff whitespace 和最终测试/功能回执。封存结果如下（均位于 BGE-M3 容器独占目录 `/tmp/bge-m3-review-fix-20261105.9La1x0`）：

| 产物 | SHA256 |
|---|---|
| `plugin-final.patch` | `146758d9791c8e6ceb7bb51695925215ca4d50ba2563c7dfaa4f99d2e935db42` |
| `commands/fg-companion.patch` | `7754ff52816e1e8cab03300ec37ef94804b2c054954eb3bb5bbb9646f7c5dcce` |
| `FINAL_VALIDATION.json` | `737c217f8d3e475355c6d65c92338d506306c2bc6d21c993d95e55deb35e4c50` |
| `candidate-plugin.xml` | `a0ea9289670ab57054807d4b50c7c1cc5125a9964984e3d3f45b229da9e13c2b` |
| `candidate-fg.xml` | `3b88017aa3611983a711ebb483ae3c52c5b05fbe61221730fd661583149f0ad4` |

先前失败回执、三路逐位一致诊断、旧兼容性回执、完整服务日志及 `deploy-001` 至 `deploy-004` 原文备份全部保留于同一独占目录。收尾只见原有两个 Bash 进程，GPU2无进程；本轮任务服务均已退出，未重启其他服务。

小型可审阅交付包：[bgem3-review-fix-20261105-delivery.tar.gz](/tmp/bgem3-review-fix-20261105-delivery.tar.gz)，SHA256 `59f525ab08e6362a21c954592ea5d42bcf3bb9447ed4a1ec6512010dcc0a7435`。仅含两份补丁、最终摘要和回退脚本，不含权重、数据或完整日志。包和容器证据位于临时目录，长期交付前需另行归档。

回退工具已保存并做语法核验，**未执行回退**。必要时在确认本轮修复需撤销后运行 `ssh mx-59 'docker exec BGE-M3 /flagos/bin/python /tmp/bge-m3-review-fix-20261105.9La1x0/commands/bgem3-rollback-review-fix-v2-20261105.py'`：先核对没有后续源码漂移，再从四轮备份恢复各路径最早原文/权限；新文件移除，Git index 保留供核对，不触碰其他源码、服务或提交。该脚本依赖容器原备份，交付包中的脚本不替代备份。
