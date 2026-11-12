# fg-review-fix-006：FlagGems PR 验证缺口修复

2026-11-09，用户要求修复 FG-R1/R2/R3。本轮只修改实际安装 FlagGems 的 tests/test_metax_linear.py、benchmark/test_linear.py，不改生产Linear、kernel、配置、公开API或模型启动参数。先在已验证独立容器GPU7验证，再发布源 BGE-M3，无服务重启。基线为FG完整patch4fac55ee…，同时重新核验三库/安装/模型及挂载。

## 验证契约

精度技能 minimal-regression，本轮为纯算子/测试维护，prefix cache不适用；不新增模型graph或正式GPQA/性能声明，不恢复已取消的MBT实验。覆盖普通/子类Parameter、FP16/BF16/FP32、范围内/外、非连续权重与bias、metadata/loader/storage/value保持，grad/no_grad/inference选择分支、1D与非连续输入、非法metadata仅检查预执行predicate；零值、抵消、Q/W/bias NaN/±Inf，保留独立FP64oracle和原容差。适用标准tests/test_linear.py也运行，并保留原graphcapture/两次新输入replay。

真实vLLM BasevLLMParameter另由外部integration.py验证，不向基础算子单测引入vLLM依赖；构造器TP rank/world仅metadata限为0/1，不冒充真实多卡集成。

性能复用仓库 benchmark 的cudagraph模式，对默认pool/扩展pool比较，四(N,K)对 × M=1/31/32/33/128/1024/1025 × bias开关 =56shape，每组3轮完整保留。两侧均同公开FG wrapper及IEEE计算；只通过临时selector override强制默认pool，host override不计入replay。记录实际launch配置、首次调用wall时间（包含JIT/tune/cachelookup，不当作纯调优时间或稳态收益），随后同规则预热3次再graph计时。独立SQLite数据库与TRITON缓存位于case，不清理用户缓存；所有回退如实呈现，不据包含默认候选就假设不回退。

## 外部证据与执行

根 `/public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261109-bge-m3-fg-review-fix-006`。commands工具在执行前保存并记录state.yml中的SHA；source/candidate原文件和指纹位于before，发布要求原patch/逐文件SHA无漂移且绑定VALIDATED.json。生产文件始终逐字比对不变。当前准备中。

首次prepare在原始Mounts列表相等判断失败，未部署源码或运行测试。重新读取当前列表一致，原失败瞬间未保存数组，不能断言已证明原因。prepare-v2保存过滤后的挂载inspect，并调用本项目verify-container-mounts.py规范化检查全部访问模式/传播/source/destination；不放宽实质门禁，原指纹与patch只允许逐字相同后复用。prepare-v2 SHA `5013bf9897623518aacb05e85cc3c23992e2037e64013c25e8e91acc744059b9`。

prepare-v2挂载规范化比对通过，三库/安装/模型一致、源服务None、GPU7空闲。隔离候选两文件部署完成，patch SHA cb47fb279da85372c09298b49f66b8a77dc083456c07a1d660fdd062e0809f8c。完整diff适用pre-commit通过，生产源码和YAML逐字未变。gate.py SHA `3494c7209ca51df60f78410c1fc4580ba0464cc14a389d2fc5ce5ab5bdfc5da1`：要求标准+专项>=174项、优化解释器>=17项、零fail/error/skip、真实vLLM12例、3x56shape全部有效且trace配置齐全后才允许发布。

发布入口publish.py SHA `5751f6a997230a3d905eecce7bd503ba927f2ca2c70dde860903773c7a9fc534`：源全指纹无漂移、候选diff检查与gate通过后才部署source两个文件；finalize.py SHA `412fedf042e1f8613dca43947130db296b56828bbaf8f8c6eac5c53e655c2a82`通过备份重建原全树指纹，证明除两文件外内容逐字不变，核验三库/模型/安装/服务和GPU释放后封存报告。模型推理生产代码完全未变，不重复启动相同模型回归；沿用已记录同运行时代码的11月9日127060值对照证据，不伪称本轮新测模型。

硬件与依赖摘要由commands/archive-hardware.py保存ENVIRONMENT.json，SHA `c205e951b6c99cf06a6621968f5baaa2302bad2f5c15b4653764d7e4538c5aa4`；只保留设备型号、驱动、MACA和包版本，不归档完整环境变量或无关进程列表。

## 最终结果

已发布到 `BGE-M3:/workspace/bge-m3/tune-src/FlagGems` 实际 editable 安装，源与隔离副本全源码指纹一致。完整 FG patch SHA `cb47fb279da85372c09298b49f66b8a77dc083456c07a1d660fdd062e0809f8c`，HEAD仍4897cc306。完整diff为4 files/+555/-1；本轮只改tests/test_metax_linear.py和benchmark/test_linear.py两个文件。原MetaX Linear生产源码、numerical kernel、YAML候选、默认行为、安装、模型、Plugin/FGV均未变。通过备份替换两文件SHA重建原全源码/配置指纹并与任务前一致，未把测试增长隐藏成运行时优化。

