# env-002-plugin-support-minimaxM3 指定分支推理验证

- 状态：retained，最小文本推理回归通过；分类：用户指定环境切换；目标：graph 模式模型推理，非性能优化。

## 优化方向与瓶颈依据

用户要求替换为 ZenithJoyH/vllm-plugin-FL 的 support-minimaxM3 分支。当前 PPU-13/minimaxM3 无服务，16 卡空闲。旧 checkout 有本地改动，不允许覆盖。

## 优化内容与适用边界

在未挂载的 /workspace 建立新 checkout，锁定 `620892ab8c083b137c24db6cfcdc32fe38cca963`，审阅依赖后切换 editable 安装。保持 vLLM、FlagGems、FlagGems-vllm 原状。复制当前 start-model.sh 配置到独立 case 启动脚本，日志不覆盖共享 service.log；不修改原共享脚本。

## 正确性与路径命中

使用本地 inference-accuracy-evaluation/minimal-regression。检查 import/entrypoint、graph capture、至少两次 replay、固定 smoke 与 C8 的内容/异常。通过也仅说明所测输入正常，不签发全量 GPQA gate。失败时调用精度定位技能，修复或回退。

首次原样分支尝试：59/59 权重分片读取完成，但服务未 ready。调用 inference-accuracy-diagnosis，以 `accdiag-006-support-branch-startup-pending` 记录。非阻塞 py-spy 采样 TP0/1/15，三者主线程均为 `determine_available_memory → profile_run → embed_multimodal → vision_tower Conv3d → FlagGems conv3d → Triton autotuner.check_disk_cache/benchmark → do_bench → torch.cuda.synchronize`。未出现模型回答，不能分类为数值精度失败；这是启动健康问题，具体 kernel 根因尚未证明。

原 Plugin 的 thead.yaml 含 conv3d/cudnn_convolution 黑名单，新分支默认空列表。仅恢复这两项既有配置并重启本实验精确实例；首次日志和栈保留。未修改 FlagGems/vLLM、graph、上下文或并行参数。恢复后服务通过视觉预热与 graph capture，文本推理回归通过；这是已验证的配置 workaround，不等于已定位 conv3d kernel 内部根因。

第二轮服务 `fad201d7b6ec:8024:7461:493495998` 于北京时间2026-10-17 14:50:58完成10请求：两次单请求及一组C8，全部HTTP200、stop结束、最终答案正确，无超时/空输出/4096上限截断/乱码/机械重复。输入185–7241 tokens，输出22–115 tokens。覆盖中英问答、数学及7241-token检索；未验证100K边界或真实图像/视频请求。

初始检查器仅剥离通用 `</think>`，而此模型实际输出 `</mm:think>`。未重跑或修改原结果；追加 `native-verification.json`，对原生响应按真实 mm 标签剥离后核验最终答案，10/10一致；H₂O等价形式在测试前已冻结允许。没有把思考内容中的答案算作最终回答。

沿用原启动语义，未启用reasoning-parser，API的content保留默认`<mm:think>…</mm:think>`内容；此处报告的是标签后的最终答案，不声称原始content只包含答案。

FULL及PIECEWISE各7个capture size在全部16 rank完成。原生运行日志累计FULL180次、NONE4次、PIECEWISE0次：FULL capture之后的多次执行证实至少两次replay；本请求集合没有观察到PIECEWISE replay，不将capture成功写成该模式已回放。新服务日志ERROR/Traceback为0，最终health200。

新分支源码清单（含两项黑名单）SHA为 `8dab5c2770298da7ef0bebef831acd5a00bb8acc9f4358f3be18e84228dd36a8`；FlagGems、FlagGems-vllm清单与切换前一致。vLLM实际导入 `/usr/local/lib/python3.12/site-packages/vllm`，源码清单SHA `0c5a0d9cbbcd805e6b3816fabf3540db3ba3f0b4cb6921017ed8329c308103b6`。`/workspace/vllm` HEAD仅作为旁置源码记录，不冒充安装包revision。

## 性能效果

未测，不声明加速。

## 决定、风险与回退

已切换 editable 导入，实际路径为 `/workspace/vllm-plugin-FL.support-minimaxM3-20261017/vllm_fl/__init__.py`，发行元数据为 `0.0.0+g620892ab8`；代码提交锁定620892ab，仅恢复私有thead.yaml中的既有两项黑名单。原 `/workspace/vllm-plugin-FL` 保留完整 dirty checkout。回退通过 `python -m pip install --no-deps --no-build-isolation -e /workspace/vllm-plugin-FL`，并仅停止/重启本实验精确服务实例；不修改其他容器/服务。

当前8024服务保留运行，未重建/发布镜像。此次不提交源码、不创建PR。未跑全量GPQA或性能测试；旧92.42% gate不适用于此分支，正式精度及性能准入仍未完成。无新增heartbeat，前台验证已结束。

启动配置来自当前共享脚本（8024、TP16、BF16、100000、seq64、batched8192、block128、关闭 prefix cache、FULL_AND_PIECEWISE、capture1/2/4/8/16/32/64）。去掉重复的 host 参数，仅监听127.0.0.1；另启用 DEBUG 和原生 cudagraph metrics 作验证取证。初次启动在加载前被精确取消，以启用 graph 计数；该取消不记为分支失败，日志保留在 `logs/service-before-metrics.log`。未停止或重启任何既有服务。

## 外部证据

PPU-13：`/mnt/nfs/users/jinghao/minimaxM3/20261017-minimax-m3-ppu13-plugin-support`。变更前先保存 `commands/prepare.sh`；安装与启动脚本也须先保存后执行。

- prepare.sh SHA256 `29abd4fa2962ce2e6cc7936c725791c12d07817b6070d205bb28ac678b23dc21`。
- install.sh SHA256 `ed1da647fb9987ddd5f8912a7e59d786f36b7460b6a9434d86e39e36176d85b9`。
- start-service.sh SHA256 `2abdb83cbe60f659990660707765b25cf2c0030ce4f9aef8e751745f27c67b75`。
- 原样分支停留证据：`logs/service-pristine.log`、`checks/worker-tp{0,1,15}-stack-01.txt`。
- 配置变更：`commands/required-blacklist.patch` SHA `b86dd5f8cb2f4af5af752cf1c32638e3596d7f753d7829104db37ca15bd98856`。
- `checks/result.json` SHA `53cbe4b70a08a71e5006855e497793419a96e85dac3a286a0cf7fc095d02d533`。
- `checks/native-verification.json` SHA `ef2d4b07c08d98da492411eb752017dd9a71d88471d41559d909ec9342b66321`。
- `runtime/service-manifest-after.json` SHA `1cfbacbad8c8c66a2e5747318638616b443d78387c0563129073c47772dc5f7e`。
