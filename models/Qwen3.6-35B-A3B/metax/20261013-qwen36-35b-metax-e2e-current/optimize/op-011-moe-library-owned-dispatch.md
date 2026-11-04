# op011：MoE统一公共库导入，去掉Plugin MetaX判断

用户明确纠正：Plugin不用加对于MetaX的平台判断，直接修改import库。仅MoE适配层执行该要求，upstream平台/worker/GDN等原有设备必需逻辑不动。沿当前真实020plugin-opt-metax/f99完整基线，只统一MoE公共依赖到flaggems_vllm，不传caller workspace。范围两生产MoE文件+两CPU契约test，不动Gems/vLLM/权重/启动脚本，不重启/热重载。

归属operator public dispatch contract：库namespace统一，平台分发交给现有Gems runtime。fused_experts主无LoRA路径保留分支原有kunlunxin自带实现，其他共享路径直接public fused_experts_impl+output.copy；移除我方MetaX与NV namespace选择、MetaX额外dtype/quant/map/activation局部特判。库负责支持/拒绝输入，错误直接传播；W8A8专用experts与LoRA框架分步路径保持。其他平台共享入口按publicAPI处理，不把mock视为硬件通过。

辅助topk/alignment/GEMM/grouped/sum统一公共flaggems_vllm导入，去掉Plugin的MetaX/privatebackend导入。alignment沿分支既有vLLM分配+6参数lowlevel接口，保留小batch/padding约束，库内部选实现；不在Plugin强制no_tle，不为此改Gems实现。topk公共API已实际核验5参，无需旧4参重试，错误不得宽泛吞掉。源公共函数实际存在，前置evidence `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/manifests/op011-before-20261015.json` SHAb3e03dea352add3eac00e3de52de035b8ac05709c1d8aaeccac99bcda9ffb6ba；所需签名/实际owner在其中，没有执行设备kernel。

备份 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/patches/op011-before-MoE-files-20261015.tar.gz` SHA3a8a3a5a8e8566863952dfb2a8f13c0fee0c616c78c44a8c7bedc2d4658ce40e。CPU mode=minimal-regression，scope真实apply AST+库mock/CPU tensor，覆盖NV/MetaX/其他平台共享导入、无workspace参数、量化/activation/map完整传递、LoRA/W8A8守护、alignment empty/padding/layout、错误无重试、GDN branch未变的守护。先冻结完整collect IDs再run，全部声明CPU测试通过才写当前源；新sourcegraph/数值/模型GPQA未跑时整体minimal incomplete。

不承诺新性能收益，不部署私有op006，不启动旧GPQA/P1K。当前运行982315保持；磁盘新库调用方案未来真正加载须新full198/65536/temp1/top_p.95/top_k20/seed42/C32/80 gate及graph最小回归，不沿用旧170/198。

状态design_frozen_before_private_edit，PR experimental，未测硬件如实not_run。

## 首轮CPU回归及诊断

原生77项=74pass/3fail/0skip，失败全部是缺公共符号测试仍预期属性访问的AttributeError，实际新代码直接from-import按Python语义抛ImportError；生产行为正确地暴露缺符号，测试预期未随接口形式更新。调用本地accuracy-diagnosis，纯Python单变量证明getattr->AttributeError/fromimport->ImportError，非数值/模型精度失败。诊断 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/results/op011-import-contract-diagnosis-20261015.json` SHA4dacb7854efa31471ab2846acff18fceeb395d912aba48655f5b6d7dfa3dca4b；首轮native d48a4ac4.../XML681213d0...全部保留。

只改测试预期异常类型为准确ImportError，不改生产候选、不降case/阈值；v2新私有目录/新产物完整复测，collection强制77 nodeID与首轮逐字一致。回归通过前不应用或叠加生产修改。首次上传动作的自动审批超时未执行，已按允许一次重试成功，未为此改代码/绕过审批。

## 已应用（2026-10-15 19:32 CST）

当前020plugin-opt-metax/f99仍为完整基线，两个MoE生产文件已统一公共flaggems_vllm导入，无新增MetaX条件、NV/MetaX namespace选择或runtime.backend._metax私有导入。fused_experts_impl直接import/调用+output.copy，不传caller workspace。无LoRA共享入口的输入支持由库判断，错误直接传播；保留上游kunlunxin既有路径、W8A8专用专家、LoRA框架分步路径，其余upstream平台/GDN逻辑未动。

