# dsh 静态审查工具配置

`dsh-static-review.patch.yml` 是任务级 overlay，不修改共享 profile。已在
dsh `0.2.2-rc.1` 的目标环境验证；原生请求工具 schema 恰为 `glob`、`grep`、`read`，
一次真实 `read` 调用完成。它移除了任意 shell、后台任务、workflow、subagent、网络工具
和文件修改工具；`glob`/`grep` 使用固定 ripgrep argv，不经 shell。

仍须给任务列出精确读取范围；该配置不提供读取路径白名单，也不证明 Host PID、设备或
容器视图完整。不要为静态审查选择 `danger-full-access`。

## 使用

先在目标安装版本上检查组合配置。`--patch /dev/stdin` 已实测可从标准输入读取 overlay，
无需在远端保存新配置文件：

```python
subprocess.run(
    ["/usr/local/bin/dsh", "--profile", "headless", "--patch", "/dev/stdin",
     "--dump-config"],
    input=overlay_text, text=True, capture_output=True, check=True,
)
```

完整 dump 可能含认证配置，必须仅提取工具 entry 的 id、name、disabled 和安全配置字段，
不要直接显示或长期保存原文。确认无 warning、id/name 匹配且执行工具全部禁用后，新建会话：

```python
subprocess.run(
    ["/usr/local/bin/dsh", "--profile", "headless", "--patch", "/dev/stdin",
     "--json", "--permission-mode", "read-only", "--approval-policy", "never",
     exact_static_review_task],
    input=overlay_text, text=True, capture_output=True, cwd=verified_task_root,
)
```

任务用位置参数传入；标准输入已供 overlay 使用，不能同时用 `-` 读取任务。也可在原任务
获授权的 `commands/` 下保存唯一 overlay 文件，用其绝对路径传给 `--patch`，再使用原任务
文件作为标准输入。不要覆盖共享 profile、复用正在运行的 session 或扩大任务目录。

每次升级先核对静态组合，再用新会话验证原生 `request/header` 的 `data.header.tools`
只有 `glob`、`grep`、`read`，并保留真实工具回执、final 和退出状态。出现额外工具、
未知 entry、名称不符或加载警告时停止使用，重新核验。失败时移除本次 `--patch` 即撤回
该调用配置；不得因此把原审查任务切到更宽权限运行。

## 本次证据

- Overlay SHA256：`f538c9dd3222071ce93451906b35d31265799178e1dab3547a227000c654c80a`。
- 使用者应在对应任务的外部产物目录记录实际 session、原生工具回执及必要 SHA；模板不绑定某个历史 session。
