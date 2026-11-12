# fix-012: PR1069 signed-zero 过滤语义修复

状态：completed-pr-updated-source-preserved。用户明确要求修复 review 4508852208，保留排序和现有优化，补边界测试，验证正确性、graph 和性能后更新 PR1069。仅 PR/私有验证容器，不隐含生产部署。

## 实现与冻结验证

新增 `_filter_order_key`，仅把负零比较 key 归一为正零，用在 threshold 计数和 mask；原 `_order_key`、排序位还原、单行/批量排序、前缀统计及 m>=32/n>=131072 guard 均不改。参考实现不改，保留 retained-value 位模式。原134测试加124边界/graph测试；先实际GPU重现旧版本错误，再验证新版本。

性能仅算子 targeted 回归，复用上游 Benchmark.get_latency；44输入/mode组合、两计时方法、20预热calls/20mswarm/50msrep、3稳定窗口<=10%最多8、5轮固定B/C/R，全部保留，B/R漂移和候选回退上限5%。继承的小词表0.9x Torch例外保留，不扩大本次修复。无模型完整精度或端到端收益结论。

远端唯一根目录 `/public-flash/jinghao/qwen3-VL/20261104-qwen3vl-mx59-topk-topp-pr/fix012-signed-zero-20261109`。源当前opt18/8030/GPU0,1保持；GPU2/3无关模型运行，选当前空闲GPU4，执行前重新检查。新no-pause不可变快照、挂载完全一致、私有源码和真实导入核验后才执行。最终恢复私有文件、停止自有clone，源PID/源码/参数/cache保留。

## 工具事实

旧identity只看 argv包含serve，误把用户现有vllm bench serve计为第二服务；这是只读采集器假设，0GPU/0服务变更。新collector明确排除bench。仓库AGENTS/workflow已读，optimization.md和deep_opt.md在此revision不存在，按现有算子规范执行，未跨目录取同名文件。

## 执行前命令冻结

- `benchmark.py`: `68961c3dd85a7e24f4406b31a18a7410f08802bcfc95ac15e9f088dd6e99fcb2`
- `control.py`: `52aca863be4564be85be2221e0fe2e8cd834ab99f599866e2fc983de812296c2`
- `backend-baseline.py`: `8e34b2921baadc8c619288027f9ed1e8e14155b176b24d79edcedd671ba06f13`
- `tests-candidate.py`: `168c5a2a537d096147d4eb6ecc728abe71b1b840caeba78fcf3a940a9f20ecb6`
- `mounts.py`: `32adacf39859e88ad6e2dad04ada248a00b636c795fed67d34328f5264bec3e3`
- `tests-baseline.py`: `abb9e0f980b4dd64460e40100e82b8c830dbf9bea65d8e9d1e1f7adc63d6845b`
- `component.py`: `20483d53a1911997b45cbf5708ecf2604948e5c05b3a0945da97d34c29d9dc65`
- `identity.py`: `a769727ff5f0266d5053bd11240455c50dda1a151e5d591dd912cc3f46670838`
- `backend-candidate.py`: `6a21e25a36135d115a571722ee1a2343a17cf3baca15d700ee57320d4d367be1`
- `contract.json`: `e5024720430793cbce1bce6b5addea5b45fb93b8a2e29979ce0a8f06733e1cd6`

唯一准备/启动命令 `/tmp/qwen3vl-pr1069-signed-zero-20261109/upload.py` SHA256 `c3249be9a492deddb61442de4d6e23d30de4127216df77f6ebf8f05b194020e2`。先归档命令与契约，唯一异步控制器执行no-pause快照、私有clone和硬件验证，finally清理自己的clone。

## 资源保护：新独立v2

