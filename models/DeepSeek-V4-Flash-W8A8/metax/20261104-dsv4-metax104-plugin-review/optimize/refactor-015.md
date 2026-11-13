# refactor-015：更新Decode TopK PR，随后继续Prefill定位

用户最新明确授权：先更新Decode PR，再继续查Prefill；本轮允许仅对此PR提交/推送，先前不提交的限制对其被此指令覆盖。原DeepSeek整改容器/安装源码/服务/脚本仍不改，不更新其他PR，不合并上游PR，也不自动将Draft改Ready。

目标是[PR #1145](https://github.com/flagos-ai/FlagGems-vllm/pull/1145)，fork `ZenithJoyH/FlagGems-vllm` 分支 `dsv4/decode-topk-20261110`，本次API核验当前head `570da319cdd679aaa9157c7e7c9f647130b51e8b`、base main `3049b821d088f5566b825bdc564120249a26181d`、open/Draft。只做该head的非force后续提交，发布前/后独立核对expected-head lease；并发变化先复核，不覆盖。

待移植证据来自 op-006 的Decode-only隔离版本（op006-operator01/diagnosis16，22/22模型minimum通过，FULL graph/8rank/source identity齐全）；该完整私有FGV包含其他未合PR，不可把整包或Prefill新public路径带入本PR。先核对当前PR/main已有common接口和依赖闭包，选择最窄共享数学适配。继承的K1024不稳定和262K全长benchmark慢点原文/原轮完整保留，不用短行收益覆盖它们。

交付前：精确PR树的算子数值/公开dispatch/至少2新输入graph、相关原native tests/CPU标准、目标代表shape三轮SDK成对计时和原11全长shape三轮，保留失败及所有轮次。模块重排/新依赖必须复核真实导入，不把私有source旧结果冒充最新PR head实测。未完成fresh全GPQA/端到端及跨vendorCI如实保留；本任务是更新Draft代码及证据，不是签发全部验收。

采用当前AGENTS5.5：mx-104 dsh在本次宿主/测试容器PATH未发现且无dsh session/关联writer，沿用内置子Agent有限范围执行；主Agent负责规划/资源/源码diff及原生证据审查和最终发布。捕获22已22/22pass且fixture已得，全部自身模型/GPU退出，Prefill离线工作暂缓到Decode PR更新后；不重发捕获请求。


## Decode PR CPU准备26执行前冻结

GitHub connector已实际回读PR1145仍open/Draft、head570da319cdd679aaa9157c7e7c9f647130b51e8b/base3049b821d088f5566b825bdc564120249a26181d；connector源码读取确认当前common `_top_k_per_row_job`已具备portable稳定收集、CANONICAL_OUTPUT与最终index排序数学，故不需要迁入未合Prefill PR的数学。为核对完整独立闭包/标准CI，创建全新本地 `/tmp/dsv4-op006-20261112/pr-decode26/repo` 精确detached checkout；不改其他工作树/容器installed，不提交推送。checkout脚本 `/tmp/dsv4-op006-20261112/pr-decode26/checkout26.py` SHA `de67ac3c04a29f3dc5414873674bdb8b1ebb964b2352fe9a22e9206351e31f9b`，执行前记录。所有GPU/graph/model/perf留给父Agent审核后的专用执行任务。


### 最窄Decode闭包26实现前归档

父Agent已批准待验移植：只common TLE launcher新增C10的两个默认False constexpr metadata；当前主线全部数学helper、通用Prefill入口、MetaX Prefill公开wrapper不改。D16私有helper从Prefill模块移到现有Decode ops模块，不再依赖未合PR1141；模块初始化仍将common Prefill模块tle指向已有MetaX_SHIM而不改HAS_TLE，初始化时点从导入MetaX Prefill提前到导入MetaX Decode，需要最终GPU重新核验；D16的NUM_ROWS runtime改动不迁入；树fallback保留当前PR的fill_tensor，数学kernel字节不改，不恢复私有torch.full。

本地payload五文件（2生产/2现有标准test/1现有benchmark）：{"benchmark/test_top_k_per_row_decode.py": "57a66df397a4803b5a0757e6aedc2932bd25fd2dacb36f44490088e45662e08c", "tests/test_metax_api_alignment_cpu.py": "9947ccf3dbffdaca484abc6553fcf0dd00489035e06cb1f7b20d004c046902f0", "tests/test_top_k_per_row_decode_metax.py": "d4defcd8122a2d33588a1a10a62f5467b64fe2bcdd96bc7c03897d89381a4996", "src/flaggems_vllm/runtime/backend/_metax/ops/top_k_per_row_decode.py": "e4c31670b896e48cb539f344f1bf5d1a7d7c3a76d6bb8dd227a0506050dc8691", "src/flaggems_vllm/ops/top_k_per_row_prefill.py": "3a5d73bec483aba3b8dca4b75a264889e18922d4e6b00d97e397ffc9311801f3"}。构建脚本SHA `03fd6c55e18eae6786c49fbe264023d7fa779eadbb7bf5fd0cc17797ff699122`；应用脚本 `/tmp/dsv4-op006-20261112/pr-decode26/apply26.py` SHA `f46ce5dc31e418a1a2820625126dd51e6fdc83adcf2c41120a124a3c91f2f3aa`。精确head与完整clean-worktree/逐文件原SHA守卫后应用，仅本地临时工作树，不提交推送。将扩展原CPU metadata suite、MetaX changed-input数值/graph suite及独立9点模型域native benchmark；原11点262K benchmark字节/所有历史负结果保留，不以新短行覆盖。

纯CPU source closure/AST/defaultNV/17个实际helper参数检查脚本 `/tmp/dsv4-op006-20261112/pr-decode26/contract26.py` SHA `04c0683d1aa0235e4de77c0f43289ff3e61651469143d4ab57d72fc4510385d4` 执行前归档。初次现有检查中12 CPU API tests、66 native CI unit、exports registration与git diff-check已过；exports排序脚本因系统Python3.9不支持原生 `list[str]|None`报错，将用既有lint环境Python3.12重验；全仓no-torch check报告73条其他vendor继承违规，保留原log，不扩大源码修复，改用工具正式paths参数复核当前2生产文件。以上均CPU检查问题，不是模型或GPU故障。

CPU source审计初次在最后registry文件检查误列当前PR并不存在的MetaX ops/Prefill路径而退出，之前数学/默认AST/17参数检查已执行；现明确该路径必须保持不存在，并核验实际当前fused/Prefill unchanged。初始脚本SHA `04c0683d1aa0235e4de77c0f43289ff3e61651469143d4ab57d72fc4510385d4`保留，新脚本SHA `3f610d4336a8fd433d5a5f1c98394e8662b145bff5bbbb836c680c71dd7e6dda`；不改任何生产代码来迁就审计。

最终本地归档脚本 `/tmp/dsv4-op006-20261112/pr-decode26/finalize26.py` SHA `83ddb6580aa807aa0762d95f9ab75efef883996d498e73a529ced869169319ce` 执行前冻结：只精确临时树生成diff/完整source manifest/tar/独立rollback和PR标题正文草案，不commit/push；正文完整保留旧K1024失败/11shape三轮262K慢表并明确新exact-tree GPU尚未执行。所有lint/原生pre-commit现已通过，无依赖安装。

归档器在生成rollback字符串时将占位符HEAD误替换到Git字面参数HEAD，AST解析明确拒绝，未执行回退/提交；source tar与manifest已生成且保留不覆盖。新增 `/tmp/dsv4-op006-20261112/pr-decode26/finalize26b.py` SHA `4a10d62c3ae07a0de6eb1283e53d961a783b5258ec7ce68a3e0bcf6fc3ef3bb8` 只读逐项校验现有tar/manifest与当前源一致后完成剩余独立产物，修正独立placeholder，不重建旧tar。

### 新远端私有PR树CPUstage执行前冻结

唯一新目标 `/opt/dsv4-op006-20261112/pr-decode26`、产物 `G/pr-decode26` 均必须不存在；先将脚本、4.8MB完整源码tar及manifest/diff/CPU回执存至现有G/commands新文件，逐SHA验证，再测试容器中仅stdlib提取/逐文件SHA/直接CPU API 12和native CI unit66检查。脚本 `/tmp/dsv4-op006-20261112/pr-decode26/stage-pr-decode26.py` SHA `61e2a02eba9ae0c3391828f14419c6a47a8a5681290129d3645316b600599245`；source tar SHA200317586b89078905d9b416958533b8d2e258f51ba06deae4d8728353883ba7/manifestSHAb5bc0afcfb70cf5345c67ae1f2f0e6664fda252cc1f4d2dfa271bdf207b0c258。无任何包导入/GPU或模型/安装动作；原installed、baseline、C10、23和其他PR不变。

远端CPU stage26在解包前安全守卫拒绝仓库原有3个instruction symlink（.github/copilot-instructions.md→../AGENTS.md、CLAUDE.md/GEMINI.md→AGENTS.md）；只创建空O目录，未提取源码/未运行测试/无GPU，冻结旧脚本不改。新增stage27 SHA `ada7be3ba9e6c20464059fa2dee1999173e99cf1658de22208f3b965faf41cf9`，要求O仍为空且R不存在，仅允许这3个精确仓库内链接，其余必须regular file，仍逐项contentSHA/禁止路径逃逸。保留stage26失败回执后继续同一个CPUstage，不修改生产源码或重做模型请求。

### 父review追加：当前PR实际Prefill初始化边界

当前PR没有MetaX ops/Prefill模块，原公开Prefill来自fused/__init__.py→fused/top_k_per_row_prefill.py。该模块_generic明确指common Prefill；_install(127–134)修改tle/HAS_TLE/final_select/merge线程上限/geometry；public(173–183)调用ensure_tle后按N16384阈值改block512/1024。新增Decode模块只在import时提前设commonPrefill.tle，不设HAS_TLE。正常首次Prefill ensure会重新装原Prefill自己的shim；原Prefill/Decode两个_build_shim、cumsum、final_select和_install AST完全相同（各自_generic不同），仍不能据静态AST宣称真实初始化时序无影响。GPU需增加公开Prefill非回归sentinel，覆盖Decode先导入/先调用与Prefill前后，记录有效HAS_TLE/tle及输出/graph。

私有helper row_starts分支为保持D16完整AST同源暂保留；本PR唯一实际调用点严格传None、ROW_START_ZERO=True，不导出、不注册、不宣称新增Prefill域。helper任何nonzero-start调用均非本PR新增支持契约。未来要收窄签名须独立重做launch/AST及GPU，不在本轮已冻结树继续改动。初始化只读审计SHA `33751ca89e2e40df854a16694e92b49daa277916de5b9153aeac404fa603ac17`；细项源码SHA/精确函数行见同JSON。


## Decode PR CPU准备26交接完成（尚未GPU验证/未提交推送）

精确当前head570da319cdd679aaa9157c7e7c9f647130b51e8b后的本地临时树 `/tmp/dsv4-op006-20261112/pr-decode26/repo` 仍detached/未commit/push。真实增量5文件（2生产、2现有test、1现有benchmark），250插入/10删除；没有增加生产文件、public API、数值kernel或未合Prefill模块依赖。生产增量：common launcher两个默认False metadata；MetaX Decode ops内部搬入原host helper并采用D16 public guard。其余数学/原tree host+kernel/通用Prefill入口不变；所有相关路径均用AST及完整文件SHA独立对照。

本地通过12 CPU API tests、66原生CI unit、17 K族实际host launch参数、默认NV/TLE常量折叠AST/完整D16 launcher/helper/public AST同源、注册导出/marker/yaml/两生产文件no-torch、Black24.8/isort5.12/flake8 7.1和原生固定pre-commit。保留初次Python3.9工具版本失败、全仓73条其他vendor no-torch继承违规、CPU审计路径误列和归档rollback占位符失败；各自修复仅工具/CPU编排，不放宽生产数值或断言。旧K1024稳定性失败及11shape×3完整262K慢表仍在原PR正文，建议草案完整原文保留后追加，不把新bounded数据覆盖旧表。

测试容器实际新私有树 `/opt/dsv4-op006-20261112/pr-decode26` 已CPUstage，外部 `G/pr-decode26`；1272源码文件逐SHA与本地归档一致。容器12 CPU API及66原生CI unit亦完整通过；未import真实Torch/FGV/CUDA、未安装/启用、未运行GPU/模型/性能。stage26原始安全拒绝三个仓库内instruction symlink的失败已保留；stage27精确白名单后仅CPU解包完成，没有重放stage26。包SHA `6f18b820316d50f66de1bf38ae835b7d0ce39872de1672068f611d72c1e383e6`，完整源码SHA `ede29ebe7d074d7c736eeec8c66b3c16dc7d88cf502d09deed320457314ca83e`，source manifestSHA `b5bc0afcfb70cf5345c67ae1f2f0e6664fda252cc1f4d2dfa271bdf207b0c258`，source tarSHA `200317586b89078905d9b416958533b8d2e258f51ba06deae4d8728353883ba7`，容器resultSHA `d212efd81680140bbdf283416a561299dd382a26d19a9f7e95a5e53f7bf35eb1`。真实增量patchSHA `be9b9592d0b8b6e6bdedd17f9ce2862257b883b1248c74e39d3fa5c00c731912`，本地回退脚本SHA `97a7b32d1ab75544855b99a5eafc598af963a92c9b7e6adf5a8bbe7d78e127d1`；回退只针对新local临时树5文件，执行前逐SHA和原HEAD守卫，未执行。

交接路径：`/tmp/dsv4-op006-20261112/pr-decode26/{result.json,candidate.patch,source-manifest.json,contract-result.json,initialization-audit.json,checks26-*.json,suggested-pr-title.txt,suggested-pr-body.md,rollback-local26.py}`。精确PR树新10组GPU参数测试（每组至少2changed-input replay）、9点模型域native benchmark及原11点full-length benchmark都只是代码准备、尚未执行。旧D16 22/22和71/82原生算子证据不自动复用到新wiring；GPU需按父review同时加现有公开Prefill路径初始化前后非回归sentinel。NV GPU/跨vendor CI/fresh GPQA/E2E均未测；保持Draft，不宣称解决262K全域退步或Prefill根因。


### exact PR-tree GPU28 执行前冻结

新独立45分钟预算自2026-11-12T07:20:11Z计（包含准备及cleanup）；任务launch停止截止08:02Z，预留180s精确清理。不延用旧capture预算。只测试R/pr-decode26 exact1272文件 manifest b5bc0afcfb70cf5345c67ae1f2f0e6664fda252cc1f4d2dfa271bdf207b0c258，不改原生产/PR。G/pr-decode28新唯一根；先运行原生quick/MetaXfocused，任何失败保留并停止晋级。原生K1024不删；full11若继续执行原core/cudagraph/warmup25/iter100三完整轮；后续supplemental/target9/sentinel另冻资产再执行。host保存完整mx-smi/docker-top(pid,ppid,comm)/GPU报告PID当时proc status/stat/cgroup/exe，未知归属STOP；inner仅自己精确PID/ticks子树TERM180→同ticks幸存KILL，无killpg。当前预检8卡全idle，source无python/EngineCore，镜像挂载匹配；每job再核验。源码前后全1272SHA，实际import须R/pr-decode26/src。

- 新脚本 `/tmp/dsv4-op006-20261112/pr-decode28/entry-decode28.py` → `G/commands/entry-decode28.py` SHA `36847cd115d93fcd537bf699197cbc0f30bf2ff35e438ddc2200a80acc5032df`。
- 新脚本 `/tmp/dsv4-op006-20261112/pr-decode28/host28.py` → `G/commands/host28.py` SHA `25b6817f37f75171710b68c8843aff3788c9dad0c50b189124dc92cd7877d396`。
- 新脚本 `/tmp/dsv4-op006-20261112/pr-decode28/inner28.py` → `G/commands/inner28.py` SHA `2bf6ace3fa010885d2d57518617e1d06f9b67e5538af17bce245db89d965be92`。

- 上传控制命令 `/tmp/dsv4-op006-20261112/pr-decode28/upload28.py` SHA `eed38ee0a0a20d9257ad6679d3c4050180327884c9948647c2418dfc8a5a2c19`；仅xb新增G/commands三脚本/asset清单及新G/pr-decode28。启动命令 `python3 G/commands/host28.py quick`，stdout只写新root/quick-launch.log，后台PID/ticks在host-process.json核验；不重放旧任务。

#### GPU28 后续job assets29（执行前冻结，不改运行quick资产）

补充两进程dp/pd公开Prefill/Decode初始化序列、I32/I64/16640/16641/17024/32768 pitched input+strided output、padding/输入不变、公开真实GPUkernel、capability0新进程、fixed9四路径SDK/FGVI32及I64转换对称计时，每shape3全轮，原bounded valid128另列。不改生产。独立supplemental中K1025/next_n2按原fallback，只查公开数学不重写断言；未验证device1明确未覆盖。
- `G/commands/supplement28.py` SHA `cf5bee02f8a1b3759eda60e4ecf0866fee66083c84c8d260a15a38099ca762d1`。
- `G/commands/sentinel28.py` SHA `bc1257c910f353ac5486551adeead0627ac226a0323711aaf003c0a9d47bf0c8`。
- `G/commands/fixed9-28.py` SHA `cf5a8d5220135a6a26620f300d8ceb463cccd734f6529b8e43d8bb317c7cfbe7`。
- `G/commands/inner29.py` SHA `3f813dd117ff7ac5ce7bc2eca064142edafbe329205f556e2af54d77c2000df6`。
- `G/commands/host29.py` SHA `21c5751c9521f6a9249c04f1b644472b966d7098bc6fa90d5e0388a858021262`。

- assets29上传脚本 `/tmp/dsv4-op006-20261112/pr-decode28/upload29.py` SHA `e173409f199b7aff71d791edfdd28b51a98b3694031e90baec5ec5775f6f584a`；仅新命令xb，不改任何现有执行脚本。

#### GPU28 exact-parent/revert性能对照 CPU stage30及执行资产

从本地Git HEAD570da319精确git archive（不含未提交5文件候选）建立test容器私有R/pr-parent30与R/pr-revert30，1269regular+3原指令symlink严格whitelist，完整逐SHA；不改R/pr-decode26。fixed9采用原Benchmark CUDAGRAPH20ms三轮，full11每role严格selector仅test_top_k_per_row_decode、core/25/100、3独立完整轮，native --record json/--output 指向每job新路径。该B为PR原头，不是旧项目原适配baseline，不混淆端到端基线。所有job还是原45min共同deadline。
- `G/commands/stage-head30.py` SHA `c01bff5d117d38188362c8e85692a54b21203e308d2b8d06fb8a605c8aa4c68c`。
- `G/commands/inner30.py` SHA `3acf670e7a834c5fb099385e5e35313a3015cf78a6ee4f34e1051743828d6b34`。
- `G/commands/host30.py` SHA `9dd0be801c85771f2c55fdf7e9b53c0a4de1e94bbd34bd0377e175400f84c78d`。
- `G/commands/entry-decode30.py` SHA `9e6660c015d1fdc22b36af42a7b149ad484b4c11045dcd9e3fd0142bedf93a50`。
- `G/commands/fixed9-30.py` SHA `c9b7c335ae3172c9d5c4e38b6c81a43cd4ab7a887462277cd7ab7afc11cc5623`。
- `G/commands/baseline-head28-manifest.json` SHA `de273f0f8688ca54bb97d55d3d4cdc70b38cc138c56f237091422c04a0702c05`。
- `G/commands/baseline-head28.tar` SHA `541688b5fd712db5643ebf2e991192fdbae7ef22ffcce7eb8bfc70acdefe9f51`。

- assets30上传控制 `/tmp/dsv4-op006-20261112/pr-decode28/upload30.py` SHA `fbaf60929475d73585597826345cfb3a010de1ceffda9e62135072be092e8fa5`，G/commands下新tar/manifest和脚本以xb写入；随后仅test容器执行stage-head30.py创建两个私有新根，无库import/GPU。

#### supplement11失败冻结与父批准的最小继承对照31

原supplement11=8fail/3pass/0skip，I32四节点不连续out被旧generic连续写污染；I64四节点旧generic编译int32/int64 ternary冲突；不是统一编译错误。原quick29/focused15均pass。失败后未跑性能/模型。父已批准exactHEAD两个I32/I64同契约最小节点与连续out初始化sentinel；若证实继承则作为Draft已知unsupported保留再继续支持域诊断。原8失败不删不改assert、不称stridedoutput通过。原测试未seed且未保存tensor，不能虚称恢复原字节；新fixture31用seed28031 CPU整数排列保存供B/C同输入严格对照，域/strides/valid0..full及全部原assert不变。

全局真实状态在entry31中记录commonPrefill/commonDecode及两个fused shim的HAS_TLE/tle/geometry/state/source before/after；两进程dp/pd sentinel只连续output。capability0独立新进程仅真实公开kernel+连续output两新输入replay，不重跑8unsupported；原11结果保留。预算仍原45min。
- `G/commands/fixture31.json` SHA `23493b780d13f0cd687e43bc79879f801b6d1236fb16be292b3ec384459ce05c`。
- `G/commands/supplement31.py` SHA `ffeb4358b21a852828a88381f7897f606af85d9e6728ebc99da594f7a0b5ccec`。
- `G/commands/sentinel31.py` SHA `3e53996ce3e8eb7c8e5871aa4cf17d49276c820f2245d1723b169a769a0e7f8f`。
- `G/commands/entry-decode31.py` SHA `2e1866de022516560a13c57cd4f5d6ab8cfa65928b7970e0a26eb0c011053f46`。
- `G/commands/inner31.py` SHA `530c70958f34988502ba70b5d26a4a93553065c084e05d67aa511f21e77b41e8`。
- `G/commands/host31.py` SHA `d5cd0ff7b5ab58ade4c31f882ff4e58618dfb829d9190b2c0abacdf821986af2`。
- `G/commands/capability31.py` SHA `cdc83f394b38f698f43af73abb2e2bc6968ad4531edaed35b2e748d3b27cb7ea`。

- 新assets31上传命令 `/tmp/dsv4-op006-20261112/pr-decode28/upload31.py` SHA `8d3661dfbea4e0c42e7aa1de7aa073ed5cba54dd84b8e46330f6b3f22e45ec49`；只追加xb。继承对照启动host31 baseline-inherited，父明确批准的诊断可预期保留rc1，不当性能晋级通过。

#### globals witness浅引用修正32（未改运行31）

运行31的before/after HAS_TLE/tle/geometry为标量快照有效，但`_state`字典直接持引用，若被ensure_tle修改，其before字典不能作为独立前态。保留31原文件/回执，不重放baseline；新entry32对_state做dict副本，仅后续job使用，原before-state字段限制在报告说明。
- `G/commands/entry-decode32.py` SHA `c6a25f6c67eafed486076ecb3daec60803fb0d4d82fe88a4b56e5de06d1365fb`。
- `G/commands/inner32.py` SHA `8343a905bae46f7869f6183631d2a14f309659a6fad4dea7bff96c94109f1215`。
- `G/commands/host32.py` SHA `3ffebac7bff9f0d43767881fdf2914dbab76d4932d36a37fda309d312dab2a84`。
- 上传 `/tmp/dsv4-op006-20261112/pr-decode28/upload32.py` SHA `f696e98515a8b4e70402f7d2ad6352f656b88e2b57523d97727a2579d97a99e7`，只新增xb。

#### 初始化范围补充33（原31冻结不改）

父review要求跨N16384全局tile阈值，sentinel33在新唯一job覆盖4096和16640两个width，每个按dpdp/pdpd公共调用，连续I32输出，capture后2次新输入replay；真实common状态每public调用后记录。失败则停止，必要只exactHEAD同case归因，不放宽。
- `G/commands/sentinel33.py` SHA `737ef0ee17c8470feb0faf406a6f6e964435ee40a1c35102ce9116cde75fd9f9`。
- `G/commands/inner33.py` SHA `0a8f81845de1d04845537cfa6630f03d9c0b106f3c57f4d2918e909030d6d7f7`。
- `G/commands/host33.py` SHA `9b892cd08cc68fb35db84bf92535090d9cc8608c8a0ecbe82e7b05625c33a12d`。
- 上传脚本SHA `c8717227256bc301ab27f25a4cff57cb8a5127cc01e8ed2d83e07958a59bec2d`。

#### 父验收继承结论后支持域串行协调34

B/C同新冻结fixture I32/I64两节点同失败，commonDecode HAS_TLEFalse→True来自原fused ensure；commonPrefill的HAS_TLE两侧一直False，新赋tle不等于误开HAS。原非连续out及genericI64问题列继承unsupported，未修复、不删除原8失败。父认可继续支持域诊断；协调34顺序：C连续sentinel dp/pd各N4096/16640 →C capability0连续 →B/C/R fixed9每点3轮 →C原bounded128 →C/B/R各full11三完整轮。新错误STOP不晋级；只支持域数据不代表原supplement全通过。所有job每次全源SHA/容器GPUownership/真实import/精确清理复核，仍07:20:11总预算、08:02停止，不能借旧8h。
- `G/commands/coordinate34.py` SHA `63a5aa16f3f3f03265798bdc50a83729beadaa49ea3db781384a6a3037e2790e`；上传脚本 `/tmp/dsv4-op006-20261112/pr-decode28/upload34.py` SHA `148a2f9be7b82a561832c1aa99c94ec903b8090abaa533c30a776087b25389a8`。唯一launch `python3 G/commands/coordinate34.py`，后台新coordinator34-process回执。

#### 终态独立native审计35（执行前保存）

只在协调34已终态+全8GPU空闲时运行，逐项汇总XML全部节点/失败/skip、raw nativebench/FIXED9三轮、真实dispatch/初始化global、源码前后SHA、fixture与浅引用限制、精确cleanup与原source脚本/source/test无模型事实，SHA产物清单写新native-audit35.json。若存在运行writer则拒绝，不重复运行审计目录。不把rc0单独当准入。
- `G/commands/audit35.py` SHA `4f50994ae4eee220455cf19f8f0af57511c6072b6263dead82d5e60557c412ca`；上传 `/tmp/dsv4-op006-20261112/pr-decode28/upload35.py` SHA `91f43e8b174794cff75936e1f90791719240ae43ace4292d52e98256ab35c369`。

#### 支持域input-immutability独立补充37

原supplement8失败在verify前置失败，不能把其未到达的input-immutable断言称通过；新4节点使用受支持连续output（storage offset8、前后哨兵），N16640 pitched/stride2及N17024 stride1，I32/I64、valid0/1/511/512/513/full，各capture+2新输入replay同时bytewise检查全部input backing和metadata不变。此补充不删改原8失败，device非默认GPU1未测仍列限制。只在协调34全部终态且GPU空闲后作为独立job执行，不与模型并行。
- `G/commands/immutable37.py` SHA `3c6cda87c4d107da726a38f56b99394d474372823aa441dd03791568201eb348`。
- `G/commands/inner37.py` SHA `739e7bd424e072284c0251bdcbc6d11c9e5df3ac24f14ad3f9071eb88aabd218`。
- `G/commands/host37.py` SHA `8fe17a6d27fc79d41ff028d36687174ec8e67804e15785d026955856be53f000`。
- 上传脚本SHA `2865d98367328640e86aaaf698de86d01b28c366815742d37c0b9c240fb4fb7c`。

#### full11 helper编排故障38（非kernel/性能失败）

原candidate-full11-1 rc1/0有效测量，首错base.py Config.query AttributeError，因entry32提前import benchmark使from conftest import Config绑定None；原错误stdout/XML/nativebench均保留，协调34停止并全GPUidle。父批准仅修正新helper38：pytest_sessionstart先assert原生conftest.Config已实例化，再import原benchmark并assert base.Config同instance、HAS_VLLMTrue、11shape；不改仓库/原CLI/测试assert。CPU Spy两情况：None时在benchmark import前拒绝、原Config实例就绪后才import且同instance，通过。三个新唯一candidate-full11-corrected1/2/3输出，不覆盖原失败、也不重跑fixed9。C3优先；第二同类错误不得机械重试。原07:20预算/08:02STOP不变。
- `G/commands/entry-decode38.py` SHA `c337e3733c9e3b40bbcce29d7c932d6421803785556a889b963bafc7358ec425`。
- `G/commands/inner38.py` SHA `d517928abb55e523179dcd57b951706893445289778b81883975baaba270c65f`。
- `G/commands/host38.py` SHA `f7e9c15f203c60d38f946581c4099e85938142b9b21851206152d7d20a0e6b0c`。
- `G/commands/entry38-cpu-spy.json` SHA `9d2e467f1fad3ae4fc9e3d71e99612dab5a3771e60d67e018c773825bc0997b0`。
- 上传脚本SHA `51db3ee145502dc994ad2cb659b42dabdd9fb3d566861bb87e1901469b91562f`。

#### corrected C full11新协调39及STOP命名空间

原协调34终态STOP作为失败证据保留；新39只观察/写STOP39，避免删除/复用原STOP。source/CLI/nativehelper38不变，新全长job corrected1/2/3全部保留原11慢点，三轮后补充37输入不变4nodes。额外full11 B/R尚未启动、预算不足将明确not_run，不能替代C三轮；fixed9 B/C/R已完整，不重复。新协调39 SIGTERM只触发STOP39并由精确inner finally清理，hardbudget仍原45min。
- `G/commands/inner39.py` SHA `1e675b17d82493ca9153ea649232f000f593a33b209e87bd742f724e4b6b2c97`。
- `G/commands/host39.py` SHA `2c495c5ce6148dc243260eef9080427f3bf29c87b21e0e3b6d522792c3cbc40a`。
- `G/commands/coordinate39.py` SHA `4dbb1775082b7da01b7054646e2504329a3c13af9417d94652d7f8468fc45cc2`。
- 上传脚本SHA `eead1c844a062f981aaf5f0d32a366b03bb405bb8aa057575b98f708a13d1d62`；唯一launch `python3 G/commands/coordinate39.py`，新coordinator39-process回执。

#### 最终审计40更新（35未执行，旧文件保留）

检查最新coord39终态/全8GPUidle后，原生XML/完整benchmarkJSON/graph/已知失败和fixture限制全保留；另通过test容器纯stdlib独立重算C1272及B/R1269regular全部SHA+原symlink，以当前actual source而非只相信inner自述绑定。新native-audit40.json一次写。非默认GPU1未测，模型/GPQA/E2E不在operator审计范围。
- `G/commands/audit40.py` SHA `34edf815fc58896cc11edba16564f72f43ea3f13babe633e0c66371aaac26dab`；上传脚本SHA `5354bee09a099d92c7d48a07beebaadc4c49b38deb5f07ae70a1cdac70a7acbf`。

### GPU28 最终交接（本子任务终态；此后停止本记录写入）

2026-11-12T07:57Z完成，在原07:20:11Z起45分钟硬预算内；主协调39和所有operator clients已退出，最终独立审计全8GPUidle，原DeepSeek/test容器无模型、仅原sleep/bash/容器init；没有暂停/重启/删除容器，没有对GLM发信号，没有修改原整改source/start脚本，没有PR/commit/push。Prefill离线23未launch；composition35仅CPUprepared、未launch；额外full11 B/R未跑（父明确优先C3与交接），不填空或拼历史。

最终原生审计 `G/pr-decode28/native-audit40.json` SHA `db55300abea4501a8acac4a30d2e702471816b3542592e729479eda9409c4d2c`，本地取回同SHA `/tmp/dsv4-op006-20261112/pr-decode28/native-audit40.json`。独立通过test容器stdlib重算C1272文件完整SHA `ede29ebe7d074d7c736eeec8c66b3c16dc7d88cf502d09deed320457314ca83e`；B/R各1269regular+3原symlink保持 `82db44b326fd96d2a6bf6b94a7b973cbc9dd86e3c8eab32c80a7e88e257a6b7a`。原source启动脚本SHA `7374987fa0f69252e45131edb63281bd42a11e17140106ce4e03372f0b0a3a48` 不变。

公开标准quick29/29 pass（固定K1024未删）、MetaX focused15/15 pass，后者14capture/28新输入replay；连续output的dp/pd初始化sentinel各1pass，均覆盖N4096/16640，每进程8capture/16新输入replay，真实global已记录Prefill HAS_TLEFalse→True/geometry64,512/N16640线程配置1024后Decode仍正确。capability0单独2pass、1capture/2replay，实际GPUkernel `_copy_or_fill/_row_local_topk/_row_reduce_pair`，正常路径真实public FGV命中`tle_top_k_per_row_prefill`及I64copy。补充37支持域连续output+offset哨兵/输入backing与I32/I64 metadata逐字节不变4/4pass、4capture/8新输入replay。device1/其他平台GPU未测，不能称全平台验收。

原supplement11结果保留8fail/3pass：I32四case不连续out污染/valid0出现index0；I64四case落旧generic的int32/int64 ternary编译错误。父批准最小exactHEAD B/C同新冻结fixture31各两节点同类失败，证明继承而非本次增量独有；不是修复通过，不把原8失败隐去。fixture31 SHA `23493b780d13f0cd687e43bc79879f801b6d1236fb16be292b3ec384459ce05c`；原未seed tensor字节未保存，31明确为同契约新fixture而非原字节replay。B31 before嵌套fused `_state`字典浅引用限制保留，common HAS_TLE/tle/geometry标量有效，后续32改dict副本。

fixed9为R1/8/64,N16640,valid512/4096/16640，B/C/R每点四计时路径各三轮，全81round/324latency留存；SDK/FGV I32与I64normalize分别报告，原Benchmark CUDAGRAPH rep20ms，effective warmup由Triton控制而非声称固定warmup20。独立CPU报告 `/tmp/dsv4-op006-20261112/pr-decode-publication29/fixed9-report.json`：C I32和I64norm各6/9达到SDK1.05，full-valid三点仍慢约10–12%；B/R四path最大漂移0.4071%，C短行最大spread5.3001%，全部原轮保留。原bounded valid128另9点成功，仅额外scope，不替代valid512契约。

完整原full11严格原selector/N262144/core/cudagraph/CLIwarmup25/iter100三独立完整C轮，nativeJSON各11点/共33，XML各1pass/0fail/0skip，所有慢点保留。有效C路径为 `candidate-full11-corrected{1,2,3}`；每轮真实benchmark22capture/220replay（不是新输入正确性验证计数），native_config_ready检查通过。33原点均慢SDK；按shape三轮median FGV/SDK为2.2853–7.9147，0/11达到1.05。不能以固定9改善替代全长缺口或宣称端到端收益；维持Draft。原 `candidate-full11-1` 的helper提前import导致ConfigNone错误/0有效测量完整保留；新38仅将检查延后到原pytest_sessionstart，CPU Spy两项及实际C3通过，不改源码/原benchmark/CLI；未重复fixed9。

本次支持exact PR-tree operator范围，不含新模型22/正式GPQA/E2E；D16历史模型正确性不顶替新树。父已独立复核nativeaudit、XML、source、dispatch与全33点统计，后续发布和新Prefill预算由父协调。

关键原生产物SHA（其余全清单在nativeaudit40）：
- `G/pr-decode28/quick/native.xml` SHA `3a0c9521591707473c4a3e4a06f570da54b949353fab178ef3e5a693d10b1040`。
- `G/pr-decode28/focused/native.xml` SHA `b8e6820bb861f579782340aaeb0a6051e544cc76c816711d8d65770654e044ef`。
- `G/pr-decode28/supplemental/native.xml` SHA `cd266485e6bcef6c25164bea2f0d620a0561f076f73016454850ef15dd154dd0`。
- `G/pr-decode28/baseline-inherited/native.xml` SHA `32861a2de233ff03fefe34be4deeaef252bbdef505538b94507d06f01da2f9dc`。
- `G/pr-decode28/candidate-inherited/native.xml` SHA `eae3a43a867c86c76061ca7ecc9fc369550ed9201ab966fc7f5d37da54f106f7`。
- `G/pr-decode28/candidate-full11-1/native.xml` SHA `396ecda1069f6dfb124f575961c19d2c4b5088dc8ebc153b73bad1d7aba50572`。
- `G/pr-decode28/candidate-full11-corrected1/benchmark-native.json` SHA `0300dca10aac8c328427e5b23e0f8c583f3d57f6efe2489b234a2d8976393d4f`。
- `G/pr-decode28/candidate-full11-corrected2/benchmark-native.json` SHA `481f124a476897130991c4a67365fd4a6daf8ad1c1fbdae0b9c4ddfd0860ec5a`。
- `G/pr-decode28/candidate-full11-corrected3/benchmark-native.json` SHA `09d331ee3fb60820eb161987cc87cc4dc1c5ff7fa5a2c0614ad91443c1879198`。
- `G/pr-decode28/candidate-immutable/native.xml` SHA `3cf5eec9fe7cda189419b6b5aa6b949b978367dcdf671262ec164dbab28c94dc`。

## 发布完成与主Agent验收

仅PR[#1145](https://github.com/flagos-ai/FlagGems-vllm/pull/1145)已按用户本轮明确指令非force更新，commit `9dd07431b4811409608436dec6fdde3bbdb0d574`，唯一parent `570da319cdd679aaa9157c7e7c9f647130b51e8b`，GitHub返回tree `2cbd1fc03d162e62e407bfcfb7603387e121299d`与本地独立temporary-index树一致。5个blob逐SHA核对；expected-head再次回读后带lease/forcefalse更新，未改变其他PR/未合并/仍Draft。PR回读head/title/body逐字一致，旧完整历史正文保留。原整改容器/installed/source脚本未动。

主Agent按AGENTS5.5例外4/5/7复核实际diff、source-manifest五文件、quick/focused原生XML及K1024节点、B/C两继承失败XML/source/cleanup、actualkernel/初始化状态/witness、fixed9和full11全轮表、独立最终C1272/B-R源码重算及all8idle。原生审计40 SHA `db55300abea4501a8acac4a30d2e702471816b3542592e729479eda9409c4d2c`，fixed9独立report `bcd642207222aa9c76d1795644c07c515dd622d0dede19d5e10efaf1023b989e`，full11独立report `a2cb14eb9ceff4ad2f8d05851526c2e9ed3625d7526d8e4924871c879be106da`。两metadata口径fixed9均6/9达到SDK×1.05参考，fullvalid仍慢约10–12%；full11新33点全部慢于SDK，完整三轮不丢。8个继承非连续输出失败、I64编译错误和首full11编排失败保留，未以rc0或新快点覆盖。无新exact-tree模型/GPQA/E2E、非默认卡/跨vendorGPU结果；composition35仅CPU准备。

发布外部回执 `/tmp/dsv4-op006-20261112/pr-decode-publication29/{published-result.json,published-pr-body.md,fixed9-report.json,full11-report.json}`；后续独立fetch已发布commit核对parent/tree/blob另追加结果。GPU28约37分钟完成、19份ownhost/controller精确PID均退出，执行者移交文档写权后由主Agent维护本节。任务转回op008真实tensor，使用新独立40min预算，不重启旧GPU28/捕获22或整改服务。

发布后独立fetch完成：新private bare库证明single parent570da31/tree2cbd1fc0、五blob与全部1272文件均匹配测试manifest；PR open/Draft/head/title、新全部三轮表格及原完整历史逐字回读通过。外部回执 `publication29/published-verification.json` SHA `7d50e39854520b8e90a85e6982c634530b5660d6a8f6c3e3d0d90d9c3b494ed1`，API正文SHA `9f3a438f8c0ca85fef9fb0ece438154231881f35e761cc002040b8e174fc9864`。原先本地记录CPU拟发布树现已由服务端Git树及独立fetch双重确认。

### 非有限partial-selection后续46：PR代码不变，新增已知门禁

Prefill诊断单行被复用为独立Decode接口输入（N904/K512/len513/58NaN），实际PR26公有MetaXDecode路径返回456唯一nonnegative索引，但将未写的-12345初始槽排序到前部，暴露partial-selection依赖输出初值/有效prefix填充问题。不是304重复行结论的直接Decode复刻，不推定真实Decode请求会遇到此NaN分布或E2E回退。父只读核对actual public source及common selector SHA与测试manifest相同，回执SHA `1378a579cf1bb22f96222a578bf607f8d93c1b46f8485afc8f0f5829f39f2ea1`。

#1145已补充该已知correctness gate并回读确认；仅PR正文metadata更新，head仍`9dd07431`/Draft，未新增source commit/push、未动安装。原全部finite quick/SDK各轮及旧完整历史继续保留，不拿新cornercase抹除，也不再仅称nonfinite未测。当前Prefill portable修复不会解决Decodecanonical此问题，Ready仍需后续独立修复与完整验证。新正文备份`publication29/published-body-nonfinite-followup46.md`。

后续Prefill私有portable修复已完成原22模型用例复验（long62/280 tokens正常stop）与离线审计50，见[op-008.md](op-008.md)。该结果不覆盖本Decode PR非有限canonical边界或SDK性能缺口；#1145仍同一commit/Draft，未额外source push/Ready/merge，整改安装保持不变。
