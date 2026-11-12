# 指定镜像 clone 复现与两个算子问题反馈

2026-11-11 用户要求：在前一轮指定镜像的独立容器中复现 clone，确认后更新 Excel；对 topk_softmax 与 clone 提交/登记 issue。用户已纠正“3个”为“2个”。继续使用 mx-59/qwen36-topk-softmax-mx59-20261111-001、镜像tag202611091810/不可变ID sha256:a4734ce7758490551c7cb7fed1794df8ccd9417a7356ac351d40bb128930fe65，无挂载、network none，不加载模型、不改源/服务/其他容器。

本轮分类 diagnostic。先只读核验容器/镜像/clone实际导入源码与启用API，再在独立新解释器内对照CPU RNG UInt8张量的torch.clone及TorchInductor preserve_rng_state：原生/仅启用clone/排除clone，保留失败原生退出码、完整traceback和实际命中来源。相同环境重新启用clone确认故障可重现；仅CPU兼容故障不能写成GPU clone数值错误。必要时对GPU4做有限组件护栏，不运行模型/全量精度，不修复源码。

复用前轮用户批准远端路径 `/public-flash/jinghao/qwen3.6-35B/20261104-qwen36-main-config-compat-mx59-001/operator/topk-softmax-image-20261111-001`，本轮新增文件均clone前缀/独立输出且执行前归档SHA，不覆盖或重放前轮数值/性能测试。

GitHub检索：已存在FlagGems #8566（NVIDIA H800/不同commit的CPU clone guard缺失），若确认同一机制则在该单补充MetaX指定镜像证据并登记其链接，不另建同根因重复单。topk_softmax前轮确认M8192/E256/K8 FP32/renormTrue的组件性能差异，数值通过；新建性能问题单，明确不是数值故障或E2E退化原因证明。公开内容限已核验版本/镜像/最小代码/必要栈/测量方法，远端私有日志与模型数据不上传。

方法：沿用本地inference-accuracy-diagnosis的最小复现/单变量命中证据；Excel按Spreadsheets编辑工作流保留原模板结构、其他内容和格式，检查文本/issue链接并渲染核验。状态见末尾最终发布记录。

实际审阅API：use_gems(include=[clone])优先于exclude，故不同时传两者。冻结8个独立解释器用例：native clone/preserve、only_clone clone/preserve、exclude_clone clone/preserve、重新only_clone clone/preserve。仅clone开启预期ValueError退出1，其余预期0；不是吃掉异常或在同进程fallback重试。审阅导入torch._dynamo后cuda_initialized=True，因此不声称本轮CPU命令完全未建立设备上下文，但复现输入严格CPU UInt8，不执行模型。

## 指定镜像真实结果

clone代码真实SHA256 `1255fcbf5b32a9cb6a10269b64e431fe38a34415e97097e9e0d6d37bb8d034aa`；8个进程记录一致，未修改库/注册代码。输入CPU UInt8[5056]，来源真实torch.random.get_rng_state。两个action均确认同一失败机制：

| action | native | only_clone第一次 | exclude_clone | only_clone重新启用 |
|---|---|---|---|---|
| torch.clone(CPU RNG状态) | exit0 | exit1 ValueError | exit0 | exit1 ValueError |
| TorchInductor preserve_rng_state上下文 | exit0 | exit1 ValueError | exit0 | exit1 ValueError |

异常真实命中flag_gems/ops/clone.py:115/42/77/62，经_clone_impl→_launch_copy→torch_device_fn.device(cpu)，在Torch CUDA guard处抛 `Expected a cuda device, but got: cpu`，未发射该输入的复制kernel。原生与排除clone保持CPU设备/dtype/字节值，直接clone另验证不共享data_ptr。8个原生回执保留预期exit1，没有改写成退出0或在同进程fallback后称通过。

分类 execution-mode/device-dispatch compatibility，CPU最小机制确认；当前未修源码，未执行GPU clone覆盖或模型graph/精度，不外推为GPU数值问题/显存问题。仅项目最小组件诊断，不签model gate。

