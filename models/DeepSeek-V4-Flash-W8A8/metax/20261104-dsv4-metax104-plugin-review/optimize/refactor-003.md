# refactor-003：FlagGems / FlagGems-vllm 改动收敛

## 当前状态（2026-11-04，candidate19）

监控更新（2026-11-04T20:32:44Z）：无新性能轮次/精度或GPU试验，源health200。已mode=ro定位FG TunedConfig_metax_triton_3_6.db：linear最佳配置57键（align32 M/N/K+dtype），benchmark_v2 1230行（原始shape+dtype+协议），无时间戳不能从rowid断言r6实际miss。发现GateLinear缺配置桥后做op002薄OOT草案，本地/远端6项CPU接线通过、Ruff0.14通过，但进一步对照证明该NativeGate fallback整改前已存在，故暂缓且未安装，不能当整改回归根因或性能修复。已准备未改C20的native限步profiling草案：P32K/D1K/C64/N128，原r6 seed391728，1100步后最多8步/8rank、关闭shape/memory记录；客户端dry-run通过，生命周期/恢复脚本尚待冻结，未启动。P2三正式与TTFT20.66%incomplete、B/R缺失结论不变；源源码/脚本未改，下一步优先取实际Mixed trace。


历史启动记录（13:26Z，已被上方进度替代）：performance01已启动（hostdriver1152217/ticks1210944076），正在候选activation；源上一轮13:04:57Z已健康恢复，本轮独立argv/smoke/空闲核验后再次按授权暂停，源码/脚本未变。计划C→B→R，P1K/P32K均D1024/C64/N128，各5预热+3正式；新候选先性能schema及实例绑定精度检查。所有测量尚未开始，不提供虚构性能值。

历史accuracy01结果（旧实例）：GPQA198/198完成，strict165/198=83.3333%达到80%阈值；flexible63/198仅作原生另一filter报告。两个filter各198唯一ID、396行逐行核验，native gate及identity-after通过，无OOM/非法访存。已评测候选实例已停止，源上轮已恢复、本轮授权暂停进行回归；性能测量尚未开始。


候选只安装在 mx-104 隔离容器 `deepseekV4-flash-refactor-20261104`，源容器源码尚未交付。算子检查通过；candidate18 模型启动在 decode-only indexer 的 Python 变量作用域处失败，未进入 GPQA。candidate19 仅修复控制流，6 项 CPU 回归及公共 API 检查通过，数值库 SHA 不变。

`model-validation02`已完成7/7 FULL Decode graph捕获，真实请求的单统计区间FULL replay计数164（另有其他区间），22/22 C1/C8/长输入回归通过，health200，KV实测557700 tokens/.85/prefixOFF。旧日志措辞审核失败保留；finalizer03改用原生完整捕获记录和区间replay计数，运行时取证通过，未改源码/采样/评分。正式GPQA198/C64/默认采样/thinking ON/prefix OFF已完成，strict165/198=83.3333%达到冻结80%门槛；gate及identity-after通过。

模型01后源服务曾按原argv、容器默认环境及脚本3exports恢复并通过推理；原交互式完整环境未保存，不宣称字节相同。模型02捕获当前源实例环境仅存内存，该轮已恢复原服务；当前performance01再次独立租用GPU，结束或失败后按原参数恢复并追加service.log。源源码未交付；精确进程和原生回执见state/model-validation02。

- FlagGems 对 HEAD 仅保留 5 个生产 Python 文件：ATen pad/zeros、MetaX MM/addmm 和 GEMM 配置归一化。已转至 FGV 的融合实现及其重复改动恢复 HEAD。
- FlagGems-vllm 对 HEAD 有 20 个现存生产 Python 文件变更，以及 3 个生产文件删除。它承接 Plugin 的 14 个数值 kernel；重复的 fused 导出和 MetaX 量化内核已撤掉。
- 按用户建议，量化经 dispatch 直接调用根包公开 `flaggems_vllm.scaled_int8_quant`，复用既有通用内核。没有保留新 SDK 桥接或自定义 SDK 量化模拟。公共 wrapper 补齐布局、空输入、设备、参数和 NaN 整数转换契约；MetaX 标准 YAML 为现有内核提供单个 launch 配置，避免 graph 捕获期间 autotune 同步。

| 验证范围 | 已核验结果 | 限制 |
|---|---|---|
| 当前公共量化路径 | 320 项 GPU 测试通过，0 fail / 0 skip；含独立参考、dtype/layout/empty、BF16 位型及更新输入 graph | 本轮正式GPQA已通过；端到端性能待测 |
| 冷调参缓存 graph | 相同 Prefill profiling → 未预热 Decode capture 用例通过，2 次新输入 replay | candidate17 原失败完整保留，不等同于历史 OOM 修复 |
| 未再修改的其他算子 | MoE 111、gather 7、QNorm 74、FG ATen 36、sparse/reference 35 通过 | 按实际代码 SHA 关联各轮原生证据，不冒称同一次模型测试 |
| 量化 benchmark | 同一原生框架、30 shapes 的 SDK / FGV graph 对照完成 | 最终固定配置仍有回退：M4096/K13824 为 0.241 / 0.197 ms；M64/K4096 为 4.450 / 2.587 µs。不是端到端结论 |
| C1/C8/长输入、模型 graph、正式 GPQA | 22/22最小回归、7/7捕获及真实FULL replay通过；正式GPQA原生请求已启动 | GPQA198/C64/默认采样/thinking ON/prefixOFF/strict阈值80%；实际165/198=83.3333% |

当前算子、模型最小回归和正式精度已通过，仍待端到端护栏及非 MetaX CI 验证，不能宣称整体 PR 就绪或性能验收通过。回退材料、命令及 SHA 保存在本记录对应远端目录。以下保留初始设计与各候选的执行历史，旧候选状态不能当作当前状态。

## 优化方向与瓶颈依据

用户要求先收敛两个算子库、满足当前算子规范，再开启精度验证。按公开计算契约分工：FlagGems 只保留 ATen pad/zeros/MM/addmm 与 MetaX 配置归一化，共5个生产Python文件；已改由FlagGems-vllm接入的cp_gather、QNorm/RoPE、Top-k及其FlagGems测试恢复HEAD。删除未使用的私有masked_fill捷径和模型GEMM全局开关。

## 优化内容与适用边界

FlagGems-vllm承接14个Plugin数值kernel及融合接口，MetaX专属实现位于vendor/ops，框架仅持workspace/通信组和metadata。复用现有标量SiLU clamp及portable prefill Top-k；撤回当前未使用的gather回补、fused_moe导入和code_cache修改。旧GDN编译器monkeypatch彻底删除，不恢复其import副作用。保留旧补丁与HEAD字节来源于远端归档。无vLLM、编译器或权重变更。

## 正确性与路径命中

candidate05执行前：FG的7个变更Python（5生产+2测试）、FGV的24个变更Python按各自仓库Black/isort/flake8固定版本检查通过。此前candidate04实际导入/dispatch及35项CPU检查通过，仅作历史证据；candidate05仍须重跑扩大CPU、独立GPU参考、更新输入graph至少2次、服务C1/C8/长输入及正式GPQA198 strict-match>=80%。所有GPU/模型验证未执行。

## 性能效果

not_run。无吞吐收益、稳定性或OOM根因结论。计划保持prefixOFF/.85，验证同workload三轮32K及受影响护栏；不能宣称四场景正式验收。

## 决定、风险与回退

只在隔离clone中应用；源模型/源码未改。用户已允许暂停源模型，待最终CPU检查通过后执行，验证后按原配置恢复。库API尚未发布，依赖按源码manifest固定，不能伪造上游revision。Top-k并列截断修复和ATen选参迁移仍需真实GPU/整模证据。

## 外部证据与执行前命令

R=/public-flash/jinghao/deepseekV4/20261104-dsv4-metax104-plugin-review/refactor01

- `candidate05.tar.gz` SHA `90b01a821dc500df850f716711d3e5c5b47fd7b37c828c2f489d3d651bb0f07e`。
- `candidate05-manifest.json` SHA `1e088f91d6ed377846e3d9d95a35ae78b2a404c79d4ea112dd34aedbc3bb95d2`。
- `commands/install-candidate05.py` SHA `bcff889083d60750794ea231b0c6f13d547772cb9bbf41a0c22c0c70b46f6d97`。
- `commands/import-check05.py` SHA `8180a37456f64d5352fc820d74a0ed56bb5e450df1c3ebfe78286fc1cf5f8aed`。
- `commands/package05.py` SHA `98de6b4f80b42cfddc993a0b1f76218cbd29f08f25e9af06c034b24922686af8`。

扩大CPU检查脚本 `refactor01/commands/cpu05.py` SHA `b4236e2dddd7ea3a9c98a23cb1e859aa6f3547cdcb8d6b22f535d5532a13a26f`；先API导入，再Plugin派发/registry/配置及FG配置/FGV公开元数据检查。

扩大CPU首轮149 passed/1 failed：旧call_op集成测试仍要求执行失败后跨后端重试，与算子规范D1冲突。调整该测试为异常原样传播且第二实现不调用，生产代码不放宽。脚本 `commands/fix-cpu05-test.py` SHA `762fc61e73054a1a58fa4fb4196b74d0b00c549fc922e2a91d091e6441878cca`，只改clone测试文件；首轮XML/日志完整保留。

修正后同范围检查脚本 `commands/cpu05b.py` SHA `650bddc2ca675b3e36f9a0b3f1890aed77d98a58058ab8263850704b32c672b4`，结果candidate05b-*不覆盖首轮失败证据。

## candidate06 执行前收敛

删除自建compiled-launch缓存，dynamic INT8改用FGV既有libentry入口；不再新增旁路launcher。GPU graph测试补齐输出sentinel，新增ATen addmm尾部独立参考。扩大Plugin重检150通过，FG/FGV部分仍在运行；本候选部署后检查新公开量化入口。

