# dsh headless：在私有 workspace 编辑代码与运行 CPU 测试

这是已核验配方，适用于任务级恢复；不修改共享 profile、关闭 sandbox、增加可写根或授予
`danger-full-access`。当前已在 mx-104 与使用私有静态 runtime 的目标 Host 的合成代码任务实证；真实模型服务、GPU、通信和
容器资格仍按各案例原流程核验。

## 为什么需要任务级收紧

2026-11-16 现场发现两项与 API 传输故障不同的执行限制：

- 使用私有 runtime 的目标 Host 没有 bwrap，安装版自动回退到 Landlock ABI1。基础打开写入会被拒绝，但自建
  outside canary 的 `os.truncate()` 成功；缩小 workspace 不能补出缺失的 TRUNCATE 能力。
- 104 的默认 bwrap 以 Host root 启动时保留 SYS_ADMIN 等 capabilities。仅增加
  `--cap-drop ALL` 又会留下非零 bounding set；过早加入的 `/run` 遮罩也会被后续根挂载覆盖。

因此，backend 的 `full` 标签或普通 write 负例不足以单独作为代码执行准入。

## 每个案例的配方

1. 在该任务已授权的案例根内 exclusive 创建唯一子目录，将 `workspace/`、
   `outside-canary/`、`commands/`、`results/` 分开。核 owner、权限、规范路径和空间；
   不覆盖既有任务。以精确 `workspace/` 为 cwd，不加 `--add-dir`。
2. 核实真实 bwrap、setpriv 和解释器绝对路径、owner、不可被 group/other 写入的 mode、
   版本与 SHA。另一 Host 即使系统版本相同也必须重新取 pin。
3. 使用案例私有 runner，严格只接受安装版 dsh 的精确 read-only / workspace-write 挂载
   参数；后者只能包含当前唯一 workspace 和后端原有临时目录。额外 bind、其他根、
   未知选项或缺少 `--` 必须失败。使用 `execv` argv，保留原命令参数，不用 shell 拼接。
4. runner 调用真实 bwrap，先 `--cap-drop ALL --cap-add CAP_SETPCAP --unshare-net`，
   再保留 dsh 原挂载参数，**其后**追加 `--tmpfs /run --remount-ro /run`。命令侧包入
   已核 setpriv：`--bounding-set=-all --inh-caps=-all --ambient-caps=-all
   --no-new-privs -- <原命令>`。中间 SETPCAP 只供可信工具下降 bounding；请求代码执行时
   四组 capabilities 必须全零。
5. 通过本任务 `--patch` 设置已核入口 `id: sandbox`、
   `name: '@deepseek-ai/dsh-sandbox-local'` 的 `config.runnerCommand` 指向该私有 runner，
   用真实字段 `runnerFailureSignatures` 明确失败签名；保持 `workspace-write/never`。不能用 `/usr/bin/false` 假装选择
   后端，也不能把说 Landlock 方言的程序放到接收 bwrap 方言的接口中。

当前已测 runner 硬绑定一个合成 workspace。它只能作为审查参考；其他 case 必须重新生成
并审核精确根与 pins，不能直接复制后移除 validator。

在原任务明确授权的 Host、私有代码和工作目录范围内，执行者可自行完成上述准备和验收，
无需为正常任务级配置再次请求人工确认。共享安装、全局 profile、额外可写根、服务或设备
权限的变更不由该配方授权。

## API 前准入与实际工作验收

先用完全相同参数做原生检查，命令与源码 SHA 在执行前留档。要求：

- 请求代码及再次 exec 后 `CapEff/CapPrm/CapBnd/CapAmb` 全零、`NoNewPrivs=1`；
  mnt/net namespace 与 Host 不同；常见 Docker runtime socket 路径不可见。不连接真实
  socket、不做 remount 或逃逸测试。
