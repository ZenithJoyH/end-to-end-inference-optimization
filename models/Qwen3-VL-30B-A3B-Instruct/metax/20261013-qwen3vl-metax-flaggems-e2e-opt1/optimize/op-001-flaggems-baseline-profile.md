# op-001 保持FlagGems开启的基线与分阶段归因

用户要求对Qwen3-VL-30B-A3B-Instruct/mx-59进行端到端优化，指定qwen3vl-opt1历史CSV，不允许通过关闭FlagGems算子获取收益。候选只改当前链路的FlagGems/FlagGems-vllm算子实现、调优或不改变其选择的执行组织；不增加黑名单，不切native/vendor，不恢复刚回退的Plugin采样特化。现有blacklist mm,mm_out,layer_norm,log_softmax冻结。

源qwen-vl的完整MoE仍为op010，Plugin采样为op012原版；source服务qwen3vl-opt1/8000/TP2 BF16/8192batch/64seq/FULL_AND_PIECEWISE capture64/prefixcache关闭。源P64K benchmark仍在运行，不干扰、不暂停、不重启。新案例用快照及同挂载的新容器，设备0/1；因此历史设备4/5结果只用于参考，独立基线必须重建。当前正式目标按P1K→P4K→P16K→P32K，D1K/C64/N128；用户P64K保留为额外场景，不替代P32K。

主指标暂按稳态输出吞吐，守护TTFT/TPOT/错误率，等待用户偏好；GPQA正式阈值已异步询问，阈值未冻结前不发正式gate。早期baseline-sanity固定10问/C8、graph capture和至少两次replay，性能baseline及缩减milestone与profiler计时分别存证；无正式验收声明。初始Prefill/Decode/Mixed热点unknown，须以实际trace/命中确认，再选择算子与单变量实验。

镜像谱系verified、挂载门禁passed；远端目录 /public-flash/jinghao/qwen3-VL/20261013-qwen3vl-metax-flaggems-e2e-opt1。状态running。

## 环境与初始护栏

新快照95b9a569b220bdefefd8d56763bd8e723619915a7e3c21c234cb8276ee777878，parent为源镜像523407e0...；源码/导入/依赖指纹相等，同挂载工具passed。Docker弃用警告进入stdout导致首次ID断言失败，保留原件后解析并独立核验canonical ID；不重建、不暂停源服务。新容器qwen3vl-flaggems-e2e-20261013，服务18430，maxCapture64与source相同，prefixcache显式disabled。

graph混合和decode各11项capture完成；两worker第一真实apply的FG全MoE函数来自FlagGems-vllm MetaX目录、use_flaggems=True、黑名单与source一致。固定真实GPQA首10问+seed20261013/C8和单请求smoke均非空，两个rank至少两次graph replay；10问均达到256tokens截断，仅早期健康观察，无正式分数。源推理环境无pyarrow，未安装新依赖；独立CPU-only官方flageval:v1评测容器读取固定数据，SHA3753f261a38bdff1176013209af120805c02c7544a86debdadfde03cbac5aec7，完整198行。未调整FlagGems选择或采样代码。

## 无profiler测量准入

首次客户端预检因DockerConfig PATH不含/opt/conda/bin而失败，未发送请求；仅修正客户端PATH，未变更推理环境。第二次Prefill预热输出吞吐20.3967/35.2487/35.4004 token/s，固定三轮预算的spread42.6%超过5%，所以无测量轮准入，旧数据保留。预先改为五轮预热、末三轮spread≤5%、三轮测量，对baseline/candidate/revert统一使用plan-v2；P1K目标总诊断预算1800s、单轮600s。attempt03结束：Prefill末三轮预热稳定、测量35.45/35.62/35.36 token/s；Decode末三轮预热1692.52/1609.62/1606.41，spread约5.3%超过5%，未准入测量，Mixed未跑。没有删除慢轮或形成收益结论。

源与独立服务实际调优环境核对相等（设备号和诊断observer除外）；冻结原有oplist、Tritoncache和黑名单，无关闭算子操作。

## 撤销持续取证开销

发现旧observer只在首次MoE apply后停止sys.setprofile，API/Engine中可能长期保留回调。旧attempt03因此只作诊断；正式比较前另建基线。有界observer-v2不安装Python profiling回调，只在第一次apply记录真实库/shape，随后恢复原方法；import hook在类加载时恢复；graph replay观察16次后恢复原方法。只停止独立18430 API及关联进程，不动源qwen-vl。首次精确控制脚本因Signals枚举序列化报错、未发停止信号，保存原件后用int(sig)修正，v2重启完成。算子/黑名单/Plugin采样源码没有变化。

有界observer新服务API21501、worker21989/21990，GPQA首十问/C8、capture与两rank至少16次replay通过，first-apply/import/replay钩子均恢复，Pythonprofile=None。实际w1=[128,768,2048]、w2=[128,2048,384]（TP2）；源码、导入和选择不变。新服务绑定baseline-e08c8ba2e3ab4bce88a5dd17aa36e3c3，manifest SHA0dcffdb4b637297dd940521b070375a390cb6dd92c4573073636c3b283870d69。当前先采集维护版profile三阶段（每组一轮无profiler上下文、一轮profile）；计时只作诊断，不代替稳态性能比较。
