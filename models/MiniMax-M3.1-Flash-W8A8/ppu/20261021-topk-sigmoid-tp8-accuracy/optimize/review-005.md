# review-005 Plugin 局部收敛

状态：已安装并通过定向回归。目标PPU-07容器`minimaxM3.1-opt-topk-sigmoid-20261021`，Plugin私有根`/workspace/vllm-plugin-fl`，官方main a696859。用户要求的三项收敛均在现有文件内完成，无新增源码文件、测试模块、dispatch、环境变量、kernel或全局方法包装。

## 最终改动

1. `quantization/w8a8/moe_experts.py`：选中experts实例通过私有`_activation_kwargs`统一保存三个已校验参数并直接透传。构造器finite/positive-limit和dynamic INT8校验、调用时缺参数拒绝保留；不写共享quant-config，不影响原SiLU路径或native adapter。
2. `ops/fused_moe/activation.py`：现有文件新增私有执行helper，集中可选融合探测、缺符号/不支持时普通激活回退及显式参数校验；执行错误继续抛出。`fused_moe.py`保留INT8/per-token/scale/block/其他量化类型的语义条件，仅把具体执行交给该helper。原`apply_moe_activation`公开API与原MoE其余pipeline的AST均不变。没有新算子实现或独立dispatch注册。
3. 测试仍在既有`test_w8a8_moe_experts.py`和`test_activation.py`中：共享oai_chain fixture，missing/decline参数化，保留原隔离/参数/选择/错误传播断言；扩展已有graph测试为宽6144非融合、宽768融合、宽766形状回退，每项两次变输入回放。

总计调整3个生产文件、2个测试文件。此次收敛目标是集中职责与参数来源，不是减少总行数；私有helper的类型/契约说明以及更完整的graph验证使总行数略增。不借整理更改量化舍入、scale、GEMM参数或库版本。topk边界与fallback、INT8/FP8接口隔离、模型映射和Thead GQA兼容均保持。

## 验证与边界

- `minimal-regression`：119 CPU/mock合同通过，11个GPU用例被deselect；另行4项物理0实际设备测试通过，无skip。原有宽6144激活reference对照以及三个helper graph路径均通过，融合INT8与FP32 scale和既有generic activation→vLLM量化reference逐位相同。
- 源码AST审计证明原tensor/输入校验、native adapter、普通activation API不变；融合8项量化资格条件与2项env/policy条件和原分支完全对应，其余pipeline AST不变。没有靠fallback冒充width768融合命中，graph测试显式要求返回融合结果；766显式要求decline并走普通激活。
- FV完整tree13f04b77、FG1798d770及用户compiler adjust SHA bffec8df均不变。独立进程实际导入仍来自规范Plugin/FV目录，导入证明不表示workers重新加载。
- Ruff按Plugin配置通过；完整最终Plugin补丁包含原未跟踪文件，diff check及reverse check通过。
- 8045原实例startticks未变、health200；未重启模型或容器，未发送模型推理请求，未触碰物理8–15。没有新模型加载/smoke/C8、完整三数据集、性能或新gate；旧167/198、467/500、267/400保留为历史。模型级重验证仍未执行，不将本轮单卡测试写成新TP8验收。

首次准备控制因读取不存在的triton distribution metadata退出，发生于apply及测试之前；证据保留在review005-20261022-01。随后在新-02归档中从实际triton模块取版本完成预检；未改变依赖、检查阈值或重试失败的数值测试。

## 证据、回退与PR

原始材料位于`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/review/review005-20261022-02`，命令先归档`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/commands/review005-*`，SHA写入state。before/plugin保留精确五文件旧内容；回退应先检查当前候选SHA及服务状态，再仅恢复这五文件，不影响其余修改；本轮未执行回退或stash。

最终Plugin full-repository tree `03261630bd3b6ba6503a7f40395cef4395b723038fd1f13cebada126c8e7bb35`。完整PR补丁`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/review/review005-20261022-02/pr-plugin.patch`，SHA `32ea14f50b5b51fda91bac056e6f080975d208ceda33d8f7fffe146f217c5a1a`。最终差异仍23文件（14生产/9测试）；FV补丁沿用review-004，不将其写成本轮新改动。

pr_readiness=ready_for_review表示可提交维护者评审，不表示所有平台硬件/新模型精度已验收。没有提交、推送或创建PR。当前模型进程继续使用已加载代码；本轮磁盘修改已由独立测试进程验证。
