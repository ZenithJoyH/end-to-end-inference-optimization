# refactor-001：跨库职责和运行时规范整改

## 当前验证状态

监控更新（2026-11-04T20:32:44Z）：无新性能轮次/精度或GPU试验，源health200。已mode=ro定位FG TunedConfig_metax_triton_3_6.db：linear最佳配置57键（align32 M/N/K+dtype），benchmark_v2 1230行（原始shape+dtype+协议），无时间戳不能从rowid断言r6实际miss。发现GateLinear缺配置桥后做op002薄OOT草案，本地/远端6项CPU接线通过、Ruff0.14通过，但进一步对照证明该NativeGate fallback整改前已存在，故暂缓且未安装，不能当整改回归根因或性能修复。已准备未改C20的native限步profiling草案：P32K/D1K/C64/N128，原r6 seed391728，1100步后最多8步/8rank、关闭shape/memory记录；客户端dry-run通过，生命周期/恢复脚本尚待冻结，未启动。P2三正式与TTFT20.66%incomplete、B/R缺失结论不变；源源码/脚本未改，下一步优先取实际Mixed trace。


历史accuracy01结果（旧实例）：GPQA198/198完成，strict165/198=83.3333%达到80%阈值；flexible63/198仅作原生另一filter报告。两个filter各198唯一ID、396行逐行核验，native gate及identity-after通过，无OOM/非法访存。已评测候选实例已停止，源服务仍恢复启动；性能尚未开始。


当前组合为 candidate19：公开量化320项GPU和冷graph检查、模型7/7 FULL捕获/真实FULL区间replay及22/22 C1/C8/长输入回归均通过。正式GPQA198题已完成，strict165/198=83.3333%达到冻结80%门槛，两个原生filter各198完整唯一题、396样本行及gate/identity-after均已核验。

该分数绑定已结束的隔离候选实例，源源码未交付。源服务13:04:57Z已恢复health200；本轮启动前再次通过实际argv和独立算术smoke、空闲检查，随后按用户授权暂停。当前performance01协调器1152217/ticks1210944076正在启动新候选服务，后续按冻结C→B→R/P1K-P32K/5预热+3正式执行；尚无性能数据。新候选使用正确设备标识和共同缓存策略，先原生性能schema校验及新正式GPQA，再测同一实例。结束后由同一协调器恢复原服务。实时状态及证据见state与[refactor-003](refactor-003.md)，以下保留执行历史。

## 优化方向与瓶颈依据

用户明确授权整改review-001其余问题。refactor-001负责14数值kernel及相关私有调用迁入FGV公开API/统一dispatch；refactor-002负责框架workspace/通信组生命周期、原子注册和量化能力前置校验。保持原数值顺序、MetaX默认YAML及启动参数，先在独立clone验证，不影响当前服务。

## 优化内容与适用边界

当前准备隔离环境。源deepseekV4-flash，clone deepseekV4-flash-refactor-20261104，源码在容器私有层；目录映射必须逐项相同。变更前保存三库HEAD/index/SHA/补丁及源码归档。commands/prepare-refactor.py SHA `b29906b8848ba35b373f60653ec0f2c4941bde8b3d6c8e0a8bf8e531fd8f40b2`。

## 正确性与路径命中

待实际契约/公开入口/独立reference/更新输入graph至少两次验证；高风险整模需正式GPQA及同workload性能护栏。当前服务占用8卡，先完成CPU/代码整改再进行必要GPU资源调度，不争抢设备。

## 性能效果

not_run，无新性能收益或OOM修复结论。

## 决定、风险与回退

待验证；不改vLLM/编译器，不提交/推送，不因迁目录丢弃能力guard/数值兼容。算子API发布及公开依赖固定需如实标为尚未发布，不虚构Commit。

## 外部证据

/public-flash/jinghao/deepseekV4/20261104-dsv4-metax104-plugin-review/refactor01

执行前补齐原生挂载核验脚本复制，prepare-refactor.py最终SHA `923fd320a03075ee83b653369bc7c060f31c8007e670b394659d1acecc063b01`；verify-container-mounts.py SHA `32adacf39859e88ad6e2dad04ada248a00b636c795fed67d34328f5264bec3e3`。

## candidate01 执行前记录

隔离完成：clone `3104fd968efc2b41c939d9dd778599e8467ea8698edd657dbc1f47904a4c3256`，快照 `sha256:b39dc2a2bc6374320225dcb349460fa78d032a85d6e8295024192ed7e9c0ef89`，lineage verified/mount parity passed。原服务未动。

