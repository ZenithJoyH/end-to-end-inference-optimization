性能优化与自动跟进保持暂停。用户已授权 Hy4-testing 多模态适配；旧007服务在新案例独立回执中精确停止，新权重启动记录见 本地案例 `models/Hy4-testing-W8A8/ppu/20261023-hy4-testing-ppu03-startup/README.md`。以下007/008为暂停前历史结果，冻结文件未改变。

007 C32 已完成并冻结：54轮全新测量、两原生比较passed，0丢轮；Prefill总吞吐12.599x，Mixed输出7.81187x，全部B/R指标最大漂移0.953954%。621项SHA及3份服务日志固定前缀独立复核passed。当前为007空闲before回退服务，候选未自动保留。008稳态profiling已准备本地契约、三阶段dry-run、流式校验器（17项）、预热准入（24项）及进程树资源采样/判定（27项本地检查）；实际watchdog、原生回执和生命周期尚待集成，未部署/采集。acceptance仍incomplete，无精度gate或C64正式结论。

# HY4 PPU-03：profiling 故障与单文件索引批处理

006 的 C16 两组 B/C/R 共54轮全新测量全部准入，两原生比较passed：Prefill总吞吐93.743→1197.995→94.134 token/s（12.780x），Mixed输出10.894→70.786→10.659 token/s（6.497x）。最大基线/回退指标漂移2.373%。终态619项SHA及三服务日志前缀独立复核通过；006各服务随后已停止，证据保持冻结。007 C32结果见本页当前摘要。无新精度gate/C64正式验收；两库及batch2048不变。

## 结果与范围

policy0.15（2026-09-07），验收范围diagnostic。独立容器完成三角色三阶段共81轮（每角色每阶段6warmup+3measure），前后服务/源码/权重清单/tokenizer和全部原生证据核验通过。Prefill/Mixed收益为reproduced，Decode测量稳定性incomplete；不代表完整正式验收。

| C8/N8场景 | 指标 | Baseline | Candidate | Revert | 状态 |
|---|---|---:|---:|---:|---|
| P1024/D1 | 总token/s | 94.0040 | 1211.1425 | 94.9552 | passed |
| P128/D128 | 输出token/s | 44.6017 | 79.3272 | 44.5148 | incomplete：TTFT spread |
| P1024/D128 | 输出token/s | 10.2120 | 49.4156 | 10.1590 | passed |

Mixed为基线4.838976倍（+383.8976%），meanTTFT59.5572→4.8159秒，meanE2E100.0986→20.5468秒；回退输出漂移0.52%。Prefill总吞吐12.883944倍、TTFT53.3442→4.1416秒。Decode meanTTFT/p99TTFT部分轮波动超15%，原轮全部保留，未删轮/改阈值/重跑；medianITL仍约94.4ms，不声称纯Decode kernel加速。

## 环境与实际改动

PPU-03/16×PPU-ZW810E，源hy4-preview，独立容器hy4-preview-perf-20261021-01/8011。env031不可变镜像内容与四实际包一致，image_lineage verified，/mnt:/mnt目录映射parity passed。模型Hy4-preview-W8A8-linear-moe，vLLM实际安装0.24.0+empty，TP16/100K/budget2048/FULL_AND_PIECEWISE，性能prefix OFF。

Plugin8b2033e4+原env031；FGV45e142327d06c65feaa0406b16417b609d6c32ff、FG3ba1d1d99010de56d12088992f8b0da3444d90ca均clean/内容不变，vLLM源码只读。唯一变量为已有backend bf16_indexer.py新增15行完整range批处理，workspace保守限制16MiB、其他shape/TopK排序/Decode保持原路径。无新kernel、vendor特例、模型语义或测试文件修改。

独立PPU oracle14/14逐元素相等；三服务16rank Prefill/Mixed PIECEWISE、Decode FULL各>=2replay，smoke9/C8/分页及观察器撤销通过。固定10题C8 no_think sanity均strict9/10、10唯一题、无TIMEOUT，仅小样本观察。

