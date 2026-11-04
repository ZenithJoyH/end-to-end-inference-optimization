性能优化与自动跟进保持暂停。用户已授权适配新多模态权重，且提供 day0 参考包；启动适配单独记录于 本地案例 `models/Hy4-testing-W8A8/ppu/20261023-hy4-testing-ppu03-startup/README.md`。旧 007 冻结证据不变。

007 C32 已完成并冻结：54轮全新测量、两原生比较passed，0丢轮；Prefill总吞吐12.599x，Mixed输出7.81187x，全部B/R指标最大漂移0.953954%。621项SHA及3份服务日志固定前缀独立复核passed。当前为007空闲before回退服务，候选未自动保留。008稳态profiling已准备本地契约、三阶段dry-run、流式校验器（17项）、预热准入（24项）及进程树资源采样/判定（27项本地检查）；实际watchdog、原生回执和生命周期尚待集成，未部署/采集。acceptance仍incomplete，无精度gate或C64正式结论。

# HY4 PPU-03 端到端性能优化（2026-10-21）

006 的 C16 两组 B/C/R 共54轮全新测量全部准入，两原生比较passed：Prefill总吞吐93.743→1197.995→94.134 token/s（12.780x），Mixed输出10.894→70.786→10.659 token/s（6.497x）。最大基线/回退指标漂移2.373%。终态619项SHA及三服务日志前缀独立复核通过；006各服务随后已停止，证据保持冻结。007 C32结果见本页当前摘要。无新精度gate/C64正式验收；两库及batch2048不变。

用户profiling主机OOM已定位；独立环境完成16rank有界trace恢复及单文件批量索引提案的三阶段B/C/R。

历史 fw001 结论：**C8/N8缩减Prefill、Mixed比较通过，Mixed输出4.84倍；Decode TTFT波动导致incomplete。** 以上为历史fw001提案的缩减比较，不能代表当前组合。当前只保留fw002的FGV一文件重复编译修复；两个库commit/安装版本不变，正式完整精度/性能均未运行。

详见[基线](baseline/README.md)、[优化与完整结果](optimize/README.md)、[验收缺口](acceptance/README.md)。

TTFT详细定位已完成机制级取证：异步两步队列的入批差异经Prefill放大为首token与早期Decode停顿，原预热只检验输出吞吐；原incomplete不变。六轮诊断在预热波动条件触发后停止，未生成测量轮，后续已将28.6s Mixed主要阻塞定位为5行Decode TopK首次JIT的PPU TTGIR阶段：冷编译24.274s，其中TTGIR20.763s。独立普通服务已恢复并通过graph/C8/分页，源码和两个算子库不变，诊断证据380文件已SHA备份。详细时序与边界见[fw-001](optimize/fw-001.md#ttft-超限的详细定位ttft-diag-001)。

[Mixed 28.6秒阻塞证据与结论](optimize/fw-001.md#已确认的阻塞阶段与触发条件)：仅编译复现、0模型请求，源码/两库/服务保持不变；138文件终态证据已SHA备份，无新精度评测。

当前[fw-002最小修复](optimize/fw-002.md#最终结果与完整-diff)已完成启动、16rank三阶段replay、C8和分页验证。精确3Prefill128+5Decode1的Mixed在16rank各2步均无TopK编译，rank0为4.368/4.164秒；外部观察器已撤销。FGV45e14232只增加一处PPU NUM_ROWS参数补丁，FG3ba1d1d9/Plugin/vLLM内容不变；未开始精度评测。证据含日志快照已留存原优化容器，跨容器备份被自动审批拒绝。

用户NFS启动脚本已按[fw-002记录](optimize/fw-002.md#用户启动脚本对齐仅编辑不启动)对齐已验证配置（端口保留8010、capture最大512、dispatch与缓存目录、prefixOFF）；仅静态校验，未执行启动或评测。

最新配置归并：安装版`vllm_fl/dispatch/config/thead.yaml`已承接dispatch与41项blacklist；脚本清除VLLM_FL_CONFIG/BLACKLIST覆盖，默认自动读取YAML。新鲜配置API验证与此前有效配置逐项相等，未重启/启动服务或精度评测；两个库内容未变。详见[配置归并记录](optimize/fw-002.md#安装版ppu-yaml归并仅配置不启动)。

最新只读诊断：[diag-001](optimize/diag-001.md)。用户当前8010/P4K/C64日志已取证，Prefill逐行路径为首要优化线索；8192仍为待验证候选，未改变服务/代码/两库或启动精度。
