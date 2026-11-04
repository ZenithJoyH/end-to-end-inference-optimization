# cleanup-006：启动脚本移除缓存环境变量与 Plugin 默认 YAML

状态：**completed_retained**（2026-10-28 11:42 Asia/Shanghai独立核验通过）。用户2026-10-28明确要求删除五个缓存目录环境变量、VLLM_FL_CONFIG和VLLM_FL_FLAGOS_BLACKLIST；配置改由Plugin默认路径YAML加载。Host mx-103，当前容器deepseekV4-flash/73eedc5bc92c，远端任务根/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/launch-config-20261028-01。

本项是已交付容器的配置整理，不开展新的性能优化或benchmark。源码位于容器私有/opt/vllm-plugin-fl，非共享挂载，直接执行用户授权的配置修改；不新建性能实验容器。保留启动脚本其他参数、prefixOFF、13→6项export；无隐藏环境注入，不通过Python设置等价cache环境变量。FlagGems/FGV缓存回到/root/.flaggems与/root/.flagdnn；vLLM默认/root/.cache/vllm（现有共享符号链接不变），Inductor/Triton交由原生运行时管理，不清空任何缓存。

设计：复用现有metax.yaml及load_platform_config已存在的dsv4_config.is_enabled限定分支。把原先Python硬编码的rms_norm/reference、router_gemm_bf16_fp32顺序、topk插入，迁入同一个metax.yaml的deepseek_v4_int8段；仅既有已验证模型身份激活时浅合并op_backends，黑名单列表整体替换。基础MetaX及其他平台不变；已有显式env blacklist/whitelist覆盖优先级保持。不是新增开关/并行配置框架，不复制数值kernel。平台先configure_for_model，worker再次configure_for_model后才注册OOT及FlagGems，实际黑名单可从8worker日志验证。

工程审查：A1-A4/B1/C1复用配置边界，不改算子；C2无新增patch；D1不增加开关，D2脚本七项全移除，D4 YAML单一事实来源并测试默认/模型/覆盖；D5保留topk与masked_fill回退，仅整理来源，退出需独立验证对应FlagGems路径数值/graph；F1配置/覆盖与非目标平台测试，F2最小C1/C8/长输入，F3原生capture与两次FULL replay，F4/F7同一主题、不提交推送；G2测试过程只写本优化案例，不写Plugin用户README。其他平台硬件未测。

计划先保存精确身份、revision、工作区与三文件备份，修改两个配置文件+已有测试及启动脚本。配置测试通过才精确停止空闲本任务API/workers并以新脚本启动；保留旧argv/env用于失败恢复。使用20条既有minimal-regression，不将其签发为GPQA gate或性能等价结论。失败恢复本次文件/脚本，恢复原API；容器不停止/删除，不影响其他服务。原算术C64变异见cleanup-005，非本轮修改范围。

执行前保存命令：commands/prepare.py（SHA以随后核验值写入）。该命令仅创建本轮唯一任务目录、备份三个Plugin文件及用户脚本、记录目标容器inspect/三仓revision及精确API身份，不修改运行环境。

prepare.py SHA `976b93bad09f4f98518b670189e8334509b24f6fe058764e9bb0000594e93505`。初次取证因已安装编译器distribution名称为flagtree而非triton中止（备份已完成、服务与源码未改）；prepare02修正元数据名称，续取证到同一新任务根，不创建第二案例。

prepare02 SHA `610b1cc1ddb878a10490361dae24bbd644be4239dafa3140c99789c851e812fc`；当前服务重新核验后绑定。候选修改仅utils.py、metax.yaml和已有test_config_utils.py，三项原SHA均逐项guard；启动脚本候选先保存，待单测通过由精确重启控制器安装。apply.py及candidate-files.json在执行前保存到commands，SHA见下一条。

取证发现当前容器没有存活API/worker，24599及随后47621等均已退出（Z）；用户service.log尾部记录11:18:33 EngineCore退出。此时尚未执行apply或修改任何源码/脚本，不能将该退出归因为本轮配置改动。prepare03接受“无原服务”事实，不停止任何进程，也不伪造回退到一个已经退出的旧API；后续如资源空闲，用新脚本启动验证，失败恢复文件及原未运行状态。
- commands/apply.py SHA `72e03bccc3691545b11dda9492358270c72c86fc0fb3c5812fcfcc219b8bd50a`
- commands/candidate-files.json SHA `4eb73b7c16f81393b19ba88830a527140dd91d74f4ffc62a0cad6841595b1596`

