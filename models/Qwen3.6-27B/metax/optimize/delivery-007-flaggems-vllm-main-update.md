# delivery-007-flaggems-vllm-main-update

User requests updating FlagGems-vllm in optimization container. Official defaultmain pinnedde2298be,8commits after29e80363. Current version0.3.0.dev1 normalwheel, private original6ea,5patchedfiles. Upstream delta43files does not touch those5files; applying trackedpatch cleanly plus retained untrackedWY gives exactly the same patched bytes, so no new operator algorithm/tile/precision changes are introduced by the local carry. No reverted/unpromoted candidate added.

This is package maintenance/rebase, not new operator development or performance acceptance. Repository AGENTS/workflow read; existing hardware/correctness evidence remains historical, not a fresh gate. No new kernel/performance work or torch fallback added; retain original .002/.02 semantics. Build normalwheel no-index/no-deps/no-build-isolation from private staged copy, validate every packaged Python/YAML file and public APIs. Before installation, run relevant existing CPU/mocked PluginGDN/MoE interfaces plus upstreamCPU optional-TLE guards, explicitly excluding GPU execution. Back up existing install and metadata; failure after install restores exact files.

New private source `/workspace/FlagGems-vllm-main-20261015-de2298b`, old source untouched. Current running model retains loaded old code until user restart; no automatic service restart, graph/GPQA/performance/model request. Package release label remains upstream0.3.0.dev1; version distinction recorded by sourcecommit+localpatch SHA. Sourcearchive `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/delivery007-20261015-fgvllm-main-de2298b-source.tar.gz` SHA `35c3f5e075a7c05a33f754ef4ff9e1441cd054c94c4ea35ea7b3bfabfe50fbde`. Stateprepared.

Saved command `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/delivery007-20261015-fgvllm-main-de2298b.py` SHA `404be2d268ebfd11cf86b77172b33b9d2bd4ea2218fd6bc7a475e28f9c0c8dac`; clean private build/candidate validation before replacing installedwheel. Test contracts use transient sys.path only, no persistent PYTHONPATH; new source folder never overwrites original private repo. Capture focused test collection first, then77PluginCPU contracts and upstreamTLECPU guards with GPUtests deselected. Versionlabel unchanged is an upstream fact, commit records actual update.

## 完成结果

优化容器 `qwen36-27b-fa-opt-20261012` 已安装官方 main `de2298be3459eeb94a3cf96a0c538a0a161ca954` 加原有5处 MetaX 补丁。新源码路径如上，Python 源码 SHA256 为 `cb45b31de3637f049bf621c81d77563f1362efb0dffb6a37fd04317177d07482`。FP32 GDN prefill、GDN recurrent 状态保护及原 Flash Attention 修复文件与更新前逐字节一致，没有加入已回退的 OP010 候选。

通过77项 Plugin CPU/模拟接口测试、34项上游 TLE CPU 测试（2项 GPU 测试明确排除）。安装后在无 PYTHONPATH 的新解释器中核对385个源码/配置文件、11个公共 API 和5个 MetaX 模块的实际导入路径及 SHA，全部通过。实际导入目录为 `/opt/conda/lib/python3.12/site-packages/flaggems_vllm`；依赖版本不变。

最终回执为远端案例目录 `results/delivery007-20261015-fgvllm-main-de2298b-receipt.json`，SHA256 `a9ae31aae27b430d8334dfca37a0a317cfc6a0db923b182be0794877ca522610`。对应 `logs/delivery007-20261015-fgvllm-main-de2298b-{plugin-contracts,tle-cpu}.log` 保存原生测试结果。安装 wheel SHA256 `f9dd37f7f232a7082515d201574283850fc8e506116675f99b0b6dbe71c649c3`；原安装完整备份位于 `commands/delivery007-20261015-fgvllm-main-de2298b/previous-install.tar.gz`，SHA256 `e8aa28f1ae2ce96e762c596a925f626c39bc8cb4cc22a0a65c53f0178ea2c2fa`，原源码目录保留。

安装后只读复核用户现役实例 `qwen36-addgdn:832568:1792052263.08` 仍运行，Plugin HEAD 为 `b8f2734` 且工作区干净。本次不重启服务，不修改用户启动脚本、白名单、缓存、vLLM、FlagGems、模型权重或源8002。新安装在新进程启动后生效；本次未执行 GPU 数值、graph、GPQA 或性能测试，不复用历史 gate 为新源码背书。上游包版本标记仍为 `0.3.0.dev1`，应使用 commit 和补丁 SHA 区分此次更新。

2026-10-15 用户询问 `/workspace/FlagGems-vllm` 的 git status 为何没有 GDN 修改。只读复核优化容器：该目录 HEAD 为 `4ea1b95b80efa2012fc5d82365f38a03ed691f09`，确实仅有历史 FA 两文件修改和两项测试文件，不是 delivery007 的安装源码。新私有目录仍为 de2298b 加5文件补丁；新目录、原 GDN 私有目录和 site-packages 安装包中的 gdn_chunk.py、gdn_wy.py、fused_recurrent.py 三文件 SHA 完全一致，匹配本次回执。新解释器在 `/tmp`、无 PYTHONPATH 时解析到 site-packages。源容器 qwen3.6-27B 当前未运行，未启动或修改它；此结论明确针对优化容器。
