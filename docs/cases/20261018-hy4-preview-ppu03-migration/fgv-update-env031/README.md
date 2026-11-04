# env031：FGV 官方 BF16 paged logits 接入

仅两处 Plugin 导入/能力检查变更，FGV 更新至官方 main@45e142327d06c65feaa0406b16417b609d6c32ff；FG固定3ba1d1d9。

- [本轮 diff](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/fgv-update-env031/plugin-update.diff)
- [累计相对官方 Plugin diff](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/fgv-update-env031/plugin-full-vs-official.diff)
- [版本、必要性、验证与回退记录](../../../../models/Hy4-preview/ppu/20261018-hy4-preview-ppu03-migration/optimize/env-031.md)

14项原生算子测试和H32/H64、clean两状态各2replay通过；新模型组合未重载或评测，原服务健康200。
