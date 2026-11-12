# PLE short-conv 地址安全排查图

| 项 | 限域规则 |
|---|---|
| 信号 | PLE状态kernel invalid page；小C1通过而大状态池/持续请求更替失败 |
| 匹配键 | 独立state更新kernel、加载int32 row、large row stride、BF16；先核实际源码和IR，不以模型名匹配 |
| 机制 | row范围合法，但row×stride先32位溢出；最终pointer64或乘后sext不能恢复 |
| 首查 | 分别追踪输出和更新kernel的load→mul→extension→GEP；边界floor(INT32_MAX/真实stride)+1；区别元素偏移和字节偏移 |
| 首个证伪 | 用已有driver寄存器/反汇编及CPU整数oracle；危险原kernel先有界地址探针，不直接真实越界复现 |
| 修复候选 | 仅在乘法前扩位；读旧状态和写回共享正确offset，保持mask/数学/舍入 |
| 通过证据 | 固定版边界/NULL/负数/空请求、prefill/decode/spec、history读写/canary、capture及两次changed-index replay；生产通道宽度的state exact对比是另一独立门禁，再同预算模型回归和原正式契约 |
| 状态反例首查 | 固定小通道地址测试通过而宽通道state失败时，用安全小索引、相同原始输入和独立CPU参考比较原版/候选，重复重置保留每次state；output tolerance通过不代表写回正确，差异数量变化只支持调度/同步嫌疑，不直接归因 |
| 同步机制分支 | 若错误集中history跨warp边界，核TTGIR blocked layout与old-position→write-position依赖。CTA间channel不重叠不代表CTA内部无WAR；同binary A/B/A、相同layout加barrier、分离读写snapshot及单warp做有界反证 |
| 编译/缓存区分 | 复用cache与新cache、独立进程的实际binary SHA及数值重复同时核验；同binary仍随机差、barrier保持layout且load→CTA-sync→store、全部首差可由合法覆盖交错重建时，优先源码同步缺失，不把合法layout选择称为算术误编译 |
| 同步候选晋级 | 读旧state后写前的无条件CTA同步优先于全池snapshot；先验证生产宽通道/三dtype/非连续layout/spec/history/empty与graph换索引，再用户授权的服务回归。barrier或新layout的性能和跨平台支持必须另测 |
| 停止条件 | 生产state回归失败即停晋级，即使原版也失败；不靠放宽容差/只重试失败挑通过掩盖。需要重启/埋点或资源不足未授权时停；原state缺失/无launch绑定时不称逐值设备输入已证明；不把局部通过当精度gate |
| 等级/来源 | reproduced：固定版地址/graph合成验证与原版/候选低索引state失败；原事故为高置信度离线机制。见[证据卡](case-index.md)，无修复后模型回归/性能结论 |
