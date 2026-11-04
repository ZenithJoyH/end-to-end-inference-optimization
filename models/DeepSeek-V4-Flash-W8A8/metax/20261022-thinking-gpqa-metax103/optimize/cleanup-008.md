# cleanup-008：去除共享缓存卷的可迁移镜像

用户明确要求检查/var/lib/dsv4、移除非必要卷挂载并使保存的镜像可独立启动。目标mx-103/deepseekV4-flash。这是部署包装任务，不是fw-006恢复、数值改动或新性能优化。源容器/共享卷/源码/启动脚本保持原样。

只读检查：/var/lib/dsv4共约12GiB；vllm9.7GiB、triton883MiB、torchinductor14MiB、历史original-image03/04测试cache835MiB。没有模型权重或必要包源码。当前/root/.cache/vllm、/torchinductor_cache、/triton_cache为指向卷的链接；镜像仍有VOLUME /var/lib/dsv4声明。实际运行入口为sleep，旧/opt/dsv4中的镜像初始化/校验元数据已与现有适配不符，不在当前启动链路。

方案：只读export源合并文件系统，流式排除缓存与挂载遮盖目录、退休旧初始化元数据，将缓存链接改为普通目录；保留三仓、vLLM、FlagTree、Torch/MACA及其全部工具链。单层docker import保留8项基础环境及用户/工作目录，去掉VOLUME；内置/opt/dsv4/start-model.sh为ENTRYPOINT，仅把现有脚本变为前台exec、默认权重路径/models/DeepSeek-V4-Flash-W8A8、首个位置参数可指定路径。当前prefixON/threeexports/编译及推理参数保持。仅挂只读权重路径的候选，明确用户授权的迁移挂载差异，不伪装原生mount_parity完全一致。源与候选五个代码/配置/so树指纹、版本、导入路径须完全一致。

验证使用本地e2e/accuracy minimal-regression：全新缓存冷启动、原18条科学选择题C1/C8重复、2条非对齐长输入及默认thinking，核验graph capture/两次replay/health和无OOM非法访存。若需要GPU，仅精确租用空闲源API，验证完停止本任务候选API/workers并原参数/内存环境恢复源API；不停止/删除/重启原容器。失败保留证据和源服务，不将缓存打包当成功。新镜像验证不复用刚完成GPQA gate、不声称同等性能或64K OOM已修复。其他机器实际运行未测，仍需兼容MetaX主机驱动。

远端根：`/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/portable-image-20261029-01`。候选deepseekV4-flash-portable-20261029；目标镜像dsv4-flash:20261029-portable。全部变更命令先保存到commands，精确SHA如下：

- commands/build.py SHA `6a2ac3cc798ccd30021b3feb8745cb8c1240386069486a4354f91885562e91a7`
- commands/fingerprint.py SHA `09a9cd418209b6438a06b1a3d4aa50d6d2f3f0c06b8ef40cf5e6ac45634a4d4f`
- commands/audit.py SHA `d3e938c239cdad655070870209c1b6e408d01ec960683dc5f130252440482970`
- 初始化stage.py SHA `fe9088af9eac83f3060e8c4555079b9a643abf9108a735ec4f9e706499960373`（本地/tmp/dsv4-portable-20261029/stage.py，校验并落盘后才执行build）。

状态：planned。

## 自动审批阻塞（未执行远端构建）

stage.py两次被automatic approval review拒绝，未创建远端任务目录、镜像或候选容器。首次理由为脚本可能向源API发送SIGTERM；再次说明实际build.py不含SIGTERM/os.kill/docker stop/kill/restart，且terminate仅针对自己的docker export/pigz子进程；之前读到的lease-source.py不在stage payload、未上传或执行。复审仍认为后台构建未独立核验，拒绝。不得通过改命令或间接执行绕过。当前只有本地脚本/记录及只读卷检查完成；镜像未构建、GPU验证未运行。需要用户确认具体构建执行；若要真实冷启动验证，还需允许在空闲时短暂租用原API GPU并原参数恢复。原容器、卷、源代码、启动脚本和服务均未修改。

