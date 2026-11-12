# refactor-007 — 主线公开接口收敛候选

用户授权：继续收敛，优先复用主线/NV公开接口；MetaX实现保留后端内部。不得影响正在运行的服务，不提交推送。

范围：mx-104 / deepseekV4-flash-refactor-20261104，FGV main025f3181 + 当前已验证ref006/op004，Plugin a696859b私有改动。以实际已安装源码为只读起点。新候选仅在远端 `refactor01/api-align01/candidate`，不安装、不改启动环境、不发送模型/GPU请求。

计划：删除4个新增FGV公开入口，复用 `topk_softplus_sqrt`、`top_k_per_row_decode`、`flash_mla_with_kvcache`、`flash_mla_sparse_fwd`。后两者主线位置参数/默认值保持，MetaX已有head/workspace/output扩展转为明确keyword-only，不能称NV已经实现这些扩展。原数值kernel、参数顺序、量化/归约语义与op004 SHA不变。Plugin既有CachedOp契约通过薄适配继续有效；不向Plugin搬数值kernel。

保留4个必要接口：batched_mqa_logits、paged_indexer_mqa_logits_match、mqa_logits_into、sparse_prefill_local。分别存在gathered/paged FP8布局、BF16 caller-out/row_shard、局部attention统计量/缓冲语义，不能靠重命名伪装成NV完整契约。

验证：CPU隔离AST签名/真实wrapper转发/失败不重试/默认fallback/导出与配置一致性/数学kernel AST不变；原GPU测试迁移到新公共入口，原断言和graph输入变化保留。禁止导入可能初始化GPU的torch/FGV/vLLM。GPU数值、真实CachedOp/graph和模型回归均待允许空闲GPU后执行，不拿旧gate认证本候选。

review-refactor-007：前一候选op004已完成数值/graph与全量GPQA+MATH；EOF离线重评分非模型修改。当前任务目标为API维护性，非性能收益，Prefill/Decode/Mixed性能均未重测。优先同语义入口合并，再评估其余契约；数值改写和新性能任务deferred。若签名/缓冲/回退不兼容，停止该项合并；不扩大主线通用语义。下一复盘触发为CPU审查完成或GPU验证失败。

远端动作脚本将先保存D/commands并记录SHA后执行；仅新目录写入。当前阶段：准备中。

执行前归档：`D/commands/ref007-stage01.py` SHA `d507e9178df8ade8cb12e69589954e423e8150c388aac1c38e3ecfa6e72a1087`。仅在同一远端任务根新建`api-align01/candidate/{flaggems-vllm,plugin}`，读取原已跟踪文件生成独立副本，禁止修改安装源/Git索引；每步后核对原SHA、Git差异SHA和服务PID/ticks/argv/health。未下载完整源码仓库，未新建容器或安装包。

stage01候选编辑守卫发现`real_num_heads`在同文件有3处，按预期停止，未触及运行源；不绕过计数校验。stage02改为AST定位目标公开函数内的唯一参数，保留stage01原脚本和局部候选；继续前全量核对安装源/索引/实例未变。`D/commands/ref007-stage02.py` SHA `441d1b17725d85d5bb26f4788bbf875ea51388057e94b8c14cda3d43f657ab87`。

stage02在未跟踪Plugin配置文件处停止；定向检查确认原安装Plugin有9个未跟踪交付文件（FGV为0）。stage03显式加入这9文件而不是忽略/清理；保留原tracked-only快照并创建完整before-v2。运行源/索引/服务未改。`D/commands/ref007-stage03.py` SHA `91d271295dca1371dc7ba9a20ca96bef063120cb90f27a1899c31351d642ce86`。

stage03完成，FGV12路径、Plugin4路径初始差异，安装源和同服务未变。CPU新增两套标准unittest（隔离真实host函数AST，不导入生产库）及候选局部格式修正通过新脚本保存：`D/commands/ref007-cpu01.py` SHA `975dc8e8a2a09949a7af2a74d4e6303399967af5f1d1064a5084fe871f01141e`。只对三个候选包装文件进行定向本地格式检查，未传输完整仓库。所有结果写`api-align01/cpu01`，不是GPU数值/真实dispatch证明。