初始控制器2332981在首个free检查检测GPU4被无关2309116/2309117占用，0快照/0clone/0GPUcalls退出，保留原failure。最新mx-smi确认GPU6空闲，新契约固定GPU6，所有B/C/R在同GPU6测，不能与历史GPU3数据算单变量收益。v2根目录 `/public-flash/jinghao/qwen3-VL/20261104-qwen3vl-mx59-topk-topp-pr/fix012-signed-zero-20261109/v2`。未停止任何其他服务。

- v2 `benchmark.py`: `68961c3dd85a7e24f4406b31a18a7410f08802bcfc95ac15e9f088dd6e99fcb2`
- v2 `control.py`: `61d82243773e1430f1180571eed0a121b6b48dc86b857167e379245c4edf9710`
- v2 `backend-baseline.py`: `8e34b2921baadc8c619288027f9ed1e8e14155b176b24d79edcedd671ba06f13`
- v2 `tests-candidate.py`: `168c5a2a537d096147d4eb6ecc728abe71b1b840caeba78fcf3a940a9f20ecb6`
- v2 `mounts.py`: `32adacf39859e88ad6e2dad04ada248a00b636c795fed67d34328f5264bec3e3`
- v2 `tests-baseline.py`: `abb9e0f980b4dd64460e40100e82b8c830dbf9bea65d8e9d1e1f7adc63d6845b`
- v2 `component.py`: `d30b2ad0b63e080d708da2ba8fe5551805ba047367eb55ef22836f5d9de4e86a`
- v2 `identity.py`: `a769727ff5f0266d5053bd11240455c50dda1a151e5d591dd912cc3f46670838`
- v2 `backend-candidate.py`: `6a21e25a36135d115a571722ee1a2343a17cf3baca15d700ee57320d4d367be1`
- v2 `contract.json`: `02341516a95c3731ee78ac9bedba76cf5d133dcc05e7cf6c6280a219133ba121`
- v2 `upload.py`: `0f9133683c8dab3d879bbe03f95ccd41af6da077c15863059fe4f99875549c5a`

本地两个改动文件pre-commit全部通过。旧qwen lintenv的pre_commit模块已失效；已用现有pr477工具环境及同版本hooks完成检查，不改目标依赖。

## 身份采集器历史常量修正

v2 collector仍含历史opt17 PID346908/ticks硬编码，因用户已重启opt18而在快照前拒绝；0clone/0GPUcalls。已完整核对collector源码，去掉历史pin，独立只读CPU预检通过；新v3契约明确绑定本轮当前opt18 PID554499/ticks712849436，由控制器校验并保留前后全源码/参数一致检查。源服务未变更。

新唯一根目录 `/public-flash/jinghao/qwen3-VL/20261104-qwen3vl-mx59-topk-topp-pr/fix012-signed-zero-20261109/v3`。
- v3 `benchmark.py`: `68961c3dd85a7e24f4406b31a18a7410f08802bcfc95ac15e9f088dd6e99fcb2`
- v3 `control.py`: `186b822a2a0bc74fb137a377a1a18775b9dd9c6e924eed62cf1e164bb7945787`
- v3 `backend-baseline.py`: `8e34b2921baadc8c619288027f9ed1e8e14155b176b24d79edcedd671ba06f13`
- v3 `tests-candidate.py`: `168c5a2a537d096147d4eb6ecc728abe71b1b840caeba78fcf3a940a9f20ecb6`
- v3 `mounts.py`: `32adacf39859e88ad6e2dad04ada248a00b636c795fed67d34328f5264bec3e3`
- v3 `tests-baseline.py`: `abb9e0f980b4dd64460e40100e82b8c830dbf9bea65d8e9d1e1f7adc63d6845b`
- v3 `component.py`: `a40aff9b9b4a5182bb0a984914ee9300026b871c5fdd39aa6d5a3df33d99a484`
- v3 `identity.py`: `5466dd5fd825770469678398144db447d26cb1744ab7271a7b98631f9b318d04`
- v3 `backend-candidate.py`: `6a21e25a36135d115a571722ee1a2343a17cf3baca15d700ee57320d4d367be1`
- v3 `contract.json`: `e25f725523537a8981d2f0193d76dc6b87de10d3f6026a30eedc8f6a64cff48b`
- v3 `upload.py`: `4352b6ecaa95d00ead892cee53029dd3dcc36a462b38ad6f68cd11318c55de2c`

