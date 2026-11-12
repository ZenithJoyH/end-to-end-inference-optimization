# plugin-gdn-lazy-pr-001

最新状态（2026-11-06）：用户要求暂时撤回，PR #699 已于05:30:38Z关闭、未合并，head d2ce43f6与分支保留。已在 [撤回说明](https://github.com/flagos-ai/vllm-plugin-FL/pull/699#issuecomment-6677752493) 说明正常 CLI/当前服务不依赖该补丁；特定导入顺序下的问题证据保留。未修改容器或服务，未操作 #702。下文提交/open 为历史事实。

用户授权：2026-11-05 将 GDN 延迟注册和循环导入修复单独提交 vllm-plugin-FL PR。

范围：从 upstream main `087f9b6e89d94f54509fba85ed3d5a7afff96c0f` 干净克隆构建补丁，不复制容器整体差异。仅移除 MetaX patches 包的 GDN 提前导入，在 ModelRunnerFL 初始化且模型构造之前按 vendor_name=metax 注册。GDN 计算实现、其他 patch、MoE、采样、KV、启动配置均不改。无远端/容器/服务操作、无 GPU/模型请求。

验证：5 项 CPU 生命周期测试通过；同一测试在未修复主线上因 GDN 依赖未就绪失败（5 errors）。测试执行生产包和生产注册语句，native 依赖使用替身，不代替完整 vLLM 导入、GPU 启动、graph 或模型精度验证。提交检查全部适用项通过；symlink/shellcheck 无适用文件。

文件与 SHA256：
- patches/__init__.py: cb3b8156c1b5a982654f37a565f0537271788a69d16415017498bdc209b72811
- worker/model_runner.py: b9273f8298afac38a22974bb41a49a97652734199efa665cc24ec7eca6bc8294
- tests/unit_tests/test_metax_gdn_registration.py: b2836ca8b38ee7ccff7813bdc5398ff82b51238eb225e9c817efcea3ba803b8e

