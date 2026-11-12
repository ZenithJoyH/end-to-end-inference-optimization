# refactor-011：FGV fork同步与按算子提交上游PR

## 最终状态（2026-11-10，以下优先于后文历史记录）

已逐项完成当前范围的MetaX数值、真实公开dispatch、graph新输入replay、源码身份与工程规范复核；**9个PR Ready，3个PR因真实性能/稳定性门禁未过保留Draft**。Ready表示可进入review，不代表已合并、跨平台CI全通过或端到端性能达标。没有改installed源码、模型服务、vLLM或编译器。

| PR | 算子/范围 | 当前状态 | 原生通过/跳过 | 当前head |
|---|---|---|---|---|
| [#1136](https://github.com/flagos-ai/FlagGems-vllm/pull/1136) | gather-cache-address | Ready | 18/0 | `ca79135040eb` |
| [#1137](https://github.com/flagos-ai/FlagGems-vllm/pull/1137) | silu-clamp | Ready | 30/0 | `3d981a5441ca` |
| [#1138](https://github.com/flagos-ai/FlagGems-vllm/pull/1138) | int8-quant | Draft（门禁阻塞） | 36/0 | `3a1e9864c2e7` |
| [#1139](https://github.com/flagos-ai/FlagGems-vllm/pull/1139) | router-topk | Ready | 38/24 | `fae391b0d35b` |
| [#1140](https://github.com/flagos-ai/FlagGems-vllm/pull/1140) | qnorm-rope-cache | Ready | 98/18 | `395b2c68ce24` |
| [#1141](https://github.com/flagos-ai/FlagGems-vllm/pull/1141) | prefill-topk | Draft（门禁阻塞） | 49/1 | `e57d59ffd6ac` |
| [#1142](https://github.com/flagos-ai/FlagGems-vllm/pull/1142) | moe-align | Ready | 239/0 | `51ece3f61f4d` |
| [#1143](https://github.com/flagos-ai/FlagGems-vllm/pull/1143) | mhc-pre | Ready | 10/0 | `654331a76224` |
| [#1144](https://github.com/flagos-ai/FlagGems-vllm/pull/1144) | mqa-logits | Ready | 78/41 | `6d033e0be069` |
| [#1145](https://github.com/flagos-ai/FlagGems-vllm/pull/1145) | decode-topk | Draft（门禁阻塞） | 11/0 focused; expanded24pass1fail | `f8d6d629075b` |
| [#1146](https://github.com/flagos-ai/FlagGems-vllm/pull/1146) | sparse-mla | Ready | 15/0 | `a24574588be7` |
| [#1147](https://github.com/flagos-ai/FlagGems-vllm/pull/1147) | compiler-isolation | Ready | 12/0 | `d6a4aceef1e3` |

最后一次组合核心回归 **527 passed / 18 skipped / 0 failed/error，120 capture / 250 replay**；1263文件SHA前后一致，17个核心测试文件不是全仓验收。18skip是原QNorm vLLM参考接口ABI不匹配，不是目标kernel失败；保留2个xunit2属性警告。MQA/MLA/GDN最新独立复验分别78/15/12pass，GDN含变长64+128、6元数据bucket与3capture6replay。原Decode K1024重复顺序失败单独真实复现，未从完整结论中抹去。

3个Draft阻塞均保留全部shape/三轮和原阈值：动态量化对SDK最差比约0.355；Prefill TopK对SDK约0.3815；Decode全长对SDK约0.1264并有继承顺序失败。比值=baseline latency/candidate latency，<0.9不能晋级。**此前将Prefill原benchmark误判为raw fallback的解释已撤回：实际HAS_VLLM=true；portable自比较约1不能替代SDK门禁。** 未增加猜测kernel掩盖退步、未放宽测试/容差/门禁。量化已有common kernel四warp配置诊断仍不足，全部120点保留。

Native Benchmark cudagraph模式使用Triton内置warmup/capture；CLI `--warmup25`在该分支不单独应用，先前“额外25ms预热”说法已校正。以上都是独立算子microbenchmark，不是模型输出token吞吐/端到端收益；不同GPU的绝对计时不混用。

上游当前变更的style/rule检查已通过，设备CI多仍排队。历史#1136 iluvatar smoke基础设施失败与#1140 maca3810依赖下载timeout未当成算子失败；连接器重跑Actions返回403，需要maintainer处理，不能声称CI全绿。MQA/汇总已保留历史合并新main2bc3b9f...；其他分支保持单算子范围。

fork `flaggems-vllm-opt`：`14127b53ffc9956bcbd88f468e5a773dcf257789`，tree `0884f75555bc606ffb0882391e066322fbd41f03`，与实测本地 `d2e9b4b2428d9f2b88295e2ad2174ff0f49e245e` 完全一致。保留按算子提交，fork main未动。汇总包含上述3个Draft候选，不能当作整套优化已通过或直接部署推荐。

完整命令/源码SHA/原始失败与慢轮在外部 `refactor01/pr-validation01`，最终审计 `final-native-audit15.json`。逐PR全head/tree/status见同目录 `final15-report.json`；public body没有内部产物路径。所有测试进程已退出，最后mx-smi八卡无process。以下为按时间保留的历史过程，早期Draft/Ready/计时/比较器描述以本段更正为准。


用户2026-11-10明确授权：同步ZenithJoyH/FlagGems-vllm的flaggems-vllm-opt与fork main，将已分析FGV优化按算子分批commit/push并分别向上游flagos-ai/FlagGems-vllm提交PR。此授权覆盖此前不提交推送限制，仅FGV；运行容器源码/服务保持不动。

独立工作副本 `/tmp/dsv4-fgv-pr-20261110`；origin/main原SHA97da71f95d72941a29a5b9b256a35521115b8a2b，origin/flaggems-vllm-opt原SHAe3fbfcef96375e428bb7631450ffadf1d9be72a2，fork main领先18提交且opt无独有提交，可fast-forward同步。上游main7598812baf1a64e7d297161f281cad65ab33ff05，相对fork main前进83、fork独有7，需保留fork的Qwen调优，不把它们混入算子PR。

按算子配齐公开API/注册/测试/benchmark和实际验证说明；移植后的PR不能继承旧SHA的GPU门禁，证据不足以ready者标draft。当前分支保留各算子提交，另派生干净PR分支；必要依赖明示。

GitHub CLI本地token失效，但已连接GitHub app可访问fork且有push权限；优先使用连接器，不打印/导出token。

已完成：flaggems-vllm-opt先fast-forward至fork main，再合并上游main并保留fork历史，随后12个按算子/独立编译器修复的提交已push。fork main保持不动，目标分支最终SHA `bcc781dcce689fe7847a7bda2b3298e070521e80`，上游基准 `7598812baf1a64e7d297161f281cad65ab33ff05`。同一内容树在GitHub连接器创建commit时由服务端生成作者/时间，因此本地commit SHA和API SHA不同；每次发布均验证tree完全一致。

为避免fork独有提交和不同算子相互混入PR，12个PR分支分别直接从上游main建立、各1commit；汇总分支保留串行12commit。GitHub回读逐一确认head/base、Draft、单commit和完整文件清单一致。

| 批次 | 上游Draft PR | PR head SHA |
|---|---|---|
| gather-cache-address | [#1136](https://github.com/flagos-ai/FlagGems-vllm/pull/1136) | `ca79135040eb` |
| silu-clamp | [#1137](https://github.com/flagos-ai/FlagGems-vllm/pull/1137) | `5d9a36eb061e` |
| int8-quant | [#1138](https://github.com/flagos-ai/FlagGems-vllm/pull/1138) | `7d1c39413ad7` |
| router-topk | [#1139](https://github.com/flagos-ai/FlagGems-vllm/pull/1139) | `1461e325700d` |
| qnorm-rope-cache | [#1140](https://github.com/flagos-ai/FlagGems-vllm/pull/1140) | `0ca2a1b92bbf` |
| prefill-topk | [#1141](https://github.com/flagos-ai/FlagGems-vllm/pull/1141) | `d3a67544fa3b` |
| moe-align | [#1142](https://github.com/flagos-ai/FlagGems-vllm/pull/1142) | `1f646c18fd70` |
| mhc-pre | [#1143](https://github.com/flagos-ai/FlagGems-vllm/pull/1143) | `00a76cf4cd51` |
| mqa-logits | [#1144](https://github.com/flagos-ai/FlagGems-vllm/pull/1144) | `6f6080b1edcb` |
| decode-topk | [#1145](https://github.com/flagos-ai/FlagGems-vllm/pull/1145) | `ef2cf9a28d60` |
| sparse-mla | [#1146](https://github.com/flagos-ai/FlagGems-vllm/pull/1146) | `269d0a7338d3` |
| compiler-isolation | [#1147](https://github.com/flagos-ai/FlagGems-vllm/pull/1147) | `06cc560bafdb` |

验证：每个独立分支AST/Black24.8/isort5.12/flake8 7.1、真实pre-commit hooks通过；MQA14/DecodeTopK6/MLA8项standalone CPU测试通过。汇总树全仓pre-commit通过；补充MLA测试SPDX头后该批次与独立分支再次通过CPU与pre-commit。全部12PR当前check-runs为空，不计CI通过。重基后未跑GPU数值、真实dispatch、graph或性能，历史容器证据不移植到新SHA；均为Draft且无收益宣称。quant/prefill-topk/MQA/decode-topk/MLA还明确披露host normalization/copy/fill的no-torch-compute人工规范复核欠项，需解决后才可ready。MetaX接口扩展不宣称NV支持。

发布范围仅FGV。容器安装源码、Plugin、FlagGems、模型服务均未改，不运行GPU/精度/性能。此前“不提交推送”限制由用户2026-11-10本条明确授权取代。自动审批曾据旧限制拦截一次MLA source-tree上传；核验最新授权、Apache源代码范围和无敏感路径/密钥后，同一连接器重试通过，未绕行。

外部证据归档：D/pr-series01/submission-assets-20261110.tar.gz，SHA256 `2d30f741b220b889a897c4156b487353189d123c2a6e371e1736ab24110e6e1e`；含每批patch/body、原始检查日志、manifest与submission-result.json（SHA256 `fd73d5fce6afb211f112bd72baa109e13eace0a1a13b1616cbe7e023b2ecce43`）。D=`/public-flash/jinghao/deepseekV4/20261104-dsv4-metax104-plugin-review/refactor01`。后续不自动将发布分支安装到容器或启动GPU任务。


发布后归档命令：`/tmp/dsv4-fgv-pr-archive01.py` SHA256 `d401977760bec0b941269634bff18420df25d1005576958a2499e1dc620d3618`，通过mx-104 SSH仅在既有D下新建`pr-series01`，校验tar SHA后排他写入；不覆盖既有产物，不触碰容器/服务。

2026-11-10用户要求依次完成验证与规范复核并将通过者转正式PR。同一ref011继续：新外部根`/public-flash/jinghao/deepseekV4/20261104-dsv4-metax104-plugin-review/refactor01/pr-validation01`，12独立源码树分别按当前PR树验证，不替换installed source。仅GPU0串行数值/真实JITlaunch/公开backend日志/graph capture>=2新输入replay；标准pytest --quick保持原容差，1800s每批，失败原样保留后修复新attempt。GPU设备已空闲，无需暂停或恢复模型。源码包SHA ea93ed059702bd57be1ec1bb416154f817e42b2c093364a9430552f7a528b899；stage脚本SHA 3b6b29b291e8358eff3e283d1cc9c5394b8c7b81cbbd21b3415a9e09a7953387。命令：在目标容器中以env MACA_VISIBLE_DEVICES=0/CUDA_VISIBLE_DEVICES=0执行新根/device-inner01.py <index>，其inner/pytest entry SHA已随stage归档。无依赖升级/安装环境改动。

解包filter在相对symlink报错、0GPU请求，保留已传tar和部分目录；恢复脚本recover-stage02.py逐项规范化路径和symlink containment，只对新文件排他写入，已存在文件须byte相同，不覆盖。SHA 0cc95d94331996e74a29119f36f32b16723a4fb2c182cf9b7ccbcea7e1b801a9。

逐批启动器launch-batch01.py SHA 3b40e0d38cfa44aeaa63d350ba129cbdb40efcaf57cb13110dfe4436339253fe，先mx-smi GPU0无process守卫，排他launch receipt，docker exec仅MACA/CUDA_VISIBLE_DEVICES=0，唯一inner预算1800s，所有输出存新根，不操作模型服务。

审计补强：SiLU添加9个dtype/layout graph新输入/sentinel/signedzero；compiler子进程显式sys.path指向本候选并assert模块路径，避免-I误测已安装；DecodeTopK复用仓库已有fill_tensor替代torch fill_/full，增加emptywidth pitchedout graph。均各PR独立新增commit+precommit通过，待GPU新attempt02，不改旧冻结树。extend02包SHA 0b81b3741d521516863e18b728daeb8d7034e24f26c92c97bf4e318a3e0ac652；stage-extend02.py SHA dda0c34558d7f00b62631d60ffaf4c29a27a19c8da2ba04a7a796711967882a1。

#1136验证已完成：18passed/0failed/0skip，GPU C550/Torch2.10.0+metax3.8.2.2/Triton3.6.0；真实gatherJIT34launch，16capture/32replay，源码前后全SHA一致。该PR作为纯正确性修复无需新增收益宣称，公开入口/独立oracle/索引int64/无torchcompute与运行时retry复核通过；NV/其他vendor仍由上游CI覆盖。已更新body并ready，API回执draft=false，head ca79135040eb738048cddb4ebff7d8287dff3a73。余下11项继续，不因单项完成终止。

为避免NFS逐文件SHA与import等待，后续在容器未安装的新私有源码目录/opt/dsv4-pr-validation-20261110中验证相同完整源码树。原始tar/日志仍归D/pr-validation01；manifest与Git树SHA精确一致，既有安装目录不变，无pip安装/编译器变更。private-stage03.py SHA 6c4989b9b30683140fa8384c971ea8beac410b212ac61ff13ff5e859e4132e1d；private-payload03.json SHA 98a54024f7a6b76b3917bd92033e9cdf00715d09ec309325a9bb98e62a2d1f57。另补MQA gathered/paged BF16独立CPUoracle与newinputgraph/布局canary；qnorm/MLA测试显式恢复RNG，均precommit通过，待新attempt03。

后续单GPU串行协调器coordinate03.py SHA 99dac9fc7f1fb28440a44f3b738aaedcb42fb29f853183381c86ef1125b5ff1e：等当前router原生receipt后，4..11各独立源码树/准确attempt，只一客户端、每批前GPU0无process守卫、原生失败保留，非法访存立即停止整串定位。不执行PR晋级，需独立审计后逐一ready。

规范复核04：quant显式contiguous后view，Router graph校验第三个slot输出，TopK空宽先device/shape校验后fill且CPU拒绝不写buffer测试。均独立precommit通过，payload04包SHA 2c54933dcda2bc2b5fea805f8c1b14e7d8be65e037e7873acf25ae977592d689；private-update04.py SHA 7f7efb05a680f4e133d928083640d91afeb36c8d243a79efd647e2c1ab4fb780，新私有目录v04+新attempt04保留旧证据，不编辑运行plan03。

后续revision04串行协调器coordinate04.py SHA f36d192f2b04565a117705a9fed43930257c53a69276822da0abbef6b70beb43，仅在03全部终态且GPU0空闲后运行量化/Router/DecodeTopK三项新SHA，不重放旧attempt；独立审计再晋级。

性能/最终补强05输入已冻结：payload05.json.gz SHA 70ff04d7ab5e319d7b2386b03a0f253d90f7f061399a9442cb821a5055e6f89e；private-update05.py SHA fcdfb30d74de118c60175c679c770452b1ca867315e3391098c80b9d27c0b549。每个性能类PR使用原生benchmark.Benchmark、同GPU0、cudagraph模式、BF16、25ms warmup/100ms measure，3完整repeat/全部core shape，不挑快轮；baseline类型逐一标SDK/portable/reference/retainedserial，核心SpeedUp<0.9不晋级，先定位/修复。QNorm两侧都包含相同q/kv状态重置copy，非纯kernel时长；mHC用publicMetaX对portable（原benchmark直调common未命中fast）；MQA覆盖shared/gathered/paged；sparse对retainedserial与split/staged，policy在benchmark-only try/finally恢复。不可用SDK不冒充baseline。仅算子micro，不重启或启动模型、不作E2E收益。补强编译器路径assert改固定expected_root并保留失败，另加两GDN native数值+新输入graph用例，待新attempt05。

最终补强+microbenchmark唯一协调器coordinate05.py SHA 0c0c03c80620390a04308ced1d6df41a913530f27ba92637980ddd6c2ef9f994，先4/7/8/10/11新attempt05，再11个算子各3原生repeat；验证失败不测该项，benchmark错误保留并停止该项其余repeat，设备错误停全串，禁止自动PR晋级。

revision05全部终态，独立micro审计：SiLU/Router/MQA/MLA三repeat全部有测量，QNorm全部不退步但接近1（含两侧resetcopy，不宣称加速）；gather原SDK benchmark不适用而skip。Quant动态30shape三轮均<0.9（最差0.355），static无关键回退；mHC fallback H128出现约0.588待归因，不晋级。prefill/MoE/decode benchmark被统一BF16参数在测量前拒绝，改为各算子真实float32/int32/float32，新输出不覆盖旧失败。Decode reference移除graph中的.item同步，仍独立torch.topk并消费每行length。

revision06输入冻结：payload06 SHA b4f9b41d03a7a222bce0c51e115929f7cea0cfb0f0ab47319a9dc8b9d47d8281，private-update06 SHA91e682917e2bcba76876e9c05a842b3352feb89389db3d288085dd9edb7012c7，coordinate06 SHAcb58ea327538936ba9772c507143decea98b2a42cd1de5a0629c6b8177862ca9。QNorm logger/deviceguard和混设备拒绝；compiler用安装FlagTree真实get_supported_primitives白名单提前选择既有native recompute，default保留其他后端原策略，不改编译器。新attempt06补标准selector原套件量化/router/prefill/MQA/decode，不只新增用例；失败保留、设备错误停串。

量化首个证伪：仅已有common singlepass JIT，warp1/2/4/8、stage1、原30shape（N512/1024/4096/5120/8192/13824，M1/64/512/2048/4096）、BF16，SDK独立q/scale校验（scale1e-6、整数差<=1），native Benchmark cudagraph25/100，同一GPU0；不新增生产kernel/改算法、不改cache。诊断probe1repeat预算1800s，不当最终晋级性能；最终如变更仍需public新SHA数值graph及3repeat全shape。probe SHA743f32c3083c098aad28990a4c72cf275a40b13be1e68819554e79ae0509f8f9，inner5e1186fd6e103029e75fedb8f1bdb574889529f4be33af6bdd00a603949f9f5d。只在05终态/GPU0空闲后启动唯一06。

revision06 GDN五项原生测试0fail/0skip、2capture/4changedinputreplay通过；真实native recompute/GDN命中，源码982c354...树1151e374...与已发布9725f7e...完全一致，#1147已ready。#1137同理已ready（源码a060352/remote3d981a/tree7fd80e1...）；PR正文更新自动审批曾拒绝内部路径和未明示head绑定，已去除内部路径、独立比对remote Git tree后安全更新成功；非审批绕行，不上传原始日志。

mHC初次回退归因更正：不是H128fallback（约0.995），而是T512/H4096专用split（0.5886）；小batch1/64/65约3.35–3.40。最小修复限制fast1..128，较大batch用现有common，删除不可达heads/fused分支（生产文件796→434行）并将新内部assert改显式校验+deviceguard，数学kernel不新增。新benchmark保留慢512并扩128/129/4096和fallback；新数值graph覆盖128/129边界与空batch。MLA补all-masked+空batch写前拒绝。revision07payload SHA6bff0a665cb5159bc28c5584db003d0723275c8e775314fe355369cd88280281，stagebe65a2c6d354b5cff0752d72733f8196e27c99f715f35c51c5da9f958dc8eb01，coordinator12a0c6780e18d16858827fb77457218279d6c0ebd902e9510b4f60afeb9433db，benchmark39376f7b3120ab29b573eab7736b33a9d57e83912b765ea3268c8c842f04bb55。仅06终态后GPU0空闲准入；先新native07，再QNorm/mHC三轮public micro，无模型操作。

原selector补测：quant36pass；router38pass/24既有TLEskip；MQA原FP4测试收集时缺可选vllm.third_party.deep_gemm，原保护块外误导入，已移入原try/既有skip语义，非跳过新增BF16/FP8独立测试。Decode原K1024 repeated-selection失败（集合正确、返回顺序重复不一致），该路径common/fused两源文件与upstream main全SHA相同（a6f76667.../5b6521a6...）；新增inherited08明确绕过新K512wrapper、原assert不改，定位是否继承。未因新用例通过而伪称全部原测试通过。

prefill初始raw comparator缺少生产public使用的CANONICAL_OUTPUT/NUM_ROWS，比较工作不完全同契约；其7shape三轮约0.38–0.56全部保留，不作为等价基线。新增单独具名complete-portable-contract comparator，明确portable fullpublic→MetaX wrapper，原raw测试/数据不删，不借其结果宣称新性能收益；此项是同算法接口收敛与特化复用。先验证完整契约下不回退再评估ready。revision08 payload120cabea842d506a5bb2079797a7359e789ca19c3a0bacaa0e7a273d34b5e167，coordinatore57eae7a307f6f51c789b3c151adc9c62359419e6b8b660f57b6ea3d57398191，benchmark4a7bd713afe79c459c81dcda1f0647fba947035f2e331c8e1591ee98f2199535，inheritedafe940575228c4f3ee23afe5c593192a4cfc3f7769e7950c6161def72de85b5c/inner15038da5ee72808df9bc7bde3ae0c38227dfbccb295afa513104c37155a3498c。07终态后串行GPU0执行MQA08、unchangedfallback复现和prefill完整契约3repeat，无模型操作。#1139数值38pass/24skip/8capture16replay+8shape3repeat全部>=1.9057，规范复核后已ready。

revision07 mHC新候选6pass/0skip，含128/129边界+空batch、5capture/10replay；graph和fallback真实JIT通过。新增MLA全屏蔽测试初稿把数学logsumexp(empty)=-inf当作ABI，失败保留：实际NV/FlashMLA独立reference tests/test_flash_mla_sparse_fwd.py:143–157明确empty LSE为+inf（O=0/max=-inf），生产staged/serial一致；按原独立golden sentinel修正测试，未改生产数值实现/容差，待09新attempt。

量化probe01因测试位于benchmark目录外未自动加载原生conftest，CLI在收集前拒绝参数，0GPU请求/无性能结果。新的probe02仅显式-p benchmark.conftest加载同一原生配置，全部输入/warp/SDKoracle不变，新目录保留旧错误，inner SHA006a6becab682fd8bee358c36ac01aaeda03a04d43fc982d29333d7d41558764。

最终09串行输入：payload3d34a0f8c074d808719fe622f6d13f96a1527da3e345fdd5eab3bcca904fd320，stage5a74374da04a34ef6e39a4b222d157f2f0042e8e8e02fd40c1a9cb6f95d708ba，coordinatorc5531b39f68a499d6c6f4dbb52d28fdf1563b5e20add46fd18f8fb1ba241c41f。08终态/GPU0空闲后，probe02→MLA新sentinel测试→combined核心17测试文件（覆盖各PR新路径与compiler isolation共同生效），不取代已知K1024原套件失败或各独立PR性能门禁。combined本地SHA58e3509420ca69e5ced062f4729be34d1e63061f，1250trackedfiles，先原upstream/fork汇总历史后按算子followup分别commit；不部署installed目录/不启动模型服务。

mHC07扩展128行仍约0.686，故保留失败/慢轮、不晋级；最终fast guard收窄1..64，65/128/129/512/4096都回现有common，增加16/32基准与32/64数值graph，删除guard后不可达empty分支。09未stage/未launch、0GPU，因该新事实superseded（冻结文件原样保留）。最终改用10：payloadb73d5072f5b076317b2625ef6b54c31990f358644bf94778c57bcd720cd976c6，stage87fa617f243cbd42f0a99a24fc64a06880a4ee9ca2751e6ab51b76ccfa6a8f9f，coordinator81ab068894a53783259699a345f2f8e1d3b1e64c9cc87c7d819c3832e0f7ad5b，benchmarkf632b42116b8f545144b2fc9eb343ec3d29be686dc4e0551791965be8c16a67d。等待08终态后probe02、mHC10、MLA10、combined10、mHC3repeat。组合本地SHA55676f5a578196418f3a0d0032af83282ab83622，未替换installedsource。QNorm最终98pass/18参考skip、2capture4replay与7shape3repeat最低0.99897，无测得加速但无关键回退，#1140已ready。MoE239pass/8shape3repeat最低1.2237，#1142ready。

10在probe02生成CLI时残留无参数的sys.argv[1] dtype表达式而退出，0GPU请求，后续mHC/MLA/combined尚未开始；保留失败，原freeze不编辑。inherited08同样因目录外--quick未载入tests/conftest而收集前退出，0复现请求；11显式-p tests.conftest。新独立入口AST/CLI索引预检查通过，probe03固定BF16、不读CLI索引，加载原生benchmark.conftest。11使用既有plan10/源码，不改冻结source。

启动前09:57Z前只读发现GPU0/1出现新VLLM workers，各约30GiB，不停止/干预。GPU2同型C550空闲859MiB且无process，后续单卡租用改GPU2并冻结新契约：所有新baseline/candidate均同GPU2配对、3repeat，不能与旧GPU0绝对时长合并；数值/dispatch/graph仍同栈，保留device事实。11精确GPU2idle守卫+CUDA/MACA_VISIBLE_DEVICES=2（inner不覆盖为0）。11脚本SHA：coordinator204260c3f6e6ee86acb6ca1092e10dd9ea1a67e336aa499c6bcfb8627a9688b8，device380a677f9024821c44f9bae09a5eac9931c962f5f8c795863774bff071ebcd90，benchmark1a1b0d6a4b00b87f8421f6afc9ce2eb98bfe9c0be081190cff794d05633fa1d2，probe2103b7e3f1a50b308aa1cc157a19acecdbdfcec4a101f51f354cb6c7ae42f8d7，inherited13e4db79a5a5f0dd5516e2e0df0e37d98c57f17195e49b886a87d6abbc5f7dbc。先验证旧10driver不活，再新输出串行；无模型服务/容器操作。

probe03已实际运行一项kernel，但SDK symmetric返回3tuple（q/scale/None），oracle脚本误按2tuple拆解而失败，未产生任何计时；原回执保留。probe04只按实际SDK接口读取q/scale并断言剩余项为None，计算/矩阵/配置/容差不变，继续同GPU2原生Benchmark标准。源码8ac064fb2d32b73d6689f299a6bc3a905aa0213daa6c3d01d570cb35cc50dd40，innerce879cfa5109003a2ec3308769cfa8ebe7240a3380c6c3eff7804c14ccc42455；等待11整体终态/GPU2无占用后只运行此新诊断，绝不以这些编排错误替代性能结果。

11：mHC C64限域8pass/7capture14replay；MLA15pass/11capture22replay，allmasked sentinel和empty写前拒绝均通过；combined518pass/18原ABI不兼容参考skip、119capture248replay/0fail，源码1250文件前后SHA一致。Decode inherited11已真实复现K1024返回排列不稳定，源两文件与upstream完全相同；原assert未改。其全长262K benchmark三轮11shape最低0.1264，故#1145继续Draft（既有稳定性问题+当前性能阻塞）。

probe04终于完整，4configs×30shape的独立SDK q/scale验证通过，全部120计时保留。GPU2每配置最小/中位加速比：warp1 0.02951/0.19741，2 0.07804/0.52707，4 0.35430/0.64076，8 0.21792/0.69170；即使逐shape乐观挑最快，27/30仍<0.9、最差0.60470。仅配置调整不足，不发布猜测policy、不新写kernel以掩盖验证失败。#1138继续Draft，公开当前36数值pass与原3repeat动态30shape全部<0.9（SDK相对）事实；static无同类阻塞。

mHC最终人工复核再补mixeddevice写前拒绝，非默认n_splits走common保留原warning，并恢复测试helper修改的RNG状态；default n_splits=1的数值kernel不变。为严谨仍用新13tree重验数值/graph、combined与3microrepeat。13payload69d7c2ce65eb6bf2e741cf672e0298ca43e8686a848ba3243235fec8f7299e36，stagea4c1c51062cf07b7b68fb82fb532f164276f6f77515356347dbaab0ce00ddcc7，coordinator0a4b050adb85b07a5d06d2a3e786999c58b4fb8a6699a580014e1e107242301a，benchmarkf63b7214e32d17f1f4ba2d81d8f319e2d5c18bba32771ba13641fe802da90fa9；GPU2只在11及probe04终态且无process后准入，最新combined local1ad0ea0b3a8b87114705f94bf77856d79ba1417d。#1146新15case与保留serial三repeat最低decode2.131/prefill3.1499、规范复核通过，已ready。#1141独立完整public契约比较三轮最低0.99038，原raw比较不删且解释工作不等价，按refactor而非新加速晋级ready。

最终计时口径校准：FGV Benchmark cudagraph分支只把Config.repetition传给Triton do_bench_cudagraph，CLI --warmup25未单独应用；实际使用Triton内置warmup/capture。已逐PR修正文案，不改命令/数据/比较。同条件计时仍有效，不伪称有额外25ms显式预热。

最终需回读条件benchmark实际HAS_VLLM（不能单凭静态fallback分支假定被选中）。新增CPU模块metadata-only脚本benchmark-identity02.py SHA988d39162e5573e1c228ab54ac638224f981f0f0066f048af685618d6291637a，仅在13终态/GPU2空闲后、各候选精确导入path，读取实际native-op可用性与函数对象；不调用算子/benchmark/模型。若SDK实际可用，则原prefill结果不能按raw comparator排除，必须恢复Draft并披露真实阻塞。

CI收尾15：最终实际HAS_VLLM审计已证实prefill原benchmark是SDK比较，前述“raw comparator不等价而排除”的归因正式撤回；其约0.38加速比是有效阻塞，#1141已恢复Draft，不用portable自比较替代SDK门禁。Quant #1138、Decode #1145同为Draft。稀疏MLA #1146和compiler #1147因真实CI风格问题暂回Draft，先修复绝对import及GDN缓存元数据中的torch计算，再验证当前新SHA，不能把历史通过移植到新树。7个其余PR Ready。

新upstream main固定2bc3b9f0a6e75e81a3ac7504642b86fa39167c9f；MQA和汇总分支已非破坏合并，新增CI registry baseline移除已注册paged导出、alias补齐和__all__/operator清单排序。7独立分支各4项CI本地检查均PASS；合并树66个tools CI测试、导出/registry/YAML/markers/pins/precommit通过；no-torch检查首次CLI误用--files收集前退出，修正为原生positional路径，21生产文件0违规（原失败保留）。未修改数值kernel或放宽容差。

revision15已冻结：payload15.json.gz SHA dfde6bc5e36531d4c45b65caf76e4bba895e7a432514979f9c5d6c4552e5201f；private-update15.py SHA f592beb3692890ca117c1a02106ed070e6671ca4e2f98e0a928c7bb5688987c2；coordinate15.py SHA 38e0c362ec045e363a65866717d6d2dd114bdb17be593258ae81a338994d1616。独立MQA ebec5cc/MLA147b53c/GDN3aed1dd及汇总d2e9b4b，仅在pr-validation01新私有v15目录测试，完整SHA前后守卫，GPU2串行；新GDN覆盖6种CUDA元数据bucket+分段变长输入独立CPU recurrence、graph新输入2replay。每批1800s，设备错误停止整串；不改installed source/服务/依赖，不启动模型。用户已释放显存，最新mx-smi 8卡无process，仍只使用GPU2。

部分上游CI是checkout503/依赖下载timeout等测试前基础设施失败。连接器Actions写权限返回403，无法代维护者重跑；不得算作算子失败或冒称CI全绿。实际代码style/rule问题已本地修复，等待新GPU回执与发布触发CI。

revision15独立回执：MQA78pass/41原SM90和可选DeepGEMMskip/38capture76replay；MLA15pass/11capture22replay；GDN12pass/0skip/3capture6replay（142.42s）。真实新GDN变长segment64+128及元数据六bucket均通过。合并树仍在同GPU2串行验证，不能提前当完整通过。后置只读audit-final15.py SHA ce4e5f5772ad7326df93c52accc16b98e8bded5e26174b6f1a8e108d791554da，将核验原生XML唯一case、skip、源码前后SHA、真实JIT/graph并排他输出final-native-audit15.json。

revision15最终独立审计通过：组合527pass/18原QNorm SDK ABI参考skip/0fail/error、120capture250replay，1263文件全SHA前后一致；MQA78/41skip/38capture76replay（1244文件），MLA15/0skip/11capture22replay（1233文件），GDN12/0skip/3capture6replay（1227文件）。原生skip消息与两xunit2属性警告保留；不把组合核心17文件当全仓或模型验收，不覆盖Decode继承失败。最新mx-smi无process，未操作installed source/模型服务。

#1146/#1147最新head上游code-style和rule-check均success，已通过API恢复Ready并回读验证。12PR最终9Ready/3Draft；3Draft为#1138动态量化SDK比最差0.355、#1141prefill SDK比约0.3815、#1145decode全长SDK比0.1264及继承K1024重复顺序失败。正式PR不是已合并，也不代表跨vendorCI全绿。其余新设备CI多仍排队，旧#1136iluvatar smoke基础设施失败、#1140maca3810依赖下载timeout待维护者重试（连接器Actions write403）。

fork汇总flaggems-vllm-opt已非force更新14127b53ffc9956bcbd88f468e5a773dcf257789，tree0884f75555bc606ffb0882391e066322fbd41f03，与实际验证本地d2e9b4b完全相同。保留原operator提交，新增upstream merge、GDN修复/测试、MLAimport和共享CI元数据各自commit；fork main97da71f...未动。汇总仍包含3个Draft候选，不宣称整体性能达标或推荐部署。归档脚本archive-final15.py SHA1fde4d8a62c95c4b5171235e1087f571e120b6b6b50b34482f164e8675901b52，将所有回执/日志/配置/冻结命令及CPU复核产物排他归档，排除已有源码tar和私有workspace，原件保留。

最终证据包：`refactor01/pr-validation01/pr-validation-final15.tar.gz`，SHA256 `b50f3cac68668067b3ef73530e1c05edb099ac07859276233a804942833799ec`，15,941,251bytes/898files；归档含CPU规则检查/冻结命令/每轮原生结果与失败、逐算子patch/PR身份和独立审计。原源码tar和workspace不重复打包，原路径保留。


## 2026-11-11：三个Draft与当前推理链路的关系（只读）

用户询问三个PR是否实际使用以及是否代表E2E退化。已通过项目inventory/connectivity-check精确mx-104后，仅标准库/文本读取整改容器，未import GPU库、未发请求/性能测试或改服务。现场未发现该容器的vllm serve/api_server进程，故本次是当前安装及默认模型配置调用链核验，不冒称当前live请求命中。

editable FGV仍为`/opt/dsv4-sources/FlagGems-vllm-main-reuse-20261105/src`，Plugin仍`/opt/vllm-plugin-fl`；新PR/私有验证副本未替换installed。三个对应数值路径均已经接入：1) mctlass_ops.py:381→DeepSeek scaled_int8_quant前端，在BF16连续2D、对称动态且宽<=16384时→dynamic_per_token_quant_int8 CachedOp→DeepseekV4MetaXBackend→FGV根包scaled_int8_quant，其他guard外用原SDK；2) SparseAttnIndexerFL Prefill→CachedOp top_k_per_row_prefill→MetaX薄wrapper→common selector，有效候选数<=K则select-all，不执行完整TopK；3) Decode长行→CachedOp decode_topk_tree→vendor桥→FGV公开top_k_per_row_decode→MetaX K512树。实际模型config index_topk=512，PR中继承K1024重复顺序失败不能直接套成当前K512模型故障。以上路径依赖原DeepSeek MetaX默认策略，不能将仅注册名当每个请求都执行。

纯AST对比安装源码和已测私有候选：量化9个、Prefill11个、Decode2个顶层Triton JIT函数均相同，无不同/新增/丢失；host检查/完整源码树不必字节相同，不把私有PR测量原值直接充当当前服务实测。三个慢实现的核心已在现有适配中，不是这次PR发布新写入服务。

当前证据支持其在命中形状时比SDK更慢、有潜在替换收益；不支持当前E2E相对整改前净退化的定量结论。0.355/0.3815/0.1264为不同形状算子micro的最差baseline/candidate比值，不是E2E吞吐比例，Decode的全长262K与模型实际有效context/填充/早退工作不同。缺少只替换一个路径的同workload/同graph/同服务条件配对模型A/B及该路径关键时长，不能给E2E退化率或将三个比值连乘。没有启动额外GPU任务或修改代码。
