# 20261020-responsibility-preserving-dedup-49 按职责边界去重

- 状态：保留；已直接修改实际安装Plugin，543 CPU通过/4既有跳过，整模与graph回归及21:21 +08最终只读审计通过。
- 分类：framework / 工程可维护性，不是性能实验，服务场景与阈值保持不变。
- 范围：PPU-13 / glm5.3-flash-opt-20260911 / 8011 的唯一editable Plugin。

## 优化方向与瓶颈依据

用户要求不要过度收敛：只处理确实重复且职责一致的逻辑，保留Plugin设计边界，并直接修改安装源码、回归验证。本轮审查确认FlagGems和reference的`_lazy_fn`具有相同模块/符号解析、binding私有闭包缓存、`_prepare`与`_is_available`契约，可共享一个很小的私有工具。它不负责backend选择、优先级、fallback或可用性探测，不发展新的dispatch框架。

不处理：vendor的owner解析/native binary加载；MHC归一化和host ABI；BF16/FP8缓存；模型注册、worker spawn初始化；旧processor语义。这些表面相似但职责、生命周期或契约不一致。纯转发也不是删除理由，不为减少文件数修改它们。

复查结果：

| 部分 | 决定及理由 |
|---|---|
| FlagGems/reference模块+符号懒解析闭包 | 合并闭包体；AST标准化证明与原两实现一致，其他注册函数AST完全未变；backend工厂与loader注入边界保留 |
| vendor `_lazy_attr` | 保留owner resolver协议，可能得到backend/native owner而非仅module；不为统一闭包扩大公共工具接口 |
| MHC adapter | RMSNorm已共享；其余保留各provider签名、依赖及“恰好一次归一化”ABI，避免为减少参数转发引入更复杂高阶工厂 |
| 模型注册/worker/BF16 ABI | 保留公共FP8与BF16物理缓存协议选择、spawn进程本地初始化及CustomOp构造时序；不是同生命周期重复调用 |
| config/processor | 沿用点48公共实现复用与旧geometry/像素预算/提示词边界，本点不再移动或扩大hook |

## 优化内容与适用边界

最终只调整两个BF16注册模块，新增25行私有懒调用工具`vllm_fl/dispatch/backends/_lazy.py`，测试扩展原backend契约文件。两端`_lazy_fn`薄入口及全部原调用点保留。注册表/实现ID/优先级、可用性探测、白名单/黑名单与供应库路径不变；工具不提前import provider，不捕获选中实现执行错误，`_prepare`后保持无import的graph路径；每binding独立缓存，不新增全局cache或锁，不修改vendor注册调用。

实际目录`/workspace/e2e-opt/glm53-20260911/vllm-plugin-FL-review-20261020-p45-v4`，HEAD PR454 `f7696963c44425fdf6603054248cc8256783b4c7`，起始源SHA `1581bddf26923dc072cc5cc2eb02e2f9519a7f7130384d3be7eebfe719c042eb`、index tree `c98015f180fb25dbf93f597c4985d10429c12c61`，51项已有暂存修改必须保留。其他库、模型文件、DB/thead、启动脚本和参数不变。

## 正确性与路径命中

按本地inference-accuracy-evaluation的minimal-regression执行。先完整原540项CPU，再覆盖懒import、重复prepare、首次调用、缺失模块/符号失败后重试、执行错误原样传播、binding隔离、availability回调无副作用及CPU fullgraph两次调用；这些不替代PPU模型graph。通过后仅精确目标原参数重载，C1/C8、16383/16384/16385原文边界、11项明确答案和FULL_DECODE_ONLY capture/多token回放守护。任何必要回归失败则冻结/定位或恢复本次路径/index。

## 性能效果

不测量性能、不声称加速或正式四场景通过；本轮仅减少一致逻辑的维护副本。

## 决定、风险与回退