- `refactor01/candidate06.tar.gz` SHA `912b33ba25a86bc8f2dd6140970c99d85e50855a54918b36f9afdaa0364f300c`。
- `refactor01/candidate06-manifest.json` SHA `68ec2f37fcf3408959e50d140cf08444f8881c9052b865848cd3e91777c9c11b`。
- `refactor01/commands/install-candidate06.py` SHA `b212943a5167d4ea90a20fe77d6c78801827134219d720122ab608de97d4ef52`。
- `refactor01/commands/import-check06.py` SHA `3474267fe7e9e5f85eeff45877d0f66c67188fb7b606a30dd9d358f4a5ed20c5`。
- `refactor01/commands/package06.py` SHA `12b6513daee674620ed0159e62ae8aaa2fcde5532667dd5a9c67176cef5f33b7`。

## GPU验证执行前冻结

用户已明确允许暂停当前模型服务。精确端口/PID/startticks/子进程和空闲指标守卫；仅SIGTERM模型进程，不停容器。原环境仅保留在协调进程内存；无论GPU检查成功或失败均恢复源API原argv/env，确认health200。GPU检查为公开接口、独立参考和新输入replay，不是模型精度。失败保留原生日志/XML并停止后续模型晋级。
- `refactor01/commands/gpu06.py` SHA `5f8db26d8785b4984401eb1709bf064110cda7b50e32ccbd9cc269533b5a511a`。
- `refactor01/commands/lease-gpu06.py` SHA `6e334def3cb879b0f2b331aedb20b051a04b8caaa5511b0f9442a8f42fd23b19`。

启动方式：宿主python subprocess.Popen执行已保存`commands/lease-gpu06.py`，新会话、stdout/stderr到`lease-gpu06-driver.log`，精确PID/startticks到`lease-gpu06-launch.json`；不重复启动。该协调器会自动停止本次空闲源API、串行公开GPU回归、finally恢复原API并保存ready。

## 诊断 FGVTK-001：公开Top-k导出覆盖

模式minimal-regression，gate-blocking。candidate06 FG32项GPU通过；FGV sparse首轮11通过/1失败，宽513、输出stride520的padding canary被改写，原生XML/日志`candidate06-fgv-sparse-gpu.*`完整保留。源码检查表明SpecOpRegistrar依次注册ops和fused，旧_metaX/fused重复导出覆盖新ops接口；旧接口直转generic，未处理非连续输出。当前为机制有支持的原因，修复后仍须同一用例/路径取证闭环。不是模型GPQA失败，也不是用户OOM根因。协调器自动恢复源服务，等待ready核实。

按inference-accuracy-diagnosis冻结现场，停止性能与全量GPQA晋级。候选仅移除重复fused公开导出，保留旧未改数值实现文件；统一从vendor/ops进入，测试明确检查该模块归属而非只判断含_metax。补齐新API的conf/operators.yaml和测试marker，以及mhc公开默认参数/更新输入graph参考测试。

## candidate07 执行前冻结

- `refactor01/candidate07.tar.gz` SHA `c4641e31810ac91bb03394cd26a7a98d6adf663b0a1c1bd677fcb3eb2ac93d21`。
- `refactor01/candidate07-manifest.json` SHA `18e4c6194fae7269312b72e8c2a8a60e2b10116e244b8371d69538c08d9a45d8`。
- `refactor01/commands/install-candidate07.py` SHA `89b4acff30de8df325ddd1ee487c18e7493a158016290c3b881becd79033e983`。
- `refactor01/commands/import-check-candidate07.py` SHA `2979100d28b56dc53bb1be2a17d40cd950b96c8ff19cc0288252a0bfcc1294eb`。
- `refactor01/commands/package-next.py` SHA `842b26cc3ef646adaba9fb099ad81f40b3a7e80bf584c7023e6b2870d54dc204`。

修复后公开模块严格检查通过（candidate07-public-contract.xml，1 passed），GPU同输入边界及完整矩阵仍待执行。FG 32项GPU已通过，代码SHA不变不重复；FGV新增边界/公开MHC/graph覆盖，原失败测试/容差保持。复用精确空闲租用/finally恢复机制，要求上轮source-restored-ready存在；执行下列已保存脚本。Popen启动lease-gpu07.py，新会话，日志lease-gpu07-driver.log，launch JSON记录精确PID/ticks。
- `refactor01/commands/gpu07.py` SHA `d06e50a2b70bbf5274560906b5a67ae7947bfbb2a7b4018568224463f9a0d42f`。
- `refactor01/commands/lease-gpu07.py` SHA `a462ec5789b384b579e4a5f1a6bb162abc8f4f997578460fbe803d8823befd9c`。

## candidate08 执行前冻结

- `refactor01/candidate08.tar.gz` SHA `25bc9d36e9e142c77bf3a4279d323d1d54f2e67d1b1419abac195faa942c8999`。
- `refactor01/candidate08-manifest.json` SHA `c831bb5f1d639f7044fd305fe3104f43384f20a50bcd21a4cc88fccfc5050822`。
- `refactor01/commands/install-candidate08.py` SHA `2b47588f70a169eeed6822225a4f34aab1147cf2ec3c12452c230f0c37df337a`。
- `refactor01/commands/import-check-candidate08.py` SHA `116af60df3c273d7e4e0ea3de69c5b43f14da866d35e3c84db425965e2ec5b11`。
- `refactor01/commands/package-next.py` SHA `842b26cc3ef646adaba9fb099ad81f40b3a7e80bf584c7023e6b2870d54dc204`。

GPU07首轮16 passed/1测试契约错误：prefill_local的生产契约和实际Plugin调用均为KV[N,1,512]，新测试误用[N,512]，在执行前assert拦截。candidate08仅补正确单例KV维度，CPU FP64参考保持[N,512]不变、容差不变，并将迁入wrapper的用户参数assert转换显式ValueError（Python -O下仍生效）。原生失败日志/XML保留。相同Top-k canary已通过，不能以此代替其余数值和整模。

## candidate09 执行前冻结

- `refactor01/candidate09.tar.gz` SHA `02549c4bca6a1b354a485444f63b5a3ce5213fdd7fb3cb7640dfe9040197276f`。
- `refactor01/candidate09-manifest.json` SHA `3026c218b942479c2ccec3d8a5eea76b5b7dec537bc454f04149c233d9a95c6d`。
- `refactor01/commands/install-candidate09.py` SHA `8fb3aee88c51a3e3a321493c272cf689a67b6cca54f673e3b76791d6575cbba5`。
- `refactor01/commands/import-check-candidate09.py` SHA `f693398c7e37a1138a39384a3466badfa1b488fe8e9908a195372c0b674816af`。
- `refactor01/commands/package-next.py` SHA `842b26cc3ef646adaba9fb099ad81f40b3a7e80bf584c7023e6b2870d54dc204`。

candidate08仅打包上传未安装：显式报错生成的两条长字符串未通过原生flake8 E501，保留该包。candidate09拆分报错字符串后原生检查通过，数值kernel未改，使用原candidate07作为实际已安装before守卫。

## candidate10 执行前冻结

- `refactor01/candidate10.tar.gz` SHA `d4e76a982bb55b7953f19b1d8622f032f8218df4ddaa5073ca1a0921747b90f6`。
- `refactor01/candidate10-manifest.json` SHA `7d28c0a8eb48e89dab2c08b9375f00a6887cd0cf34e3c2247806fa3c0c18498c`。
- `refactor01/commands/install-candidate10.py` SHA `6a172957f796a7dc35eb020075440279adadbe7aad5e572c95248f4e91f4ab39`。
- `refactor01/commands/import-check-candidate10.py` SHA `192c628e802745111f0e1ebed700c96f2ec66e262e9ac2009279f07535d11bd1`。
- `refactor01/commands/package-next.py` SHA `842b26cc3ef646adaba9fb099ad81f40b3a7e80bf584c7023e6b2870d54dc204`。

进一步A3复核：QNorm已有FGV MetaX token-tiled优化，candidate10直接迁移该235行实现到vendor/ops，删除重复旧路径，替代之前复制的356行generic版本，保留大/小token两条既有选择；generic仅加动态token边界和显式校验，不复制另一套kernel。删除无剩余导入的旧vendor Top-k代理。新增17/513 token独立参考与更新输入graph，用于覆盖generic/tiled两分支；当前待GPU。candidate08/09均未安装，当前clone还是07。

GPU10执行前：源已由lease-gpu07恢复health200。四个独立进程串行验证既定FGV sparse/MoE/gather/QNorm矩阵，每个suite首个失败止；如其中失败，继续其余既定独立数值接口检查以一次收集问题，不叠加新优化、不晋级模型，最后汇总非零退出并恢复源。原FG32已通过且SHA不变。启动方式同前Popen已保存lease-gpu10.py，新会话，精确PID/ticks写lease-gpu10-launch.json。
- `refactor01/commands/gpu10.py` SHA `81671d2b9ea83ae216ef1c96bfdbc8543a85ba11d4ac4188ea1e94ec1cf16da9`。
- `refactor01/commands/lease-gpu10.py` SHA `2c033718eeeab6ad6d581eaee7162a40ba395658da98f08f50928c2ce5726e3f`。

## candidate11 执行前冻结

- `refactor01/candidate11.tar.gz` SHA `bd1c41c7d29ca0ae9a9fa36a1cea679d10381d5da12d3914a511e58143f213ba`。
- `refactor01/candidate11-manifest.json` SHA `70da4d5d9b6e9d206fcc4070eebf97dc1208fcdcd34388c3a392fe0f921b5249`。
- `refactor01/commands/install-candidate11.py` SHA `ce7ad22f0087f3e20bc949cd2abbeff77b052b0168c90ad1161ba49c8b1b019a`。
- `refactor01/commands/import-check-candidate11.py` SHA `04e5b37fb98d3954b1e916eab13991b8a2c202c70e77c2b42fc6850dc25bc6cc`。
- `refactor01/commands/package-next.py` SHA `842b26cc3ef646adaba9fb099ad81f40b3a7e80bf584c7023e6b2870d54dc204`。

