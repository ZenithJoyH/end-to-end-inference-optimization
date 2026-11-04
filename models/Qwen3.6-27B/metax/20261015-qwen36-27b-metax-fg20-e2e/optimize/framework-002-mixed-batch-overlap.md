# framework-002-mixed-batch-overlap

最终状态（2026-10-16）：本轮回退三阶段与离线Decode定位均已完成；性能整体 **incomplete**，metadata候选不保留。9份原生record、87轮/27 measured、9408请求0失败，plan/contract/client/service/raw/validation SHA全部复核；未删除任何慢轮，10%spread/1%回退漂移/5%guard及原数值容差保持。以下原计划与过程按时间保留，旧pending/incomplete环境表述表示当时状态。

| 阶段milestone | baseline吞吐 | candidate吞吐 | revert吞吐 | B→C | B→R吞吐漂移 | 原生结果 |
|---|---:|---:|---:|---:|---:|---|
| Prefill P1K/D1/C64/N128，total tok/s | 5694.1523 | 5727.1996 | 5686.6342 | +0.5804% | −0.1320% | passed |
| Decode P1K/D512/C64/N64，output tok/s | 940.8560 | 943.2032 | 939.4023 | +0.2495%观察值 | −0.1545% | incomplete：baseline meanTTFT spread13.4452%>10% |
| Mixed P1K/D256/C64/N128，output tok/s | 700.4087 | 702.2617 | 698.3162 | +0.2646% | −0.2988% | failed：未达2% |

三个阶段全部决策指标的最大绝对B/R漂移分别0.229913%、0.998445%、0.721919%，均保持原1%要求，Decode P99ITL接近边界仍原样报告。候选全部延迟guard不超过5%；Mixed P99 E2EL由29236.3737升至29459.2046ms（+0.7622%），平均TTFT由5814.1919降至5759.5441ms（−0.9399%）、平均TPOT68.6348→68.6138ms（−0.0305%）、P99ITL1481.0090→1474.7551ms（−0.4223%）。Prefill平均TTFT−0.6162%，Decode平均TPOT−0.2104%均限本场景；Decode有效性失败不能因中位数较好而忽略。所有B/C/R共同采用OP003 full修复，这些增量只解释metadata，不是full修复的独立收益。

控制器退出，terminal SHA `a47dda84a2f8ff6c950d921d540b89d3f62c6c95089e8a5400c0960d834cdbdf`。原生比较SHA：PF `252f3a598757d0cb149d174836a91c4fdecdbad752abfc826ca067ad2543ed37`，D `5e0a9d6dc7845332bb28607c425efdfc0bcd04ab42d8ab977b2c8f70e7471b30`，M `436a5155ce17262e04b0f6b842ac5a99d67a0041b8bc36cd4ea52a4cc9ffa4d7`。回退D/M record SHA `b13f5d23f0728d76adb66958bc34c43a125973e98cea0a9832a634cb1b6b28fe` / `2f832130b068bdcbac2b29c7c2251377cf550fce65b1ee4ef484e48f66d56aed`。

独立C恢复Plugin/full两原件及原4repo，无本case模型进程；源S恢复qwen36-addgdn/18002、精确PID954040/create1792130229.17，full20/noBlacklist/attention1、TP2/GPU2,3/8192/graph64和原4repo全部核验一致。现役源模型路径仍为用户重新下载的新路径。原8002/其他GPU/权重/tokenizer/vLLM未操作。原服务现运行原始full版本，两项实验补丁仅归档，未部署/推送。监控已按终态暂停。

### Decode TTFT波动定位：重复GDN JIT与未覆盖key

正式测量r7/r8/r9的平均TTFT为7768.6492/6848.8802/6847.8062ms，原spread13.4452%。r7的64请求仅15.999ms内全部发起，排除客户端分秒级串行发送；前token分组由常见1+7+8…变成1+1+7+8…，多出早期小批次。输出在相对t=0.6768～2.8799s有2.2031s停顿，常规对应长gap约1.44s。后续逐token均值TPOT54.5479/54.5115/54.3983ms基本相近；异常集中于该Decode milestone的残余Prefill/早期调度，不是把TTFT当纯decode设备时间。

已保留的baseline专属Triton缓存显示：r7相对t=0.8240～1.4399s产生 `chunk_gated_delta_rule_fwd_kernel_h_vmajor` 新编译产物，编译中间文件至binary区间0.61598s，落在上述长gap内。暖轮r1也有3次新H编译，对应其更长前几组TTFT；r2～r6与r8/r9没有新H编译。利用请求单调时钟与节点wallclock offset对齐，并交叉核对原生date；`/public-flash`文件mtime落后节点时钟约202秒，未拿它直接对齐本地/tmp缓存。

源码机制：该FP32路径已将H候选prune为BK32/BV16/4warps/stages3，但`N_BUCKET/SKEW_BUCKET`仍是autotune key及未参与kernel数学的constexpr。9个不同cache目录的lowered source SHA均为`2c7ac0f488957606188aff7c9e5fe5cef7915879073b2e98785376608579e8fd`，binary SHA均为`be2058672cdf0b7259a14fefa6aedd351a4d16a0a1ae4dda08848fd596c1c716`。动态首批构成变化与新key重复JIT是本次波动的强证据；固定6暖轮且只看吞吐的准入未覆盖全部稀有key。不是将本例重定向为优化冷启动：第7轮已经进入预先冻结的measured，发现服务运行中出现新key后必须保持原结果incomplete。

边界：历史r7没有双rank详细trace，未还原精确bucket二元组，不能把平均TTFT的全部约0.92秒差值都精确分摊给编译器，其他CPU/driver/GC的剩余份额仍未知；这轮没有新GPU请求或源码改动，未通过新A/B证明任何GDN修复。延迟证据不证明数值异常，不改变FP32/IEEE、.002/.02或20项白名单。

