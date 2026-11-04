# eng-072：多图输入配置适配与原生链路核验

收尾：后继acc021／acc022证据全部归档完成，监控已产品确认删除，当前BF16／image16／encoder graph关闭的8010保留等待用户方向；无新服务或推理操作。

最终后继覆盖已齐全：同一BF16／image16多模态8010的[GPQA acc021](acc-021-full-gpqa-mm16.md)175/198＝88.3838%通过新gate；[ERQA acc022](acc-022-full-erqa-mm16.md)251/400＝62.75%，完整400图文题原生score及独立CPU证据审计通过，但无ERQA阈值／同配置baseline，不宣称开启16图前后等价。两项原评测全部退出、source／API绑定不变，健康空闲；本轮0新重启／smoke／encoder graph／8035／提交推送，结束monitor后保留当前服务等待方向，无新性能承诺。

后续完整文本精度覆盖：同一BF16／16图多模态8010的[acc021 GPQA](acc-021-full-gpqa-mm16.md)新strict175/198（88.3838%≥88%）及原生gate／独立CPU终态审计通过；9题60K空final计错、0真实HTTP超时。[acc022 ERQA](acc-022-full-erqa-mm16.md)正由原串行队列运行，无新重启或encoder graph启用；ERQA结果未出，不把GPQA通过外推任意多图精度／容量或性能。

2026-10-24 后续覆盖：用户另行授权同一8010／image16／BF16实例的完整C64 [GPQA acc021](acc-021-full-gpqa-mm16.md)及[ERQA acc022](acc-022-full-erqa-mm16.md)。两项预检通过、唯一串行controller已启动GPQA，ERQA等待；0新模型启动／重启／smoke，encoder graph仍关闭。终态分数尚未产生，不能以此条升级本页minimal结论；跟踪见对应记录与state。

## 终态：14请求多图最小回归通过，当前16图服务保留

2026-10-24 13:55:12+08原唯一driver自然退出，`FINISHED.json`／summary／156成员manifest完整；14:22+08独立CPU审计588检查通过，原36冻结输入、父8manifest成员、全部素材／raw HTTP／token／真实来源及当前source再次校验。没有首错、HTTP失败、空final、2048截断或重试；不混入旧eng071结果。monitor已由产品确认删除，任务结束，非暂停模型服务。

| 覆盖 | C1 | C8 | 结果 |
|---|---:|---:|---|
| 横竖异尺寸双图 | 2 | 2 | 按顺序红／蓝；C1均270 token，全序列相同 |
| 相同bytes换序 | 1 | 2 | 蓝／红，顺序随输入改变 |
| 重复图 | 1 | 2 | 红／红／蓝，重复项保留 |
| 16张唯一bytes、横竖异尺寸 | 2 | 2 | 16项红蓝逐项正确；C1均183 token，全序列相同 |

14/14完整HTTP200，C8真实8请求；返回183–483 token，完整token长度／usage／prompt、thinkend248069及EOS248046或248044、finish stop均核验通过。服务prompt6908／generated3856与全部返回精确相等；零额外推理。只计一次本轮启动、一次旧API精确SIGTERM自然排空，没有第二次重启或恢复。

语言graph两类capture各7/7；C8前native FULL1309，summary冻结时FULL1791，其中实际unpadded8／FULL184。该证明是当前原生调度dispatch结合冻结native graph wrapper，不是每rank独立设备kernel trace。encoder graph／encoder compile始终false，不声称encoder graph通过。

异尺寸和16图批次共16份（各8rank）真实BF16 Tensor调用链均为：`Qwen3_VisionTransformer.forward → MMEncoderAttention.forward_native → _forward_sdpa → torch_sdpa_wrapper → Torch scaled_dot_product_attention → /opt/FlagGems/src/flag_gems/ops/attention.py:flash_attention_forward`。函数源码SHA与冻结源及当前容器逐份相等，profile均恢复，0tensor值读取／额外模型执行。异尺寸grid形状[2,3]，query[1,480,2,72]；16图首次已有2图encoder cache复用，新增grid[14,3]，query[1,3648,2,72]（每rank2heads／72dim）。这不是丢失两图：完整请求16份有序素材、1153 prompt token及16项输出都已核验；不把缓存未重执行当来源缺证或声称所有16图都重新执行encoder。