辅助topk/alignment/GEMM/grouped/sum统一公共API，alignment保留NV原包装的workspace分配/小batch/pad/6参数lowlevel契约；不在Plugin选择no_tle。公共topk5参已核存在，删除旧4参宽泛异常重试及重复定义，选择后错误一次上抛，CPU覆盖该契约。Gems平台实现能力未修改，未来实际设备验证仍必须补做，不把mock参数传递当不支持输入在硬件正确通过。

V2原生pytest **77passed/0fail/0skip，29.47s**；collection IDs逐字等于首轮77。首轮74/3失败和诊断完整保留；只改准确ImportError预期，生产候选与首轮相同。CPUactual import-path evidence在results/op011-v2-CPU-import-paths-20261015.json，根/caller/adapter均私有stage，原生结果 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/results/op011-v2-CPU-contract-20261015.json` SHAa61641cc4d97413b6c5fac65d4ee5803d55e7902f3221e06bb05cb138ac66acd，XMLaffbf9bbe4d2f8d8a578ab112d7a6ea427cfe14782b5f57fd773349574cdbb67。

应用回执 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/manifests/op011-applied-20261015.json` SHA21ee2a79e4ae95acceffa0315287acaee77e81506bbadbcb20bd9de79ee4503e；新文件SHA：impl/fused_moe.py=9fe42e19b6eed1838813dba41213f68e1b0bc9506f8dd6ddddd890ae2169f053，utils=4f851d2986f844810f5f1b1b096c3f622bb69a243e9bf0ae0df78cfd9495603e。两生产+两CPU测试改变，其余514Plugin文件和其他3repo/模型/完整env/精确服务实例保持，12253文件核验通过。source manifest `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/manifests/op011-plugin-files-20261015.json` SHAaed351c7a172b907a8b29e32da797f7c7ecb2bb8106580783cecf24233ce537e，patch `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/patches/op011-library-public-imports-20261015.patch` SHA1ab20b23bf1f3bfc53a847215f7f1f1c4c609c652a35b271798bb5e638111ad4。apply e0592ea3...已执行不可重放；rollback-op011-public-MoE-imports-20261015.py SHA675559785c3a2b7c6d0937930f2cc38ae342436be554c83fd059a2586436fb10仅保存未执行。

源已写盘，未重启/热重载，candidate=gdn-op005-plugin-f99f9dbb-moe-library-public-4f851d29；旧982315服务加载source历史不变，不声称新模型已生效或通过精度。整体minimal incomplete/PR experimental；新source真实graph/数值/full198GPQA/P1K not_run，旧gate不能复用。用户代码请求完成，不能擅自新开停服或性能流量。

## 用户收窄范围：v3（实施前冻结）

最新用户指出topk调整过多，要求fused_experts仅NV/MetaX放开。收回此前额外topk清理：辅助MoE文件严格等于f99原文件只替换`from flag_gems import`为`from flaggems_vllm import`，恢复原4参兼容、renormalize和原分支继承的重复定义，不另做清理。原宽泛except语义来自上游而非本轮新增。utils共享快路径只增加`device_name in ("nvidia", "metax")`限制，其他平台保留原分步/既有Kunlunxin路径；callerworkspace仍不传。只改2生产+2CPU测试文件，不重启。

v3最小CPU矩阵预冻结77项：公共调用39（含5种非目标平台拒绝快路径）、辅助库契约25（含原4参兼容/归一化/异常）、原GDN守护13。每次完整收集IDs后执行，无GPU流量；硬件/graph/新fullGPQA仍not_run。此前77通过证明的是旧v2范围，不能替代v3。沿同一op011记录；新备份/计划/命令全部v3唯一命名，保护旧证据。

## v3已应用：以本节为当前事实（2026-10-15 19:46 CST）

