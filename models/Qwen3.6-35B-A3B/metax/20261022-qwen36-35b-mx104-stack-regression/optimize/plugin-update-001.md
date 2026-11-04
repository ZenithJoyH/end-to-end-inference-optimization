# Plugin release/0.2 更新

用户要求更新当前 B 容器 Plugin。目标 mx-104 / qwen36-35b-regression-b-20261022 私有 /workspace/vllm-plugin-FL，当前release/0.2 HEAD7cb559947cb61fd8b69fa5027d8ec113e528a644。保留本地7个tracked修改及全部untracked；FGV c4673a/vLLM/Gems/模型/启动配置不变。仅更新源码，不自动重启或发模型流量，不复用旧精度gate。

设计归属：环境维护，沿当前分支快进并三方移植既有本地改动；无需新增dispatch/backend或kernel。先独立准备合并结果，冲突逐处审阅，实际工作区最后替换。跨平台运行/模型精度尚未验证。

挂载已核验仅/data和/public-flash，/workspace私有。无活动controller。先完整tar备份含.git，再fetch origin release/0.2。

归档并执行 commands/plugin-update-audit-fetch-001.py SHA 664af6427712d0dd2ebc13998f3c1fdac24fc4c771c8d13e4519675683a8415e；输出 environment/plugin-update-001/audit-fetch.json，执行前已记录。回退材料 plugin-before.tar.gz 和local.patch，原文件不覆盖。

上游仅新commit1bc0c775ffbdf4a0b0e2efb5e847d586e902273f（PR638），只改flash_attn.py；实际本地PR文件预期字节等同upstream。执行前逐字核验、原index无staged更改、祖先关系通过后，git reset --mixed推进当前release/0.2/index，工作区所有字节及untracked原样。无hard reset/checkout覆盖。新唯一 commands/plugin-update-apply-001.py SHA 6f53606352c1f34940a4ad77ab231ef7a6709e2bbffb8f7912b94a878ed54a26，先归档SHA再执行；备份SHA ebb5c89aaa15c74d75c5d31208789219f0de66ee2b4598e859584a102c03a8b9。验证全部工作区文件SHA相等、Python compile、fresh Plugin import、FGV源SHA不变。无需设备/model测试，因推理源码字节没有改变。

apply001已推进HEAD和通过全字节/compile断言，但末尾observer使用docker默认python3而非实际Conda，import vllm_fl时ModuleNotFoundError。保留apply-result.json，非服务/模型失败；不重放变更。新只读commands/plugin-update-verify-002.py SHA f443c991c9432ca4707b8d8cdf52913c2153bad5178f9de87144f1dccf67b675使用/opt/conda/bin/python，从原tar独立逐文件重算工作区字节，fresh import和语法检查，无任何源码/分支写入。

verify002实际Conda import因独立exec缺少服务中的MACA_PATH导致FlagTree driver初始化拒绝；非更新引入的源码错误。保留verify-result-002.json。新只读commands/plugin-update-verify-003.py SHA 1e85d035d8542f40e5b48e83c1660b7850c0e2f2ca06ea82fd5f539d39f9f27c仅为这个子进程传入MACA_PATH=/opt/maca及MACA_HOME=/opt/maca，不更改服务环境。所有失败完整保留，无模型/服务操作。

条件式收尾commands/plugin-update-closeout-004.py SHA e174c6a0cfff440d9d19f314a390b0d916ccc2d2a8106080884c1584e4ae5df5：仅verification003通过才追加远端continuation.plugin_update_001，CAS确认无活动job，保存前后副本；原phase/current_service和GEMM pending-reload事实保留。0模型/服务操作。

## 结果

已更新当前release/0.2 HEAD7cb5599→1bc0c775ffbdf4a0b0e2efb5e847d586e902273f（上游合入PR638）。517个工作区文件逐字SHA与更新前完整tar一致；flash_attn.py原本就是上游PR638版本，因此其本地M标记自然消失，其他6个tracked本地修改+4个untracked全部保留。399个Python源码compile通过，真实Conda+MACA导入vllm_fl路径正确；FGV c4673a保持。没有服务重启、模型流量、GPU数值/性能测试或新精度gate；因有效源码无变化，未新增设备测试。

最终独立报告 environment/plugin-update-001/verification-003.json SHA a4c95b2fde3308845a0a763b9bb9d7f7b066666f51512f49a604854c76605365；全部失败observer产物保留。remote continuation SHA5ad777e34edfd5eedbfdb2fc42281896b5e4ea8a2fccf5a4a9fe41a69c66ca48。先前GEMM源码待服务重载事实不因本次Git base更新而改变。