下一步排序（rev016，仅计划未执行）：优先验证FP32固定配置下去除无用bucket特化的稳定key方案，先检查compile variant、原数值/graph矩阵、真实模型命中/C8；然后按测量前冻结、所有角色相同的key覆盖与延迟准入重建三阶段B/C/R。任一数值/graph失败即停；不能修改旧r7或仅补一个快轮使旧比较通过。不再因metadata仅0.26%收益继续扩大该改动。

离线审计命令 `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-decode-offline-diagnose-v1.py` SHA `44eeb03a2401c5b2f6f7791bb46e7867ced97514fe46ccd6e20eb7d7f44c84d7`；输出 `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/results/fw002r4-decode-diagnosis-v1/audit-and-diagnosis.json` SHA `85c4efe894feda59aca2c460bdf911652e16b85a260d35ecdc533a78dc7bfc84`，其中9份source/ttir/binary/metadata均已按SHA归档到同目录cache-evidence，GDN源码另存。最终恢复验证JSON同目录 `restoration-verification.json` SHA `e0a618db8d489f952937bdd438b8e53f606de06603cb4ec33d4b7772f7d3f563`。当前20项无正式198gate，不宣称四场景验收。

---


状态incomplete/external-model-directory-missing；完整Mixed归因和数值通过，模型graph/三阶段待恢复权重后继续。用户2026-10-16明确要求继续Mixed批次插入和CPU/GPU重叠分析，吞吐优先，保持全部20FG和原atol.002/rtol.02。沿用当前案例/已专用复刻容器，原baseline/source/de2298b+5/cb45与TP2GPU2,3未变；先重新只读核验镜像/挂载/四repo与精确现役身份。用户先前暂停18002并恢复的授权覆盖本轮同一服务，不操作原8002/其他卡/shared/vLLM/权重或用户脚本。

已有三阶段基线和OP002真实ABI B/C/R：Decode+1.39%/Mixed+1.33%未达2%，候选撤回，不再做tile/warp搜索。Mixed P99ITL~1.49s与强制新prefill相关只是待证假说，前64迭代trace未覆盖第二cohort。本点先capture再analyze，用完整相同Mixed P1024/D256/C64/N128、T0ignoreEOSseed42、3runs/2warm/最后profile、每round600s、profiler max_iterations0不裁剪；两rank/CPU标记/graph correlation/实际GDN+attention命中，检查完整首批、后续prefill插入和排空。记录相对原native无profile统计、不要把profile耗时当性能。trace原始与分析脚本留远端。

首个证伪：若CPU/GPU timeline不覆盖两cohort或缺rank/边界，保持incomplete；不按热点worksum臆造criticalpath，不用短窗口给P99ITL归因。比较CPU调度间隙/主机同步、实际prefill设备干扰、通信/rank不平衡与client限制至少两个解释。若已消除主机间隙，不能为CPU重构选点；按真实机制在配置或Plugin最窄扩展点选一个变量。不关闭FG或把FG目标dispatch绕成vendor获益。

候选尚未选定/源码未改；选择后在首次性能测量前冻结实际变量、边界、原数值/graph/C8与三阶段对照契约。计划仍为PrefillP1024/D1/C64/N128、DecodeP1024/D512/C64/N64、MixedP1024/D256/C64/N128，父正式目标P1024/D1024/C64/N128；scope targeted/diagnostic，非full正式验收。原20FG当前无正式198 gate，不复用旧all21/166。保持源码/数值语义未变的配置低风险候选用新graph两次replay及fresh10docC8验证；若涉及高风险数学/图语义，必须补正式精度或不实施。

最终新baseline/candidate/revert各phase6/6/8warm+3measured，固定末3throughputspread<=10%，全部轮/慢轮保留，全部比较指标spread<=10%、回退漂移<=1%；主Mixed输出>=2%且Decode无>5%退化，跨阶段吞吐/延迟守护5%。若目标机制也改善Decode，分别报告，不能要求无关主指标必升。不得因结果临时修改准入/容差，失败回退并保留。结束恢复原20FG/8192/graph64源18002与独立容器原代码，监控终态停用。不提交推送，不自动改用户脚本。

远端根：`/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e`。所有命令执行前保存且SHA写回state，当前独立container为qwen36-27b-fg20-e2e-20261015/18012，原服务qwen36-27b-fa-opt-20261012/18002。

执行前命令/SHA：
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002p-service.py` SHA `469f30a9d9bb515f0c3505ac435c5bb9c4c1ef1b0652be3647613dd8318c17ee`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002p-controller.py` SHA `e0929a3a05efedaebc4c05b03f755575abc4225aef2e542a81ccd23c270f54b9`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002p-launch.py` SHA `5121aac5b5322d4275282792135bede9644acf55a8cba886dc7550b311f96792`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002p-c8-config.json` SHA `f6e43cb5a67c58b8a69918635803050a44a7793d1e7842e89d2271893da96fad`


分析结果与唯一候选冻结：两rank各128个new请求、526个CPU execute事件（524活跃+2空）、19个含prefill/505个decode迭代，99.698% GPU kernels按launch correlation关联，后续插入在iteration258–268完整覆盖。prefill设备span中位约1.505s；decode迭代间无设备活动的间隙中位约0.10–0.11ms，暂不支持重写CPU调度。GPU活动union仅占本trace跨度93.7–93.8%，不是硬件利用率或criticalpath分解；engine-core调度CPU未直接采集。v3误将GPU镜像同名range重复计为1050步，已保留为无效phase分析；v4只取CPU user_annotation修正，不重采trace。

