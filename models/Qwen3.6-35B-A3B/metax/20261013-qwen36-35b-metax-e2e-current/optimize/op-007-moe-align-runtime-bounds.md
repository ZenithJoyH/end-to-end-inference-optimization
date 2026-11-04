# op-007：MoE alignment 输出边界取消值专化（规划）

方向：operator/improve；父场景P1024/D1024/C64/N128，关注Mixed/prefill/Decode中alignment阶段的形状编译。当前仅证据和方案，不与op006叠加部署。

自有TP LLVM与同时间窗TTIR源定位确认当前stage1来自/workspace/FlagGems-vllm/src/flaggems_vllm/ops/moe_align_block_size.py:405。MetaX fused_moe显式导入moe_align_block_size_no_tle，经4stage调用stage1，插件align shim也指向同一库入口；不是通用FlagGems同名文件的猜测。捕获两份LLVM除临时ModuleID及两个mask界限48968/766和51064/798外逐字相同，E256、tokens_per_thread256、block_size_sorted256、block_size_expert4都相同。

拟议单变量：将numel_sorted_token_ids、numel_expert_ids两个tl.constexpr mask界限改为运行时标量/do_not_specialize；保留num_experts、tokens_per_thread、block_size_sorted、block_size_expert以及实际padding block_size。两个长度只用于offset<length的写入mask，不驱动向量形状；不能取消用于tl.arange的block参数。整套alignment的整数排序/专家ID/计数/填充、invalid expert map和smallbatch收紧行为保持原契约。

首个证伪：当前固定vectorbucket的两个捕获长度应只需一个编译模板；完整alignment而非stage1单函数做精确整数/填充校验，覆盖小/零token、power2边界、dtype/stride、E与block边界；再验证目标graph>=2 replay、原生benchmark每声明case old/current>=.95。公开generic stage1会影响其他后端调用，实施前按目标repo设计比较通用标量改动与MetaX边界方案；未测平台不宣称通过，不加plugin平台特例或native/Torch计算fallback。任何正确性/越界/graph/性能guard失败停止并保留结果。

当前环境：mx-59/qwen3.6-35B/8010/TP2物理GPU6/7，当前源gdn-current-plus-op005-bca465d2。用户要求保持FlagGems全部启用；attention/GDN/MoE workspace复用保持。原地例外有效，vLLM/模型/tokenizer只读，不停容器/其他负载。已有单次停服窗口均结束；本计划不含自动重启/部署授权扩展。

当前正式GPQA170/198=85.8586% gate仍有效；但只属于已加载source。新候选无已执行精度/graph/benchmark/E2E数据，不能复用当前gate签发新source；正式加载后按198/max65536/temp1/top_p.95/top_k20/seed42/C32/80门槛重新验证。最小回归先执行，失败保留并诊断，不叠加优化。

完整P1K006的1133.427/991.227/1146.247tok/s、13.677%spread>10%以及慢轮全部保留，不能挑快轮算收益、改warmup、重跑creator或直接切P4K。全部原始产物留唯一ROOT；下一步私有候选必须从当前GDN+op005源码复制并保存现有dirty/SHA/补丁/回退，不能使用旧sampler整包覆盖。

结果/决定：planned_not_implemented，production code_change=none，GPU correctness/compilecardinality/graph/standardbenchmark/E2E全部not_run，PR readiness=planned/untested；非目标硬件未测。回退目前无需执行，因为没有修改；私有补丁产生前先记录beforeSHA和可恢复快照，失败仅保留私有产物，不动运行服务。

外部结论：/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/results/op005-residual-specialization-conclusion-20261015.json SHA75bbd364697597101ce2562acdb936a92e49c4a7ee928ce7af583f8e6a1028ec；真实LLVM差异证据7a54a0fa8ea108a4545e2d2efb71416d67e23b3adebe9af8fea75289eabbc7b9。
