# BGE-M3 Plugin第二轮收敛

用户要求进一步减少当前完整适配补丁。范围mx-59/BGE-M3，保留FP16/FP32及joint功能。当前34 files/+2089/-3、patch SHA146758d9791c8e6ceb7bb51695925215ca4d50ba2563c7dfaa4f99d2e935db42，与前次交付一致，无用户源码漂移。当前生产服务GPU2/8000健康，既有独立当前状态容器可用于GPU3验证。

完整方案与持续状态见[plugin-slim-002](../../../models/BGE-M3/metax/20261105-bge-m3-mx59-base-1k/optimize/plugin-slim-002.md)。执行前先保存工具、备份、完整diff/index及逐文件SHA；先在隔离容器验证，再发布源文件，不重启源服务。FG/FGV/vLLM/权重保持原状，不提交推送。

功能回归复用前轮functional-smoke.py契约并适配到GPU3/默认平台配置：FP16/FP32原生embedding、每侧HTTP C8、FP32全部8种joint选择；controlled max_num_seqs=1、maxlen128/MBT256，两侧相同以消除已知合批形状导致的FP16伪差。C8验证请求并发与返回，不代表GPU batch64或模型graph。精度阈值仍atol1e-5/rtol1e-4。工具/tmp/bgem3-slim-functional-20261105.py SHA256 `fa8d665d35d8a32faba7a6ed47783e6e8ededf1be1ab4ca5fd0f2c3e5e35fafc`，执行前存入既有远端case/plugin-slim-002/commands/functional.py；先baseline，再candidate。

准备工具/tmp/bgem3-slim-prepare-20261105.py，SHA256 `ea2dd327eea084e758325dc5f8475e0eff23914c242effc6de72d939cf07974e`，上传Host唯一/tmp入口后执行；只在既有案例内创建plugin-slim-002，核对源/候选完整patch、空staged、三库/安装和原挂载一致性，保存原patch、指纹及工具。未启动/停止源服务、未改代码。

候选部署工具与payload已冻结，包SHA256 `b3998cc792a0dc7ee70d4ca84d1e9d013557b6bc21bfb08a56a5c1c8bddccdbd`；文件SHA {"candidate.tar": "444bb47fa39f2e3e4f0622d2515632b3519f2148cb2b7c53fb8c1ede8cba8b6d", "candidate-manifest.json": "f3f7455676627e02cdf262ce566385da9b096606531574bbbfb826ce5cb275c2", "deploy.py": "2d979bb785d0afa53783d44ef3044bf428bce03dcef25174dfbb6d81b1956257"}。下一变更入口仅在baseline服务结束后执行：隔离容器python case/commands/deploy.py candidate candidate-001。工具先核对完整旧patch/空staged/17项逐文件SHA、保存每份原文/权限和Git index，再原子逐文件修改；删除的是已备份的新添适配/示例文件，不涉及模型数据。异常回滚已变文件/index；对被删除的intent-to-add只做限定force-remove，不重置其他源码。源发布仅在全部验证通过后使用同一manifest source source-001。

候选部署命令被自动审批拒绝，理由为共享挂载可能让17项修改影响在线源服务；该命令未执行。按审查意见先做只读取证（private-proof工具），保存case/PRIVATE_SOURCE_PROOF.json。实际共享目的地仅/public-flash与/data，目标真实路径/workspace/bge-m3/tune-src/vllm-plugin-FL不被任何挂载覆盖，source/candidate根文件系统身份不同，真实import路径均在各自私有树，双方旧patch仍146758…且源health200。该证据用于消除共享源码风险后重试同一候选命令，不通过间接执行绕过审批。

验证执行副本case/commands/validate.sh，SHA256 `7d740973de4f967a4fb3a152a82c99d8b6946e2c1c30cce004f4e12f4b3c918e`。单一GPU3顺序执行模型BGE全部单测、完整dispatch单元集、generic Worker新增契约，再复用功能回归candidate与baseline数值对照；不与本轮服务并发跑算子测试。产物case/results/candidate-unit.{xml,log}及candidate-functional.json、functional-comparison.json；错误即停止，不掩盖pytest失败。

