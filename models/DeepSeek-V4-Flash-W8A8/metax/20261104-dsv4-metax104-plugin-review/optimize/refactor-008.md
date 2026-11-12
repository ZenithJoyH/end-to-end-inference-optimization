# refactor-008 — MQA/MLA 公开接口进一步收敛

用户请求：继续尝试收敛不规范接口，复用主线公开契约。当前服务保持运行；本轮只创建隔离候选和CPU验证，不安装、不发GPU/模型请求、不提交推送。

基线：mx-104 / deepseekV4-flash-refactor-20261104，FGV main025f3181 + ref006/op004/ref007；当前已验证ref007数值/dispatch/graph123项与ON/OFF模型各22项通过，但不等于NV实测。只读现场HEAD025f3181、FGV37暂存路径、health200已重新核验。

候选：D=/public-flash/jinghao/deepseekV4/20261104-dsv4-metax104-plugin-review/refactor01；新api-align02/candidate独立副本。mqa_logits统一BF16共享KV与已gathered量化KV两种明确布局；paged_mqa_logits复用已有main入口，MetaX BF16 Q/量化KV通过明确类型分支保持旧预MMA舍入；sparse_prefill_local合并入flash_mla_sparse_fwd的2D索引+caller-buffer扩展。旧helper转私有，Plugin保留CachedOp契约以薄adapter调用公开API，无数值kernel迁入Plugin。MLA workspace/真实头数/输出参数保留，不能假称NV支持全部MetaX扩展。

review-refactor-008：目标为维护性而非性能。Prefill/Decode/Mixed原有性能证据不能迁移到本候选；没有累计性能收益结论。优先删除冗余公开名，次选明确新mqa_logits，拒绝把BF16强塞fp8_fp4接口或隐藏workspace；数学改写/冷启动/性能任务deferred。首证伪为CPU真实wrapper AST转发、out别名、prewrite拒绝、fallback不重试；随后需要GPU数值/真实dispatch/graph及模型最小回归。本轮不暂停运行服务。

规范：operator A1-A4/B1-B3/C1-C7/D1-D3/E1-E4/F3-F4、Plugin A1-A4/B1-B4/C1/D3/F1-F3。新增数值实现为0；保持op004 gather SHA、全部JIT AST以及common/NV源码字节；公开导出/yaml/测试marker同步。适用GPU门禁未执行时交付状态pending，不凭CPU通过晋级。

回退：未安装候选，原已安装源码和Git暂存/工作区快照完整不变；无需服务回退。远端任何新脚本执行前记录路径/SHA，仅新api-align02写入，不覆盖旧api-align01。

执行前保存：`D/commands/ref008-stage01.py` SHA `e48a2f3effca70dc17931b6e0aeb6931e6ea38442a078c515fce548faed673de`；只CPU复制当前tracked/untracked明确文件至新候选，前后原安装文件/索引/同服务精确身份核验。

stage01在Plugin既有`.github/copilot-instructions.md`符号链接守卫停止，仅部分复制、未改安装源。stage02验证链接实际指向同库内部并保持链接形态，对已有候选文件逐SHA复核后续传；不放宽到外部链接。`D/commands/ref008-stage02.py` SHA `570a40cf74f697c1ff3ee273eef49b6f146681b844b7e3b31fdc981d941f8950`。

执行前`D/commands/ref008-apply01.py` SHA `579081c9bfc10457b848472cb1e6d07efc99dadf9f7c5717e7adb411e58b4797`；`api-align02/updates01.json` SHA `0bd8cf3204dc3cac1a47ba910c01e6141bc9818fddc7e8fca5dc5424fe21dad5`。仅候选更改，保留原GPU参考/断言迁移调用。

执行前`D/commands/ref008-final01.py` SHA `e0e5b8d37fa1e51e65cb311e6778fb8d7ab82541537d42ff97acc0b1a5671e29`。
执行前`api-align02/finish-updates01.json` SHA `4178f9f11e6e937b0a604764a087ecb7abd5acf24979b6305e0a4a4ada6ad246`。
独立review未发现数学/分派阻断，已修正文档旧API清单；新增导出/配置/主线签名静态测试。最终CPU复验及全部JIT/common/NV/原服务源索引守卫通过后冻结patch/manifest，不安装。

