# report-013 禁用 FlagGems 算子调查与 Issue / Excel 交付

九项已完成独立组件调查并提交到 `flagos-ai/FlagGems`，均Open，title/body已独立回读逐字核验。Excel按用户原模板12列、9行生成，原示例删除，所有必填项/链接/复现Python语法和可视排版已检查。

## 结论与问题索引

| 算子 | Issue | 实测问题 |
|---|---|---|
| `exponential_` | [#8764](https://github.com/flagos-ai/FlagGems/issues/8764) | N151936 offset推进37984，原调用方固定减4无法恢复私有Generator；兼容问题，不是分布错误证明。 |
| `index_select` | [#8765](https://github.com/flagos-ai/FlagGems/issues/8765) | stride2索引被当连续读取，选择错误行；MetaX vendor副本。 |
| `mm` | [#8771](https://github.com/flagos-ai/FlagGems/issues/8771) | M1 BF16公开接口比native慢32.10%，限定当前默认fallback。 |
| `max` | [#8766](https://github.com/flagos-ai/FlagGems/issues/8766) | [1,NaN,2]返回2.0而非NaN。 |
| `mm_out` | [#8772](https://github.com/flagos-ai/FlagGems/issues/8772) | 双方同out=预分配，M1 BF16慢25.93%。 |
| `max_dim` | [#8767](https://github.com/flagos-ai/FlagGems/issues/8767) | NaN values及首次NaN indices均错误。 |
| `linear` | [#8773](https://github.com/flagos-ai/FlagGems/issues/8773) | M1 BF16慢22.22%；非连续batch固定反例通过，不提交view缺陷。 |
| `sort` | [#8774](https://github.com/flagos-ai/FlagGems/issues/8774) | 独立接口UInt32 copy_异常；仅注册copy_后能运行，但两形状慢4.44–5.93倍。 |
| `sort_stable` | [#8775](https://github.com/flagos-ai/FlagGems/issues/8775) | 补copy_后signed zeros稳定索引[1,3,0,2]，native[0,1,2,3]；另有同样执行依赖/性能缺口。 |

## 实际环境与边界

Mx-59原qwen3vl已不存在且八卡被无关Ray占用，本任务没有争抢/停止它；用户随后明确指定mx-104、指定镜像并批准新目录。镜像digest为`sha256:8eea91662853b5df230c836a0ced54c31a0f138be11aeaafc30fb6bdc95b02af`，FlagGems c3c5f5ab2，Driver3.8.1 / SDK3.7.0.38 / Torch2.8.0+metax3.7.0.7 / FlagTree0.7.0.post2+metax3.6 / Triton3.6.0。十个所涉source文件与FG HEAD一致且前后SHA不变。

最终九项禁用集合来自用户指令；镜像Config.env仍是旧四项，不能用它宣称最终服务九项配置已核实。调查直接调用公开API并单独验证ATen注册路径，不启动模型。采用用户提供镜像和历史相同两挂载，所有cache/脚本为私有，未改共享代码。

## 方法、反证与保留的失败

- 首组55个确定性case、6次实际ATen exponential_调用；34capture/68次变化输入replay，其中28组满足原生默认容差、6组更大M/FP16边缘数值差异原样保留，未改称passed。
- 五个固定tiny复现独立确认index/max/max_dim，linear非连续输入反证通过；sort直接调用在copy_处失败。
- 只注册copy_后，两sort重载各2形状的正常值及初次indices与native一致；4capture/8次变化输入replay通过。stable signed-zero固定常量案例则明确失败。
- 首轮mm_out比较的native未带out=而FG复用out，不公开为可比数字；另以双方同out=重新冻结有限对照。
- no-network首先导致FlagTune下载失败。独立host-network复核可取得平台包，但镜像缺xgboost，AUTO仍default回退。以下主性能数据限定该实际回退路径，未安装/升级依赖、未测cost model正常加载环境。
- 官方Triton do_bench：warmup20ms/rep50ms/median，至少3稳定窗口、最多8；固定5轮B/C/R全部保留，spread/漂移≤10%。

| 在线M1 BF16 / K=N2048 | Native ms | FG ms | Revert ms | FG耗时增加 |
|---|---:|---:|---:|---:|
| mm | 0.020736000 | 0.027392000 | 0.020736000 | 32.10% |
| mm_out | 0.020736000 | 0.026112000 | 0.020736000 | 25.93% |
| linear | 0.025343999 | 0.030975999 | 0.025343999 | 22.22% |

以上都是合成组件输入的完整公开接口耗时，不是纯kernel时间、实际模型capture或端到端收益。未证明所有历史禁用来自本次所见缺陷，也不把组件结果当旧GPQA根因。

## 交付与收尾

- Excel：`/Users/baai/Documents/ChatGPT/端到端推理优化/outputs/qwen3vl-flaggems-issues-20261110/FlagGems_问题反馈批量导入_Qwen3VL_MetaX_20261110.xlsx`；SHA256 `757e593b07d7dba9878bb48097073c8b45607ff93995a878538585f2fb3adb8e`。单页、原12列、9条记录，全部Issue链接唯一且已真实创建。
- 原始模板、正文、回执、完整计时/失败、源码指纹、生成器和xlsx均归档在`/public-flash/jinghao/qwen3-VL/20261110-flaggems-disabled-ops-issues`。
- 两个自有clone均在控制器自然finally后停止，经源码校验后删除；5个原有运行容器ID及状态保持，其他容器stop调用0，模型请求0。没有生产代码/依赖修改、没有新precision gate。
- 旧PR1069的代码和CI/部署历史不由本报告改写。本报告仅问题反馈，不是优化完成或精度修复。

## 外部证据

- `results/final-audit.json` SHA256 `a0f390a6adbcb1cbad5609b14ae4ab9c10e26f70a8e1a39f1d81af13b485a871`。
- `results/issue-receipts.json`、`commands/issues-drafts.json`：九项真实发布的正文、编号及链接；GitHub独立回读均精确一致。
- `results/{index_select,max,max_dim,linear,mm,mm_out,sort,sort_stable,exponential_}.json`：原始55case及RNG证据。
- `results/minimal-repros.json`、`results/clarified.json`、`results/online.json`：有限反证、同out=及网络/依赖澄清。
- 所有日志、脚本和失败版本保留，不重跑覆盖。最终工作簿归档版本见delivery-final.json。

2026-11-11按用户要求，将本地交付Excel的C2:C10统一改为“端到端推理优化”。独立导出核验仅这九个值改变，样式、列宽、行高、冻结窗格、其余字段及Issue链接保持；远端前次归档仍为历史版本。

2026-11-11用户再次指定问题场景为“常规模型适配”，本地Excel的C2:C10已统一修改；独立核验只有九个场景值改变，其他内容和格式保持，先前“端到端推理优化”更名记录为历史。