## 正确性与路径命中

- 标准+专项Linear **174 passed**，包含原有36项与新48项、原标准90项；零fail/error/skip。原graph capture及两次新输入/哨兵replay保留并通过。
- python -O错误/选择路径 **17 passed**，零fail/error/skip；唯一warning为pytest预期的优化解释器断言提示。
- 真实vLLM BasevLLMParameter集成 **12组通过**：三dtype×范围内/外×连续/非连续，loader/metadata字典成员身份、storage和权重内容不变。构造器TP metadata限0/1，未宣称真实多卡初始化/通信验证。
- 普通Parameter及普通子类覆盖FP16/BF16/FP32、scope内外、非连续权重与bias；保持loader与metadata、storage/stride/offset/值。新基础单测不依赖vLLM安装。
- grad-enabled/no_grad/inference_mode选择、eligible一维、非连续输入的实际public调用均与独立FP64参考一致且选择符合预期。非法device/dtype及M=0只对执行前capability predicate作反例，不对不匹配device/dtype发射不安全baseline kernel，不新增公共异常语义。
- 零输入、零权重、精确抵消、strided bias通过独立FP64参考；零reference范数单独精确判断，未做0/0或放宽容差。input/weight/bias各自NaN/+Inf/-Inf共9例按独立参考零容差/equal_nan通过。
- 完整4文件diff的项目pre-commit通过；source/candidate diff --check均通过。测试本身仍调用公开flag_gems.linear，保留独立参考与实际ATen/tuner命中断言。
- 本轮无生产计算变化，不重复启动相同模型服务；已有11月9日127060值模型配对仍作为相同生产代码的历史功能证据，不伪称本轮新模型测试或正式精度gate。

## 性能效果

硬件MetaX C550物理GPU7（进程可见GPU0），driver 3.8.1，MACA 3.7.1.5；torch 2.10.0+metax3.8.1.0、Triton 3.6.0+metax3.8.1.0、FlagGems HEAD4897cc306。FP32、同公开wrapper/IEEE算术/同步、graph replay，四(N,K)特征对×七种M×bias开关，**3轮×56shape全部保留**。每轮112条实际launch配置与56组首次调用wall时间保存在trace；首次wall含可能的JIT/调优/cache lookup，不混入稳态或当纯调优耗时。默认/扩展pool独立配置hash，数据库在本case专用目录，后续轮复用已测缓存，用户默认数据库未改。

下表为相同shape每侧3轮延迟中位数之比。**这是既有调参策略相对默认pool的验证，不是本轮测试代码变更带来的性能收益，更不是模型端到端吞吐结论。** 范围只限该设备和矩阵；其他卡仍有无关任务，不声称整机空闲。

| (N,K) | M≤1024已测shape加速比范围 | M1025最大绝对延迟差 |
|---|---:|---:|
| (3072, 1024) | 1.0060–1.1010x | 0.0145% |
| (1024, 1024) | 1.0713–1.1220x | 0.0057% |
| (4096, 1024) | 1.0422–1.0991x | 0.0075% |
| (1024, 4096) | 1.0716–1.1252x | 0.0033% |

已测特化区间观测加速1.006–1.125倍，支持保留当前候选与选择区域。范围外M1025共8组走同一默认路径，最大观测延迟增加0.0145%；所有这些微小回退亦保留，不把计时波动解释为真实算法回退或收益。没有删除慢轮或挑选最好轮；具体三轮和配置见BENCHMARK_REPORT/原生JSON/trace。未设业务SLO，不签发正式性能验收。

### 完整56组稳态摘要（每侧三轮中位数，ms）

