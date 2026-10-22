# TP allreduce：限域定位地图

## Python归约事件缺失，但源码/实例绑定仍在

- 信号/匹配键：Torch编译graph服务，helper仅以Python条件记事件；当前PPU TP8 BF16→FP32→BF16链，C1/Mixed同前缀最终分布不同。其他编译器/后端须重核，不能直接迁移命中结论。
- 首个检查：核当前运行窗口的FX dtype、最终生成代码实际collective入参buffer/castback、cache artifact SHA与worker/请求/graph绑定。编译内联可绕过Python日志；源函数在磁盘或被绑定本身还不够。
- 数值分叉：编译链正确而raw logits已不同，则用已有raw/概率/noise/RNG做CPU过滤参考；不要先提高更多归约精度。局部输入/输出与最终hidden未保存时，首数值层仍unknown，下一步申请窄前向/LM-head边界取证。
- 停止条件：不能将源码/静态调用数当实际kernel trace或数值通过；没有当前层张量不复用旧版本首差异，也不自动新增请求、埋点或重启。
- 证据等级observation（编译数据流，非新GPU重放），来源[042补证卡](case-index.md#编译路径补证python事件缺失不等于fp32修复未命中)；不改变正式164/198失败，无性能收益。

## Mixed首Prefill同token输入、归约后首次数值不同

| 字段 | 规则 |
|---|---|
| 信号 | 各rank完整目标分支输入逐位相同，postTP首次不同，HC等下游只传播差异 |
| 匹配键 | 现有限域证据为Qwen3.8-Flash-Next/PPU TP8/BF16、hidden2560、778/808目标行、Mixed前7Decode rows、graphNONE首Prefill；其他shape/后端未知 |
| 机制 | 逻辑target行位置改变其落入的通信分块/有效rank累加顺序，BF16逐步舍入非结合；不等同非连续stride或tensor storage-offset错误 |
| 首个实验 | 保存全部rank目标输入和归约前后完整目标行；独立固定数据拆开总shape、target offset、allocation offset、peer填值，BF16与FP32对照；CPU参考使用真实环拓扑而非假设rank按编号排列 |
| 通过证据 | 局部机制应有原始输出逐位重现、三重复/跨rank、canary/input未改写、精确source/shape/stride/offset/comm证据及FP64参考；模型候选仍须同前缀/长Decode/C64及原正式契约验证 |
| 停止条件 | 实际source/布局不明、模型服务有其他负载、资源不足需重启、输出越误差界/非有限/guard损坏或测试跨rank不等时停该测试取证；不自动改服务/采样或把未覆盖ring匹配失败当bug |
| 证据等级 | reproduced，仅该数据/布局/原生版本；不是所有shape不敏感，也不是通用FP32完全逐位确定性（当前FP32仍有末位差、转BF16才同） |
| 来源 | [案例卡029/030](case-index.md)，原始完整证据链接至对应模型optimize记录；未测性能，不宣称正式精度修复 |

## 局部FP32 castback通过，但最终logits仍不同

- 匹配键：同案例031模型实际layer0，FP32归约输出可有1.49e-8末位差，cast BF16后postTP/HC完整目标行同；不能要求FP32天然逐位结合。
- 首个检查：同时保存局部castback/FP64参考与最终raw logits/实际过滤概率/noise；采样token相同不是分布相同。若局部已同、最终不同，转查第一个尚未覆盖的下游边界及内部自有通信，不自动扩大精度改动。
- 停止/晋级：剩余最终差异说明候选尚未达同前缀目标，不能仅凭算子通过签模型gate。任何新增埋点/重载按用户范围另确认，长Decode/C64/正式契约仍分别验证。
- 证据：031，reproduced且限域；明确是“局部修正成功、最终一致性未成功”，无正式精度/性能收益。

033/034进一步缩小该分支：外层helper未覆盖的MoE自有late BF16 collective在同输入后先变；仅为该模型runner实例提高归约精度后，同19/C8的MoE postTP及最终logits/prob均相同，跨baseline上游与FP64参考补证。此时后续首测转向长Decode/C64/原正式范围，而不是从短点通过推定60K已修复或继续盲目叠加精度改动。适用键仍限当前PPU/TP8/hidden2560/778、808+起点7，其他平台/拓扑/尺寸未知，详见卡033/034。
