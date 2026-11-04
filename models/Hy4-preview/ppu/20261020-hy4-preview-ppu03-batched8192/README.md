# HY4-preview / PPU-03：8192预算初测

**未保留8192；原8010/2048/prefix enabled已恢复并验证。**

新版FGV45e/env031同anchor，唯一变量CLI max_num_batched_tokens2048→8192，TP16/FULL_AND_PIECEWISE/10桶/GPU.85/100K固定，性能prefix关闭，所有admitted测量轮保留。

| 缩减场景/指标 | 2048 | 8192 |
|---|---:|---:|
| Prefill P1024/D1/C8/N8输入吞吐 | 95.95token/s | 93.17token/s |
| Prefill平均TTFT | 52.14s | 78.32s |
| Mixed P1024/D128/C8/N8输出吞吐 | 10.2022token/s | 10.1746token/s |
| Mixed平均TTFT | 59.58s | 77.52s |
| Mixed平均TPOT | 319.81ms | 181.88ms |
| Mixed平均E2E | 100.19s | 100.61s |
| Decode P128/D128/C8/N8输出吞吐 | —（预热未稳） | 44.39token/s |
| GPU KV容量（startup日志口径） | 347152tokens | 308701tokens |

8192 Mixed吞吐未提高（观察-0.27%），TTFT增加30.11%，TPOT降低43.13%，总延迟基本不变（+.42%）；Prefill吞吐-2.90%、TTFT+50.22%。两项延迟的反向变化不能当作净吞吐收益。整段Prefill探针含预热同32768输入/32输出，原生迭代20→8，证明批处理组织改变；CPU/具体kernel瓶颈未由trace定位。

按预设未达5%主指标收益/TTFT守护越界停止，不保留8192、不追加独立revert，维护比较器真实incomplete；Decode基线4warmup未稳定（70.68%），无measured，不以候选单独通过补齐参考。以上为有界同plan A/B观察，非完整因果/正式验收。四原始D1K/C64/N128场景和完整198题GPQA均not_run。

[完整fw-002契约、证据与决定](optimize/fw-002.md) / [结构化基线](baseline/README.md) / [当前状态](optimize/README.md) / [验收边界](acceptance/README.md)。

原服务现使用env031安装代码及FGV官方45e14232，FG3ba1d1d9不变；9smoke/C8、三组16rank各2replay、两次2689token分页通过，实际prefix hit 2624tokens。新服务实例`f1d5138652d2365ae3c1c4409458dfe818bb98b9e790eb0314cff5f913633648`。完整性能证据431文件SHA非破坏镜像到原容器同绝对根`/workspace/.hy4-preview-migration-20261018-01/perf-20261020-02`；原生source-recovery恢复证据另存，运行恢复不冒充性能revert。