当前prefill native MetaX attention每层都`prefill_seq_lens.tolist()`→GPU tensor→int32 cumsum。完整轮19×16=304个unified_attention调用；一个明确例子是BF16 query[8192,12,256]/kv[8192,2,256]，int[8]元数据D2H等待79.42ms，随后创建int[9]前缀和。该等待含前序GEMM/GDN工作，不可把累计20s都当可消除时间。将GPU权威seq_lens在每次metadata builder末尾快照一次，生成同一int32 prefix供同组各层只读复用，消除重复同步/分配/launch；不修改attention kernel、数学或dispatch。未选择局部budget8256的本地准备模板，未上传/执行，不做多配置扫描。

设计归属：framework，唯一MetaX vendor backend文件，新增两个metadata可选字段和窄helper，builder每步创建新对象（无跨步/全局cache）；decode无prefill、cascade、DCP>1不增加工作；外部手工构造metadata仍用原helper回退。原16个attention层共用本步metadata，后续模型重启/新步必须新建；检查同一GPU长度缓冲区原位变化后新metadata不会继承旧prefix。非MetaX导入/实现未改。所有20FG保持注册，原有FGcumsum仍执行，只减少冗余次数，native attention仍是原基线实现。Plugin/vLLM0.20.2/MetaX C550限定，其他平台硬件未实测；experimental，禁止提交推送。

数值oracle：GPU权威量化/整数输入不变，原方式生成prefix与独立CPU整数累计校验；原native paged FA使用两组相等prefix比较BF16完整输出，保持.002/.02；覆盖单/多prefill、partial/context、非连续seq_lens、每步缓冲复用与int32边界。模型全graph新启动+至少两replay/真实P>128元数据路径命中、fresh10docC8后才测量。FP32 GDN源不改，不以C8冒充198正式gate。原三阶段baseline/candidate/revert全部新测，主Mixed>=2%、PF/Decode哨兵5%guard、全部spread10%/B-R drift1%冻结不变。

E2E执行前SHA清单：
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002e-source-service.py` SHA `4663dd2d6f481f8b14fc999f34ef11b7f926b16c7a6d053f5b005d7da1bda886`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002e-model-service.py` SHA `e0ec11368472973bbac98e612c0a3610fe1758e588c2d420ae80d928ae1a90f9`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002e-controller.py` SHA `bd042c4c493a2aebb5a61811e1ddc867d913e0adce8c06dd66f186e5759a1313`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002e-launch.py` SHA `cf584bf1c801b6d2ac67ba1c9f34fa322369e5b0ee2063c2aea23bf3d08ebfc5`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002e-numerical-launch.py` SHA `9b81c5d648b6118ab24929fbc1a6ba62d74da597eec4b17ee58f3439753c61b1`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002e-numerical.py` SHA `de755b3344302c6e95a2c45d65d3f4493b43901b50431cecc4a7c626240263fa`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002e-prefill-plan.json` SHA `60302fb08cf63837f88a3dd2a139daed65e46a97abd825a5054edeb6710a8949`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002e-prefill-comparison.json` SHA `91685a4335355849d0590ab5395443b754c01333626e4c03f1f814503be4f455`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002e-decode-plan.json` SHA `48d98d29593e59e52a156177f41ee46deb1528078739e55a8920fabfe9e13578`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002e-decode-comparison.json` SHA `d1c7a0503428257addcb7947470fe8d38f55edd0e4c2e8d203e97b338a90eac9`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002e-mixed-plan.json` SHA `26ef74a0c790c171eb1ef920f4a8326c6f2667b30c368afab523cfde19f1fce4`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002e-mixed-comparison.json` SHA `a88b1dde533dcc796e04891ddddb4c7ba628061ca2c882941351c4291acebce1`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002e-baseline-c8-config.json` SHA `ad8d336801a834c27a83a2d4e32d31d242afc2fc042afaa9c23f3492055b675e`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002e-candidate-c8-config.json` SHA `f0d24ba70ce91c0589242ba9694a7795d9431e6925366fbf60327ac4e350df86`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002e-revert-c8-config.json` SHA `28a0479cdc5d61147e93799ef3fb42f4a12657bacedebd7d93daf2dfe56d0a41`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/patches/fw002/flash_attn.original.py` SHA `9a1e87cb97b9ec3283351e3e75d8a25f81c9800fc140661e094eb0da7c2c2bae`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/patches/fw002/flash_attn.candidate.py` SHA `c4d25e9fbe5594f8a49c28d00378d2a98841c323199e600d7c5b3de2fbf24f57`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/patches/fw002/candidate.patch` SHA `16063115e13b63b96a0d6acca0973070e6e970263900b07a7dcdb5cec1d57e37`

唯一E2E控制器已启动：host PID1820698/create1792116497.35/startticks505605635，回执SHA `63f843189226dab30b47c3ec5115cb5dc875dfefe235ec1bf7ca80d42e256fce`，master SHA `bd042c4c493a2aebb5a61811e1ddc867d913e0adce8c06dd66f186e5759a1313`，inputshas SHA `1a150f2dce49801b7e48e48fe99008c1a2b1d8d93655ec4dc3356b49f46de719`。源暂停/恢复授权沿用，30分钟只读监控已精确绑定此控制器；当前不宣布收益。

控制V1在模型启动前因producer fw002e-source-process/consumer fw002e-probe-source-process路径不同而中断，0benchmark请求/候选未安装；14prefix与5BF16pagedFA全部逐位相同的数值结果保留（SHA `bcaec2ef2f6658ecab67a9a4b4b4d98b1f58e14db028612295b0f8decd1c7f04`）。只修控制路径，新增r2独立ID，复用数值不重测，先等V1原源恢复终态。静态producer/consumer文件名交叉预检已补，所有同一候选/计划/门槛不改。

