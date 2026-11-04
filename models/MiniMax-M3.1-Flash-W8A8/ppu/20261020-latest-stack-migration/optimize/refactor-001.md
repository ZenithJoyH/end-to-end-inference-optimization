# refactor-001 Plugin 平台边界与适配代码收敛

当前接入更新：[adapter-001](adapter-001.md) 已移除缓存/预处理与try融合三个dispatch注册，改为直接库调用；当前201单测通过，设备/模型回归因卡占用待执行，下文既有回归属于历史版本。

当前策略更新：[policy-001](policy-001.md) 已撤回新增provider/平台白名单，恢复上游环境开关；新容器当前独立启动脚本显式设置既有开关=1。此前实验中的策略/启动SHA为历史记录。

当前路径更新：两库已按用户要求更名为 `/workspace/vllm-plugin-fl`、`/workspace/flaggems-vllm`，见 [rename-001](rename-001.md)；下文原路径为本实验执行时的历史记录。

已应用到新容器 `minimaxM3.1-opt-latest-20261020` 的私有 Plugin：`/workspace/minimax-m31-latest-stack-20261020/plugin`。本轮整理通用调用、backend 策略和模型语义的职责，保留现有数值实现；原容器、8035 服务、全局启动脚本、FV/FG kernel、vLLM 与编译器均未修改。无提交、推送或新 PR。

## 最终设计与文件

以下路径均相对上述 Plugin 根目录。

| 职责 | 最终位置与变化 |
|---|---|
| 通用 INT8 Linear | `quantization/w8a8/linear.py` 使用 `CachedOp("scaled_int8_mm")`；删除设备名称、算力、warp 与私有模块路径判断。FG/reference backend 负责公开 API 与原生 fallback。沿用既有 Linear 策略 key/黑名单、strict/fallback。 |
| 库选择策略 | `dispatch/backends/flaggems/impl/provider.py` 统一按 op 读取现有配置；默认白名单放入 `dispatch/config/thead.yaml`，已有显式环境开关优先。每 worker 缓存，不新增永久环境变量。 |
| MoE/激活 | `ops/fused_moe/activation.py` 经 CachedOp 调用，删除 vendor 判断；库接入位于 FG backend，量化融合按公共可选能力和策略选择；`quantization/w8a8/moe_experts.py` 合并重复参数构造，保留 SiLU/OAI 语义。 |
| W8A8 通用语义 | `quantization/w8a8/moe.py` 统一传递显式 alpha/beta/limit，安装幂等。 |
| MiniMax 模型语义 | `patches/minimax_m3.py` 单入口维护 packed mapping、视觉三路 QKV 与缺失原生 preprocessing 包装。删除旧 `minimax_m31_w8a8.py`、`minimax_m3_ppu_attention.py`，去掉无读取方的 lm_head 标记和模型构造器包装。 |
| 平头哥编译兼容 | `dispatch/backends/vendor/thead/patch.py` 集中原有 topk16 与 BF16 GQA8/D128/topk16 Prefill launch 兼容；在 `WorkerFL.load_model` 的 backend 边界安装，按 MiniMax 架构及实际 shape 限定。其他模型不安装这组 patch；kernel 数学与已保留 launch 参数不变。 |

平台特化仍有必要，但已限制在平台配置/backend 边界。两个 launch 包装因当前编译器限制保留；待上游原生路径在同设备、同 shape 和 graph 下通过后可删除。不以 served name、权重路径或机器身份选算子。没有另建 dispatcher。

共涉及 30 个新增、修改或删除文件（含测试、文档）；生产 Python 净减少 32 行。移除了重复选择、构造器包装、重复参数和日志，而非只搬动文件。

## 版本与依赖

Plugin 基线 HEAD `a696859b9aa528dfd5b21f5da3403fdc16bac4cd`，最终完整源码 tree SHA256 `374b2b47b83dcf35504f716dd088430be14045b0329c3aacb7a669bf989152d9`。

FV 保持 HEAD `fa78ddee4c3e78ce5047213ff0ef02acff34b2d5` + 保留补丁，tree `2f62194e14f5f49eb579532aacbafd20716db372f260a2396b32fe4e1fe13f26`；FG 保持 HEAD `8200f71f51d784d54a5a51019cb955acb74d64c1` + 保留补丁，tree `1798d770ab7e7247d9b91c45870297776a3f041055d5da8ec854cdd34178c8be`。vLLM 0.24.0 / torch 2.10.0 / Triton 3.6.0 不变。FV 的公开 scaled INT8、MoE 与可选融合能力仍为跨仓库依赖；未选该能力的路径不应强制导入可选库。

