# env-010：保存移除遗留环境变量的镜像

状态：**完成**。2026-10-28 10:19:37 CST，在 `mx-104` 保存当前 B 容器，生成本地 Docker 镜像；未推送。此次仅维护镜像，未恢复性能回归，未运行精度或推理请求。

| 项目 | 结果 |
|---|---|
| 来源容器 | `qwen36-27b-regression-b-20261022` |
| 新镜像 | `qwen36-27b-metax-optimized:20261028-clean-env` |
| 镜像 ID（当前 Docker OCI manifest） | `sha256:f001fd92fbc72300a67a6547530a9a59ef725cdb2027ae6f8044c54e6c849a8b` |
| 配置 blob digest | `sha256:26ae456985032aba7ebff6add17b056c77c6b8d21081b545773a9874fcc9089d` |
| Docker 报告大小 | 9,186,966,619 bytes（约 9.19 GB） |
| 移除项 | 镜像 `Config.Env` 中的 `VLLM_FL_METAX_CONTIGUOUS_SINGLE_PREFILL`，真正删除 key |
| 保留项 | 其他全部镜像配置、17 个 rootfs diff ID、代码及本地修改、Git 状态、全部包版本及 editable 安装、shell 配置 |
| 当前服务 | API / Engine / 两个 worker 的 PID、启动时间、完整环境哈希均一致，health 200；未暂停、停止或重启 |
| 当前源容器 | Config、HostConfig 和 Mounts 完全未改；原容器及当前进程已继承的旧变量值仍保留 |

新镜像 `Config.Env` 保留原 PATH；其他启动时手工 export 的配置仍由原 shell / 启动脚本负责，不额外固化为新的镜像 ENV。已有 shell 内容（包括 env-009 的 unset）保持不变。原有版本描述 labels 可能包含历史版本，按用户要求原样保存；实际源码与安装指纹为准。

模型 `/data/Qwen3.6-27B`、启动脚本和结果位于外部挂载，Docker commit 不会嵌入这些数据。以后用此镜像新建容器时，仍需原 `/data`（rw/rslave）和 `/public-flash`（rw/rprivate）挂载及相应设备、网络、IPC 等运行参数。本轮未创建替代模型服务。

## 实施与验证

使用当前 Docker 29.1.2 支持的 `docker commit --no-pause` 保存文件系统；通过标准 `docker save` / `docker load` 边界修改导出的 OCI / Docker 元数据，只删除目标 ENV，更新配置及 manifest 摘要。未操作 daemon 内部文件。所有层数据原样传递，最终 rootfs 和其他镜像配置逐项比较通过。

只读、无网络、无 GPU、CPU1 / 内存2G 的临时校验容器核对四个实际包的内容哈希、Git HEAD / branch / dirty 状态及 diff 哈希、全部安装版本和安装来源哈希、shell 文件与保护目录。新镜像与源容器指纹完全一致，仅遗留环境变量读取结果变为 absent；校验容器自动删除。源模型只接受 health 检查，无额外推理。

正式加载前独立检查计划：其他 config / history / rootfs 相同，全部 17 个 OCI layer descriptors 未变，无 layer member 被替换。加载后复验新镜像、源代码、安装及当前服务。仅在通过后删除本任务中间快照 tag 及 9,186,988,544 bytes 临时归档；最终镜像和小体积计划、回执保留。未删除源镜像、源容器或挂载文件。

## 原生产物

远端根目录：`/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression`。

- 证据目录：`manifests/env010-clean-image-20261028/`；包含原容器配置、前后指纹、快照和最终 inspect、配置差异、元数据计划、CPU 验证与命令日志。
- `receipt.json` SHA256：`b2361a4c226dd04c2e16cc1864a35a119b1ef06885b16b761ebf676fb53eaf82`。
- 已审阅并执行的 `plan.json` SHA256：`d2c6b33e179a8c6fb365785e904762a19e1cfc641fc39cc6b6174f820c9538aa`。
- 最终控制命令：`commands/env010-clean-image-v3-20261028.py`，SHA256 `442b9750f5fbed7b465edc93f4680e744be3aa9561c3888d7fd2274842940b1f`。应用参数为 `--apply-plan-sha256` 加上述计划 SHA，执行前已登记。

## 准备阶段记录

以下保留执行前登记和两次安全停止的事实。V1 在 commit 后因空 User 与省略 User 的表示差异停止；二者都是默认 root，未改变用户语义。Docker 仅用于运行时的 Hostname / Attach / TTY 等字段保留于原容器配置，正常不会进入 OCI image config。V2 通过镜像及 live 验证并保存归档，随后发现当前 Docker image ID 是 OCI manifest digest、不是 config digest，因原先的错误假设停止。V3 按实际 index / manifest / config 摘要关系验证并继续使用同一个快照与归档，没有重复 commit 或 save。两次停止均在最终镜像加载前，未改模型服务。

# env-010: Preserve optimized container as a clean local image

