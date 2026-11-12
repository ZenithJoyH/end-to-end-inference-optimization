# 按原生命令修正BGE-M3性能脚本

2026-11-05，用户提供完整`vllm bench serve --backend openai-embeddings`命令，要求调整当前`mx-59:/public-flash/jinghao/BGEM3/test/perf_test/vllm_perf.py`。本轮是用户指定远端副本的维护，不修改本项目`test/`导入基准，不改变服务/源码，不执行整套性能测量或签发性能结论。

## 当前事实与设计

- inventory/连接通过；目标为普通文件0644/root:root，旧SHA `5494b335b376099d2c0bb67146c329f71295fd282673a73126bb1518519ba55b`，408行，原文已取回`/tmp/bgem3-embedding-perf-before-20261105.py`。
- 当前服务`127.0.0.1:8000/v1/models`返回bge-m3；示例18340未监听。`/models/bge-m3`和`/mine/benchmarks/bge_m3/native`不存在，实际tokenizer路径为`/public-flash/models/bge-m3`。采用当前路径/8000为默认值，提供CLI覆盖。
- 保留当前四种输入长度1024/2048/4096/8192及C64；按参考命令改为N256、native output-len=1占位、batch-size1、range/prefix0、inf/1/seed0、ready-check0/native-warmups0（probe-rate按下文兼容检查调整）、e2el与50/95/99、extra-body三字段原样（special tokens true、truncate null、float编码）。不发送ignore-eos。
- 沿用原RUNS5/SKIP_FIRST3，但将前3轮明确标记warmup且全部保留。它们是整轮预热，与每次native命令的num-warmups0不同；测量轮全部保留，不事后挑选。提供`--runs 1 --skip-first 0`复现单轮示例。
- 原`--enable-all`的4K并发1/4/16/256保留；移除从Qwen复制的128K/256K两项，不缩短冒充BGE支持，也不把本次诊断称为项目正式四场景验收。没有Decode/输出token吞吐列。
- 每次运行创建唯一结果子目录，每case/每round保存原生详细JSON、命令、日志、validation和CSV。读取实际vLLM0.24 pooling JSON；完成数/逐请求errors/实际input_lens/总token/有限metrics/吞吐算术必须一致。缺文件、部分失败、预热失败或非零退出即停止并非零返回，不写成功均值。
- 原生pooling JSON的total_token_throughput在此任务等于输入token吞吐；CSV展示E2EL均值、中位数、标准差及P50/P95/P99。汇总是测量轮指标的算术均值，百分位列是各轮百分位均值，不是合并请求的总体百分位。

本地已读取本项目性能Skill/映射/工具能力：维护版正式runner当前只支持生成式/v1/completions。本轮遵从用户明确要求修改指定远端wrapper，仍委托已安装vLLM原生embedding客户端，不另写HTTP性能引擎；未选择/执行性能Skill的baseline/targeted/formal测量模式，不把维护验证当性能验收。

## 验证计划与已完成检查

候选`/tmp/bgem3-embedding-perf-20261105.py`。语法及Ruff(E/F/I、format)检查通过。离线模拟原生CLI的验证产物`/tmp/bgem3-embedding-perf-checks-20261105.761vu9av`：命令参数按用户参考构造（真实CLI检查后的兼容差异见下文）；完整5轮/3预热/2测量的JSON及CSV流程通过；15种无效结果被拒绝，部分失败、非零退出、缺JSON、超时均在首轮停止且不生成成功汇总；dry-run不创建目录或发送请求。

后续在容器私有唯一/tmp目录保存验证工具和候选：用真实`add_cli_args`解析命令、真实tokenizer/RandomDataset离线核对各长度（包含special tokens），再以原生embedding请求函数发送一条16-token功能请求确认接口与usage，不跑N256矩阵，不报告吞吐收益。所有模拟性能数据明确标记为测试，不能当实际模型结果。

## 部署方案

全部维护验证通过后，先将部署工具保存本地并上传Host唯一/tmp文件，再执行旧SHA检查/原文独占备份/语法核验/权限保留/同目录原子替换。只允许改用户指定脚本；本项目原始test资产、启动器、模型服务与三库保持不变。记录候选SHA、精确执行副本、备份和验证回执后完成交付。不自动回退或执行完整压测。

