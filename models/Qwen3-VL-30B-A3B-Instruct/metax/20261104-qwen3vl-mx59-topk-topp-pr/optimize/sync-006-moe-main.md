# sync-006-moe-main 同步容器MoE到主线

- 状态：MetaX 文件同步、回归及最终独立审计完成；通用 MoE 升级阻塞，保留旧版。用户2026-11-04明确授权mx-59/qwen3vl的fused_moe同步主线，保留PR1069和其他配置。
- 固定主线：208ab5802fc9a3ea5458481f4a92b7bff330e283；只同步通用/MetaX fused_moe与配套tests，不git pull/reset整个仓库，不更新依赖、配置表、Plugin或模型服务。
- 验证模式：minimal-regression，保持当前无模型服务状态；主线MoE单测、Qwen-VL E128/TP2几何的实际MetaX公开算子及graph变化输入回放、PR1069完整组件与实际调用graph护栏。没有模型服务则不擅自启动或声称全模型精度/graph gate。
- 容器源码写入前再次核验私有workspace、模型空闲、GPU0空闲及SHA，保存原始备份。失败恢复本次文件，保留所有失败证据。
- 外部产物：/public-flash/jinghao/qwen3-VL/20261104-qwen3vl-mx59-topk-topp-pr/moe006；本机临时目录/tmp/qwen3vl-topk-pr-20261104/moe006。命令、配置、测试范围和SHA执行前冻结。

## Failure and narrowed safe execution

Exact main generic/MetaX/test upgrade failed at test_quant_offsets_promote_past_int32, and all three files were restored. Isolated fixture and Torch reference pass; generic-main quant kernel fails immediately on synchronize. TTIR/LLVM address offsets are 64-bit; lower-level cause is unconfirmed. No compiler/config workaround applied.

Next bounded execution: only exact-main MetaX fused_moe file, with generic/tests kept at original bytes. This is a partial synchronization; generic-main upgrade remains blocked. Commands and contract: /public-flash/jinghao/qwen3-VL/20261104-qwen3vl-mx59-topk-topp-pr/moe006/metax-only-v2/commands/. Existing MoE suite, actual QwenVL geometry and graph, PR1069 tests/caller guard must pass before retention.

### MetaX v2 harness incident
25 existing MoE tests passed; BF16 M1 old/new and 3 graph replays passed. Test harness supplied out without workspace13/workspace2, triggering the existing API guard; source was rolled back. v3 passes all three buffers, with extents derived from the actual implementation. AST/compilation checks passed before upload. No operator code or assertions changed. v3 execution contract and SHA: moe006/metax-only-v3/commands/execution-contract.json.

## 当前保留范围与验证

只保留 `/workspace/FlagGems-vllm/src/flaggems_vllm/runtime/backend/_metax/ops/fused_moe.py`，精确对应 main `208ab5802fc9a3ea5458481f4a92b7bff330e283`，SHA256 `9de7b6eb0c366da625cb291b3be37d1fda01e8b9c346d10fb0924c12f0541746`。Qwen 与 Qwen-VL 的 TP2 shape/config helper 分开，计算 kernel 本身与更新前相同。通用 `ops/fused_moe.py` 与原测试文件仍为更新前字节；没有加入兼容补丁。

- 现有 MoE 单测：25 passed。
- 真实 MetaX 公开算子：E128/H2048/I384/topk8，BF16/FP16 × M1/8/65/545，8 组新旧逐位一致；8 次 capture、24 次变化输入 graph replay 全部通过。`out`/workspace 与 `inplace` 各两组通过，输入及默认 RNG 保持。
- PR1069：91 项测试通过（含18次组件变化输入 graph replay）；真实 Plugin 调用另外18次变化输入 replay 通过，接口、fallback、幂等和错误不重试护栏保持。
- 控制器回执：`moe006/metax-only-v3/results/completed.json`。仅目标 MetaX 文件发生变化，Plugin、FlagGems、PR1069 源码及104项配置文件、依赖 revision、容器配置保持。没有启动模型、改启动脚本、运行全量精度或性能。

## 未完成部分

整套主线通用 MoE 未保留。主线 `test_quant_offsets_promote_past_int32` 在当前环境发生非法显存访问，三个文件自动回滚；隔离探针确认 4GiB BF16 strided fixture 与原生 Torch 参考均通过，只有主线量化 kernel 同步时报错。编译 TTIR/LLVM 中相关地址索引已为 int64，尚未定位到更低层原因，不能直接宣称厂商编译器 bug。失败、回滚与独立探针保留于 `moe006/results/`、`moe006/logs/` 和 `moe006/results/offset-ir/`。此问题不是当前 BF16 模型分数根因证明。

后续若要求通用文件也精确同步主线，必须先解决该边界回归；不能跳过失败测试、改依赖/编译参数或把 MetaX 局部通过写成整体通过。当前没有继续 GPU 测试或生产变更计划。

## 独立最终审计

`moe006/metax-only-v3/results/final-audit.json` SHA256 `29e9809783abdf1446295413d9355e8f0cf710839fcbaae3890f81321debb4df`。相对本次操作前，仅MetaX fused_moe一个Python文件变化；Plugin/FlagGems全部Python源码、PR1069、104项配置、启动脚本、容器Config/HostConfig一致。目标容器仍只有shell、无模型服务。通用部分状态为incomplete，不能整体签通过或生成模型精度gate。

## 后续修复

本记录的原主线失败与回滚不改称通过。后续[fix-007](fix-007-int8-large-stride.md)已用三个量化kernel的整数偏移归并修复，在原48项+新增14项和graph验证后同步；当前通用文件为主线加该补丁，007为最新状态。
