# env028：当前安装版本启动、graph replay 与分页缓存验证通过

PPU-03 / hy4-preview 的新 service09 已加载 env027 当前安装组合，endpoint `127.0.0.1:8010`，模型 `hy4`。仅重启该服务和执行服务范围最小回归，没有修改 Plugin、vLLM、两个 Gems 或模型/tokenizer。

| 检查 | 结果 |
|---|---|
| 启动 | 沿用 TP16、100K上下文、2048 batched tokens、FULL_DECODE_ONLY、prefix cache enabled；health/readiness 200。 |
| Graph capture | 51/51 个 FULL decode capture 完成。 |
| 实际 replay | 全部 16 rank 各至少 2 次 post-ready CUDAGraph.replay；原方法正常返回后记录，未替换计算。 |
| 当前代码生效 | 16 rank 的实际安装导入路径及11个差异文件 SHA 与 env027 吻合，完整614文件前后不变。 |
| Smoke / C8 | 单请求+8并发，共9份唯一请求/原始响应通过。 |
| 分页 / cached prefill | 两次长共享前缀请求都返回 OK，prompt tokens [13249, 13249]，跨2048分块；第二次原生 prefix-hit 指标增加 13184.0 tokens，usage.cached_tokens=0。 |
| 身份 | 新鲜容器 inspect、前后服务实例、四仓源码、模型/tokenizer及配置一致。权重以131个文件inventory/stat和index/config内容核验，没有重新读取多TB权重二进制。 |

当前完整补丁 SHA `dab9c9eca5dfc26f08e7661d1f7c5900210063007452a20dd2d8e785cb2d2a95`，官方基线 `8b2033e417a535a828a1d7594d36bd33e36e3b57`。实际 Plugin `/workspace/vllm-plugin-FL/vllm_fl/__init__.py`；vLLM 实际为安装 wheel `0.24.0+empty`。

两个 gems-opt 始终保持 FGV `46387d7f96050204c1b932f35680a3ea03896fa6`、FG `3ba1d1d99010de56d12088992f8b0da3444d90ca`，clean、revision及tracked摘要不变。未清空编译/算子缓存；dispatch字节SHA `e016b76d935b5792a182ee46ede3595edcfb0e155ed077176fe2a4806c610bf0` 不变。启动脚本、日志和证据路径使用新编号，服务参数保持。

这只证明当前 env027 **组合版本**的服务最小回归通过，不追认中间版本独立通过，也未强制覆盖每种 padding shape。env020/021 的算子范围证据和env027 CPU契约证据仍各自保留。R2数值观察未在此轮改动或消除；198题GPQA与87%正式精度仍待验证。按用户指令没有启动GPQA/性能评测、签发gate或恢复heartbeat；其他平台未实测，不宣称完整精度/性能验收通过。

旧service08仅按新鲜核验的PID/start_ticks及后代树精确停止，没有停止/重建容器或影响其他服务；设备/端口释放后只启动一次新实例。新实例 `e6fd341079ee54be365569b36e31f6bd2df599bd3191d496f1e95b9fbe81db9b`，PID关联见 service-start-09.json。

原始证据根 `/workspace/.hy4-preview-migration-20261018-01/restart-20261020-02`：commands/为执行前保存的脚本；logs/service-09.log、controller.log和各阶段日志；results/service-smoke-09.json、独立response-09-*、paged-response-*、paged-service-probe.json、graph-replays-09-*.jsonl、final-validation.json；前后inspect与service/源码/model/tokenizer清单。最终清单evidence/final-sha256.json SHA `82cbd2778119b5aea3edcd551bdbce5441935ecde77748098231b22664853d01`；final-validation.json SHA `0120df4c47d67c210636ebdc8c99ea01396a6eb2a4debf0e47f1f891d5fbbfed`。本地 `/tmp/hy4-restart-20261020-02`。本地accuracy Skill minimal-regression bundle `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`。

当前安装的三文件回退备份仍见[env027说明](../plugin-cleanup-env027/README.md)；需要回退时先精确停服务再换源码/重启并重新验证，不热替换在用worker。本轮不回退或继续启动评测。

当前相对官方完整diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-cleanup-env027/full-diff.md`） · [env028实验](../../../../models/Hy4-preview/ppu/20261018-hy4-preview-ppu03-migration/optimize/env-028.md)