## 用户明确恢复授权

用户同意执行构建，并允许在服务空闲时暂时停止模型进程；无卷镜像验证后恢复原服务，保留原容器和卷。已按同一冻结stage.py重新发起构建，旧拒绝证据保留，不扩大到fw-006恢复或其他服务。

## 已授权的冷启动与恢复验证

构建成功后协调器检查源服务空闲、精确 PID/startticks/argv、源码及脚本 SHA；源环境仅在租用进程内存中保留。仅停止模型 API/workers；候选无外部缓存卷、仅权重只读挂载，完成 20 条最小回归和默认 thinking 1 条后释放 GPU，再恢复源原 argv/env/cwd/stdout 并核验两次推理。源当前 prefixON 按原样保持，不将本次验证声称 prefixOFF。

- `commands/lease-source.py` SHA `7311528be88eb58b9352395eb087177fb62761e45f90d94791d67d069c7be778`
- `commands/sanity.py` SHA `baa807558fa90277669a75ff0971695be89949e1530bbc0b101f9a8a9efa5824`
- `commands/validate.py` SHA `e53877eb271eeeab22bc6e05a4ed7c2bbb3bf9b814a365df0d29be1f297de431`
- `commands/coordinate.py` SHA `6d4ec2c3ca71a9efaa59af156613f9c1a9b4970ef469dcdcbafc9fb0d49e559b`
- 本地 stage-validation.py SHA `99a71f742e1615c042fc06f8af9046beeaf9b9db2fe96d392972accd7e27ae31`；验证范围为部署迁移，非性能比较、完整精度或 OOM 修复。

保存可迁移 Docker archive：`commands/save-image.py` SHA `c0d9a6fb527f2636afa57cc87f2bc3c0252f9450688aba7d7ee232cf1fc0695b`。仅 docker save 读取新镜像，pigz 压缩，保存 SHA；不导出卷或模型权重。

迁移说明 `PORTABLE-README.md` SHA `35c3fa3b976736fea99c887292bab972f570ae335548977714eb2a49780aa995`；Docker run 仅挂只读模型，保留 127.0.0.1:18001、TP8 和源 prefixON。

归档全量只读校验 `commands/archive-review.py` SHA `b801780da0ac3b4082989f18271b4efe31530255931b625cde89d1939beb9e13`：读取完整 gzip/tar，核对 manifest、配置内容寻址 SHA 和 VOLUME 缺失。

归档附加检查第一版把 Docker image Id 当作 config digest；本机 containerd image store 实际 Id 为 OCI manifest digest，导致断言失败，非镜像/推理失败。保留失败回执，v2 按 manifest→config 和 rootfs diff_id 核对，`commands/archive-review-v2.py` SHA `9d19425c4de5510447c521e29ec8e6569da5657b736a64a94954cc8a0094182f`。用户补充仅需本机镜像，无需使用归档；已有归档保留，不再额外制作。

最终只读复核 `commands/final-review.py` SHA `d0c15a6a10d8006a7730539d6dd732bd27d8de2ab079b939606c78d1973d6634`：21 回归、C8 FULL graph 至少两次 replay、源码/镜像/挂载、源精确进程身份与恢复推理、无 OOM/非法访存。

## 候选验证完成，源恢复中

02:00:36Z 候选 21/21 请求通过：18 条短/C8 回归、两条 10449/10454 token 非对齐长输入、默认 thinking。7 档 FULL graph capture 完成；原生 cuda_graph.py 表记录 C8 FULL count=2（两段），达到两次 replay。未见 OOM/非法访存；候选 API/workers 已退出，容器保留。02:01:05Z 开始按原 argv/env/cwd/stdout 恢复源服务。

镜像 `dsv4-flash:20261029-portable`，OCI manifest ID `sha256:baa39b3367835097c2ef7195d9251209edd1f5c5e799662ae20d7fa7f6f5e209`，VOLUME=null；候选仅权重只读挂载，五个源码/库树指纹一致。可选归档已保存（13540061868 bytes，SHA `17743165f19ac5d0ec77f984283f8b7ede99c0b140533310e4e068003835cfa9`），v2 全量 blob/manifest/config 核验通过。用户表示只需验证后本机镜像/commit；不要求使用此归档。

