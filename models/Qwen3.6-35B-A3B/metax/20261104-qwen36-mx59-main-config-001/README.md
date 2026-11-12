# Qwen3.6-35B / mx-59 主线 MoE 配置

已完成用户指定的`qwen36-35b`同机旧配置→新配置→旧配置P1K对照，并恢复试验前的新配置服务。GPU4/5、TP2、0.9、prefix-off、Graph64、全部启动参数、GDN和采样保持。

P1024/D1024/C64/N128，充分形状预热后的三轮总吞吐中位数：旧2907.06、新2982.58、回退2892.56 tok/s；新+2.60%，旧/回退漂移0.50%。原生比较、独立文件重算与fresh HTTP/源码恢复核验通过。未复现MoE新配置造成1K稳态下降。

发现动态batch首次JIT混入短程测试，主要是采样`_guarded_sweep`；旧源也会出现数秒停顿、吞吐降到2159.40。统一请求形状预热后9测量轮无新增kernel元数据、无>0.5s全流间隙。历史跨Host数据没有逐请求明细，不能唯一解释所有历史gap；首失败和全部测量原样保留。

早期25数值/50变化输入Graph和实际配置选择验证复用，未重跑。本次仅targeted诊断，无新完整模型精度gate或四场景正式验收，不外推持续容量。未改启动脚本、不提交推送；当前日志和完整证据见记录。

- [来源与未测正式基线](baseline/README.md)
- [变更、对照、原因和回退证据](optimize/fgv-moe-main-config-001.md)
- [当前结构化状态](optimize/README.md)
- [完整验收尚未执行](acceptance/README.md)

2026-11-05: user-requested unused FGV GDN tuning cleanup completed. Only gdn_chunk.py restored to tracked HEAD; Plugin GDN registration, current main-profile MoE and sampler retained. No service start or inference request. See [cleanup record](optimize/fgv-gdn-cleanup-001.md).