最终候选扩大CPU命令 `refactor01/commands/cpu11.py` SHA `4df4fccb63cd58198a3452558132f3402e49a3f7b279be7a4f3d665b69cf2c1e`，包含新增原生评分前置选择和addmm副作用异常不重试。先安装candidate11并完成该命令，之后才租用GPU。

## candidate12 执行前冻结

- `refactor01/candidate12.tar.gz` SHA `c13098d5a01483fcd890a67a5da086c8fdc150f833c627eace61b48415e92857`。
- `refactor01/candidate12-manifest.json` SHA `be63071391330c08a9542ed95e3f199ec9151289b72ab19f3596813a81ecf83d`。
- `refactor01/commands/install-candidate12.py` SHA `78e2fea9b846f2add602cc221c6f33c1afe48a2405a920c2f75b96232bd9350d`。
- `refactor01/commands/import-check-candidate12.py` SHA `a2d7439d1dd09290f5e93ea91450fe734dbab34898ce400cfa53e7948c39e2a7`。
- `refactor01/commands/package-next.py` SHA `842b26cc3ef646adaba9fb099ad81f40b3a7e80bf584c7023e6b2870d54dc204`。

CPU11：Plugin152全部通过，FG2 passed/1元数据保护测试失败。当前Triton Config的copy协议丢弃自定义vendor属性，因此candidate12在浅拷贝后补全原vars，再只替换kwargs/stages；保留相同断言，不放宽。仅FG元数据一行改动，复验公开导入/FG3/FGV1，Plugin152按代码SHA不变保留。命令 `commands/cpu12.py` SHA `955ea65cac200574c69e562a8a79a6cc903b08f180dd87c34419a65b9ed75d46`。FGV既定GPU10实际通过MoE111、gather7、QNorm74；无skip/非法访存/OOM。

GPU12执行前冻结：FG新增out/注册和addmm失败语义/配置元数据需重跑完整保留ATen矩阵；FGV sparse补正decode测试shape、新公开路由/非有限量化/MHC最小graph，运行全文件，预算每suite3600s/最多3失败后停止。同样不放宽容差或断言。MoE111/gather7/QNorm74的生产代码SHA及测试保持不变，沿用GPU10原生证据。两个独立进程均结束后自动恢复源。Popen启动已保存lease-gpu12.py，新会话、日志lease-gpu12-driver.log、launch回执精确PID/ticks；CPU12三项returncode均0为硬守卫。
- `refactor01/commands/gpu12.py` SHA `f19f5ecb84186885c7b7d18f297aae2c1d961123a475891035bbfdd6bd104c8b`。
- `refactor01/commands/lease-gpu12.py` SHA `56f6bdcf85edcc24c1e82e5ebb524b378ee3221e592c4bd6b5bb39776b5f9566`。

## 精度工具预备（不发送模型请求）

官方镜像已在mx-104。创建独立CPU评测容器deepseekV4-flash-gpqa-refactor-20261104，保留精确inspect；评测工具与原始llmrun共同冻结到refactor01/toolchain-20261104。这里只核对解释器、任务库与数据缓存，GPU数值/最小回归通过前不启动全量精度。工具bundle无模型权重或数据集。
- `refactor01/accuracy-tools.tar.gz` SHA `f89c60acde355ecb37420b20463c893805e6f21937eb2d124c1311a3a7f7b9b8`。
- `refactor01/commands/prepare-evaluator.py` SHA `0195d1108ba54fb5bd3bd2cb298bd70a9445499f5b500ba909a829911d3cf5bf`。
- `refactor01/accuracy-skill-minimal.json` SHA `40605374230efd02ad9b4ba62f379c2b7038d5f9c00025d3c00de3194a34c538`。

## QUANT-NONFINITE-001

GPU12：FG36全部通过，FGV sparse31通过/2非有限量化失败。K4096及13824的7行测试只3个元素不同，位置NaN/+Inf/-Inf，INT8差128；有限零/极小/极大/正负混合在该矩阵q值一致。scales原断言尚未到达，不能声称其已通过。旧文件 `commands/quant-before12.py` SHA `8c7e5e30b7f8306e354910cb06460f5bedbd121550d42448b04a1152dc53003e`，从同一clone旧来源冻结；候选13在MetaX vendor内对齐SDK fmax忽略NaN及NaN转整数0的行为。该机制仍须GPU旧/新/SDK三方取证与BF16全bit-pattern/边界/replay验证；不能据此推定原GPQA或OOM原因。

## candidate13 执行前冻结

- `refactor01/candidate13.tar.gz` SHA `7096a48d351803d0737b9887ed56f3ccc6a69b0a82165fdebdd0fb0d58804806`。
- `refactor01/candidate13-manifest.json` SHA `0c02f83c7a32935c2052f902d35f865fbce47205c452303f6d82618ba7cf3bdc`。
- `refactor01/commands/install-candidate13.py` SHA `539b8200c5c8f7078499e993f179403896070079b5aa66e558379916d4742d0b`。
- `refactor01/commands/import-check-candidate13.py` SHA `dfc5e8a2a953382d9275c5b78b8dc07a5d1f75e4d680400133b1c8e3f238c39f`。
- `refactor01/commands/package-next.py` SHA `842b26cc3ef646adaba9fb099ad81f40b3a7e80bf584c7023e6b2870d54dc204`。

候选13执行前进一步缩小：先只对转INT8之前的NaN中间值置0，amax归约仍保留原实现，不凭推测改其NaN语义。下一GPU命令保存旧/新/SDK的逐行scale bits，再判定amax是否确需修改；补充BM4/BM8和prefill4096行量化分支。

## candidate13 执行前冻结

- `refactor01/candidate13.tar.gz` SHA `b6c6dc76864170eb3d736a5b5fb5cab90971b811ac69cd4f8ca9aa4ffdfe7ca8`。
- `refactor01/candidate13-manifest.json` SHA `e8839963ea6c2c5b754172a1e8a5e95143583029959eebbdc41d0fbac007faa1`。
- `refactor01/commands/install-candidate13.py` SHA `539b8200c5c8f7078499e993f179403896070079b5aa66e558379916d4742d0b`。
- `refactor01/commands/import-check-candidate13.py` SHA `dfc5e8a2a953382d9275c5b78b8dc07a5d1f75e4d680400133b1c8e3f238c39f`。
- `refactor01/commands/package-next.py` SHA `842b26cc3ef646adaba9fb099ad81f40b3a7e80bf584c7023e6b2870d54dc204`。

GPU13冻结：源已由lease-gpu12恢复health200，FG36/sparse31（除量化两项）通过；其余不变。旧/新/SDK同输入9行对照（包括NaN/Inf和零/极端有限/混合微小值）先保存逐行scale bits，再逐K4096、13824检查65536个BF16 bit-pattern常数行；每矩阵需10GiB空闲，异常原样失败，不调低契约、不与源GPU争抢。然后全sparse文件含新增BM4/BM8及4096行分支重检。新coordinator仍使用CPU12同API156项证据，差异仅MetaX量化kernel一条NaN置0，源未交付。
Popen新会话启动已保存lease-gpu13.py，launch回执lease-gpu13-launch.json记录PID/ticks；finally恢复原服务。
- `refactor01/commands/quant-before12.py` SHA `8c7e5e30b7f8306e354910cb06460f5bedbd121550d42448b04a1152dc53003e`。
- `refactor01/commands/quant-diagnose13.py` SHA `37ebfd702216bedf0e37e9ce7fcb4365697da22814120dbb494f506e691eb916`。
- `refactor01/commands/gpu13.py` SHA `9d3b15a85ec157321886eb025852fe5efc6aac8c9773491a1ad7509ad5ebefbd`。
- `refactor01/commands/lease-gpu13.py` SHA `fc718759ea056e220dfe93b30941fdcdac499fbccd0e39e209d1cb6ab7f14f32`。

GPU13恢复身份守卫补齐：health200之外，ss宿主PID必须对应恢复回执的容器PID和同一startticks；写source-restored-identity.json。最终lease-gpu13.py SHA `87bd7c06f897bb5acf8223f47510eb927cec29bac0cd3808f421e24abdf92051`。

评测器准备只执行v2：新容器以root读镜像内已缓存数据，inspect环境项仅保留安全路径白名单，其他值redact；不记录完整环境。`commands/prepare-evaluator-v2.py` SHA `ebb5e2224fe720f4339bbd7a878ac07c302b502125f68e99682f3545a0c39625`，此前v1上传但未执行。

## candidate14 执行前冻结

- `refactor01/candidate14.tar.gz` SHA `48aaace74f9450887391700df36ba7113010e5bc1cf537f1d51e3be761e8d909`。
- `refactor01/candidate14-manifest.json` SHA `ee7196608235fb39ffce9eeaf42667ad44be71f5efd8c5ec5ced83c46fd66790`。
- `refactor01/commands/install-candidate14.py` SHA `95741317c7c780ac51b2613173154ad2838857c29f9b2ce0bd1739a06faf615a`。
- `refactor01/commands/import-check-candidate14.py` SHA `1eeef1e185ee402d28fd341e6cefa4362d2d5f50d22c52d84b21e95453d01e85`。
- `refactor01/commands/package-next.py` SHA `842b26cc3ef646adaba9fb099ad81f40b3a7e80bf584c7023e6b2870d54dc204`。

## candidate14 收敛决定和验证前冻结

