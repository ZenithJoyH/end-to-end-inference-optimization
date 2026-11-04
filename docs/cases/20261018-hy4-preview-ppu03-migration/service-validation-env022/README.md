# env022：当前 HY4 版本启动、graph replay 与分页缓存通过

PPU-03 / hy4-preview 新service08已加载当前env021/r15组合源码，endpoint `http://127.0.0.1:8010`，served name `hy4`。本轮仅重启服务和验证，Plugin/Gems/vLLM/权重没有修改。614文件清单与补丁SHA `e66c0b38c3f70d7135b2cb7bd8a5194455f0ae42e665016ea50c4f7d4ad14310`保持不变，全部16rank的实际Plugin导入路径和11个差异文件SHA吻合当前候选。

| 验证 | 结果 |
|---|---|
| 启动 | 原参数TP16、100K上下文、2048 batched tokens、FULL_DECODE_ONLY，readiness/health200。 |
| Graph capture | 51/51个FULL decode capture完成。 |
| 实际replay | 16个rank各至少2次post-ready CUDAGraph replay，来源和PID核验通过。 |
| Smoke / C8 | 1+8共9个唯一请求和独立原始响应全部通过，无重复编号覆盖。 |
| 分页 / cached prefill | 两次共享长前缀请求均返回OK，prompt tokens为[13249, 13249]，跨2048 chunk/TopK边界；第二请求usage cached=0，原生prefix-hit指标增加13184.0 tokens。 |
| 身份 | 新服务前后四仓源码、model/tokenizer、启动配置和实例一致；实际vLLM是安装wheel 0.24.0+empty。 |

两个gems-opt仍固定FGV `46387d7f96050204c1b932f35680a3ea03896fa6`、FG `3ba1d1d99010de56d12088992f8b0da3444d90ca`，分支、clean及tracked-file摘要前后保持不变。没有手工修改或清空编译/算子缓存，也未为了启动增加兼容空壳或更改参数。旧AOT缓存引用已删除的fl_w8a8_dynamic_per_token_linear，vLLM按自身load-failure流程自动重新编译当前路径，后续capture/replay以新结果核验。沿用原dispatch内容SHA `e016b76d935b5792a182ee46ede3595edcfb0e155ed077176fe2a4806c610bf0`，只更换启动脚本/日志/证据路径。

耗时观察：首次长前缀约339秒，缓存复用约2.28秒。单次含首次路径开销，未做性能比较或隔离归因，不宣称性能达标。

这次验证绑定**当前env021组合版本**，不是给被后续收敛的中间版本补签通过。此前短上下文和padding operator回归保留在env020/021；当前服务测试没有单独声称强制命中每一种padding形状。R2数值观察不在本轮改动范围，完整198题GPQA与87% gate仍未验证。未启动评测、未恢复heartbeat，亦没有性能收益结论；其他平台未实测。

## 生命周期与证据

旧service07仅按PID/start_ticks核验的本服务进程树精确停止，未停止或重建容器，设备释放后只启动一次service08。新实例 `3e147d84c5850ac8481aaad0c67ecba0def8b3de89992527fb4c892b16fadb04`；PID/start_ticks仅作实例关联见service-start-08.json。

远端 `/workspace/.hy4-preview-migration-20261018-01/restart-20261020-01`：commands/保存执行前冻结脚本与SHA；logs/service-08.log和controller.log、results/service-smoke-08.json、paged-service-probe.json、graph-replays-08-*.jsonl、final-validation.json；service-before/after及evidence/记录新实例的四仓/模型/tokenizer/运行身份。完整终态文件清单evidence/final-sha256.json SHA `ea50dc771ebd6500f77c4b2af45bae442ddd5b08f5b6e35a43ab845051e1d6b4`；final-validation.json SHA `ef12867cfbe1836ac43a340021b849de35168796a8fc0408254f782447862a50`。本地原始副本 `/tmp/hy4-restart-20261020-01`。

按本地e2e/accuracy minimal-regression执行（bundle `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`），服务级最小回归通过，不是正式模型精度通过。当前源码的备份与单文件回退仍按[env021说明](../plugin-review-env021/README.md)，运行服务时必须先精确停服再回退并重启，不能把旧代码热替换进worker。未经用户新指令不回退、不重启、不启动GPQA。

当前源码完整diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env021/full-diff.md`） · [本轮实验记录](../../../../models/Hy4-preview/ppu/20261018-hy4-preview-ppu03-migration/optimize/env-022.md)