r2执行前SHA：
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r2-source-service.py` SHA `4db6272fb22eb6c2029da45fe9a28ab7f41ad32abb8b84c6a390d0cb6a8121b5`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r2-model-service.py` SHA `77241bf00ec6d0e8e4fad360316a0265d6e0eeb5c698a2989432eba399345735`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r2-controller.py` SHA `076e3a324e341010aeeca2bf768a54ab26afb9dbec93684b459b7d2da6df6403`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r2-launch.py` SHA `86c4d2593549750bbe60b2ed284fe49f8cf18dc3065eb02e1ceb1e2c3abde0b7`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r2-prefill-plan.json` SHA `60302fb08cf63837f88a3dd2a139daed65e46a97abd825a5054edeb6710a8949`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r2-prefill-comparison.json` SHA `91685a4335355849d0590ab5395443b754c01333626e4c03f1f814503be4f455`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r2-decode-plan.json` SHA `48d98d29593e59e52a156177f41ee46deb1528078739e55a8920fabfe9e13578`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r2-decode-comparison.json` SHA `d1c7a0503428257addcb7947470fe8d38f55edd0e4c2e8d203e97b338a90eac9`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r2-mixed-plan.json` SHA `26ef74a0c790c171eb1ef920f4a8326c6f2667b30c368afab523cfde19f1fce4`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r2-mixed-comparison.json` SHA `a88b1dde533dcc796e04891ddddb4c7ba628061ca2c882941351c4291acebce1`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r2-baseline-c8-config.json` SHA `0627b7d6076d39fb86d80687aac2007d0d7a033c3a33dc9046f4f2870bb95b61`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r2-candidate-c8-config.json` SHA `9bdebc3f466c402987369b1b328d68c08f85e822d75b7820b8cbf1c3ba88b860`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r2-revert-c8-config.json` SHA `cd871f9c828597d7dc0ef4d95120771d326ec140ece5353086a4d236ae6ef1e7`

r2唯一控制器已启动：host PID1834650/create1792116901.33/startticks505646033，回执SHA `9456e5e5afdd3aaafa1087a4f6b9af8338164e1fc674e8db6665c181636294b5`，inputshas SHA `c1c96c07a0b0069265967fb28743c9beba3178a304bdd10843eb8b9fc9ab0a21`。原V1已安全恢复终态，无历史模型轮重复；新原生B/C/R仍待结果。


本轮当前终态（2026-10-16，北京时间）：r2基线API进程209190/create1792116961.58在加载模型配置前退出，vLLM报告Repo id格式错误。进一步只读核验Host、源容器、独立优化容器均不存在 `/public-flash/models/Qwen3.6-27B`，父目录仍存在但没有匹配Qwen3.6/27B的目录；这是模型路径外部消失，不能归咎本候选数值或kernel。此前完整Mixed采集成功且旧V1于10:13恢复过原服务；r2在只读weights元数据核对后、基线模型实际读取前目录消失。本任务没有删除、重命名、移动或写入模型/tokenizer。

候选未安装：C私有Plugin目标文件仍原SHA9a1e87...，原4repo基线无候选变更；r2只完成prepare-identities，API基线失败，没有benchmark轮或请求。14整数prefix用例、GPU同地址新metadata快照和5组真实BF16pagedFA输出全部逐位一致的数值结果仍有效；模型候选graph/C8与三阶段性能均not_run，不能声明端到端收益。初版控制路径失败及其安全恢复结果独立保留，不能与此次外部路径缺失混为一个问题。

只对本任务精确host控制器PID1834650/startticks505646033/回执9456...发送SIGINT，先确认其基线209190已zombie、C无活动model workers、GPU路径原件不变且0runrecords；控制器保留终态，stop-baseline遇到已退出API的身份查询失败，记录restoration-needs-inspection。没有信号发给其他模型/其他GPU/源8002。原18002已按用户授权暂停，但当前因为权重目录缺失**无法恢复运行**；没有盲目重启或选择替代权重/路径。监控已暂停，已询问用户原目录是否移动及新路径。

阻塞证据：`/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/results/fw002r2-model-path-blocker.json` SHA `33f34bb93c044fe7517316acc1c6accc041bc964dbb86846a6cc62a009f5af56`；r2控制终态SHA `2c9fa01ebef894967da3f34e047e063e6ded201b8d2148a17b947a21f92fea84`。复现/取消命令在commands/fw002r2-stop-blocked-controller.py，SHA `dea88b31e80bc561dc0fb98a27af30420f46ac52132d8685ef981a6f56415034`，执行前已保存。恢复条件是用户恢复原目录或提供新路径，先重验原25权重/config/tokenizer文件SHA，然后优先恢复原20FG/8192/graph64/18002服务，再以同候选/原容差/同三阶段冻结契约继续。既有有效数值和trace复用，当前0模型性能轮，无需重复已完成测量；不自动重新下载或更换模型、不放宽门槛。

### 2026-10-16 用户重新下载后的恢复检查

用户确认已重新下载。当前Host/S/C仍无旧路径，聚焦父目录发现新权重位于 `/public-flash/jinghao/qwen3.6-27B/Qwen3.6-27B`。先完整核验原25文件SHA；仅在完全相同后，以新路径恢复原18002（其余参数及全20项FG不变），不修改用户启动脚本或目录挂载，不创建旧路径符号链接。模型路径变化将同样应用新baseline/candidate/revert并记录，不复用旧性能轮。

- 命令：`commands/fw002-verify-redownload.py`，SHA256 `cfc0d0a1badf7cfbbf9f0a200359523b948ac55a39bde58a940907584a2199a9`。后者仅在SHA通过且源容器无模型worker/18002无占用时恢复服务。
- 命令：`commands/fw002-recover-redownload-source.py`，SHA256 `2ec7d1fc9b0515680ddaddb996e2009e1c92368790581e63e765bb08dea38730`。后者仅在SHA通过且源容器无模型worker/18002无占用时恢复服务。

原25文件完整SHA全部相等，新校验回执 `results/fw002-redownload-verification.json` SHA `04ab4ce7c50bcdda8191a792ee030a6288f09a6e66b81c0e39e71f5667296cce`，模型/配置aggregate7824cd94...、tokenizer aggregate d2a1ebf0...与旧身份相等。额外文件含README/LICENSE/merges.txt，不改既有25文件；新文件mtime仅用于后续同轮变化检查。源恢复新PID931048/create1792118419.96已启动，readiness待核验。

r3沿用同候选c4d25/原数值证明、原20FG与.002/.02、同2%收益/5%守护/1%漂移门槛，新三角色统一新模型路径；只修控制器的已退出API处理及ready时主动检查精确API存活，防止外部路径丢失后等待整段超时。不会复用旧性能轮。执行前新命令SHA：

- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r3-source-service.py` SHA `378133ea4c44dce12bd054e5070c2475b117fb7184d0c16bccd7466f83d3e348`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r3-model-service.py` SHA `67b15e6ee9c1c9bf6f0afbfa34e3a541d0bee6c64c7dafac5fdc578ac12a1782`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r3-controller.py` SHA `964fc8bb560761ef779bf4dae90f3ba0457b5ce4858988ead4d94dc0ad003cc1`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r3-launch.py` SHA `137fb3b64a990520bd677c7e1794328877a0e6dc3d3290a8fd8f1f964e31c86e`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r3-prefill-plan.json` SHA `4375ddfcc3619b618a017fc5ffdeca96325ceeaba2b23076f544dfb8bac232fe`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r3-prefill-comparison.json` SHA `91685a4335355849d0590ab5395443b754c01333626e4c03f1f814503be4f455`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r3-decode-plan.json` SHA `df42552abeecd4904665de303c8f3604d4d65ae0033caf437d58423213bb9088`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r3-decode-comparison.json` SHA `d1c7a0503428257addcb7947470fe8d38f55edd0e4c2e8d203e97b338a90eac9`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r3-mixed-plan.json` SHA `e6e50f2bd1f98f758d7ae8d4f98939e5cdfd4ab8a19709c7b8aab8f0b6ca27f8`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r3-mixed-comparison.json` SHA `a88b1dde533dcc796e04891ddddb4c7ba628061ca2c882941351c4291acebce1`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r3-baseline-c8-config.json` SHA `5191bb82dd9cf68338c1db2362ce8d264e0399471878279f57367c2302ab2992`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r3-candidate-c8-config.json` SHA `afedc71439f2efc8612aaddfe32ab5a6a6882320a55863b793c927b1b14a138e`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r3-revert-c8-config.json` SHA `f430bde967043a497c8c5dfbcf6079fbcc94fd6111985c6414adf029f714afec`