QUANT-NONFINITE-001全BF16位型检查失败，旧自定义SDK模拟量化退出候选，保留全部失败证据；改为Plugin dispatch选择vLLM既有MetaX SDK公开桥接，删除FGV自定义量化内核/元数据/对应专属测试。该选择没有新增数值实现，不以SDK对SDK自证正确。新增独立CPU常数行oracle及实际dispatch/graph新输入验证。原BF16逐项取整后乘scale的Torch分解移到公共reference，明确reference.pytorch，禁止伪装vendor kernel。旧量化差异不能解释历史GPQA/OOM。lease13已自动恢复源API，health200及精确NSPID/ticks一致；源代码和启动脚本未交付。

- `refactor01/commands/import-check-candidate14.py` SHA `50b3ce3c5ebdb2b6035ad0fd282b9a82aa1fd140a0a976ca67def65842dc5209`。
- `refactor01/commands/cpu14.py` SHA `1b09406f61ccbdd04ab97329c2b4b18c2f4c17e5b7b3fb5fd7d98472ac673cfd`。

用户指示优先直接尝试FGV已有scaled_int8_quant：本轮不改其源码，通过根包公开API取证实际MetaX模块与SHA，27个有限shape/dtype组合以独立CPU参考q误差<=1/scale rtol1e-6，8组新输入graph各两次replay；NaN/Inf/极值单列与SDK逐行对照，不把诊断当全模型gate。此后再决定接入，不能把尚未测的SDK候选当最终决定。GPU14同租用期完成剩余FGV sparse/reference回归；源恢复日志追加原B/service.log，保留旧日志。
- `refactor01/commands/gpu14.py` SHA `5dd35616e70cebeb97e529767b3f4331d8bc4c943eb1a74c48907ef7bf7ca570`。
- `refactor01/commands/lease-gpu14.py` SHA `86dc5c1974111257a86317a369afebb99f313dd74d0f0a4c8394218d3808ecb4`。
- `refactor01/commands/probe-fgv-scaled-int8.py` SHA `a3c8d99a4916e75a8f261acf8b235ffb58130feff560295246e6868cd73a328b`。

GPU14执行前静态预检修正previous lease守卫，必须读lease13源恢复回执，非自身lease14；最终未执行脚本SHA `36d9055d118f2c2b369673a88bbff396caf29f5bbb2e2b3c3972495f7b467417`。

正式精度formal-gate输入冻结准备仅采集task/data两次，不查询模型。GPQA198、C64、thinkingON/prefixOFF、模型默认temperature1/top_p1/top_k-1/maxgen30000、API seed1234、lm-eval seed42、strict-match阈值0.80。命令 `refactor01/commands/prepare-accuracy-inputs.py` SHA `6d2c91f8e88e2b77bc0e23c355dd0c3548534b55b129b777ffdaba32fecf7cb2`。

## candidate15 执行前冻结

- `refactor01/candidate15.tar.gz` SHA `6dcb81397d656bb4c3bc9996d84961bf2c34d5747dac25969f623c64a9b344ac`。
- `refactor01/candidate15-manifest.json` SHA `c4de5b26f3cef59d9836d2d039deac9b1e223ea7f0f4e4ff4ad6187d186f5d4f`。
- `refactor01/commands/install-candidate15.py` SHA `85b856b4abdc53e6d3be6ed9c252ece59d603484b490e5e59a81e2ab60698052`。
- `refactor01/commands/import-check-candidate15.py` SHA `d320fb96d69be11d4fedafe145dd610b54e7dadfd3e175736dcb1fe4825fd844`。
- `refactor01/commands/package-next.py` SHA `842b26cc3ef646adaba9fb099ad81f40b3a7e80bf584c7023e6b2870d54dc204`。

## Public FGV quantization trial and candidate15

Existing package-level API resolved to MetaX. All27 finite shape/dtype cases passed independent CPU q<=1 and scale rtol1e-6; 8 graph cases each passed2 updated-input replays. Defaults scale/azp missing caused TypeError. NaN/Inf and zero lanes under tiny scales differ from SDK. Extreme finite BF16 FGV127 vs SDK0 at K4096 is recorded separately, not treated as a mathematical oracle. Candidate15 removes newly added SDK bridge/policy, reuses default FlagOS dispatch and root FGV scaled_int8_quant; no copied quant kernel. Existing FGV MetaX file gets public defaults/zero-token/stride/device/leading-dimension guards, first-line logging/libentry, and explicit NaN intermediate-to-zero before saturation; finite operation order unchanged. Test original full matrix plus new independent CPU/boundary/graph/all-BF16 patterns. FG remains5 production files. GPU14 sparse/reference suite passed; exact XML count pending audit, source lease14 restore receipt authoritative. CPU14 all4 returncodes0.
- `refactor01/commands/cpu15.py` SHA `f24eb4aa5f7e333d2466cc5e17086c0067046a71100ce9accde0b91d92c44a8a`.
- `refactor01/commands/gpu15.py` SHA `18018b11a9fece88d029cec713d3986bac09fe637766b9107302514a11b3e708`.
- `refactor01/commands/lease-gpu15.py` SHA `66aeabd2635a9f8a85aeb5a81cf92431cdd061afac0473b6627d5943fb7385ca`.
- `refactor01/commands/import-check-candidate15.py` SHA `d4768f808227f61f6a28efd0a8f007fb79844161f6ed57ef3581fa4c7667cdd8`.

GPU15 durable launch script `refactor01/commands/launch-gpu15.py` SHA `e018ecb21c79939c8f4a20c52fa038c17dcc4e32522c4d568a7701b3baacf17b`; CPU15 all4 checks must pass before starting. GPU suite original scaled_int8_quant plus new public contract cases, each3600s budget; no model requests until pass.

GPU15 before-launch addition: only after the complete quant correctness suite passes, run the existing repository dynamic quant benchmark30shapes BF16, native SDK vs package FGV, cudagraph mode/iter100/warmup25, JSON raw metrics retained. No E2E gain claim. Final gpu15.py SHA `80ec541c2515bda3b66cc813266b1b76cb0ec6f53b695f2209fb639ea5708175`.

Whole-model preflight command snapshot-installed.py SHA `d68cd47947b43e347d6107ad9c2700586bee998603d4640aabc5d5125b2d86ad`: source content hashes/current public quant function identity; actual weights fingerprint uses full headers plus first/last64KiB probes/file metadata, explicitly not full306GB hash; tokenizer/config full SHA. No model requests.

GPU15 quant316 passed/0skip, native dynamic benchmark1 passed/1static deselected; all raw shape measurements retained. Source lease15 restoration pending current receipt. Snapshot v1 failed before artifact publication because the installed FlagTree exposes module triton without a triton dist-metadata entry; v2 records actual module version/path and distribution mapping, preserving v1 error rather than inventing version. Minimal model check frozen22 requests (10 arithmetic/science C1 + same10 C8 +2long), no expected answers inserted into the prompt; temperature0/max2048 are this minimal contract only. It is not GPQA scoring and cannot replace the official gate.
- `refactor01/commands/snapshot-installed-v2.py` SHA `9c26dd7d57c3d309e1a3af639aba377d8fc86de4f472eaf32c751ca0aa4adb38`.
- `refactor01/commands/minimal-model15.py` SHA `8b5372357d8b0566c53dc9744e3c69ed39453ec2ed8b8aca4be5a5471ee38e99`.

## Trial16: compare existing portable FGV quant implementation

GPU15 existing MetaX root316 passed, but original native benchmark30shapes shows slower than SDK at every shape (M4096/K13824=3.388ms vs0.1971ms). No E2E gain is claimed. Before a final path decision, run an isolated-process diagnostic of the already existing portable FGV implementation under the same public benchmark/finite/graph cases. A process-local root alias selects that implementation only for this explicit diagnostic; no installed code or source service is changed. SDK remains an independent comparator, BF16 extremes separately noted. Lease16 requires completed lease15 source restoration and CPU15 checks; finally restore source.
- `refactor01/commands/probe-fgv-generic16.py` SHA `43e6da0864d1ff53f235ef4579f15c22d65e6440a720382350e3445c22409d51`.
- `refactor01/commands/bench-fgv-generic16.py` SHA `6a7520d37f1e82acb5b443478ea568eea8c171a0a0f493dc265900267a9338cd`.
- `refactor01/commands/gpu16.py` SHA `4a50e9cf77fa86e7a18f3d6be450b0ef43eb9a3702382b234e6d6f4c779a6963`.
- `refactor01/commands/lease-gpu16.py` SHA `943458f761bb6ffdaccde78277dd5e4b3406595111d24f07963367de74e33b76`.
- `refactor01/commands/launch-gpu16.py` SHA `b8e1afdc73b7115ab4f4932888cdf390606f953c2417bc66e363a0f848a06cf6`.

## candidate17 执行前冻结

- `refactor01/candidate17.tar.gz` SHA `4141577a03df3f46a81d3f7ecfc5184edb59025171ee186eac3c7f9b3670820b`。
- `refactor01/candidate17-manifest.json` SHA `8b646460567824f0017362e26aa6f574edd26c89d00565001a97496ac846708f`。
- `refactor01/commands/install-candidate17.py` SHA `868b3879e69ac6d234be03a8fb23c0b0733e3530ab72b5fb3e2aeb048d55ef78`。
- `refactor01/commands/import-check-candidate17.py` SHA `025041310e16411a1a8281d1d4ad50e0227d01c05d8b72803742f3f094db0a5b`。
- `refactor01/commands/package-next.py` SHA `842b26cc3ef646adaba9fb099ad81f40b3a7e80bf584c7023e6b2870d54dc204`。

## Candidate17: reuse existing portable public quantizer