prepare03 SHA `8932f4754317afbebe3842d03940801ef293fcf0263605b7389a9e017ef3fff7`，manifest/source-process已保存；最后打印仍取pid产生KeyError但只影响终端摘要，不影响备份。source-process真实状态not_running_before_any_source_change。apply已完成，候选script SHA6b04bd83cdf118a9e3f6dabab0959ff109eb404ffafdf43777668bb363870d23，七项移除/六项保留；源script尚未安装。unit-tests.py运行目标Plugin现有config/policy/blacklist测试，Junit与原始log保存在任务根。

52项Plugin原生配置/selection-policy/FlagGems黑白名单测试通过（含新4项模型限定、默认路径、隔离与覆盖测试），无失败。unit-tests.py SHA `d5a0e95d55bc9fcc30b469e4d2d7f0788c7d2f54c69a5a2ac1a86bfd54254dff`。

执行前保存commands/launch-validate.py SHA `4474a0cf3f16586e48bcc541c6f8728986aecac535946c0b49d0c0d2e1ce663e`。guard当前容器身份、script原SHA、无新增用户API；安装已核验七行删除候选，用真实start-model.sh启动。无原存活服务，因此不停止任何旧PID。等待health/capture，执行原20条minimal，审计8worker三项黑名单、API无七变量、FULL至少两次replay、无OOM/非法访存。失败只停止该控制器新启API、恢复三文件/原脚本及原未运行状态。

当前candidate由真实start-model.sh启动：API48735/startticks1157896807（仅本轮运行证据），控制器host2057503/ticks1157896778。日志已明确从/opt/vllm-plugin-fl/vllm_fl/dispatch/config/metax.yaml读取配置；当前等待加载/编译/capture，无重复启动。

最终独立取证commands/verify.py在result通过后执行：逐文件candidate SHA/内容、七变量不在启动脚本、新鲜进程默认目录解析、基础MetaX黑名单未污染、精确API身份/health以及git diff --check；生成final.patch和各原生证据SHA。新进程导入只作配置路径/依赖核验，不冒充其他平台硬件数值通过。

取证改正：启动日志未出现WorkerFL黑名单INFO行，不能虚构8rank已直接观测。现有/tmp/flaggems_enable_oplist.txt在新启动时已更新，包含实际FlagGems/dispatch调用但无三个被排除的ATen实现；logger INFO可见性另核验。原控制器硬性要求8rank INFO属于取证脚本假设，不代表配置功能失败。continue-validate仅按精确host PID/ticks替换本任务控制器，保留同一API和worker，不重启模型、不改测试/期望/源码/采样；继续同20条回归、FULLreplay与环境审计。黑名单证据如实限定为原生注册入口测试、默认YAML启动日志和实际oplist，不声称直接读取8worker值。新命令执行前保存并核验SHA。

verify.py SHA `76584ce6dad3e914ebbda4ce2b8095eb757f7dbd37be5e7da5b746ea54ea9f81`。独立取证首次因模板ROOT全局替换误伤VLLM_CACHE_ROOT标识符而SyntaxError；未修改服务/源码/环境、没有重跑模型回归或回滚。verify02仅将替换范围收窄到root=Path(ROOT)表达式，保留失败输出，继续同一API核验。
continue-validate.py SHA `b1532cc379a2775616230529ae51cfc9c8db2ed45896f8a9de72b2542bb0a239`；native logger probe确认worker effective level30/INFO disabled，未为取证添加永久日志环境变量。


## 最终交付

已更新当前容器deepseekV4-flash（73eedc5bc92c）的Plugin及/public-flash/jinghao/deepseekV4/start-model.sh。脚本SHA `6b04bd83cdf118a9e3f6dabab0959ff109eb404ffafdf43777668bb363870d23`，仅删除用户指定七项export，剩余六项是GEMS_VENDOR、VLLM_PLUGINS、TF32、MULTI_STREAM阈值、TUNED_CONFIG_FOLDER及NO_USAGE_STATS。启动参数、nohup/service.log行为、TP8/MBT4096/seq64/.85/FP8/FULL_DECODE_ONLY/thinking默认及prefixOFF保持。没有添加环境变量隐式注入、profile、startup hook或缓存软链接。

配置自动从 `/opt/vllm-plugin-fl/vllm_fl/dispatch/config/metax.yaml` 生效，不再依赖外部/graph_patch/metax_graph.yaml。YAML的deepseek_v4_int8段集中维护rms_norm/reference、router_gemm顺序以及[topk,masked_fill,masked_fill_]黑名单。现有模型识别分支激活该段；backend映射合并、黑名单列表整体替换。基础MetaX模型仍是原两项黑名单及原RMS默认；其他平台文件未改；显式环境变量覆盖入口保留其原语义。不增加新的模型YAML/JSON或runtime patch，不修改vLLM/FlagGems/FGV数值实现。