- 远端 `refactor01/commands/migrate-numerics.py` SHA `ef7a401763bdd063a91dbb0b9a8ccd7e0897b130fd9d72dda013327b2346f274`。
- 远端 `refactor01/commands/refactor-runtime.py` SHA `84acde30592af64a92da34b0aa537010fd2407d0d2aa4d73280402aed7346d2c`。
- 远端 `refactor01/commands/connect-public-api.py` SHA `0095687860fe90012ecad762f371588e05e50c47cf82d7e00a08cc4222a409cb`。
- 远端 `refactor01/commands/install-candidate.py` SHA `c106181ddbd80f7532317a65790dc08a0e1f10f87ba1abd79592450815bc0c23`。
- 远端 `refactor01/candidate01.tar.gz` SHA `270efad8e6410aeba165a25b14ceac33857bc2fe06e536997861564c78ef1c54`。
- 远端 `refactor01/candidate01-manifest.json` SHA `05e6fdb6615692eb65905604be0af4afde92ac61a1d7e487c6fce4242c4b29e3`。

将先安装隔离clone私有源码，逐项验证导入/API/故障回滚；当前还没有GPU数值、graph、正式精度与性能结论。

补齐MoE/GEMM统一dispatch及平台能力限域后的执行候选为candidate02；candidate01仅上传未安装。

- `refactor01/commands/finish-bridges.py` SHA `2e52f0c32aaddad5e5b9b3c6cc8e7f02e2f27e11c25293a08cfe4c883ff2416f`。
- `refactor01/commands/install-candidate02.py` SHA `01fbd10015a549c2d656d14f271a7c59a92da50492d9492cb829f44e25dc0aa7`。
- `refactor01/candidate02.tar.gz` SHA `a60c45c4d1dc714c2e54785f67eaa3ff1081be5d56105951a23c87bf3536f3c4`。
- `refactor01/candidate02-manifest.json` SHA `7c71e8dc1898171506bb3bcef9b373891dedc5df0e2b0cae8baa0f030684c2fb`。

CPU导入/实际registry命中检查脚本 `refactor01/commands/import-check.py` SHA `026e8399081108919a1688ed0ca314323008ca6f6f610dd2a4e96fd3cfc6640f`；只导入/选实现，不启动GPU执行。首次安装调用发生在上传完成前，文件不存在、零源码变更；上传结束核验后续执行。

## 独立检查发现的 Top-k 边界缺陷

历史`vals>=threshold`后按位置截前K会漏掉阈值之后的更高分项。例如1024分数前1023项0、末项10、K512，原代码会取前512个0。候选先保留所有`>threshold`，再取最小索引的同分项，两级归约均修复；新增独立CPU Golden/GPU实际执行与两次更新输入replay测试。此处属于数值行为修复，未把静态推导当GPU通过，必须执行正式GPQA。

## candidate03 执行前冻结

候选修复普通函数扫描漏导出pointwise对象的问题；通用MLA公开符号保持原样，新增明确特化API。manager原子发布新registry，选定MetaX依赖失败不再被发现器吞掉。保留旧candidate02导入失败和11 passed/1不符合现场假设的CUDA-context断言失败；修订后以零Torch GPU张量分配为CPU资源守卫，真实context状态单独报告。

- `refactor01/candidate03.tar.gz` SHA `7d4fc4dcd30ef6e0e3860153892fa722f1a108fc3dcda5fa5802942a021de749`。
- `refactor01/candidate03-manifest.json` SHA `886b704e054b4544faa0ac954e3e315cf3e6be251ef8a5bac80333de5d1f69cc`。
- `refactor01/commands/refine-candidate03.py` SHA `841d905c08c405f29a91c2a4316d68040d9e3ba5885220c598e9c201c3d2eb5e`。
- `refactor01/commands/repair-topk-ties.py` SHA `d3ee6cfa0dc28239d5108c23d8b19da0f953bb56e528e1e7f5aeaa0210c5a7f9`。
- `refactor01/commands/install-candidate03.py` SHA `6d96320dd431d2f20b0fe29876724662b0f6b3fe68035df5705d45eaff91ec4c`。
- `refactor01/commands/import-check03.py` SHA `321f63d8cd3c7919277ca29b82b087ec6b9deb2fefd219467558fc537fa0a7ea`。

## candidate04 执行前冻结

