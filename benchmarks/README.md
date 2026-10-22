# Attention 算子性能比较

`flash_attention_compare.py` 在目标 PyTorch 环境中，对比候选文件导出的
`run()` 与已安装的 `flash_attn` 原生 API。无需加载模型，不修改或重启服务。
候选文件须是可独立导入的 Python 文件；其入口签名与本次 main.py 的 varlen API 一致。

## 复现默认18组测试

在已经安装 torch、triton 和沐曦原生 flash_attn 的容器内执行：

```bash
CUDA_VISIBLE_DEVICES=2 /opt/conda/bin/python -P flash_attention_compare.py \
  --candidate /path/to/main.py \
  --output-dir /path/to/results
```

脚本使用可见设备中的逻辑GPU0，即上述物理GPU2。先选定空闲卡；它不会管理、停止或重启其他进程。
`--candidate`、`--output-dir` 都是执行环境内路径。结果自动写入新建的
`fa-compare-<时间>-<随机后缀>/`，已有运行目录会被拒绝覆盖。

复现2026-10-21版本可加：

```bash
--expected-sha256 e2f78d30268caab7656193e070463eaab1271b9fac35c7ed57ffd4ef20cca642
```

若要测修改后的文件，可省略该参数或填新SHA；每次都会冻结候选副本并记录实际SHA。

## 默认条件和计时边界

- BF16、Q16/KV2/D128、paged KV，page16，causal，无ALiBi/滑窗/softcap/dropout。
- Decode：B1/8/32/64 × KV1024/2048/4096，每请求Q1，共12组。
- Prefill：B1/Q1024、B8/Q1024、B1/Q4096、B2/Q4096，共4组。
- 另有两组ragged哨兵：Q=[17,5]/KV=[113,57]，Q=[1009,257]/KV=[1009,1021]。
- 原生Prefill调用 `flash_attn_varlen_func`，Decode调用 `flash_attn_with_kvcache`；
  候选调用文件中的 `run`，包含其Split-KV forward、partial和combine。
- 相同随机输入与置换页表；先进行输出对拍，首个哨兵额外检查FP32 reference，
  每shape做两次变化Q输入graph replay对拍。atol/rtol均0.03，relative L2不超过0.01。
- 每侧20次预热后capture；Decode每graph32次API、Prefill每graph4次API。
  graph预热至少5、最多12个窗口，末3窗口散差≤8%才准入。
- 准入后保留全部9轮，每轮native→candidate→native。报告每API设备时间的中位数、P90、
  散差与原生前后漂移；散差/漂移超过8%返回incomplete，不删除慢轮。
- 校准后每轮目标10ms，replay数限制1…32。P90是9轮调用均值的P90，不是单次调用尾延迟。
- 排除JIT、capture、Python/allocator、元数据生成、KV append、服务输出buffer拷贝、
  TP通信及网络；是重复数据的独立算子测量，不是模型端到端性能或精度gate。

新脚本默认计时核心与原实验一致；收尾还检查native before/after各自的散差，
比原脚本只检查合并native散差更严格。原实验18组均满足此附加检查。

## 可选命令

```bash
# 查看18组shape，不导入torch，不使用GPU
python flash_attention_compare.py --list

# 检查参数与候选SHA，不执行候选模块或GPU工作
python flash_attention_compare.py --candidate /path/to/main.py --dry-run

# 单独复现当前主要Decode形状，随机seed与全量测试对应项一致
python flash_attention_compare.py --candidate /path/to/main.py \
  --output-dir /path/to/results --case decode-b64-k1024
```

可通过 `--cases` 选择逗号分隔的子集，通过 `--q-heads`、`--kv-heads`、`--head-dim`、
`--page-size`、`--dtype`、`--seed`、`--rounds`、`--warmup` 修改条件。
修改默认值会形成新配置，不能将不同workload的数字直接与旧结果计算加速比。
`--timeout` 默认每shape180秒，`--total-budget` 默认总共900秒；超时仅终止本次创建的worker进程组。

## 输出和退出码

终端列 `candidate/native` 是候选耗时除以原生耗时，大于1表示候选更慢。

- `summary.csv`、`summary.json`：所有已选shape的成功、失败或不完整状态及延迟。
- `<case>.json`：tensor布局、来源SHA、数值/graph检查、预热与全部原始轮次、统计与漂移。
- `<case>.log`、`<case>.command.json`：每项日志及精确worker命令。
- `config.json`、`sources/`：冻结配置和脚本/候选副本；独立Triton cache路径记录在配置中。
- `run.json`：整体状态、结果SHA与源文件是否在测试期间改变。

退出码0表示所有测量有效完成，候选较慢也返回0；1表示执行或正确性失败，2表示证据不完整。
失败和超时行保留在汇总中，不以成功shape掩盖它们。
