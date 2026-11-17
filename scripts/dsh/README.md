# dsh HTTP 传输诊断

`transport-diag.cjs` 是按任务启用的 Node preload。它观察 Undici diagnostics_channel，帮助区分请求尚未收到响应头、响应头已收到后的中断、HTTP完成，以及同一进程中的连接复用。它不修复网络，不改变 fetch、dispatcher、TLS/HTTP 协商、endpoint、重试或权限策略。

## 使用范围

先核实任务使用的真实 Node、dsh 入口及版本，并把 hook 放到该任务已授权的私有控制目录，保存 SHA。使用与原 dsh wrapper 相同的 Node 和必要 PATH；不要升级或替换共享 Node/dsh。下面的变量均指已核实的绝对路径，任务参数仍由调用方按原规则冻结：

```sh
DSH_TRANSPORT_DIAG_ENABLE=1 \
  "$TASK_DSH_NODE" --require "$TASK_DIAG_HOOK" "$TASK_DSH_ENTRY" \
  --profile headless --json <已冻结的任务参数>
```

enable flag 只用于当前进程，不写全局环境或共享 profile。没有该 flag 时 require 不安装观察器。不要使用 NODE_DEBUG、SDK完整请求日志或未筛选的完整stderr代替这个hook。

真实provider验证前先做下面的mock和loopback检查，再冻结任务、数据、请求/重试总预算、精确停止条件和产物位置。首次验证使用允许外部provider处理的synthetic内容；不得把未经授权的内部文件、密钥或业务内容作为测试材料。工具权限、sandbox、资源与服务门禁保持原要求。

## 输出与解释

只有stderr中以 `[dsh-transport-meta] ` 开头的JSON是本工具的安全投影。其余SDK stderr不属于该投影，可能含敏感信息，不应未经筛选回收或分享。

| 字段 | 含义与限制 |
| --- | --- |
| `request` | 本进程内的递增序号，不是provider request ID |
| `event` | created / sent / headers / complete / error |
| `elapsedMs` | 从该请求首次被观察到起的相对时间 |
| `status` | 已观察到的100–599响应状态，未知为null |
| `phase` | before_headers或after_headers；后者不证明首个body/SSE字节已到 |
| `alpn` | h2、http/1.1或unreported；unreported不能推定HTTP版本 |
| `socket` / `socketUse` | 仅本进程WeakMap连接序号/使用次数，不记录地址 |
| `causes` | 最多5层，name/code固定白名单；未知为OtherError/OTHER |

**`request:error`不等于任务失败。** OpenAI SDK收到SSE `[DONE]`后可以主动取消剩余HTTP body，正常完成的任务也会出现after_headers error。当前保守投影不调用任意error getter，可能把DOMException AbortError记为OtherError/OTHER。应与dsh final、持久session中的llm/retry和工具原生结果一起判断，不能把这些正常取消计为API断流。

`complete`表示观察到Undici响应结束；没有该事件不能独立证明异常。历史 `terminated: other side closed (UND_ERR_SOCKET)`在Node24与现场pi-ai的loopback对照中对应响应头后body流中断，而headers前中断得到fetch failed变体；这只是机制支持的归因，不定位服务端、网关或中间网络，也不能替代该次请求的现场证据。

Node内置fetch使用的Undici版本与另外安装的npm undici包可以不同，应分别记录。已验证实例为Node24.22.3内置Undici7.30.2；不要根据npm包版本推断实际协议栈。

## 安全边界

hook不读取或输出URL/path/query、request属性、headers、body、error.message/stack、token、socket地址或内部源码。request/socket只作为WeakMap键；其他字段只接受own data descriptor和固定enum/数值，跳过getter。最多输出256条。订阅回调捕获自身错误，避免同步观察器异常影响请求。

它不会创建新权限，也不会证明sandbox完整性。部署、日志路径、请求数控制与精确进程清理由任务控制器负责；hook的256条输出上限不限制实际请求数。

## 检查

无网络mock（5项，含秘密哨兵、poison getter、未知code、cause循环、抛异常sink和连接序号）：

```sh
node --test unit_tests/test_dsh_transport_diag.cjs
```

按需原生loopback：只绑定127.0.0.1随机端口，使用合成数据模拟200成功、headers前关闭与headers后关闭。它不连接真实provider；环境需允许本地listen，结束会关闭server与连接。

```sh
node --test scripts/dsh/tests/transport-diag-native.test.cjs
```

远端运行时仍应使用目标dsh实际使用的Node。公共fixture不包含某台Host、模型或安装目录。依赖具体SDK安装路径的额外 `[DONE]` 对照保留在案例外部证据中，不作为公共工具默认测试。