final01全部52项CPU测试通过，但JIT审计误包含Plugin旧ignored build/lib产物，候选按有效tracked/untracked快照没有该目录，集合守卫停止。保留CPU结果和原脚本，不重复GPU/模型请求；final02将两侧比较范围统一到明确安装源码manifest，新增文件仍全检，不忽略生产文件。执行前`D/commands/ref008-final02.py` SHA `dc9fd7357b23cf17d328715aa91ea52fbaf2828914ce0b65518d36dca1abc17a`。

## 最终隔离候选结果

4个临时FGV公开名全部删除，保留1个新语义族并复用两个既有公开入口：

| 原公开名 | 收敛入口 | 契约与边界 |
|---|---|---|
| batched_mqa_logits | mqa_logits | 显式gathered (FP8[M,N,128],FP32[M,N])；starts=None、ends有效范围，保持原预MMA BF16舍入/out别名 |
| mqa_logits_into | mqa_logits | BF16共享KV、start/end、caller-out/padding、row_shard；Plugin兼容桥仍返回None |
| paged_indexer_mqa_logits_match | paged_mqa_logits | main025已有公共入口，补其yaml元数据；FP8tuple转发原common，BF16查询/packedcache扩展保持原舍入并显式clean_logits=True |
| sparse_prefill_local | flash_mla_sparse_fwd | 2Dindices+完整out/statistics扩展进入原私有helper；Plugin压缩单KV头维度，library恢复原caller形状；普通3D路径不变 |

`mqa_logits`为新的公共语义族，并非声称NV已有同名等价实现；`paged_mqa_logits`补yaml条目不等于新增数值算子。4个旧名称仍允许作为Plugin内部CachedOp兼容契约（薄桥），但FGV公开导出/配置/required-API不再使用。MLA workspace、real_num_heads及输出缓冲扩展仍保留；没有将它们隐藏到全局cache/scheduler对象里。NV未实现/未实测这些扩展。

52项CPU契约测试全部通过：既有FGV10+Plugin8、新MQA14/MLA8/公开表面4/Plugin桥8。AST隔离执行真实host wrapper并验证转发、输出别名、边界拒绝、不重试、常规分支以及签名/导出/yaml；不导入torch/FGV/vLLM，无GPU/模型请求。变更Python15项格式检查通过（FGV Black24.8/isort5.12/flake8 7.1、Plugin Ruff0.14），另新公开表面测试同样格式/flake8通过。原有GPU测试/benchmark只迁移公开调用，参考/数值断言保留，未执行。

按本轮有效tracked+untracked源码manifest覆盖的1460个JIT定义AST完全不变；171个common/NV生产文件字节相同，4个旧host helper体仅改私有名，op004 gather仍SHA5d12074cb3d0608f4d38ad5d14c5ee2e8325b729ed10d06629ad2832e8b9ab19。1460为本轮递归AST口径，不能与此前不同扫描口径1410推断新增kernel。

安装源FGV1189/Plugin639文件与Git index/worktree diff SHA不变，同服务PID/startticks/argv不变、health200。无安装、停重启、JIT清理、代码提交或推送。当前运行版本仍ref007；候选为api-align02，不引用旧gate证明新源码通过。GPU数值、真实dispatch、graph、模型最小回归与非MetaXCI仍pending，未测性能、不宣称E2E收益。

最终产物`D/api-align02/final01/`包含两库patch、完整candidate-manifest及独立源码包/result；原apply01、CPU日志、stage守卫失败保留。final01的审计范围错误仅涉及ignored build/lib副本，final02只CPU修正并复用未改源码的52项成功日志；没有盲目重发模型请求。初次定向差异读取早于apply写入得空集，已在完成后重新读取17差异文件，空集未作为验证证据。首次final脚本传输路径拼写错误在写入前失败，正确路径唯一执行。

