# diag-005-attention-blacklist

状态：completed-passed；分类operator/replace；用途：用户指定的精度backend对比，未测试性能，也未决定正式backend替换。

## 结果与决定

修正版完整GPQA strict为160/198＝80.8081%，达到预冻结80%，新gate已签发并核验，当前源码与服务实例仍一致。此前FlagGems候选159/198＝80.3030%，黑名单净增1题、+0.5051个百分点。单轮temperature1/C32没有显示明显整体提升，不能据此认定FlagGems attention是分数偏低的主要原因。

| 同题逐题判断 | 题数 |
|---|---:|
| 双方正确 | 149 |
| 仅黑名单正确 | 11 |
| 仅FlagGems候选正确 | 10 |
| 双方错误 | 28 |

仅黑名单正确doc IDs：18、47、48、52、88、93、94、97、120、166、186；仅旧候选正确：12、45、64、69、99、127、145、152、162、180。原始/处理后198题、gold和实际请求arguments逐项相等。温度采样及批调度可能影响结果，未做固定输入logits/张量边界二分，因此精度因果仍未定位。原始旧任务分数153/198、156/198和修正版159/198全部保留。

## 配置和路径

Plugin白名单/黑名单互斥；直接设置单项黑名单会启用其他算子。本轮构造实际注册表的等价complement blacklist，包含1466项，仅将attention_backend eligibility由true变false。其余实际ATen注册16项及Plugin选择保持，权重/tokenizer22文件新内容校验相等，四仓库源码SHA与candidate04相等。

独立优化容器`qwen36-27b-fa-opt-20261012`、2/3卡、18002；服务实例`qwen36-fa-opt:82515:1791815908.86`，两rank确认vendor.metax/native mcFlashAttn设备kernel、FlagGems varlen/splitkv0、graph190/rank和固定10题C8 smoke通过。源8002和源容器未修改。

修正版gpqa_diamond_generative_cot198题、strict80%、C32、temperature1/top_p.95/top_k20/max30000、harnessseed42/APIseed1234、BF16 TP2 graph、关闭prefix cache保持。评测容器`qwen36-fa-gpqa-fixed-20261012`，run UUID `8215e1f159d64472bdff81c650b89998`，原生cached0；2026-10-12 14:43:56 UTC启动，15:41:47 UTC结束，198唯一题/两filter396行与来源验真通过。

超时0；原生响应日志14条length、184条stop，仅作健康观察，正式分母198不变。日志一次ERROR字样来自模型思考文本，不是运行异常。辅助日志matched186、strict154/186不能替代正式160/198。

## 启动缓存诊断

首次切换沿用FlagGems编译cache后启动失败：原生返回Hkv2无法赋值到Hq12。两种backend共用cache key96868c4236和相同key factors，但attention submod7占位参数顺序及KV update边界不同，旧产物将KV张量作为query。独立cache验证了正确query heads12和实际16-token KV page。

最终采用`VLLM_CACHE_ROOT=/tmp/qwen-fa-native-clean-vllm-cache`，这是backend切换时必要的缓存隔离差异。私有Plugin诊断日志已完全恢复原字节SHA`9a1e87cb97b9ec3283351e3e75d8a25f81c9800fc140661e094eb0da7c2c2bae`；未保留源码语义补丁、未改vLLM/SDK。独立784-page API子页方案的9项数值/graph证据仅为诊断，扩展probe未完成后已精确取消；子页适配器未接入模型，不算本轮修复。

## 证据与回退

远端案例根目录：/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention

| 证据（相对此根目录） | SHA256 |
|---|---|
| manifests/blacklist-03-service.json | 2ae3b7082106706b4f40292cab2f23c6a6c9466c3b9c9369e5ce2aff33d8374c |
| manifests/gpqa-attention-blacklist-process.json | ea0164ea623d5116c256ba60f17bff03523a54042ebc5b85242f10e1ee322589 |
| results/gpqa-attention-blacklist-terminal-validation.json | c9d47036d60d387b79f370081e92894bd75aae653ec62129427578ed8ae53ec2 |
| results/gpqa-attention-blacklist-accuracy-gate.json | db81877b5787e8d5c5177cc7b685e02fc5f96f1375b69d103cc3a345deb3c081 |
| commands/diag005-finalize-terminal-v2.py | d24aa9b2d7dc22a962fb86954731c9ed37320716579fc11cca8939f51d77356e |

完整native results/sample/run-record路径、SHA、启动/诊断命令及回执在state.yml；结果目录results/gpqa-attention-blacklist，日志logs/gpqa-attention-blacklist-formal.log。终态校验脚本仅验证已有结果及当前源/实例，未发模型请求；gate issue/check passed。

当前黑名单服务保留、监控qwen36-metax-flash-attention-op001已PAUSED。历史candidate04配置/gate保留；回退必须核验精确实例并按rebind或重新正式评测绑定，不能将原gate直接当新服务gate。不部署源服务，不自动重测，不开展性能。