Trial16 portable FGV finite27/graph8 passed; native benchmark30shapes completed, M4096/K13824=0.19046ms vs SDK0.19703ms, much faster than candidate15 MetaX3.388ms. Smaller shapes remain slower than SDK (all raw rows preserved), not a universal speedup. Remove the redundant MetaX quantization file/export instead of adding another kernel or SDK emulation. Root package now uses the existing common implementation; common wrapper adds defaults-preserving layout/device/empty validation and NaN INT8 conversion0 (no change to finite operation order). Vendor guards apply via runtime device name, not cuda-only. Non-MetaX hardware not exercised; require downstream CI, no cross-platform performance claim. New root/common changes require original full quant matrix/boundary/BF16/graph316 and the same native benchmark before model validation. Plugin/FG code unchanged from candidate15, CPU17 repeats import/public2/FGV1; previous Plugin154+FG3 guard tests remain SHA-identical.
- `refactor01/commands/import-check-candidate17.py` SHA `e1528eefe3ad24bb842963a8073b67c6dd4b9fa57da1307b1d19af5ab29f972c`.
- `refactor01/commands/cpu17.py` SHA `49392f5d18a9132d41c3564cdd4391d4b600afe716dad138720fd86e364933a4`.
- `refactor01/commands/gpu17.py` SHA `70269afd3ccc861fbda30c9cb7053334b18c6466756c9554e4b463a41813a363`.
- `refactor01/commands/lease-gpu17.py` SHA `1b0d166659ca74b02bf8fb2ddd47ff94182711f25973ec110adc3a66b77447e9`.
- `refactor01/commands/launch-gpu17.py` SHA `f29847f7ab3314f66d96cf19609befb8baaad9a8cd999393f98d20540f6b0f3e`.

Before GPU17, add a faithful cold-tuner graph regression: original model has capture warmups0; existing common autotuner has per-token-bucket keys. Profile M4096/K4096 then capture M64/K4096 with a fresh private diagnostic tuning cache, no decode warmup; require2 updated-input replays. If capture fails, preserve it and do not start model/GPQA. This does not alter startup script/env or source.
- `refactor01/commands/gpu17.py` SHA `5555826a686ec9f2665444a6276c8d6cd5827878aace65e8c85f66360a1618c3`.
- `refactor01/commands/cold-quant-graph.py` SHA `eea4744f10a62308fa6ae12066d9779c9359520eb939df1447db8978b214ec88`.

## candidate18 执行前冻结

- `refactor01/candidate18.tar.gz` SHA `4584b3605abfe44d38b8a947efdccfb0a376cf39e60041f6659810aa0ffe10ee`。
- `refactor01/candidate18-manifest.json` SHA `05c7e5d4792ae07b6b10be43ee2a936ed2e2d35d1539fba5d21f3884baea1a20`。
- `refactor01/commands/install-candidate18.py` SHA `b6a3fe6a229a2acd34d7e30e4a12d9d132f20b6774074c2b2f675d162bd370c3`。
- `refactor01/commands/import-check-candidate18.py` SHA `f30aadd7c1584c78b01e9a482e326e5ca3e4a17186fd721b5106160d1a90933e`。
- `refactor01/commands/package-next.py` SHA `842b26cc3ef646adaba9fb099ad81f40b3a7e80bf584c7023e6b2870d54dc204`。

## candidate18 执行前冻结

- `refactor01/candidate18.tar.gz` SHA `f4ba090d7ec962df871228aea879cc88c983f77ec240763666f887c1d1aa7950`。
- `refactor01/candidate18-manifest.json` SHA `bad43cda00cb12cb1219abe5d79e7fa27f9d9a0a18b41d37b84402ac2650fa0d`。
- `refactor01/commands/install-candidate18.py` SHA `b6a3fe6a229a2acd34d7e30e4a12d9d132f20b6774074c2b2f675d162bd370c3`。
- `refactor01/commands/import-check-candidate18.py` SHA `f30aadd7c1584c78b01e9a482e326e5ca3e4a17186fd721b5106160d1a90933e`。
- `refactor01/commands/package-next.py` SHA `842b26cc3ef646adaba9fb099ad81f40b3a7e80bf584c7023e6b2870d54dc204`。

## QUANT-CAPTURE-002 / candidate18

Cold-tuner graph17 failed exactly at native Triton autotuner -> testing.do_bench -> torch.cuda.synchronize inside capture (operation not permitted). GPU17 stopped after this required failure, no model/GPQA. This is not an OOM and is not evidence about old fw-006. Candidate18 changes only vendor quant tuning policy: standard MetaX YAML supplies a single4warp/1stage config for existing common static/dynamic(single,main+tail,two-loop) kernels. Native autotuner len1 skips benchmark; no compiler/global tuner monkeypatch, no startup environment/cache parameter or duplicate kernel. It must pass the same cold17 reproduction with fresh cache tag18, then full public quant matrix (added K16401 boundary/two-loop graph), and all30 native benchmark shapes. Cold-case script unchanged SHA. CPU18 adds actual config uniqueness checks; Plugin/FG unchanged. Numerical tolerance and original failures remain untouched.
- `refactor01/commands/import-check-candidate18.py` SHA `f35a654e4e07335788f064a01e43a96cfdccc577b9295307543c765820613a48`.
- `refactor01/commands/cpu18.py` SHA `060012847f353304e5dca241afad1f65710a22d47a79be766a1d2cdcc83fd1f4`.
- `refactor01/commands/gpu18.py` SHA `ee7dbd30f13c8b9116f534b16ea4e5e0ca6f2ceb9de45b1b0f84d3bd6b63701c`.
- `refactor01/commands/lease-gpu18.py` SHA `bfc681700640570e5644b6aac1bc5e40adc9fd13de56cde7bdc236f03f45f08e`.
- `refactor01/commands/launch-gpu18.py` SHA `150d2115ed054db1ad070e9f3ae74ef199b93a40dd561aada69638eec53d681e`.

## Whole-model/official formal orchestration frozen before execution

Only candidate18 cold/320/benchmark30+CPU receipts all pass and source18 exact restoration permits selection. Model lease compares original source restored identity (PID/ticks) and idle metrics, source/clone IDs/current mounts, preserves full source env only in memory, source original script unchanged. Clone-only old compile/code caches reversibly isolated (overlay EXDEV copy/move with disk guard); no source/shared cache clear, no final-script env additions. Clone port18011, original prefixOFF/.85/argv exceptport, native capture/log check and22 fixed C1/C8/long minimal requests (long filler512/2048 lines; no gold answer leaked in prompt). Stop on failure and restore source exactparams/log append. After minimal/native FULL>=2 review, official evaluator preflight/fullGPQA C64 via SHA-frozen original runner, threshold80%; formal coordinator tracks exact child processes and native CLI, uses fresh UUID native cache, no scorer changes. Source/weights/tokenizer before/after and APIidentity audited, original source restored in finally after clone workers exit. No model test or GPQA launched yet.
- `refactor01/commands/select-model18.py` SHA `33f7fa3182ca21401077d0f622b5028d2b5dd2a70ac45a5d4bed36463532db79`.
- `refactor01/commands/model-lease01.py` SHA `c902a7ed044b3fb5f4d46d28c8298cf5161048ab39beded3b12901956293c051`.
- `refactor01/commands/finalize-service01.py` SHA `d2cdc14415b9ebafcc830b805c977e2a9c873e10d0233b8b62123340405e61a1`.
- `refactor01/commands/minimal-model15-v2.py` SHA `357b517b95985aa0b7d645b2bad67032ee8dce40a5f5772b8e9599890f80ea04`.
- `refactor01/commands/accuracy-inner01.py` SHA `bce8fe678735bf709043e59b6430a142afed93576bc9ce7acb5a7837a461989f`.
- `refactor01/commands/coordinate-accuracy01.py` SHA `7c5859a98022260561e3d03609ee82c0f48fa669d48bb89bd8d24dee5d2bca65`.

Candidate18 completed cold capture+2replays, quant320/0fail/0skip and native benchmark30 valid rows. Final fixed config has regressions versus SDK (M1/K4096=4.251us vs2.403us; M64/K4096=4.450us vs2.587us; M4096/K13824=0.24097ms vs0.19705ms). These remain visible; no E2E/performance acceptance. Source lease18 health200 restored with exact identity; selected candidate artifact frozen. Model activation now authorized after live changed/deleted file SHA verification; final command hashes below, previous unexecuted controller hash superseded.
- `refactor01/commands/model-lease01.py` SHA `e78a5401cab02d020859b257ad0d773a85e069efda5abb64b104e0d3b0602f4e`.
- `refactor01/commands/launch-model01.py` SHA `89f9aab2837b80bc1974f03c354eeeaaf64a83c18334abd8e35222d908ba1b32`.

Lifecycle audit: the already-running model coordinator stop_exact checks PID/ticks without excluding stateZ; clonePID1 is sleep, so eventual orphan zombies may block its normal restoration despite no GPU workers. Add an independent scoped recovery guard before termination, with the clone API exec environment (the original source dict passed unchanged at launch) retained only in guard memory, known3exports checked and only SHA persisted. It waits until the original coordinator exits, never races it; if source already healthy it does nothing. Otherwise it stops only dedicated clone live model processes, treatsZ as exited, requires allGPU idle/no source listener/unchanged script, then restores original source argv/env and appends original log. No container/PID1 stop, ptrace, broad process kill or environment dump. Main driver/source restoration receipts and recovery receipts are both retained, not relabeled as clean coordinator exit. Command `refactor01/commands/recovery-guard01.py` SHA `6e9e7cea75eb2efe4009c7e6769299717dd552128a3865fbc55a558814d7fc37`.

Model-validation01 activation failed before ready/minimal/GPQA; native KV557624 at.85 observed. Main cleanup then failed because PID/ticks-only liveness treated zombie compiler children as live. Recovery guard also exited before arming on a /proc enumeration race (exited child790747); no environment was serialized. Main coordinator has exited, original full interactive environment only in its memory is lost. Execute canonical restoration using approved unchanged original argv, container defaults and exactly the script3exports, appending original log; explicitly do not claim byte-identical interactive env recovery. Guard exact source/clone IDs, no live GPU owners, unchanged script, no source listener and dead prior driver. Do not restart containers or change source code. `commands/restore-source-canonical01.py` SHA `a6f82e651dcc9bf7f854b5d0865c0e1902e69e68745e245095f40b90261530fb`. Native activation root cause still being extracted; optional FlagTune xgboost warnings are not assumed fatal.