本地54项CI工具测试及16subtests通过；初次本地工具测试目录拼错工具事件无GPU/无产物影响，正确目标为tools/test_ci_absolute_imports.py和tools/test_ci_helpers.py。

当前唯一v3控制器2341069/startticks713174021，control.py SHA186b822a2a0bc74fb137a377a1a18775b9dd9c6e924eed62cf1e164bb7945787；不得重复启动。静态AST复核20个原函数在还原两处filter helper名/文档后全部相同，benchmark/reference字节未变。

## 快照成功、CLI提示解析工具事件

v3已成功no-pause生成不可变快照05822ba1（parent原faefdf7，12,196,689,168bytes），但Docker --pause弃用提示混入返回值，imageID完整字符串校验拒绝；未创建clone/未运行GPU。source-preservedpassed；Docker事件仅commit及只读exec，无pause/unpause。新Docker应使用 --no-pause。v4仅复用已核验快照，不再commit；先核验v3完整source-before与当前源全部一致，clone代码/mount/model/import再核验。旧failure保留，不作模型失败。

当前唯一执行根 `/public-flash/jinghao/qwen3-VL/20261104-qwen3vl-mx59-topk-topp-pr/fix012-signed-zero-20261109/v4`。
- v4 `benchmark.py`: `68961c3dd85a7e24f4406b31a18a7410f08802bcfc95ac15e9f088dd6e99fcb2`
- v4 `control.py`: `7af84e1c493c8335e457481f01c916490f27c6e373052c547d7d9d0b8623d486`
- v4 `backend-baseline.py`: `8e34b2921baadc8c619288027f9ed1e8e14155b176b24d79edcedd671ba06f13`
- v4 `tests-candidate.py`: `168c5a2a537d096147d4eb6ecc728abe71b1b840caeba78fcf3a940a9f20ecb6`
- v4 `mounts.py`: `32adacf39859e88ad6e2dad04ada248a00b636c795fed67d34328f5264bec3e3`
- v4 `tests-baseline.py`: `abb9e0f980b4dd64460e40100e82b8c830dbf9bea65d8e9d1e1f7adc63d6845b`
- v4 `component.py`: `fcf2184c9a862feeb1966fd0c567d7940b59f9130a2b84a9c0e130ab84065b10`
- v4 `identity.py`: `5466dd5fd825770469678398144db447d26cb1744ab7271a7b98631f9b318d04`
- v4 `backend-candidate.py`: `6a21e25a36135d115a571722ee1a2343a17cf3baca15d700ee57320d4d367be1`
- v4 `contract.json`: `b4a06fe28b2fad25dcd075a45b7dc9168a186724ee96a128b3dbb0aeeb2cf7bb`
- v4 `upload.py`: `faf11431b458e918a438b6cc71c94b9e0994bf937c6c46cc72aaea28f9436640`

## 硬件验证进展

v4唯一控制器2343154/ticks713204874，前3工具控制器均已退出，无并发实验。挂载与快照完整源码/导入/模型事实匹配passed。GPU6实际公开入口已复现旧signed-zero错误6组；新实现48组普通输入与基线位级一致，8额外capture/24变化输入回放、输入/RNG保持通过。完整单测258 passed（含124新增），耗时115.05s；单测26capture/78replay（12新增/36新增），总34capture/102replay。性能44行仍在跑，尚不签发最终通过。

独立CPU/只读最终审核命令 `/tmp/qwen3vl-pr1069-signed-zero-20261109/independent_audit.py` SHA256 `bcdba2ff239a5e2ea86e406962cba35fb6e639a6c7dd4d284aebb628ab3f6adc`，待唯一控制器完整终态后只执行一次，独立重算44行/5轮/双方法、258case XML、全部graph来源、source当前identity与克隆回退停止情况。