用户指出的两项范围均已修正：`fused_moe_utils.py`明确`elif current_platform.device_name in ("nvidia", "metax")`；其他平台不再落入完整fused_experts调用，保留原分步/上游Kunlunxin独立逻辑。NV和MetaX共用公共`from flaggems_vllm import fused_experts_impl`和相同参数，不传caller buffers。辅助`impl/fused_moe.py`已逐字验证等于HEAD f99原文件仅把import库替为flaggems_vllm；topk恢复原5参尝试/4参兼容/renormalize。上游继承的重复定义不在本次做额外清理。之前v2的扩大平台与topk清理已收回，旧测试和回执仍保留。

原生CPU77项全部通过，29.03s，0fail/0skip：公共调用39（5种排除平台均到分步路径且不导入完整API）、辅助25（含旧4参归一化）、GDN13。结果 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/results/op011-v3-CPU-contract-20261015.json` SHA0bfb914f0578b6741f6406651130a1a20e7f4c7982710a8efa4d3b8ee539f567，XML SHAffdf857981cb9aabd0fc8d92d376f61133272985435a3701028a1ec541021948；完整收集ID与实际私有导入证据为results/op011-v3-CPU-collected-IDs-20261015.json和op011-v3-CPU-import-paths-20261015.json。本次测试声明按最新用户范围修订，未要求与历史v2 nodeID相同；没有删除失败记录。

应用 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/manifests/op011-v3-applied-20261015.json` SHAb3fa23fa29f7108311a9626ade8e18030b48409596ee4f216f276f1a9a5003fc；Plugin清单SHA1e904d6247656b50b7054aa93a99d85d53f987b4505edb7d3293463dda096d5b，patch SHA0b6f246bb38494809496338f23727c21d058ca8d5dc65831a66a0c4d34a71ea7。两生产文件：utils SHA775a64189d1b0bc77fa7524f1b4ff13e4354d86d1283d6da789e053a72511035；helper SHAff2ecd4321e1c1de249c78b0b33ce4410aa23d8f1059c3a92c243357d2deef55。仅两生产+两CPU测试变动，其他514Plugin文件/其他三repo/模型/完整env及精确API982315实例保持，12253文件检查通过。备份 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/patches/op011-v3-before-MoE-files-20261015.tar.gz` SHA87ce6b263d83fefe483305eb6b883ca24bae7aa69b40a08420839b90a9b55ffe；v3精确回退脚本已保存未执行。所有执行命令SHA在state的command_SHAs。

磁盘候选gdn-op005-plugin-f99f9dbb-moe-NV-MetaX-775a6418；服务没有重启/热重载，仍加载旧gdn+op005源。新source设备数值/graph/full198GPQA/E2E均not_run，整体minimal incomplete、PR experimental；旧精度gate不能复用，新版本性能不宣称通过。automation继续PAUSED，不自动恢复旧算子优化或开启服务中断。

## 用户授权发布（2026-10-15）

用户明确要求提交当前代码到020plugin-opt-metax。先新核容器518文件及已通过CPU77回执，封存准确4文件：两生产MoE文件+两份契约测试。其余3个本地未跟踪测试不混入提交。源快照 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/patches/op011-v3-publication-files-20261015.tar.gz` SHA052f7cf0a6588bf3dd398c2004854250ac61e8b74a23ed5d61956d7c674a9bbe；payload SHA f0a46ac6576c36bcc7c23613a7cc11d88f11122182d65eb773c5830044837597。

