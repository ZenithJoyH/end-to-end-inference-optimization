# Qwen3.6-35B / mx-104 Plugin 采样导入生命周期修复

2026-10-22，Asia/Shanghai。目标为`mx-104` / `qwen3.6-35B-verify` / `/data/Qwen3.6-35B-A3B-nomtp`。用户要求在Plugin中修好采样导入顺序、保持现有采样优化逻辑，并验证真实服务使用优化采样器。

**修复已完成并保留。** Plugin仍基于`release/0.2@7cb559947`，只改3个生产生命周期文件，新增1个导入顺序集成测试。6项导入回归、25项数值/边界检查以及实际TP2服务验证通过。vLLM源码、两套Gems和模型config未改变。

## 问题与修复

原平台补丁在vLLM采样模块尚未初始化完成时继承`TopKTopPSampler`，可能形成循环导入。后续只替换定义模块，也不能更新消费者此前保存的`from-import`类别名。

在Plugin的MetaX patch和ModelRunnerFL初始化边界延迟安装采样补丁，并刷新精确清单内已加载的消费者符号。首版6项导入回归得到4失败、2通过，进一步定位到`gdn_linear_attn → layernorm → 部分初始化的vllm._aiter_ops`循环；第二版将GDN注册同样延迟到模型构造前，GDN实现保持不变。

生产改动位于`patches/__init__.py`、`patches/topk_topp_sampler.py`、`worker/model_runner.py`；新增`tests/integration/test_metax_sampler_lifecycle.py`。原采样guards/helper/方法7项AST一致，shortlist/counting kernel字节一致。`apply_patch()`按已知模块属性和`hasattr`更新，不承诺保护这些精确位置上的第三方override。

## 验证结果

| 项目 | 结果 |
|---|---|
| 第二版新鲜解释器导入顺序 | 6通过，0失败/错误/跳过；首版失败证据保留 |
| 独立GPU0采样回归 | 25/25：15对真实采样、9个guard边界、1组AST/内核保持 |
| 数值保持 | 同输入/seed的tokens相同，processed_logits/输入修改逐字节相同，generator末状态相同 |
| 实际服务 | TP2，GPU0/1，BF16；两worker都构造MetaXTopKTopPSampler，绑定Plugin forward_native，use_shortlist=true |
| GDN延迟注册 | 两worker各30个MacaGatedDeltaNetAttention实例 |
| C1与两轮C8 | 共17请求HTTP200且非空；C1答案2，C8真实shape[8,248320] |
| shortlist真实执行 | 两轮各252次成功调用，合计504次；含两个worker |
| graph | PIECEWISE和FULL capture日志各5/5；两个worker均有请求阶段成功replay，合计至少512次 |
| 源码完整性 | vLLM2176、FlagGems-vllm276、FlagGems2985个包文件未变；vLLM Git干净 |
| editable来源 | Plugin `/workspace/vllm-plugin-FL`，vLLM `/workspace/vllm`，FGV `/opt/FlagGems-vllm`，FG `/workspace/FlagGems` |
| 收尾 | 临时服务已停止、端口关闭、GPU无残留进程；容器继续运行，修复代码保留 |

临时观察器位于远端case外部`observer/sitecustomize.py`，未进入正式源。profile事件计数有每worker/phase/event/shape的128条记录上限，因此replay数是下界。C8使用ignore_eos与128-token上限维持采样cohort，length结束是预设诊断行为。观察器增加CPU开销，本轮不报告性能收益。

## 范围与交付

`minimal-regression=passed`，`pr_readiness=reviewable_target_verified`。这证明指定模型/容器的修复及服务路径；正式模型精度、正式性能、其他模型/平台硬件与绕开ModelRunnerFL生命周期的自定义runner未测。没有签发或复用精度gate，没有提交或推送。

临时服务的精确启动配置、身份和请求记录保存在远端launch manifest，不在本地固化瞬时PID。本轮按用户明确要求直接修复指定容器，未开展新的性能优化实验。

- [结构化状态](../../../models/qwen3.6-35b-a3b/metax/20261022-qwen36-35b-mx104-sampler-fix/optimize/state.yml)
- [实验完整记录](../../../models/qwen3.6-35b-a3b/metax/20261022-qwen36-35b-mx104-sampler-fix/optimize/sampler-import-001.md)
- [前序代码审计与editable迁移](../20261022-qwen36-35b-mx104-code-audit/README.md)

远端根：`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-sampler-fix`。

| 原生证据 | SHA256 |
|---|---|
| `service-001/verification.json` | `56c74b5a2834ad5b2a8fb043b5be07905c19082afaea71be29171d41c66d0f7e` |
| `numerical-regression.json` | `34deb691d54b7136a6f09a25d57e517c41ed7501342f0fe9e0b92a9fc66d6dcc` |
| `import-tests-v2.xml` | `5fba5e100215dc958eff19cf2fe89feffeb3dd2dde3c9cbce0a5ef3a4d968ede` |
| `final-source-audit.json` | `8b1e2022e851d118555b819d1918d40b722cdbdb20c79351b5036a01e983d7da` |
| `closeout.json` | `03d89228f2515c33619c07f947f94e19b3f89ccfea88fa4c3ff3588c2e835e17` |

增量补丁为`sampler-lifecycle-only.patch`（SHA `4daa8bc041b2944fe608271ac3b9ca56826c333d3bc59c2f96219263087c6c80`）。原文件在`before/`，保护性回退脚本`commands/rollback-sampler-fix.py`（SHA `9e32e8b256fabe0da07a5fea3d33929e7b3175640cd1ea3c90baa9469f210610`）已生成、未执行；恢复前核对候选SHA，避免覆盖后续改动。
