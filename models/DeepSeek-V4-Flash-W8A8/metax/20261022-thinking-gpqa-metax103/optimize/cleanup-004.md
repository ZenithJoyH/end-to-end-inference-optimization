# cleanup-004：容器预设环境变量迁入模型启动脚本

状态：**retained / 已完成**（2026-10-28 09:58:24 Asia/Shanghai）。用户2026-10-28明确要求检查影响当前推理的变量，将有效设置写入start-model.sh，并清理当前容器预设。Host mx-103；当前容器deepseekV4-flash。

本项为部署配置整理，不新增算子优化或性能收益主张。原生Docker Config.Env不可原地修改；保存当前writable-layer快照，用支持的OCI元数据导入生成相同rootfs/layers的清理镜像，只保留8项MACA/系统路径变量。以完全相同挂载/设备/资源配置创建独立候选容器，原容器保留。需要切换时只停止精确空闲任务API及其workers；验证后将原容器改名为回退副本，候选沿用deepseekV4-flash名称，不停止/重启/删除原容器。用户本轮清理指令授权此最小可逆替换与启动脚本更新。

保留到脚本的变量按当前读取点冻结，含平台/Plugin、dispatch/黑名单、TF32、多流阈值、调参/编译缓存、usage关闭。已无读取点的DSV4_*、VLLM_FL_METAX_*等历史开关删除。基础PATH、LIBRARY_PATH、LD_LIBRARY_PATH、MACA_PATH、MACA_CLANG_PATH、CUCC_PATH、CUDA_PATH和TZ保留在容器，保障交互环境。实际变量清单和读取点写入远端environment-plan与本记录。

验证：e2e/accuracy minimal-regression，复用20条C1/C8/长输入检查；真实graph capture与至少两次FULL replay；核验当前服务完整argv、必要env、导入路径与Python源码SHA相等。对旧preset与新script设置做同值比较，不签发新GPQA分数或性能gate。本项不跑全量GPQA/性能。原GPQA87.37%及op-007性能保留其历史绑定，不迁移为新分数。失败恢复原脚本/原API，仅操作本任务。

外部任务根：/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/environment-cleanup-20261028-01。快照创建--pause=false，不暂停当前API；OCI元数据仅改config.Env/history，不读取/复制大层，不修改Docker底层存储文件，不修改权重或vLLM源码，不清理共享cache。

- commands/prepare.py SHA `a9aff266f62cdcf4161b5c99931e714412832f889b64069bed92aef25fe842fa`

- commands/build-script.py SHA `a22809ef1578322ba6c6c09fd76cb2a3771ecf8523b6c2b2087ca2aea2173880`
脚本保留13项设置：GEMS_VENDOR/VLLM_PLUGINS、VLLM_FL_CONFIG/FLAGOS_BLACKLIST、TF32、多流阈值、TUNED_CONFIG_FOLDER、五个编译/生成代码缓存目录，以及NO_USAGE_STATS避免开启原先关闭的遥测。对既有外部YAML的通用配置/黑名单读取予以保留；模型初始化内置策略不等于所有调用方都忽略该YAML，上一轮口头说明须以此次逐调用点核验为准。另补齐当前实际API已有但旧脚本遗漏的--cudagraph-metrics，用于native replay证据，推理语义和prefix原开启状态均不改变。

准备门禁通过：source快照e117adaea795470543cfca7efb5c269bcb8b7427acba1100586e25c1c032d694；clean镜像60911198bc6b87761a28377e3ad35f29b2e0690c1017876fdedbd15dfee86f2c，所有层和rootfs与快照完全相同，仅OCI配置ENV/history不同。候选容器63249a7da309df2dfd4341a94bc712975c6260367305144e810bc3b901b5f56b；原生mount verifier passed；四仓Python源文件SHA集合完全相等。原API尚未受影响。原始prepare.js使用Docker29的--pause=false兼容选项，daemon提示应使用--no-pause；记录提示、不把它混入imageID。

切换契约：脚本13项值与原镜像同值，其余全部删除，基础8项保留。build-script02将补齐的--cudagraph-metrics放到argv最后，与当前API精确参数序列一致。原脚本/service.log先保留备份；只有精确空闲旧API停止后才用新脚本启动候选；20请求及FULLreplay、env审计通过才交换容器名称。原容器保持运行、命名deepseekV4-flash-env-backup-20261028，失败则恢复原脚本、名称、旧API原argv/env，不停止或删除容器。
- commands/build-script02.py SHA `17ab06c3e9d8a487e6ffa488aef6497defb413788459ce7d103ac77ac45b1ce0`
- commands/lease-source.py SHA `4b79bf2af78d5b5c03ee1ebaba2bd8d8905df9602f32bb6f129d774b16833c15`
- commands/migrate.py SHA `08fa327bafa2af36e5edb726d266fafe0e0c11245bdb0b9cbc4235b29c95437f`
- commands/minimal-regression.py SHA `f288daa7ffce59c7725c2c55b143a45fe04e8163bd289f172c85bc7f6c8ad446`

