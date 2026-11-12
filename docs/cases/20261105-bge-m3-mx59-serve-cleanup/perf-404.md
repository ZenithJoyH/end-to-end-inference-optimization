# BGE-M3性能脚本404诊断

2026-11-05，用户询问使用mx-59的`/public-flash/jinghao/BGEM3/test/perf_test/vllm_perf.py`时为什么模型服务返回404。本轮仅只读诊断；未修改测试脚本/启动脚本/源码，未启动benchmark或重启服务。

连接通过项目inventory与connectivity-check。目标脚本408行，SHA `5494b335b376099d2c0bb67146c329f71295fd282673a73126bb1518519ba55b`。第24行模型名bge-m3、27/28行127.0.0.1:8000与实际服务一致；第37/38行backend=vllm，第43/44行endpoint=/v1/completions，仍是生成式压测请求。默认case同时设置input/output长度，解析生成token、TTFT、TPOT等指标。

当前`/public-flash/jinghao/BGEM3/service.log`明确连续记录`POST /v1/completions →404`。在同一BGE-M3容器中、禁用HTTP代理后只读核验：

| 请求 | 当前事实 |
|---|---|
| GET /health | 200 |
| GET /v1/models | 200，id=bge-m3，root=/public-flash/models/bge-m3，max_model_len8192 |
| GET /openapi.json | 服务暴露/v1/embeddings、/v2/embed、/pooling，未暴露/v1/completions或/v1/chat/completions |
| POST /v1/completions，空JSON | 404，detail=Not Found |
| POST /v1/chat/completions，空JSON | 404，detail=Not Found |
| POST /v1/embeddings，空JSON | 400，缺少input等字段，证明路由存在且已进入请求校验 |

空JSON请求没有有效模型输入，不触发推理；未向正在运行的服务施加benchmark负载。原404日志与本轮诊断产生的少量404/400可按时间区分，没有清理或覆盖原日志。

根因已确认：BGE-M3以pooling/embed方式服务，客户端仍请求生成接口。不是模型名、服务未就绪或Plugin YAML加载失败。不能只把URL改成embeddings而继续发送prompt/max_tokens等生成请求。

容器实际vLLM0.24.0的`benchmarks/lib/endpoint_request_func.py`第619行起已有`async_request_openai_embeddings`，发送model+input；第874行注册backend `openai-embeddings`。应配合endpoint `/v1/embeddings`，去掉生成输出长度/ignore-eos等生成设置，按embedding口径统计请求延迟、req/s和输入token吞吐，不将向量维度1024视为生成1024个token。当前诊断未执行性能评测，原404请求不能形成有效性能结果。
