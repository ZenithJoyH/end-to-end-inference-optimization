# 20261013-qwen3vl-metax-flaggems-e2e-opt1

- [baseline](baseline/README.md)
- [optimize](optimize/README.md)
- [acceptance](acceptance/README.md)

2026-10-15：基于用户当前 MoE JSON 配置和 qwen3vl-opt2-retry 运行事实，在新独立容器 `qwen3vl-flaggems-op003-20261014`（mx-59/GPU0,1）继续优化。op003/004 的完整MoE调参未达到晋级门槛，没有写入产品；实际随机采样 trace 定位 FlagGems radix sort 直方图热点，op005仅将计数器int64改为int32，保留所有原有算子选择、黑名单、MoE JSON和Plugin/vLLM代码。

采样契约temperature=0.7/top_k=20/top_p=0.8。原始P1024/D1024/C64/N128，各角色3warm+3measure，吞吐中位数1133.59→1357.26 token/s（+19.73%），回退1130.62；P99TPOT56.09→46.82ms（降低16.53%）。主指标、延迟和稳定性守护全部passed，每轮128请求全部成功、9轮测量均保留。D256 milestone亦passed（+15.33%）；两组收益不可相加。

[op005完整记录](optimize/op-005-flaggems-sort-sampling.md)包括算子数值/graph、原型特殊值恢复、两rank采样归因、native结果和回退证据。新候选已保留在独立容器私有FlagGems，测试服务已停止；用户qwen3vl-flaggems-e2e-20261013四仓库源码hash与快照一致、8000仍返回qwen3vl-opt2-retry，未回写或重启。

用户明确暂缓正式精度评测，无GPQA分数/gate；新组合尚未覆盖P4K/P16K/P32K，不宣称四场景最终验收。旧greedy MoE +8.30%观察及波动超限、combined copy_/cumsum黑名单负结果与回退都保留在对应实验中，不能与本轮采样契约混算。

共享NFS满后，正式对照产物存于独立容器私有 `/workspace/e2e-artifacts/20261013-qwen3vl-metax-flaggems-e2e-opt1/hist32-full03`，通过docker exec读取。外部命令、原型和trace仍链接到用户授权远端案例 `/public-flash/jinghao/qwen3-VL/20261013-qwen3vl-metax-flaggems-e2e-opt1`；文件身份及位置见optimize/state.yml。

2026-10-15 用户授权回写：sort单行优化已部署到 `qwen3vl-flaggems-e2e-20261013`，与独立容器测试源码完全一致；核验MoE JSON及FlagGems-vllm/Plugin/vLLM所有当前修改保持原样，原sort文件已备份。服务未重启、未发起压测，交由用户启动服务后进行端到端测试。Agent暂不继续远端变更；独立容器性能证据不冒充本次用户容器复测结果。详细回执与回退路径见[op005](optimize/op-005-flaggems-sort-sampling.md)。
