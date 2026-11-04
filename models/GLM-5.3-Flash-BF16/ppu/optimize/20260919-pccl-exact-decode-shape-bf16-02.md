# 20260919-pccl-exact-decode-shape-bf16-02 PCCL 算法选择

- 状态：`failed`
- 分类：`framework`
- 目标场景：TP16 BF16 Decode all-reduce
- 目标阶段：Decode
- 依赖：PCCL/FlagCX collective

## 优化方向与瓶颈依据

Decode trace 中 two-shot all-reduce 占可见设备活动，实际 payload 为 TP16 BF16
`[32,4096]`，即 256 KiB。测试强制 Ring/Tree 是否优于自动选择。

## 优化内容与适用边界

使用 SDK benchmark 对相同 dtype、进程数和 payload 比较 PCCL 自动、Ring、Tree；
没有修改模型服务。

## 正确性与路径命中

9/9 进程退出 0，`#wrong=0` 且无越界。首次误用 `bfloat16` 字符串导致 FP32 fallback
的结果已作废；结论只使用工具支持的 `bf16`。

## 性能效果

| 算法 | 中位延迟 | 相对自动选择 |
|---|---:|---:|
| 自动 | 78.45 μs | 基线 |
| Ring | 110.4 μs | +40.7% 更慢 |
| Tree | 263.9 μs | +236% 更慢 |

## 决定、风险与回退

决定不强制 collective 算法，继续使用 PCCL 自动选择。没有服务源码或配置改动。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/allreduce-analysis/pccl-exact-decode-shape-bf16-02`

