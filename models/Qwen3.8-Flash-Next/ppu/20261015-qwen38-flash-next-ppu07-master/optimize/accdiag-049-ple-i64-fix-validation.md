# accdiag-049：PLE state乘前i64修复、边界/graph和仅8010最小回归

## 授权与冻结计划

用户2026-10-20明确授权修复PLE状态kernel的64位地址计算，先边界和graph受控验证，通过后仅恢复8010小范围精度回归，再向flagos-ai/FlagGems-vllm提交关联Issue与PR。不访问8035/物理0–7、不重跑全量GPQA、不修改采样/权重/其他数学。模式inference-accuracy-evaluation minimal-regression，沿用inference-accuracy-diagnosis及key-operator-analysis；无正式gate。

源故障acc016保持incomplete/no gate。当前8010无listener，原容器运行中，PPU8空闲；只对8–15做资源门禁。基线库`/opt/qwen38-fgvllm-main-20261019-b4d3382` clean HEAD b4d3382bb04da4e0ab444849697865b4d5fcd86e，ple_conv.py SHA163ebcd33074941a65ba8767ad518a4cf38073833f4617d1e59edfe60bc4e03b。上游main fa78ddee4c3e78ce5047213ff0ef02acff34b2d5的故障函数仍相同；PR基于上游main，只改这一独立state kernel的乘前cast并增加限域测试，不把历史Plugin/FP32/QSA/Gems修改混入PR。

远端CASE=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-016-full-gpqa-ppu07-c64-fp32-fixed-qk-20261020；新D=CASE/diagnostics/accdiag-049-ple-i64-fix-20261020。所有命令先保存CASE/commands并核SHA；原故障证据不覆盖。修复使用容器私有`/opt/qwen38-accdiag049-ple-i64-20261020/fgvllm`真实源码副本，保留原安装不改，只给8010设置该副本/src优先导入。回退为旧PYTHONPATH，但不得自动恢复已知危险地址实现。

算子验证只在PPU8（逻辑cuda0）运行：原危险实现仅做有界地址探针，不真实越界；固定版检查10485/10486/11242及高索引、NULL0/负数/空请求、history读与写回、BF16/FP16/FP32/非连续layout、canary，以及capture后至少两次更新device indices再replay。预先核资源，不够则停止，不抢占其他负载；失败保全raw/状态/编译产物，不晋级模型恢复。

算子通过后，仅恢复8010一次；复用当前Plugin attention/MoE FP32、Gems i64/randn、QSA M16、normal_/index_select黑名单和047固定调优。新日志/observer root，不覆写旧目录；仅修改观察器配置中的路径/新source SHA等事实绑定，不新增数值埋点或改变数学。小范围冻结10新生成请求/C<=8/0重试：两次C1 doc2，随后C8 docs0/1/2/4/5/6/9/11，取本轮samples中原完整messages；temperature1/top_p.95/top_k20/min_p0/presence0/repetition1/API seed1234/原stop/max60000/返回完整token和prompt。这些是已返回控制题，不覆盖原C64更替或长难题，不外推198题分数。实际服务capture两类7/7和至少两次replay另核，输出异常保存后不补发/不重启。

短请求前台跟进，若实际超出当前交互窗口则复用现有heartbeat且只实质变化通知。终态保留服务身份、实际import/worker证据、完整HTTP/token/原样错误/图记录和源码SHA；不因局部通过宣称原GPQA已修复。Issue公开模型/硬件/版本、最小合成复现、根因及真实验证范围，不上传私有题目、完整模型日志或权重；PR用Closes链接Issue，并在Issue回链PR。

