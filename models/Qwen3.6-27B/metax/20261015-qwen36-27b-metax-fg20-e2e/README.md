# Qwen3.6-27B / MetaX / 当前20FG脚本范围

本轮三阶段baseline/candidate/revert已全部完成：87轮、27个measured、9408请求全部成功，原始证据与SHA已复核。metadata候选Prefill吞吐+0.5804%、Decode观察+0.2495%、Mixed+0.2646%低于2%门槛；Decode基线meanTTFT测量spread13.4452%超过10%，整体验证incomplete，候选未保留。全部B/R决策指标漂移<1%（最大0.998445%），未删慢轮或放宽门槛。

Mixed前轮长停顿已由双ranktrace定位为FG full小整数新尺寸在线调优；OP003修复通过194数值/16graph replay、微测与模型命中，并使本轮新baseline Mixed的3测吞吐spread为0.1794%。三角色共同使用该修复，本轮没有其相对原full的独立E2E增量。结束按约将Plugin/full均恢复原件，补丁归档。

Decode慢轮进一步定位到GDN h_vmajor重复JIT：64请求16ms内发出；r7早期2.203s输出停顿内生成一个新编译产物，source→binary约0.616s。9个cache变体lowered source与binary完全相同；FP32固定配置仍保留无用N_BUCKET/SKEW_BUCKET特化键。暖轮r1有3次新H编译，r2-r6/r8-r9没有。历史r7无ranktrace，精确bucket组合及剩余CPU/driver耗时未知，保留原incomplete，不据此宣称数值缺陷或新修复通过。

源qwen36-27b-fa-opt-20261012/18002已恢复ready，精确PID954040/create1792130229.17；独立qwen36-27b-fg20-e2e-20261015已无模型进程。两容器原四仓SHA核验相等，完整20FG/attention1/noBlacklist、FP32 GDN、.002/.02、TP2/GPU2,3/8192/graph64均保持。原8002与其他GPU任务未操作。

模型路径/public-flash/jinghao/qwen3.6-27B/Qwen3.6-27B原25文件SHA一致，用户启动脚本仅同步了新路径。30分钟监控已在终态暂停；当前20FG无正式198gate，四场景正式验收未执行。没有提交、推送或自动追加测试。

远端证据根：`/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e`。离线审计/缓存归档在`results/fw002r4-decode-diagnosis-v1`，完整事实见[FW002](optimize/framework-002-mixed-batch-overlap.md)和[结构化记录](optimize/state.yml)。

- [原始基线](baseline/README.md)
- [多轮总览](optimize/README.md)
- [OP003 full](optimize/op-003-metax-full-small-integer.md)
- [正式验收状态](acceptance/README.md)
