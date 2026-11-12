# fix-007-int8-large-stride

## 结果与保留范围

通用 MoE 的大 stride INT8 非法访问已修复并完成安装后回归，最终独立审计通过。当前保留 main `208ab5802fc9a3ea5458481f4a92b7bff330e283` 的通用 MoE，加仅涉及三个量化 kernel 的寻址表达式修复。MetaX MoE 保持上一轮已同步的主线版本，PR #1069 和其他推理配置保持。

- 通用文件 SHA256：`4434453dc5eab0b2f3a9f8f80c2143f5e2b60bbfc891dc5713ea32e1f7f91146`。
- MetaX 文件仍为：`9de7b6eb0c366da625cb291b3be37d1fda01e8b9c346d10fb0924c12f0541746`。
- PR1069 后端仍为：`0f3f4eeb160032a6832e0ac214e947bb9fe435570f4de22eb1791f63d4befbb4`。
- 相对本轮开始，仅通用 `ops/fused_moe.py`、主线原测试文件和新增 `tests/test_fused_moe_large_strides.py` 三个文件变化。没有整体切换仓库、升级编译器/依赖或修改 Plugin。

## 定位与修复机制

发现方式与模型影响范围：主线测试直接 `importlib.import_module("flaggems_vllm.ops.fused_moe")`，绕过厂商分发，调用通用INT8 helper的合成大stride用例，不能据此认定Qwen3-VL模型命中过该路径。公开MoE入口的实际算子回归确认 `flaggems_vllm.fused_experts_impl` 指向 `_metax/ops/fused_moe.py`；该厂商文件自包含、有自己的量化逻辑，没有导入这次修复的通用INT8 helper。本次BF16/FP16非量化回归不进入该INT8 helper。MetaX仍复用独立的共享alignment等辅助算子，这与通用MoE量化实现是不同路径。此次只读取证也未发现Plugin直接导入 `flaggems_vllm.ops.fused_moe`；没有额外启动模型或采集在线模型trace，不将通用测试失败作为模型故障证据。

同一 C550、相同输入 `[3,384]`、BF16、元素 stride `2**30`，链式 `base + row_offset + col_offset` 的读取探针稳定非法访问；先计算完整整数偏移，再执行一次 `base + offsets` 的版本逐位正确，显式64位字节地址及逐行重定位原量化 kernel 的对照也通过。

原主线已经把 row/cols 转为 int64，TTIR/LLVM 中也保留64位计算，因此修复不是补一个缺失的 int64 cast。证据确认的是当前编译路径对链式大偏移指针表达式的错误处理；具体更低层编译 pass 尚未定位，不能外推全部 MetaX/编译器版本。

仅修改 `_int8_quantize_per_token_kernel`、`_int8_quantize_per_token_wide_kernel`、`_swigluoai_quantize_per_token_kernel`：先合并元素偏移，再加基址；相关输出寻址同样归并。量化/激活公式、FP32累加、可观察的半精度舍入、NaN处理、mask、tile、warp、参数及 wrapper 均保持主线原样。无额外 contiguous copy、逐行生产 fallback、汇编或运行后跨后端重试。

## 正确性与 graph

1. 私有候选先验证后同步：原主线48项测试逐字保留，新增14项行/列大stride、非零storage offset、单/双pass、BF16/FP16/FP32及OAI输入/输出布局测试，共62 passed，0 skipped；新增42次变化输入graph replay通过。
2. 实际安装路径：同样62项通过；独立MetaX公开算子8组（E128/H2048/I384/topk8，BF16/FP16 × M1/8/65/545）新旧逐位一致、24次变化输入replay通过，`out`/workspace、`inplace`、输入及默认RNG守护通过。
3. PR1069：91项测试通过，包含18次组件变化输入replay；真实Plugin调用另18次变化输入replay通过，接口、能力fallback、幂等和执行错误不重试保持。
4. 审计恢复后复核：相同源码重新安装后，原失败用例及新增14项共15项再次通过，新增42次变化输入replay通过。没有更换候选或修改断言来获取通过。
5. Black/isort/flake8按目标仓库配置检查通过。没有启动模型或运行模型精度、端到端性能；结果只属于算子与实际调用graph回归，不签发模型gate，也不解释历史GPQA分数。

## 两项验证工具问题

