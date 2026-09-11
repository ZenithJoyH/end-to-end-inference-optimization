# 容器复刻与共享源码隔离

每次实际优化仍从用户指定的适配容器创建新优化容器，保持所有目录挂载的 Source、Destination、访问模式、传播和 volume subpath 一致。这里明确相同挂载下的源码隔离方法，不放宽原服务保护规则。

用户可以另行提供目标 Host 上的远程工作目录，用于保存本案例的 Host 侧控制文件和远程原始产物。始终在其下创建唯一 case 子目录并记录规范路径、权限、空间和校验信息；不得覆盖既有内容。该目录不是新的容器挂载来源：只有它已存在于源容器挂载清单时才能以完全相同的映射供优化容器使用，否则通过 Host 侧编排或不改变挂载清单的 runtime 文件传输收集产物。

## 执行分支

1. 只读获取源容器 inspect、镜像身份、必要 writable layer 改动、目录挂载和实际导入路径。检查设备、端口、主机资源及共享使用者。源容器不承载本任务 benchmark/profile 或源码修改。
2. 若有效适配状态在 writable layer，先保存并核验不可变快照；仅镜像 ID 相同不能证明 writable layer 内容相同。镜像谱系验证需要源状态、快照/内容指纹和导入证据，不能由挂载比较工具自动授予。
3. 创建新容器并比较 inspect：

   ```bash
   python3 scripts/verify-container-mounts.py \
     --source-inspect /external/source.inspect.json \
     --optimization-inspect /external/optimization.inspect.json \
     --output /external/mount-comparison.json
   ```

   输出保存规范化清单与差异；非零退出表示失败。工具保守地同时比较 file bind，并保留未知挂载类型；不检查或更改运行中的容器。它不会将 `image_lineage` 标记为 verified。
4. 如果待修改源码位于优化容器自己的 writable layer 且未被其他服务使用，记录指纹和已有修改后直接在该副本实验。
5. 如果源码位于共享挂载，在优化容器**未被任意挂载覆盖的私有目录**建立源码副本，保留 revision、未提交补丁及内容指纹；不得改变原挂载或通过符号链接假装隔离。只在优化容器内调整 editable 安装或导入路径，检查 site-packages 是否也被共享，禁止向共享安装目录写入。
6. 在任何测量前，从每个 worker 核验 Plugin、FlagGems 的 `__file__`、版本、源码内容以及实际 dispatch 命中。私有副本与源有效代码内容先保持一致，完成新容器 baseline 后才引入候选变化。构建/JIT/response cache、日志和输出也应使用独立路径，记录会影响可比性的变化。
7. 容器内部不存在可安全隔离的源码/安装位置，或需要更改挂载、共享配置、vLLM、基础镜像时，先形成具体方案与回退方式，再按既有授权判断是否需用户批准；不能写共享源码继续实验。已明确批准的例外记录批准依据，不重复申请。

## 留存与回退

项目记录镜像谱系证据、挂载 diff 位置、源码原/新导入路径、revision、已有改动及补丁 SHA。完整 inspect 和日志放入用户提供的远程案例目录或其他已明确的外部产物目录，项目记录绝对路径、清单和必要 SHA；不写入凭据或完整环境变量。

回退只针对本任务优化服务：恢复该服务的原私有源码、启动配置并验证 readiness、实际导入路径和 smoke。操作前重新解析当前服务身份，不执行历史 PID。源适配容器保持原状。