真实CLI兼容检查发现本机客户端**不支持`--probe-request-rate`**，首次探针在参数解析阶段退出，未生成请求或部署代码。修正为不传该选项，其余参考参数保持；不修改/升级vLLM。该版本自带的初始试请求保留，不能把num-warmups0或省略unsupported flag描述成“完全没有试请求”。候选文档和记录已明确此区别。

移除不支持选项后，Ruff/format及全部离线检查再次通过；新回执`/tmp/bgem3-embedding-perf-checks-20261105.2ybe8c7t/REPORT.json`，旧回执保留。修订原生验证工具保存为`/tmp/bgem3-embedding-perf-native-v2-20261105.py`，将重新检查全部受支持参数、离线special-token长度及单条16-token功能请求。

待执行部署控制器：本地`/tmp/bgem3-embedding-perf-deploy-20261105.py`，Host执行副本`/tmp/bgem3-embedding-perf-deploy-20261105-m5q8j2.py`。SHA256 `b58e6433f3d13f98fd9dea6d188c918668cce5110beb57652d4a764c3c1396b2`；候选SHA256 `aa8aff0d7681256556b83234c1f4f7cd7e315f48e1c603168a837fce621e2338`。控制器先保存唯一Host /tmp证据及同目录原文备份，旧SHA漂移拒绝替换，显式保留root:root/0644并原子替换；不复制NFS扩展属性，不启动服务或benchmark。仅在原生验证通过后执行。

原生v2检查通过：容器证据`/tmp/bgem3-embedding-perf-native-v2-20261105.v8x_sj_l/REPORT.json`，候选SHA与待部署一致。真实add_cli_args接受全部参数；RandomDataset+tokenizer核验包含special tokens的16/1024/2048/4096/8192长度精确一致。原生请求函数向当前8000服务发送1条16-token embedding，HTTP成功且usage为16。没有执行native整轮或N256矩阵，没有性能结论。客户端导入时仍出现既有torchvision/mcoplib/maca patches警告，未阻塞此次验证，未修改这些依赖。

## 部署结果与使用

已在mx-59部署指定脚本，SHA256 `aa8aff0d7681256556b83234c1f4f7cd7e315f48e1c603168a837fce621e2338`，保留root:root/0644。Host证据`/tmp/bgem3-embedding-perf-deploy-20261105.5u_cu__s/REPORT.json`；原文备份`/public-flash/jinghao/BGEM3/test/perf_test/.vllm_perf.py.embedding-5u_cu__s.original`，SHA与上述旧SHA一致。部署工具退出0，服务重启/benchmark执行均为false。

在BGE-M3容器中运行单轮8192/C64/N256：

```bash
python /public-flash/jinghao/BGEM3/test/perf_test/vllm_perf.py \
  --input-lens 8192 --runs 1 --skip-first 0
```

追加`--dry-run`只打印命令。默认运行四档长度、每档5轮、前3轮整轮预热；单轮示例显式取消该设置。可通过`--port 18340 --tokenizer /models/bge-m3 --result-dir /mine/benchmarks/bge_m3/native`切到用户示例环境，前提是目标服务/路径存在。每次结果写入result-dir下的唯一子目录，默认根为脚本同级`benchmark_results/bge-m3/`；保留原生round JSON/log/命令/校验回执及summary.csv。

回退方案：先核对目标SHA仍为本次版本，再从上述原文备份恢复到精确目标，保留root:root/0644，随后语法检查；无需重启服务。不自动执行回退。

部署后首次只读验证已核对Host性能脚本SHA；附加检查误用Host的serve.sh路径（该路径仅在容器内存在）而提前退出，尚未执行容器dry-run。删除无关路径检查后重新核对容器内实际目标；部署及备份未受影响。

最终部署后验证通过：Host与BGE-M3容器的目标SHA均为`aa8aff0d7681256556b83234c1f4f7cd7e315f48e1c603168a837fce621e2338`；容器内编译语法与`--input-lens 8192 --runs 1 --skip-first 0 --dry-run`退出0。打印命令为openai-embeddings、/v1/embeddings、8000、实际tokenizer、C64/N256、extra-body原样，未传不支持的probe-request-rate或ignore-eos。验证控制器本地`/tmp/bgem3-embedding-perf-verify-20261105.py`；此次dry-run没有执行benchmark或创建结果目录。

## 按用户要求恢复原代码和CSV格式（最新版本）

