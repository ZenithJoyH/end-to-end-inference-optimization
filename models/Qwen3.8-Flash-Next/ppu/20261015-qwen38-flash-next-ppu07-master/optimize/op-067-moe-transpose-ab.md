# op-067：仅关闭完整MoE自动权重转置的算子/graph诊断

- 状态：已完成两组独立B/C/R及CPU终态审计；算子/graph范围通过，关闭自动转置显著降低成本。线上8010完全未改，不宣称端到端恢复或新精度gate。
- 用户授权：保留MoE选参/BF16/所有现有修复，仅独立算子和graph小范围对照，8010不重启、不跑GPQA、不访问8035、不提交推送。
- 分类：`operator/improve`诊断性单变量；正式acc019仍failed-score，无gate。本轮用户明确授权是有界诊断例外，不恢复正式性能优化。
- 方法：`key-operator-analysis`负责完整算子/graph microbenchmark；数值覆盖按`inference-accuracy-evaluation/minimal-regression`限于算子部分。无模型HTTP请求，模型级minimal仍not_run。公共性能Skill/runner仅用于端到端服务，不虚造本轮原生run-record/正式targeted回执。

## 假设与唯一变量

原vendor源码SHA807d12ce；baseline/revert保留`_ENABLE_TRANSPOSE=True`、原4项缓存和10/16GiB门禁，candidate仅在其独立进程中设置`_ENABLE_TRANSPOSE=False`，即不做自动权重转置（不是关闭缓存后仍每次复制）。所有kernel、selector、dtype、路由、TLE/空输入修复完全不变，线上源码/进程无变化。

假设：完整入口在层间缓存miss时把整权重复制录入graph，额外成本显著。以一层真实TP8形状、冷缓存capture重放模拟miss；不复制48层，不假冒当前8010实际graph节点或端到端效果。

## 冻结范围

