# fw-014-minimax-adaptation-contract-refinement 小范围适配收敛

- 状态：retained，minimal-regression 通过；用户明确要求实施；不是性能优化，不新建容器。2026-10-17 15:24 +08:00 核验。

后续正式精度：当前无黑名单/无新增测试的组合由[accformal-006](accformal-006-ppu13-gpqa-c64-60k.md)按198题/C64/60K/阈值88%完成，strict-match 179/198=90.40%，gate复验通过，14条60K截断单独记录；这是当前组合证据，不覆盖本文件原始回归回执或证明本点独立贡献。

## 优化方向与瓶颈依据

620892ab 的 sigmoid+bias 单组 grouped-topk 路径丢失 indices_type；公共 router 未约束 backend 支持范围。general plugin 过早安装预处理 patch，可能在 worker 设备绑定前导入 accelerator kernels。

## 优化内容与适用边界

仅修改 Plugin：保留原健康 checkout，在容器私有 `/workspace/vllm-plugin-FL.support-minimaxM3-refine001-20261017` 建立真实副本，editable 实际导入已核验。基于620892ab，改动3个源码文件、新增2个测试文件；继承既有卷积黑名单，不改 kernel、模型权重、vLLM、FlagGems 或 FlagGems-vllm。

- `FusedTopKBiasRouterFL` 的 sigmoid 单组复用仅接受 FP32 logits/bias、匹配行数/设备、连续 expert 列及1D连续 bias、expert≥2、1≤top-k≤min(32,E)，indices_type 为 None/int32/int64。保留调用方要求的索引 dtype；空 token 不启动零网格；scale 仍只应用一次。
- 软最大值、低精度/不支持 layout/shape、AITER 和 hash 等不进入新分支，回原 `fused_topk_bias`；hash 参数保留。既有路径在目标平台是否支持该输入另论，不承诺新增 fallback 能力；选中 backend 后的执行错误不吞掉。
- 预处理 patch 从 general `register_model` 移至既有 `WorkerFL.load_model`，位于设备初始化之后、实际模型加载之前，与既有 moe_sum patch 相邻；保留幂等、native-op 保留、原函数回退信息及惰性 backend 导入。不重构 qknorm bridge/native capability 检查，不新增 dispatch 框架。

## 正确性与路径命中

使用 inference-accuracy-evaluation/minimal-regression。CPU 72项通过；真实 PPU 121项通过，包含 M=0/1/8/32/65、E=2/128/257、k=1/4/32、None/int32/int64、renormalize 与缩放、非对齐/行 stride，以及直接 CUDAGraph 两次 replay。实际命中 `grouped_topk/default.flagos`，权重与 Torch reference 比较 rtol2e-5/atol1e-6，索引精确比较。

同启动契约新服务 `fad201d7b6ec:8024:23178:493728712`：TP16 BF16，100000上下文、max_num_seqs64、8192批token、禁用prefix、FULL_AND_PIECEWISE sizes1/2/4/8/16/32/64。16rank分别完成FULL/PIECEWISE capture（每模式7/7），原生日志FULL180次、PIECEWISE0次、NONE4次。完成两次C1及一轮C8，共10/10最终答案匹配（去除mm:think，水化学式按预冻结等价写法归一），输入185–7241 token、输出22–115 token。HTTP均200，finish_reason均stop；错误/超时/空输出/截断/乱码/异常重复均0，服务ERROR/Traceback0。保留服务运行。

生命周期证据边界：顺序、重复调用和原函数保留由CPU/mock/AST覆盖；独立新进程核验新路径、general中无安装、worker hook在模型加载前，native缺失时首次安装True、再次False。首次辅助审计额外要求16rank INFO安装日志，得到incomplete；独立探针确认worker logger有效级别30、无handler，INFO默认不可见。原回执保留，补充v2审计，不改源码/服务/请求，也不把独立进程结果冒充运行中16rank对象内省。`accdiag-007-refine001-lifecycle-log-observability` 分类为观察器假设无效，不是模型输出失败；无正式分数/gate。

| 验证范围 | 证据与结果 | 未测/边界 |
|---|---|---|
| 路由支持条件内 | hardware，PPU121项 executed_passed，default.flagos | 非目标硬件交对应平台CI；不能宣称跨平台通过 |
| 不支持条件、hash/AITER、错误传播 | mock/static，CPU72项 executed_passed | 不等于原路径在PPU所有输入都能执行 |
| 幂等、native保持、worker安装顺序 | mock/static + 独立实际环境probe executed_passed | 未观察运行中各rank安装事件 |
| 完整模型graph与C1/C8 | hardware，10请求及双模式capture executed_passed | PIECEWISE请求replay、真实多模态、100K边界未测 |

Python语法、pytest、`git diff --check`通过；ruff在现有环境不可用，未安装新依赖。`pr_readiness=experimental`；完整GPQA、正式性能和其他平台均not_run。

## 性能效果

未测，不声明收益。

## 决定、风险与回退

候选先独立测试后切换editable，保留候选运行。修改前检查旧8024服务running/waiting均0，只停止精确PID/start-ticks及其匹配子进程；未触碰其他服务。前后manifest确认candidate、两个算子库、vLLM、模型配置/权重清单与启动契约在回归期间不漂移。