最终补充取证：直接按/proc/worker/environ逐项断言失败。已在安装的setproctitle元数据说明及vLLM set_process_title调用中确认：标题修改会覆盖/proc/PID/environ，但不破坏Python内os.environ。因此不把该现象误判为变量丢失，也不声称逐worker环境全部可读。最终核验采用API进程13项精确值、spawn继承实现、8worker身份与9条以上实际custom-policy日志、源码相等及20条真实请求/FULLreplay，保留此取证边界。没有为取证新增永久SPT_NOENV变量或侵入运行中进程。
- commands/verify-final.py SHA `0979b06b4da1a0c0ca822c526be43ff286b425f4960f5695e8cf1b342a1feec0`

## 最终结果

`/public-flash/jinghao/deepseekV4/start-model.sh` 已更新，SHA `7963febb4b87a9ced7013322931929ba9930eb5f8c3976c53995475b9764e961`。原脚本备份在远端 `start-model.before.sh`；原service.log保存在 `service.before.log`，新日志继续写用户目录的service.log。当前同名容器ID `63249a7da309df2dfd4341a94bc712975c6260367305144e810bc3b901b5f56b`；新镜像 `dsv4-envclean:20261028-clean`，ID `sha256:60911198bc6b87761a28377e3ad35f29b2e0690c1017876fdedbd15dfee86f2c`。旧容器ID `99c34f50202ee7f969056280110186121bb0715c4d0e5d619047fd3e783a20a2` 保持运行并改名 `deepseekV4-flash-env-backup-20261028`，仅作为回退副本，旧任务API已退出。

镜像/容器预设59→8；13项有效设置移入脚本，38项历史/无必要设置删除。基础8项为PATH、LIBRARY_PATH、LD_LIBRARY_PATH、MACA_PATH、MACA_CLANG_PATH、CUCC_PATH、CUDA_PATH、TZ。未更改推理实现、权重、tokenizer、挂载、设备或资源限制；保留原prefix cache开启和thinking设置。本轮不新增精度/性能分数。

| 脚本设置 | 保留理由 |
|---|---|
| GEMS_VENDOR=metax / VLLM_PLUGINS=fl | 指定平台实现及Plugin加载范围 |
| VLLM_FL_CONFIG=/graph_patch/metax_graph.yaml | 通用dispatch/辅助配置仍读取该入口 |
| VLLM_FL_FLAGOS_BLACKLIST=topk,masked_fill,masked_fill_ | FlagGems注册范围，须维持已有路径 |
| TORCH_ALLOW_TF32_CUBLAS_OVERRIDE=1 | 数值/矩阵计算策略，保持原值 |
| VLLM_MULTI_STREAM_GEMM_TOKEN_THRESHOLD=0 | 原生DeepSeek attention仍有读取点，保留单流边界 |
| VLLM_TUNED_CONFIG_FOLDER=/tuned_configs/H=4096 | 原生MoE/其他fallback可读取调参目录 |
| VLLM_CACHE_ROOT / TORCHINDUCTOR_CACHE_DIR / TRITON_CACHE_DIR | 保留现有编译产物与缓存策略，避免更换执行产物 |
| FLAGGEMS_CACHE_DIR / FLAGGEMS_VLLM_CACHE_DIR | 两库生成代码/调参缓存入口 |
| VLLM_NO_USAGE_STATS=1 | 保持原遥测关闭设置 |

独立复核：API44/startticks1157315643，health200；20/20请求通过，含两轮C8和两个>10K非对齐输入；FULL C1count15/C8count2及padding到8多次replay。8worker身份和10条custom-policy日志已核验；API13项环境同值；遗留DSV4/VLLM_FL_METAX变量不在当前容器Config.Env与API环境中。四仓全部Python源码指纹与迁移前相同；剩余RMS patch保持已删除。无OOM/非法访存/MCCL错误/traceback。

证据SHA：result `ee759e00ee1daa1100d861d947fa4b6c36033139b931f781a7bd7ba17073e8b7`；runtime-env `798fc1cba46211dca8c8c98567250df93097f075f53f91d1d450be66ac16cf02`；minimal `4e89914b059b987b2853f3e13b42dbe30d7bc9ad3c90fa70ac95a3f179faf8db`；final-verification `8fe2cada506c52c7063e8b5f9602ab7b9a7dc3d40bca8e411c8c246f5800ae83`；mount comparison `0aaaf9b2d11091e21c27ebc68874f5f1a8f3c61d7a5739f8b499083f81dcff3b`。全部原始回执位于本实验远端根。

回退仅针对当前任务API：精确停止新API和workers，恢复start-model.before.sh，将当前容器改回staging名、旧备份改回deepseekV4-flash，使用旧容器原环境启动服务。不要停止/删除容器、整体清空共享缓存或整体回退Git。未提交或推送。

OCI元数据导入实现参考[Moby Docker29.1.3 LoadImage](https://github.com/moby/moby/blob/docker-v29.1.3/daemon/containerd/image_exporter.go)，本机已通过原生docker load和层digest相等证明，无Docker存储目录文件修改。
