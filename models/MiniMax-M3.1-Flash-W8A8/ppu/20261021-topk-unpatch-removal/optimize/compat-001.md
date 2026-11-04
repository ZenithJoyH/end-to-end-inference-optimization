# compat-001：按用户要求移除top-k固定launch兼容

2026-10-21用户明确要求“你把topk的patch去掉吧”。仅修改PPU-07 `minimaxM3.1-opt-latest-20261020`私有Plugin副本；FlagTree0.7.1.dev1+ppu3.6、GQA head-tile兼容、其他三库改动和启动配置保持。

当前只读预检发现8045已停止、容器没有模型进程；本轮保持其停止状态，不替用户启动模型或评测。实现范围为Thead `patch.py`删除`_PrefillIndexTopK`及`_patch_prefill_topk`，模型加载hook仅安装GQA兼容；复用现有`test_thead_launch_compat.py`清理已删除逻辑并验证不包装top-k，避免新增测试文件。

变更前备份两个文件、记录三库revision与完整源码指纹、归档命令和补丁；变更后断言GQA类与安装函数逐字不变、除目标两文件外所有源码字节不变。运行受影响的Plugin单测与格式/语法检查。不会stash/commit/push。

依据：上一轮独立8卡50项数值/graph检查及100次replay通过；已知原生autotune与K128在tie上可能选择不同block，此行为由用户明确要求恢复。该记录不把旧模型分数迁移成新候选精度，不宣称模型级回归或正式GPQA已通过。

远端案例：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-removal-01`。

## 完成结果

**已移除top-k patch。** 删除`_PrefillIndexTopK`、`_patch_prefill_topk`，Thead加载hook不再导入/包装`index_topk`；只调用原有GQA head-tile安装函数。`_PrefillHeadTile`类与`_patch_prefill_head_tile`函数源码逐字相同。关联测试在原文件收敛为GQA/架构选择/worker顺序/幂等检查，并在原架构测试中验证top-k对象不变；没有新增Plugin测试文件。

仅改动：

- `/workspace/vllm-plugin-fl/vllm_fl/dispatch/backends/vendor/thead/patch.py`，最终SHA `b0ecc6d69c4f42690842b2871810a642172c032fbbb1a7513b9c1869c2f2a8ae`。
- `/workspace/vllm-plugin-fl/tests/unit_tests/dispatch/test_thead_launch_compat.py`，最终SHA `834d1485555ba2bd2529a9b9c01a3a8cad4e54a0c8415b0065d2f0f315f2b23d`。

逐文件核验其余Plugin/FV/FG源码无变化；版本未升级，未stash/提交/推送。精确变更见[删除补丁](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-topk-unpatch-removal/topk-removal.patch)，SHA `2abc4737685b04213fd7cb928fea028cf2523c696a742c4e9800865ff966edc9`；原件备份在远端`backup/`，恢复只需按`change-result.json`校验对应旧文件，不覆盖其他用户改动。

## 验证与边界

现有Thead兼容和MiniMax注册两组测试共**13项通过，0失败/0跳过，4项GPU测试明确未选中**。随后在真实导入模块调用`apply_thead_patches`，验证top-k仍是原来的`Heuristics → Autotuner → _topk_index_kernel`对象，六组K候选2048/1024/512/256/128/64保留；GQA仍安装且重复调用幂等。源码语法、残留符号搜索、git diff whitespace检查通过。

首次隐藏全部设备导致vLLM非GPU测试导入时无法查询device capability，留下2个导入错误、11项通过、4项跳过；其`unit.log`/`unit.xml`完整保留。更正测试环境为仅物理0号卡可见以供能力查询，并用`not gpu and not multi_gpu`显式排除GPU测试，未修改生产源码来迎合测试。更正后的回执位于`verification-visible0/`。

8045在操作前已停止，终态仍停止；未启动或重启模型服务。下一次用该容器启动时将使用原生top-k autotune。**本轮没有执行去补丁模型最小回归、正式GPQA或性能测试，不能宣称旧分数已验证当前组合。** 先前50项/100replay只作为相同原生kernel与编译器的独立算子证据；已知tie行为改变仍有效。

远端终态`result.json` SHA `f3dc94847a67424cfb6df97baca4c611fc490340764ad56d3bae4216f82dc173`，单测XML SHA `2f9f67f184fb30229291b3a1de9ddb254dbf1af13085daa7802a5a450a2c55e7`。各命令与备份/验证原生路径见[state.yml](state.yml)。PR准备状态experimental，剩余项为模型级验证；本轮无新gate或自动监控。
