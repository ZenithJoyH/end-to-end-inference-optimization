# compat-001：新版FlagTree下去除top-k兼容的前置验证

用户2026-10-21要求检查能否去掉top-k patch。目标为PPU-07 `minimaxM3.1-opt-latest-20261020`、FlagTree `0.7.1.dev1+ppu3.6`、MiniMax-M3.1-Flash1019、8045、物理0–7。先执行独立测试，不修改服务或源码；GQA head-tile兼容保留。

设计归属：检查Thead的`_PrefillIndexTopK`是否仍必要。它只把topk16改为同一原生JIT的K128/T16/4warps/2stages，其余输入沿用原生autotune。候选恢复同一vLLM函数的原始heuristics/autotune，不改算法、模型参数或其他dispatch。

模式：本地inference-accuracy-evaluation `minimal-regression`。第一证伪实验为真实PPU数值和graph：从已核验vLLM源码提取原函数到独立测试模块，分别运行原生autotune、现有固定K128兼容、独立CPU参考。覆盖小于/等于/大于topk16、K64/128/256边界、非对齐、当前100K长度上限对应块数、多head、多请求、非连续score、NaN和tie。每项capture后更换score执行两次replay。唯一值要求索引完全一致；tie要求选择分数等价，同时单独记录精确索引差异，存在差异则不能直接认定删除安全。首次真实编译/数值/graph失败即停止晋级，保留patch并做归因，不重启服务。

物理0–7仍承载当前服务但健康idle、每卡约18GiB余量；独立进程仅使用这些已授权设备，小张量，逐卡串行，不访问8–15。任一新请求出现或内存不足4GiB时停止本次检查。原生产服务及三库源码指纹前后复核。

只有上述测试通过且无tie行为疑点，才准备最小去补丁候选和服务级最小回归。当前服务仍使用patch，不能将其旧graph或模型输出当作去补丁证据。本轮没有授权外部消息或自动性能测试，不借用旧精度gate；正式精度按实际后续变更单独判断。

远端案例：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-unpatch-01`。

## 结果与保留决定

物理0–7共50项算子数值/graph检查通过，每项显式2次replay，共100次。GPU0完整22项覆盖上述边界，其余每卡4项代表性检查共28项。真实原生autotune实际选择K64，数值满足独立CPU参考；没有复现此前的K→1编译阻塞。

但同分的精确索引行为不等价：GPU0的257块全同分、129块分组同分输入，原生K64与现有固定K128都选出了正确top-k分数，却产生不同的block集合。固定相同4warps/2stages，仅改变同一原生JIT的K64/K128，再次稳定复现；改变K64的2warps/4warps则结果相同。两项同分输入的每个query16个选中block仅1个相同，集合对称差为30；无同分的257块控制完全一致。这是top-k合法tie选择差异，**不是已证实的模型精度下降或FlagTree新数值bug**。它会改变稀疏attention的实际读取集合，故不能作为无行为变化的清理直接推广。

**决定：保留生产top-k patch；GQA兼容保持。** 本轮只运行了独立测试，未编辑Plugin/FV/FG源码，也未重启8045。前后逐文件源码指纹与API/engine/8worker的argv/startticks完全一致；终态HTTP200、running/waiting均0。去补丁服务未部署，模型最小回归与完整GPQA均未启动，无新精度gate或性能结论。后续若要移除，应作为单独候选验证模型级最小回归和正式精度，再决定是否保留。

## 测试执行问题与证据边界

首个单进程跨卡脚本在GPU0完成22项后，GPU1首项的graph capture发生指针访问错误。按本地`inference-accuracy-diagnosis`核查`torch.cuda.graph.__init__`确认：类级`default_capture_stream`在第一次调用时固定在GPU0，随后切卡复用该stream导致跨设备访问；数值launch本身已通过。此原始失败完整保留并归类为跨卡测试证据无效，不作为原生kernel失败。

只修正测试脚本，为每卡显式创建`torch.cuda.Stream(device=device)`；相同冻结矩阵中剩余GPU1–7的28项全部通过。没有丢弃原失败、修改测试数据/精度准则或修改生产源码。原始22项与补测28项合并为50项，不把失败的GPU1首次capture重复计入通过数。

原生产物：`device-result.json`、`stream-fix/device-result.json`、`stream-fix-reason.json`、`tie-bisection-result.json`、`tie-set-result.json`；每项命令和SHA已归档，控制脚本本地见`../commands/`。远端终态`result.json` SHA256为`509e2067785c07c4160416b3a511450ab17a81df516b33663b165e86ca91acb1`。机器可读结论及各原生证据SHA见[state.yml](state.yml)。

Skill：inference-accuracy-evaluation/minimal-regression，bundle SHA `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`；辅助精度定位只用于归类测试执行错误和隔离K相关tie行为。正式精度未测，模型影响unknown；没有新建或启用监控。
