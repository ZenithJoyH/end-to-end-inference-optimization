# env-035：Plugin上游main+PR455与FlagGems-vllm更新

2026-10-20后续正式组合验收：[acc-017](acc-017-full-gpqa-ple-fixed.md#终态177198通过正式阈值7条60k问题仍存在)沿用该版本基础及后续私有FP32/i64/QSA M16/051 PLE改动，177/198（89.39%）通过0.88阈值、原生gate核验通过。只证明绑定的当前完整组合，仍7条60K reasoning-only，不将旧安装版本或本次通过等同未打补丁上游独立通过。

2026-10-19用户明确要求更新当前容器Plugin到flagos-ai/vllm-plugin-FL，拉取PR455，并更新FlagGems-vllm。范围为PPU-07/qwen3.8-flash-opt-ppu07-20261015；只环境安装/CPU静态及导入检查，不重启/热切换8010、不访问8035、不发模型/GPU算子请求/全量GPQA、不升级Torch/FlagTree/vLLM/权重/FlagGems。旧034 FP32/i64/QSA M16源码及运行实例保持，当前19/C8通过不绑定新版本。

## 执行前事实和方案

- 默认新Python Plugin editable实际/workspace/vllm-plugin-FL-qwen38-adaptation，HEAD939600b3且有既有模型/runner/slot补丁；metadata版本0.0.0+g2b2fe95e2与HEAD不同，以实际源码为准。运行8010实际是private034（model9ce7d6ca/旧FP32+i64/M16），两者不能混称。
- 默认FGVLLM editable实际/opt/qwen38-fgvllm-main-20261016-6568039，HEAD65680392、version0.3.0.dev1，有已验证PPU QSA M16私有补丁。旧源码不变，避免运行worker惰性导入混用；Gems private017 i64不改，默认FlagGems安装也不升级。
- 上游只读ref核验：Plugin main a696859b9aa528dfd5b21f5da3403fdc16bac4cd；PR455 head3cb373b11a81428c42ac5dd63348a00ee84f7863，merge ref053d8f71390a35ced02811a813ac3df5ca5bf11a；API state open/merged=false/mergeable=true、base_ref main/base_sha ca6fb176ba704e0022736fd143539cef017032ee。FGVLLM main b4d3382bb04da4e0ab444849697865b4d5fcd86e。网页工具辅助阅读，精确refs/父链以目标git核验。
- 新任务目录BASE/environment/env-035-plugin-pr455-fgvllm-20261019（BASE=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container）。先保存default安装/源码/必要editable元数据、034运行身份/关键SHA/镜像挂载，然后在新external source stage fetch上述固定main/head/merge；确认main包含关系，能直接使用已存在上游merge则用它，否则只在新工作树整合PR差异，不生成/推送任何新提交。冲突不以整树覆盖或擅自放弃保护解决。
- 安装在未挂载的新/opt私有副本，保留旧副本；记录Plugin与FGVLLM新的AGENTS/pyproject、ABI及QSA/精度保护差异。必要保护能等价兼容才迁移；无法兼容则报告确切阻塞，不谎称新版本已验证。先静态/CPU检查后pip editable --no-deps --no-build-isolation，仅更换两包安装绑定，依赖不自动升级。旧metadata按清单备份、重复editable精确核验，不删源码或清缓存。
- 当前服务不重载，显式PYTHONPATH仍指旧private034和旧FGVLLM；升级仅影响后续新进程默认安装，不宣称在线模型已用新版本。共享start-model.sh不自动覆盖；后续服务切换/graph/精度验证需新范围。

完整原始日志/补丁/git refs/metadata/安装与回退回执保存在远端env-035目录，本地仅摘要与SHA。PR作为用户指定依赖，不向PR写入任何内容。pr_readiness=experimental，无新精度gate/性能结论；旧164/198 failed/no gate不改，monitor维持PAUSED。

执行前命令：BASE/commands/env035-prepare.py SHA `9d2bafd2304019a002aa5c24652aacaa4c03f755385a6e5480e874a04d96897e`。Host执行仅snapshot+fetch到新E/plugin-source与fgvllm-source，不安装/改旧代码/重载；固定refs不是浮动pull。若上游merge-ref不含冻结main，则在新staging main上`merge --no-commit --no-ff PRhead`（临时命令级identity、无新提交），冲突保留并停止；完整代码及AGENTS/依赖随后由主Agent阅读。旧依赖默认安装与运行034都保留。

## 安装前冻结

fetch完成：上游merge-ref不含冻结main，故新staging在a696859b上无提交合并3cb373b1，合并无冲突，无新commit。FGVLLM b4d3382已上游原生包含PPU minimum M16（单CTA/split共用实现），不再移植旧QSA算子补丁。两个新私有安装目录为`/opt/qwen38-plugin-pr455-20261019`、`/opt/qwen38-fgvllm-main-20261019-b4d3382`；旧source不变。

PR模型已由单文件改成package，旧诊断埋点不盲拷。仅将034数学保护移植到新`gpu/tp_reduction.py`：BF16显式TP先FP32后BF16；实例绑定MoE late reduction且精确保留SP/TP/EP/pre-reduced/trunc/native非BF16 guards，不改vLLM类或engine源文件。此为本地实验保护补丁，并非PR455原生内容；不声称新栈模型/graph通过。private017 Gems两文件保留原字节且安装不升级FlagGems；新服务仍需显式保留原private017导入路径。默认Gems安装未改，不能混称默认已经i64。

执行前冻结BASE/commands下：`env035-install.py` SHA8aaa0f8f1ba09571c5814d49e3986394fc205bc7683d9c1020d69cbe6b54fda3；`env035-tp-reduction.py` SHAedab47370cb009926b82fd8c900467a3fbde14f084e08a7a3b68644afdb76349；`env035-model.patch` SHA4eb43c9410415928736de08a997cb7d8cf36fc9711349b9548536e68b2fd611c；`env035-cpu-check.py` SHAa40f7c7c36b992b9bc4fde84a2ef110fe17006b3b5e43786ed09669ce618d76b。先校验旧源码与默认绑定、8010同身份/空闲counter、精确备份两包metadata，再复制私有树/patch/compile/CPU mock契约，才pip两包no-deps/no-build-isolation。任何失败停止、保留日志，不自动重启/升级依赖。pip不会让已有PYTHONPATH覆盖的8010切换新版。

首次安装：54项CPU mock契约通过、两树compile通过；pip Plugin在metadata阶段拒绝`VLLM_VENDOR=thead`，未卸载/切换旧包。新setup.py仅cuda值构建native扩展，值为空走官方纯Python安装，因此下一命令显式`VLLM_VENDOR=`，不是伪装CUDA平台或改代码。原失败日志保留`E/pip-plugin.log`。scp返回0但远端未落盘，实际用SSH stdin排他写入且SHA吻合；此前未执行安装。续行命令`BASE/commands/env035-install-resume.py` SHA `ccf74062d6a01f213e6b4a6fce654736f8429619436a0bd1edc3136ffd3aa990`，先核旧绑定/源码不变再只安装两包，无依赖升级/服务操作；安装元数据原tar已保留以备回退。

两包安装成功，`INSTALL_FINISHED.json` SHA c701cc7d95a81e8214b5479ebdceefe4ac07f251cc9cf603bec63c2d399c06f6。default及env-u-PYTHONPATH两种新进程find_spec均命中新目录；Plugin metadata0.3.0rc2.post1+ga696859b9.d20261019（metadata仅HEAD信息，完整组合以main+PR+本地补丁/treehash为准），FGVLLM0.3.0.dev1/headb4d3382工作树clean。vLLM/Torch/FlagGems版本与origin未变，所有旧source Python SHA/critical保护未变，8010同API1767049/start509637043/health200且prompt9356/generation3328不变。

CUDA_VISIBLE_DEVICES空的实际包级导入成功且QSA来源为新FGVLLM _thead；直接model导入触发vLLM能力查询在隐藏卡时失败，不当作模型服务故障。接下来保存`BASE/commands/env035-terminal-audit.py` SHA8242091921f9ee72aa39b5500034f222c3de56e1815ce8a3f99671459f95d96a：仅新Python进程CVD8/private017 Gems、正常register_model及模型模块导入，不加载权重/构造GPU tensor/推理；核QSA真实函数对象M16及本地FP32helper来源，冻结完整newsource manifest/上游PR和本地diff，再核旧source/8010计数，记录缺失/失败，不自动修改依赖或服务。

## 终态

- 两包安装及实际导入成功。Plugin新模型路径`/opt/qwen38-plugin-pr455-20261019/vllm_fl/models/qwen3_8_flash_next/gpu/model.py` SHA f4be1dae518e5b89655d9a0668ef5c585c661709c66e0002ac5a795bc01067a6；本地helper SHA edab4737。主进程普通注册后模型模块可导入，未加载权重、未运行GPU算子/模型。上游FGVLLM包`vendor_name=thead`，实际导出QSA函数指向`/opt/qwen38-fgvllm-main-20261019-b4d3382/src/flaggems_vllm/runtime/backend/_thead/fused/qsa_attention.py`，函数体`min_block_m=16`、SHA3bb3d083，与旧已验证特化字节相同；这仅是函数来源/静态M16证明，不是本轮kernel hit/graph replay。
- 默认及清除PYTHONPATH两种新进程均命中新Plugin/newFGVLLM。完整源码组合、上游PR staged diff和本地FP32 diff冻结于`E/source-after.json` SHA aadb4d922e1728b2629a0ac0d01644be9ebb7528ed603d37809ee3a5843ad2d9；PR MERGE_HEAD为3cb373b1、HEAD为a696859b，无新提交；FGVLLM HEADb4d3382且clean。`model.py.orig`只是patch产生的新副本内原始备份，不改旧live tree。
- `E/model-import-target8.log` SHA7a2121ca96071e5f9d073f3bab1c6a7ca05f19b8a054a87f7df90f4572a8ab10：正常register_model与目标模型模块导入rc0，private017 i64真实来源确认；PPU没有vllm._C的warning保留，不将仅import成功称TP8/graph/正确性通过。CPU mock54通过同样不替代真实通信/模型精度。
- `E/TERMINAL_AUDIT.json` SHA **804912822678ef2c2f84c2c3f1947e2a1c29a662e89170938d7aec077a11dafa**：旧defaultPlugin/旧FGVLLM/live034每个Python文件、017 i64两文件、旧M16关键SHA全部不变；8010API1767049/start509637043/argv5744d999保持，health200、running/waiting0、prompt9356/generation3328不变。0重启/0推理请求/0模型评测，未访问8035或改共享启动脚本，未升级其他依赖。
- 当前在线模型仍034旧private环境且旧诊断埋点仍在；新安装仅后续新Python进程默认生效。后续切换要清除旧Plugin/FGVLLM显式PYTHONPATH覆盖、保留private017 Gems且重新验证服务/graph/最小回归，不能直接复用034精度结果或历史gate。未另行启动/重启，monitor PAUSED。

回退准备（仅记录，不执行）：两包原editable安装元数据精确备份`E/install-metadata-before.tar`，原源码及其dirty补丁均未改。若用户要求恢复默认绑定，可在不改变依赖下分别以`VLLM_VENDOR=`和`pip install --no-deps --no-build-isolation -e`重新绑定`/workspace/vllm-plugin-FL-qwen38-adaptation`及`/opt/qwen38-fgvllm-main-20261016-6568039`，再核find_spec/direct_url和服务绑定；不要解包覆盖全部site-packages，不停止/重启容器。本轮pr_readiness=experimental-local-protection-patch，非PR提交；无正式精度gate、无新性能结论，旧164/198 failed-score/performance blocked保持。
