# op-003：应用 MetaX FLA PR #638

- 状态：已应用，28项 CPU/mock 检查通过；用户明确要求将 PR #638 应用到当前优化容器。不重启运行中的服务，GPU/graph/完整精度/性能未测。
- 分类：operator/replace；MetaX backend 内单请求长 prefill 的连续 KV 接入。
- 目标：mx-104，`qwen3vl-pr943-split1-mx104-20261023`；沿用当前案例与既有独立私有源码。无新容器、性能测量或精度 gate。

## 优化方向与瓶颈依据

按用户指定 [PR #638](https://github.com/flagos-ai/vllm-plugin-FL/pull/638) 应用 prefill 路由。冻结上游 head `3e04e696f5ab93d25ef90b1f0e1d0fb50cd9ab60`；只改变单请求长 prefill 的 KV 表示，不更换整仓版本。PR 的 2048 crossover 是待测启发式，不能据此宣称本模型性能提升。

## 优化内容与适用边界

实际文件 `/workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/vendor/metax/impl/attention/flash_attn.py` 位于容器私有层。DECODER、单个 prefill、逻辑 KV 长度至少2048、未量化，且已处于 non-cascade/single-DCP 分支时，按 block table 将 K/V 聚合为连续张量并裁剪尾页；共用一次 varlen 调用。其他 prefill 输入走既有 paged 路径；encoder/cascade/DCP/decode 不变，混合批次保留原输出切片。

当前 Plugin HEAD `08da21cb39601752040196232b60a152382c0f8f`，已有 sampler 与 decode split1 修改保留。目标原文件 SHA `2eaec0be03b16ad1d4b5e24851655eea53d0fb90db83a5ccaeff04011dcb3002`；PR 原文件 SHA `f49f4a5b401a5ca66f04f10b27e7b6f186e3efe1c8d214556efb0b1edaf36514`；候选 SHA `4e12e6ba6b739560cfee8cae47324c859aae1058257b67b89ec2f9357569a174`。候选与上游全文差异仅 decode 的 `num_splits=1`。

不改 FlagGems/gems-opt、FlagGems-vllm/MoE、vLLM、安装、启动参数或 prefix cache。非 MetaX 文件不变；其他平台硬件未测。当前服务已经由用户重新启动，不能沿用上轮维护的“服务关闭”快照，不停止或重启它。

## 正确性与路径命中

执行前冻结 CPU/mock 验证：FP16/BF16 各14条，覆盖2047/2048、非顺序物理页、部分尾页、长 chunk、混合 prefill/decode、多 prefill、量化拒选、cross/encoder/cascade/DCP/decode 回退及输出别名、共用参数、decode split1。执行实际 forward AST，vendor 函数 mock；连续 KV 逐逻辑 token 对照独立页索引参考。执行成功不代表 MetaX 数值、graph 或模型精度通过。

先 CPU/mock 通过，再原文件 SHA guard 替换；重新运行已安装文件测试。全四仓库文件清单前后比较必须只有目标文件变化，服务 PID/startticks/argv/env hash 不变；失败仅恢复本次目标文件，不干预服务。

## 性能效果

未测量。此次仅用户指定补丁应用，无新性能声明；完整精度与 graph 也未运行，不转用历史 gate。现有进程保留已加载实现，新补丁须重启模型服务才生效。

## 决定、风险与回退

已应用文件、等待下次重启生效；`pr_readiness=experimental`，不提交推送。回退使用远端保存的原文件，仅在当前文件 SHA 仍为本候选时恢复，避免覆盖并发人工修改。GPU 数值/graph/端到端效果需后续独立验证，不自动追加本轮运行。

## 外部证据

远端根 `/public-flash/jinghao/qwen3-VL/20261026-qwen3vl-metax-pr638-apply`，位于用户已指定 mx-104 工作根。上传前核验规范路径、owner root/mode755、可用空间14T，独占新目录，不覆盖旧证据。

- `commands/apply_pr638.py` SHA `8f1c32c41c0d686c85b46928dfadb5f3eaaad9ca4b2dcaf191feba9e865d0698`。
- `commands/check_routes.py` SHA `508058ae6c5687a6ab969232d1aa27ec939cb5d63a4461834e2674c93201352d`。
- `patches/pr638-local.patch` SHA `86108ca4b1cb4c36d9ea5f7942ef3caf91698d55b6549a0c7b2ec04f3ae3cf76`。
- 原文件和四仓库已有 Git diff 保存于 `backups/`；前后版本/文件摘要和服务身份保存于 `manifests/`；最终回执 `results/completed.json`。

2026-10-26应用结果：目标候选SHA一致，四仓库逐文件对照只有目标文件变化，28项CPU/mock执行实际安装文件通过，Python语法与目标Git diff --check通过。已有采样、gems-opt、MoE和decode split1均保留。未停止/重启/发送生成请求给运行服务。

原应用脚本的服务检测只检查argv[0]包含vllm，遗漏`python3.12 /opt/conda/bin/vllm serve`包装入口，因此原manifests的services空列表**不能证明服务关闭，也不足以证明完整argv/env前后一致**；原回执保留，不覆盖。补充只读审计 `commands/audit_installed.py` SHA `a046abe0b53a3c565a61b79538f64697da69dc5a8e448accfee877a2fa649def`，按argv[:2]识别并绑定初次只读ps已经观察到的PID1157943/startticks1131602128，再核验源码、decode1与modelsHTTP200；无GPU或生成请求。实际用户服务`qwen3vl-opt11`、9999端口，argv明确`--no-enable-prefix-caching`。本任务未切换cache或其他配置，不能拿之前18977/prefixON的历史恢复当现状。

最终决定为applied-on-disk/restart-required。已加载模型进程不自动采用此文件修改，尚无新路径硬件命中证据。独立审计回执 `results/independent-audit.json`。

独立审计通过：当前用户启动参数CUDA_VISIBLE_DEVICES=0,1、端口9999、served qwen3vl-opt11、prefix cache关闭，原PID持续存在且modelsHTTP200。它与本案例历史GPU4,5/18977/prefixON不相同，本次只读记录，不修改、不混用历史测试或gate。安装文件SHA `4e12e6ba6b739560cfee8cae47324c859aae1058257b67b89ec2f9357569a174`，decode仍1。

最终回执SHA `ebc4b09dda4474d8a5a1f790af831d0e710a6dc25d5813558a49c01749bee355`；独立审计SHA `d4d0bc434041604303a511c29a6267a3b968d9036f7ac360a5106962656bd515`；安装文件28项CPU检查SHA `95107a024547d6e5b3e9c1ec66bb833ecbbc39d53f46830599973802e3a77849`。
