# eng-069 图片／视频多模态源码审计

- 日期：2026-10-24；状态：源码分析完成，设备／模型验证 `not_run`，不签发多模态 gate。
- 分类：framework／operator 静态调用链诊断，不实施优化；阶段为视觉编码 Prefill 及其与语言模型的接入，不产生 Decode／Mixed 性能结果。
- 范围：PPU-07，`qwen3.8-flash-opt-ppu07-20261015`；三规范源码目录及该容器安装的 vLLM／Transformers。保留 BF16、op068 原始权重布局及现有算子修复。
- 用户边界：只分析源码，不解除暂停、不重启、不访问8035。实际未发 import、测试、推理、GPU、health／metrics 请求，未修改远端源码、配置、缓存或 monitor，未提交／推送。

## 优化方向与瓶颈依据

结论：**普通图片／视频的结构性主链路已经接通，但不能认定当前平头哥版本已经完成多模态适配与验收。** 主要缺口在视觉 Attention 的平台选择和实际 OOT 分发不一致；另有可选 encoder graph 与视频裁剪配置边界。没有源码依据要求重写整个视觉塔、为 patch embedding 新增 Conv3d kernel，或直接断言 head_dim=72 不受支持。

当前 `--language-model-only` 服务不会创建视觉塔，也会跳过视觉权重；文本成功不证明视觉算子能编译或图片／视频推理正确。已有 acc020 的176/198文本 GPQA gate 保留其原绑定与范围，不能外推多模态。

本轮仅从宿主机读取原 API 进程的 `/proc/<pid>/root` 源码，不进入暂停容器执行命令。开始只读 inspect 为 paused；收尾只读 inspect 已为 running／Paused=false，**本 Agent 未执行 pause/unpause，外部变化原因未知，也未重新暂停**。收尾“仍暂停”断言因此未通过，不能声称完整运行时前后冻结成立；下述结论绑定已核 SHA 的本地源码快照，不是运行中函数对象／kernel 命中证明。

## 源码链路：已有部分

源码位置以下以容器路径为准；行号对应本轮快照。

| 环节 | 核验结果与依据 |
|---|---|
| 模型与处理器注册 | `/opt/vllm-plugin-FL/vllm_fl/patches/qwen3_8_flash_next.py:133` 的架构映射和234起注册；`models/qwen3_8_flash_next/gpu/model.py:1191` 的 ProcessingInfo 及1196起 Qwen3VL processor／dummy inputs 注册齐全。 |
| 图片／视频输入 | 安装版 `vllm/model_executor/models/qwen3_vl.py:1248` 处理视频元数据、帧和时间戳；2106／2130起解析图片／视频 tensor，2159／2181起调用视觉塔并拆分各媒体 embedding。外层模型继承这些实现。 |
| 视觉塔与权重 | Plugin `model.py:1251` 在非 language-only 时构造 Qwen3_VisionTransformer；1384起 AutoWeightsLoader 与继承的 visual／language_model 前缀映射衔接。权重索引有333项 `model.visual.*` tensor，含当前视觉层 packed qkv／proj／MLP；只核索引，未读 tensor 数值。 |
| 合并与 PLE | `model.py:1208` 声明 requires_raw_input_tokens；1311起按 mask 合并视觉 embedding，1354起同时传原始 input_ids、inputs_embeds、positions 等进入语言模型。不是以视觉 embedding 覆盖掉 PLE 所需 token IDs。 |
| 三轴 MRoPE | 外层继承 Qwen3VL `get_mrope_input_positions`（安装版2571起），非 language-only 时不剥离 MRoPE 配置。内层 text class 的一维位置方法不能误当外层多模态实现。QSA indexer 有 MRoPE sections／interleaving 处理，cache 保存多轴 int64 position；仍需真实跨轴／chunked prefill 验证。 |
| 视觉 RoPE | Plugin worker 在构造模型前调用 `patch_oot_apply_rotary_emb`（worker.py:257）；attention/utils.py:140 将 ApplyRotaryEmb.forward_oot 接入 FL dispatch。FlagOS 实现支持3D／4D输入、cos形状及 partial tail，开关1时可调用 FlagGems-vllm。thead 默认优先 FlagOS、仍允许 fallback；本轮不是实际选中 backend 的证明。 |
| 视频 CPU 预处理 | video_preprocessor 与 Qwen3VLVideoProcessor 存在，OpenCV headless4.13.0.92／Pillow12.2.0包文件存在。未安装 av／decord／torchcodec 不等于视频一定不可用；本轮未导入解码器或验证具体编码格式。 |

实际视觉配置：hidden1152、27层、16 heads、head_dim72、patch=(2,16,16)、spatial_merge=2、输出2560匹配语言维度；TP8下通常每rank2 heads，MLP4304/8=538。deepstack indexes为空，本模型当前不走 deepstack。上述非典型 shape 是验证重点，不是已证实错误。

