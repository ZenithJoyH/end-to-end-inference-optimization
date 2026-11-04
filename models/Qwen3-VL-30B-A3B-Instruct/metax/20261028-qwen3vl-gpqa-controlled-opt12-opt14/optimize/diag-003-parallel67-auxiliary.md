# diag-003：用户授权GPU6/7并行辅助E67

用户2026-10-28明确告知6/7空闲并要求并行且互不影响。沿用inference-accuracy-diagnosis与formal-gate，本次只新增一个辅助E67=PR638 Prefill/default0，完整198题/C64/strict64一次，其他模型/源码/采样/prefixON不变，不加其他组合/ERQA/性能，不按分数追加。原D1已正式开始，不能为迁移中断/更改它；原factor2 controller1738426/ticks1147819842与D1→E1顺序、原source恢复协议完整保留。原同GPU0/1 E1用于消除换卡影响，辅助E67不冒充同设备单变量结论。

GPU6/7已mx-smi确认无模型进程，同C550/driver/runtime，NUMA1；原D1 GPU0/1为NUMA0。新模型容器qwen3vl-gpqa-e67-mx104-20261028复用冻结快照1c00be94，mount同源，源码私有。新CPU evaluator qwen3vl-gpqa-parallel67-mx104-20261028使用同official v1 image1396，原task/runner/评分，双provenance核验后才GPU。模型API8037，adapter19967，原served-name qwen3vl-opt14；新端口在启动前bind检查，独立输出/cache/UUID、private Triton/HF缓存，原数学/采样参数不改。模型/evaluator/proxy/controller绑定CPU40-79,120-159及容器memnode1，既有任务无任何亲和性更改。

D1实际CPU允许0-159，无法在不改变正在运行评测的条件下声称CPU绝对排他，NUMA/内存带宽与NFS仍是共享宿主资源。预检整机MemAvailable762GB/available disk14GB，保留resource快照，标记并行范围及共享宿主限制，不宣称零影响或性能对照。只读模型/数据共享，写入限私有容器缓存与唯一E67目录；不争抢原代理19964、8030或原evaluator/采样进程全局状态。

新remote根factor2/parallel67，只创建新材料。CPU准备器parent commands/prepare_parallel67.py 51e63ebaab1ad48eb8538efa9c3c1973bf0f0f183db2c2d82ff147e7f1ff305b；控制器执行模板parent commands/parallel67_execute.py 17f38bd6f4c2e39b70acc5cb4667514812998b33c0fe5e6b371936e850c75525；本地/private/tmp副本编译通过。准备不发GPU/模型请求、不改原source/原controller。新启动前归档最终生成controller SHA和有限execution-contract。并行finally只停自己的模型与proxy，绝不停止/恢复用户source；source恢复唯一owner仍为factor2原controller。两个owner作用对象不重叠，禁止并发interrupt或操作旧finally。

状态CPU-preparing，无E67分数，不给历史gate转绑。结果以parallel67/results/gpqa或completed/failure与实际实例取证为准；共享同一个qwen3-vl-gpqa heartbeat，汇总两条线实际阶段，全部终态再删除。

## 资源保护拦截（非模型失败）

14:10首次mx-smi 6/7空闲，但14:17准备器启动前复检已发现GPU6被/minicpm-ocr-1.0-metax104-20261026新进程1764610/ticks1147876629占用30388MiB；只有7仍空闲。prepare_parallel67.py在创建新容器/评测器前拒绝，0GPU算子/0模型请求/0在跑服务变更。parallel67仅保留目录与device-before资源快照，不将其叫模型精度失败，也不直接重跑既有exclusive目录脚本。没有信号发给MiniCPM-OCR或原D1。已通知用户并问释放6/7后再并行或保留串行；当前原factor2 controller1738426仍正常D1正式GPQA。释放事实核验前不争抢；不能自行换到其他卡或停止无关模型。

用户答复“我已经释放出来了”，重新实际核验后继续已授权并行；原partial目录保留。新准备器parent commands/prepare_parallel67_v2.py SHA724133c334960bd8bbe955782bf1474e3e4fb170ebfe01951c43d85a9e6bbbda只将唯一目录改为factor2/parallel67-v2，其他合同不变，仍仅198题一次；模板SHA17f38bd6仍原样。启动仍有再次GPU6/7所有权/8037和19967端口检查，不停原串行控制器。

14:20 mx-smi已复核6/7释放。v2模型隔离/mount/source通过，但CPU evaluator用sha256 imageID创建导致Config.Image不满足正式工具要求的official v1标签（Image ID本身与原相同），provenance前置拒绝，0模型请求。新finish_parallel67_prepare.py SHA13f0cdc3f437d9504ccc1909462976b40c2d5a522ee8c960eb14f598f524c718仅建立同字节镜像但正确引用标签的新CPU evaluator -v2，停止自己的原空CPU evaluator，保留旧inspect/log；原D1/用户服务无操作。双来源核验/生成冻结controller完成后才GPU。

新official CPU evaluator已双来源捕获，raw/eval doc精确相同。严格task_config比较仅因metadata.base_url从19964隔离到19967拒绝；这正是冻结端口差异，评分/样本/生成参数均未变。finish_parallel67_prepare_v3.py SHAc6adb660b36e1f10e51c8873e46c4f34fd3fe00fcf8346ba8c30785e16cb14aa将已知endpoint逐项断言后只归一化此字段再完整比较，不改任务/评测器/原始provenance，继续未完成CPU冻结，不重放数据集推理。新contract同时冻结roles静态资产。

## 执行前冻结与独立CPU复核