本地临时克隆：/private/tmp/vllm-fl-gdn-lazy-pr-20261105-001。现有容器保持不变；公共 PR 不上传内部评测数据。发布状态：已提交正式 PR [#699](https://github.com/flagos-ai/vllm-plugin-FL/pull/699)，open、非 draft。

分支：`ZenithJoyH:fix/metax-gdn-deferred-registration-20261105-001`；commit `e4db4a45b6753078d48928b71e173f05d78709db`，父提交为上述 upstream main。GitHub 提交与 PR 文件清单复核为恰好三个文件（两个生产位置、一个相关回归测试），共 +187/-1。无本地案例记录或内部数据进入 PR。

## 用户纠正目标版本：release/0.2

2026-11-05 用户指出应提交对应 vLLM 0.20.2 的版本。只读确认 upstream release/0.2 `6e11d0ab687247fdf4347a52788ec4f2baf57c79` 的 pyproject 固定 vllm[audio]==0.20.2，MetaX Docker/CI 同版本。准备将现有 PR #699 基准和 head 重新绑定该 release，不新建重复 PR。旧 main 提交 e4db4a45 保留为历史，不带进 release diff。

在该 release 的干净克隆重新生成同样两处生产改动，测试 native 路径采用该版本 gdn_linear_attn，而非 main 的 gdn.base。5 测试通过，未修改 release 基线5项导入错误；git diff --check 通过。全量 pre-commit 首次指出 model_runner 原有5行尾部空白；为严格限定本次改动，将这些原有行原样保留，确认新增尾空白为0，并显式 SKIP=trailing-whitespace 后其余适用 hooks 全通过；在 PR 如实注明。未执行 GPU/模型或容器操作。

## 真实环境导入复核（用户追加要求，执行前）

用户要求先验证原代码真实循环导入，而非仅模拟依赖未初始化。暂停 PR base/head 更新（release commit d2ce43f6 已生成，但未更新分支/PR）。目标 mx-59/qwen36-35b 已确认 vLLM0.20.2+empty/Torch2.8 MetaX，现有 Plugin 自带 GDN 延迟注册。将在新鲜子解释器中用仅进程内源码 loader 加回 GDN 原位置导入，对照未改的当前包；全部依赖、GDN模块、导入链真实加载，无依赖替身，不改容器源文件/服务、不加载模型/发请求。先做有限4个入口×2种注册模式，保存每次完整真实堆栈与源码 SHA。该对照仅证明当前栈中 GDN 单变量影响；另须区分 release/0.2 完整源码（原采样器可能独立触发循环），不能将当前栈替代整个 release 栈。

真实验证已归档：gdn-real-import-20261105-001（当前容器单变量8进程）。首入口 vllm._aiter_ops 提前 GDN 模式，实际触发 rocm_aiter_ops partially initialized module，外层 PlatformFL 捕获后仍 exit0，GDN未加载；判定需同时检查日志和注册，不能只凭退出码。

release验证准备001的scp传输失败，driver输出均为缺快照(no JSON)，0有效导入；原目录保留。002仅成功传输干净 git archive 快照（SHA2568ba317f74b18cda3b46197a0b5cf55dd68b4924e9b2545a8ee2f8bfb8112cd32），脚本字符串预检发现转义问题未执行。003使用002同一只读快照，修正观察脚本；本地已断言其生效的package/runner字节与release PR候选完全一致，开始两个入口×两种时机真实依赖对照。所有准备/观察失败不作为模型或数值失败。

## 最终重新绑定与真实验证结果

PR #699 已基于 `release/0.2@6e11d0ab687247fdf4347a52788ec4f2baf57c79` 重新提交：head `d2ce43f6fd7133f321b6abd033a0159552df498e`，1 commit，3 files，+186/-1。GitHub复核 base=release/0.2、head匹配且mergeable=true；不包含main其他历史。旧main提交仅历史记录。

真实依赖验证：当前容器的4个fresh入口（_aiter_ops/layernorm/sampler/model_runner）加回提前GDN导入均出现循环警告、GDN未注册；原延迟版本4入口无此警告。原生exit均0，证明不能以exit0宣称注册成功。source-before/after相同；summary SHA256 `ee445cc0df58bb799a73b4cb42f0e2be7913b1b4886e2d731271705aadea6c44`。

干净release快照003中的layernorm入口：原包第23行导入GDN，native GDN第33行回读尚未初始化的RMSNormGated，真实ImportError明确复现；延迟GDN后同入口无该异常，后续真实导入定义/注册MacaGatedDeltaNetAttention成功。_aiter_ops-first入口仍先被独立旧sampler循环阻塞，两种GDN模式都有该警告；不扩大本PR到采样。summary SHA256 `0aabb862f7861bee4479f5ac9c36c6b49ea2ffc17926c5d7ba9e3c7dcacf25b6`。所有依赖真实，无单元依赖替身；loader仅变更指定生命周期字节，未落盘更改部署源码。GPU模型构造/graph/精度未运行。PR说明已据此修订，明确捕获异常后的静默注册缺失及采样边界。

release提交文件SHA256：patches/__init__.py `2c5f1cf0b28e3a6c6e8316f2555199aa57e8655c9b3e93f55ea36dbf2f25ac30`；worker/model_runner.py `30f6c4908bb62e38a84c576f8179364e834b2047a3170f25a9acde24530c892e`；unit test `873a1ecb4c17fd4ec8048e2e00941f44b7251859a4c1f212b5789b00d698544e`。

补充004真实入口 vllm.v1.sample.ops.topk_topp_sampler：原包第23行进入GDN→nativeGDN→layernorm→_aiter_ops，真实rocm_aiter_ops部分初始化错误；延迟GDN后无patch异常，真实GDN注册成功。source前后相同，summary SHA256 `d13769404e00e08146fabd0b91a46898677006b3b8061bc264bbaf7c9ef05203`。全部有限导入进程已自然结束，未产生服务/模型请求。

## CI pending 检查

用户询问pending。GitHub原生status明确为license/cla=pending，description=Contributor License Agreement is not signed yet，入口 https://cla-assistant.io/flagos-ai/vllm-plugin-FL?pullRequest=699 ，需用户本人签署，不代签。初查head d2ce43f6只有labeler完成，无正式CI运行。release/0.2工作流只监听opened/synchronize/reopened/ready_for_review，不监听edited；head推送发生在base从main切release之前，之后仅edited未触发。已保持head/base不变，close→reopen现有PR重触发。新CI https://github.com/flagos-ai/vllm-plugin-FL/actions/runs/41952920045 ，原生status=pending、jobs=[]，pending_deployments=[]；当前仅确认尚未创建任务，不猜runner故障或审批原因，无测试失败证据。PR仍open、base=release/0.2、head=d2ce43f6。

## CI failure investigation

PR699 head d2ce43f6: job 127001803535 (test-kunlunxin / unit) failed in Check device availability, before Install project and Run unit tests (both skipped). Log: KL3 kernel exception error=721/status=299; torch.cuda.synchronize() raises CUDA error: wait for noc idle timeout after about20 minutes. Existing .github/scripts/kunlunxin/check.sh only imports torch, checks device count and creates a small ones tensor and synchronizes; it does not import the changed Plugin GDN module. Diagnosis: Kunlunxin device/runtime preflight failure, no evidence of a PR699 test regression; precise hardware cause needs runner-side investigation. No source changes, GPU reset, broad rerun or external comments made.

The report uploader also logs missing api_token after the device failure; workflow marks that uploader continue-on-error, so it is secondary and not the device failure cause. Lint/build plus Ascend/MUSA unit passed; MetaX unit was still queued at inspection, not claimed passed. Failed job: https://github.com/flagos-ai/vllm-plugin-FL/actions/runs/41952920045/job/127001803535 .

## Review response — 2026-11-06

User authorized responding to current review or adjusting the PR. Reviewer ceci3 asked why GDN registration is triggered in ModelRunner rather than OpManager. Checked current head d2ce43f6 and release implementation: this is the existing layer-class `register_oot` lifecycle, not a new kernel-dispatch entry; MetaX has no GDN OpManager entry/call bridge. Replied with the import-order rationale and scope boundary in [the original thread](https://github.com/flagos-ai/vllm-plugin-FL/pull/699#discussion_r4488418366). No code change or push was needed for this question; thread remains unresolved for reviewer confirmation.

All 3 PR file Git blob hashes matched the local verification copy. Re-ran `python3 tests/unit_tests/test_metax_gdn_registration.py -v`: 5 CPU tests passed; `git diff --check` passed. No GPU/model requests or container/service changes. These checks do not upgrade the existing hardware-validation boundary.

## 用户新容器反例核对 — 2026-11-06

用户在 mx-59/vllm0202-fl-release02-20261106 的正常服务未复现循环，已核实该成功路径成立：干净 release/0.2@6e11d0a，实际 vllm CLI 初始化/--help 成功且 GDN OOT 注册为 MacaGatedDeltaNetAttention，无 maca patches 循环警告。同一容器原始源码、相同服务环境中的新鲜解释器先导入 layernorm 或 sampler，仍分别出现 RMSNormGated / rocm_aiter_ops 部分初始化警告，入口返回时 GDN registry 为空；均 exit0。没有源码替身或 loader 改写，没有模型/服务操作。

因此 #699 仅能定位为“特定导入顺序下的 GDN 注册失败修复”，不能泛化为“未修复 release 正常 CLI 必然启动失败”，也不保证有精度/性能收益。详细对照和来源见 [gdn-user-container-audit-20261106-001](gdn-user-container-audit-20261106-001.md)。公共 PR 未改动。

后续用户明确要求如实反馈到 PR：已发布 [复核评论](https://github.com/flagos-ai/vllm-plugin-FL/pull/699#issuecomment-6677716331)，并在 PR 描述开头补充成功路径及 import-order-dependent 限定，保留原测试与验证边界。GitHub 读回确认评论正文成功；head仍d2ce43f6、base仍release/0.2，无代码推送或容器变更。