- Host PPU-07，已存在且谱系/挂载通过的优化容器`qwen3.8-flash-opt-ppu07-20261015`；仅物理15（进程逻辑0），不初始化0–7或其他卡。
- 独立进程，前后绑定8010 API1693692/start537709560/argvSHA c146e2da及源码指纹。在线health/metrics只读，不调用completion。若running/waiting非0、身份漂移、health异常立即停止当前自有测试，不停止/重启模型。
- 预检15卡86376/98304MiB、0%利用率，8010空闲；余量约11.6GiB。只驻留一层600MiB合成BF16权重。额外进程预算2.5GiB；原转置门禁关闭时该对照无效，保留原件并停，不强制门禁、不扩显存、不清线上缓存。
- 远端E：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/operators/op-067-moe-transpose-ab-20261023`，唯一新目录、拒绝覆盖。所有命令/输入PT/CPU reference/输出/逐轮结果/来源/SHA留E，新缓存仅E/runtime各进程独立根。
- 真实per-rank形状：E512/H2560/I80/topk10，w1=(512,160,2560)、w2=(512,2560,80)。CPU seed20261023、固定生成归一化输入和权重，一次保存完整合成张量，所有角色同输入字节。不是模型真实权重或GPQA。
- M1/8/64为Decode代理，M128为小Prefill哨兵，M0/13仅边界/分支正确性；均非服务并发，不含TP collective、attention/KV、scheduler、网络或Mixed。
- 2组独立B/C/R进程，顺序B1→C1→R1→B2→C2→R2，不额外重试。每角色覆盖同6个M和2组changed-input，数值oracle采用CPU显式SwiGLU专家和路由归约，BF16阶段舍入与FP32累计另存；容差rtol.05/atol.01且relative-L2<=.03、必须finite，B/C原始输出逐份保存，不按结果改容差。
- 每非空case：先3次算子JIT/allocator预热（不计时比较），清空**仅该微测进程自己的**转置字典并释放自有临时块后捕获冷缓存graph。changed-input至少2次replay核验。固定8轮graph预热（每轮5次），末2轮spread<=10%；5测量轮（每轮10次），保留全部轮，spread<=10%；B/R中位漂移<=10%，否则incomplete，不挑轮/自动增加预热。
- CUDA Event记录完整MoE graph replay设备时间，wall另存，不用profiler-on。只在目标路径实际开/关、配置字典逐项相等、数值/graph和稳定性齐备时解释差异；>=5%作为预冻结的诊断信号，不宣称用户性能验收达标。
- 总GPU预算40分钟，首次错误停止，不自动修复/重测。全量精度和线上性能均not_run；本轮最多支持“转置对所测完整算子成本有/无明显贡献”，无法单独证明旧端到端回退已消除。

## 命令、证据与决定

命令准备后在本段记录路径/SHA再执行。生产源码、三个repo HEAD/index和原cache不修改；进程内开关随退出自然消失，无服务回退动作。当前结果not_run；下一步为冻结输入/命令、核资源后单次运行。

执行前冻结命令：`E/commands/control.py` SHA `e3edf6cf08486450f2751b69c4d1d9818d2e6454cb4bd80f1b2eb78a208e3a18`；`E/commands/worker.py` SHA `7ce0154a449b9e363010167e8123d432acee80c47d65cc998b0e7aeeab620ba4`。仅一次CPU `control.py --root E --container qwen3.8-flash-opt-ppu07-20261015 --device 15 --port 8010 --mode prepare`，核PREPARED和输入SHA后，仅一次同参数`--mode run`；脚本不含模型启动/停止/重启操作。每个非空M除2组changed-input replay，再对一个选中合成专家的w1×0.5、w2取负做replay并恢复原权重再replay；CPU预存两个相应reference。这只修改独立进程内的合成权重，原模型权重和保存输入PT不变，计时使用恢复后的权重，完整输出均保留。捕获前原缓存miss预条件各角色一致，不把单层热缓存计时冒充48层轮转。

CPU准备后、GPU launch前，仅在E下排他建立新cache父目录：Python `r=Path(E)/'runtime'; r.mkdir(); [(r/role).mkdir() for role in ['B1','C1','R1','B2','C2','R2']]`，供各原生库自行创建triton/gems/vllm/SQLite子项，不复用或删除旧cache。此命令不导入库或初始化设备。

GPU对照已自然结束，6角色齐全、无FIRST_ERROR；原`FINISHED.json` SHA `9ea28c57e5d9c31e049fb547fa484aaa94458328a511ef10439a0010b030344d`、`comparison.json` SHA `9d5bb85dde33b4a1e1cb6ebd2da39fe64ba8b61ea48bcd53da67947e8419568b`。执行前保存仅CPU审计`E/commands/audit.py`，SHA `0758a096e77d075a0568ed106711c6bf48b36f3223f234c5fbd9bf5a8986ba45`；仅一次`python3 E/commands/audit.py --root E --container qwen3.8-flash-opt-ppu07-20261015`，排他输出`E/cpu-audit-001`。核全部原manifest/输入、126份输出与CPU reference、配置/所有轮/回退漂移、当前/source前后和8010计数；CUDA_VISIBLE_DEVICES为空，不发GPU或模型请求，不重测。

## 正确性与实际路径：算子/graph范围通过

6个独立进程均自然退出，唯一GPU阶段总188.8365秒；没有FIRST_ERROR、资源停机、门禁强制覆盖或额外重试。全量198精度/服务请求/模型级最小回归均未运行，原acc019 failed-score/no gate保持。

三库、三repo HEAD/index、engine、bootstrap/固定调优、模型/tokenizer元数据和当前8010身份/启动参数/服务计数before=after=独立审计current；配置probe记录每个M的完整base/G1/G2参数，六角色逐项相等。baseline/revert只用原True，candidate只用False；原4项容量和10/16GiB门禁完全未改。capture中B/R每case实际进入2次miss转置，C为0次；30次非空graph capture、120次changed-input/合成权重变化及恢复replay检查通过，另2160次预热/计时replay全部保留。M0为空边界，M13是naive→alignment/SiLU分支哨兵，未纳入性能表。

CPU审计独立重读126份完整输出/PT与reference，全部finite且通过预冻结容差；最大全局绝对误差0.0078125、最大relative-L2 0.005001945。B1/C1在5非空M×4种replay输出的20对逐位相同；其他角色126项整体均以CPU reference核验，未把20对扩称所有可能布局/精度等价。改变并恢复原合成权重后仍随replay正确更新，支持转置转换确实位于所捕获测试graph内，而非只保留首次输出。没有改真实模型权重或输入PT。

## 性能效果：完整MoE graph replay，非端到端加速

单位ms/次，先取各进程5测量轮的中位，再取两组同角色进程中位。固定8预热轮准入及全部5测量轮保留；最大测量spread2.4466%，最大B/R漂移1.4299%，所有角色间波动通过10%界限。每角色独立cache，JIT/allocator准备不计入表中。

| M（合成token行） | B：原转置开 | C：关闭转置 | R：重新开启 | B/C算子倍数 | 减少ms/次 |
|---:|---:|---:|---:|---:|---:|
| 1 | 2.513918 | 0.033558 | 2.533894 | 74.91× | 2.480360 |
| 8 | 2.551588 | 0.084822 | 2.576526 | 30.08× | 2.466766 |
| 64 | 3.175314 | 0.670138 | 3.138356 | 4.74× | 2.505176 |
| 128哨兵 | 3.404422 | 0.867828 | 3.383336 | 3.92× | 2.536594 |

这是E512/H2560/I80/topk10、单rank单层600MiB合成权重、冷缓存capture的**完整算子设备graph时间**，包含其alignment/GEMM/激活/归约及开关带来的布局/复制变化。不是单个GEMM时间、模型token吞吐、C64服务并发或TP8端到端倍数；两独立进程也不是两个新模型服务。M1/8/64为Decode shape代理，M128仅算子小Prefill哨兵，Mixed/四场景不在本轮授权范围。parent `p1024-d1024-c64-n128`只是后续晋级映射，不代替该场景。

## 机制、反证与决定

关闭策略在各M减少的成本约2.47–2.54ms/层，近似固定，且重新开启后回退复现；这与对完整600MiB权重做读写转换、而非仅处理topk选中专家的机制相符。在这个冷缓存完整算子/graph范围，自动转置策略的显著代价已由单变量B/C/R复现，不再仅为静态嫌疑。

仍不能将上述差值全部标为permute kernel自身时间：关闭转换同时使GEMM权重stride回到原布局，这是该唯一开关的必然后果；本轮没有额外热转置graph对照或逐kernel计时去拆分两者。更没有当前8010真实graph节点dump/在线切换后的阶段或端到端测量，不能宣布原服务6.9token/s或11题超时已经恢复。不得把层数×差值当成正式TP8收益，也不复用旧split入口的不同配置来算“完全恢复比例”。

最大额外自有CUDA reserved为1568669696B＝1496MiB（1.46094GiB），低于预冻结2.5GiB；终态15卡回到86376MiB、仅原Worker_TP7，当前8010 API1693692/start537709560/argvSHA c146e2da仍health200、running/waiting/KV/preemption0。prompt104482/generation3552451与前值完全相同，0模型推理请求、0服务启动/停止/重启、0生产源码/选参/修复/旧cache修改，无8035或0–7操作，不提交推送。

决定为`passed-scoped-operator-graph`、证据保留，**不部署**。后续若用户授权制作最窄候选，优先取消重复自动转换而非增加cache上限/先改tile；实际接入仍需独立候选源码/graph/模型最小回归与原正式精度契约，服务重载和端到端测试另行授权。本轮不能解除acc019精度阻塞或签正式性能gate。

## 完整外部证据与知识差量

E保存两份原执行脚本＋CPU审计、629147429字节完整合成权重PT、6个M的全部输入/CPU reference与SHA、六角色输出PT/配置probe/capture miss记录/全部计时轮、独立编译cache/metadata/binary、前后来源及服务证据。

- 原manifest2015成员逐文件大小/SHA通过；manifest SHA `88f44ee5b7bae47e49dc498ff597c17ab400d8b08aa556b47521971920be2919`。输入manifest另按PREPARED SHA校验，7份PT全部一致。
- 独立CPU审计`E/cpu-audit-001/report.json` SHA `56799a905868d47d23e299ea5cf8d991a6c35aa9568f0ea4bae21a6b361cdab9`、manifest SHA `b2d01466a731401adea0464832035a9009d5491a601885153a32c387d7983f5e`，回读原始报告/manifest通过；`numeric-audit.json`逐份保存误差与20对B1/C1比对。
- 无profiler-on计时，没有正式模型gate/原生性能runner回执，不冒充公共性能比较器passed；无新heartbeat，短任务前台已收尾。

知识差量`confirmed/refined`：原先CPU仅证明4项缓存无法保留96权重，真实性能仍未知；现在在真实per-rank尺寸、原选参和原门禁的冷缓存graph下，开→关→开方向可在两独立组稳定复现，并用合成权重改变/恢复验证replay更新。未来优先核cache miss是否捕获了容量级复制，避免先盲调G1；范围仍为上述kernel/revision/shape，不能外推到所有PPU、热缓存或当前线上端到端收益。