## 需要适配／修复与适用边界

### 1. 优先补齐平头哥视觉 Attention 的明确分发

静态证据：

- Plugin `platform.py:405–450` 声明视觉支持 TORCH_SDPA／FLASH_ATTN，默认依据通用 device capability 尝试选择 FA；仅昆仑芯有专门能力判断。
- `attention/utils.py:113–117` 仅在 `current_platform.is_cuda()` 时把 MMEncoderAttention.forward_oot 绑定到 forward_cuda；本 Plugin 的 is_cuda 仅对 NVIDIA 成立，平头哥没有对应绑定。
- vLLM `model_executor/custom_op.py:169,201` 的 OOT 默认落 forward_native；`layers/attention/mm_encoder_attention.py:700` 的 native 实际调用 SDPA。即使选择器返回 FLASH_ATTN，也不能据此认定 PPU 执行 FA；初始化还可能进行 FA 版本／依赖探测。

建议在现有平台／backend 边界补 PPU capability 与真实 forward 对接，让“选择结果、导入依赖、实际实现”一致。初期可明确使用 SDPA 作参考，再接已有 FlagGems／vendor 的非因果、变长视觉 Attention，不能直接复用语言解码 causal／KV-cache 路径。须核 BF16、D72、ragged cu_seqlens、多图／多帧、QKV stride 和数值；**尚无硬件证据证明某一具体 kernel 必须新增或重写。**

FlagGems 已注册 math／flash／efficient／fused overrideable 等 SDPA 下层，且存在 thead fused attention 实现；不能把上层 TorchSDPA 等同于全程 PyTorch math，也不能直接断言必然 O(S²)／OOM。如果实际选中 math，则其显式 score 矩阵才有平方内存风险。应先确认真实下层 dispatch，再决定替换范围。

### 2. 启用视觉 encoder graph 前必须消除 device→CPU 动态分段

vLLM `v1/attention/ops/vit_attn_wrappers.py:231` 对设备 cu_seqlens 差值 `.tolist()`，随后 Python split／循环／cat。Qwen3VL 视觉 metadata 将 cu_seqlens 放在设备上；因此当前 SDPA 路径包含 host 同步和数据依赖分段，不能据此认为 encoder 可完整 capture／replay。

优先方案是 graph-compatible 变长 Attention；或在 capture 外准备静态分段元数据，并明确各 token budget 的 padding／mask。**默认 `cudagraph_mm_encoder=False`（config/compilation.py:524）；这不是普通 eager 视觉编码必然失败，也不说明语言模型已有 FULL／PIECEWISE graph 失效。** 不应先开启 encoder graph 再用文本 replay 当通过证据。

### 3. 禁止当前模型未实现的正值视频 pruning 配置

Plugin `model.py:1213,1254` 声明不支持 multimodal pruning，并将实例 EVS 关闭、pruning_rate固定0；但继承的 processor 读取全局 multimodal_config.video_pruning_rate（Qwen3VL:1269），正值时减少视频占位 token（1339–1349及1460起）。模型端仍返回未裁剪视觉 embedding，存在 token／embedding 数量不一致路径。

建议在 Plugin 配置校验处对正值直接报清晰错误，保持普通视频不裁剪；完整实现 EVS／重算 MRoPE 是另一独立适配任务，当前无必要混入。默认 None／0 不触发本问题。`supports_multimodal_pruning=False` 只阻止 runner 某些 pruning 路径，不会自动让 processor 忽略全局正值配置。

### 4. 视频元数据健壮性与资源预算

安装版 `vllm/multimodal/video.py:614–633` 的帧数计算使用 original_fps 作除数；Qwen3VL:991–1054 的 timestamp 也依赖 fps。对异常0值缺少显式正数校验，建议在输入／视频元数据边界校验 finite positive fps、有效 frames_indices 与采样后帧数一致，并给出清晰错误。这是共有预处理健壮性问题，**不是平头哥独有 kernel 缺陷，也不是已发生的本轮视频事故**。

已有实现默认避免二次抽帧，并处理显式 num_frames 时 fps=None，不重复“修复”这些现成功能。后续应冻结图像分辨率／数量、视频 fps／max_frames／像素及 token 上限：当前模型的最大像素配置较大，不能把文本C64预算直接套到多帧视觉编码。CPU解码／H2D／vision encoder／语言 Prefill 应分别测量；本轮不估算吞吐或显存达标。

## 不需要凭猜测新增的修复

- Patch embedding 表面是 Conv3dLayer，但 kernel=stride、无padding且groups1，现有层会走 unfold＋linear 路径（vLLM layers/conv.py:77,221,247）；不能仅见 Conv3d 类名就要求移植 PPU Conv3d。
- 视觉 ApplyRotaryEmb 的 OOT 桥接已经存在；FlagGems-vllm rotary kernel 使用 padding／mask，D72不是静态禁止条件。视觉旋转表构造最终覆盖72维，不能把中间 partial rotary 维度当最终算子维度。
- MRoPE、原始 token 与 embedding 双输入、visual权重前缀已有接入。尚未证明 PLE／QSA／GDN／MoE 为图片／视频必须另写一套；应先验证其多模态位置和 batch 边界，不改已保留 BF16／MoE 选参及修复。

