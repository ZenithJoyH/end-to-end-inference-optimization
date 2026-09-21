# fw-010 TP8 collective 因果微基准草案

## 范围与当前证据

本文仅准备下一轮本地脚本和执行契约，未在 PPU-01 执行，未修改服务、
Plugin、FlagGems-vllm、FlagGems 或 vLLM。远端执行前必须先在
`models/Qwen3.8-Flash-Next/ppu/optimize/state.yml` 建立稳定实验条目，并创建
`optimize/fw-010-ring-allreduce-causal-control.md`；本次为避免与正在进行的
`op-015` 共享 ledger 编辑冲突，没有提前改动这两个文件。

`prof-005` 的 no-stack TP8 trace 在 P4096/D128/C64/N64 上证明：

- Mixed 63 个 graph window 中，RING AllReduce 跨 rank 中位累计 activity
  为 `3.968s`，Mixed marker wall 中位为 `40.143524s`。
- Decode 中 two-shot AllReduce 中位累计 activity 为 `1.742s`。
- collective 调用次数在 rank 间一致，但 stream-sync 累计等待差异很大；
  因此 rank spread 仍可能是 profiler observer effect 或上游 straggler，不是已证明的
  通信配置收益。

## 真实调用和 shape

模型有 48 层，每层 attention output 与 MoE/MLP output 各有一次 TP
hidden-state 归约，即每个整模 step 为 96 次 all-reduce。当前 vLLM
revision `ee0da84ab9e04ac7610e28580af62c365e898389` 上的精确框架路径是：

```text
attention out_proj
  -> vllm/model_executor/layers/linear.py::RowParallelLinear.forward
  -> tensor_model_parallel_all_reduce(output_parallel)

MoE/MLP output
  -> vllm/model_executor/layers/fused_moe/runner/moe_runner.py
     ::MoERunner._maybe_reduce_final_output
  -> tensor_model_parallel_all_reduce(states)

both
  -> vllm/distributed/communication_op.py::tensor_model_parallel_all_reduce
  -> get_tp_group().all_reduce
  -> vllm/distributed/parallel_state.py::GroupCoordinator._all_reduce_out_place
  -> vllm/distributed/device_communicators/cuda_communicator.py
     ::CudaCommunicator.all_reduce
  -> supported-backend dispatch; custom AR is disabled, trace lands in PCCL
  -> trace-selected RING (large) or two-shot (small) device kernel
```

当前服务启动显式带 `--disable-custom-all-reduce`，所以 vLLM custom
all-reduce 不是可比较候选。`CudaCommunicator` 在 custom 之前还有
symmetric/quick-reduce/FlashInfer 等条件分支，在 custom 之后通常进入
PYNCCL；现有记录只证明了最终 PCCL kernel 和 custom-disabled，没有保存
`Using [...] all-reduce backends` 运行日志行，因此不把 PYNCCL 当作已完整证明的
`impl_id`。远端运行前应先从保留服务日志补读该行；这个只读校验不改变
微基准的 PCCL 底层对照目标。保留配置为 BF16、`hidden_size=2560`、
`max_num_batched_tokens=4096`、`max_num_seqs=64`，因此首轮的两个加权生产消息为：

| 阶段 | tensor | 每次消息字节 | trace 自动选择 |
|---|---:|---:|---|
| Mixed/Prefill | `[4096,2560]` BF16 | 20,971,520 B (20 MiB) | RING AllReduce |
| full Decode | `[64,2560]` BF16 | 327,680 B (320 KiB) | two-shot AllReduce |

`[1,2560]` 只作 Decode 边界正确性控制，不进入收益加权。

## 已有配置入口与候选边界

- backend 只用当前已验证的 `torch.distributed` `nccl` 入口，其在 PPU
  环境落到 PCCL。这个 standalone 入口用于测 PCCL 消息大小/协议选择，
  不冒充 vLLM `CudaCommunicator`/PYNCCL wrapper 开销的完整仿真。
- baseline 不设 `NCCL_ALGO`/`NCCL_PROTO`，保留 PCCL 对不同消息大小的默认
  RING/two-shot 选择。
