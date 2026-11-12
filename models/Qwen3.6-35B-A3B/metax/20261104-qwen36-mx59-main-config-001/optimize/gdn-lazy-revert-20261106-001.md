# 回退 qwen36-35b 的 GDN 延迟注册

用户明确确认目标为 mx-59 / qwen36-35b，仅回退 GDN 延迟注册。不是干净的 vllm0202-fl-release02-20261106。恢复 MetaX patches/__init__.py 的原 gdn_linear_attn 导入，删除 ModelRunnerFL 中新增的延迟导入块；保留采样 register_model 路径及旧 topk_topp_sampler 导入移除，保留 MoE、KV预算、GDN算子实现和其他文件。

目标私有 /workspace/vllm-plugin-FL，容器 b96e1f3a3c61bcf2946803b8d88aace5bcff7599466023de86007db9e9fb4094；挂载仅 /public-flash 和 /data，不覆盖源码。变更仅导入时机，恢复 release/0.2 原有机制。C1/C2/C3：先检查两个文件精确原内容，预构造和AST检查，再备份两文件并修改；失败按内容guard回退。F1/F4/F7：原版逐字比较、保护清单、AST与diff检查；不重启、不发模型请求，不把磁盘修改声明为当前进程重新加载或硬件回归通过。已知非正常import-order入口的原风险随回退恢复；用户已选择撤回该修复。

执行前归档计划：远端 /public-flash/jinghao/qwen3.6-35B/20261104-qwen36-main-config-compat-mx59-001/gdn-lazy-revert-20261106-001/commands/apply.py，SHA256 4902f438c383aaa4d86ec748d805f7f3e92e744507ef445b5d2b8e2e48bc3c09。唯一新目录保存备份、前后源码/服务身份、结果和diff，不覆盖旧证据。Host执行前检查容器ID与源码不落在挂载内；只执行一次。

状态：completed_disk_revert_no_service_restart。

首脚本在HEAD检查处退出1，尚未备份/写源码；误将另一容器release HEAD用于当前目标。新只读核实目标HEAD=1bc0c775ffbdf4a0b0e2efb5e847d586e902273f（PR638），两处精确diff未变。唯一接续apply-002.py仅修正预期HEAD，全部原内容断言/范围/备份保护不变，SHA256 12a86ed123c72cd5fdd543c56e56f5a4d22ef2acd7732a395dd6eca5acab5d96；保留首脚本及失败，执行新脚本一次。

接续原生exit0。恰两文件改变，其他扫描的4165个Python源码文件字节不变；model_runner.py逐字等于当前HEAD，patches/__init__.py仅剩原先采样迁移需要的topk_topp_sampler导入删除。AST和git diff检查通过。独立读回diff再次确认GDN已恢复原导入位置，保留GDN实现及采样/MoE/KV修改。服务进程身份前后保持；未重启、未热加载、未跑模型/硬件回归，新导入时机将在下次进程启动生效。

结果result.json SHA256 bb72b1b87ee2690c78b90b01e84f778ff509be5d431b2de5bf62b942f7b103a3。backup/保留原两文件；若要撤销本次回退，须先核验当前候选字节后恢复备份，不覆盖后续改动。公共PR699保持已关闭，PR702未改，无提交推送。
