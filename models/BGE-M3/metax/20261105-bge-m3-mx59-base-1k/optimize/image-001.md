# image-001 发布镜像与当前代码的1K对照

- 状态incomplete（测量已完成，稳态未证实）；诊断性镜像对比；scenario embedding-p1024-c64-n256；纯encoder无Decode。

## 优化方向与瓶颈依据

用户观察1K总吞吐低。现有2轮均值40553.59 tok/s但波动大；不先归因某库。对比发布镜像与当前可写层版本。

## 优化内容与适用边界

不改源码。源BGE-M3只读取/快照，不承载本轮性能负载。新容器共享原挂载、私有源码、独立日志，按用户要求释放PID2575320所在GPU后串行使用。同模型FP16、eager、TP1、maxlen8192、maxseq64、MBT32768、prefix disabled、seed20261023、同一原生benchmark客户端。

## 正确性与路径命中

待镜像/挂载门禁通过后固定单条/C8 embedding与数值对照；正式精度not_run，原生vLLM启动/真实导入路径逐侧记录。

## 性能效果

未运行。预冻结1K/C64/N256/random/seed0/range0/extra-body原样；输出1仅placeholder。计划当前A→发布B→当前A2，均5轮/前3轮整轮预热/后2轮测量。预热末3轮吞吐span/median<=15%、测量span/median<=15%、A/A2漂移<=15%时才支持有限范围稳态差异；不满足则保留全部数据并标incomplete，不删除慢轮。每轮超时1800s，每侧总诊断预算900s；客户端仅本任务进程，错误即停止。主指标Total tok/s，guard成功256/长度1024/零错误、Req/s和E2EL。无业务SLO/正式精度门槛，不宣称达标。

## 决定、风险与回退

尚无结论。仅停止本任务新服务；保留源服务和全部既有结果。发布/当前同卡串行，若显卡被无关进程占用则停止本轮。保留新容器以供复核，不自动删除镜像/容器。

## 外部证据

唯一远端case待创建后补充。

已完成A/B，A2运行中。以下均为各组第4/5轮算术均值，不能称已证实稳态：

| 组 | Total tok/s | Req/s | Mean E2EL ms | 轮P99均值 ms | 预热准入 | 测量波动 |
|---|---:|---:|---:|---:|---|---|
| A-current | 45228.88 | 44.17 | 1121.54 | 4238.29 | False | True |
| B-release | 26678.94 | 26.05 | 1737.07 | 5719.10 | False | False |

B-release单条/C8与A的最大绝对差0.00029466、最小cosine0.9999989977，在预冻结阈值内；是功能/数值smoke，不是正式精度gate。

## 最终对比与决定

同GPU3、同启动配置、同客户端，5轮中前3轮预热/后2轮全部统计。15轮共3840个benchmark请求全部成功，usage均为1024 tokens。

| 组别 | Total tok/s | Req/s | Mean E2EL(ms) | 各轮P99均值(ms) |
|---|---:|---:|---:|---:|
| A-current | 45228.88 | 44.17 | 1121.54 | 4238.29 |
| B-release | 26678.94 | 26.05 | 1737.07 | 5719.10 |
| A2-current | 76719.81 | 74.92 | 950.71 | 2587.63 |

这些是各组观测均值，不是稳定加速比：A/A2吞吐漂移69.63%；三组预热span分别21.90%/39.34%/77.41%，均超过15%准入，B和A2测量span分别36.16%/74.66%。因此正式判定为incomplete_steady_state，不丢弃慢轮、不修改旧契约。不支持将1K偏低归因于近期代码整理，也没有观察到切回发布镜像带来优势；根因尚未定位。

单条/C8数值检查均通过预冻结阈值（跨镜像max_abs=0.00029466，min_cosine=0.9999989977）；未做正式精度评测。对照服务全部退出、GPU3已释放，新容器保留idle；原BGE8000 health200，源/新容器三库指纹、原脚本和全部历史产物SHA不变。

证据：/public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261105-bge-m3-mx59-base-1k.x4jxof0i/results/COMPARISON.json，SHA256 faa01afc2bcd21069a411830dddd717be5698bf68fbecff285269bcba6a93eb9；FINAL_AUDIT在manifests/，SHA清单为manifests/SHA256SUMS.json。逐轮CSV位于results/{A-current,B-release,A2-current}/benchmark/，保留原22列格式；E2EL在对应native JSON。

下一步先定位轮间波动（客户端、API/调度、主机共享负载或设备执行），必要时单独选择profiling，再冻结新稳态契约重做同卡配对；本轮不改任何推理源码或将某一侧晋级为生产候选。