候选修复普通函数扫描漏导出pointwise对象的问题；通用MLA公开符号保持原样，新增明确特化API。manager原子发布新registry，选定MetaX依赖失败不再被发现器吞掉。保留旧candidate02导入失败和11 passed/1不符合现场假设的CUDA-context断言失败；修订后以零Torch GPU张量分配为CPU资源守卫，真实context状态单独报告。

- `refactor01/candidate04.tar.gz` SHA `a1240793be223c5c9d71edbbe288ab19b9be6e89c39a081a8eac30cfdd6c90b2`。
- `refactor01/candidate04-manifest.json` SHA `4c3ab47919ad933be4a7dac926e1cdd0cd376e62b4b82e716ae069e7b75aecb8`。
- `refactor01/commands/finalize-candidate04.py` SHA `d8e58c6b143b7d0392a2fd0505508ec49c1ec35b123d042b0419f78020d20874`。
- `refactor01/commands/install-candidate04.py` SHA `a6db075c9b426811b8523511ade30c14ace6a5fbcd19080b5f274f41466ccae8`。
- `refactor01/commands/import-check04.py` SHA `27ea8cb1272389c5d37ac8e406cecb9ba9fad86000ba66f15826bb52ebbe292f`。

候选04公开入口/真实派发通过，35项CPU回归全部通过（无skip）。后续补齐indexer BF16原生GEMM和解量化的统一dispatch，移除未使用的FG模型私有masked-fill捷径并复用既有公开ATen实现；两个模型调参JSON全部27项SPLIT_K=1且其余tile字段不传入MCTlass，因此删除无效JSON，仅保留原生get_config覆盖和厂商实际选参。更新后仍需扩大回归，不用旧35项通过替代最终候选结论。

2026-11-04T23:20:07Z 当前组合C20正在performance03共同输入准备回归：5完整准备批次640成功0失败，P32K第三准备批进行中，正式0轮，未见推理OOM/非法访存。source按本轮授权暂停、原8310源码未交付；唯一main负责恢复。当前详细证据与所有历史失败仍见同一[op-001](op-001.md)及state；此前compile诊断为历史阶段，不代表当前仍卡启动。仅P1K/P32K工程范围，尚无完整B/C/R收益结论。

2026-11-04T23:55:47Z：P3六准备批768/0后正式dryrun因新增Python-I同级模块导入失败，0正式，已按guard恢复源并独立8310SHA/8GPU核验。仅移除nativeperformance/compare入口多余-I，完整三角色nativeplan dryrun+comparehelp/旧TTFT超限停止守卫CPU通过后，唯一P4已启动候选activation。代码C20/模型参数/阈值/共同准备协议不变；无模型OOM。当前源由P4授权暂停/后续finally恢复，仍未交付，最新详细证据见[op-001](op-001.md)/state。

2026-11-05T01:10:27Z：当前P4候选P1K哨兵5预热+3正式原生全部完成1024success0fail，output/medianTTFT/medianTPOT正式spread0.5591%/0.7234%/1.1478%均<10%；完整每轮指标/SHA见[op-001](op-001.md)和state。目标32K已由真实nativeCLI P32768/D1024/C64/N128/seed391723进入首轮预热，0完整正式，B/R未开始，不报整改相对收益。API/driver精确live/health200、actualargv OFF/.85、无OOM/非法访存；source仍P4授权暂停/未交付。旧P3导入错误不再阻塞P4，未改数值或阈值。

2026-11-05T02:14:21Z：P4候选32K已5预热+1/3正式，首正式128/0、output217.542522tok/s、medianTTFT8715.869538ms/TPOT274.310832ms，末2预热outputspread0.07646%满足原准入。第2正式进行中；B/R未开始，不能报完整三轮/整改相对收益。详细每轮SHA和历史慢轮见[op-001](op-001.md)/state。API/driver健康、无OOM/非法访存，源仍授权暂停/未交付；参数与阈值不变。

2026-11-05T02:38:13Z 用户要求“32K跑完就停”已执行：候选P32K三正式各128/0，output217.542522/217.864058/217.512040tok/s，medianTTFT8715.869538/8679.770780/8194.677815ms，medianTPOT274.310832/274.222906/274.556505ms；轮间spread0.161816%/6.004672%/0.121613%均<10%，无推理OOM/非法访存。原source恢复并独立health/5+7smoke/原argv/OFF/.85/8310SHA/8卡验证，clone模型退出。B/R未启动，候选未交付，不报告相对收益/完整验收；当前整改与回归按用户指令暂停，heartbeat已删除。详见同一[op-001](op-001.md)及state的原生SHA/边界。