- 新增OAI测试最初把原生sigmoid当作逐位参考，BF16一个值相差约`9.3e-10`。8组对照证明原版、修复版和原有独立未融合激活输出/q/scale全部逐位相同，差异为原有FP32超越函数近半精度舍入中点的现象。新测试改用主线既有测试相同的独立未融合激活参考，目标激活/q/scale仍为零容差；另检查独立FP64公式的存储精度边界。原48项测试没有修改或跳过，原失败结果保留。
- 安装后所有数值/graph测试通过，但审计误把`accuracy_result.json`归为配置，触发了精确回滚。只读检查确认它由`tests/conftest.py`更新、生产源码引用为0，是唯一非源码差异；其余111项配置精确不变。保留原失败/回滚回执，归档报告前后内容；仅对这一已证实测试产物更正分类，重新安装相同已验证字节并复验15项。没有排除其他JSON或放宽真实配置门禁。

## 证据与回退

远端根：`/public-flash/jinghao/qwen3-VL/20261104-qwen3vl-mx59-topk-topp-pr/moe007`。

- `commands/`：所有执行前冻结的脚本、契约、原主线与修复源码、最小补丁；主线原测试字节校验不变。
- `results/address-probe.json`、`results/oai-baseline-audit.json`：地址表达式分离及原版数值语义对照。
- `results/private-completed-v2.json`、`results/installed-moe.xml`、`results/topk.xml`、`results/reapplied-stride.xml`：私有、安装路径及恢复后验证。
- `results/config-audit-incident-resolved.json`、`results/pytest-report-*.json`：测试报告分类纠正及完整产物，不覆盖先前失败。
- `results/completed.json`：最终同步回执；`backups/deploy-source-files.json`：本轮原文件备份，回退仅限本次三文件并受SHA约束，不reset其他用户代码。

下列为执行时冻结与诊断记录；后续状态以最终回执及独立审计为准。

User authorizes localizing/fixing generic MoE INT8 large-stride illegal access; preserve PR1069 and all config; validate correctness/graph before deployment.

Host/container: mx-59/qwen3vl; recheck no model/GPU0 idle, private workspace, current identity. Remote root: /public-flash/jinghao/qwen3-VL/20261104-qwen3vl-mx59-topk-topp-pr/moe007.

Known failure: main208ab quant rows3/K384/BF16/stride2**30; native fixture/reference passed; TTIR/LLVM offsets already64-bit. Only MetaX file is main; generic original retained.

Next: finite standalone address-reading probes, comparing chained addptr/combined offsets/explicit64-bit byte addresses/per-row bases. No compiler/dependency/config changes or Torch fallback/skipped tests. Candidates stay private until validated. Final scope: all48 upstream tests; affected stride/dtype/storageoffset matrix and changed-input graph; existing MetaX/PR1069 guards.

Mode: minimal-regression; no model service/start/formal eval/performance. Failure leaves verified source unchanged.

Command address_probe.py SHA256 e92a782e93811cf276f1bc7ac99bb3cb9401a10b7c0ce45b80672b0a9a2444c4; bounded4roles/6launches; archived remote before execution.

Command launch_address.py SHA256 bdc235a1a90fabffe6854b926fa457fa288cd3829ab95138c95eaf4c48d159a9; bounded4roles/6launches; archived remote before execution.

Private validation command generic-fixed.py SHA256 4434453dc5eab0b2f3a9f8f80c2143f5e2b60bbfc891dc5713ea32e1f7f91146. 48 unchanged upstream +14 new graph tests/42 replays, no production write; config YAML copied byte-exact to mirror relative layout.

Private validation command private_validate.py SHA256 99c003c8d5552bdcdf53d5fb3840d34ad89b025e21b8b41bef936b472384f44e. 48 unchanged upstream +14 new graph tests/42 replays, no production write; config YAML copied byte-exact to mirror relative layout.

Private validation command test_fused_moe_large_strides.py SHA256 cff1cd90f33d315332566bb7f77c776807b3ffae4b92702a95e96229cf9e6dc8. 48 unchanged upstream +14 new graph tests/42 replays, no production write; config YAML copied byte-exact to mirror relative layout.

Private validation command launch_private_validate.py SHA256 26574a25d6794ffd8786e077d9c006fb0efe517fa5f01767d5c2dffe188066f1. 48 unchanged upstream +14 new graph tests/42 replays, no production write; config YAML copied byte-exact to mirror relative layout.

CPU preflight incident: production fused_moe_config.yaml is absent (not a changed config); initial launcher assumed present and stopped locally before SSH/GPU. Corrected to enforce absence in both production/private module, or byte parity if present. New launcher SHA256 b18a519b38d0936e3cac3086b06dd8121f23ebf0f864bafb102f78f4f3c7307b.

