# maint-005：清理其他 Qwen-VL 容器

状态：completed-container-cleanup-model-service-not-running。用户明确要求删除当前容器以外的其他 Qwen-VL 容器。仅 mx-104；保留 `qwen3vl-pr943-split1-mx104-20261023`，不停止/重启该容器或其现有服务，不改源码、镜像、volume 和宿主机文件。不触碰 Qwen3.6/3.8、GLM、Kimi、DeepSeek 等其他模型。

## 范围与保护

只读清单共 8 个目标：release-erqa-20261026、release-gpqa-20261026、release-splits-20261026、split0-erqa-20261025、fixed-splits-eval-20261024、fixed-splits-20261024、gpqa-20261023、erqa-20261023（全名及精确 ID 保存在已归档脚本）。7 个 running 但仅有 idle sleep/tail/init/bash，1 个 exited；均无模型/评测任务。匹配规则必须以独立 VL 标记结尾或分隔，不能误匹配 qwen38_vllm 等其他模型。最终删除只用固定 8 个 ID，不执行 prune 或宽泛模式删除。

## 产物与执行

已确认大部分历史证据位于 Host bind mount，保留原路径。两个评测容器另有新 opt12 case 私有副本，归档全部私有案例文件；两个实验/发布容器私有 Git 工作区按 tracked/untracked 文件完整归档（排除可重建缓存/权重和 Git 历史，镜像保留）。每个归档包含源文件 SHA 清单，逐文件解包读取核验后才允许删任一容器；已退出 evaluator 只读 docker diff 确认无未挂载 case 结果。

执行脚本 /public-flash/jinghao/qwen3-VL/20261027-qwen3vl-container-cleanup/commands/cleanup_containers.py，SHA `29aa2bc05e17f32e394947d972cf07662b8a56d9e09c68d9f070f443c6da5c10`。先归档所有目标、再次核验精确身份与空闲状态，再 docker stop / docker rm（无 -v）；不自动删除镜像或 Host 数据。前后比较保留容器身份、挂载和服务 readiness，比较无关容器以及镜像清单；原始清单/归档留在 /public-flash/jinghao/qwen3-VL/20261027-qwen3vl-container-cleanup。

## 验证和边界

维护任务，不是精度/性能实验；不发生成请求、不复用旧精度 gate。待执行后补充结果。私有源码归档是恢复材料，不保证容器全部 cache、site-packages、完整运行环境可一键恢复；镜像和持久化评测证据继续保留。

## 删除后校验修复（无重复删除）

8 个目标均已删除后，原脚本在比较无关容器时因 Docker Mounts 数组顺序不稳定触发断言。原命令/事件保留，不重放清理；独立只读 final_audit.py 逐 ID 验证目标消失、所有其他容器仍存在且 image/running 状态不变、保留容器完整配置及 readiness。小挂载集合通过排列还原原始 hash；大挂载集合原来只有未规范化 hash，无法追溯全配置，明确记录此限制，不伪称所有字段有完整 before/after 证明。

补充命令：`/public-flash/jinghao/qwen3-VL/20261027-qwen3vl-container-cleanup/commands/final_audit.py`，SHA `cac965eb64702460fb8729821f928a74e8ae17aa9d31f46da9b07ef9bf59b6b6`，归档后执行，仅写回执，无容器操作。

补充最终审计 v2：`/public-flash/jinghao/qwen3-VL/20261027-qwen3vl-container-cleanup/commands/final_audit_v2.py`，SHA `0ae63cc69c66b3d8dc121e4b294acb876b6afb6b022ca507880afc25d418fcab`。v1 只读审计遇到保留容器内9999连接拒绝，复查未发现模型进程，不能强称服务健康。v2 如实记录模型未运行，不自动启动/重启；容器清理仍已完成，保留容器自身仍运行且配置未改。模型退出原因尚未建立，不能归因容器删除或假称用户停服。

## 最终结果（2026-10-27 12:32 北京时间）

8 个目标容器全部移除，272→264；Qwen-VL 仅剩 `qwen3vl-pr943-split1-mx104-20261023`。所有其他263个容器 ID/image/running 状态保留；其中226个完整原字段指纹核验（允许 Mounts 顺序置换）通过，37个多挂载容器受原快照仅保存未规范化 hash 限制，不宣称其全部配置有完整独立比对证明。停止/删除命令只使用8个精确ID，无 prune、rmi、volume 删除或 Host 数据清理。目标镜像全部仍存在。

四份私有 Git 源码/评测文件 tar.gz 已逐文件 SHA 验证，共32011文件；其他评测材料在原Host bind mount，原路径保留。归档清单 /public-flash/jinghao/qwen3-VL/20261027-qwen3vl-container-cleanup/manifests/archives.json，SHA `8863454bd1258256399fc1d88e0b8c165d2eeea7055402b9cf27356825016f81`。最终回执 /public-flash/jinghao/qwen3-VL/20261027-qwen3vl-container-cleanup/results/completed.json，SHA `48e299b503f1d90071ca32168666d01b352087345a6d03f1e5d4b2c881ed5026`。

保留容器 init身份/配置/挂载未变、仍running，Attention源码仍精确PR638（SHA f49f4a5b...）。但最终9999连接拒绝，实际未发现模型serve进程；未主动重启恢复，不能声称模型服务健康。只读快照只能确认当前状态，未建立退出原因。该情况已明确通知用户，不能归因于旧容器删除或未经证据称用户主动停服。

原删除后校验失败和只读HTTP检查失败保留为工具/健康观测，不重放删除；最终规范化核验限制写在 /public-flash/jinghao/qwen3-VL/20261027-qwen3vl-container-cleanup/results/verification-incident.json，SHA `f6ad5318e5dc591a4cf8227b71a98a1620cdf8628c3c018c9c1db33da6b5186f`。不签精度gate，不追加精度/性能任务。
