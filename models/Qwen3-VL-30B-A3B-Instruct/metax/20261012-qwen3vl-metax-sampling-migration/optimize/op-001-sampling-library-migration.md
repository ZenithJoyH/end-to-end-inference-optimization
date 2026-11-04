# op-001-sampling-library-migration 采样过滤实现归属调整

状态 completed-code-migration；operator/improve；父目标 P1K/D1K/C64/N128；本轮仅迁移与算子级验证。用户要求调整代码归属及查明 reference/来源；已提供远程根目录 /public-flash/jinghao/qwen3-VL。

## 优化方向与瓶颈依据

原 Plugin 已接入，但调用 vLLM 中新增未跟踪实现。将平台实现纳入 FlagGems-vllm 并暴露公共 API，Plugin 保留原实验开关与 shape 路由。源容器不变，快照复刻隔离容器测试；源码在容器私有 /workspace，不修改共享挂载中的同名仓库。

## 编码前项目真相

| 字段 | 冻结内容 |
|---|---|
| API/reference | vLLM ee0da84ab 的 apply_top_k_top_p_pytorch；非 torch 单一公开 API |
| 可编辑 | 隔离容器 FlagGems-vllm 新算子/MetaX backend/导出/测试/benchmark，Plugin 采样接入；vLLM 仅移出已有未跟踪文件（用户迁移授权） |
| 只读 | vLLM reference、FlagGems 基础实现、所有源容器/共享源码 |
| Build | 既有 editable install，无二进制重编译 |
| Validation | 对拍稳定 reference + vLLM reference、dtype/layout/empty/tie/非对齐/任意FP32，graph 两次 replay，Plugin 路由与导入 |
| Benchmark | 相同 logits/filter、稳态算子延迟 ms；目标 M64/V151936；不称端到端结果 |
| Active set | M1/2/64，V1/257/151936；k/p 单独与组合，BF16 网格FP32及任意FP32 |
| 超时 | prepare 10min；functional 10min；operator benchmark 5min |
| Profiler | 本轮不采集；路径/源码和原生计时作为替代证据 |
| Autotune | MetaX 迁移，固定原有 launch 参数；NVIDIA 暂不支持，NVIDIA tuning 豁免；不声称新调优 |
| Fallback | 算子内不得调用 torch 计算；可复用 FlagGems 非torch入口；unsupported 抛 NotImplementedError；Plugin 保留原 reference fallback |

## 对齐契约

| 字段 | 内容 |
|---|---|
| 输入 | MetaX contiguous rank2 FP32 logits；k int32/int64、p FP32、同设备contiguous长度M；0<k<=V，0<=p<=1 |
| 输出 | 原地 mask logits，返回同一张量；输出dtype/device/shape不变 |
| 累积精度 | FP32 softmax与cumsum；整数计数精确 |
| 语义 | 升序稳定值排序；top-k 严格小于阈值；top-p 累积 <=1-p 删除，至少留1；tie/signed-zero/-inf按对拍确认 |
| 不支持 | 非MetaX、非连续、非FP32、超出本轮shape范围；训练/autograd；非法k/p数值 |
| Reference torch | 仅 tests/benchmark；生产调用已存在 FlagGems kernel，不调用torch compute |

## 路径设计

| 路径 | 条件 | 实现 | 验证 |
|---|---|---|---|
| early | empty 或无过滤 | 元信息/直接返回 | empty/identity |
| fast | 值可无损表示BF16 | 计数排序、阈值筛选；BF16无损验证不得引入host sync | BF16网格、正阈值、尾部 |
| general | 任意FP32 | 精确值排序路径，避免BF16舍入 | temperature样式/随机FP32 |
| unsupported | 非支持dtype/layout/device | 抛NotImplementedError；Plugin保持参考路径 | 反例/无vendor导入 |

## 优化内容与适用边界

迁移后补齐无损BF16前提处理与尾部lane mask；如果无法在本轮安全实现，收窄或保留为未晋级候选。操作前保存命令、源码SHA和可回退快照。optimization.md/deep_opt.md 在当前仓库根部不存在；本轮为迁移维护，不开展未知文档定义的调优阶段。

## 正确性与路径命中

实施前冻结为 not_run；最终49项算子与7项Plugin验证通过，模型服务范围仍 incomplete，详情见后文。

## 性能效果

端到端 not_run；算子级三轮结果见后文，不代替正式四场景或性能验收。

## 决定、风险与回退

retained-code-only；本轮迁移及必要正确性保护已回写，未重启模型服务。备份/快照与SHA守护回退入口见后文。

## 外部证据