原18002新路径实例931048/create1792118419.96于2026-10-16T02:43:25Z /v1/models确认ready，原源码与启动参数（仅模型路径改变）已经恢复。随后按用户授权精确停止，r3唯一控制器1851417/startticks505818463/create1792118625.63启动，process SHA `7b25cb375191b9c3a90ee419e91e055b9e24ab50fe26eb14ea35e3a9bce43afb`；worker SHA `964fc8bb560761ef779bf4dae90f3ba0457b5ce4858988ead4d94dc0ad003cc1`、inputshas SHA `5d46fec5d743ab67681c83f97db681cc4844359c2e049e06998253b554981da9`。已完成mount/source/新weights元数据门禁、capture/stop source和prepare identities；当前waiting-private-model-ready，没有候选安装或性能数据。30分钟只读监控已绑定新精确回执并ACTIVE。

用户2026-10-16明确授权将启动脚本改到重新下载的实际路径。只替换模型路径一处，20FG/8192/graph64及其他参数不动、不重启服务；修改前原SHA0b6381匹配并保存原件，bash-n通过后原子写入。执行命令 `commands/fw002-update-start-model-path.py` SHA `f9c203c042f09f14a20cfdab66e977ec71439e0532894640e6c7cf8a35189325`；当前r3基线Prefill/Decode已complete，Mixed进行中，不重复或打断既定控制器。

启动脚本路径已按用户明确授权更新，原SHA0b638...→新SHA `ce05fbfeceee26a65debdc41867ce48332a42ff30b035e2290e7520565b2ff21`，回执 `results/fw002-start-model-path-update.json` SHA `99001f91baab47a3f91a8f348fdb89940f36c21f5fadf22c43bd742b5ac313e0`。仅一处路径替换，bash-n通过，原件commands/fw002-start-model-flagos-before-path.sh保留；未重启服务。r3初始脚本旧SHA检查已完成，三角色实际启动来自已捕获的新路径cmd，未读取脚本二次生成配置，因此本次用户路径同步没有改变B/C/R变量/契约，无需重跑。

基线实际实例209762/create1792118686.11，runtime SHA d6724c3f...，双rank各31graph replay/112attention调用/224整数copy/336精确FP32WY，packed grid[4,1536,1]/block64；10docC8/20rows通过。Prefill原生complete、6warm+3measured/每轮128req0failed，total吞吐三轮5640.676/5641.706/5643.660 tok/s（中位5641.706）；Decode complete、6warm+3measured/每轮64req0failed，output三轮941.148/940.144/939.660（中位940.144），p99ITL47.627/47.074/48.087ms。两阶段warmup准入通过。Mixed目前预热进行中，候选尚未安装；这些是基线绝对值，不是优化增量。