| M/N/K/bias | 默认pool | 扩展pool | 加速比 |
|---|---:|---:|---:|
| 1/3072/1024/False | 0.022897 | 0.020797 | 1.1010x |
| 1/3072/1024/True | 0.023045 | 0.021207 | 1.0867x |
| 31/3072/1024/False | 0.022947 | 0.021646 | 1.0601x |
| 31/3072/1024/True | 0.023217 | 0.021545 | 1.0776x |
| 32/3072/1024/False | 0.022942 | 0.021459 | 1.0691x |
| 32/3072/1024/True | 0.023322 | 0.021541 | 1.0827x |
| 33/3072/1024/False | 0.022640 | 0.020742 | 1.0915x |
| 33/3072/1024/True | 0.022817 | 0.020842 | 1.0948x |
| 128/3072/1024/False | 0.035984 | 0.034042 | 1.0570x |
| 128/3072/1024/True | 0.036030 | 0.033905 | 1.0626x |
| 1024/3072/1024/False | 0.225480 | 0.224144 | 1.0060x |
| 1024/3072/1024/True | 0.227950 | 0.224339 | 1.0161x |
| 1025/3072/1024/False | 0.234490 | 0.234499 | 1.0000x |
| 1025/3072/1024/True | 0.235756 | 0.235790 | 0.9999x |
| 1/1024/1024/False | 0.021430 | 0.019393 | 1.1051x |
| 1/1024/1024/True | 0.021559 | 0.019468 | 1.1074x |
| 31/1024/1024/False | 0.021597 | 0.019496 | 1.1078x |
| 31/1024/1024/True | 0.021768 | 0.019441 | 1.1197x |
| 32/1024/1024/False | 0.021602 | 0.019510 | 1.1073x |
| 32/1024/1024/True | 0.021778 | 0.019410 | 1.1220x |
| 33/1024/1024/False | 0.021607 | 0.019495 | 1.1084x |
| 33/1024/1024/True | 0.021762 | 0.019492 | 1.1165x |
| 128/1024/1024/False | 0.021689 | 0.019681 | 1.1020x |
| 128/1024/1024/True | 0.021906 | 0.019557 | 1.1201x |
| 1024/1024/1024/False | 0.084132 | 0.078536 | 1.0713x |
| 1024/1024/1024/True | 0.084230 | 0.078492 | 1.0731x |
| 1025/1024/1024/False | 0.091636 | 0.091641 | 0.9999x |
| 1025/1024/1024/True | 0.092083 | 0.092086 | 1.0000x |
| 1/4096/1024/False | 0.023079 | 0.020999 | 1.0991x |
| 1/4096/1024/True | 0.023392 | 0.021454 | 1.0903x |
| 31/4096/1024/False | 0.023398 | 0.022230 | 1.0525x |
| 31/4096/1024/True | 0.023544 | 0.022591 | 1.0422x |
| 32/4096/1024/False | 0.023352 | 0.022209 | 1.0515x |
| 32/4096/1024/True | 0.023552 | 0.022241 | 1.0590x |
| 33/4096/1024/False | 0.036761 | 0.034956 | 1.0517x |
| 33/4096/1024/True | 0.036576 | 0.034816 | 1.0505x |
| 128/4096/1024/False | 0.052974 | 0.049328 | 1.0739x |
| 128/4096/1024/True | 0.052838 | 0.049123 | 1.0756x |
| 1024/4096/1024/False | 0.291325 | 0.279249 | 1.0432x |
| 1024/4096/1024/True | 0.292681 | 0.279881 | 1.0457x |
| 1025/4096/1024/False | 0.319243 | 0.319267 | 0.9999x |
| 1025/4096/1024/True | 0.320853 | 0.320852 | 1.0000x |
| 1/1024/4096/False | 0.077113 | 0.069733 | 1.1058x |
| 1/1024/4096/True | 0.077031 | 0.069790 | 1.1038x |
| 31/1024/4096/False | 0.077173 | 0.069745 | 1.1065x |
| 31/1024/4096/True | 0.077804 | 0.069250 | 1.1235x |
| 32/1024/4096/False | 0.077164 | 0.069877 | 1.1043x |
| 32/1024/4096/True | 0.077768 | 0.069115 | 1.1252x |
| 33/1024/4096/False | 0.077223 | 0.069927 | 1.1043x |
| 33/1024/4096/True | 0.077629 | 0.069367 | 1.1191x |
| 128/1024/4096/False | 0.077309 | 0.070346 | 1.0990x |
| 128/1024/4096/True | 0.077930 | 0.069822 | 1.1161x |
| 1024/1024/4096/False | 0.314371 | 0.291257 | 1.0794x |
| 1024/1024/4096/True | 0.311662 | 0.290844 | 1.0716x |
| 1025/1024/4096/False | 0.343621 | 0.343611 | 1.0000x |
| 1025/1024/4096/True | 0.343670 | 0.343682 | 1.0000x |

## 决定、风险与回退

FG-R1/R2/R3的验证缺口已补齐，保留现有实现；FG补丁可交PR review。未新增模型graph、backward、其他平台硬件或模型正式精度/端到端性能支持声明；基础单测未引入vLLM硬依赖。源容器未重启，任务开始/结束都无运行BGE模型服务，GPU7已释放。MBT实验保持用户停止状态，没有新性能优化叠加。无commit/push。

回退入口：`docker exec BGE-M3 /flagos/bin/python /public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261109-bge-m3-fg-review-fix-006/commands/rollback.py source`，仅在本轮两文件SHA仍匹配时恢复before/source原文，拒绝后续漂移，不重启服务；已保存未执行。

远端证据：`/public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261109-bge-m3-fg-review-fix-006/FINAL_REPORT.json` SHA `303bf988e794f8363c6936ec79dee538c8fb9f2dbda268eed71490706ff0b1f0`；`/public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261109-bge-m3-fg-review-fix-006/SHA256SUMS.json` SHA `88dc654cc491a1e19fa2c843e945b972187f98db407acad20e073bd29ff61cc1`。PREPARED、规范化挂载快照/比对、前后指纹、JUnit、全部native JSON/trace、BENCHMARK_REPORT、ENVIRONMENT、完整patch、工具SHA及原文件备份一并保留。
