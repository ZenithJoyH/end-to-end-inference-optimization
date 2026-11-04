# 20261018-prefill-host-sync-40 消除索引器短Prefill判断的GPU同步

- 状态：隔离探针完成、暂存未安装；分类 `framework`；父场景 `p32768-d1024-c64-n128`；阶段Prefill/Mixed，Decode为守护。

## 优化方向与瓶颈依据

实际Plugin `sparse_attn_indexer_kpool` 每次Prefill用`positions[decode_tokens:num_tokens].max().item()`判断上下文是否≤2048。这会产生设备归约与主机读取。当前vLLM indexer builder已明确`seq_lens_cpu_upper_bound[num_decodes:]`对Prefill精确，用于chunk分配；它是原始token粒度，压缩后seq_lens不能混用。

假设：在Plugin已有metadata-builder hook内计算一次Prefill终点最大值并附加到本模型metadata，调用处用该CPU整数替代GPU归约。减少每层同步及kernel launch，实际收益待测，不把消除同步自动视为端到端收益。

## 优化内容与适用边界

设计归属：复用`vllm_fl/patches/glm5next.py`中幂等kpool builder hook和`models/glm5next.py`的本模型索引入口，不改vLLM。只在CPU上界张量可用且Prefill rows存在时填元数据；原始GPU判断作为缺元数据fallback。保持所有positions、pool写入、logits、Top-K、cache和dtype不变，不按题号/模型路径选择。

必须证明异步spec decode的非精确CPU行被排除，mixed批次仅对Prefill行取最大值。边界2047/2048/2049、不同已缓存长度、chunk续写、多个请求、无CPU字段和纯Decode分别验证。目标graph capture/两次replay与C1/C8仍需验证。源码落地前保留既有dirty副本，回退精确恢复本次前内容。

## 正确性与路径命中

已完成32组CPU元数据语义对照、32组原GPU读取fallback路径、2组禁止设备访问spy检查和边界/缺字段检查；通过。候选模型文件SHA `cd0304435c4c6f2a000cb226c2ee455e8760b19b091ebd290296edf40c7a72a5`、metadata hook SHA `27e46b37b31901f918a63de6f5644f5bad371f0a7bd068a80e41d03edbe3ba36`，部署包SHA `19331d6442b9337ac349a7acc3df845f3bd6d15aefa4888586b4040a4e58723b`。仅外部暂存，未安装到运行服务；设备对照/计时等待点39结束且设备空闲后执行，不污染基线。

## 性能效果

点39结束后的隔离设备探针通过12组设备语义对照；shape=[32768]、100组配对样本。旧GPU归约/主机读取判断的host wall中位数19.8145µs，候选CPU整数判断0.3005µs，差19.514µs/次。这不是模型关键路径测量，不能把比例或每次节省量直接当成端到端收益。

相比当前长Prefill约55秒批次，单次可消除成本很小；暂降低服务试验优先级，等待实际调用次数/关键路径占比证据，不为此单独安装并重启服务。模型graph capture、两次replay、C1/C8与Mixed A/B/R尚未运行，端到端收益为not_run；若后续晋级，仍须吞吐≥3%且P99守护退化≤5%。

## 决定、风险与回退

`staged/deferred`，未安装、不提交推送。不能假设普通seq_len上界对spec decode精确；不能仅用整个batch max误判短Prefill。字段缺失、设备不为CPU或形状不符合时原路径fallback。仅保留候选与探针证据，不将micro通过标为模型正确性通过。

## 外部证据

远端：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261018-point40-host-sync`；本点源文件快照与候选保留在该目录。快照控制命令先保存到点39的`commands/stage-point40.py`后执行。

设备探针`commands/device-micro.py`，结果`device-micro.json`；未修改原始采样字段。
