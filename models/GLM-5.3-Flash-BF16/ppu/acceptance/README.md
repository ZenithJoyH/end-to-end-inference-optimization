# 优化验收状态

Agent 结构化事实入口：[state.yml](state.yml)。

状态：`incomplete`。

- 精度：`passed`。sparse MLA 当前候选的完整运行有 169 个 strict 正确；13 个超时题
  同身份补测新增 3 个正确，按用户指定的合并口径为 172/198（86.87%），达到 86%
  门槛。用户明确指定 timeout 不阻断精度通过；8 个补测仍达到 60K 的样本作为稳定性风险
  保留。项目原生零超时 gate 未签发，后续性能按用户批准的 `performance_only` 口径执行。
- 正式性能：固定 P1K/P4K/P16K/P32K、D1K/C64/N128 四场景的最终
  candidate/baseline/revert 验收尚未完成。当前 P1K 数字是已保留组合的
  scenario-entry baseline，不是最终验收结果。
- 稳定性：C8 8/8 通过；长稳和资源稳定性未开始。
- 最终候选与回退：尚未冻结最终候选。已保留优化已生成 Plugin
  9 个和 FlagGems-vllm 7 个模型分支 commit，并已推送到三个
  `ZenithJoyH` 仓库的 `support-glm5.3-flash` 分支；远端 HEAD 已核验。最后研究服务已停止，
  本轮未重启。
- vLLM 专用 MQA 配置和全部新增非 ATen GLM serving 算子已迁移到
  `FlagGems-vllm support-glm5.3-flash@9117ae5`；Plugin
  `support-glm5.3-flash@95b04f7` 已改用公共 API。FlagGems 原
  `4a3cba0`/`fec9807` 已从支持分支移除，`master` 和支持分支均为
  `9c9bff3`。基于这一无旧提交组合的 23/23 + 11/11 测试及导入检查通过，
  但尚未绑定到运行服务或最终候选，不能据此更新正式验收状态。

只有最终候选源码、配置和服务身份绑定的完整正确性与性能门禁全部通过后，才能更新为完成。

精度配置、服务身份、样本异常、结果 SHA 和远端原始路径已统一合并到
[state.yml](state.yml)；本目录不再保留重复 runbook、manifest 或结果副本。