First private validation:48 upstream+12quant stride graph+FP16 OAI passed; BF16 OAI native sigmoid differs1ULP (9.313e-10). No production update. Next bounded audit: original vs fixed and separate activation on8contiguous fixtures+FP64; isolated original standalone OAI large-stride call. No tolerance change before proof.
oai_audit.py SHA256 4344b6207b33b3b3769129f954484d7c7ed9a5eea4f8c8ee8f7e9933231cd91d
launch_oai_audit.py SHA256 ba65d4b56f6e986d37780ffa3c17e2ebd60ad090729db0bbb1e8346798bedc87

OAI proof: original/fixed quant activation+quant+scale and independent unfused activation exact on8fixtures. Seed61 BF16 native sigmoid differs1ULP also in original: gate-11.6875/up11.5, baseline=-2.1513551473617554e-7/native=-2.1420419216156006e-7/FP64=-2.1467006562014646e-7. Original unfused large-stride activation passes, unchanged. New OAI test reference corrected to existing independent unfused activation (same reference as upstream test_quant_and_oai_quant), still strict0/0 target activation/q/scales; add independent FP64 formula check within one storage ULP. Original48 tests unchanged.
New tests SHA256 f71f5fa44e307a813a9893ae909f92b6ad0c6ddb0445c4c59133e393bb95d744; candidate unchanged4434453d.

Private-v2 completed:62/62, no skips,42 changed-input replays. Deploy only after this receipt and exact candidate SHA guard. Install main generic+pointer grouping plus original48 tests and added14 tests. Preserve exact mainMetaX+PR1069+112configs/Plugin/FG/container settings. Installed tests re-run plus publicMetaX8cases24replays/PR1069 91tests+18operator+18actualPlugin replays. No model/dep/flag changes.
deploy_controller.py SHA256 33731e4aa0de0d32306fae3d36ded6e9feacf2484d0ad553f5311cbfc0c4920b
deploy-payload.json SHA256 974eb03c9452b44426ace2e40c48bd1f14c44c5c41bc53083c9858f0348b1c1e
moe_regression.py SHA256 24a4773b98ec849debd53d351b70e7cef45ebd2f87fd57cb76ec55cc8f4e2a4a
topk_hook.py SHA256 b3c4e2f5c5b53987042c4c77904ea5396818fdf8ca369028cf5288ab3372c6a1
launch_deploy.py SHA256 3491c61c6519592e94b29a7c8e06098db01c8022130f48acc389d90694954143

Independent final audit after controller completion: source/112config/PR1069/MetaX/container identity, original48tests and only3function AST diffs vs main. Command SHA256 f9d8d812714a15b8e3cf983dbac169e1dcd73269a43e1c11f1de164ebe6c766b.

Postvalidation collector incident: all62MoE+91Topk and publicMetaX/caller graphs passed, then source audit classified generated accuracy_result.json as config and auto-rolled-back. Read-only proof: only thisJSON changed,111 realconfig assets exact; tests/conftest.py writes REPORT_FILE, production source references0. Preserve report/failed receipt. Reapply exact validated source+15 original-failure/stridegraph rebind tests; no broad numerical rerun or code/tolerance change. Single explicit artifact exception, not excluding arbitraryJSON.
Recovery SHA256 ce488835b7a62359a39102dd3c8a7b6ebd9c5a99fcb42aae1e77f6e66928be0d

Final audit updated before upload: enforce111actualconfig hashes, sole explicit pytest report artifact difference archived. No generic JSON exclusion. New final-audit SHA256 d2cb295a2b888c5be91c57ff0a1b325d49fdb9fe270cfc5300b812c2d2962370.

## 最终独立审计与复盘

`results/final-audit.json` SHA256 `e29ebbc4e382732ca58636c765337b53ff5e0d937504b70df5c278d4894583be`，与同步回执关联。主线原48项测试字节精确不变，仅三个指定kernel函数的AST与原主线不同。111项真实配置、启动脚本/容器Config/HostConfig、Plugin/FlagGems及PR1069均一致；测试报告更新单独归档。目标容器无模型进程，全部测试进程退出。

规划复盘 `plan-moe-stride-repair-20261104`：006的部分同步/回滚与本轮失败参照、采集器误分类均保留；当前组合代码已通过算子/graph回归。Prefill、Decode、Mixed没有新模型证据，不能把既有TopK组件加速与本修复相加或推断E2E收益。当前请求已完成，无待运行GPU任务；只有新的用户模型验收/性能任务或新正确性失败才触发下一轮。