### r3 Mixed基线稳态准入失败（2026-10-16T03:15Z）

只读核验原record SHA `ca6b10a4545700cb238e3667f998b2bae0e4c490add75eb02a95f0ee958e7689`，8轮warmup全完成128请求/131072输入token/32768输出token且0失败。吞吐依次623.288、554.219、699.303、698.831、698.393、697.613、699.048、623.685 tok/s；冻结末3相对spread10.8030596%>10%，native failed。0measured，不能挑第3–7轮替代固定末3，不把预热中位当收益。Prefill/Decode各3measured仍独立有效，但整轮E2E incomplete，候选未安装/模型graph与候选PF/D/M及回退测量not_run，无法判断候选端到端收益、延迟变化或B/R漂移。不是候选数值失败；原模型基线自身波动，根因unknown。控制器正在停止基线并按既定流程恢复原20FG源码和18002，不追加请求/重试/改变契约。全部8轮raw/validation SHA逐项已只读匹配。

准入失败后只读审计：PF26/D26/M24个原生record引用（raw/validation/plan/contract/service/client等）全部SHA匹配，各record inputs_verified_before/after均true。两容器4repo与目标file9a1e原件一致，C无活动model/worker；S新恢复实例938713/create1792120565.55，20FG/attentionflag1/no blacklist/8192/prefixoff/graph64和新权重路径均匹配，正在完成加载/graph，尚未宣称ready。候选patch及数值证明保留但未安装，未自动重试或修改契约。

### r3 最终收尾：incomplete / original restored

控制器终态 `results/fw002r3-terminal.json` SHA `d6e2b370cbee4b33e1d1e6180fc00a9cc67bae17d299b4d4c3fa9b0e58387849`，status `completed/incomplete/baseline-admission-or-measurement`，无控制异常/恢复异常；这里completed仅指控制流程结束，性能实验仍incomplete。

原服务实例 `qwen36-addgdn:938713:1792120565.55`，回执 `manifests/fw002r3-source-restored-launch.json` SHA `5d47f6c0b8042be589507bdbbd3ad41f1a45537a2f030d56565b905f0c1906fb`。2026-10-16T03:19:40Z GET /v1/models确认18002 ready且指向已核验新模型路径；source log graphcapture/engineinit完成，GDN prefill/packed dispatch各2条。监控没有发送模型请求验证源服务replay，也没有签精度gate/rebind。两容器4repo和Plugin目标原件SHA相等，独立容器无活动模型worker。全20FG/.002/.02和用户授权路径修改保持，源8002与其他GPU任务未操作。

| 阶段 | baseline原生状态 | measured | 基线吞吐中位 | candidate/revert |
|---|---|---:|---:|---|
| Prefill P1KD1C64N128 | complete | 3 | total5641.706 tok/s | not_run |
| Decode P1KD512C64N64 | complete | 3 | output940.144 tok/s | not_run |
| Mixed P1KD256C64N128 | failed warmup admission | 0 | 无有效实测值 | not_run |

共26基线轮/2752个原生记录benchmark请求/0请求失败；PF/D共6个measured，Mixed仅8warm。不把上述基线绝对值或暖轮当作优化收益。没有候选端到端收益/延迟增量或baseline-revert漂移数据，数值证明仍仅是既有14prefix/5nativeFA逐位相等。候选模型graph/C8因前置基线失败未运行；不是候选数值失败。微基准、profile等待时间都不替代缺失对照。无新formal198或四场景验收。

监控已按授权终态PAUSED。原脚本backup、新路径脚本、新旧控制失败及所有慢轮保留。下一轮应先定位原路径Mixed波动；需按新冻结计划统一重做B/C/R时另行记录，不挑轮、不放宽门槛、不复用本轮原样本冒充新比较。本监控不追加测试或修复请求。证据仅支持scoped observation，不修改SOP，也不把波动归因于候选数值或FP32。

### 用户授权续定位基线Mixed波动（2026-10-16）

先使用原8轮native stream start/TTFT/ITL重建快慢轮；不新发请求。原生max_concurrent_requests按秒桶统计，不拿88冒充semaphoreC64失效；实际stream时间戳重建并发另核验。逐token中位44.4ms几乎不变，只能提出额外插入/停顿假说，不能直接认定内核稳定。执行前保存 `commands/fw002d1-analyze-existing.py` SHA `c28ecc856a480a034a6583b59bc185598cc5e62f1f2c286f35182c561e6ce1b9`；输出results/fw002d1-existing-analysis.json，保留所有轮。数值容差、FG20与10%准入不变。

rev015复盘：当前无新保留优化，原20FG。现有旧trace19prefill最大1.531s，没有本次慢轮2.9s特征，不能拿旧trace解释新慢轮。新6轮有界capture=2warm+4profile，P1024/D256/C64/N128/T0ignoreEOSseed42，每轮600s，双rank全轮max_iterations0和现有CPUcustom scopes；预注册停止6轮，不自适应挑轮或无限复现。先graph两波64+fresh10docC8，原private4repo不改，设备2/3源授权暂停后用独立C，最终恢复原S。20FG/.002/.02/10%准入不变。本采集不要求性能准入，profiler耗时仅诊断；后续真实性能仍需全新PF/D/M B/C/R及原10%/2%收益/5%guard/1%漂移契约。capture若未出现慢态保持not-reproduced，不直接进入候选收益判断。