## candidate19 执行前冻结

- `refactor01/candidate19.tar.gz` SHA `120cfa48354444e9f41a32d24412e925ee80d5bacd6d0103a64cc0b958b8c4ef`。
- `refactor01/candidate19-manifest.json` SHA `067f51746ce653fbacf2c37861f3cab63ad2e8cbe81613fd4fae6641240b7c5f`。
- `refactor01/commands/install-candidate19.py` SHA `0ea81389a410d2962973f96a3323b84cf33994f01578ec9c7e8e4d00f49c7ebb`。
- `refactor01/commands/import-check-candidate19.py` SHA `84a6cb6d2aa2f8569d6c21246d78c7b58ee22c6b037b6eb6b363a4c1144d93c3`。
- `refactor01/commands/package-next.py` SHA `842b26cc3ef646adaba9fb099ad81f40b3a7e80bf584c7023e6b2870d54dc204`。

## candidate19 执行前冻结

- `refactor01/candidate19.tar.gz` SHA `6dc93aeb8fb1249f8546bccd191ce823c524f0178b0d1fdf3c88c2b8f07f21e7`。
- `refactor01/candidate19-manifest.json` SHA `135ce90065d8cc9be1a39ca8a9ce99791b4b8d371527c8f1c50e680f95394f88`。
- `refactor01/commands/install-candidate19.py` SHA `0ea81389a410d2962973f96a3323b84cf33994f01578ec9c7e8e4d00f49c7ebb`。
- `refactor01/commands/import-check-candidate19.py` SHA `84a6cb6d2aa2f8569d6c21246d78c7b58ee22c6b037b6eb6b363a4c1144d93c3`。
- `refactor01/commands/package-next.py` SHA `842b26cc3ef646adaba9fb099ad81f40b3a7e80bf584c7023e6b2870d54dc204`。

## INDEXER-DECODE-003 / candidate19

Native model18 capture failed at sparse_attn_indexer_fl decode-only with UnboundLocalError num_rows (initial trace at17:35Z local+08). The same common call also lacks topk_indices on graphsafe decode if no prefill preceded it. Define both from decode logits/buffer after the decode branch, independent of prefill. No numerical-library changes; operator320/current SHA evidence retained. Add6 full production Python decode-flow CPU tests (batch1/4/64, short/long score pools, independent output/canary assertions, numerical providers explicitly stubbed). Original module must fail the same test before fix. Scoped Ruff cleanup removes unused variables and binds callback valid-hint integer to its prefill chunk, no math change. New model graph/C1/C8/long and formal scope remain mandatory.

Correction to cleanup attribution: main stop_exact timed out after240s; it did not record survivor states at the timeout. The later canonical restore audit found no live clone task processes and no zombies. Zombie misclassification is a code risk, not a confirmed historical cause; delayed compiler-process exit is also possible. The recovery guard failed before arming on a disappearing /proc entry. Canonical source restoration is in progress; no byte-identical interactive env claim.
- `refactor01/commands/import-check-candidate19.py` SHA `f3af29694da386ca8413fc33617f7814d4c55ce1f13d48986eceab3f2ba4b1e5`.
- `refactor01/commands/cpu19.py` SHA `5f70a4ccce57ddd7096a7e74d03aea8664c598e571fca88694ed0da10f42a47a`.
- `refactor01/commands/test_indexer_decode_control.py` SHA `aeb7ffda3034138cc8d85c5d2f9c10f77cf8c60f44f12c899b3211e5c40e58e6`.

## candidate19 执行前冻结

- `refactor01/candidate19.tar.gz` SHA `eda41b295a533704274f0d1d8abdd7c933093f99ed32eb0886656680a5c8bbff`。
- `refactor01/candidate19-manifest.json` SHA `72068e8790b3c873ed2705d95c104e670a4e65b1072a80713cf1968199d5b3fb`。
- `refactor01/commands/install-candidate19.py` SHA `0ea81389a410d2962973f96a3323b84cf33994f01578ec9c7e8e4d00f49c7ebb`。
- `refactor01/commands/import-check-candidate19.py` SHA `84a6cb6d2aa2f8569d6c21246d78c7b58ee22c6b037b6eb6b363a4c1144d93c3`。
- `refactor01/commands/package-next.py` SHA `842b26cc3ef646adaba9fb099ad81f40b3a7e80bf584c7023e6b2870d54dc204`。

CPU19 import failed because package-next regenerated its old import-check04 template, still requiring the intentionally removed FGV dynamic_per_token_quant_int8 API. This is stale validation metadata, not an actual library import failure. Fix the generator template once to inspect public scaled_int8_quant/indexer_dequantize_fp8; rerun scoped CPU as19b, preserve19 failed receipt. Installed19 manifest72068e8790b3c873ed2705d95c104e670a4e65b1072a80713cf1968199d5b3fb verified after transient SSH disconnect; no repeated install. Source canonical restore health+exact identity and arithmetic smoke passed.
- `refactor01/commands/import-check04.py` SHA `d45ebfb7802c32c3ca320068f1b33d00b233f4d4b6ec4fc97caa02fd3dd8bd04`.
- `refactor01/commands/import-check-candidate19b.py` SHA `1c3aa56faab1dd99cff2d4351a902c9173311d9ee957dff78abb87406c33856a`.
- `refactor01/commands/cpu19b.py` SHA `3dbbbc3ffa5d79f4f0d6d5eccf695bdd4ff422103997bfa9a66bdd43481082db`.

Model-validation02 planned after CPU19b: same clone/port/prefixOFF/.85 and original argv, only Python indexer control-flow changed. Retain private numerical/AOT caches from model01 because no numerical kernels/compilation settings changed; do not claim fresh compile. Require new model capture/2replays/minimal22 then official formal scope. New controller liveness excludesZ/X and accepts canonical restoration receipt host_api fields. CPU-only cleanup exceptions are recorded but do not skip source restoration if native evidence shows allGPU idle. Source env is captured from its current healthy canonical instance and retained in coordinator memory; no disk env dump. Accuracy01 provenance/config/contract still unused by any model run, remains first formal scope. No duplicate evaluation.
- `refactor01/commands/select-model19.py` SHA `006f1d7f53ac4c06628f6b6d7b571f3c031f5cda2d1cf041b84c088ed46d5084`.
- `refactor01/commands/model-lease02.py` SHA `2e7643ca7cf391b4a554b3e75a47e381107e63ed623889b692af9e1989aa84d0`.
- `refactor01/commands/launch-model02.py` SHA `b9c0b38c5fda06f966c12ccb9694880f346a1713528bc37a829d92eb6d782879`.
- `refactor01/commands/minimal-model02.py` SHA `b6980d43aa72c800e4754b7dee59b3dd7ab6e7337ed0612863dfcf01ec27da79`.
- `refactor01/commands/finalize-service02.py` SHA `658ce61d94d0cc3502336589ea8229ed044a08720ddd21fe71d916f0b1faf20d`.
- `refactor01/commands/accuracy-inner02.py` SHA `fc538411e92a3aa764b50eca153d4a41af710b1c88f9f328ccbc0de135c979db`.
- `refactor01/commands/coordinate-accuracy02.py` SHA `cac1b7eb7cd0b4cc0e353803f122fba3e3bca9dc049473d4b72ab33534311337`.

CPU19b native import/Plugin8/FGV2 all returncode0. Model19 selected after unchanged FG/FGV SHA proof; model-validation02 launched host driver850897/ticks1210299942, controllerSHA2e7643ca7cf391b4a554b3e75a47e381107e63ed623889b692af9e1989aa84d0. Source exact idle lease/clone activation guarded by controller; no formal requests yet.

Prepared formal activation request (not executed until native model evidence review): `refactor01/commands/request-formal02.py` SHA `e5c6bc477831cd841f98e2da28c281b1f298d090c52348dbd28401b970dcd1c3`. Requires22 passed, actual service-finalization passed, exact API alive/health200 and no prior evaluator receipts; no repeated run.

Model02 native activation still active; slow optional FlagTune model preload fell back for missing xgboost, no dependency modification. Queue one audit controller to avoid idle review delay: waits for real model22 minimal pass, verifies exact model lease/no failure, runs frozen finalizer requiring actual FULL capture/replay/native no-errors/source identity, then frozen formal request. A review failure stops promotion and remains visible; no blind retry or alternate evaluator.
- `refactor01/commands/review-model02.py` SHA `8f2689c7c9b96158ff03bf623c213d0d856b73af9a1929185c2525c6d90d1f3f`.
- `refactor01/commands/launch-review02.py` SHA `ebe8f23fc70a058bb275ef667cad1cc4ddb65c39b16afeb110fe19ff58efea8f`.

Review02 launched host857714/ticks1210377405, scriptSHA8f2689c7c9b96158ff03bf623c213d0d856b73af9a1929185c2525c6d90d1f3f. Native AOT reload observed for all8ranks at19:47; optional FlagTune model preload delayed startup, defaults after missing xgboost. Original native warning preserved, dependency/compiler not modified. Latest activation still waiting, no model/GPQA result or OOM claimed.

Model02 native startup reports KV557700tokens at19:51:34+08 with.85/prefixOFF. Current numerical/private-AOT policy unchanged; capacity is measured, not inferred to equal source or historical567220. Capture/readiness/minimal pending at this observation.

Model02 ready/health200,22/22 minimal passed. Review02 stopped before formal at missing assumed logger phrase. Preserve original audit failure; finalizer03 consumes real native100%7/7 FULL progress completion plus successful engine initialization and requires a single FULL stats interval Count>=2 (not a sum of repeated one-count tables). It changes evidence parser only, no model/metric/threshold/source change. `refactor01/commands/finalize-service03.py` SHA `e72c048cc3583cc2b61ba3fb5774117b049fba43eca5e6357ac8dbef369f96c9`. Old finalizer/review records retained.