三库canonical editable及完整Plugin／FGVLLM／Gems／engine source-before／after／当前完全相同，HEAD／index和BF16／MoE原始布局／PLE／QSA／index／index_put／randn等现有修复保留。当前API Host3459214／start553495020／argvSHA`646b86aec9182f0f5f53227e2880519d7d4dd7a5fbd7964b76d47417bf06fc2d`，8010 listener／READY／argv绑定一致，image16／video1、FGVLLM开关1、仅bootstrap PYTHONPATH；health200空闲，KV0／抢占0。没有访问8035、全量GPQA／ERQA、性能测试或提交推送。

原件仍在R=`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/eng-072-multi-image-input-20261024/model-regression-001`：

- `FINAL_SUMMARY.json` SHA`c88e8b6ac52c99338d89ea31e79f1c2342ee393554980f1d04bb40dc9746837f`；原生156成员`manifest.json` SHA`906c46b2d6fcd6bc11b4986463083a42599092f0b5b3cc53c3484f0e83793265`。
- `terminal-evidence-001/`保存原raw请求／响应／headers／token、素材、来源、日志及前后source；不覆盖或补写旧证据。
- `diagnostics/terminal-cpu-001/terminal_audit.py` SHA`5b841a722fc7dad6eef0458f52aa82c0681fe3ca2383a53e4f764a18eace78a4`；CPU回执`terminal-audit-001.json` SHA`fb1a46840a6b0f370edc83d28ee4172027dd9b996c894a3fb4cd63af3ead7e8b`；补充manifest SHA`1d39bb84d99b51cbdba664fd90769bfc84e5c0c2ec08ee49ff9f433b92e25531`。两份新增CPU材料已保存至全新目录并回读SHA一致，0新推理或GPU。

结论仅为所冻合成媒体多图minimal通过；不签formal gate、不外推ERQA／文本GPQA／任意尺寸16图C64容量或性能。保留当前BF16 image16的8010等待方向，不自动恢复全量评测或停止服务。以下为执行前和中途历史。

## 新授权：仅一次8010重启及14请求多图minimal（执行前冻结）

2026-10-24 用户明确授权仅重启8010一次应用image16，覆盖异尺寸／换序／重复图／16图边界，核实际视觉Attention及graph replay。保留BF16及全部修复，不启用encoder graph、不访问8035、不跑全量评测、不提交推送；此前“不重启”仅属上一阶段。当前精确旧API3895409／start552602448／argvSHA e58dee3a67ecd27a839617e5010c2d3e37eab4d994401fec9cc406b69b4a38b2只接受本轮唯一SIGTERM自然排空，不追杀旧PID、不强杀或自动恢复／二次重启。

使用本地accuracy `minimal-regression`，bundle SHA`1ed06a57f1f6e1ef39fb7fd872f579122b098a18f0255ade0a1160d6432c2b66`。inventory确认PPU-07；首次连接工具在沙箱内RPC失败，外层同一`connectivity-check --limit PPU-07`完成ok3／changed0。新只读preflight确认旧8010健康空闲、候选及父8manifest一致、完整三库／engine source不变、优化容器同镜像及`/mnt:/mnt`RW唯一挂载。

运行子目录R=`E/model-regression-001`，唯一控制器`R/commands/model_control.py --mode run`；仅prepare→单次launch调用，不重发。控制器SHA`b4c7656453e38a5328e17ba34affd7648e1d7f08cd220d91d3c435e1f3a17f1c`；10文件传输包SHA`6549f59b4378166ad4e05b6847665c37db36bad1943052fd28d40403d7f877c6`，preflight SHA`6997392afea624ae7a2414586beb34670dc9632976b0bd72fac1d77c03517d97`。先以stdin传包、核整体SHA及白名单／拒绝已有R，保存commands后才执行`--mode prepare`；核PREPARED／frozen inputs／argv／fixture后再`--mode launch`。本地准备目录`/private/tmp/qwen38-eng072-runtime.ChYYeC`。

固定14请求，max2048／timeout600s／0重试／0隐藏HTTP预热：

- 6个C1：异尺寸红／蓝双图2次；相同bytes换序蓝／红1次；重复图红／红／蓝1次；16张唯一bytes、横竖不同尺寸、交替红蓝图2次。
- 前两类重复case的完整token序列各需一致；输出颜色按输入逐项精确匹配，不忽略重复或省略。
- C1正常、8rank实际视觉来源及native语言FULL dispatch≥2后，仅8个C8：异尺寸／换序／重复／16图各2。需要实际unpadded8／FULL调度证据。
- 16图cap不是任意大图或C64容量承诺；不新增负向HTTP／正式题／性能请求。17图拒绝由上一阶段CPU契约覆盖。