CPU01：FGV10 + Plugin8共18项通过，0生产库导入/0GPU请求。候选FGV9个变更Python文件经Black24.8/isort5.12/flake8 7.1通过；Plugin受影响文件及新测试按原Ruff配置检查通过，原文件只格式化新增函数。最终冻结脚本`D/commands/ref007-final01.py` SHA `46a39ff79700048de9c2012e6c1ec0978ea330335fa3a27cea384ac21c88f695`：重验18CPU、全部JIT定义AST、common/NVIDIA字节不变、op004不变、安装源/索引/同服务不变，并生成独立最终patch/manifest/archive，不安装。

## 候选结果（未安装）

FGV新增公开算子ID从8个收敛到4个：

| 原公开入口 | 候选入口 | 契约处理 |
|---|---|---|
| fused_topk_bias | topk_softplus_sqrt | Plugin保留原CachedOp的参数校验/输出分配/转发；评分与Top-k仍完全在FGV |
| decode_topk_tree | top_k_per_row_decode | 8参数与主线完全一致、原地写indices并返回None；旧树实现改私有；Plugin桥保持原输出别名；非K512/next_n1等条件保留原MetaX general路径 |
| deepseek_v4_sparse_decode | flash_mla_with_kvcache | 主线位置参数/默认值/tuple结果不变；原有real_num_heads/split_workspace显式keyword-only；dense/V32仍转发common |
| deepseek_v4_sparse_prefill | flash_mla_sparse_fwd | 主线位置参数/默认值/三输出不变；原有out/max_logits_out/lse_out/real_num_heads显式keyword-only |

注意：NV/common文件未新增这些MetaX扩展参数，不能声称跨平台扩展完全相同；MetaX内部kernel/launch仍厂商目录。剩余4个新ID的实际语义差异见计划段，未用别名伪装统一；没有新增数值优化。

验证：18/18独立CPU契约测试（FGV10+Plugin8）通过并复验，1410个JIT函数AST完全不变，171个common/NVIDIA文件字节不变，op004 gather SHA原样保留。所有候选Python语法有效；FGV变更文件Black24.8/isort5.12/flake8 7.1、Plugin原Ruff配置检查通过。原GPU数值/变化输入graph测试只改调用入口/参数，保留原参考与断言，尚未执行。

边界：CPU通过仅证明签名、metadata分流、参数转发、别名、错误传播和静态导出；不等价于GPU数值、真实runtime注册/命中、capture/replay或模型验证。旧精度gate不能绑定未验证候选。非MetaX CI、性能、发布依赖等交付限制保留。

运行保护：已安装FGV/Plugin全部tracked及9个Plugin未跟踪交付文件SHA、Git暂存/工作区diff SHA均未变化；同一个本轮起点服务PID/ticks/argv不变，health200。0模型请求、0GPU请求，无模型/容器stop/restart、无cache操作、无commit/push。自动审批拒绝的完整仓库下载没有执行；改用同远端独立候选和定向差异文件检查后完成，不存在遗留授权阻塞。

候选目录（模型容器和宿主既有bind内）：
`/public-flash/jinghao/deepseekV4/20261104-dsv4-metax104-plugin-review/refactor01/api-align01/candidate/{flaggems-vllm,plugin}`。
最终产物在同根`final01/`：配套两库patch、candidate-manifest.json、candidate-source.tar.gz、18项CPU日志与result.json。stage01/02守卫失败保留，stage03完成；final01最初一次错误路径命令在打开脚本前退出，正确唯一执行已完成，无重复验证任务。