原始目录：远端ROOT/clone-reproduction-001（每项独立command/log/native与results/<label>/result.json）。`verification.json` SHA256 **920c75118375b10c581c57ead09f75d170fe8b9242a9397e0ba84b31c1772c77**。本地独立复核8项退出码、输入shape/device/dtype、错误路径及一致源码SHA通过。

命令（均先归档且执行一次）：
- `commands/clone-audit-001.py` SHA256 `36e8ab6ebc8def767030475675b82a83141c0d7311ffd4a8bd22c2dab3cbd099`
- `commands/run-clone-audit-001.py` SHA256 `3700920e7e3190b79ebfc0fefe1afd5441af96ff8d1d4043497027e00df574fc`
- `commands/clone-worker-001.py` SHA256 `43be8f73aaa1399848188646a36816c2d2b5de3d8155d1cf9acb07da42dec7e1`
- `commands/run-clone-reproduction-001.py` SHA256 `6d9c53b161e6f8193d898d9be88260114e802b2e944cf81a9540a3fd68ca1dc5`

## Excel 与公开问题单状态

Excel已更新指定镜像当前复现的真实结果、最小脚本、clone源码/验证SHA，移除旧“当前镜像未复现”的描述。topk数值/大batch性能事实保持；镜像ID明确标为ID，不再混称registry manifest digest。clone的GitHub列填现有同机制 https://github.com/flagos-ai/FlagGems/issues/8566 ，L列明确本次证据尚未公开补充；topk新单尚未发布，没有虚构URL。

创建topk公开issue的首次工具调用被自动审批拒绝：理由为现有授权未明确覆盖内部镜像地址、环境/组件版本及性能数据公开披露；该调用没有创建issue，未通过其他工具绕过。已准备移除内部镜像/机器/用户路径的两份公开草稿（必要软件版本/hardware型号/微测结果/精简栈保留），异步请求用户明确披露授权；后续发布或留存依用户回复。此前状态（2026-11-11）：clone复现与Excel完成，外部发布等待披露授权。

## 最终发布记录（2026-11-12）

用户明确回复“同意”，授权按已审阅精简稿公开MetaX C550型号、必要开源组件版本/commit、最小复现、精简栈及组件微测结果。未公开内部镜像地址、Host、用户路径、完整日志或模型数据。该授权解决此前自动审批阻塞；没有重复运行GPU或CPU复现、没有变更推理栈。

- 新建性能Issue [FlagGems #8959](https://github.com/flagos-ai/FlagGems/issues/8959)，正文与批准的topk公开草稿逐字回读一致（草稿SHA256 `bf8792d2a26c84836e23ccd85240d8df5e697e2c982b19407b234ac506c06e4b`）。明确M8192/E256/K8下耗时高约29.4%，小batch较快，并保留数值通过与非E2E结论的边界。
- 向现有CPU clone同根因Issue [#8566补充MetaX复现](https://github.com/flagos-ai/FlagGems/issues/8566#issuecomment-6811533403)，comment ID `6811533403`。正文与批准草稿回读一致（SHA256 `83683fc5f1b7f39d8d9cc2fe9cae783510916bad4dc082e359fcb34a51022580`），没有另建重复clone问题单。
- Excel仅更新K2/K3/L2/L3：两个URL、实际发布时间与状态；指定镜像及原始组件证据仍保留于本地Excel。保存后独立检查四单元格与其他值均正确，视图渲染检查通过。
- 最终Excel SHA256 `2e0e9c6d5aec591363c79cd622759de5f00ba19bf48e6c29837443dacef7d383`。

最终状态：组件复现/问题反馈/Excel回填完成；未实现或部署算子修复，未签新模型精度或性能gate。公开回执和表格校验的工作文件在本机 `/private/tmp/qwen36-issues-publication-20261112-001/`；持久追踪以两个GitHub链接和本记录为准。

2026-11-12 按用户反馈修正导入格式：GitHub Issue列K3从评论锚点改为标准Issue URL https://github.com/flagos-ai/FlagGems/issues/8566，评论链接移至L3备注。K2/K3均通过https://github.com/org/repo/issues/数字格式校验，仅这两处关联单元格变更；Excel最新SHA256 0f8fd39aaed7ab9e1d8f67772d79ab45cb3e94c60ec9ac552120d3a166261b32。
