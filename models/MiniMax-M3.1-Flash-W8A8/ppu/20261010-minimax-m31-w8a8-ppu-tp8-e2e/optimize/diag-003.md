# diag-003：TP8 8-head attention 错误的机制定位

已确认：当前 PPU Triton 3.6.0 的 BF16 8-row tile 在 shared-memory→MMA 的 **A 矩阵加载地址生成**中漏掉 lane16 对应的 K 位。K 每32元素内，前16被重复使用、后16被漏掉，造成 Q×K 与 P×V 都算错。源 attention 算法、模型权重和 W8A8 本身不是这一最小复现的必要条件。

证据是修改独立 LLVM IR 副本中的 A 地址（`lane & 8`→A专用`lane & 24`，B原表达式不变），然后原始→修正→原始：最小矩阵随机误差 .998820→1.40e-7→.998820，onehot与128K全覆盖行/列基向量 exact，graph两次通过。原native attention（GQA8/D128/topk16）同一8处A地址修正后，176-token误差1.10164→.00191226→1.10164；qlen2及prefix128同样恢复，并各有两次graph replay。

| 原native算例 | 原路径relL2 | 仅修正A地址relL2 | 恢复原路径relL2 | 两次graph |
|---|---:|---:|---:|---|
| Q176 / prefix0 | 1.101639 | 0.001912 | 1.101639 | 通过 |
| Q2 / prefix0 | 0.364100 | 0.000932 | 0.364100 | 通过 |
| Q17 / prefix128 | 1.108185 | 0.002385 | 1.108185 | 通过 |

现有 fix-001 的H16内部padding避开了错误的H8加载布局，这解释了为何此前它能恢复完整GPQA170/198。此次只做机制定位，没有修改安装的编译器、vLLM、三个推理仓或根脚本，没有重启当前服务，也没有新的GPQA/当前实例rebind或性能收益。全部测试位于独立空闲物理PPU8，生产0..7保留。

结论范围为当前PPU后端、BF16、M8/128/128及MiniMax native Prefill路径；未定位到编译器C++源码行号，不能声称已修复编译器。真实错误生成地址与因果干预已经验证；其他平台/dtype及新的发布修复仍需独立验证。

下面保留执行前假设、失败与收窄过程。

用户明确要求继续定位具体成因。沿用 accdiag-005 已冻结事实：同输入第0层QKV映射一致、H8 native失败、H16内部tile修复通过24算例及完整198。当前不新增性能改动、不重启服务，不更改vLLM或三个推理仓；全部变化限案例诊断脚本内的新JIT函数。

先定位block pointer/索引mask、QK dot、softmax归约、PV dot与融合编译交互。使用物理PPU8（只读预检为空闲）运行独立小算例，生产0..7保留。执行前再次检查卡8和源码SHA；若出现其他占用则退出。此设备变化仅属于机制诊断，不计算TP8性能收益。

同CPU输入固定seed，M4/8/16配对；先测原生路径与独立QK/PV，加入onehot P→PV=V可手算恒等性。数值摘要及编译IR/源SHA保存远端案例，写入同一实验记录。插入观测可能改变编译，因此不以观测后的通过否定原失败。最终报告区分已确认机制与仍未证实的底层原因；不以tile16能修复单独宣称compiler bug。

首轮 micro 完成（result SHA c0fc1a...，scope-review75ca45...）：QK M8误差1.00658，PV onehot M8误差1.16936；M4/M16正确，M8补齐16后QK误差1.50e-7、onehot exact。QK/PV共用完全相同编译IR，排除attention页表/mask/softmax是复现的必要条件。实际backend为PPU，GPU IR将M8 dot转成16x16 PPU MMA，LLVM中A寄存器有重复打包；重复是否错误尚待机制实验，不单凭片段下结论。当前诊断进程已退出，四仓源码、根脚本和当前生产实例保留。

下一轮先测原输入load/store与FP32逐K FMA，并用逐行onehot及行/列编码B做映射检查；原M8与补齐16运行graph两次。最后仅在诊断Python进程移除accelerate_matmul pass，installed compiler字节不变，比较同输入dot结果。全部结果保留，不把编译错误当作数值通过，也不提交性能收益。

第二轮的观测部分有效：A/B加载存储exact、FP32逐K FMA exact、平台torch.mm exact。M8逐行onehot+行编码B输出2k+16（k位于每32下半）；K每32的上半完全丢失；列编码B输出2n。M8 graph两次均relL2=1.05372，补齐16两次exact。后续删除accelerate_matmul pass在当前ConvertTritonGPUToLLVMPPU编译阶段失败，整轮incomplete，不将该失败当作数值验证。

LLVM定位到A矩阵ldmatrix地址：8-row源码的`lane & 8`没有包含lane16的K偏移，基向量模式与此吻合。下一实验只在IR副本将该mask从8改24（保留lane8并增加lane16），通过原始→单变量修正→原始和128K全覆盖验证；如通过，可确认具体地址生成机制，仍不直接修改安装编译器或vLLM。

IR副本全局mask8→24只恢复onehot0与K全覆盖行编码，随机仍relL2=.714866，故保留为部分机制证据，不作为修复；原SSA同时用于B地址且带or disjoint假定。进一步只分离A地址（新增lane_A_kmask=tid&24，A的XOR改用新变量，B保持tid&8）后：随机relL2=1.39662e-7，onehot exact，128K所有行/列编码exact，graph2误差同量级；恢复原IR后随机relL2=.998820、onehot1.021741重现。结果d4de997.../scope-reviewd9f23efe...。最小矩阵乘的地址遗漏lane16机制已确认，下一步只核对原native attention生成IR同一缺陷。

原native attention首个IR确认控制因mask解析严格匹配debug尾逗号而退出，未应用任何IR改动；scope-review0033a919...。原生IR已归档（541341d...）。修订解析先在本地CPU对实际IR做预检，按BF16 MMA前4寄存器反向溯源，仅选中A的8个ldmatrix，唯一被遗漏的mask为%232=tid&8；所有B加载保持原表达式。修订实验覆盖qlen176/2及prefix128，并做原始→A地址修正→原始、graph2；是机制诊断，无安装源文件变更。

最终证据复核通过：`profiles/diag003-rootcause-01/review.json`，SHA `b4dfa8f88ec387e2dff633449a682caa4f522ccbed9f0ba4703e8011b956712d`，完整远端路径见state.yml。核心native result SHA7036be99...、scope-review a67c2d69...；控制脚本签收原始→A-only→原始、3个native算例及各2次graph、全128K基向量、四仓/根脚本不变、原生产进程保留、卡8无残留。C++扩展与Python后端身份SHA写入state；没有compiler源码PR或模型验收签发。