- inside 合成写入允许；预先存在且 Host 可写的 outside canary 的 open/write、truncate、
  unlink 均以明确 EACCES/EPERM/EROFS 拒绝，前后内容 SHA/size 不变；read-only 写入拒绝。
  不把 ENOENT 或任意异常当作 sandbox 成功。
- 独立冻结测试先真实失败，测试内容 SHA 固定。新 session 只处理获授权内容；先证明一次
  fs 编辑工具对自建 outside canary 返回 `FS_SANDBOX_DENIED`，再修改唯一代码文件并运行
  冻结测试。禁止 escalation、改测试迎合实现或意外写入后静默恢复证据。
- 核原生工具 catalog、实际调用/结果、source diff、测试/canary/control 前后 SHA、退出及
  cleanup。文件编辑工具使用独立的进程内路径围栏，shell 原生负例不能替代其负例。

若该版本未持久化 foreground 的 numeric exitCode，明确标为缺失；可以核安装版 renderer
源码与原始完整结果的确定映射，不能以 CLI `completed` 或模型 final 自述代替退出证据。
本次采用此源码绑定闭合，没有重复运行 API 或单测。

## 已验证案例与限制

| Host | 任务私有 runtime | 实际编辑与测试结果 |
| --- | --- | --- |
| mx-104 | 现有已核 bwrap + 私有收紧 runner | 新 session 只改一行；一次冻结 unittest 的两项 test 通过；原退出数字未持久化，由绑定 renderer 与完整回执确定为0 |
| 私有 runtime 验证环境 A | 复制已核静态 bwrap 到本任务私有 bin，独立 setpriv pin | 新 session 只改一行；只读冻结 launcher 恰运行一次两项 test，实际工具输出 `DSH_TEST_EXIT_CODE=0`；0 API重试 |
| 私有 runtime 验证环境 B | 同上，路径与 pins 独立验证 | 同样完成唯一代码修改、一次两项 test，实际工具输出 `DSH_TEST_EXIT_CODE=0`；0 API重试 |

三机都实际验证了 fs 编辑工具对 outside canary 返回 `FS_SANDBOX_DENIED`，没有 escalation；
测试、outside fs canary、runner 与控制文件 SHA 保持，工具表为 `bash/edit/glob/grep/read`。
最初 `triangular(n)` 公式 `n*(n-1)//2` 被改为 `n*(n+1)//2`；独立参考是 `sum(range(n+1))`。
104 baseline 四个数值 subtest 失败，修复后两项 test 通过。先前 Landlock truncate 实验改变
的独立 canary 完整保留，未误写成 API 期间越界。

使用私有 runtime 的目标 Host 未另跑初始 baseline，复用104完全相同 source/test SHA 的初始失败证据；两机本地
实际各只运行一次修复后的冻结测试，两项通过，不将复用证据写成各自已跑过 baseline。

使用私有 runtime 的目标 Host 的 bwrap 是从104已核的非 setuid、无 file capability、静态公开工具字节，经控制通道
复制到各任务唯一私有目录；没有安装到系统目录或修改全局 PATH/profile。不能把它的成功
归到旧默认 Landlock 上。每台 Host 的 runtime 与 SHA、原生负例、codework 回执、失败候选和控制 manifest 均保存在对应任务批准的外部产物目录。

其他 Host 的私有 bwrap 引入必须由其独立单元取 pin、原生
验收后再使用。此配方不等于完整 Host 安全隔离审计，也不替代真实 Host/设备生命周期
管理权限；[静态 read/search 配方](../scripts/templates/dsh-static-review.README.md)仍适用于
只读审查。

撤回该配方时停止对应 codework session，转到已验证的静态审查或原内置执行者；不要移除
收紧配置后继续以旧默认 partial Landlock / root-capability bwrap 运行代码。网络请求、设备
节点与 Host runtime IPC 被本配方主动隔离，需要它们的测试仍须另行按实际授权设计并验证，
不能自动增加挂载或改为全权限。