```json
{
  "changed_files": {
    "flaggems-vllm": [
      "benchmark/test_metax_sparse_adapters.py",
      "conf/operators.yaml",
      "docs/metax_sparse_ops.md",
      "src/flaggems_vllm/runtime/backend/_metax/ops/__init__.py",
      "src/flaggems_vllm/runtime/backend/_metax/ops/mqa_logits.py",
      "src/flaggems_vllm/runtime/backend/_metax/ops/paged_mqa_logits.py",
      "src/flaggems_vllm/runtime/backend/_metax/ops/sparse_indexer_decode.py",
      "src/flaggems_vllm/runtime/backend/_metax/ops/sparse_indexer_prefill.py",
      "src/flaggems_vllm/runtime/backend/_metax/ops/sparse_mla_prefill.py",
      "tests/test_metax_api_surface_cpu.py",
      "tests/test_metax_mla_interface_cpu.py",
      "tests/test_metax_mqa_api_cpu.py",
      "tests/test_metax_public_contract.py",
      "tests/test_metax_sparse_adapters.py"
    ],
    "plugin": [
      "tests/unit_tests/test_metax_mqa_mla_bridge_cpu.py",
      "vllm_fl/configs/deepseek_v4_metax.py",
      "vllm_fl/dispatch/backends/vendor/metax/impl/dsv4/mqa_mla.py",
      "vllm_fl/dispatch/backends/vendor/metax/register_ops.py"
    ]
  },
  "artifacts": {
    "candidate-source.tar.gz": "9e593464a241c92525517fdebafe3b82cc2e7c2ce4099baf012d78edb2743cad",
    "candidate-manifest.json": "98e2328d6578dd2b567c49d557e95ddfc881128eccda2636ec79e6ee9b1f24f6",
    "plugin.patch": "0dae4986ea4d9c8fcdc02b773bc16c9ee12a729a90339e97b749cadf680640a1",
    "flaggems-vllm.patch": "a4f798f398326166c54a193e222c6297f1160ff52bad332e5698752a4621067b"
  }
}
```

## 用户授权直接应用安装源码

最新用户明确“直接都应用到容器中安装的源码”，覆盖此前仅候选不安装范围。按该指令先应用18路径，不等待GPU门禁；状态必须标CPU-only/GPU数值dispatchgraph待验证，不能宣称已验证交付。服务不重启、不发模型/GPU请求；保存18路径/模式及两库Git index/patch到api-align02/delivery01/backup，完整原SHA和candidate SHA守卫；FGV沿用全暂存约定仅stage本轮路径，Plugin原index保持。只读验证editable路径和容器私有源码，原脚本/同实例/argv/health不变。失败精确回退本次已写路径，不清JIT或覆盖并发编辑。

执行前`D/commands/ref008-install01.py` SHA `6a2e63a1ffd9e7e9e3bd973cf9f0347881c6d2a79ea2deceae5fb42d21488212`。

安装前18001 health连接失败，尚未执行任何安装/进程操作；按当前实际状态核验，不声称仍health200。install01仅保存本地未执行，install02允许记录已离线服务并保持该状态、不自动启动，同时补FGV index并发SHA回退守卫。执行前`D/commands/ref008-install02.py` SHA `e599c5d9627472e853f83d8a85152a95539e9a9885e52befc9617d9a0acc1e83`。

## 已按用户指令应用到实际安装源码

已完成18路径应用：FGV14、Plugin4。实际editable安装目录确认是`/opt/dsv4-sources/FlagGems-vllm-main-reuse-20261105`和`/opt/vllm-plugin-fl`，二者不位于容器的/public-flash或/data挂载中。应用后完整FGV1194/Plugin641文件与冻结候选manifest逐SHA一致；52项CPU契约测试在实际安装目录再次通过，无GPU/生产库导入。

FGV本轮路径已沿用历史全暂存约定同步，42项staged，未暂存/未跟踪0；Plugin原index未改，仅应用本轮文件，既有改动保持。HEAD不变、无commit/push，启动脚本SHA `da4c5138e58b262fe6efc163e301e7f7250b00f349624d024e970911bda82d98`不变。没有pip安装或依赖升级、没有JIT/cache清理。

本轮安装前已实际无18001 API进程、health不可达；安装后仍相同状态。没有自动启动、停止、重启模型或容器，不把该既有离线状态归因于此次安装，也不宣称新版本runtime已验证生效。源码已在安装位置，下次启动会读取；GPU数值、真实dispatch、graph及模型最小回归仍pending。用户直接应用指令覆盖此前“候选不安装”的范围，未覆盖任何验证结论。

回退备份：`D/api-align02/delivery01/backup/`保存18路径原文件/模式、两个Git index与差异patch。安装脚本具有并发源码/index SHA回退守卫。结果：`D/api-align02/delivery01/result.json` SHA `8856ff2a271b496a13920a1ef3b9bcda08c50e1b5874efab62476e052d71c85f`；6份已安装CPU测试日志在同目录。install01未执行；install02唯一成功执行。旧候选及CPU-only结果保留，不重写历史为GPU通过。