执行前冻结：CASE/commands/accdiag049-prepare.py SHA224af0224cc47d0387e46932902c18926905338ba4f0c5e3e6413ae23c2f4aa1；accdiag049-ple_conv.py（唯一state加载乘前cast+注释）SHA611e4bc04be29c654c0d40f67d735b37e7af4a01d8bfd15768a7df654a95e180；accdiag049-test_ple_conv_large_state.py SHA81a8743cc60f630c75536fd4650a4018301922d00fec15ff4382b3eb83c6995b。prepare命令`python3 CASE/commands/accdiag049-prepare.py`仅复制私有仓库并替换目标单文件/新增测试，核8–15空闲和镜像挂载；不启动服务。GPU pytest计划固定11项新增（3dtype×decode/prefill/spec及2empty/index-dtype）加仓库原有test_ple_conv.py，最高单卡大buffer约9.8GB，所需资源不足则not-run停止；不扩资源。

prepare已通过8–15空闲/镜像和mount一致/私有copy与源码SHA回读，未启动服务。原危险实现地址算术沿用048已冻结CPU位模式证据，不真实访问其溢出地址。唯一micro controller CASE/commands/accdiag049-micro.py SHA3de6c841f0f45a9e0293b8ea9e39f4bbec6fdb9fe9ec6287978f78fe104eb087；执行`python3 CASE/commands/accdiag049-micro.py`，最多1800秒，物理8，原始pytest日志D/micro.log与MICRO_STARTED/FINISHED。大layout测试channels129/history9/stride204800，实际stride边界同生产但channels缩减；graph每case固定三次动态换索引replay，无吞吐结论。

首轮micro：新增11项地址边界/3次graph/empty全部通过，但既有10240channels Decode和spec两项state exact比较失败，总29passed/2failed/21.42s；output数值比较已过，state mismatch1663/1023，最大4.6875/5。首次原始pytest traceback/log与编译cache保留；此时没有自动修改额外代码、放宽容差或启动8010，最小门禁为failed。后续只做安全低index1/2/3 A/B，不执行旧危险大索引：CASE/commands/accdiag049-safe-ab.py SHA0808069c00ee2361b17dde6b114d400adbc67c5255cb27bb5051ba52b981b13c，物理8/同seed73049输入/old-vs-i64各3次，保存CPU独立state参考、原始输入和全部输出PT到D/safe-small-index-AB-001。用以区分新增/继承实现问题与reference问题，仍0模型请求/0恢复，不隐瞒失败。

safe A/B完成：原版Decode三次state mismatch2432/2044/1790、spec1791/767/895；仅i64候选Decode1661/256/1530、spec768/511/766。原版prefill128/128/0、i64 prefill0/0/0。相同输入重置后差异数量仍变，证明并非只有本次cast引入的问题；支持另有原地state更新同步/编译实现问题，但尚未以单变量机制闭环，不自动增加barrier或改写算法。CPU独立参考不依赖原GPU reference。原始输入与18次实际输出、report共22文件已独立验SHA/大小；report SHA965c43186544a443227e2d1f27f47429f2e356b878a4a9062d8e49f2e92a05b4，manifest SHA59e89ee4e6d3cc90c2254a5399ef14c6e626343328076ff7a5f9dfcbb86cbabc。micro回执SHA9e51d97f9124db5528083b6c1747c780cbe6bff25d70db0e8047f867011d10ba。21份实际候选state TTIR全部为row load后extsi到i64再muli i64；地址修复已实际编译，但不代表其他state一致性通过。

PR整理仅给新增测试加SPDX/black24.8/isort5.12/flake8检查，kernel字节SHA仍611e4bc0不变；最终测试SHAcb149b6b7362da7b4bdece251dc89284cb070323f643853d6094370ca1b69109。保留首轮原始测试SHA不改，整理后只重验已通过的新增11项，不重试失败的原生产shape以挑选通过。公开草稿PR将明确29passed/2failed及原版A/B，不宣称最小门禁已过或模型已恢复。

安全GPU地址probe命令已冻结：CASE/commands/accdiag049-address-probe.py SHA83cbbe441c757b6fdfcdf46221fcc5c38f4e6b7899df057f73717cdcde0c3cbe，仅4元素scratch对比原i32与乘前i64偏移，capture+3次changed-index replay，不解引用任何大池/溢出地址；产物D/address-probe-001，不复用旧marker。实际算子大layout测试只跑固定版。