## Profiling 故障与机制

用户日志19:34:47开始profile，19:43:32停止；19:45:16/26内核global OOM杀死两个同容器worker，匿名RSS约135/132GiB，随后rank7失联/EngineDead。16rank stack/shapes开启、无有效iteration上限；OOM已证实，积累/导出具体内存贡献由配置时序推断，不称设备显存OOM。

独立有界恢复关闭stack/shapes/memory/table，warmup1/active4/max4，stop_profile200、无新OOM。16gzip各展开约1.7GB，包装器后处理750秒超时，原失败回执保留；ijson流式JSON/CRC审计恢复16rank证据。Plugin实际标记new/cached，cached不必然Decode，GPU不按CPU重叠强行分段。

旧trace rank0 indexer CPU inclusive68.803秒/63次、where215082次，是候选依据，非critical path或E2E加速比。单文件批量原整数表达式减少launch，B/C/R复现支持短上下文框架组织开销；未对其他模型/平台或长上下文泛化。

## 决定、下一步与留存

fw001对比收尾时独立容器恢复原基线完整源码，fw001候选仅保存为待晋级提案；当前新增保留fw002，见后文。原适配容器生产源码、用户launcher/service.log未改。最初复刻阶段在源证据目录有控制副本；后续源归档被审批拒绝，新增材料均在独立/评测容器，不绕过源保护。

源acc006 full198 strict183/198=92.4242%通过87%，不绑定新候选/独立实例/prefixOFF；当前无新fullgate。正式P1K/P4K/P16K/P32K、D1024/C64/N128均保留为not_run；只完成当前P1K的三个缩减milestone。review-001在state中排序晋级精度/正式父场景、TTFT分批归因及按需bounded reprofile，未启动新测试。PR readiness experimental，无提交/推送；无证据修订通用SOP/算子稳定知识。

外部原始根：独立容器`/workspace/.hy4-preview-migration-20261018-01/perf-20261021-01`。终态完整备份：评测容器`/tmp/hy4-preview-ppu03-perf-20261021-01/performance-result-backup-fw001`，739文件/17125983字节，逐文件SHA/大小通过，manifest SHA `f6fe3c2a652797b1d7462be6f010e0865460837064e61f000c45d60f4577237c`。原profile traces留原根，未重复打包。暂时网关不可用期间原baseline自行完成，恢复后核验终态，未重复启动。

[模型案例与状态](../../../models/Hy4-preview/ppu/20261021-hy4-preview-ppu03-e2e/README.md)；[fw-001完整指标、契约SHA、回退及边界](../../../models/Hy4-preview/ppu/20261021-hy4-preview-ppu03-e2e/optimize/fw-001.md)。

## TTFT专项定位（2026-10-22）

对原27个Decode轮逐一核对原生SHA及start_times/ttfts/itls：8请求约1.5ms发出，B r7最早流在后续Prefill期间停顿10.413s、B r8为8.034s；C r9的640ms停顿与首SSE分组1+2+5相符。原预热仅检验outputthroughput，未证明TTFT稳定；B/C meanTTFT spread21.25%/40.04%，15%上限和原incomplete保留。

独立原基线上的有界外部时间线确认AsyncScheduler/step_with_batch_queue：全部8请求在约9–13ms收到，前两步在10.68/11.70ms已排入；等待首个future约1.45s后才处理余下6个输入，随后以6prefill+2decode执行。分批窗口的毫秒变化会被Prefill放大成秒级首token/早期输出差异。六轮每轮127个纯Decode步均观测FULL replay；较小Prefill/Mixed为PIECEWISE，超512token步未观测replay。旧候选异常轮无同期trace，新观察器也会扰动入队微时序，不能冒充旧轮精确重放。

