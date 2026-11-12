# KV gather 案例证据

## DeepSeek-V4-Flash W8A8 / MetaX C550 / 2026-10-23

- 状态：寻址修复kept；证据等级reproduced；性能稳态incomplete。
- [主记录](../../../../../models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/op-001.md)，[案例摘要](../../../../../docs/cases/20261022-thinking-gpqa-metax103/README.md)。数字与原始证据以主记录为准。
- 环境：TP8 C550，vLLM0.24 empty；Plugin a696859b…+fw001；FlagGems8200f71f…+本地patch。mode eager+graph。
- 路径：prefill/mixed，default.flagos→flag_gems.cp_gather_indexer_k_quant_cache；同名FGV副本未命中。真实uint8 cache[15135,64,132]、页stride1039680B，scale页stride259920float，head128；prefix关闭。
- 触发：P32首轮SDK精确gather ATU fault；后续MCCL错误为次生。原故障精确物理ID未捕获。
- 修改：operator/improve；scale地址乘法前int64，以及独立B31/63搜索界限纠错；1个生产文件3行，布局/数据/公式不变。
- 正确性：旧GPU B31/63漏写复现；地址8263旧32位回绕由无访存探针证明；>8GiB同stride参考、canary、graph、仓库13测试及模型10请求通过。
- 端到端：P32三轮各128/128成功，无非法地址/OOM。第三轮较慢、spread12.913%超过10%；全部保留，不宣称稳态性能通过或累计加速。没有新完整GPQA，历史85.86%仍属原实例。
- 后续独立实验：[indexer top-k布局修复](../indexer_topk/case-index.md)定位动态copy编译并通过新的三轮稳定性测量；该结果归属op-002，不回写成op-001原三轮通过。
- 知识差量refined：逻辑KV view尺寸不足以审计地址安全；应核验真实物理页stride和各指针元素单位，并证明算子所属库。内存安全通过与吞吐稳定性通过分别记录。
- 后续首查：真实调用函数→有效物理ID和stride→整数乘法宽度；先做安全算术探针，禁止重新发起已知非法load来“证明”错误。
- 限制：未测其他硬件，未测任意内部stride；原始失败当次输入未捕获；op-001本身没有证明第三轮变慢原因，不能外推该修复提高其他模型速度。后续归因证据见独立op-002。