独立新进程解析默认缓存：vLLM=/root/.cache/vllm（已有共享cache符号链接未动），FlagGems=/root/.flaggems，FGV=/root/.flagdnn；Inductor/Triton目录由原生runtime管理，脚本不再指定。旧/tmp/build-fg、/tmp/build-fgv和共享编译缓存均未清理。缓存目录及编译产物变化可能改变首次编译时间，未测量或声称性能等价。

52项Plugin原生单元测试通过；20/20固定模型回归通过，含C1两条、两轮C8、两条>10K非对齐长输入。目标服务已完成graph capture，原生FULL C1 count10/C8 count2及padding replay；8worker身份核验、API七变量缺失、health200，无OOM/非法访存/MCCL错误。worker INFO日志因有效level30未直接输出黑名单；证据为真实配置加载路径、模型注册入口测试、实际更新的oplist无被排除ATen实现及连续模型回归，不伪造8rank直接观测。原生日志的xgboost缺失AUTO fallback为继承状态，不在此项升级依赖。

这是e2e/accuracy minimal-regression，不是新的GPQA gate、历史87.37%重绑定或无profiler性能比较。其他平台硬件未测，相关路由/隔离mock只代表配置行为。整套历史适配PR状态不因本窄补丁自动变为ready_for_review。源服务在本轮改动前已退出；新服务是按本轮新脚本启动。未自动提交或推送。

原始产物位于远端任务根：
- final-verification.json SHA `ef94dd86adb34a382dbbbcc6da30c1bc487f2f5fda3e18b037add55ad1933a32`
- result.json SHA `652df3b137876b84beb1b67748ca1f206568630e2f9a50004d3d0648e964d202`
- unit-test-result.json SHA `982f2c1f54e496fec21a5ef4a26ab9854cac2a58c561bd7170ab72fbdd092385`
- minimal-regression/result.json SHA `4774c4869c0373f56f1d1633090e33af4ebbf05b527b39e23f407ea975b62291`
- runtime-environment.json SHA `c48941442c6f7e111c13ff2e3188943f5d86a610915e78b8941ec9fd5973f275`
- final.patch SHA `3a2ee1d5c7e12e074b9609c0596169d3461b0efec7cbd220bdd6cb3a55ef1ed6`
- commands/verify02.py SHA `76fef7bcdd46f3640c0afb4aa51033f869df18f72664aafb3a49e3db16107f36`

回退仅恢复backup中的三文件和start-model.sh；不整体Git reset、不清缓存，不停止或删除容器。若需停止验证服务，先重新核验当前精确API/startticks及子进程，再恢复文件与脚本。原始无存活API状态不能冒称恢复一个历史PID。控制器/取证脚本问题与全部失败信息已保留；没有为脚本问题修改模型输出期望或重启当前已通过模型。


## 剩余三项环境变量只读复核（用户后续询问）

本次未修改脚本或重启服务。进一步按实际覆盖方法而非仅grep读取点核验：
- VLLM_MULTI_STREAM_GEMM_TOKEN_THRESHOLD：原生vLLM默认1024，但当前DeepseekV4NativeAttention.attn_gemm_parallel_execute（ops/deepseek_v4_attention.py:476）已覆盖原生方法，不读取该变量；模型make_layers显式aux_stream_list=None（models/deepseek_v4.py:218），attention亦保持None。因此=0对当前MetaX V4 INT8路径冗余；不能推广到其他原生DeepSeek模型。
- VLLM_TUNED_CONFIG_FOLDER：原生MoE/LoRA/mamba存在读取点，默认None；当前W8A8 MetaXExperts通过_shape_configs读取policy.moe.tuned_config_folder，由configs/deepseek_v4_metax.py:117指定Plugin包内ops/deepseek_v4_metax/tuned_configs。不是从外部/tuned_configs/H=4096选择当前主路径参数，因此当前模型不依赖该export；其他模型/备用原生MoE路径不能一概认定无用。
- VLLM_NO_USAGE_STATS：默认False；=1仅关闭vLLM使用统计，usage/usage_lib.py:is_usage_stats_enabled还支持DO_NOT_TRACK与用户文件。不影响模型启动、推理计算或graph。移除会恢复默认统计策略，可按部署偏好保留。

因此三项均非启动硬性依赖，前两项当前路径冗余，第三项为可选遥测设置。此前cleanup-004保守保留两项的理由只证明原生读取点存在，不能证明当前覆写路径实际使用；以本次更具体的路径核验为准。本次只读结论不冒充“删去后的启动/精度/性能已回归通过”，现有脚本及cleanup-006结果SHA均不变。