用户要求保留修改前的代码组织与CSV格式。本轮以原始408行脚本为基础，恢复MODEL/TOKENIZER/HOST/PORT/RUNS/SKIP_FIRST单独常量、COMMON_ARGS显式列表、四元组case、原函数分层与逐场景CSV输出。不再使用上一版合并summary.csv或新增Phase/Status/Input Length等列。

CSV_COLUMNS恢复原22列及原顺序；format_result/append_csv/average_metrics/save_error_log的AST与原版一致。文件恢复`bge-m3_<input>in_1out_c<concurrency>_n<requests>_<YYYYMMDD_HHMMSS>.csv`，逐轮标签`Run1(SUCCESS)`/`Run1(FAILED)`，末行SUMMARY；均值仍为预声明前3轮整轮预热之后的全部2轮，round到2位。默认输出目录恢复当前工作目录下benchmark_results/bge-m3，可用--result-dir覆盖。输入1024/2048/4096/8192、C64/N256与openai-embeddings /v1/embeddings保留。

Decode=1仅为原生命令占位，不存在的生成token/输出吞吐/TTFT/TPOT/ITL列留空，不将E2EL伪装为这些指标。Total tok/s为embedding输入token吞吐。E2EL仍由原生详细JSON保存并在控制台输出，native日志/命令/结果在结果根的native/<scenario>_<timestamp>/。保留JSON完整性检查、失败即停止且不产生成功SUMMARY、超时仅停止本客户端的行为。本轮只做格式维护，不运行模型负载或正式评测。

执行前计划：本地候选`/tmp/bgem3-embedding-perf-format-20261105.py` SHA256 `ab20c38d01884b3c3f878bec4c8c9e442860017a87fe133274c1d1a374d3931a`。Host当前目标SHA已只读核验仍为`aa8aff0d7681256556b83234c1f4f7cd7e315f48e1c603168a837fce621e2338`。控制器本地`/tmp/bgem3-perf-format-deploy-20261105.py`，执行副本`mx-59:/tmp/bgem3-perf-format-deploy-20261105-m5q8j2.py`，SHA256 `10d7f60932a5bfa6f93b3b57fcce37acf21e6e233bf070c65b469f40fef0e27d`。先核对旧SHA/权限、独占备份原文并保存/tmp证据，同目录暂存+再次SHA检查+原子替换，保留root:root/0644；不动服务或其他源码。验证通过后执行。

格式恢复离线回执：`/tmp/bgem3-perf-format-checks-20261105.iwwjd25i/REPORT.json`通过。实际生成2场景×5轮CSV，逐项核验原22列表头、命名、Run1(SUCCESS)至Run5(SUCCESS)+SUMMARY、SUMMARY只统计4/5轮且保留2位小数；生成式专有字段为空。15种无效原生JSON均拒绝，partial/非零退出/缺JSON/超时均只有Run1(FAILED)且无SUMMARY。dry-run不创建文件，模型请求0。Ruff E/F/I检查通过；没有对保留的原代码做全文件格式化。

最新格式版本部署完成：SHA256 `ab20c38d01884b3c3f878bec4c8c9e442860017a87fe133274c1d1a374d3931a`；root:root/0644保留。原上一版备份`mx-59:/public-flash/jinghao/BGEM3/test/perf_test/.vllm_perf.py.embedding-format-nvajveyc.original`（SHA aa8aff0d…），最初原始格式脚本备份`.vllm_perf.py.embedding-5u_cu__s.original`（SHA 5494b335…）仍保留。Host部署回执`/tmp/bgem3-perf-format-deploy-20261105.nvajveyc/REPORT.json`，工具/原文/候选均存于同一证据目录。未运行压测或重启服务。回退仍需先核对当前SHA无后续人工修改，再恢复精确备份。

最新部署后验证通过：Host/容器SHA与候选一致，容器AST确认22列原表头，编译语法及8192/C64/N256单轮dry-run退出0。打印的原生命令与参考参数一致（保留已确认的probe-rate兼容差异），没有请求或结果目录创建。控制器`/tmp/bgem3-perf-format-verify-20261105.py`。容器工作目录当前为/public-flash/jinghao，所以默认结果根解析为/public-flash/jinghao/benchmark_results/bge-m3；此行为与最初脚本相同，可通过cd或--result-dir指定。