安全GPU probe已通过capture+3次动态换索引replay，row10486/11242/12000分别确实出现原i32负偏移，固定i64等于CPU；report SHA32961909c3d82bce27666540eecc71f9737daf9e97a80c06701989af4363cca8，large-state危险解引用0。最终仅重验新增11项控制器CASE/commands/accdiag049-final-new-tests.py SHA14f39e06054177961236e6b71cce61039a5d779c62fa998227b0c0e0aaeb192a，命令`python3 CASE/commands/accdiag049-final-new-tests.py`；生产shape两失败不重试、不改状态、不以本子集代替总门禁。

## 终态决策与上游提交

最终格式化测试11passed/2.04s，日志SHA693e393bd2a7a3a378af7be94dd8fb6e1bac6ddd78bdb2d7839a744f1fb364a6。新增9个大layout case各3次changed-index graph replay，共27次检查通过，另2项empty通过；不掩盖原combined 29passed/2failed。地址宽度修复在此范围通过，整体minimal-regression仍failed，**8010未恢复、0模型请求、0模型服务启动**，计划10请求未执行；保留原FP32/Gems i64/randn/QSA M16/黑名单/固定调优，不访问8035。

用户随后明确允许公开模型名、硬件/驱动版本和寄存器偏移摘要，不含题目、权重或完整内部日志。已创建[Issue #958](https://github.com/flagos-ai/FlagGems-vllm/issues/958)和[草稿PR #959](https://github.com/flagos-ai/FlagGems-vllm/pull/959)，PR正文`Closes #958`、Issue评论回链PR，PR已附加当前任务。base main fa78ddee4c3e78ce5047213ff0ef02acff34b2d5，fork ZenithJoyH/FlagGems-vllm分支`fix/ple-state-int64-addressing-20261020`，head a8d30bc17c1f213d91e1c432fdcbc453106c5347。仅2文件：state kernel早扩位+注释，以及新增合成边界/graph测试；通过GitHub回读完整源码和测试，精确等于本地实际验证内容。未提交本项目脏工作区、模型权重/数据集/完整内部日志，未混入历史适配补丁。pr_readiness=needs-revision/draft：原生产shape状态一致性失败尚待单独定位，不宣称可合入、模型精度修复或服务已加载。

最后CPU-only冻结命令先保存CASE/commands/accdiag049-freeze.py，SHA53bda6fabd2dd364beb057ec81e1706256b5168c73c2a13187d092ed81072354；执行`python3 CASE/commands/accdiag049-freeze.py`仅复制已有编译cache/候选源码/测试/patch、SHA核验原始PT和日志、记录发布回执，检查8010仍无listener；不启动服务、GPU或请求。新产物D/terminal-evidence-001，保留原失败日志和AB原件，不覆盖旧材料。

终态冻结完成：503份原始/编译/源码/发布证据独立SHA与大小核验；summary SHA5a1b5b409fd4694b873ee3228940c48e2af67b769835954aa08a176bbaf0a2b6、manifest SHAf03e54c05b330686b644001f2ea22413da653afcd71d27bcf540814310c39ef6、publication SHAd1cf4e24abcf1ff6121501e4454a6a9b513c8bd40bb40a240562e587f1b82038。原安装源码SHA163ebcd3未变，候选未加载模型；8010连接拒绝，无再次恢复。编译物为实际测试生成，21份state TTIR已归档；无性能结果或formal gate，旧acc016故障污染incomplete和acc015有效164/198 failed-score不改写，监控保持PAUSED。

结论：乘前i64地址修复在合成边界/graph范围已验证；生产通道state exact失败阻止候选晋级。旧版同输入低索引A/B反例说明另有原地状态更新一致性问题，尚不能唯一归因为同步或编译，不自动增加barrier/改写数学。等待用户决定是否继续定位该独立问题，再讨论恢复8010和计划中的10请求；不追加GPU测试、不自动重启或全量GPQA。
