# 非算子瓶颈：有界取证工具步骤

本页是 [system-bottlenecks.md](system-bottlenecks.md) 的执行配方，按问题选一节，不串跑全套。已有报告足够或有界未知结论可用就 `analyze`；只有影响排序的剩余缺口才在 C5 原预算内补证。新采样命令面向目标 Linux，离线分析按实际工具环境执行；文档不代表已执行/支持，不在本机 macOS 上 attach。

目录：[预检](#preflight) · [CPU](#cpu) · [等待](#waits) · [时间线](#timeline) · [通信](#communication) · [rank](#rank) · [请求/调度](#request-scheduler) · [KV/graph](#kv-graph) · [系统资源](#system) · [交付](#return)

<a id="preflight"></a>
## 1. 按证据类型准备，每次只派一个操作

已有有效报告、rank/log 对照或离线 trace 分析，只核原报告身份/SHA、范围、窗口及对当前决策的适用性；不要求源进程仍存活、目标 Linux、重新连接远端或新采样预检。直接阅读不必建新输出目录；需要派生文件时，在已批准的本地或远端外部目录使用唯一输出。目录创建不是 capture、不是新 review。

只有新采集才核授权 Host/独立优化容器与实际资源：PID attach/线程采样核目标 namespace 的 PID/TID/角色，关联 Host↔容器映射、启动时间和采后身份；NIC-only 核接口/namespace，metrics-only 核 endpoint/服务身份，均不要求一个无关活 PID。不能把两 namespace 的同号 PID 当同进程，不导出完整 argv/environ 或密钥。工具/权限/挂载门禁按实际操作核验，离线复用不重做运行预检。

下面各 recipe 是**单独派发的一个操作正文**，不能把多个采样块盲拼成同一任务。每次由原协调者按 C5 查已有/在途覆盖，发放原任务实际剩余额度和本操作额度；采集、工具退出、导出/解析、身份复核与回收都计入预算。采样窗口必须预留结束/回收时间，不能换 recipe/新目录就把 remaining 重置。以下检查仅做入场核算，**不是自动 deadline 控制器**；完整操作由已核原任务监督按额度约束，缺少安全有界退出/回收能力时返回缺口，不擅造跨工具 timeout 接口。后续解析是另一个有界只读操作，先复用数据，绝不顺带重采。

执行前把准确配置、下列轻量包络与**一个**选定 recipe 保存到唯一 `commands/` 文件，先 `bash -n` 再派发。占位符现场替换，不 `source` 未审配置；`operation_cap_s` 及 `remaining_budget_s` 必须来自同一原任务的本次分配，不是新预算。

```bash
set -euo pipefail
set -o noclobber
case_root='/REPLACE/approved/absolute/case-id'
operation='REPLACE_OPERATION_NAME'
remaining_budget_s='REPLACE_CURRENT_REMAINING'
operation_cap_s='REPLACE_THIS_OPERATION_CAP'
finish_reserve_s='REPLACE_EXIT_PARSE_RECOVERY_RESERVE'
window_s=0  # 采样操作在此填正窗口；不能通过入场核算后再增大
target_pid=''  # 仅PID采样填已核PID；离线/metrics/NIC-only保持空
case "$case_root" in /*) ;; *) exit 2 ;; esac
case "$operation" in ''|*[!A-Za-z0-9_-]*) exit 2 ;; esac
for value in "$remaining_budget_s" "$operation_cap_s" "$finish_reserve_s"; do
  case "$value" in ''|*[!0-9]*|0) exit 2 ;; esac
done
case "$window_s" in ''|*[!0-9]*) exit 2 ;; esac
test "$operation_cap_s" -le "$remaining_budget_s"
test "$((window_s + finish_reserve_s))" -le "$operation_cap_s"
test -d "$case_root"
rout=$(mktemp -d "$case_root/$operation.XXXXXXXX")
trap '
  operation_rc=$?
  trap - EXIT
  set +e
  date -u +%FT%TZ > "$rout/end.utc"
  printf "%s\n" "$operation_rc" > "$rout/exit-code.txt"
  if test -n "$target_pid"; then
    if ps -p "$target_pid" -o pid=,ppid=,lstart=,comm= > "$rout/process.after" 2> "$rout/process.after.stderr"; then
      awk "/^(Name|Tgid|Pid|NSpid|Cpus_allowed_list|Mems_allowed_list):/" "/proc/$target_pid/status" > "$rout/process.after.scope"
    else
      printf "process identity unavailable; scope partial\n" > "$rout/process.after.gap"
    fi
  fi
  exit "$operation_rc"
' EXIT
date -u +%FT%TZ > "$rout/start.utc"
if test -n "$target_pid"; then
  test "$(uname -s)" = Linux
  case "$target_pid" in *[!0-9]*|0) exit 2 ;; esac
  test -d "/proc/$target_pid"
  ps -p "$target_pid" -o pid=,ppid=,lstart=,comm= > "$rout/process.before"
  awk '/^(Name|Tgid|Pid|NSpid|Cpus_allowed_list|Mems_allowed_list):/' \
    "/proc/$target_pid/status" > "$rout/process.before.scope"
fi
```

`case_root` 先核规范路径/符号链接、owner/权限/空间，不能是 `/`、home/权重/共享源码根。每操作独有 `rout/cmd`，不复用上一块 shell 状态；工具自己的输出也必须是新文件。此 EXIT 包络保留原退出码和部分报告，不签发有效性/充分性结论，也不保证超时后子进程/异步导出已结束；由原任务核验并回收。采后PID消失/重用、namespace/服务或接口身份变化标对应 scope partial，不自动复采。结束记录失败本身也须保留原监督日志，不能改写成成功。

只发现本操作实际用到的工具：`command -v TOOL`、实际版本/帮助，例如 `pidstat -V`/`pidstat --help`、`py-spy --version`/`py-spy record --help`、`perf --version`/`perf record -h`、`perf report -h`、`curl --version`/`curl --help all`。帮助用非零显示用法时单独留其原码/内容，不用 `|| true` 掩盖采集失败。工具/权限/符号不足就保留已有有效 scope 与缺口，不安装、sudo、改 ptrace/perf/sysctl、增加容器权限或开全局探针。

每操作的 start/end、实际样本/计数窗口和身份分别解释；先 pidstat 20秒再 cgroup 20秒不是同窗因果。确需联合窗口时由协调者派一份有界操作：before counters→一次选定采样→after counters，复用同一报告，不重复 sleep/采样或默认同时 attach 多 profiler。单次 capture 可服务多个诊断分支，按原身份映射覆盖，只补其剩余缺口。

<a id="cpu"></a>
## 2. CPU：先线程区间统计，再选择一种调用栈

**先看区间线程 CPU 与切换。** 已核实 pidstat 支持以下参数后执行；显式 count 防止无限运行：

```bash
test -n "$target_pid"
test "$window_s" -gt 0
cmd=(pidstat -u -w -t -p "$target_pid" 1 "$window_s")
printf '%q ' "${cmd[@]}" > "$rout/command.txt"
"${cmd[@]}" > "$rout/threads.txt" 2> "$rout/stderr.txt"
```

按 TID/角色对齐 `%usr/%system/%CPU`、自愿/非自愿切换与同窗口进度，说明是否按单核口径；不加 `-I` 后又把百分比当单核。`ps %CPU` 多为生命周期均值，不作本窗口 CPU 证据。单线程满核而全机平均低仍可能限速；切换高不自动证明 GIL/锁或因果。CPU低且提交慢转[等待/配额](#waits)，关键线程 on-CPU 高才选下列一种栈；现有栈已足够不再重采。

**Python 栈（可选 native 视角）。** 先确认 Python 构建/工具兼容和 attach 权限：

```bash
test -n "$target_pid"
test "$window_s" -gt 0
cmd=(py-spy record --pid "$target_pid" --duration "$window_s" \
  --rate 49 --output "$rout/stacks.svg")
# 只有本问题需 native 且现场帮助/平台支持已核实，才在执行前选用：
# cmd+=(--native)
printf '%q ' "${cmd[@]}" > "$rout/command.txt"
"${cmd[@]}" > "$rout/stdout.txt" 2> "$rout/stderr.txt"
```

栈中样本比例不是端到端延迟占比，记录睡眠线程过滤、采样数/失败及 native 展开率。`--gil` 仅是筛选持 GIL 样本的视角，不证明其他线程等待它；native/GIL 栈均不提供完整 off-CPU 时长。符号/权限不足时保留已有线程统计和未知 native 部分，不重复盲试所有选项或自动跟踪所有子进程。

**native on-CPU 栈（与 Python 采样择需，不默认同时跑）。** 以下用目标 PID、用户态软件时钟事件与有界采样；先核 `cpu-clock:u`、fp 展开、`--no-inherit` 可用性：

```bash
test -n "$target_pid"
test "$window_s" -gt 0
cmd=(perf record -e cpu-clock:u -F 49 --call-graph fp --no-inherit \
  -p "$target_pid" -o "$rout/perf.data" -- sleep "$window_s")
printf '%q ' "${cmd[@]}" > "$rout/record.command"
"${cmd[@]}" > "$rout/stdout.txt" 2> "$rout/stderr.txt"
```

采集操作到此结束。已有有效/部分 perf.data 需要解释时，另派有界离线操作（包络中 PID 留空），读取已核文件，不重跑 record；record 非零不自动否定其中全部样本，report 失败也不反推需要重新采样：

```bash
perf_data='/REPLACE/verified/existing-perf.data'
test -s "$perf_data"
cmd=(perf report --stdio --no-children -i "$perf_data")
printf '%q ' "${cmd[@]}" > "$rout/report.command"
"${cmd[@]}" > "$rout/report.txt" 2> "$rout/report.stderr"
```

只解释实际覆盖的 PID/TID/线程生命周期；不继承采样可能漏新线程，不能写“全部 worker 已覆盖”。fp 缺 frame pointer 时栈可能截断，先标缺口/复用已有符号；确需改 DWARF 等方案须确认支持、开销和原预算，不为补符号再整轮跑 workload。样本解释运行中的用户态热点，不覆盖内核/阻塞/可运行等待，不将驱动等待墙钟当 CPU 自耗时。下一实验针对已证实的热栈/重复工作，检验提交空隙和目标主指标是否同时改善。

<a id="waits"></a>
## 3. 等待、配额、NUMA：快照是线索，delta 才描述窗口

**目标线程状态线索。** TID从已核角色映射选取，不扫描全机；保存本节准确命令后，用前后两次读取夹住同一 `window_s`：

```bash
test -n "$target_pid"
test "$window_s" -gt 0
target_tid='REPLACE_VERIFIED_TID'
case "$target_tid" in ''|*[!0-9]*|0) exit 2 ;; esac
for edge in before after; do
  date -u +%FT%TZ > "$rout/$edge.utc"
  awk '/^(Name|State|Tgid|Pid|Cpus_allowed_list|Mems_allowed_list|voluntary_ctxt_switches|nonvoluntary_ctxt_switches):/' \
    "/proc/$target_pid/task/$target_tid/status" > "$rout/$edge.status"
  if cat "/proc/$target_pid/task/$target_tid/wchan" > "$rout/$edge.wchan" 2> "$rout/$edge.wchan.stderr"; then
    :
  else
    field_rc=$?
    printf 'wchan unavailable; native exit=%s\n' "$field_rc" > "$rout/$edge.wchan.gap"
  fi
  if test -r "/proc/$target_pid/task/$target_tid/schedstat"; then
    cat "/proc/$target_pid/task/$target_tid/schedstat" > "$rout/$edge.schedstat"
  else
    printf 'schedstat unavailable\n' > "$rout/$edge.schedstat.gap"
  fi
  test "$edge" != before || sleep "$window_s"
done
```

`wchan`/State是瞬时线索，不是精确等待时长/等待对象因果；0、缺权限或线程消失保持缺口。schedstat 原始字段须按当前内核[调度统计文档](https://docs.kernel.org/scheduler/sched-stats.html)核语义/单位/启用状态，才比较同TID的区间运行/可运行延迟；未启用、缺失或零值不等于没有runqueue等待，不改sysctl来启用，也不由它推精确锁等待。更深 off-CPU/调度追踪只用已支持、已授权且能证明 PID 过滤及切出/唤醒/切回覆盖的工具或现有报告。不给默认全机 `perf sched record`/`-a`；仅对 PID 采部分 sched 事件可能漏切回，不能冒充完整等待证据。区分 runnable 缺 CPU、锁/IPC/I/O、设备等待和无任务正常睡眠，再决定是否值得补证。

**配额/cpuset 窗口。** 先读取目标 PID 的 `/proc/<pid>/cgroup` 及该观察 namespace 的 mountinfo 中相关 cgroup 挂载，核对 hierarchy、mount root/mountpoint 与命名空间映射。cgroup v2 的 `0::...` 不能直接拼成宿主 `/sys/fs/cgroup/...`；容器可见根可能重定位/隐藏父级。由已核映射填写下列路径，逐个确认是目标组/可见父级；v1另按其已装文档读取，不套本例单位：

```bash
test "$(uname -s)" = Linux
test "$window_s" -gt 0
cgdirs=('/REPLACE/verified/target-cgroup' '/REPLACE/verified/visible-parent')
printf '%s\n' "${cgdirs[@]}" > "$rout/verified-paths.txt"
for edge in before after; do
  for i in "${!cgdirs[@]}"; do
    mkdir "$rout/$edge-$i"
    for field in cpu.max cpu.stat cpuset.cpus.effective cpuset.mems.effective; do
      if test -r "${cgdirs[$i]}/$field"; then
        if cat "${cgdirs[$i]}/$field" > "$rout/$edge-$i/$field" 2> "$rout/$edge-$i/$field.stderr"; then
          :
        else
          field_rc=$?
          printf 'read failed; native exit=%s\n' "$field_rc" > "$rout/$edge-$i/$field.gap"
        fi
      else
        printf 'unavailable\n' > "$rout/$edge-$i/$field.gap"
      fi
    done
  done
  date -u +%FT%TZ > "$rout/$edge.utc"
  test "$edge" != before || sleep "$window_s"
done
if ! test -e "$rout/before-0/cpu.stat.gap" && ! test -e "$rout/after-0/cpu.stat.gap" && \
   test -r "$rout/before-0/cpu.stat" && test -s "$rout/before-0/cpu.stat" && \
   test -r "$rout/after-0/cpu.stat" && test -s "$rout/after-0/cpu.stat"; then
  awk 'NR==FNR {a[$1]=$2; next} ($1 in a) {d=$2-a[$1]; print $1, (d<0 ? "reset/invalid" : d)}' \
    "$rout/before-0/cpu.stat" "$rout/after-0/cpu.stat" > "$rout/target.cpu.delta"
else
  printf 'missing cpu.stat; delta unknown\n' > "$rout/target.cpu.delta.gap"
fi
```

仅在两份 `cpu.stat` 均有效且同一组身份时执行 delta；缺文件时交缺口，不把 `.gap` 填零。对可见父组同样计算，报告实际覆盖层级；不可见祖先保留限制。v2 `cpu.max` 的 quota/period 是容量约束，不是本窗口实际 CPU；`nr_throttled`/`throttled_usec` 增量只说明对应统计范围的节流，不能直接相加成请求延迟，字段/祖先口径随内核核实。结合 effective cpuset、线程区间统计及进度判断容器受限，不能看全机空闲就排除它。

NUMA先读允许核/内存节点及已安装 `lscpu --extended=CPU,NODE,SOCKET,CORE`、`numactl --show`、`numastat -p "$target_pid"`（各自先核帮助与权限）。`numactl --show` 仅描述运行它的进程策略，不替代目标 PID 的策略；目标策略需目标进程/启动或已核 `/proc/<pid>/numa_maps` 证据。远端节点分配不证明关键路径损失；资源放置实验由协调者在任务私有启动/分配内另派，不修改全局设置。

<a id="timeline"></a>
## 4. 主机提交与设备时间线

已有可信 trace/原生报告先分析：绑定 worker/rank/设备、phase/step、host enqueue、输入就绪、设备开始/完成及同步依赖，区分 CPU 处理慢、设备队列和正常等待。需要新 trace 才按入口 `capture/reprofile` 与已核平台工具补缺失范围；沿用 runner dry-run、导出有效性和原捕获回收，不给系统配方另造 trace 启停工具。

仅需分层导航时，对已有文件使用现成离线入口（先核当前 `--help`）；本地可读文件无需目标Linux、活PID或远端预检，只有新派生输出需要唯一目录：

```bash
trace_file='/REPLACE/verified/existing-trace.json.gz'
cmd=(python3 evaluation/performance/trace_analysis.py --trace "$trace_file" \
  --output "$rout/analysis.json")
printf '%q ' "${cmd[@]}" > "$rout/command.txt"
"${cmd[@]}" > "$rout/stdout.txt" 2> "$rout/stderr.txt"
```

此命令从项目根或已核工具副本运行；外部 trace 不意味着在错误容器重放。有效 annotations 已有且匹配 SHA 时再按 [trace-analysis.md](trace-analysis.md)加参数，不为填层归属重采。该工具不采 CPU 栈、off-CPU、NIC 或完整系统关键路径；缺字段/stream/rank保留 unknown，活动时长和也不是 CPU self time 或设备利用率。

<a id="communication"></a>
## 5. 通信：先关联服务操作，再决定原生 probe

1. 从已核 service/worker配置及现有启动/通信报告取实际库版本、backend/transport、组成员、设备/NIC路径，配置声明与实际命中分开。只截取对应group/时段，不默认全局 debug；首次开通信日志若需重启由协调者另派生命周期操作。
2. 在同组、同逻辑 step/collective序号及 dtype/shape/peer/字节范围，关联输入 ready、host enqueue、设备开始/完成、consumer等待。使用已有source-event位置与本地 elapsed；无clock对齐不相减跨host时间戳。晚到转CPU/rank，不能直接把 collective长归网络。
3. 低成本同窗口链路读数：先确认目标 NIC 的真实 namespace/名称/设备归属，再读下列快照；不是默认遍历全部网卡。

```bash
test "$(uname -s)" = Linux
test "$window_s" -gt 0
nic='REPLACE_VERIFIED_NIC'
case "$nic" in ''|*[!A-Za-z0-9_.:-]*) exit 2 ;; esac
printf '%s\n' "$nic" > "$rout/nic.txt"
for edge in before after; do
  mkdir "$rout/$edge"
  cat "/sys/class/net/$nic/ifindex" > "$rout/$edge/ifindex"
  for field in rx_bytes tx_bytes rx_dropped tx_dropped rx_errors tx_errors; do
    cat "/sys/class/net/$nic/statistics/$field" > "$rout/$edge/$field"
  done
  date -u +%FT%TZ > "$rout/$edge.utc"
  test "$edge" != before || sleep "$window_s"
done
```

按同 NIC 身份计算 before/after 增量和窗口长度；计数重置/设备切换不能相减。NIC总字节含其他进程，不等于该 collective payload、重传或物理带宽上限；RDMA/专有链路可能不由这些 netdev计数完整覆盖，须核对应原生计数器，不将缺值当零。错误增量支持排查线索而非单独证明根因。

4. 仍无法区分传输与组织、且会改变方案时，**只有已授权且独占的测量设备/NIC/CPU窗口**才做通信 probe；不得与服务争用。发现当前安装 native bench 的实际路径、版本/帮助、支持的库/设备/group/消息/dtype/预热/迭代/超时和退出语义，保存精确 argv 再执行。没有跨厂商通用 CLI；不能臆造统一 `--tp/--size` 参数。命令结构：`<已核限时工具> <本操作扣除结束回收预留后的采集时限> <已核native bench> <已核进程组/设备/消息范围/dtype/预热/迭代参数>`，所有占位项现场替换，未知则不执行。若该平台单个collective无法安全取消，只在原生命周期授权内控制本任务进程组，副作用未知先核验，不自动重试。
5. probe结果只解释匹配拓扑/消息范围的通信能力，与服务时序比较仍要算arrival、同步、pack/copy和争用。工具/权限/独占资源不足时返回有界结论与重开条件，不跨厂商fallback、改驱动/网络或换Skill重试相同缺口。

<a id="rank"></a>
## 6. rank：用原事件构造可比较小表

先用现有manifest/进程映射建立逻辑rank→角色/设备/group；`pidstat`的线程CPU不是设备rank工作量。按以下步骤从已验证日志、trace事件或原生报告取值，不以数组位置猜rank：

1. 冻结比较单位：同phase、group、逻辑step/token/microbatch和适合的TP/PP/EP/DP角色；记录每项对应的文件SHA、行/事件索引与单位。日志字段名按当前revision的真实schema核实，不能盲用固定regex猜字段语义。
2. 复用 `rg -n --fixed-strings '<已核group/step标记>' <已核日志文件>` 导航到目标窗口；trace用上节离线工具导航，不能从其输出制造不存在的token/专家字段。仅提取同一比较单位的有效/填充token、query/KV长度、localshape、专家接收/执行分布、PP stage/DP batch、compute/copy/comm/主机空隙/等待及来源；不可识别填 unknown。
3. 保存小表到原外部产物，当前实验只留摘要/路径。以下全为**合成示例，非测量数据**：

| group/step/phase | rank/role | effective/padded tokens | local shape | compute / copy / comm (ms) | wait/arrival依据 | 来源 |
|---|---|---|---|---|---|---|
| ep0/42/decode | 0/expert | 16/32 | 2 experts × M16 | 3 / 0.2 / 1 | unknown | 合成事件A |
| ep0/42/decode | 1/expert | 48/64 | 4 experts × M16 | 7 / 0.2 / 1 | unknown | 合成事件B |

4. 比较多step的工作量与最慢者身份：不同token/KV/专家shape不能仅按“每token耗时”断言坏卡；PP不同stage先看层/微批与bubble，DP独立副本按相同到达窗口比较请求长度与队列，不强配无对应step。compute/copy/comm可能重叠不能相加为完成时间。
5. 缺逻辑step、角色或关键peer时仅交局部观察，不能声称定位全组straggler；先判断补哪一个角色/窗口会改变选择，不盲采所有rank全部trace。clock误差大于skew时arrival量保持unknown。工作量偏斜选路由/分片/批处理证伪；等工作固定rank慢回查CPU/设备/transport；只有等待高则回查依赖/流水与Mixed干扰。更均匀本身不算端到端收益。

<a id="request-scheduler"></a>
## 7. 请求接入、排队与调度

从当前服务manifest/实际配置核实服务与 metrics endpoint、模型/副本标签及版本，不能猜 `/metrics` 一定存在。下例只 GET 已核 endpoint，不创建推理流量；涉及凭据时沿用已批准安全凭据机制，不把token写入命令、日志或URL：

```bash
metrics_url='REPLACE_VERIFIED_METRICS_URL'
case "$metrics_url" in http://*|https://*) ;; *) exit 2 ;; esac
cmd=(curl --fail --silent --show-error --max-time 5 "$metrics_url")
test "$operation_cap_s" -ge "$((5 + finish_reserve_s))"
printf '%q ' "${cmd[@]}" > "$rout/command.txt"
date -u +%FT%TZ > "$rout/scrape.utc"
"${cmd[@]}" > "$rout/metrics.txt" 2> "$rout/stderr.txt"
```

先核metric help/type/labels与当前版本，选择已知属于目标服务/模型的 Running/Waiting、到达/完成/失败counter、排队/调度时间、input/output token与长度分布、batch占用；保存原快照，提取时保留单位和标签。趋势用已核时间边界的两次快照，先复用已有，再按原预算只补缺的一端，不重做其他采样；counter取有效delta，gauge比较变化，histogram按桶语义分析，不能对累计值直接当区间耗时。无服务字段则交缺口，不编造监控指标名。

客户端慢/流式成批时按同request ID关联客户端发送/首包/末包与网关接入、engine准入/首token/输出事件；先排除客户端连接池/CPU与代理缓冲/慢客户端背压。跨clock不可直接做精确分段。队列持续上升且到达高于完成支持过载假设；还需排除客户端限速与长度差异。已有证据可直接提出一个准入/batching实验；负载扫描另由性能Skill在授权预算内派发，不由抓metrics顺带启动。

<a id="kv-graph"></a>
## 8. KV、抢占、graph 与重新编译

复用同服务/窗口的metrics与已核日志，按当前真实字段筛选KV blocks/预算/使用、驻留query/KV长度、prefix命中、preemption/recompute/swap、临时显存与graph/workspace；容量不足与HBM带宽分别解释。基于runtime/日志证明实际graph请求/命中/replay/capture-size、fallback和重复编译事件/shape，而非仅看启动开关。用已有容量/trace sidecar按需解释，不因缺某metric新建监控系统。

区分首次加载/JIT/capture与准入后的反复编译；默认只优化稳态，原测量显示未稳态则按性能契约修预热，不事后丢慢轮。KV容量与抢占看完整Decode生命周期，不能仅凭prompt剩余块推并发；候选只改一项KV/batch/chunk/graph变量，集成时回验Mixed及另一阶段，不每次日志检查重跑模型。

<a id="system"></a>
## 9. 系统干扰、设备与内存

设备库存/健康按 inventory 平台选择 `nvidia-smi`、`npu-smi info`、`ppu-smi`、`mx-smi`、`hy-smi`/`hy-smi --showpids` 或 `mthreads-gmi`；只查询已授权设备，当前工具不支持精确范围时先说明输出范围，不扫描别的Host。先核实际版本/帮助，不跨厂商fallback。按同窗口核设备频率/功率/温度、显存与已知使用者、链路错误；单点利用率不是阶段峰值或根因。

主机内存/I/O问题优先复用现成资源报告。需要目标PID区间证据且工具支持时，用CPU节的同样留档方式执行 `pidstat -r -d -p "$target_pid" 1 "$window_s"`，查看major/minor faults、RSS及进程I/O；进程I/O不等于物理磁盘占用，minor fault也不等于从磁盘读页。系统压力/共享NIC/编译负载仅作同窗口上下文，不能把别的进程成本归给服务。发现共享竞争交协调者分配/串行测量，不停止无关任务或清共享cache。

<a id="return"></a>
## 10. 解释、停止与回到排序

每次交回：问题/原假设与反例、所选最低成本方法、实际输入/命令/窗口/版本、各报告有效性与覆盖（和结论充分性分开）、支持/反对/unknown、关键路径/暴露等待及新增成本或待测项、产物路径/SHA、预算消耗/停止与重开条件。权限/工具/符号/关键字段不足、报告无新增决策价值或预算耗尽就停止同缺口升级，保留部分有效证据；不无限换工具重采。

协调者在同一 C2/规划点明确该结果使哪项CPU/通信/rank/调度/KV/graph候选采纳、降级或暂缓，选择首个单变量实验与跨阶段守护。已有证据足够可以直接实验；报告归档不等于消费，采集完成不自动触发新benchmark。实现/局部筛选、批次集成和正式精度/性能仍按D0/D6/D7，不能用CPU降低、collective更短或rank更匀代替无profiler服务净收益。

命令语法核对入口：[sysstat pidstat 源手册](https://github.com/sysstat/sysstat/blob/master/man/pidstat.1)、[py-spy配置源码](https://github.com/benfred/py-spy/blob/master/src/config.rs)、[Linux perf record](https://github.com/torvalds/linux/blob/master/tools/perf/Documentation/perf-record.txt)、[perf report](https://github.com/torvalds/linux/blob/master/tools/perf/Documentation/perf-report.txt)、[cgroup v2](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html)、[proc](https://docs.kernel.org/filesystems/proc.html)、[curl](https://curl.se/docs/manpage.html)。这些不是目标版本能力/权限证明，执行前仍以安装版帮助和实际报告为准。