## 验证

外部原生产物根：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261020-minimax-m31-latest-stack-migration/profiles/refactor-001-20261020-01`。全部命令先归档到该案例 `commands/`；准确 SHA 见 [state.yml](state.yml) 的 `refactor-001.scripts/native_evidence`。

| 范围 | 实际结果 | 原生产物（相对外部根） |
|---|---|---|
| 调用契约、provider、黑名单、strict/fallback、无可选依赖、非目标平台/模型隔离、重复安装与 worker 生命周期 | 178 passed / 0 failed；mock 只证明路由和契约 | `validation/plugin-unit-04.xml` |
| PPU 8–15，INT8 经新公共 dispatch，M7 fallback/M8/16/32/64/8192、K128/6144、N96/768/1536 | 56/56 逐位一致，每 case 两次 graph replay | `validation/dense-int8-dispatch-01.json` |
| 模型 preprocessing/cache 写入、激活、路由、graph | 10 passed / 0 failed / 0 skipped | `validation/model-operators-01.xml` |
| 原生 reference INT8 与 OAI 激活 fallback，物理 PPU8 | 两项通过，每项两次 graph replay；最大误差 0 / 9.3132e-10 | `validation/native-fallback-01.json` |
| Flash1019 TP8 模型服务，8045 / MiniMax-M3.1-latest | FULL 7/7、PIECEWISE 7/7 capture；C8/C33/C64 共 105 个合成请求 + 2 项中英文 smoke 全通过 | `candidate/service.json`、`candidate/minimal-receipt.json` |
| 风格、源码冻结、补丁 | Ruff 按仓库 0.14.0 要求检查受影响范围；最终单测在格式化后运行；三库 tree 未漂移；两份补丁反向检查及 `git diff --check HEAD` 通过 | `post-validation-source.json`、`validation/close-receipt.json` |

模型服务没有直接 graph replay 计数器；原生 capture、实际满并发、prompt plateau 与 generation 增量证明 decode 已持续执行，推导迭代下界分别 29/36/35，不能冒充直接 replay 计数。继承的 breakable graph 配置在原生日志中禁用 torch.compile/Inductor，本轮不声明 Inductor 验证。

初次 unit-01 在导入期安装平台 patch 触发循环导入，已定位并移到 Worker 模型加载边界；unit-02 的一个旧 test double 未适配关键字转发，已保持契约断言修正。失败 XML/log 均保留；最终 unit-04 及设备/服务测试通过。未修改或放宽数值容差。

其他平台硬件未运行，应交给对应平台 CI；mock 不能证明其设备数值或性能。**本轮没有完整 GPQA/Math500/ERQA，没有正式精度 gate，也没有端到端性能数据或新增吞吐收益结论。** 旧 gate 未复用。

## 交付、回退与当前状态

`pr_readiness=ready_for_review`：职责、测试与补丁已整理，可供代码评审；不代表全平台实测或正式性能验收。

- 本轮增量补丁：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261020-minimax-m31-latest-stack-migration/profiles/refactor-001-20261020-01/refactor-only.patch`，SHA256 `97ceedadf3068bca54e7d6696a6e723cc139411535e0399eaa35923adac93e0c`。
- 相对官方 HEAD 的完整适配补丁：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261020-minimax-m31-latest-stack-migration/profiles/refactor-001-20261020-01/official-head-combined.patch`，SHA256 `c9c2c83a3d2ff198bb61cfb06131e01bf5d1527f8681583a05536e51f50670b8`。
- 改前备份：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261020-minimax-m31-latest-stack-migration/profiles/refactor-001-20261020-01/plugin-before.tar.gz`，SHA256 `1e9e95857d53bfc6e2b2e707b1f7f400f5a0359c9283302158ea10ea265729b7`。

回退本轮时先按当时精确绑定停止目标模型实例，验证最终 tree 后反向应用 **refactor-only.patch**，或从备份恢复本轮受影响文件，再核验改前 tree `5a6c381c021e0a338b2f0f46ec0c15e2e16a728a2a06161095113c766161411c` 并回归。不要用完整官方补丁反向应用来回退这一轮，否则会移除之前保留的适配。

临时 8045 验证服务已退役，容器及最终代码保留；旧 8035 健康，根目录 `start-model.sh` SHA 未变。新容器独立启动入口仍为 `/workspace/minimax-m31-latest-stack-20261020/start-model.sh`，实际启动需重新检查设备与端口空闲。监控保持 PAUSED，无后续自动评测或压测。