已普通快进推送 [b8f2734](https://github.com/ZenithJoyH/vllm-plugin-FL/commit/b8f2734beb80738ce5e4f7c61c2056f41e5c9ba5)，父f99f9dbb，目标ZenithJoyH/vllm-plugin-FL/020plugin-opt-metax；git ls-remote再次确认远端指向完整commit b8f2734beb80738ce5e4f7c61c2056f41e5c9ba5。四文件455insert/11delete，其中测试新增445行，生产仅10insert/11delete；生产helper对原branch仍只是import替换，utils仅NV/MetaX条件和公共库调用差异。提交对象逐文件SHA等于当前容器准确字节。

发布在独立本地临时checkout完成，容器HEAD/index/dirty未变（仍f99+相同两生产patch与未跟踪tests）；这保护原工作区，不是声称容器已切新commit或重启。发布回执 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/manifests/op011-v3-publication-receipt-20261015.json` SHA1e3d6e026553d9ed21fd41c2660613a74ca80eba18b13ba49f01b7b3ec901074 再次只读验证四文件与原index一致。服务/其他负载无操作，automationPAUSED。已通过CPU77，syntax/EOF/secret-marker/diff-check通过；可选Ruff0.14工具下载长时间缓慢后取消，Ruff/fullprecommit未执行，未为格式化改写已验证源码；graph/fullGPQA/E2E仍not_run/PRexperimental。最初本地AnsibleRPC沙箱启动失败后，受许可执行同一mx59connectivity已通过；py_compile缓存写入受限改为内存compile，均非代码回归失败。

2026-10-15 16:23UTC最新：隔离缓存后的正式GPQA已完成，UUID d7e72aff3e6a4a7c8809d3ae7113be32 strict164/198=82.8283%>=80，0timeout；全198/65536/temp1/top_p.95/top_k20/seed42/C32不变，全部filter/原生来源/config/12355源码/当前service/env/model/tokenizer/镜像挂载连续性通过。CPU收尾15:56:07完成，nativeissue/check成功：gate accuracy/acc006-isolated-cache-g64k-accuracy-gate-20261015.json SHA9fdcc14eec68a6203a3c46cbf7e45c46fdcea5474ba4def838119fedaf98a642；terminalcontinuity06b0a111d267331fd8525ed33c6be9b66add1385f36273844fd7c725683b8fb7，terminalvalidation4f6834150a253a745c977c3254a54fd3ba48a6ee734669d5f8e3d30c9e6940d8。未重复GPQA或issue/validator。当前API1025146及GPU6/7workers保持，旧cache/source未动，原19FG范围不变。

缓存隔离执行边界得到反事实支持：相同源码/参数，旧cache启动Vheads8且0/198，新增VLLM_CACHE_ROOT后K/V均1head、两TP各22actualgraphreplay、C1/C8和新full164/198通过；可恢复性能工作，内部缓存key/二进制失效机制仍不作过度确定归因。原始0/198、C1无关输出及私有负面/utility失败全部保留，不改判为通过。该分数只绑定当前组合/环境，不能归因单个Plugin/MoE/library改动或冒充NV验证。原用户启动脚本尚未写入cacheRoot；下次reload须保持隔离策略，不授权未来停服。

P1K新scene-entry基线已16:21:45启动：run-idop013-p1k-full-001，modebaseline/rolebaseline，controller1531875/birth502086404，nativeclientns1032848/birth502086510。完整P1024/D1024/C64/N128/temp1/ignoreEOS/seed42/range0，4warm末3spread<=5%/3measuredspread<=10%/600sround/全轮保留/无profiler。当前仅新scope单实例基线，不能与旧20scope不稳轮算精确gain。新planSHAf0a5bac2...、comparison8bbbadbd...、v2identityb5be1a8c...、observer1dfbb147...、v2launch36841b6f...。Freshsource/gate/APIidle/资源/镜像挂载/timeNS/cgroup通过。首版dryrun因baseline不能传--accuracy-gate而拒绝，0benchmarkrequests/无run目录，原文件日志保留；v2仅修原生接口，外部nativecheck+gateSHA仍冻结在identity/launch，七轮dryrun通过，不放宽测量/精度标准。真实测量尚无结果。

CPU收尾器1533067/birth502096784已16:23:29启动，commands/wait-finalize-op013-p1k-full-001-20261015.py SHAde78eacd2efda4335ae607c3812398f241dca454fc922a37ada40ac5b149d4d3；launcher11b45361...已执行，不可重放。只等现有native退出后finishd14dd85a...与analyzef929f151...，不产生新GPU工作。监控monitor-op013-p1k-full-001-20261015.py SHA3ffd90624dde2d41c84fb96fbe3a88ef0cafdb9b1a5d4775e8ec20e8f5c911d4。终态核native全部轮+稳定性+observer开销+source/gate连续性+compiler/共同停顿时间线；未达稳态/incomplete保留，不丢慢轮/自动加warm。review024首优先本轮baseline，其后按实际当前owner/routing/compiler证据重排；不能切P4K/最终acceptance通过。所有旧creator均不重放，heartbeat继续ACTIVE。