执行前命令SHA：
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002d1-controller.py` SHA `f7b1ceb5a09a555357a4008583077b26d04bebf624c19fe5b7845b1973c6b119`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002d1-source-service.py` SHA `2f17645178e04e90583108d89abb36ead68efe25ab95f107ab3ff3aa88f1b57a`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002d1-model-service.py` SHA `4dd49307cedb2782f8f0648186822d9688df36abf0bb2855f766226ec5f1411b`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002d1-launch.py` SHA `8a304571e2d4046e6ed5d69f01a0ebe891eda941b44b83acdabe657f72f69dad`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002d1-baseline-c8-config.json` SHA `dbdae3fc757699df85179a2cde8c78ad2de429d06eea968c20c90ccfb18e821b`

新fw002d1控制器1913763/start506112461/create1792121565.61已真实启动，process SHA `c7aceced553783e04bc6f9f780f02eb93634289799b51b37cfeb34cf7be114c4`，controller SHA `f7b1ceb5a09a555357a4008583077b26d04bebf624c19fe5b7845b1973c6b119`，inputshas SHA `1e015c55b8aed5b7f30ea3211c19b15ab4ddd3644a835bdfbcd104b8fb7e73dd`。源原4repo、mountparity、weightsstat门禁通过并精确暂停938713原服务，独立模型加载/编译中，未进行新候选安装。30min纯只读监控已绑定该receipt，沿用用户授权；主任务在采集后继续分析及有证据的修复，监控自身不发新请求。

Trace离线分析预注册：`commands/fw002d1-analyze-traces.py` SHA `cdf8ff68e4e2660c7b22aa0d0e593db1e8e4a65ec34e7c4695e370d021a9b3c2`。仅解析已有文件，始终CPU user_annotation execute_new/cached外层关联driver correlation到device kernel，不按同名GPU镜像range重复计数；逐轮逐rank保留所有prefill/decode迭代及shape、kernelwork、CPU/driver inclusive耗时。大于2s的prefill只作诊断分组，不挑性能轮；profile费用不是收益。可先解析单份已导出trace形成partial，最终必须全部4profile轮双rank核验。

FW002d1采集与全量分析已完成：terminal SHA9167b768.../analysis SHA c1cd795b...，4profile轮共8份ranktrace全部核验，新请求每rank每轮128、kernel关联>=99.6979%；第4轮两rank各4个约3s慢prefill，CPUfull1.45–1.55s、模型forward1.50–1.58s，重复缓存刷新/调优kernel证实full在线调优根因。源18002实例946383/1792123272.69已恢复ready。全部旧失败保留。

新r4预注册：源四repo原件/20FG精确capture暂停；先独立full187integer+fallback数值、8graph两replay和6newN+4cachehit微测，通过才安装C私有full（FGtree a5184db5...），重跑metadata14prefix/5FA，再原2%/5%/10%/1%契约全新三角色三阶段。full修复在三角色中恒定，Plugin c4为唯一对照变量。最后C恢复Plugin/full原件和S18002原代码，避免直接部署未正式验收候选。每probe有精确PID/birth回执，900s有界，超时只取消其所属进程再恢复，不允许dockerexec子进程残留争抢GPU。静态AST及producer/consumer名称预检已过，尚未启动。

执行前命令SHA：
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-controller.py` SHA `fc6aecaae7b8d1a303b7abdf54233d87e6b96eca8fa689278edfdad3a2393878`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-launch.py` SHA `930f8044620f42c1f6fb34e5f236b334806a305e99b01143a0dad4dfce8e8f00`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-source-service.py` SHA `ed0ac21ed6d22c42b1900f51f47dc137ec4560afba3d1dfb7273036e344f995b`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-model-service.py` SHA `a90f1669d98a26646ecb568386a42e893e08295430479488de6dfed80c189ddc`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-launch-probe.py` SHA `f97839efdad0991b2a9ba6e82e20c43e493e27e2f16dde4c885c8b8f4aa96c85`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-cancel-probe.py` SHA `2e11eba2f0eb58f395e223f7ae4d078cdf20afbb60cd7e7c65f4836fbe478b9e`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-apply-full.py` SHA `f74eb687aa8c4d767b4419101dc1322fd4d1b721b165f1b0c6c04b9e48f898c6`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-meta-numerical.py` SHA `2f7008ff087a5377ff532e840c6e08698643e2ab791189772a889c54c64b461c`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-baseline-c8-config.json` SHA `325e6f864b040b6280ccebd77539e7ad0a83a44aee2a3c59ebd28cd8b86460bc`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-candidate-c8-config.json` SHA `9f4e1c2d4f010b704dc92bccaee89782d4c488fbb8425024d8cdb613cba94043`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-revert-c8-config.json` SHA `d91d8261c657f88fb31a5c9c49ba5a6946deafbdbac599b4be41303600461251`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-prefill-plan.json` SHA `4375ddfcc3619b618a017fc5ffdeca96325ceeaba2b23076f544dfb8bac232fe`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-prefill-comparison.json` SHA `9cd1196b2e1b74e539fa0210311e2d9901416fe6cf01d1b75c508b9f63fc8481`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-decode-plan.json` SHA `df42552abeecd4904665de303c8f3604d4d65ae0033caf437d58423213bb9088`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-decode-comparison.json` SHA `324994c9c36fbfd6512cdadc732f93b6dfceb844cadab50e9b6032e24fd16a39`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-mixed-plan.json` SHA `e6e50f2bd1f98f758d7ae8d4f98939e5cdfd4ab8a19709c7b8aab8f0b6ca27f8`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-mixed-comparison.json` SHA `c5879725b1cee03ee079f0cbb93c03170a7c66218672bbcf2a1f5319fcca5f85`

