# op-002：按用户要求回退当前容器的 PR638 FLA 修改

授权：用户明确要求“把容器中针对fla代码修改回退下吧”。目标仅 mx-104 的 qwen3vl-pr943-split1-mx104-20261023，当前 fork024plugin-opt / HEAD08da21cb39601752040196232b60a152382c0f8f；回退 Attention 文件的 PR638 Prefill gather 改动，不改 split0、采样、MoE、gems-opt 或启动脚本，不启动/重启模型。

## 归属与边界

类型：operator/replace 的显式回退，恢复现有 MetaX vendor Attention 原 paged KV 调用。不新增 hook/dispatch/config，不影响其他平台的文件。目标文件是容器私有 /workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/vendor/metax/impl/attention/flash_attn.py；只挂载/public-flash与/data，目标不在共享挂载下。

修改前文件 SHA f49f4a5b401a5ca66f04f10b27e7b6f186e3efe1c8d214556efb0b1edaf36514；预期恢复 HEAD 文件 SHA f81fa552667b3ed98d1cf141d2dee33ba10476cda9a997744495bdbc36289ef2。只读 git diff 已确认全部改动属于 Prefill 的局部连续K/V gather及输入替换；current/HEAD 的 native kvcache 调用均省略 num_splits（默认0）。

当前容器仅 sleep infinity 和交互 bash，没有模型/benchmark 进程。代码回退后留待用户启动生效，不自动发送GPU请求。服务/配置/其他源码前后核对；不签发精度或性能结论。

四仓库修改前：Plugin08da21c（__init__/sampler/Attention本地改动），vLLMee0da84干净，FlagGems c3c5f5ab干净，FGVbad340d（MoE/采样现有改动）。所有 tracked/untracked 非ignored仓库文件前后做SHA比较，要求唯一变化是目标 Attention 文件。

## 可复现命令与验证

远端既有用户授权案例根：/public-flash/jinghao/qwen3-VL/20261027-qwen3vl-opt13-performance-gap；在新 rollback-pr638/ 子目录保存 commands/backups/results，不覆盖此前诊断。根真实路径、owner/权限、空间和新子目录不存在已核验。执行脚本先归档并记录 SHA，随后保存目标原字节、HEAD字节、diff、四仓库指纹后再原子替换目标文件。guard同时检查当前文件与HEAD指纹、私有目录、无模型/benchmark进程，防止误写新状态。

静态验证：恢复文件等于HEAD、AST/compile语法、native调用未显式split、Prefill原k_cache/v_cache/block_table、git diff --check、四仓唯一文件变化。无GPU/graph/完整精度/性能复测，未测项显式保留。再次恢复PR638可使用本次备份并核验SHA。

归档命令：rollback-pr638/commands/revert_pr638.py，SHA `f33dbd86469402235f05010b9baa186833624e23ad940f9b0fb8e320ceb07b45`。项目 connectivity-check 在受限环境遇到本地 Ansible RPC 启动错误，正常权限重试已完成 mx-104 专用验证；未以普通SSH退出码替代连接核验。

## 完成结果

2026-10-27 15:39:44北京时间完成，状态 completed-on-disk。目标文件SHA f81fa552667b3ed98d1cf141d2dee33ba10476cda9a997744495bdbc36289ef2，逐字节等于当前024plugin-opt/08da21c的HEAD文件；Prefill恢复直接传key_cache/value_cache和原prefill_block_table，PR638 gather及其日志移除。native kvcache仍省略num_splits，使用vendor默认0。

四仓前后文件校验：vLLM5655、Plugin579、FlagGems6571、FGV1082，合计13887项；唯一变化为目标Attention文件。原采样适配、直方图、gems-opt和FGV MoE均保留。AST/compile语法、HEAD等值、git diff --check通过；独立只读复核目标/备份/命令SHA再次通过。

回执：rollback-pr638/results/completed.json，SHA `c2bedd284d036aedb72de565fc19960e61ac61224db62cfacf9c2b8fb664e0c6`。完整前后指纹和scope在同目录results/；原文件备份rollback-pr638/backups/flash_attn.before-pr638.py，SHA f49f4a5b…；HEAD原文件与旧diff也已保留。只在用户需要重新应用PR638时按该备份有界恢复。

前后均无模型或benchmark进程，未启动/停止/重启服务，未发GPU请求。用户下次启动模型即加载恢复后的FLA；本次不宣称graph、正式精度或性能已经验证，也不把先前opt13/opt12结果转绑到新源码。