## 最终交付：retained

2026-10-29 02:04:49Z 最终复核通过。无卷候选冷启动从 01:50:18Z 至 01:59:35Z，约 557 秒；这是全新缓存首次编译的诊断耗时，不作为性能收益。候选 21/21 最小回归通过（含 C8、两条约 10K 长输入、默认 thinking），实际 FULL graph replay 已核验，无 OOM/非法访存。测试仅覆盖 mx-103，不代表完整 GPQA/MATH500/四场景或 64K OOM 验收，fw-006 继续暂停。

原服务已在 02:04:38Z 恢复健康，按原 argv/env/cwd/stdout 运行；之后两次推理均通过，原生日志记录 FULL replay count=4。原容器 ID、镜像、挂载、共享卷、源码指纹及启动脚本 SHA 均保持，未停止/重启/删除原容器。源 prefixON 保持。旧正式精度属于旧服务实例，本次未签发新正式绑定 gate。

- 本机可直接用的镜像：`dsv4-flash:20261029-portable`，不需要再次 commit。
- 无卷验证容器：`deepseekV4-flash-portable-20261029`，模型进程已退出，仅 sleep；仅只读权重挂载，其他测试容器/卷未动。
- 镜像内启动脚本：`/opt/dsv4/start-model.sh`；默认权重 `/models/DeepSeek-V4-Flash-W8A8`，不依赖原 `/public-flash`/`/data` 挂载。
- 若用户后续自行 commit 验证容器，需要 `--change 'ENTRYPOINT ["/opt/dsv4/start-model.sh"]' --change 'CMD []'`，否则会继承验证容器的 sleep 入口；此类再次 commit 也会包含验证生成的缓存。当前交付镜像是验证前的干净镜像，不含本次生成的缓存或验证日志。
- 原容器直接 commit 仍继承 VOLUME 声明和卷链接，不等同本次无卷镜像。

最终证据：`final-review.json` SHA `b3fda423bdb1ff2746dfea8a3fe5a96eef67fcc7512d4fbfb5b636bd254c26a6`；`validation/result.json` SHA `8af650fefe18c5a6fd83a9dd3fa9052a16fdfe0d961bc2084c1892aa966fa81a`；`source-restored-inference.json` SHA `e7e3afbdba06988ac9108abacb7566bf8d4836c473a7c6223e51c1a275f7d144`；`source-preserved.json` SHA `1b605b83f1fe08769f6efb2eac8ea0d82083afc7088b2a6289ffb16456b473cd`。全部位于本记录指定远端根。可选归档全量校验通过，原失败为 OCI manifest/config 摘要类型的检查脚本错误，已保留并用 v2 修正；不是模型失败。

无需回退：源内容未改。如不采用新镜像，可继续使用已恢复的原服务；无须删除原卷。没有自动提交或推送。

本地记录校验：当前模型 state schema 和全部实验文档/README 链接通过；全仓 check-project-records 未通过，报错为其他模型既有 schema/链接和过程产物规则问题，未修改或清理这些无关内容。

## 用户追加：从交付镜像新建容器

用户要求基于该镜像启动一个容器。核验原 TP8 服务仍运行，新建 `deepseekV4-flash-portable`，仅权重只读挂载、MetaX 设备、64GiB shm、host 网络，入口 sleep infinity；不启动第二个模型服务，不操作原服务或其他容器。`commands/create-user-container.py` SHA `4475512ec852f43d44b9fda30622e9fef841168f5746f54e9cd8e236bd27fabe`。

2026-10-29 10:19:15+08:00 新容器已启动并核验镜像 ID、唯一只读权重挂载、64GiB shm、sleep 入口、启动脚本可执行和模型 config 可读；回执 `user-container-result.json`。原模型服务保持运行。