执行前微调控制器的只读probe存活检查，容忍检查时恰好退出的NoSuchProcess竞态，不放宽PID出生校验；最终controller SHA `fb004c19b6b894f4a3bcfc34e4b8f67bfe35d7a9c27cd9bc2caff855f5487cb3`（上方未执行草稿SHA由此替代）。全部源/目标名称AST预检通过。

执行前静态收紧：最终使用controller-v2/launch-v2与input-shas-v2，额外冻结standalone probe、两组原件/候选、原生runner和父capture证据SHA，probe启动后再次对照已冻结workerSHA。此前v1控制文件仅预备、从未启动或发请求；不覆盖旧文件。最终controller SHA `7b8187149d1d9b8afcd66b4483a3962068a489d2032d0d64a71729fec5704218`，launcher SHA `17f33da8be692aff8862214920431f817660c31295801fa360f093310b14e0ad`。

新r4实际控制器1972435/start506361450/create1792124055.5，receipt SHA7478f067...，worker-v2 SHA7b818714...，input-v2 SHAe68c3bfc...，39文件冻结。OP003数值/graph/micro全部通过后已安装私有FGa518，metadata14+5在新FG下逐位一致重跑通过（SHA5827be49...）；新baseline实例288787/1792124252.15双rank各36fixedfull/0scale/32graph replay，fresh10docC8通过。当前Prefill测量，Mixed是否稳定及candidate/revert全部实际增量待原生记录，10%准入/2%Mixed/5%guard/1%漂移不变。


R4 新基线进度：Prefill、Decode 均已生成 complete 原生 run-record（各3 measured、errors=[]、轮次 raw/validation SHA 全匹配），Mixed 正在原8暖轮计划中，暂不宣布稳态。PF 总token吞吐中位5694.1523 tok/s、平均TTFT中位8992.3456ms；Decode output中位940.8560 tok/s、平均TPOT中位54.5115ms。Decode 三个测量轮平均TTFT为7768.6492/6848.8802/6847.8062ms，spread约13.45%，已标记为后续原生比较的有效性风险，保留三轮，不能以移除首轮或放宽10%门槛消除。它不改变已查明的 Mixed full 在线调优机制，也不能提前宣布本轮端到端准入通过。


2026-10-16 05:13 UTC 只读核验：唯一控制器PID/出生及worker、receipt、39-file输入清单SHA匹配。新基线 Mixed 原8暖轮末3为701.0486/700.3597/702.4706 tok/s，spread0.3011%，通过10%准入；3 measured为699.9411/701.1974/700.4087，median700.4087 tok/s、spread0.1794%。11轮各128成功/0失败，输入131072、输出32768 token，recordSHA8f9998dc783255442520c6ef4aa6d8fab64a108f26a2ffcbd85be5cfed21a2d2。测量延迟中位：meanTTFT5814.1919ms/p99TTFT11968.8535ms/meanTPOT68.6348ms/p99ITL1481.0090ms；该阶段列入比较的指标测量spread均<10%。这支持本轮基线Mixed稳定，不能与旧失败暖轮计算端到端收益。

候选Prefill与Decode各6暖3测已complete且errors=[]，recordSHA分别d3c9fe8073bbf6a2528cce813ad8a3e7a6b36f49e8771c71eba4fbdb095524fb、0f263c39a4fb795366f22cddc3ca2b5bcf608cac851d9ad9656917239f43c6c2。5份完成记录的plan/contract/client、所有raw/validation SHA逐项复核相等，全部测量轮保留。候选Mixed正在暖轮，revert未开始；尚无原生最终比较，不签发收益或验收结论。基线Decode meanTTFT13.445%测量spread仍超10%，保留原3轮并等待原生比较如实判定。


2026-10-16 05:43 UTC 只读进展：metadata候选三阶段全部完成，Mixed原8暖3测，recordSHA35b2cae7c7aad53b33df69a430897ad66bed5c0cf3b238ae753021db035f5d97；末3暖spread0.1165%，3测吞吐median702.2617 tok/s、spread0.1420%。11轮各128成功/0失败、输入131072/输出32768 token。候选Mixed平均TTFT5759.5441ms、p99TTFT11926.2915ms、平均TPOT68.6138ms、p99ITL1474.7551ms、p99E2EL29459.2046ms；p99E2EL较B约+0.76%，所有列入比较的候选Mixed measured指标spread<10%。

在共同OP003 full修复前提下，metadata的暂定B→C增量：Prefill total5694.1523→5727.1996（+0.5804%），Decode output940.8560→943.2032（+0.2495%），Mixed output700.4087→702.2617（+0.2646%），Mixed低于原2%主收益门槛。尚未生成最终native比较，不能宣布可保留或把该增量归给full修复；baselineDecode meanTTFT13.445%波动原样保留。

回退Plugin原件已由既定controller完成，仍共同采用OP003 full进行对照；实例qwen36-fg20-e2e:357714:1792128229.67，runtimeSHA2736824844e354698a35e430833f064f276833ae99b14c0eef4a8fea36f16347，双rank各30 graph replay/48 fixedfull/0scale、attention逐层integercopy恢复各256。回退Prefill已完成，recordSHA6cb4772f0d89ff654fc61fcf8be73e4ea24cf4435b52c2081f371fe775bfecd2，total median5686.6342 tok/s；Decode运行中、Mixed未开始，最终B/R漂移待完整比较。全部7份complete记录的plan/contract/client/raw/validation SHA及请求/token数核验通过，未删轮或放宽门槛。结束仍须恢复C的full原件/四仓并恢复源原20FG/18002，不将仅Plugin回退误写为源服务已经恢复。
