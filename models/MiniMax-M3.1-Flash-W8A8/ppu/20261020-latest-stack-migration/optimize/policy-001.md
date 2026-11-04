# policy-001 撤回非必要的库选择策略改动

当前接入更新：[adapter-001](adapter-001.md) 已移除缓存/预处理与try融合三个dispatch注册，改为直接库调用；当前201单测通过，设备/模型回归因卡占用待执行，下文既有回归属于历史版本。

用户要求不修改非必要的上游环境开关行为。本轮仅撤回refactor-001新增的provider helper、平台op白名单及对应文档，恢复既有MoE/动态量化直接读取 `fl_envs.VLLM_FL_USE_FLAGGEMS_VLLM`；新接入的INT8/OAI adapter沿用同一个现有开关。官方env定义和默认值不改，必要算子接入/模型语义/backend边界与FV/FG kernel保留。

为在显式开关方式下使用保留的FV优化，新容器独立脚本增加已有开关=1，不改全局脚本；原host归档脚本保留，新脚本以唯一名称归档。mode=minimal-regression，执行开关正反例/默认值与上游函数AST一致性、适配契约单测，资源空闲时执行设备graph及临时模型最小回归。未执行完整精度或正式性能，不复用gate。操作前备份与预image逐文件校验，代码直接修改官方main工作区，禁止stash/提交/推送。

## 已完成的代码核验

- 删除 `dispatch/backends/flaggems/impl/provider.py`，移除 `use_flaggems_vllm(op_name)` 与按平台/算子的默认选择。
- `dispatch/config/thead.yaml`、`dispatch/README.md`、`envs.py` 与官方main逐字节一致；`VLLM_FL_USE_FLAGGEMS_VLLM` 未设置时仍为false。
- 既有5个MoE adapter和动态INT8量化函数与官方main函数体AST一致，开关正反例覆盖真实环境变量读取；新INT8/OAI/fused-experts接入沿用直接 `fl_envs` 判断。
- 仅新容器独立脚本显式设置已有开关=1，以启用FV库及本任务保留优化；不改变框架默认值、不在调用点添加平台特例。原host脚本作为历史归档保留，新脚本见state的startup_script。
- 199项单测通过；8–15卡INT8 56/56逐位一致、最大误差0且每case两次graph replay通过；模型preprocessing/激活/路由10项通过。

当前Plugin完整源码tree为 `3e8bf10ab7629a27ec960757ddb7e50b40054603eb33b8017288a64a608288c7`，FV/FG未改。模板/请求级graph最小回归仍在进行，未签发正式精度gate，没有性能测试或收益结论。

## 最终回归与交付

105个合成算术请求（C8/C33/C64）及2项中英文smoke全部通过；实际并发达到8/33/64。FULL 7/7和PIECEWISE 7/7 capture完成，绑定API实际进程环境已证实原开关=1。服务没有直接graph replay计数器，decode迭代下界及其推导见原生minimal-receipt；设备56case均直接capture/replay两次。继承breakable graph配置下Inductor禁用，本轮不声明Inductor验证。

临时8045已退役，容器保留，源8035健康200；全局启动脚本未变。最终三库源码与候选冻结一致，两份补丁反向校验通过；原生审计确认官方env/config/docs逐字节不变、helper已删除、main分支且暂存区为空。`VLLM_FL_USE_FLAGGEMS_VLLM=1` 也会按上游原有定义选择其他已存在的FV分支，本轮没有改写这些分支；本轮最小回归不等于新的完整多模态/GPQA精度结论。

新容器启动入口仍为 `/workspace/minimax-m31-latest-stack-20261020/start-model.sh`；host当前归档为 `/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261020-minimax-m31-latest-stack-migration/commands/start-model-latest-env-switch-20261020.sh`，SHA256 `3a3abf44ece2e8da920de4184e4b391107af0513f8c53a7bb22e89f81657d251`。仅增加现有开关=1并使用独立日志位置，不引入新环境变量定义。之前host启动脚本为历史版本，不作为当前入口。当前安装路径仍为 `/workspace/vllm-plugin-fl`、`/workspace/flaggems-vllm`，Plugin包版本不变；源码直接在官方main的工作区修改，未用stash迁移、未提交或推送。

原生产物根 `/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261020-minimax-m31-latest-stack-migration/profiles/policy-001-20261020-01`：

- `validation/unit-01.xml`：199 passed。
- `validation/dense-int8-dispatch-01.json`：56/56逐位一致，最大误差0。
- `validation/model-operators-01.xml`：10 passed。
- `candidate/minimal-receipt.json`：105+2 passed，非正式分数/gate。
- `validation/final-audit.json`、`validation/close-receipt.json`、`result.json`：当前配置和终态。
- `validation/startup-log-archived.log`：不可变的本轮启动日志副本，避免后续手工启动改写当前日志。
- `policy-only.patch`：本轮精简改动，SHA256 `a3d0f6c51a416c0c44c7547ca8da078baab1dca595f17b55def3bb9e8eb00f8c`。
- `official-head-combined.patch`：当前完整改动相对官方main，SHA256 `9fd2b7b67c8e1568334bcedb4e0f4ef7fba095ab41e84f922b2b8e8d4d500cbc`。

精确证据与命令SHA见 [state.yml](state.yml)。回退只针对停止后的目标实例，核验源码后反向应用本轮patch、恢复归档的start-model-before.sh并重新验证。改前备份保留全部未提交文件。`pr_readiness=ready_for_review`，尚无当前组合的正式GPQA/Math500/ERQA或性能数据，正式性能仍不允许；监控PAUSED，不启动后续测试。

2026-10-20 范围更正（[tests-001](tests-001.md)）：原回执实际为 **198 项CPU + 1 项GPU量化测试通过，共199项**。上文如称纯CPU或零设备测试，表述不准确；原生JUnit保留，本更正不改变通过总数，也不补齐模型/graph验证。后续CPU命令显式排除gpu/multi_gpu。