补采仅6warmup均8/8成功，末3输出吞吐spread51.36%按契约停止、0measured、无重跑；第6轮Mixed 28.5847s仅rank0墙时，设备/其他rank/算子根因未定。失败与全部trace冻结，before/after服务和四安装包一致，两个算子库未变。为清除process-bound观察器，恢复原普通启动器并做启动/graph/C8/分页回归；不计算新性能收益。详细证据、SHA及恢复终态持续写回[fw-001](../../../models/Hy4-preview/ppu/20261021-hy4-preview-ppu03-e2e/optimize/fw-001.md)。

收尾已完成：普通服务启动、16rank三阶段replay/C8/分页通过，四包/模型/tokenizer/config一致；当前源为原env031，候选未安装。评测容器独立`ttft-diagnosis-backup-001`保存380文件/11.00MB，manifest SHA `08bd6ae6635b7c13878a0c588dae2061dcd01fb0736e0f1918c13b771f443ade`，旧B/C/R备份不动。


## Mixed 28.6秒后续定位（2026-10-22）

主要阻塞已确认为5行Decode indexer TopK首次JIT，PPU make_ttgir阶段占主导。异常窗口的精确kernel hash已复现：新隔离cache冷编译24.274s，其中TTGIR20.763s；内存命中0.157ms、磁盘命中0.739s。NUM_ROWS虽未在kernel体使用，constexpr仍生成不同cache key，测试1..8/16行的IR与PPU二进制逐字节相同。Piecewise split内部路径的特化未被其他行数预热覆盖，不代表Decode FULL graph失败。

仅编译验证，0kernel launch/0模型请求；两库、四包源码、原cache与当前服务未变，无重启或精度评测。原始rank编译/TP等待分配及剩余执行时间未记录，不能把全部28.6秒精确分摊或当新性能收益。原Decode incomplete保留。完整138文件/12318066字节已SHA备份，manifest `ff1797cc4822e3a8f317eb004dff59454f973a252e923e00a11b4d9a68167e8a`，位置与逐项证据见[fw-001](../../../models/Hy4-preview/ppu/20261021-hy4-preview-ppu03-e2e/optimize/fw-001.md#已确认的阻塞阶段与触发条件)。


## fw002最小修复（2026-10-22）

FGV固定45e14232、不升级，只在PPU non-TLE launch将未使用的NUM_ROWS编译参数固定1，真实grid不变；FG固定3ba1d1d9、Plugin/vLLM不变。9行数oracle索引逐元素及CPU TopK集合相等；首次5行复用1行编译、无lowering。启动、全16rank三阶段各>=2replay、9/9smoke+C8与两次2689token分页通过。全部16rank各两次精确389token Mixed无TopK编译，rank0为4.368/4.164秒，原长JIT阻塞未再现；观察器已撤销。原合成token探针无有效内容而失败，修正client prompt的v2通过，旧失败证据保留。此为请求的阻塞修复与功能验证，不宣称稳态速度或正式模型精度通过，未开始精度评测。当前只保留fw002，不叠加fw001提案收益。

[完整diff、版本、核验与回退](../../../models/Hy4-preview/ppu/20261021-hy4-preview-ppu03-e2e/optimize/fw-002.md)。证据留原优化容器，包含247文件/28.58MB及静态日志快照，SHA清单已逐项核验；跨容器备份被自动审批拒绝，未执行传输。

用户随后将配置收敛到安装版PPU默认`thead.yaml`：dispatch/41项blacklist只保留在YAML，脚本删除两项重复export并unset继承值；真实默认加载与旧有效策略完全相等。仅配置API/语法校验，未启动模型或精度评测，库内容固定；新模型运行验证尚未执行。

2026-10-22 用户P4K/C64当前日志复核见[diag-001](../../../models/Hy4-preview/ppu/20261021-hy4-preview-ppu03-e2e/optimize/diag-001.md)：慢现象与Prefill加入高度相关；原逐行indexer仍在。8192仅待测，未重启/修改/新测量；旧C8收益不外推。
