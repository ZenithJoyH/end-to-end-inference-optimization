# HY4-preview / PPU-03：完整GPQA精度通过

完整198题GPQA C64已完成，strict-match **183/198=92.4242%**，高于预冻结87%阈值。原参数、官方原runner、独立UUID和数据指纹未改变；396样本行对应198题×2filters，每题strict/ flexible各一次。前后服务、完整四包/仓源码、131权重文件身份清单、tokenizer和启动配置一致，acceptance issue/check通过，42文件/28141872字节原生证据已SHA备份。heartbeat hy4-ppu-03已PAUSED。

当前保持2048/FULL_AND_PIECEWISE，FGV官方45e14232和FG gems-opt3ba1d1d9冻结不变。结论绑定当前env031组合；完整性能验收尚未执行，8192初测未保留。

- [本轮完整精度与证据](optimize/acc-006.md)
- [验收状态](acceptance/README.md)

以下为历史迁移与验证记录，当前状态以本节和acc006为准。


env030已用一文件最小修复解决当前PPU上FULL_AND_PIECEWISE短输入答非所问：BF16 indexer缺失splitting_ops边界，捕获dummy metadata=None后replay跳过真实索引/cache写入。只在该indexer构造处幂等补边界，计算/dispatch不变。两个gems-opt、vLLM、权重和tokenizer均未改；未开始评测，旧acc005保持取消、heartbeat暂停。

启动与FULL/PIECEWISE各10组capture通过；16rank各至少2不同step的prefill PIECEWISE、mixed PIECEWISE、decode FULL回放通过，并观察到前两阶段实时metadata和cache写入。9/9 smoke/C8及原失败同题两次均正确；两次13249-token分页请求OK，第二次实际prefix hit 13184 tokens。采用GPU预算0.85、10桶/max512、batched2048和100K上下文；大于512-token chunk走NONE，本结论不表示所有prefill都被捕获，不含正式精度或性能结论。

- [本轮最小修复、证据与限制](optimize/env-030.md)
- [一文件完整diff](../../../../docs/cases/20261018-hy4-preview-ppu03-migration/plugin-fix-env030/README.md)
- [历史失败](optimize/env-029.md)
- [实验总览](optimize/README.md)
- [验收状态](acceptance/README.md)

2026-10-20 初步性能任务运行交接：独立性能案例未修改env030源码或两Gems，512配置候选未保留；原8010/2048/prefix cache已恢复，当前实例`e6562463824a7aebecb1d655b8efdcfe1d2c27321329cff33a0a1f4b36304805`。新鲜C8/三阶段16rank2replay/分页+2624实际prefix hit证明见[性能案例](../20261020-hy4-preview-ppu03-initial-perf/README.md)，最终源恢复manifest SHA `17bbca17c4bb84e69b06d55503f7a0077160b87e4bc139ff1901872588703480`。历史service13及所有旧精度证据不覆盖，本轮未启动GPQA。

2026-10-20 env031：已将原 hy4-preview 安装 FGV 更新到官方 main@45e14232，Plugin BF16 paged logits 改从 FGV 导入；FG3ba1d1d9不变。14项算子测试和4组各2次动态graph replay通过。当前 HY4 未重启，仍加载env030/旧FGV，新磁盘组合整模型回归和正式精度尚未执行。见[env031](optimize/env-031.md)。

2026-10-20运行交接：8192独立性能试验已结束并拒绝，原hy4-preview恢复2048/prefix enabled/8010；env031新版FGV45e已在原容器实际加载，当前实例`f1d5138652d2365ae3c1c4409458dfe818bb98b9e790eb0314cff5f913633648`。9smoke/C8、16rank三阶段各2replay、2x2689分页及2624真实prefix hit通过，16观察器退出；FG3ba/source/vLLM/模型/tokenizer保持本轮基线，GPQA未跑。见[8192案例](../20261020-hy4-preview-ppu03-batched8192/README.md)。终态 `/workspace/.hy4-preview-migration-20261018-01/perf-20261020-02/results/final-verification.json` SHA `b527267761cec83388fd03efa4d0424b96b36a59f4b2ec11e26fcb433ad2c0e6`。