```json
{
  "cpu0.log": "9f4c7eb86181b6ea0d2f3a984cac0b6e94b97153ed68bb34fadd136c5c25b3a4",
  "candidate-source.tar.gz": "37fb876dd6419c78f84988debed0076b82cbaa2b5b3842591ef43d1e79ec6a18",
  "candidate-manifest.json": "924a147b9052ffd702837a781ab1d826c447b6dcb96690847cd39ce0e63339af",
  "cpu1.log": "e7c2ba518c67b1993cc7a194d898a88a61bb0d392fe5a64d0d3c73276bd2c7ab",
  "plugin.patch": "76059f7d845c0e32731e8cd1697aedb45670521a393f648cde3e68ffaedb8629",
  "flaggems-vllm.patch": "f90f056c50b5cbf6ef159a05612a669acb91563fec4b494ba2a2bd354209042b"
}
```

## 用户授权 GPU 验证与交付

最新用户明确已结束测试，授权精确暂停当前模型、验证后更新整改容器并恢复，不提交推送。当前服务实际为 opt2 / 18001 / prefixOFF / .85；保存实际 argv/env（env仅协调器内存），先 GPU 数值/真实 CachedOp/变化输入 graph，再限定18路径安装；临时 prefixON 做22模型最小回归及7FULL/单区间>=2，再恢复原 prefixOFF argv/env 并复核22 runtime/graph。失败恢复本次暂停前源码与索引/服务，cleanup/restore阻塞保持main持env。

执行前资产脚本 `D/commands/ref007-stage-gpu01.py` SHA `ff2057310acdc6809b9e66b25968ce1215b105aca2a1d1f40c0c3783fcc61efc`；只创建 `api-align01/{lease01,validation01}`、冻结新命令和旧helper/候选SHA、CPU验证。原final01不改。GPU后生成 `api-align01/gpu01`，17项真实dispatch/回退与现有FGV core和18项gather回归，数值容差/参考与至少2新输入replay预冻结，失败不放宽。当前未暂停/未启动GPU。完整GPQA和性能不在本次用户要求内，旧formal gate不绑定新源码。

GPU lease01执行资产SHA `bc07a2fae99bd8e12652c11738a2ad2101410d5e848194024746a39a1d2eab13`。stage CPU完整候选/安装源/index守卫passed，0请求。唯一launch命令已发出；后续以lease01/gpu01回执核验，不重复启动。

原生GPU已完成core88与真实CachedOp/回退17，0fail/error/skip；尚待gather18和模型阶段。收尾独立审计脚本 `D/commands/ref007-review01.py` SHA `bff80303cedf00cb6a8d5a2e340ad948d867ba58c943f1790eadadf9120f1d4b` 在唯一lease终态后执行：全manifest、XML集合/逐case dispatch属性、prefixON22+原配置22/minimal/graph、精确实例/原argv/script/8卡归属。只写新独立审计回执，不发模型请求。

## GPU、模型验证与交付完成（2026-11-06 18:33 BJT）

用户的新授权已执行，唯一lease01终态`complete_updated_service_restored`，协调器已退出；生命周期711.18秒。没有重启/停止/删除容器，只精确SIGTERM本任务原模型及临时验证模型关联进程；17条signal动作均为15，无SIGKILL。full env仅协调器内存，恢复本次实际健康实例的argv/env，不声称更早历史交互环境字节相同。

