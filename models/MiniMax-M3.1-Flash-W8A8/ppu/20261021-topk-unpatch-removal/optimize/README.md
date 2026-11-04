# top-k patch移除

[compat-001](compat-001.md)：已按用户要求删除Thead top-k固定K128兼容及相关测试，GQA字节不变；13项现有单测通过，真实加载hook验证top-k保持原生autotune。仅改2文件，精确补丁和备份已归档。8045原本停止且保持停止，正式模型精度未评测。[删除补丁](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-topk-unpatch-removal/topk-removal.patch)