Finalizer03 passed: service instance mx104/3104fd968efc2b41c939d9dd778599e8467ea8698edd657dbc1f47904a4c3256/851052@1210301188; health200, actual capture and FULL interval replay proof,22minimal. Native FULL rows sum712 descriptive, not used as independent repeated-one-count evidence. Frozen request-formal02 executed once, native formal activation now pending process inspection; no score claimed. Source restoration still owned bymodel02 coordinator.

Official native GPQA started2026-11-04T12:04:45Z, preflight passed. Exact host coordinator1028630/ticks1210461018, evalinner458/ticks1210461025, evalformal610/ticks1210461815 verified live. One cacheUUID5ab972ffeaba406fae16df4edcf9588b, mode=ro unnamedCOUNT0/198 at observation, source candidate APIhealth200, no evaluator failure receipt. Cached-request scanning198 is not completed generations. Heartbeatdeepseek-mx104 updated to this active run; no duplicate start. Model02 source restore remains pending.

## 正式精度01已通过；性能01输入预冻结（尚未运行）

GPQA strict165/198=83.3333333333%，达到冻结80%阈值；flexible63/198=31.8182%为独立原生filter，不替代strict。两filter各198唯一ID/每doc-filter一次，共396行，完整性独立核验；native acceptance check通过，identity-after源码/权重/tokenizer/version不变。源恢复仍在启动，不宣布健康恢复。

Gate SHA429cd74f17c8c1da5a610aa26e9607bd46070fa574d08dd3ece2ef79cd472b90；native result SHA0a3940ae199225d58e61a304f426a9b15420c57be808ecae726efedfe173ae56；samples SHAbde1ae3e9748365ae5765be24efc67ecb868f0c5924060297a28091fb00d806e；identity-after SHA238b49749b03164bf398982895523f0c121a9c00ec80a9af784b9534437c0a54。第一次独立check误用python-I导致同目录sample_validation无法导入，修正为原runner同样的非-I入口后PASS；未修改工具或结果。阶段[SCORE]matched0/0仅辅助解析未匹配，正式结果以native results/gate为准。

规划复盘review-refactor-002：combined candidate19有公开GPU和正式GPQA证据，但无mx104同workload端到端数据，不能累加kernel收益。Prefill/Decode/Mixed瓶颈均待测，以同一Mixed的TTFT/input-throughput与TPOT/output-throughput代理分别观察，承认网络/排队/调度残余。先保持已有组合、仅测性能回归，不继续堆叠优化或改编译器/TLE。deferred：量化深度调优/新融合，直到E2E表明值得投入。

性能身份清单发现设备编号是整数，而compare要求字符串；旧精度gate有效，但不能把它直接用于新性能身份清单。缓存准备描述也应使用三角色共同的真实策略。保留旧manifest/gate，禁止改字节或放宽rebind；新候选实例生成正确manifest并再跑相同正式GPQA198，然后同实例性能测量，属于身份兼容修正，不是追高分。源复原health+最小推理完成后才允许新lease。

模式targeted，P32K目标/P1K哨兵，均D1024/C64/N128；每角色5预热+3正式，最后2预热throughput spread<=5%，正式spread<=10%，throughput回退<=5%，medianTTFT/TPOT回退<=5%，B/R漂移<=10%。一个独立实例/角色，顺序C→B→R，同clone，原argv/.85/prefixOFF，保留默认私有缓存、无手动清理，按source-specific AOT key记录与稳态准入；不声称冷缓存对称，不增加启动缓存环境变量。所有轮保留，失败/incomplete不挑慢轮；只支持两个场景的工程回归，不宣称四场景或NV约86参考同等精度。还需每角色实际dispatch/编译命中及新编译变化、native dry-run/客户端指纹、真实源恢复与最终bounded delivery。
- `refactor01/performance01/perf-plan01.json` SHA `c5d05ea40f88c12694f89b51e9a562d17e1d47fb044701d8386db4e81274ffd3`.
- `refactor01/performance01/perf-comparison01.json` SHA `1d3bef20b81329df4a7eb5129715a85fd7eaf765b4dd038e0ec2c93de553c0ea`.
- `refactor01/performance01/perf-protocol01.json` SHA `584c31f8d05dba6faeceeb05c8e800d3d05b327d618fea57b0510729e433f467`.
- `refactor01/performance01/performance-skill-bundle01.json` SHA `4e27796b3c628daa6266a4ecdd356c446e172fe0de25d3fced7ddc11abd145ae`.
- `refactor01/commands/prepare-performance01.py` SHA `0fb2545f63bd8e21f793c805bbb3efcc74e7007eab8922f606689f807de7310e`.

## 32K性能执行编排01：执行前冻结

用户2026-11-04明确继续32K三轮并对比整改前版本，保持prefixOFF/.85。原source13:04:57Z健康恢复回执已出现（实际API1128349/ticks1210649200），先CPU输入预检/新accuracy02 provenance，再独立租用精确空闲源API。C→B→R都用同clone，原初源码工作区归档而非HEAD作B/R，99条实际内容差异受完整SHA守卫；只清理这些Python模块派生字节码，不清JIT缓存。C新实例正确性能manifest先通过原生schema消费校验，再跑同原生GPQA后同实例性能；不改旧gate。每角色22最小回归、真实7档FULL捕获及区间>=2replay、真实设备/argv/代码/权重/后验身份。调用维护版runner/compare，无自建benchmark。基线/候选/revert每个输入轮1800秒预算、总12h、所有轮保留。失败停止精确本任务client/API后finally恢复原源argv和内存环境并arith smoke；可升级SIGKILL仅限180秒SIGTERM后仍存活的精确PID/ticks关联进程，记录动作，无容器操作。性能实际指标/status仍未运行。
- `refactor01/commands/perf-runtime01.py` SHA `49567f24a050f984f03178674570f034f9689ddbef5ff0cc23511ea87454911e`.
- `refactor01/commands/perf-coordinate01.py` SHA `dfa86ac401a45776f5b970638ef932d13ab26cb380cca546d1767a5d4535f43c`.
- `refactor01/commands/perf-client01.py` SHA `951121f4c565b92867385eaad81bf148d185708cf6f80639aec031e0a8383759`.
- `refactor01/commands/perf-finalize01.py` SHA `7f47da7bc1260740e44698e2ea8f25af984790becc4b785a65c5314262204f4b`.
- `refactor01/commands/perf-minimal01.py` SHA `cf7124ff2cb8853c2b6a4d0225d1bc0aafaf7ca932db062fc5f584dd767256c1`.
- `refactor01/commands/perf-switch01.py` SHA `f4df0162290fd759e1ebe9dd8ffc3e3112f66ca78989b0bcdbdbbcf5196035d1`.
- `refactor01/commands/perf-preflight01.py` SHA `409bf269d3b39a7786a930528a64a8d7bcf1c90f836c06f238d04ae4e5e9eca3`.
- `refactor01/commands/perf-accuracy-prepare01.py` SHA `8ab0e765186467c9a9f47956dd960d2a8156687b7f0fc797d6a6d5f3f8aee92c`.
- `refactor01/commands/perf-accuracy-inner01.py` SHA `81d1be017f47b2647602cbac8b2cf9ddbd5b4cb6b0781a666a624ff02a3f4777`.
- `refactor01/commands/perf-accuracy-coordinate01.py` SHA `efb6a35e93de095fc7ff55f2eee51921cc3d006e5a1ce6cb4f116e816ee4da08`.
- `refactor01/performance01/perf-states01.tar.gz` SHA `44a9be4df097871b625662804b834a067e74be4d4da1e0926ab9ca69698dc0e9`.
- `refactor01/performance01/perf-states01.json` SHA `3f58c14cf3949664d501bd2ad55301fe587ac1adbe3117f1bf6be6a895a320bf`.
- `refactor01/performance01/perf-plan01.json` SHA `c5d05ea40f88c12694f89b51e9a562d17e1d47fb044701d8386db4e81274ffd3`.
- `refactor01/performance01/perf-comparison01.json` SHA `1d3bef20b81329df4a7eb5129715a85fd7eaf765b4dd038e0ec2c93de553c0ea`.
- `refactor01/performance01/perf-protocol01.json` SHA `584c31f8d05dba6faeceeb05c8e800d3d05b327d618fea57b0510729e433f467`.
- `refactor01/performance01/performance-skill-bundle01.json` SHA `4e27796b3c628daa6266a4ecdd356c446e172fe0de25d3fced7ddc11abd145ae`.
- `refactor01/commands/minimal-model02.py` SHA `b6980d43aa72c800e4754b7dee59b3dd7ab6e7337ed0612863dfcf01ec27da79`.
- `refactor01/commands/snapshot-installed-v2.py` SHA `9c26dd7d57c3d309e1a3af639aba377d8fc86de4f472eaf32c751ca0aa4adb38`.
- `refactor01/performance01/execution-assets01.json` SHA `4889825ce8689c3a97f9010c1dacf74faa0c94b1115e64c80fdd162b056b3dd3`.
- `refactor01/commands/launch-performance01.py` SHA `8ad25b6a161b300b3587b322ae0262d030b0b40be0c08c7bd96826bdf857b8ea`.

执行前补齐metrics异步更新的60秒空闲观察、精确clone GPU退出后才丢弃进程记录、恢复期间重复SIGTERM不打断恢复、原生run-record成功值为complete（非passed）。尚未执行，以下最终SHA替代前一未执行版本：
- `refactor01/commands/perf-runtime01.py` SHA `2f10e2a57eb34d0c328c0b8d59432074b9351d1d40b9d08db1bdae6895a5f4cc`.
- `refactor01/commands/perf-coordinate01.py` SHA `457a31d7bd1c3a84f73acf4ebf8c308de87cb7513d33255d40cfe412dadcde59`.
- `refactor01/performance01/execution-assets01.json` SHA `3cb8fe40cf716983c9c033701c961edf13e599e7eeb0600fe37aee9a446f79d6`.
- `refactor01/commands/launch-performance01.py` SHA `8c68b106149edfd568a2b942a4e23396e5f64fcfeb3038e37114067255fe2224`.

