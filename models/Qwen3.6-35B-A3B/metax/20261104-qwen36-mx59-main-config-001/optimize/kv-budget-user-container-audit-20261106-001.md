# PR702 在用户 release/0.2 容器的只读核验

日期：2026-11-06。范围：mx-59 / `vllm0202-fl-release02-20261106`。用户要求核实实际问题与正常启动是否需要补丁；本次没有重启、修改源码/参数、启用开发接口或发送模型请求。

## 结论

**当前配置正常启动不依赖 #702。** 此容器 Plugin 为干净的 `release/0.2@6e11d0ab687247fdf4347a52788ec4f2baf57c79`，没有 PR702，仍已完成模型加载、profiling、graph capture 和 API startup，health=200。不能把 PR 描述为该容器必需的启动修复。

**源码中的预算口径缺项仍存在，但本次未量化当前启动漏算的字节数，也没有复现 OOM。** 总显存×utilization 是绝对预算，profiling 的 non-Torch 项仅为相对初始快照的增量；初始正 non-Torch 占用不在自动预算扣减项中。PR702 补扣该项，并对 warmup 后的 requested-limit 建议做相同修正；基于初始 free memory 的建议不得再次扣减。初始 non-Torch 是设备总占用减当前进程 Torch reservation，不等同于已确认的某个库泄漏。

## 当前服务证据

- vLLM 0.20.2，TP2 / GPU4、5 / port8020 / utilization0.9 / prefix cache关闭；max-num-seqs64、max-num-batched-tokens8192、FULL_DECODE_ONLY capture64，无显式 KV bytes。
- 未修复 worker SHA256：`51a168eae6dbe45b3598eefb1dba7fb5ce6bfb9344ffe3ec5d9df4d725cd2bc5`；memory_policy helper不存在。检查前后 API/EngineCore/两worker启动身份与worker源码一致。
- 启动日志记录 profiling/warmup 146.93秒、GPU KV cache 2,151,245 tokens、graph capture及 Application startup complete；所读完整日志未见OOM。metrics记录2068 GPU blocks，当前running/waiting均0、逻辑KV使用率0，后者不表示物理KV预分配已释放。
- mx-smi观察每卡61652/65536 MiB占用（约94.07%），剩3884 MiB。相对0.9×总显存高2669.6 MiB。该终态占用还含graph、工作区及后续分配，**不能把这2669.6 MiB直接归因于初始non-Torch漏算**；utilization也不是硬件强制上限。
- 当前日志没有初始MemorySnapshot和完整profiling分项，无法从结果反推初始占用。VLLM_SERVER_DEV_MODE未设置，OpenAPI未暴露collective_rpc；未启用接口、未注入进程代码、未执行worker RPC。

## 验证边界与下一步

没有做同配置有/无补丁的重启对照或高水位图文负载，因此不宣称该补丁在当前容器已证明能防止OOM，也不宣称可安全删除。历史mx104的初始占用和短测结果不转用于本容器。若需要证明当前实例的具体漏算量，应在用户允许的下一次受控启动中记录同一进程的initial snapshot、profile分项、实际KV分配和capture后显存，再做同配置比较；不通过另开CUDA进程的快照冒充原worker初始值。

既有精度/性能状态、PR702和其他容器均未更改。

## 归档

远端只读证据归档：`/public-flash/jinghao/qwen3.6-35B/20261104-qwen36-main-config-compat-mx59-001/kv-budget-user-container-audit-20261106-001/`。

`evidence.json` SHA256：`90ba0316b146c1c3c7238ef4502fbd8b7fd7765aae53e7de55517d68ea8c8090`。包含服务/源码/日志摘要、GET health/metrics及设备数值；不保存其他GPU工作负载或完整环境变量。`inspect.py`为本次已完成的只读观察脚本存档，归档操作没有重执行它；不将后归档表述为预冻结实验。