唯一控制器已完成44/44行、全88比较，最大耗时回退0.54661%、最大B/R漂移1.33276%，源保留passed、私有clone已回退停止。独立审核归档/执行命令 `upload_audit.py` SHA256 `a35a581f1ac636ddc62ea946824da664750b813bccec74a98e8593d826e24508`，仅CPU/只读现状，无GPU/模型请求。

## 发布前独立审核通过

258单测/124新增、6组旧错误GPU复现、48普通输入位级对照、共34capture/102变化输入replay及44行×2计时×5B/C/R轮审核passed。所有轮次保留；普通耗时变化-1.147%..+0.455%，graph-1.454%..+0.547%；最大B/R漂移1.333%，均满足预冻结5%回退/漂移上限。原模型源服务/code/config保留、私有clone回退并停止。

唯一准备发布：parent039f03ed，2file-only delta，tree `cef856dfc20ee7c545c1b87b81cad89132b12bac`，测试字节与payload一致；非force expectedSHA039f03ed ref更新，随后更新PR说明；不发review回复、不resolve线程、不合并PR、不部署source。tree_payload.json SHA256 `0fbd9543a6f41471194545c5fee200ae929128334248ea1ef0f53efbc93bbf67`。

独立最终审核回执SHA256 `43dd83bf5ebaaa3b550fc2af1bf669eed634ae61cdbdfa81904f4f312d1cfc6a`。

修复提交已非force推送 b1287f170190078481c71f9c2836067846892499，GitHub取回2文件均与测试字节完全一致。PR说明草稿SHA256 97210cab334c488ecf0883fd44adcfad553aa49a88d7fdf7dde4bc98ba527af2，明确本轮258测试/44行回归与历史guard性能分开，不改变旧未达标参考项记录。

独立审核已通过，按用户此前仅保留qwen3vl的清理偏好，删除本任务新建且已回退/停止的自有私有测试clone；先后source完整核验，精确clone ID/Image guard，只docker rm自身、不删volume/镜像/挂载目录，不再操作其他容器。
- `remove_verified_clone.py`: `db95774c6cfb5464bfe6038e077e0d164922fa0c66fb95f1445b9e225ce01562`
- `upload_cleanup.py`: `fda899585f3a5250b87e071eeb39b8416d64ed7aff9dc1dd1ad40725b88fab3a`

## 最终交付