保留该限定去重，不继续扩大改动。命令执行前已保存远端commands及SHA，受影响路径与index有精确备份，失败v1与其回退保留。最终源码稳定，其他库、启动脚本/参数、权重/tokenizer、DB/thead、镜像/挂载不变；两库各一份editable安装，8011健康空闲。未提交/推送/创建PR，无新完整GPQA/性能，不改绑点46旧175/198。正式PR仍`needs_revision`：既有配套FGV能力依赖、非PPU/公共FP8与多模态硬件、当前最终完整gate尚待验证；本轮未新增这些差异，也不能据CPU mock宣称全平台通过。

## 外部证据

唯一远端任务根（创建前校验权限/空间/规范路径）：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261020-point49-responsibility-dedup`。前台跟进短CPU/模型回归，不启动旧heartbeat或控制器。

执行前冻结：补丁SHA `e5566bd37afb82b92580fb94e1d18415ddf8c8db04f3c8abc25eadef0ad034c8`，仅4路径（3运行时+原测试文件）；运行时代码净减19行，新增7项CPU测试，不以文件数作为收敛目标。测试ruff0.14检查/格式通过，运行时代码AST通过。

新任务根下保存命令：`commands/prepare-v1.py` SHA `4ca3e8c9d5d8810ef6793428786f0a38bb6a5e66e00f05c872cfbd890eac3841`；`commands/apply-v1.py` SHA `57cc1ba3f6415136779ec6b040db252e265abbda74f9db109390fc65c07fd643`；`commands/model-control-v1.py` SHA `b32b29d729ab88000fe0d6444051d2be57d7dabcda989c7c1aa72b39891e3518`；`commands/final-audit-v1.py` SHA `29cb935fa4ba260ad0f568008fc53073d929faf8c850b4ac37d945715b6b891c`；`commands/final-audit-v2.py` SHA `02394ee0d7a4d87cea236ea2c17c2668a120442e75db20c116ef6a32a18da2e8`。包SHA `b471ed18da920174b2bcd5eb5c2da6430504e1295f60bdd0d8160cd0b61ea33c`，严格校验成员、普通文件及SHA后才保存/执行，无覆盖旧证据。

精度方法：`e2e/accuracy` / `minimal-regression`，完整bundle SHA `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`。本地py_compile因macOS默认外部缓存目录无写权限未执行，改用无写入AST检查通过；不是源代码验证失败。

### apply01失败及限定修复

完整547项中542通过、1失败、4既有跳过（117.64秒），原多平台测试直接调用backend的`_lazy_fn`，删除该工厂导致AttributeError。新7项及其他原测试通过，未发模型请求；受影响文件/index精确恢复至点48，原服务未重启且health200。原始`apply01/cpu.xml`和`cpu-rollback.json`保留，不覆盖/删除失败轮。

按inference-accuracy-diagnosis（bundle SHA `796f57d730fa08a05afa0417af3107087e8513d3de2c989d6a14b80ee8aece2e`）定位p49-private-lazy-factory-contract：同一闭包可合并，但backend工厂是已有测试契约/加载器注入边界，应保留薄委托而不是改旧断言来适应删除。v2两端工厂及原调用点保留，仅工厂体委托公共helper。先在恢复的原路径跑同一失败测试，再应用修复、重跑完整547项，随后模型回归。未叠加其他修改。

v2仍4路径，运行代码净减12行（含测试总+101行），不追求减少文件数。命令`commands/apply-v2.py` SHA `aa3d706c9d42564c5cbd46c012425e95b030bf801bcf1dccf2e5a60ef7a7c755`；`model-control-v2.py` SHA `c9edb64721f890b10de05bf2cb2488e0cd19870128ab1ec57c899b10751bef00`；`final-audit-v3.py` SHA `af33edcbdd02b732bbd5311cbb6891c31ce63aebfccd83c79213bf4616fe5e44`；`final-audit-v4.py` SHA `5f35785d94b72f80c2d6b283eba9d758cd571710aa433fe31c4c87ae51a7d5ca`；补丁SHA `980aada4748ca024197ed523fcbf028106a4a2708fa0807d21e692f936aa517e`、manifest SHA `5ffaf09f8d3ce021fed61996acbdd95abb553d5d8c4f25f37fde8fd0b29b1272`，包SHA `1d5206bb1e3fd0618ca362676fe69b8035b3f43c7afe98878ac16c50b430143e`。v1模型/审计命令不执行。

21:04 +08：apply02恢复原路径同一测试1通过（8.99秒），修订版完整547项543通过/4既有跳过/0失败（118.56秒），未删改原540项断言。新源码SHA `1244047dda213e6ec06bb019fbeb0b9414a0f03c42f7d5db5a0d23b7a165a02d`，index tree `dfbec399e6692032c68d88aaa50b7812626a0510`；SCM51→52只增加一个25行私有helper，无新增平台文件、无新测试文件。模型重载前原服务未变、health200，下一步仅执行已保存model-control-v2的唯一dispatch；模型/graph结论尚待新实例回归。

### 最终回归及身份（21:21 +08）

model01已唯一派发（控制器3650411/start_ticks521732574），原实例固定检查后按原argv/env重载。新实例`PPU-13:glm5.3-flash-opt-20260911:3811715:521734328`实际加载SHA `1244047dda213e6ec06bb019fbeb0b9414a0f03c42f7d5db5a0d23b7a165a02d`，C1/C8、P16383/P16384/P16385精确原文边界及11/11明确答案通过。FULL_DECODE_ONLY capture11/11完成，9个C1/C8多token请求和3个D8边界请求提供至少两次decode replay覆盖；不是逐rank profiler证据。源码变更后的启动缓存重编译日志保留，不据启动耗时判断稳态性能。

最终只读`final-audit-v3.json`通过，SHA `1644b79586007139a1fe699f32afab38e5c3e5d762b8fd379fa252182ee2d536`；镜像/挂载/私有安装根验证`environment-final-readonly-v2.json` SHA `bc88610e899d519bc218af42fc20f0b8841d256a8130b766fb3ae22d05c37849`。HEAD仍纯PR454 `f7696963c44425fdf6603054248cc8256783b4c7`、分支`glm53-multiplatform-worker-fix-p45`，52项暂存可在VS Code源代码管理查看，未提交。Plugin/FlagGems-vllm各仅1份editable，源适配容器只读未动。

原生证据与SHA：

- `apply02/cpu.xml`：`f96094fa3421d2e2fb3753918fbafd5c1aa8aef92634032ebbafb79736df52d4`。JUnit118.101秒；pytest摘要118.56秒，两项原字段均保留。
- `model01/completion.json`：`967e0f5197ef7309768ffa01138b82ad5ddc76862e289fcd7b41a153a972ed4c`；`model01/candidate/final-audit.json`：`56b8af08cbdbceb0a190476ef8b80a9544aaf5f031ed1c36f1c278bec73d89cf`。
- `apply02/final-vs-PR454.patch`：`e39a43cc3624b397594fe8c0ed8b3a9d298ad65f3de9954e11cb049efe716627`，原路径备份`apply02/affected-before.tar.gz`：`6c82c3706e425654604c1728053cc805b6980a4f4a2ddcbc4d620f7f32b978e1`，索引备份`apply02/index-before.bin`。
- `diagnosis-v1.json`：`7e8c0c4bee0c938cfddea809ac6e75fae7712f5edee0092d03761439771a40b7`；私有工厂契约故障已通过原路径/失败候选/修订后完整CPU及模型graph闭环。
- 原启动脚本SHA再次只读核验`5b1d0a52b129ada50cf38f2ba35194cb43d67a41901d2876e1150e4e7eef31ca`不变；TP16/BF16/MBT32768/maxseq64/threshold0/关闭前缀缓存均未改。

方法影响：minimal-regression先阻止删除既有backend工厂的候选晋级；保留该必要边界并重跑完整原范围后通过。此结果只覆盖点49工程重构，不是新GPQA gate或端到端性能收益；当前不允许据旧gate进入正式性能验收。短回归前台跟进，无新增heartbeat，旧monitor保持暂停。停止本轮，不自动启动下一优化点。