- 候选仅设 `NCCL_PROTO=Simple`。该入口已在同一 PPU/PCCL 栈的 HY4 TP16
  独立微基准中真实生效；其 25 MiB 形态改善约 8%–10%，但 8 MiB 和
  4 MiB 分别回退约 47% 与 12%–13%，所以不能外推到 Qwen TP8。
- 不设置未在当前 PCCL 证明的 `NCCL_ALGO=TwoShot`；trace 中出现
  two-shot kernel 名不等于存在这个环境变量取值。`Tree` 在同平台既有
  sweep 全面慢于默认，不进入首轮。

## 微基准和待执行命令

脚本：
`docs/cases/20260919-qwen38-flash-next-ppu-e2e/fw010-tp8-collective-microbench.py`。

它为每个 shape 捕获一个含 96 次 all-reduce 的 graph，不计 profiler，且：

1. capture 结果必须逐元素 bit-exact；
2. 修改输入后两次 replay 都必须逐元素 bit-exact；
3. 计时前的 buffer reset、rank barrier 和 device synchronize 不进入计时；
4. 7 轮整链重放的每 rank 样本都写入 JSON，用 rank-median 和
   `max/median` 判断 straggler。

待 PPU0–7 确认无服务/无 worker、`op-015` 已结束且 fw-010 ledger 已登记后，
在优化容器内用两个独立 communicator 进程组执行：

```bash
source /usr/local/PPU_SDK/envsetup.sh
export PATH=/usr/lib64/openmpi/bin:${PATH}
export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:${LD_LIBRARY_PATH:-}
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
export GLOO_SOCKET_IFNAME=eth0
export NCCL_IB_HCA=fic2_soe_bond
export NCCL_IB_GID_INDEX=1
export NCCL_IB_ADDR_FAMILY=6
export NCCL_SOCKET_IFNAME=bond
export NCCL_SOCKET_FAMILY=AF_INET6
unset NCCL_ALGO NCCL_PROTO
torchrun --nnodes=1 --nproc-per-node=8 --node-rank=0 \
  --master-addr=127.0.0.1 --master-port=29631 \
  fw010-tp8-collective-microbench.py \
  --output /absolute/new/result-root/default.json

unset NCCL_ALGO
export NCCL_PROTO=Simple
torchrun --nnodes=1 --nproc-per-node=8 --node-rank=0 \
  --master-addr=127.0.0.1 --master-port=29632 \
  fw010-tp8-collective-microbench.py \
  --output /absolute/new/result-root/simple.json
```

当前 PCCL revision 有已记录的 graph 工作完成后
`destroy_process_group()` 不返回问题。脚本在全 rank 最终 barrier 后显式正常
退出，不把 communicator teardown 混入性能变量；如果运行期 collective 本身卡死，
仍视为 graph safety 失败。

## 决策与停止条件

只有以下条件全部满足，才能进入服务候选：

- baseline/candidate 的 capture 与两次变输入 replay 均 bit-exact；
- `[64,2560]` 和 `[4096,2560]` 的加权 collective chain 中位改善至少 8%；
- 每个生产 shape 的最慢 rank 不超过 rank 中位的 1.10 倍；
- 候选对 Mixed RING 的改善与 `3.968s / 40.143524s` 贡献结合后，
  能合理预测至少 1% Mixed wall 收益。

出现任一情况立即停止，不修改服务：

- 任一 bit-exact、graph capture 或两次 replay 失败；
- runtime collective 卡死、rank 分叉或明显 outlier；
- `Simple` 对大消息的收益被 320 KiB Decode 回退抵消，或加权收益低于 8%；
- 大消息改善不足以预测 1% Mixed wall；
- 只能通过未证实的 PCCL 环境变量、修改共享 runtime 或转向已禁用的
  vLLM custom all-reduce 才能继续。

即使过了上述算子门槛，也只允许启动独立服务 A/B/R；profiler-on
activity 和本微基准不是端到端收益。正式精度仍被 GPQA 170/198
(`85.86% < 88%`) 阻塞。