argv与已冻结candidate逐字相等，仅image1→16；video1／像素／采帧／语言graph／BF16／其他参数不变。运行证据与固定调优日志换新R，compile／tuning缓存用独立新根`/opt/qwen38-eng072-multi-image-20261024/cache`，不清旧缓存；PYTHONPATH仅R/bootstrap，三库canonical editable无覆盖。pin047／黑名单保持。

一次性视觉forward观察复用eng071方法：每个C1 case首次已有forward执行内`sys.setprofile`只读函数对象／源码SHA／Tensor元数据，不读值、不额外执行算子，finally恢复profile；非逐kernel设备trace。换序／重复图复用相同bytes，原生多模态cache可以避免重新encoder执行，不能把这当来源缺证；要求新异尺寸及新16图批次的各8rank nativeSDPA→Torch wrapper→Gems Attention真实调用。encoder graph／compile仍false，graph证明仅指语言capture及实际replay。CPU控制器3项测试（含5种HTTP／语义错误分支）及observer1项机制测试通过，不当硬件结果。

首HTTP／输出／observer／启动异常即停止新阶段，等既有C8在途自然收集，冻结raw bytes／headers／完整返回token／原错／源码／日志／manifest，不自动修复、恢复或追加预算。readiness40min，持续编译不因shm60s提示判死锁；保持当前8010终态等待方向。以下为上一阶段证据。

### 13:18+08 唯一重启已执行，加载中

R已prepare并独立回验36冻结输入、14请求／16唯一素材、换序／重复bytes关系、精确candidate argv及encoder graph关闭。PREPARED SHA`3cb9c517ff6f73068c9626a83164111fb6c6838a2bc94afdebd2d925eabc37dc`，requests SHA`feabc28fb9dfaf51f5807ede3baaac8c8ee8a2a2794fbab8b46e5759b2c516c6`，launch SHA`599757578c9a355a3c5bd0d7b89ae809ebf3182e88d8047774dd14098da11e59`。唯一driver Host3457933／start553494659／argvSHA`6a8571c93107e12244deee9611ab1f7cc0c98f611a6da9c5b2777dac5ad900ea`。

1792819121.4859529仅向旧API精确SIGTERM一次，1792819123.5849395原owned tree自然排空；只查物理8–15无人占用后1792819123.637943单次启动。新日志确认image16／video1、BF16、encoder graph与compile false；8rank启动来源日志已出现，但截至第二只读快照尚无READY／新HTTP，权重加载推进中，不作新服务健康或回归通过声明。

原PAUSED heartbeat `qwen3-8-ppu07-mm-eng071`已通过产品工具更新为本轮`qwen3-8-ppu07-multi-image-eng072`／ACTIVE／30分钟，id不变，范围仅只读监控原driver；正常推进／无变化静默，只通知完成／首次失败／明显停滞／需处理，终态暂停。没有恢复旧eng071控制器或旧评测。依据精度技能的长任务监控要求使用既有heartbeat；产品文档只用于核对调度功能，不作为模型证据。

## 范围与执行前约束

2026-10-24 用户要求先停止GPQA／ERQA，优先做好多张图输入适配。两项评测仍在准备阶段，未创建或启动新evaluator／controller，新增评测请求为0，无需停止任何模型进程。原eng071 monitor保持暂停。

目标仅PPU-07、`qwen3.8-flash-opt-ppu07-20261015`、8010／TP8物理8–15。保留BF16及全部算子修复；不重启、不启用encoder graph、不运行推理／GPU／全量评测、不访问8035、不提交推送。先核原生实现，再准备配置；没有缺失实现证据不重复编写视觉数学路径或修改vLLM。

