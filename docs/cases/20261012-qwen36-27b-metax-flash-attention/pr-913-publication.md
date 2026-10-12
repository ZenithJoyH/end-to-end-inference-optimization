# Flash Attention PR 913 发布记录

本文件仅记录侧边对话中用户明确要求的分支和 PR 发布，不推进主线程的优化、评测或服务操作。

- Fork: https://github.com/ZenithJoyH/FlagGems-vllm
- 分支: qwen3.6-27B-metax-opt
- 基线: 46a81d39732af0e1b0ef6c474e500591dfb2d124（fork main；未修改 main）
- 提交: c9560c73fc1956aa0e1cd07ad560e1d1b2114923
- PR: https://github.com/flagos-ai/FlagGems-vllm/pull/913
- 状态: open / draft；读取时 mergeable=true，mergeable_state=unstable，不代表 CI 完成。
- 范围: MetaX scheduling.py / splitkv.py、数值/graph回归测试、graph微基准及CI选择映射，共5文件。
- 实验生产补丁SHA256: 4f3cd49fb47e752b5670c8e53fe6f77564734ef18a8bc7910f5c19a8970b9426；应用到fork main，两个生产基线文件一致，最终生产diff保持一致。
- 已核验历史78项MetaX测试回执；GPU测试函数与FP32 reference的AST未改变。增加3项host guard，提交套件总计81项。
- 当前PR整理验证: 33项隔离host调度检查通过；54项CI工具测试及16个subtests通过；Black24.8.0/isort5.12.0/flake8 7.1.0、语法和whitespace检查通过；源码到测试/benchmark映射检查通过。
- 未重新运行提交套件的GPU测试、打包后的benchmark、正式模型精度和端到端性能；没有改动远端服务或占用评测设备。
- 自动审批拒绝了包含内部模型性能和验证数据的初版PR描述。改用只描述公开代码问题、补丁和本地工程检查的文本后成功创建Draft PR；公共PR未披露内部性能表或模型验收细节。
- Codex应用附件尝试返回side thread not found；PR本身已确认存在，可通过上述链接访问。
- 独立本地checkout: /tmp/qwen36-fa-pr-20261012
- 本地检查证据: /tmp/qwen36-fa-pr-host-checks/scheduler.xml、/tmp/qwen36-fa-pr-host-checks/ci-tools.xml

主线程的state.yml、README、容器、自动化与评测任务均未由此发布操作修改。