候选最终验证：363单元项通过；完整适用pre-commit通过且无自动改文件；真实FP16/FP32 native、每侧C8及全部8种FP32 joint输出共127060个数值与本轮精简前基线逐位一致（max_abs=0，原atol1e-5/rtol1e-4未放宽）。候选服务全部已停止。下一步按既有manifest发布到用户指定BGE-M3私有源码：docker exec BGE-M3 python case/commands/deploy.py source source-001。该操作仅更新/workspace/...内17项Git工作树文件并保存原文/index，不修改Python已加载对象，不停止/重启8000服务，不改FG/FGV/vLLM/权重；新代码在下次进程启动加载。部署前仍检查原完整patch146758…和逐文件SHA，不覆盖后续人工改动。

回退工具case/commands/rollback.py已保存并本地语法检查，未执行：仅允许source-001或candidate-001；必须验证当前完整patch仍是本次1f68…、空staged及逐文件新SHA，才从该部署原文恢复17项文件/权限及原index，最后校验完整patch回到146758…；不停止服务或回退其他组件。工具SHA256 `2645e73565ca5442c6061f60218f51a883f50f9ae762ed23988759d3260aa83d`。precommit原生日志一并保存外部commands/precommit.log。

源私有仓库source-001已按相同候选发布，完整patch与测试版一致（1f68…、30/+1539/-3），原HEAD不变且staged为空。最终封存工具case/commands/finalize.py（本地/tmp/bgem3-slim-finalize-20261105.py，SHA256 `557d8033b9ade95ce76dd2489f0ad670c73e9c34b62cd5b76b3fd397fa7014cd`）将复核源/候选源码一致、FG/FGV/安装/权重配置未变、363项JUnit零skip/零失败、数值127060项零差、源进程身份/health保持、GPU3释放；只写报告/校验和/小型交付包，不编辑环境或重启服务。

## 完成结果

| 项目 | 精简前 | 精简后 |
|---|---:|---:|
| 完整diff文件数 | 34 | 30 |
| 完整diff新增行 | 2089 | 1539 |
| 其中运行时代码新增行 | 480 | 431 |

净减少550行（26.3%）。合并专用MetaX选择别名、删除两份冗余dispatch YAML、收回单次调用到OpManager公开入口、移除248行自写示例benchmark和重复说明。保留模型PAD位置修正、native/joint全部功能、请求隔离、I/O hooks、写入后错误不重试和generic Worker兼容；原模型/边界测试保留，并扩到完整dispatch单元集。

- 完整patch SHA256：`1f68a24bff51c88028f5b2764cca0b60a3e560089cd6f4eae63229b5826412bf`；Git基线仍5463eae，staged空，未提交推送。
- 验证：363 passed、0 skipped；全部适用pre-commit通过；真实FP16/FP32、HTTP C8和8种joint选择共127060个数值逐位一致（max_abs=0，原容差不变）。
- 实际后端：两种dtype统一通过既有vendor.metax注册；FP32计算继续由default.flagos的公开FGV provider执行，无新数值kernel或隐藏fallback。
- 源/测试候选完整补丁与文件指纹一致，FG/FGV/vLLM安装、模型配置保持原状；源服务进程未重启、health200，仍持有精简前已加载模块，新源码下次启动加载。GPU3已释放。
- 外部证据：`/public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261105-bge-m3-mx59-base-1k.x4jxof0i/plugin-slim-002`，源原文/权限/index在source-001，候选原文在candidate-001；回退工具commands/rollback.py已语法检查，未执行。
- 交付包：delivery.tar.gz，SHA256 `2c2de7f5991da797fb63a00c4365a55b7abb2da62722b5e88a8da64505e51232`。正式精度、性能、模型graph及其他平台硬件未测；配套公开依赖尚待固定，PR状态仍experimental。

本轮最初候选部署曾被自动审批以共享源码风险拒绝；只读挂载/文件系统取证证明/workspace私有后，同一候选命令获准执行，最终没有待批准动作或阻塞事项。

本地取回交付包并校验SHA一致：[/tmp/bgem3-plugin-slim-20261105-delivery.tar.gz](/tmp/bgem3-plugin-slim-20261105-delivery.tar.gz)；[完整补丁](/tmp/bgem3-plugin-slim-20261105-delivery/plugin-full.patch)。最新本地schema、三阶段身份与两份实验文档链接检查通过。未重复项目级全局检查（此前其他模型/既有过程材料已有无关失败，未修改这些文件）。
