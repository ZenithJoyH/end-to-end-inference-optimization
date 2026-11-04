# cleanup-005：DeepSeek V4 MetaX 容器瘦身

状态：completed_retained（2026-10-28 11:11 Asia/Shanghai独立核验通过）。以下前半部分保留计划与失败历史，最终交付结论见文末。用户2026-10-28要求在保证推理正常前提下给当前容器瘦身。Host mx-103；当前容器deepseekV4-flash/63249a7da309。当前image60911198bc6b报告Size30,839,171,746bytes/38layers；容器root du -x为63,378,989,056bytes。所有模型/共享挂载排除在删除范围外。

本项仅包装/冗余文件整理，不改变模型、采样、推理源码、Python依赖版本、挂载、设备、启动脚本或环境策略。通过独立候选清理后导出merged rootfs并生成单层压缩OCI镜像，实际消除旧层/whiteout占用，不能用在旧层上删除文件的表面数字宣称镜像变小。原容器及不可变snapshot保留回退，不做docker prune或全机空间回收。

## 删除与保护边界

预计主要可移除项：/opt/dsv4-upgrades历史升级安装/备份18.1GB，FlagTree/build约7.3GB，旧MACA3.7除FFmpeg外约6.8GB，pip缓存0.86GB，NVIDIA构建下载1.13GB，Conda包缓存0.25GB，以及旧Plugin候选/旧准确率副本。只在private candidate删除，原始材料仍在源容器与snapshot，明确保留恢复入口，不销毁唯一证据。

必须保留：实际editable Plugin、FlagGems、FlagGems-vllm及各自Git目录；已安装torch/vLLM/FlagTree；MACA3.8.2完整运行/JIT SDK；/root/.flagtree/metax LLVM19工具链与plugin；驱动；旧MACA3.7的FFmpeg完整子树（当前进程maps证实仍被torch加载）；共享/var/lib/dsv4与/public-flash、/data完整映射。FlagTree保留源码/Git，仅去掉build及其compile_commands符号链接。Conda硬链接由在候选文件系统内先unlink缓存再export处理，避免直接过滤tar导致保留文件的hardlink target丢失。

## 门禁与验证计划

源API在准备/导出阶段继续运行。snapshot使用--no-pause。候选挂载用原生verify-container-mounts检查；比较五个核心Python源码树SHA、实际mapped ELF依赖ldd不缺失；flatten后再次比对源码/依赖/环境配置和路径。GPU租用仅精确停止空闲本任务API及workers，源容器保持运行。先用全新私有Triton缓存在8GPU运行小规模数值核验，证明JIT编译工具依赖可用；再由现有start-model.sh启动服务。复用e2e/accuracy minimal-regression原20条请求，加2条>32K输入和64并发短数值请求，共86条；核验capture/FULL replay、API健康、无OOM/非法访存/MCCL错误。通过后新容器沿用deepseekV4-flash，原容器改名deepseekV4-flash-slim-backup-20261028作为回退；失败恢复旧API。用户本轮瘦身要求授权此最小可逆迁移，不停止/重启/删除源容器。不新增正式GPQA或性能分数，不声称长时间稳定性。

远端根：/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/container-slim-20261028-01。大型原始产物保存在该目录，本地仅留摘要和SHA。
- commands/clean.py SHA `92f6f307b9ac80f2229bce0f2c0930991f8240c29222ca10b654152ef4a23419`
- commands/prepare.py SHA `13d7c75947fd4dbd6ba2b5b6480386f6105a26cab310f2dac5322be488d2a882`
- commands/verify-container-mounts.py SHA `32adacf39859e88ad6e2dad04ada248a00b636c795fed67d34328f5264bec3e3`

私有候选清理已执行，首次ldd检查把torch扩展中由Python预加载的libtorch依赖当作缺失而停止，尚未导出/切换服务。原服务未动。修正取证：仅对独立ldd子进程补充torch/lib和conda/lib搜索目录，同时比较原容器与候选的相同依赖、实际mapped文件SHA和Python源码；要求新增未解析依赖为0，不修改实际服务环境。不重复清理，失败回执保留。
- commands/verify-clean.py SHA `bd5e4d72de6201b549b935ac4987af1f6a45062b9aa49c9359b607bd9fd570c1`