[PR1069](https://github.com/flagos-ai/FlagGems-vllm/pull/1069) 更新到 [`b1287f17`](https://github.com/flagos-ai/FlagGems-vllm/commit/b1287f170190078481c71f9c2836067846892499)，Open/ready/mergeable。相对039f03ed仅2文件变化；server tree `cef856dfc20ee7c545c1b87b81cad89132b12bac` 与本地测试树完全一致，发布后取回2文件逐字相同。代码只新增filter key及两函数调用替换/文档；20个原函数还原helper调用名后AST相同，排序、前缀kernel/guard、host dispatch/分配、API和参考均不改。

MetaX C550/GPU6：旧错误6组实际复现；258设备单测通过（含124新增）。单测26capture/78变化输入replay，额外8capture/24replay，总34capture/102replay，48普通输入对原PR位级一致；输入位模式、k/p与RNG保持。precommit及54CI工具测试/16subtests通过。

44行×2计时×5固定B/C/R全保留并可比，普通耗时变化-1.147%..+0.455%，graph-1.454%..+0.547%，最大B/R漂移1.333%。这只是修复的算子回归，无E2E提升/正式模型gate。旧B64/V4096低于0.9Torch目标的继承问题仍在原PR说明中保留，没有称passed或叠加优化。

源qwen3vl/opt18/8030、全部推理源码/配置/默认采样/cache/PID保持，HTTP200；本次没有同步这份新修复到源容器。已按用户清理偏好删除本任务自己的已核验临时clone；原始命令、完整轮次、counterexample、XML与回执远端保留，快照保留。没有发review回复、resolve线程或mergePR。

新CI：rule-check735与basic-ci2225已排队，license/cla success，尚不称CI全部通过。旧039的basic-ci2165为cancelled而非success，历史记录不覆盖。

## 全部归一化性能数据

完整API含clone/workspaces，ordinary/graph是上游Benchmark对应方法。BF16-grid为FP32里可由BF16精确表示的数据；both=k20/p.8，p=p-only.8。负百分比为耗时下降，非E2E吞吐。

| 输入 | M | V | 模式 | ordinary B ms | ordinary C ms | ordinary变化 | graph变化 |
|---|---:|---:|---|---:|---:|---:|---:|
| BF16-grid | 1 | 4096 | both | 0.118528 | 0.118784 | +0.216% | +0.358% |
| BF16-grid | 1 | 4096 | p | 0.114944 | 0.115456 | +0.445% | +0.545% |
| BF16-grid | 1 | 151936 | both | 0.276480 | 0.276480 | +0.000% | +0.032% |
| BF16-grid | 1 | 151936 | p | 0.269568 | 0.270080 | +0.190% | -0.156% |
| BF16-grid | 8 | 151936 | both | 0.595456 | 0.590080 | -0.903% | -0.837% |
| BF16-grid | 8 | 151936 | p | 0.534400 | 0.536832 | +0.455% | +0.371% |
| BF16-grid | 8 | 262144 | both | 0.584448 | 0.584704 | +0.044% | -0.138% |
| BF16-grid | 8 | 262144 | p | 0.548608 | 0.548992 | +0.070% | -1.454% |
| BF16-grid | 31 | 131072 | both | 0.817152 | 0.817408 | +0.031% | +0.132% |
| BF16-grid | 31 | 131072 | p | 0.755584 | 0.756992 | +0.186% | +0.187% |
| BF16-grid | 32 | 131071 | both | 0.885504 | 0.886528 | +0.116% | +0.073% |
| BF16-grid | 32 | 131071 | p | 0.818176 | 0.818432 | +0.031% | -0.406% |
| BF16-grid | 32 | 131072 | both | 0.819840 | 0.819968 | +0.016% | -0.027% |
| BF16-grid | 32 | 131072 | p | 0.749056 | 0.750848 | +0.239% | +0.194% |
| BF16-grid | 32 | 151936 | both | 0.939392 | 0.943104 | +0.395% | +0.197% |
| BF16-grid | 32 | 151936 | p | 0.867840 | 0.869376 | +0.177% | -0.203% |
| BF16-grid | 64 | 4096 | both | 0.569344 | 0.562816 | -1.147% | -0.057% |
| BF16-grid | 64 | 4096 | p | 0.535296 | 0.530432 | -0.909% | +0.167% |
| BF16-grid | 64 | 151936 | both | 1.699072 | 1.700864 | +0.105% | +0.080% |
| BF16-grid | 64 | 151936 | p | 1.551872 | 1.557120 | +0.338% | +0.072% |
| BF16-grid | 64 | 262144 | both | 2.798848 | 2.800768 | +0.069% | +0.105% |
| BF16-grid | 64 | 262144 | p | 2.557696 | 2.561408 | +0.145% | +0.092% |
| FP32 | 1 | 4096 | both | 0.119552 | 0.119552 | +0.000% | +0.359% |
| FP32 | 1 | 4096 | p | 0.114944 | 0.115456 | +0.445% | +0.547% |
| FP32 | 1 | 151936 | both | 0.276992 | 0.277248 | +0.092% | -0.020% |
| FP32 | 1 | 151936 | p | 0.270080 | 0.270848 | +0.284% | -0.210% |
| FP32 | 8 | 151936 | both | 1.173760 | 1.174272 | +0.044% | +0.174% |
| FP32 | 8 | 151936 | p | 1.153536 | 1.152768 | -0.067% | +0.293% |
| FP32 | 8 | 262144 | both | 1.803264 | 1.804032 | +0.043% | +0.002% |
| FP32 | 8 | 262144 | p | 1.767168 | 1.768192 | +0.058% | +0.066% |
| FP32 | 31 | 131072 | both | 3.113728 | 3.114752 | +0.033% | +0.065% |
| FP32 | 31 | 131072 | p | 3.045376 | 3.046912 | +0.050% | +0.101% |
| FP32 | 32 | 131071 | both | 4.754816 | 4.756352 | +0.032% | +0.019% |
| FP32 | 32 | 131071 | p | 4.688256 | 4.689408 | +0.025% | -0.007% |
| FP32 | 32 | 131072 | both | 2.953984 | 2.956544 | +0.087% | +0.024% |
| FP32 | 32 | 131072 | p | 2.884352 | 2.885120 | +0.027% | -0.149% |
| FP32 | 32 | 151936 | both | 3.402496 | 3.405312 | +0.083% | +0.018% |
| FP32 | 32 | 151936 | p | 3.328768 | 3.329664 | +0.027% | +0.028% |
| FP32 | 64 | 4096 | both | 0.507136 | 0.506880 | -0.050% | +0.055% |
| FP32 | 64 | 4096 | p | 0.496896 | 0.496640 | -0.052% | -0.001% |
| FP32 | 64 | 151936 | both | 6.459392 | 6.462464 | +0.048% | -0.067% |
| FP32 | 64 | 151936 | p | 6.314752 | 6.319616 | +0.077% | +0.025% |
| FP32 | 64 | 262144 | both | 10.816768 | 10.824320 | +0.070% | +0.071% |
| FP32 | 64 | 262144 | p | 10.580736 | 10.590464 | +0.092% | +0.129% |

## 最终回执

- 独立最终审核：`43dd83bf5ebaaa3b550fc2af1bf669eed634ae61cdbdfa81904f4f312d1cfc6a`
- `results/completed.json`: `07cfd12c0e70e229abbbbaa7df986e6cc3875633de259aa0f79af2f5845a4d84`
- `results/benchmark.json`: `7059ef7573ce67141856d5fe64a2a0c2ee70bc33c69d9ee52a3787e61325ccf9`
- `results/component-correctness.json`: `e64bb65b1ddb225d74de96f194f08aa79fc7ff7c5dd23ba7305ddfafe9b41d71`
- `results/baseline-reproducer.json`: `c91bc56790502b9d5c94ec9ba7358e576790ce7af1054ca6f95a0d03e038b58c`
- `results/pytest.xml`: `baa34b850c5acf29748a1e11e6eb97dfb52b0af335ca1bab5464bee2fb593d52`
- `results/source-preserved.json`: `5b218ecce8be6107c4bc0d0c01129090d546d8029af9b3f7ee52aab3028d6d5b`
- `results/runtime-mapping.json`: `bdcdae11a5aac9405165e4fe6972212aa81ccdcf730d8672e7be56c086e7b9d1`
- `manifests/upstream-benchmark.json`: `1dc8bcb27fabac9d9f96f5cec3b500ec544b2682937d57f0ac844ed517a5e758`

知识增量：位级可逆排序key与浮点过滤等价类应分开；signed-zero canonicalization只能用于比较，不应破坏排序逆变换或保留值符号。当前GPU组件证据不证明任何正式GPQA根因或分数改善。

最终发布元数据、静态审核和PR说明归档命令 `archive_publication.py` SHA256 `90a4a384dea4b427a3700fd2916cea0d092263b72eb7090400a7f07a6d28d7c5`；仅写已授权case的新回执文件，不发模型请求、不再做容器变更。
