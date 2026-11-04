# reqdiag-001 外部请求体为字符串触发500

用户报告 `/mnt/nfs/users/jinghao/minimaxM3.1/service.log` 接请求后报错，并说明来自外部调用。按本地 `inference-accuracy-diagnosis` Skill 排查，归类 request/output-health / API协议校验；未进行模型推理、改源码、改配置或重启，没有新评分/gate，也不改变历史三项精度。

## 服务与错误证据

通过当前日志写入进程、容器cgroup/NSpid/startticks与实际argv核验，日志对应 `minimaxM3.1-opt-20261008` 的8035服务，实际权重Flash20261019，served name `MiniMax-M3.1-new`，TP8/物理0–7，maxlen100000，FULL_AND_PIECEWISE。它与最新 `minimaxM3.1-opt-latest-20261020` 迁移容器不同，不能把当前错误归到该容器中刚修改的INT8/MoE接入。

冻结的日志前缀约2.95MB，发现11处 `AttributeError: 'str' object has no attribute 'get'`；已保存最小错误栈和原文件SHA/长度/mtime，不复制真实请求内容。栈均落在 `/usr/local/lib/python3.12/site-packages/vllm/entrypoints/openai/chat_completion/protocol.py:870` 的 `ChatCompletionRequest.check_cache_salt_support`：`data.get("cache_salt")`。

这里 data 是整个请求体校验对象；异常说明它是 str，而不是要求的 dict。不是 cache_salt 字段需要改配置；校验器在确认请求对象类型前直接 `.get()`，造成未处理的AttributeError及HTTP500。当前vLLM `0.24.0+empty`、Pydantic `2.12.0`、FastAPI `0.136.1`。失败发生在API校验，未进入模型计算。

## CPU离线复现

在该原容器独立CPU进程，使用真实 `ChatCompletionRequest` 和合成数据：

| 输入 | 结果 |
|---|---|
| Python dict → model_validate | 通过 |
| JSON字符串 → model_validate | 精准复现AttributeError/同函数第870行 |
| 一次JSON编码 → model_validate_json | 通过 |
| 二次JSON编码 → model_validate_json | 精准复现同一错误 |
| dict 中合法字符串 cache_salt | 通过 |

全部5项预期结果吻合。没有HTTP POST/模型请求或GPU计算。健康接口和models接口均返回200，model ID为MiniMax-M3.1-new。读到的Plugin/FV/FG路径属于原容器，记录在原生回执；没有把静态新容器导入身份冒充运行服务。

## 原因与处置边界

服务端机制已确认：收到非对象的字符串请求体时，vLLM before-validator 缺少类型保护，错误变成500。外部发送代码和真实body未取得，**具体在哪一层转成字符串仍未确认**。重复JSON序列化是可精确复现的常见原因，不能据此断言用户一定用了某个库或写法；也未抓包、记录真实body或外部Token。

外部调用方应确认最终HTTP JSON顶层为object。使用requests/httpx这类 `json=` 参数时传dict，例如 `json=payload`；不要先 `json.dumps(payload)` 再放入 `json=`，以免再次编码成JSON字符串。服务端同样存在错误处理健壮性缺陷，合理行为应返回请求参数错误，而不是未处理异常；本次按诊断范围未修改vLLM/Plugin或正在运行的服务。

这是请求健康问题，不是新的模型精度失败，不改旧分数或gate；现服务实例的gate绑定仍需独立核验，不复用旧实例身份。没有启动性能、正式精度或监控任务。

## 证据

远端根 `/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261019-minimax-m31-flash-ppu-tp8-accuracy/profiles/request-protocol-20261020-01`。`result.json` SHA `db01c947912128228895d68e6619b685438f55a0047c9cc22af807c385b12893`，含日志/服务身份/协议源文件SHA、5项复现、实际依赖版本与健康检查；必要引用和命令SHA见 [state.yml](state.yml)。`cpu-reproducer.py`、退出码和原始CPU日志均留远端。首次控制命令因旧精度案例没有profiles父目录而在任何采集/复现前退出，v2仅创建本轮唯一路径后完成；未重跑失败的模型或数值评测。