原健康 `/workspace/vllm-plugin-FL.support-minimaxM3-20261017` 完整保留；源码快照、候选补丁和校验值在远端。回退在PPU-13执行以下已保存脚本（会精确停止候选、重装原健康checkout并用同参数重启；执行后仍需health和smoke核验）：

```bash
bash /mnt/nfs/users/jinghao/minimaxM3/20261017-minimax-m3-ppu13-plugin-support/refine-001/commands/rollback.sh
```

本轮未执行回退，不宣称回退后服务已经复验；不提交/推送代码或创建PR。

## 外部证据

### 2026-10-18 用户要求 amend 原提交

用户明确授权将当前三文件源码收敛合入`620892ab8c083b137c24db6cfcdc32fe38cca963`，不要增加后续commit。只读确认远端`ZenithJoyH/vllm-plugin-FL`的`support-minimaxM3`分支头仍为该SHA，运行中私有checkout也基于该SHA，仅三文件变化、无新增测试/thead.yaml差异。拟在本地独立临时clone中保留原作者及提交说明执行amend，再以精确旧SHA的force-with-lease更新此分支；amend必然改变SHA，不改动运行中容器源码/HEAD/服务，不创建PR。原提交父节点`ca6fb176ba704e0022736fd143539cef017032ee`须保持不变。

准备目录`/private/tmp/minimax-m3-amend-20261018.x9xr5k/plugin`；准备diff与容器diff的SHA256均为`468e5432772c16c36279734978e7dbe4a132768742fb239e6bd99f15723b4507`（86插入/21删除）。原代码已通过前述CPU72/PPU121及当前组合全量GPQA179/198；本次仅改写提交身份，不声称新执行了模型测试。执行前计划：本地bundle备份原分支 → 精确stage三文件 → `git commit --amend --no-edit` → 核验父节点/作者/说明/源码树/提交数 → `git push --force-with-lease=refs/heads/support-minimaxM3:620892ab8c083b137c24db6cfcdc32fe38cca963 origin HEAD:refs/heads/support-minimaxM3` → 只读复核远端SHA。若远端已推进，lease拒绝即停止，不覆盖新工作。待写入最终SHA与推送回执。

执行结果：上述流程完成，远端`support-minimaxM3`已从620892ab替换为[43e0980de214b75fd1a813e7e1f8cfcbb557edbc](https://github.com/ZenithJoyH/vllm-plugin-FL/commit/43e0980de214b75fd1a813e7e1f8cfcbb557edbc)。GitHub API与ls-remote复核一致，parent仍为ca6fb176，tree为`27d9cc51d4b357d7a34d70b40822d69f559e2116`；原作者/作者日期/提交说明与commit总数不变，临时工作树干净。该commit相对其父节点最终涉及4文件：原有attention适配、router、minimax_m3 patch、worker；general注册阶段改动被撤销，因此最终提交不含__init__.py差异。无新增test或thead.yaml差异。三文件Python语法及diff检查通过，未额外运行硬件/GPQA。

本地完整历史bundle已验证，路径`/private/tmp/minimax-m3-amend-20261018.x9xr5k/before-amend.bundle`，SHA256 `5fe36d3c8f6efbb53aad663848f772eb704ea15a80de6b2a67f44a91a0fcf9eb`；原容器仍保留旧HEAD及完全相同的已验证源码diff，不在运行环境fetch/reset/amend/restart。恢复远端旧提交需另行授权，并以新SHA的精确lease更新，不自动执行。此前GPQA和gate仍绑定原运行实例及其冻结证据，不修改历史manifest/SHA；本次只发布相同源码。未创建额外提交或PR。

PPU-13：`/mnt/nfs/users/jinghao/minimaxM3/20261017-minimax-m3-ppu13-plugin-support/refine-001`，包括 commands/runtime/logs/checks；执行前保存脚本。baseline service 为 `fad201d7b6ec:8024:7461:493495998`。

- 单元：`logs/unit-cpu-final.log`、`checks/unit-cpu-final.xml`；算子：`logs/operator-ppu.log`、`checks/operator-ppu.xml`。
- 请求：`checks/result.json` SHA256 `03465d64436129ae35a677c8a3c1ced94576f5c3bff673e85480c937a32c8b3b`；完整原始request/response在checks。
- 审计：`checks/native-verification-v2.json` SHA256 `9508cc394081fbed2581ce300bc6e740a6de78fea429b5eeeefd7191342bce7c`；初版incomplete `checks/native-verification.json` 未覆盖。
- 最终manifest：`runtime/service-manifest-after.json` SHA256 `a19bb33e8c9a93b9e6cf00e5d56d3463c627f72ac87692d62465ec1de2e72198`；Plugin源码manifest `948069e59e5fc997a1f244d2fee362db55305c639f7bd79b006738dcc54a6255`。
- baseline tar：`runtime/plugin-before.tar.gz` SHA256 `a1fcbb3238bb6aa939e6087572a787b3270f3df21c1d7d0315937592e439c844`。
- 完整candidate补丁：`runtime/candidate-vs-commit.patch` SHA256 `bce979c889b043ab7ed1242e4fb902fa63d6f4b275d3bbbb23e74c3d71b3c943`；candidate tar SHA256 `bdf8b6961ac6b8b7ba53770f2b1ee733bc758e09de14dde69c857252957cd273`。