prepared437bc241ab36219627c85ea0299e9532cf9188efc520b60ade19b399b8ac70f6，contract200b28638a68318e745a4bc2b4bbbb032c848b0d9a255b75bf8e16ea47b3270c，controller d52d12eed360b9004a01d6a3a392cb9168b3fa827bd2eb86eee516e4236c0979；remote parallel67-v2/commands/control.py。独立CPU审查R/EVAL、仅8037/19967、helpersURL、无stop_source函数/无SOURCE访问、newlaunch CUDA6,7/冻结全部artifactSHA通过。CPU预检旧事件已resolved，0formal请求；新CPU evaluator为qwen3vl-gpqa-parallel67-mx104-20261028-v2。现在只启动一次新controller，运行中再次检查GPU所有权/端口。

## 唯一并行启动回执

controller1815528/ticks1147952882，脚本d52d12ee；14:26:22 E67模型76/ticks1147952917于6/7开始加载，尚未完成该实例graph/native/正式GPQA。原1738426/D1 GPQA正常，串行E1仍保留。当前root source仍由原controller临停，任何恢复只认factor2/results/source-restored.json；并行finally不触碰它。统一heartbeat已改两线，至少半小时简报。

14:29:07独立docker top+mx-smi交叉：host1817633→GPU6、1817634→GPU7，均属新E67容器，不占0/1；Cpuset40-79,120-159/Mems1通过。mapping artifactSHA c1dff465ec5f5d25ac4cbb78118c4ca4534e67790dca575bc5244a4d4b7f832b。CPU pressure avg10 .49%、IO pressure0，load6.67/160逻辑CPU，无明显资源压力，不将其解释为完全零共享带宽影响。两rank capture/native文件已出现、API启动完成，仍等replay16/观察移除/smoke/fullstartup前不宣称formal。三阶段本案例schema/identity/文档链接校验passed。

14:30:21辅助E67当前实例双rank native0/FGV/capture+16replay/观察移除/普通smokeC8/source/config门禁通过，独立GPU6/7 mapping已证明；正式GPQA198/C64开始。原D1仍正式运行，无并行failure。各一次完整结果待终态，不能借旧通过gate，也不能将graph执行计数当独立数值reference。

14:31 heartbeat只读：串行1738426与并行1815528精确ticks仍存活；D1 native184/198（unique HTTP200185），E67 native93/198（unique HTTP20095），无最终分数/失败/恢复终态，同设备E1仍待原串行流程。用户刚于14:30获启动通知，不重复推送，原半小时监控继续；不新增请求/更改服务。


## 当前终态（2026-10-28 15:06后）

同GPU0/1 D1原paged＋split1为127/198=64.1414%，E1 PR638＋default0为129/198=65.1515%，均过64。辅助6/7 E67同E1代码为122/198=61.6162%，有效失败、无gate。三角色均完整198、来源/冻结配置/源码前后/上游无采样覆盖及seed审计通过；独立复核已有D1/E1 gate通过，仅绑定已停止的测量实例。

独立CPU核验 `factor2/results/independent-six-role-audit.json` SHA58f50fd6bcbc6efd9120bb75997f05dedfd26c3d4aeaa7861212fb504f18e28d。六角色全部15对的198doc/arguments一致、完整响应相同数全部0。E1/E67为107两者对、54两者错、22仅E1对、15仅E67对。设备/NUMA/CPU约束/时序不同，不是硬件单变量；D1仍可用全部CPU，隔离GPU/端口/私有缓存不等于证明宿主带宽零干扰。

原串行controller单finally于15:06:38恢复SOURCE opt14：PID1707852/ticks1148172233、f81/原argv/env/cwd/8030/prefixON，回执factor2/results/source-restored.json SHAa04389b01ab18b11e6d3e4eb210748af256ed16c675708689848d43725e60bc8。独立当前collect与恢复身份/源码/模型/tokenizer/版本逐项exact，容器PIDticks和models200实查passed；0额外generation。两个controller退出，D1/E1/E67模型容器均停止，source正常保留；没有把测试通过版本部署到source或转移gate。

## 规划复盘 plan-factorial-aux4-20261028

使用本地inference-optimization-planning，保持accdiag-opt14-c64-gpqa-001 rootcause unconfirmed。补齐组合后不能说只有split0或只有原Prefill导致下降：D1/E1都通过，且同E1代码跨设备辅助失败；未固定请求seed且逐题响应不同，机制和统计不确定性仍存在。原有效低分保留，不自动加完整轮/ERQA/性能，不改采样、MoE、阈值，不做生产修复。

Prefill：PR638条件为单prefill、decoder、seq>=2048、无KV量化；七个C1错而B/R/D/E全对的CPU诊断候选doc21/31/47/91/122/145/170，prompt分别222/241/239/289/308/392/319。不能由短初始prompt排除长输出后的重算或邻居影响，info_once日志也不能绑定题目。Decode：尚无本case同输入QKV/logits/实际noise因果证据；Mixed：批轨迹、无请求seed和并行宿主共享影响尚未排除。未测性能，无累计E2E收益，GPQA耗时不作吞吐。

下一步限CPU按最小doc_id规则选doc21，核对原factory请求、实际路径/缓存与token元数据可得性，设计有限同输入采样窗口；doc21是诊断材料，不得特化生产实现或冒充正式评测。先证明真实tokenIDs/窗口、原始logits和变换前probs/noise捕获可中性执行，再冻结独立有限协议、命令SHA、资源检查和唯一finally恢复。当前尚未启动新GPU观察或完整评测；发现缺映射/实际IDs/路径则记incomplete，不用旧文本重新分词冒充生成IDs。复盘触发为最小复现、设计不足或新的反证。保持原source运行。