执行前实测预检完成：source已health200且实际argv与未改脚本完全对应；CPU99路径archive/installed SHA守卫通过；tokenizer trust_remote_code=False可载入且CUDA未初始化；新accuracy02两次实际task/data provenance一致、0模型请求。原生执行代码只读SHA如下（使用已冻结远端toolchain，不升级或替换）：
- `refactor01/toolchain-20261104/evaluation/performance/vllm_perf.py` SHA `d7bac00f99827943cf63eac9cd557c1730bd5e9dcae74dfd1c9c31463a3a2187`.
- `refactor01/toolchain-20261104/evaluation/performance/performance_plan.py` SHA `ef4838ec42d8fabb2d1e1042790098ab81b546583909c6a1691e5aa3fad18d4b`.
- `refactor01/toolchain-20261104/evaluation/performance/compare_performance.py` SHA `01e75d094a430c5e557b95de5bc050a8592e98af0cb30f03e68a3143f6dbc54c`.
- `refactor01/toolchain-20261104/evaluation/accuracy/formal_accuracy.py` SHA `a4db5710cdd221b78f7b9cfd1e2bd3334869fccc73751af453f35ce71fe95b7d`.
- `refactor01/toolchain-20261104/evaluation/accuracy/acceptance.py` SHA `ad37a18b3278b4f9a20588cc47f8d621a4e5bd37ea2ac84eef0f40a11cedd88d`.
- `refactor01/toolchain-20261104/evaluation/accuracy/sample_validation.py` SHA `9799f2df22b1f9bf08331b6ae7e0fdfc345e2dcadc0f81202265f59b38ffcd11`.
- `refactor01/toolchain-20261104/test/Accuracy_test/llmrun.py` SHA `82cf6e8304cb6f9eb8ca48fe4055f6bbb2054a7b6a90d56de3d6b7a08e90c61e`.

性能01实际启动：hostdriver1152217/ticks1210944076，最终execution-assets SHA3cb8fe40cf716983c9c033701c961edf13e599e7eeb0600fe37aee9a446f79d6。source原恢复13:04:57Z已核验health、实际argv一致；本轮source-before-smoke独立5+7成功并连续空闲，再精确暂停原API/workers。新C正在启动，尚无accuracy02模型请求或性能轮次。新accuracy02数据provenance两次一致及99路径CPU源码/归档/tokenizer无CUDA检查通过。该协调器含全C/B/R/比较/finally恢复，禁止重复启动/争抢GPU，实际结果以P原生回执为准。

## candidate20 执行前冻结

- `refactor01/candidate20.tar.gz` SHA `ebc5eb7f84aaaa7be8a79fd8b7f39b25d3c421079a1f8141be0ea96339f8063a`。
- `refactor01/candidate20-manifest.json` SHA `24450715084f4a8e97aba7bb75bd90f0ff92c6d2af20c13f19b9a9c67a8333f3`。
- `refactor01/commands/install-candidate20.py` SHA `6c9193f02fc36b62c88ee68ee5378f2fc9519f3f7c8f836d32812cb8a31f4921`。
- `refactor01/commands/import-check-candidate20.py` SHA `99816cf43ec61f30cde6a5acd258cf20e276dfc361c4a9a140dbe292924e16a1`。
- `refactor01/commands/package-next.py` SHA `842b26cc3ef646adaba9fb099ad81f40b3a7e80bf584c7023e6b2870d54dc204`。

2026-11-04T23:20:07Z 当前组合C20正在performance03共同输入准备回归：5完整准备批次640成功0失败，P32K第三准备批进行中，正式0轮，未见推理OOM/非法访存。source按本轮授权暂停、原8310源码未交付；唯一main负责恢复。当前详细证据与所有历史失败仍见同一[op-001](op-001.md)及state；此前compile诊断为历史阶段，不代表当前仍卡启动。仅P1K/P32K工程范围，尚无完整B/C/R收益结论。

2026-11-04T23:55:47Z：P3六准备批768/0后正式dryrun因新增Python-I同级模块导入失败，0正式，已按guard恢复源并独立8310SHA/8GPU核验。仅移除nativeperformance/compare入口多余-I，完整三角色nativeplan dryrun+comparehelp/旧TTFT超限停止守卫CPU通过后，唯一P4已启动候选activation。代码C20/模型参数/阈值/共同准备协议不变；无模型OOM。当前源由P4授权暂停/后续finally恢复，仍未交付，最新详细证据见[op-001](op-001.md)/state。

2026-11-05T01:10:27Z：当前P4候选P1K哨兵5预热+3正式原生全部完成1024success0fail，output/medianTTFT/medianTPOT正式spread0.5591%/0.7234%/1.1478%均<10%；完整每轮指标/SHA见[op-001](op-001.md)和state。目标32K已由真实nativeCLI P32768/D1024/C64/N128/seed391723进入首轮预热，0完整正式，B/R未开始，不报整改相对收益。API/driver精确live/health200、actualargv OFF/.85、无OOM/非法访存；source仍P4授权暂停/未交付。旧P3导入错误不再阻塞P4，未改数值或阈值。

2026-11-05T02:14:21Z：P4候选32K已5预热+1/3正式，首正式128/0、output217.542522tok/s、medianTTFT8715.869538ms/TPOT274.310832ms，末2预热outputspread0.07646%满足原准入。第2正式进行中；B/R未开始，不能报完整三轮/整改相对收益。详细每轮SHA和历史慢轮见[op-001](op-001.md)/state。API/driver健康、无OOM/非法访存，源仍授权暂停/未交付；参数与阈值不变。

2026-11-05T02:38:13Z 用户要求“32K跑完就停”已执行：候选P32K三正式各128/0，output217.542522/217.864058/217.512040tok/s，medianTTFT8715.869538/8679.770780/8194.677815ms，medianTPOT274.310832/274.222906/274.556505ms；轮间spread0.161816%/6.004672%/0.121613%均<10%，无推理OOM/非法访存。原source恢复并独立health/5+7smoke/原argv/OFF/.85/8310SHA/8卡验证，clone模型退出。B/R未启动，候选未交付，不报告相对收益/完整验收；当前整改与回归按用户指令暂停，heartbeat已删除。详见同一[op-001](op-001.md)及state的原生SHA/边界。

## 2026-11-05 激活调用链只读复核

用户手工运行整改容器后询问 `silu_and_mul_with_clamp` 是否小算子组合及能否接入FGV融合实现。仅静态源码/进程环境白名单检查，无生产改动、模型请求、GPU测试或服务操作；自动工作继续暂停。

- 当前候选的 routed W8A8 MoE：`MetaXW8A8Experts.apply` 第166行调用继承的 `self.activation` → 原生 `TritonExperts.activation` 第159–160行 → `swiglu_limit_func`。后者在原生 `fused_moe/utils.py:430–444` 使用 `clamp(gate)`、`clamp(up)`、`F.silu`、乘法和 `output.copy_`，带 `torch.compile(dynamic=True, backend=current_platform.simple_compile_backend)`；PlatformFL未覆盖其默认inductor。**源码组合不等于已经证明运行时多次独立kernel launch**，本次未采集新trace/检查实际生成kernel。
- 当前模型配置 `swiglu_limit=10.0`、`hidden_act=silu`。FGV根公开导出 `silu_and_mul_with_clamp` 和 `silu_and_mul_with_clamp_out`；其前向将gate上限clamp、up双边clamp、SiLU和乘法放在同一Triton计算中。out接口可写已有MoE workspace，避免为了返回Tensor再额外copy；接入仍须遵守dispatch与dtype/stride/输出别名/limit语义边界，并验证BF16数值和graph，不能据源码宣布等价精度或E2E收益。
- Plugin现有 `SiluAndMulWithClampFL` 的CachedOp封装未覆盖上述继承MoE入口。另一路generic flagos adapter在 `VLLM_FL_USE_FLAGGEMS_VLLM` 为false时回到原生 `forward_native`；实际API进程该变量未设置（默认0）。因此不能把“已有FGV封装/模型初始化检查公开API存在”说成“所有DeepSeek激活路径都命中FGV”。单开全局开关也不能解决继承MoE入口旁路。
- 当前远端SHA：Plugin MoE adapter `80a1da43cbf5b86ba15826b3f23e5683c3084a90cb0bcf85b1803006c1d573ee`；Plugin activation `ed929ee42f12163e882d6e9dd0e9bf1da6fa0f328df7f42954c48ff900ad4900`；generic backend activation `f1bd6b5966d4d87cd8af2010109c68526f1915427706ba4b6169bad924eab6fa`；原生MoE utils `7707cb5fdc4945c061d0972fb7386cb13c0c164701e15bffa946a8daec25b9e8`；FGV common clamp `bc9716d911cb3a9f6ad1a1425ac1bb30711cf57a41905a435fbf49dd014c7309`。未安装额外MetaX clamp覆盖实现。

这是已发现的接入缺口，尚未修复；不改变C20已测结果，也不恢复自动整改或干扰用户当前手工性能测试。

2026-11-05 op003已完成当前授权交付：真实MoE clamped SiLU经Plugin dispatch进入FGV融合out；同时修复FGV负零与Plugin共享workspace元数据契约，未在Plugin新增数值kernel。最终CPU12、GPU115+9、16capture/32新输入replay、模型7FULLcapture+22minimal通过，整改容器已更新并在18001恢复原参数；源容器未改。旧A3/P4性能不适用于新源码，无新GPQA或性能结论。详细失败/回退/最终SHA见同一[op-003](op-003.md)及state。