User explicitly requests a new image from current B with residualVLLM_FL_METAX_CONTIGUOUS_SINGLE_PREFILL absent, preserving optimizations/all other environment/config and no impact to running model. Onlymx-104/B containerID5b198123/image50b91afb. No source service pause/stop/restart/signals or inference; no registry push or package/source changes.

Target newtag qwen36-27b-metax-optimized:20261028-clean-env. Temporary source snapshot tag qwen36-27b-metax-optimized:20261028-env010-source-snapshot; require both absent. Current installed Docker29.1.2 explicitly supports commit --no-pause. Save currentfilesystem via this flag, verify source and CPU-only snapshot identity. Never use default-pausingcommit.

Native DockerfileENV or commit-change cannot truly unset an inherited key. Use standardDocker save/load archive boundaries: edit only exportedOCI/Docker JSON metadata, remove exactly that Env entry (not setempty), update config/manifest descriptor hashes/sizes and final tag. Copy every filesystem layer member byte unchanged; verify rootfsDiffIDs equality afterload. Do not edit Docker internal files or use containerd internal sockets. Preserve all other final imageConfig fields exactly versus snapshot, including original labels. Original version-label text may be historical; actual source/install fingerprints remain authoritative.

Before/after live source and imageCPU probes record 4 actual package content/GitHEAD/branch/worktree/diff identities, all installed versions and hashed install origins, exact shell init files, protectedcache/source backup roots. No GPU/kernel/model imports in probes; only find_spec/hash/metadata/Git. Verification containers are read-only/no network/CPU1/mem2G/no GPU and auto-remove; override only verificationcontainer workdir/entrypoint. Confirm currentAPI/Engine/workersPID/startticks/full-environ hashes/health at each checkpoint; preserve originalContainerConfig/HostConfig/mounts.

Mounted/data model weights and/public-flash scripts/results are not embedded bycommit; preserve originalbindings onfuturelaunch. Snapshot contains private/workspace and/opt repositories, existingedits/editable installs/MACA/Conda shellconfig and currentcompilationcache. Performance remainspaused. Source container/image untouched.

Temporary archive saved inside currentremote case with ample15TBspace, lowCPU/IO controller priority. Remove only this task-created archive and temporarysnapshot tag after finalcleanimage andlivechecks pass. Finalimage remains local inDocker; no tar export requested/retained. All small configs/plan/probes/receipts remain forrecovery/audit.

Command `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/env010-clean-image-20261028.py` SHA256 `07a84308cffc64be593922cd00da47328e7d1aa75e10583b4eff715fcfa80023`, syntax passed. Prepare creates non-pausing snapshot/exports and metadata plan only; final load requires reviewedplanSHA. Evidence /public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/manifests/env010-clean-image-20261028. Status preparing.

Preparation v1 stopped after successful non-pausing snapshot because User empty string was omitted in image metadata. Snapshot c03f54e36462 is preserved; no duplicate commit. Reviewed default-root semantic equivalence; Docker runtime-only TTY/attach/hostname fields are retained in container-before.json for future run, not imageConfig fields. V2 resumes this exact snapshot and keeps every effective image config field; final comparison remains exact against snapshot except the target Env removal. Command `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/env010-clean-image-v2-20261028.py` SHA256 `397362c4a11e68a6d3f3171f8449cecbb4f116b8b5ed85d768efb27cc6479dac`, syntax passed; invocation `ionice -c 3 python3 /public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/env010-clean-image-v2-20261028.py`.

V2 snapshotCPU/source/service/save verification passed. Metadata preparation stopped before any write/load: Docker29 containerd store image ID is OCI manifest c03f54e36462, not config blob897ee707c8aa; effectiveConfig is equal and all17 diffIDs match snapshot. V3 validates original index manifest digest plus config blob digest/effectiveConfig/all diffIDs, computes final image ID from updated manifest, and resumes existing archive without duplicate commit/save. Command `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/env010-clean-image-v3-20261028.py` SHA256 `442b9750f5fbed7b465edc93f4680e744be3aa9561c3888d7fd2274842940b1f`, syntax passed; invocation `ionice -c 3 python3 /public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/env010-clean-image-v3-20261028.py`. All failed assertions retained; no filesystem/source/service changes.

Metadata plan reviewed before load: `d2c6b33e179a8c6fb365785e904762a19e1cfc641fc39cc6b6174f820c9538aa`. Independent read-only semantic check passed: only target Env removal in config; other config/history/rootfs identical;17 OCI layer descriptors unchanged and no layer member is replaced. NewConfig digest26ae456985032aba7ebff6add17b056c77c6b8d21081b545773a9874fcc9089d; expected image manifestIDf001fd92fbc72300a67a6547530a9a59ef725cdb2027ae6f8044c54e6c849a8b. Archive9186988544B. Authorized apply invocation (same registered V3 controller): `ionice -c 3 python3 /public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/env010-clean-image-v3-20261028.py --apply-plan-sha256 d2c6b33e179a8c6fb365785e904762a19e1cfc641fc39cc6b6174f820c9538aa`. Load, CPU/liveverification then only task-temporary tag/archive cleanup; no source signals or restart.
