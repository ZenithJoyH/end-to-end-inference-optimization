# op-004：MetaX Attention 精确对齐 PR #638

用户明确要求删除当前容器的 `num_splits=1,`，使 MetaX FLA 调用代码仅保留 PR #638 的变更。按上下文限定为 Attention 文件；已有 Plugin sampler、FlagGems-vllm MoE/采样和 FlagGems 优化保留，不将整容器回退到 Plugin PR 基线。

目标为 mx-104 的 `qwen3vl-pr943-split1-mx104-20261023`，源码 `/workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/vendor/metax/impl/attention/flash_attn.py`，私有 `/workspace`。Plugin HEAD `08da21cb39601752040196232b60a152382c0f8f`；FGV `bad340d67a35e583989fcebf56326f60edc85c9c`，FlagGems `c3c5f5ab274f7d1a8a95e3d3ba7bbac28e4a9fd4`，vLLM `ee0da84ab9e04ac7610e28580af62c365e898389`。四仓库现有改动先完整指纹化并保存，修改前备份目标文件。

冻结 PR head `3e04e696f5ab93d25ef90b1f0e1d0fb50cd9ab60`，目标 PR blob `fb2de517e5898ee247c663640c63c8e3ab124999`。只删 decode native kvcache 调用的显式 split1 参数，恢复原 vendor API 默认行为；不修改 prefill 路由、sampling/MoE、启动参数或 prefix cache。候选必须与 PR 完整文件逐字节相同。

执行前脚本：/public-flash/jinghao/qwen3-VL/20261027-qwen3vl-metax-pr638-only/commands/remove_split1.py，SHA `80531fbd33de1d185710c9dbd3c3915577022610b41bd2c8c49463b3f36ff373`。远端目录用户授权根 `/public-flash/jinghao/qwen3-VL` 下新唯一子目录，owner/权限/符号链接/空间预检后创建。备份和四仓库 before/after 指纹留在远端；当前服务身份前后核对，不停止/重启服务。语法/AST/PR blob/差异检查，不发模型请求或新性能实验。当前现有服务已有加载代码，不声称磁盘修改热生效；新 split0 配置须用户后续重启，旧 split1 精度不能重绑定。

状态：completed-on-disk，运行中服务保留，后续重启生效。

## 执行结果（2026-10-27）

11:38:30 北京时间完成单行删除。安装文件 SHA `f49f4a5b401a5ca66f04f10b27e7b6f186e3efe1c8d214556efb0b1edaf36514`，Git blob `fb2de517e5898ee247c663640c63c8e3ab124999`，与 PR #638 head3e04e696 文件逐字节一致。目标 native kvcache 调用无显式 num_splits；使用 vendor API 默认设置（split0/自动选择）。静态语法、AST、git diff --check 通过。四仓库 tracked/untracked 源码指纹仅此一个文件变化，其余现有采样/MoE 优化全部保留；因此只声称 Attention 文件精确等于 PR，并非整个 Plugin 或容器只包含该 PR。

回执：/public-flash/jinghao/qwen3-VL/20261027-qwen3vl-metax-pr638-only/results/completed.json，SHA `3516f0fd0f493cbb5b9a189ee3b9ec2bc2695f72b89f781a0a8de3f670bba1be`。备份：/public-flash/jinghao/qwen3-VL/20261027-qwen3vl-metax-pr638-only/backups/flash_attn.before.py，SHA `4e12e6ba6b739560cfee8cae47324c859aae1058257b67b89ec2f9357569a174`；可按指纹有界恢复，未自动回滚。

独立只读核验当前源码 SHA/AST 和原进程 startticks 通过，9999 /v1/models HTTP200，served name qwen3vl-opt12。未停止/重启服务或容器，未发生成请求。当前服务 prefix cache OFF 是用户启动事实，未变更。运行中 worker 不热更新；本次 split0 源码不继承旧 split1 GPQA/ERQA 精度 gate，未运行 GPU/graph/正式精度/性能。