- 原生测试123/123：FGV核心88、真实Plugin CachedOp/回退17、op004 gather18；collection/execution/XML唯一集合一致，0fail/error/skip。既有CPU18与1410 JIT AST不变/171 common-NV字节不变证据保留。
- 17项真实dispatch：树Top-k `vendor.metax`→新公开`top_k_per_row_decode`，decode/prefill `vendor.metax`→公开MLA；router `default.flagos`→`topk_softplus_sqrt`。真实调用函数来源是候选源码；独立参考、输出别名、workspace、hash/normal routing、BF16/FP32及至少两次变化输入graph replay通过。另K64与next_n2真实general MetaX fallback数值/graph通过，无运行错误重试。
- 已限定更新18路径，FGV与Plugin安装路径保持不变；FGV当前37项暂存、0未暂存/未跟踪，Plugin原index保留。未修改FG/vLLM/权重/tokenizer/编译器；未清JIT缓存/修改缓存DB/添加启动cache变量；op004生产SHA保留。
- 临时prefixON服务：22/22最小回归（10C1+10C8+2长输入）与独立arithsmoke通过，7/7FULLcapture，单FULL统计区间359；不是全量GPQA。
- 最终恢复用户实际prefixOFF/.85、served model `deepseek-v4-flash-w8a8-int8-opt2`、18001；原argv逐字一致、原env仅内存恢复，启动脚本SHA `da4c5138e58b262fe6efc163e301e7f7250b00f349624d024e970911bda82d98`未变。再次22/22 runtime回归+独立arithsmoke、7/7FULLcapture、单FULL统计区间301通过。两实例日志推理无OOM/非法访存/EngineDead/Traceback；临时服务受控退出时resource_tracker semaphore/shared_memory警告单列保留，不当模型OOM。
- 两份模型日志各8rank显示fused_topk_bias→default.flagos、decode_topk_tree/sparse_mla_decode/sparse_mla_prefill_local→vendor.metax；sparse_mla_prefill直接公开入口由GPU dispatch测试证明，不能把模型headpack-local路径冒称调用该入口。
- 独立审计重新校验FGV1189/Plugin639文件SHA全等候选、原argv/script、health200、8卡全部属于最终模型及子进程、每个原生XML/dispatch属性与44个模型结果。最终host API2606163/container1444155/startticks1227169827仅为此时回执，未来需实时核验。

仍未执行新正式GPQA/MATH、无profiler性能或非MetaX GPU CI；旧正式gate不绑定新源码，不称精度/性能最终验收完成。没有提交/推送。原main025依赖发布与既有PR限制保留；现有SOP已覆盖本次接口薄适配/真实命中/graph验证，无需据此修改优化策略。

外部证据根`D/api-align01`：`gpu01`为完整原生测试产物，`lease01`保存精确进程动作、限定备份/安装、两实例日志/模型检查及独立审计。monitor `deepseek-ref007-gpu-restore`已在独立完成后删除。`ref007-review01.py`唯一执行通过，未运行第二协调器/额外性能任务。

核心证据SHA：

```json
{
  "independent-review01.json": "ef33eebf19e8eca87cb54358db6dca95ccc986ed23bd9f74601155a4074f81f2",
  "result.json": "b7fbe4d084a86e582c608033467946938009848a90b83bcee7128b5b816f1413",
  "install-result.json": "9484ac95bd8c1d401d605d0b6c5d0ffb37d666440982d9fe8590a81ab32d7ab2",
  "updated-ready.json": "d82158c11c31438934906db557bf61676d156f93aee908b4942ff4196007ce6e",
  "accuracy-ready.json": "bf66cd398271cc370e01c11a968e48fc20ac67ed07470982c6e4c26f990c4ef9",
  "accuracy-cache-evidence.json": "d3bc95b8fc03711587d9e87538cb18667de8ffbe1c7b841f907e97f835a0d23c",
  "model-minimal/minimal-result.json": "82909a0df6d743ad604a2a37fddbadc68dc9695299ac7781c8d066e2ce9068be",
  "model-minimal/graph-evidence.json": "2aa8fbd9f0aa80f4b6857528fdae001a491d7a766b57fbe7d9f20474e952bb7e",
  "accuracy-minimal/minimal-result.json": "18de08e61173cfa18dc0d4b30f5e61d20aa313546ba64e23480883e9263e947b",
  "accuracy-minimal/graph-evidence.json": "28a2cd90f673772f9ad5d2c1fee6eadd4c02ee332b8c75baaaf19f3ee8b51afb",
  "updated-smoke.json": "263f9208c82b91d3bc95281898670b911d83e0c4d70ab053cc8cc76a743fabba"
}
```