导出/压缩契约：只导出已清理且sleep空闲的private prep容器，保留文件mode/owner/PAX xattrs/hardlinks；排除挂载点内部底层目录内容（Docker export不导出volume当前内容，但可能导出被挂载遮盖的image底层目录，故显式过滤/public-flash、/data、/var/lib/dsv4的内部项）。不改变实际挂载。pigz -1 -p4压缩，记录未压缩tar diffID与gzip digest；使用保留原Config/8项ENV的一层OCI镜像，经原生docker load导入。所有新镜像对比基于相同Docker inspect.Size字段，root du另记，不把备份保留情况下的镜像缩减冒充全机已释放空间。参考[Docker export](https://docs.docker.com/reference/cli/docker/container/export/)。
- commands/build.py SHA `57c8dc3b1edc7454d83b1c3ea72dc53cdbe507a650b6db92713cd915dc4a3806`

源与清理候选核验通过：五个核心Python树完全相同，400个实际mapped二进制字节一致；standalone ldd原有7项预加载依赖解析限制在两侧相同，无新增缺失项。root du从63,378,997,248降至28,911,214,592bytes（实际根文件系统减少约54.4%）；镜像实际Size待flatten后测。
模型切换不更改start-model.sh，脚本SHA固定7963febb...；沿用当前API44/ticks1157315643的完整argv/13环境值与prefixON设置。先24项fresh-JIT（8GPU×3dtype非对齐向量）再86条服务请求，原生capture/replay和日志健康全部通过才交换名称。
- commands/jit-smoke.py SHA `80612bc661b2fa432b31661a535ceacc3624a6965f8d2f0eceb339df390896b9`
- commands/extended-regression.py SHA `58e1a3d375d956ddb7c89da4591aa4af3f359eaf726b8b690276ae089a6c3a60`
- commands/lease-source.py SHA `2cb4bc1c9b0d2800c55e26a3f9db400cf2f0fbbca3e8fdeca12ff07f6466f0ef`
- commands/minimal-regression.py SHA `af168772005f254d4b28e1af67479f96968be2b291aa45fe72bf3cd09ca882af`
- commands/migrate.py SHA `f01686df2cb238bab382b0aaa42d5d324dd2d5ba8b4b5a87c0360cf5bf9ba18a`

- commands/verify-flat.py SHA `655566fadb06fe612801f08027443eb615758feeaa565d5e55268508cfa48b29`
flatten最终候选在GPU租用前再次独立比较五个Python树、400个实际mapped二进制SHA、editable direct_url以及critical LLVM/FFmpeg保留路径；新镜像不同层不可仅凭base tag作为谱系证明。
切换前加入flat-verification硬门禁，最终migrate.py SHA `71a15e42ce3eca8da73758e1d75d1aedd32cbb834251805d29be8da7c404df01`（尚未执行）。

单层镜像已成功导入：dsv4-slim:20261028-runtime，ID510baaeb92b74ecb023701d5b06a66318e0ef778e45ff61a7e15cf4d495a0d8f，Docker inspect.Size=13,634,367,315bytes；原30,839,171,746bytes，减少55.79%。38层→1层。candidate73eedc5bc92c已创建并通过原生mount parity；当前source服务仍未切换。

第一次切换前置guard发现用户启动脚本SHA已变，直接退出，未进入lease、未停止API、未产生JIT或请求。只读diff确认唯一用户改动为--enable-prefix-caching→--no-enable-prefix-caching；当前旧API44仍prefixON且health200。以用户最新脚本SHA ecdbb44508f2e7eb2d257d925de201565b4cf7f30b111d859c6814fb8f96a01d为准，交付验证使用prefixOFF，保留用户修改；候选argv仅允许此已识别参数替换，其他逐项相同，回退保留旧API原始ON参数。没有覆盖脚本。此前“prefixON保持”计划由此被用户最新脚本替代，不将此配置变化隐瞒为镜像瘦身变量。
- commands/migrate02.py SHA `9104c7fbc9f9dc802ba3f3623fc718c17a808e6195fd894f9d01360f8e840bad`

- commands/verify-final.py SHA `f514041ca2e028ac77bf6d4f38eb1b6e1aa72f22edf0dec0379ee28c96e616e4`
最终独立验证包括最新用户脚本ecdb...不变、prefixOFF、8worker、24fresh-JIT+86服务结果、两条实际prompt>=32768、五树源码不变、无OOM/非法访存/MCCL/traceback，且源容器退役为running backup。worker /proc环境受setproctitle影响，不作不可靠的逐项等值声明。

## 精度诊断 incident slim005-c64-arithmetic

24项cold-JIT通过；20条既有minimal通过；扩展66题中65通过，C64-16题“Only output the result of 116 + 200.”在temperature0/seed0/max_tokens128/thinkingFalse下返回516而非316。两条34017token长输入均通过，无OOM/非法访存。扩展脚本按原冻结全对断言失败，候选未晋级，自动回退原容器/API（旧prefixON参数）。原始失败结果完整保留。此为新加入但未先测基线的算术fixture，尚不能归因为瘦身；必须按inference-accuracy-diagnosis做原路径同题/并发对照，不能修改答案或删掉失败题以获得通过。正式GPQA历史分数不因本题被重写。
最小C1原路径复现3次，仅用于快速判断原模型行为；源prefixON与失败C64/prefixOFF不同，不能把该探针冒充同条件最终对照。后续如需判断新增回归，将对双方冻结同prefixOFF、相同请求/seed/并发重测。
- commands/diagnose-c1.py SHA `e6246c68d523292a27e3aa3ff69fa0c3cf689ddd243a96d7d7a2c2ebc23feda8`

C1原容器复现3次均为316，source-restored API26476/ticks1157583206，prefixON；不能用不同并发/不同prefix结果判断瘦身归因。diagnosis02冻结同条件baseline：未瘦身原容器、同最新用户脚本prefixOFF、完全相同20minimal+2×34017长输入+C64，temperature0/seed0/thinkingFalse/max128。保持原66题全对判据及全部输出，source API结束只由精确lease控制，原环境内存保存；baseline扩展失败只作为诊断结果而非通过。先运行baseline再决定必要的candidate同条件对照，不盲目重启重复。
- diagnosis02/commands/baseline.py SHA `4d40699048fb0f1400e00720772a17b836ef90925603f098dc18eee2a472dad1`
- diagnosis02/commands/extended-regression.py SHA `bd38a69b926e9830c5cdc6edc5808197e48b56a649326453c8a77d171e47a2e0`
- diagnosis02/commands/lease-source.py SHA `c21db4b2a1f35913ab5b016c0a8ec658657fb9eb253a3ea3671f7582a8a643ff`
- diagnosis02/commands/minimal-regression.py SHA `c5f5efce11b01eef6ab0eda856f0eace0bb4e4170e5b339042fefe9261985ff4`

同条件原路径首次20+66全部正确，尚未复现516；不能据单轮基线就归因为瘦身。冻结原模型prefixOFF的3轮同64请求（仍temp0/seed0/thinkingFalse/max128），保存所有输出及实际正确数，仅诊断批次/数值变异，不改变原失败判据。
- diagnosis02/commands/repeat-c64.py SHA `87664d653f18652a7a4578e941916e30648df5ff3a1f0dbd04ec89746ca64589`

原未瘦身容器prefixOFF三轮C64原算术请求为64/64、62/64、63/64；第2轮相同case16再次516，第2/3轮case28出现228而非328。第一candidate63/64与source重复中存在相同错误签名，故“瘦身是该错误必要条件”已被证伪；精确算子/模型数值机理仍未定位，不称rootcause confirmed。初始20+66全对判据的失败继续保留，不能改写为通过。没有达到正式GPQA阈值失败的证据，历史87.37%保持原绑定。

validation03在再次执行前冻结新的运维fixture：原20条语义回归不变；2条34017-token输入不变；C64以唯一整数1700..1763回传检查请求隔离/格式/完成，不把非thinking加法能力当100%健康oracle。仍要求全部86请求内容/finish通过；先在未瘦身原容器测同一fixture，再对candidate完全同配置验证。原算术失败作为独立精度观察明确报告，绝不把新fixture当作原算术问题已修复或正式accuracy gate。24fresh-JIT数值检查和源码/400库精确相等约束不变；不改推理代码、权重、采样或抽取器以迎合算术题。
- validation03/commands/extended-baseline.py SHA `cd90cb2e7041f1db897ebb0c6c070105f2e9ad3a5286fba370ef1ddc8646c790`
- validation03/commands/extended-candidate.py SHA `bc2296c4db527f339593a2e235af3db65acfb5e315fba315448285703bb234e6`
- validation03/commands/minimal-baseline.py SHA `424b11ab7ba2cce81096d1ae1decc6d6b7ead2283038ead8e25b42fcea070752`
- validation03/commands/minimal-candidate.py SHA `88871d9e5cc5b55cf8d8434bdd4aa2eb3f16350aa30406f1d2ee9af44ff48da7`

validation03原未瘦身容器已按新运维fixture全部86/86通过（原20+长输入2+唯一整数C64）；先验基线已建立。candidate将按相同fixture、同prefixOFF/seed0/temp0/thinkingFalse执行，保持全对判据，不把它等同于旧算术fixture。原算术问题在source189/192与candidate首63/64中同签名复现，归类为原模型/栈C64输出变异；不声明其底层机制已确认。既有20回归与fresh-JIT24一直通过，未发现新增包装依赖错误。
切换沿用当前source baseline API45517/ticks1157641274的prefixOFF完整argv；不再混用最初ON的服务。两个restoration supervisor在最终通过后均retire；候选失败则当前OFF基线恢复。
- validation03/commands/lease-source.py SHA `1eb681b1e92c6ed6030cc4fe7e2c8228081be1504864b3d39fa86fa52e625d3e`
- validation03/commands/migrate.py SHA `f2ac4dda5108c9bc4302d0a0f6e9257248a451663fdb5d4671db0b42c6be2407`
- validation03/commands/verify-final.py SHA `55a0bf72f3ee381317eb106fe9742e543b45ae488cc4c5229de4fdfe2b3b3b33`

最终独立核验已通过，当前薄容器已接管原名。收尾只删除本次生成且已由Docker导入的重复13.63GB压缩layer，以及仅sleep的私有prep容器（精确ID2096e1ede2ac；不使用-v）；保留原source backup和snapshot，不清理共享卷/缓存/历史证据。执行前校验镜像ID、一层结构、layer完整SHA与大小、prep身份和唯一sleep进程。
- commands/housekeeping.py SHA `32d7caf8ec5b25a8f965e7aca04889b3252d06a4d9b6a8b63de16e56aa2bead9`


## 最终交付与结论

当前 `deepseekV4-flash` 已是瘦身运行容器73eedc5bc92c，镜像 `dsv4-slim:20261028-runtime` / sha256:510baaeb92b74ecb023701d5b06a66318e0ef778e45ff61a7e15cf4d495a0d8f。原容器63249a7da309保留为 `deepseekV4-flash-slim-backup-20261028`，容器仍运行，仅旧API退役；source snapshot保留。两个restoration supervisor均收到retire回执。源/候选挂载完全相同，未清理共享模型、源码或编译缓存。

| 体积口径 | 原环境 | 瘦身后 | 减少 |
|---|---:|---:|---:|
| Docker image inspect.Size | 30,839,171,746 bytes | 13,634,367,315 bytes | 55.79% |
| 镜像层数 | 38 | 1 | — |
| root du -sx（不含挂载） | 63,378,997,248 bytes | 28,911,587,328 bytes | 54.38% |

删除范围为历史升级/候选、旧SDK非运行部分、构建目录和安装下载缓存；实际editable源码、全部400个mapped二进制、五个Python树、当前SDK/LLVM及仍被使用的旧FFmpeg保持一致。原生mount parity通过，新增ldd缺失0。备份保留意味着上述镜像差额不能冒充宿主机已释放空间。

最终baseline和candidate均按同一prefixOFF运维fixture通过86/86：20条既有语义回归、2条34017-token长输入、64并发唯一整数回传。独立私有缓存24项fresh-JIT（8GPU×FP32/FP16/BF16）通过；原生FULL graph capture/replay通过；API health200，8workers，未发现OOM、非法访存或MCCL错误。当前13项模型环境来自启动脚本，镜像只保留8项平台环境；没有新增隐藏预设。用户启动脚本SHA ecdbb44508f2e7eb2d257d925de201565b4cf7f30b111d859c6814fb8f96a01d保持不变，使用用户已改成的prefixOFF。

边界：这只是运行依赖与运维最小回归，不是新的GPQA精度gate或正式性能等价测试。首轮非thinking/C64加法探针63/64的失败未被改写；原未瘦身环境同条件三轮64/64、62/64、63/64（189/192）复现相同516/228错误签名。因此瘦身不是该错误的必要条件，底层机理仍未知，作为继承的并发输出变异单独保留。新的echo fixture仅证明请求隔离和完成，不宣称算术问题已修复。

独立最终证据均位于远端根的validation03：
- result.json SHA `4868fb4ab193f54fc04c0d57e4f8cad3fe33b9f1273acde8b269cb4d33944bb5`
- final-verification.json SHA `08d02d1977fb9e99d255bf75f72cb5a708595313788bebf96f836e8bff503e2e`
- jit-smoke-result.json SHA `e88d826d0f3b12aa5cfa224f796a91782b28711cb68dba0c4b65df3dad7002bb`
- candidate/minimal-regression/result.json SHA `43eed2a1a0880e354015b12f8ff731a85def7f42693463f08929947c06697f6c`
- candidate/extended-regression/result.json SHA `c4de4420a091ca18f189f70ea2e9f5807aab82ae509eac685658b7c5d3002fa1`

回退：只停止当前精确API及关联workers，将当前薄容器改回staging名、backup改回deepseekV4-flash，再在backup执行未改动的当前start-model.sh；不需要回滚模型源码、挂载或权重。不自动提交/推送。

收尾完成：已删除本任务重复压缩layer 13,634,364,098bytes及sleep-only prep容器2096e1ede2ac（未使用-v），共享卷和所有回退材料保留。housekeeping-result.json SHA `c6a1c4b648a052fef3223223e8abe164b4d86312f4ef3651399ef382d5ed1569`。清理后再次确认current/backup均running、当前API health200。