## 正确性、路径命中及后续验证清单（本轮不执行）

Plugin `tests/qwen3_8_flash_next/test_multimodal.py` 只有3项：typed config、小维度 mock embedding 合并、weight mapper。tiny vision为64维／4 heads，不覆盖真实1152／16 heads／D72，也不包含真实图片／视频编码与 PPU graph。

后续单独获准验证时建议先：

1. 图片单张／多张／非方图、不同grid，视频文件／预采样帧／奇数帧补齐、时间戳与 mixed image-video placeholders，核真实 processor、visual权重加载及占位 token／embedding 对齐。
2. 视觉 D72 BF16 attention／RoPE／位置插值／linear 的数值与真实 backend 命中；不能用 fallback 或 CPU mock 代硬件。
3. 三轴不同的 MRoPE、图像／视频后文本、chunked prefill，核 PLE raw IDs、QSA position cache 与后续 Decode；现有文本 gate 不直接复用。
4. 先验证普通视觉编码与语言 graph；若另行启用 encoder graph，独立 capture 并至少两次变化输入 replay，覆盖多图／变长视频，不能沿用文本 graph 计数。

这只是后续建议，不构成测试启动授权。多模态模型精度、长视频能力、吞吐与显存均 `not_run`。

## 性能效果

无 baseline／candidate／revert，无 profiler，无实测速度、波动或收益；本轮未确认视觉 Attention 是实际性能热点。当前文本 acc020 gate 不受本静态审计替换；P1K四场景性能和多模态性能仍分别待验证。

## 决定、风险与回退

决定：完成静态分析，**不实施补丁，不解除或恢复任何暂停，不改变服务／monitor**。优先候选为平台视觉 Attention 分发与正值 pruning 配置防护；encoder graph仅在需要时单独适配。没有修改，无新回退操作；既有 BF16／算子修复及回退备份保留。

风险边界：源码可以说明可达路径及条件性缺口，不能证明运行时命中、kernel编译成功、完整权重数值一致或图片／视频精度。容器暂停状态在外部变化，未取得完整收尾运行绑定；不把之前文本进程结果冒充本轮多模态结果。

## 外部证据与来源

临时只读快照：`/private/tmp/qwen38-mm-audit-20261024.n6oN2n`。在本机分析结束时6878项source、18项processor的文件大小／SHA均匹配；临时目录不是长期远端归档，不把它当可永久恢复的发布产物。原始源码仍以目标容器上述目录为准，未来验证前须重新绑定。

| 产物 | SHA256 |
|---|---|
| sources.tgz | ec09bab935b4645329ae9d647d575717cc493d613d954edfe88686f7f49e728c |
| source-manifest.json | 68f18ac0500aaa30dfecac3ab53243445a000a739e10bbbe72fdca0e9a80f5ea |
| processor-sources.tgz | fb723909381e00de982fc8e96720d8f4a4684b2be8b490089b912b1bcf9f7dde |
| processor-source-manifest.json | de4dd7e2311f1e845aa798f453f9add7261a674c58ebb348fde54f93ba11f381 |

读取的 Git HEAD／index 清单 SHA（非干净工作区声明）：

- Plugin：a696859b9aa528dfd5b21f5da3403fdc16bac4cd／871bdbffa2c0b52bd93f482182837654b5f5bc8201d1cc456f5c35a4d664adf0。
- FlagGems-vllm：b4d3382bb04da4e0ab444849697865b4d5fcd86e／48cc3b74d6056120cbae7e5f989f86981a6c96a4b4b9902f8f4c57b48bc17c7d。
- FlagGems：f0aa7f12180cea4776a2aba3f3889b8fb82a28b1／0ec71a8a132fa9ec42eedec8f2054daf2efca3f9ffc3395959cdf21256043474。

关键源 SHA：Plugin BF16 model d458a1ce…34517c；platform dd7c89f1…7346a3；attention/utils 1308514c…17adfc；FGVLLM thead MoE cac5b989…f939b（完整值见state）。元数据版本：vLLM0.24.0+empty、Transformers5.8.1、torch2.10.0、torchvision0.25.0。权重仅查看索引（SHA99e815241ef03325536b0aaa4441deea45174c17fae31e10f0bb456410c590de），未加载／重读权重字节。

取证限制保留：proc-root命名空间下普通 git status 未能运行；不把HEAD等同实际工作树。收尾 runtime-source-facts.json 因 paused断言失败为空，未覆盖伪造回执；源快照独立manifest核验通过，但不宣称运行环境完整终态审计通过。
