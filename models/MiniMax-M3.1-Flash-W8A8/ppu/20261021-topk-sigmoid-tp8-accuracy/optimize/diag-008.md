# diag-008 new2与原容器精度对照

状态：现有原生归档对照完成；用户补充的最高分轮次待定位。使用本地精度诊断流程只读比较原生产物，归档对照脚本与聚合报告；未发送模型请求、重启服务或修改源码/配置。本轮new2 GPQA已通过81%门槛，该诊断不改写原分数或gate。

## 比较对象与分数

| 数据集 | 已核验旧容器10/19归档 | 用户补充最高分（待原生核验） | 本轮new2 acc-007 |
|---|---:|---:|---:|
| GPQA | 171/198，86.36% | 89.90%（按完整198题粒度推定178/198） | 167/198，84.34% |
| Math500 | 461/500，92.20% | 93.80%（推定469/500） | 464/500，92.80% |
| ERQA | 255/400，63.75% | 66.25%（推定265/400） | 259/400，64.75% |

用户最高分顺序93.80/89.90/66.25按完整样本粒度对应Math500/GPQA/ERQA，尚未取得对应原生产物及配置。相对该用户报告值，本轮GPQA少11题约5.56个百分点、Math500少5题1.00个百分点、ERQA少6题1.50个百分点；这仅为待核验的数值差，不是已证明代码回归。不能把已核验旧归档171/461冒充用户更高的178/469那一轮。

## 已核验的可比性

旧run为`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261019-minimax-m31-flash-ppu-tp8-accuracy/accuracy/user-flash1019-t1-suite-20261019-02`；新run为同本案例的`accuracy/new2-t1-suite-20261022-01`。两者都是Flash1019、TP8物理0–7、BF16、prefixcache开启、max_model_len100000、max_num_seqs64、batched tokens8192，FULL_AND_PIECEWISE capture sizes相同。

模型产物指纹/tokenizer/vLLM Python源码树SHA相同；权重指纹使用既有manifest范围，不冒充全分片完整哈希。GPQA全部198题及Math全部500题的doc/prompt/target hash逐题一致，原生任务配置去metadata后完全一致，实际payload均temperature1/top_p.95/top_k-1/seed1234；生成上限分别18000/28000。两轮正式客户端并发均32，无timeout/原始空响应/NUL-only。

用户另报max_model_len32768，说明其最高分轮次与上述100000归档不是同一服务契约。上下文总长度与生成上限是两项配置；目前不能推断其GPQA实际生成预算也是32768，也不能断言长度差就是掉分原因。

## 逐题变化与失分线索

GPQA旧171→新167：164题两轮均对，7题由对变错，3题由错变对，24题均错。7个新错均有可提取的严格答案，仅2个触顶18000；不能主要归因于格式提取失败或全部归因预算。净少4题全部在化学，物理/生物正确总数相同，这只是定位线索。全体新31个错题中17个触顶，11个缺严格答案提取且均触顶；旧27错中16触顶、10缺严格答案提取。延长预算是否恢复得分需要同请求验证，不能加回推测分数。

Math500旧461→新464：454题均对，7题由对变错，10题由错变对，29题均错。两轮各1题触顶28000且错误。相对已核验旧归档，Math500实际多对3题；相对用户最高分则尚缺原生逐题对照。

## 源码差异与结论边界

| 组件 | 旧归档HEAD | new2归档HEAD |
|---|---|---|
| Plugin | 08da21cb39601752040196232b60a152382c0f8f | a696859b9aa528dfd5b21f5da3403fdc16bac4cd |
| FlagGems-vllm | 46387d7f96050204c1b932f35680a3ea03896fa6 | 0dfb5cd7478e58320e81124d31473f06eac79aba |
| FlagGems | 3b76f81d4113e585f7fead01f46113dd249dc9a9 | 8200f71f51d784d54a5a51019cb955acb74d64c1 |

HEAD之外还包括各自工作区保留改动，完整包Python/config树及真实导入路径已写state。旧run没有完整编译器指纹；new2为FlagTree0.7.1.dev1+ppu3.6及用户dot-K16修改。多个组件同时不同，不能把分差直接归因topk-sigmoid、量化融合、编译器或平台特化，也不能把固定seed视为跨数值栈逐token一致的证明。当前根因未确认，无修复或回退动作。

## 后续验证与64并发约束

已在用户test目录及已知评测容器/工作目录有限查找，未找到89.90/93.80/66.25那轮原生结果；未扫描整个共享/mnt。已异步请求该轮结果目录。

先取得该轮results/samples/config，核实实际生成预算、评分filter、seed、权重和完整样本。若需要补测，按用户要求统一64并发、新run/独立cache、单次全量并保留全部结果，不择最好轮。要区分代码回归，旧/新两组合须使用同一个C64契约；只把当前100000服务从C32改C64不能称复现用户32768服务，也不能与旧C32构成单变量代码A/B。当前未获明确重启授权，不改变现运行服务的上下文或源码。

## 外部证据

脚本：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/commands/diag008-native-compare-20261022.py`，SHA `75cf0d0c9d07c1202a8cbf768016cf786e4b26103513aebad8423f28ca4f5a82`。

报告：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/accuracy/new2-t1-suite-20261022-01/diag008-native-comparison-20261022-01.json`，SHA `0f61e518e757f06674dfb5e2b4ec52ab71c86a3e6848b02f3df0124c502fac2d`。报告仅保存聚合统计、配置和证据引用，不保存题目/答案/响应正文；各native result/sample及身份SHA见state的diag-008.comparison。