/public-flash/jinghao/qwen3-VL/20261012-qwen3vl-metax-sampling-migration/；准备脚本 commands/prepare.py（SHA见state）。


## 完成结果与来源

已先在 qwen-vl-sampling-opt-20261012 私有源码验证，再按用户当前源码调整指令回写 qwen-vl 的9个文件。源容器未承载本任务benchmark/profile，未停止、重启或删除；回写时无模型服务，逐文件SHA检查防止覆盖并发修改。vLLM仅归档移出原未跟踪实验文件，tracked reference保持原样，git status为空。FlagGems源码没有改动；既有Plugin MoE改动保留。

新API为 flaggems_vllm.apply_top_k_top_p。通用模块提供显式unsupported入口，MetaX runtime替换为vendor实现；FlagGems可选依赖仅在选中该路径时加载。Plugin仍使用已有实验开关及M64/V151936路由，支持条件补齐dtype/device/layout，不新增通用dispatch框架。

不是原样拷贝：BF16无损性在设备上检查，任意FP32使用FlagGems值排序kernel，避免temperature/penalty后的舍入；尾部计数增加valid mask，signed-zero按现用FlagGems排序key处理；生产路径只用torch.empty/empty_like分配，计算由Triton与FlagGems承担。11处torch调用静态审计均为允许分配。NVIDIA不支持且无调优声明，MetaX固定参数迁移，不做autotune搜索。

vLLM参考在vllm/v1/sample/ops/topk_topp_sampler.py的apply_top_k_top_p_pytorch（363–404行，ee0da84ab）。原实验文件没有Git历史，作者/生成过程不能确认；可确认的实现来源是既有计数排序实验代码、FlagGems排序基础和vLLM过滤语义，均已保存原件/SHA。PyTorch sort默认不保证stable，stable=True才保证相等元素顺序；本轮对齐当前服务使用的FlagGems稳定radix路径，其他backend未验证。

## 最终验证

49项算子功能测试通过，覆盖M1/2/64、V1/257/151936、BF16网格/任意FP32/正值tie/-inf/signed-zero、k/p/组合、空batch与unsupported metadata。graph在M2和M64下切换BF16、FP32、ties，各两次replay一致。7项Plugin路由/形状/dtype/layout/fallback/幂等测试通过；路由测试包含mock，不代表完整模型服务通过。black/isort/flake8与git diff --check通过。

联合pytest曾因两仓库tests.conftest重名收集失败（measurement-invalid），失败日志保留，分进程同范围重跑通过。旧实验在BF16随机输入有40处差异、正值tie有8192处差异；后者首行应保留1个却保留129个。只给旧代码增加尾部valid mask后两例差异均降到0，根因confirmed；迁移候选两例也为0。无模型正式分数结论。

## 算子性能（3轮中位数）

同进程、无profiler、seed42、k20/p0.8；reference使用vLLM PyTorch过滤入口及现用FlagGems ATen实现，注册在计时循环外。两路均包含相同logits.clone()恢复输入。单位ms；没有独立进程/revert，属于算子级观察。

| M/V/输入域 | reference ms | candidate ms | 逐轮加速比中位数 |
|---|---|---|---|
| 2/257/bf16 | 2.0704 | 0.4906 | 4.283× |
| 2/257/fp32 | 2.0312 | 0.6397 | 3.176× |
| 64/151936/bf16 | 28.6916 | 1.8757 | 15.296× |
| 64/151936/fp32 | 28.7395 | 22.4789 | 1.278× |

上述reference是vLLM语义原路径，不是存在边界错误的旧实验代码；不能把这些数字称为对旧实验的迁移增益。decode仅完成采样算子视图，prefill/mixed及服务TPOT/TTFT未测。

## 保留、限制与回退

retained-code-only；迁移完成，pr_readiness=needs_revision。未重跑模型服务C8、完整GPQA和端到端性能，未签发gate；非MetaX硬件/训练/非法k,p值/所有浮点特殊值未完整验证。生产依赖当前FlagGems sort内部Triton helper，升级时必须重验契约。正式上线/PR还需目标模型服务与跨平台CI验证。

回退脚本commands/rollback_qwen_vl.py带当前/备份SHA守护，--dry-run验证10个文件通过；去掉--dry-run会恢复本轮9个文件及vLLM原实验文件，拒绝覆盖后续修改。回退不自动停止或重启服务。快照镜像与逐文件备份路径见state.yml。

最终补丁位于patches/final-FlagGems-vllm.patch、patches/final-vllm-plugin-FL.patch；全部原始日志与校验信息位于远程案例目录，SHA见optimize/state.yml与artifact-manifest.json。没有提交、推送或创建PR。