外部产物预定：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/eng-072-multi-image-input-20261024`。仅新建、拒绝覆盖；CPU命令保存在该目录commands下。当前本地准备目录`/private/tmp/qwen38-eng072.RlMlTC`。

## 已有证据与候选

当前8010的`--limit-mm-per-prompt`为`{"image":1,"video":1}`，是明确的多图准入限制。原生继承链为Plugin Qwen3.8 → Qwen3.5 → Qwen3VL，处理器复用Qwen3VL；Qwen2VL ProcessingInfo声明图片支持数量为None（实现层无固定上限），但实际准入仍受用户配置限制。

原生实现逐图读取`image_grid_thw`生成占位符、把拼接视觉特征按各图grid拆回tuple，DeepStack按逐项长度拆分，MRoPE按prompt offset排序逐项生成位置。待用当前实际源码的CPU抽取测试验证1／2／16图、不同尺寸／顺序和17图拒绝边界；CPU替身不代表视觉模型／设备验证。

候选仅将image上限1改16（ERQA原生400题有113道多图，最大16），video仍1，像素预算／采帧／BF16／graph／其余argv不变。不拼图、不丢图、不改样本或自动启用encoder graph。16是服务准入上限，不是C64下任意尺寸16图显存或性能保证。

## 验证与交付状态

执行前冻结命令：`commands/prepare.py` SHA256 `d7a815750e630d6f0b31f97ef2c0001eed4a901310da1c2a819fede170b8d37a`，`commands/cpu_contract.py` SHA256 `35633277c1cf823696eef7e9000e70fe124defa6e98adcafde2a5f90b3f48836`。通过SSH stdin tar只传这两份已核SHA文件；新建上述E／commands，拒绝已有E与非白名单成员，再执行`python3 -B E/commands/prepare.py`。只读取精确8010身份／health／metrics、CPU source probe和AST抽取方法；CPU用空CUDA_VISIBLE_DEVICES与空VLLM_PLUGINS，不导入vLLM或模型，不调用设备API。产物包含原argv回退副本、NOT-APPLIED候选、前后源码、CPU回执与manifest；无可执行模型启动命令。

## 终态：配置就绪未应用，56项CPU检查通过

2026-10-24 CPU核验在目标容器完成（epoch1792815701.8336973）。直接读取当前安装源，抽取原生方法执行CPU测试：原image1限制能重现2／16图拒绝；候选16接受0／1／2／16、拒绝17；1／2／16图异尺寸视觉特征切分与顺序、逐图占位符长度、逆序到达feature按prompt offset恢复MRoPE、位置总长及delta、DeepStack逐项长度／顺序／文本位置为零，合计56项通过。视觉塔是标记CPU数据替身，embedding merge使用CPU参考替身；不导入vLLM、不加载权重、不调用GPU，不把此结果当视觉数值／模型精度或完整前端验证。

没有发现需重复实现的Plugin多图数学逻辑，因此三库及vLLM生产源码均未修改。当前模型文件仍`9e74fb34a833611b1a00df18f3710bd63853acd5997f41274b5e5258832f94fe`，前后完整source probe逐字相同，三库HEAD／index／既有BF16及算子修复保持。原生Qwen3VL源码SHA`39097f612de0d84d1ce7e408ce91447f3521e3cfeafb6792c4c5d02dcdce5d2c`，处理器计数校验SHA`4deba006b7975ba86cb89386650420320d7e9d571c23df7e8c0f444ae1ffe61f`。

E下产物：

- `launch-before.json`：原完整argv回退副本，SHA`352d17d72c88e77939a2fed51f360d95be861159802e54d899a2683bc0eae451`。
- `launch-candidate-NOT-APPLIED.json`：只把image1改16，video1及其他argv精确不变，SHA`ed9cfdfa939366c13a8d8c726ceb2e8ad5f2c5280468cdfd50efeb7d3f8cdb4d`；不是启动脚本，不自动执行。
- `CPU_CONTRACT.json`：SHA`207a388843c868fa6f7f0c4e651282d7c0e971c3bede84a82b737ba1352d5a7a`；`SUMMARY.json` SHA`e6b96c68cd4577b4f1c32751706cd5a3610fc90245e2e5b530cd04e77117d75a`。
- `source-before.json`／`source-after.json`均SHA`7a0ace9c0c9f74f8bd80f909fbd9dcb35695a3615592ce37eef77f9c849dd335`。
- 8成员manifest SHA`1462ba6f11cf24440ab2d5a7bcd547c17b343d575b192dcf805fc626323e1049`，单独SSH只读回验8/8一致，并核当前/proc argv仍原配置。

8010仍API3895409／start552602448／argvSHA`e58dee3a67ecd27a839617e5010c2d3e37eab4d994401fec9cc406b69b4a38b2`；health200空闲，prompt1944／generated1140前后不变。0服务启动／停止／信号／推理／GPU测试，encoder graph关闭，未访问8035或提交推送。首次传输因macOS AppleDouble额外成员被白名单拒绝，E当时尚未创建；禁用COPYFILE元数据后按原SHA两文件交付，没有覆盖旧证据或生产文件。本地无numpy不安装依赖，改用目标容器现有CPU依赖运行该契约。

现服务仍image1，**16图候选未应用，实际多图回归`incomplete`**。新配置会影响启动时多模态最坏情况预算，不能承诺16图任意尺寸／C64显存或吞吐。后续需用户另行授权一次8010重启，然后验证实际多图视觉Attention、capture／至少两次replay、异尺寸／换序／重复图／1-2-16边界／真实C8与完整raw-token；不自动恢复全量GPQA／ERQA，不继承eng071单图minimal或旧文本gate。
