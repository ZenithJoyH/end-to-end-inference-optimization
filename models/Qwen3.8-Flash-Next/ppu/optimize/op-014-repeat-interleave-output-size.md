# op-014：repeat_interleave 已知 output_size 消同步

## 状态

`rejected_reverted` — 微探针、Plugin 补丁、full graph capture 和服务级
canonical 均通过，但同卡组 P4096/D128/C64/N64 A/B/R 只改善
0.1309% 输出吞吐，低于预冻结的 1% 门槛。补丁已回退。

## 改动

`PleShortConvAttentionMetadataBuilder.build()` 在混合 spec/non-spec token 分组时，
将 CPU metadata 已知的
`num_spec_decode_tokens + num_decode_tokens + num_prefill_tokens` 传给
`torch.repeat_interleave(..., output_size=...)`。不改变 token 排序、dtype、shape
或 fallback，只避免 PyTorch 为求输出长度执行 device-to-host scalar read。

- 补丁：`commands/patches/op014-repeat-interleave-output-size.patch`
- 修改前文件 SHA-256：`3ae84180f7b5f4d70886c98f1d1afcf2255f8f7223a110397ec4894cf81a9a59`
- 修改后文件 SHA-256：`c1062b5810a1bcfec7cfca7f61e11a0ffd08700cee2b3f6472b7086d195a87e7`

## 独立探针

P4K 三个典型形态（单请求 4096、64 请求 Mixed 总计 4096、64 路
Decode）全部逐元素一致。每次原路径有 2 次 `item/_local_scalar_dense`
和 2 次 `cudaStreamSynchronize`，传入 `output_size` 后全部为 0。无 profiler
主机耗时从约 51.9–53.2µs 降到 25.0–28.0µs，改善约 47%–52%；
三组候选 graph capture 均通过。

证据：
`/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/diagnostics/op014-repeat-output-size-probe-02/result.json`。

## 服务门禁

- service51：PPU0–7，port 8031；与 service50 的 maxseq64/batched4096、M64 BM16、
  QSA 8448 和 native `mm/mm_out` 配置一致。
- PIECEWISE 19/19 和 FULL Decode 11/11 graph capture 均完成。
- 3 波×8 并发共 24 次 canonical replay 完全一致，且与 service50
  canonical SHA-256 `54f05e02051a882c0b45503581c97389e987c8e8b7be6bd7a227e544b7d9cbf7`
  相同。
- 服务身份证据 SHA-256：
  `8849da895991cea79fd6d27963625a7e9d82c29ced43e987f1a8eefe4a5a8872`。

## 端到端判定

- 跨卡组 D1024 筛选因 PPU0–7 与 PPU8–15 冷启动/设备组差异被判定为
  `invalid_control`，安全停止客户端后未用于归因。
- 同卡组使用 PPU0–7、port 8031、同一 plan/contract/client，分别启动 fresh
  baseline/candidate/revert 进程；三组均 2 warmup + 3 measured、零请求失败，
  graph/canonical 均与 service50 一致。
- baseline/candidate/revert 输出吞吐中位数分别为
  `176.7390/176.9704/175.7037 tok/s`；candidate 相对 baseline 仅 `+0.1309%`。
- 维护版 comparator 返回 `failed`，唯一 issue 为
  `output_throughput: primary improvement below threshold`；`changed_paths` 精确为
  `[/plugin_sha256]`，所有延迟/总吞吐 guard 未触发。
- 比较结果：
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/op014-d128-same-device-abr-comparison-02.json`，
  SHA-256 `05f8dd6a800becf1e198e3e2ec0613c9103c40a04221ed2f9747a28fc6bd20f3`。
- 回退后 Plugin 文件 SHA-256 恢复为
  `3ae84180f7b5f4d70886c98f1d1afcf2255f8f7223a110397ec4894cf81a9a59`，
  service56 保持 healthy。

## 审查边界

当前表达式在现有 callsite 语义上正确，但若未来因更大端到端收益重开，
应改为直接从 `query_lens_cpu.sum()` 或权威 prefix-sum metadata 取得
`output_size`，并补 spec/plain decode/prefill/zero-padding 交错、pure-spec/no-spec
bypass 以及 graph + 2 replay 单测。当前不为 +0.13% 收益继续投入。
