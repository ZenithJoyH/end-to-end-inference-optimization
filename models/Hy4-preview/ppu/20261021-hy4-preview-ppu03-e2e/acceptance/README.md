# HY4 最终验收状态

**incomplete。** 历史fw001仅完成C8/N8缩减B/C/R：Prefill/Mixed passed、Decode因TTFT波动incomplete。fw003的002仅得到Prefill/Mixed/P4K基线，189项终态证据冻结；用户恢复后的003在measured阶段再现波动，候选因控制漏项已安装，随后完整功能验证通过且211项证据冻结，未做候选benchmark，仍无新收益或正式gate。两者均不能作为当前组合或正式四场景性能验收。

004 has valid bounded targeted comparisons and independent retained functional proof; neither is formal acceptance. 005 failed before inference due to generated parser name, preserved as41file freeze. 006 has exact004 semantic argv and is starting fresh C16 validation; no new performance conclusion.
原适配组合acc006全198题strict183/198=92.42%通过87%，但不绑定本次候选/独立服务/prefixOFF。新完整198题GPQA、正式P1K→P4K→P16K→P32K/D1024/C64/N128及最终组合验收均未执行。没有签发新gate，没有宣称模型端到端优化完成。

<!-- e2e:summary:start -->

- 案例：20261021-hy4-preview-ppu03-e2e
- 当前状态：incomplete_no_formal_candidate_acceptance
- 当前候选：env031+fw002+yaml001+15line fw003 retained andnewfunctionalvalidated;004targeted gains only, noformal gate
- 下一步：Follow existing006 revert Mixed after Prefill9rounds admitted; freshafter/drift/comparison pending, no formal gate.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|

<!-- e2e:summary:end -->

后续TTFT机制诊断不改变验收结论：原Decode比较保留incomplete；补采仅6warmup并按稳定性条件停止，未签发任何新精度或性能gate。普通服务已恢复，详见[fw-001](../optimize/fw-001.md#ttft-超限的详细定位ttft-diag-001)。

004阶段隔离targeted对比的C1基线已通过6warm3measured及前后身份核验；004候选四组36轮已准入且after身份一致；当前revert完整功能验证已通过，四组回退性能复测中，比较尚未完成。当前依然没有新正式gate，不以启动实验视为收益。

004四组targeted B/C/R现已全部passed并冻结837项证据，Mixed4.934倍和P4K+40.913%仅属于缩减里程碑。主Agent正以独立retained动作保留同15行并重新验证；当前正式精度/四场景gate仍缺失，acceptance保持incomplete，不把里程碑通过等同最终验收。

独立retained保留/新功能验证现已完成并冻结119项证据、独立SHA复核通过；当前服务确认为同004实测候选。仍无新完整198题精度及正式四场景gate，因此最终acceptance保持incomplete。下一C16扩展仅本地契约草案，未启动新测试。
