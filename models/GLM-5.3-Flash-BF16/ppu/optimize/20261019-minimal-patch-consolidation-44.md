# 点44：迁移补丁收敛

状态：**retained，精简版已安装、目标服务运行，75项CPU契约、41项选路及模型最小回归通过**。最终只读审计时间2026-10-19 21:15 +08:00。用户要求将点43的所有修改和新增收敛，只保留必要内容。本点是维护性精简，不新增算法、不调整调度参数、不声称性能收益。

准备已完成：46项CPU契约通过；全部41个op的精简前后selected impl一致；白名单外所有源码逐文件SHA不变，FlagGems-vllm所有Python实现不变，YAML解析结果相同。归档v1的AppleDouble、v2的上游内部symlink被严格检查拦截，均发生于overlay/安装/模型请求之前；v3禁用AppleDouble、只允许目录内部链接并复用核验干净的未安装checkout，原失败证据保留。

受控切换命令`commands/switch-v1.py` SHA `5f697fa01b1f9c5b85009f93228601eb34e3513fbe4565bdd075f375a837cb3e`，18:36唯一派发、18:41模型回归完成，无需回退。两库均为新私有副本，原点43源码未覆盖。`finalize-v2.py`完成29项算子CPU契约、完整补丁导出、逐文件必要性说明和最终只读身份/镜像/挂载核验；v1只保存未执行。候选origin保留官方URL，没有fetch/push。

## 优化方向与依据

点43 Plugin 相对 PR454 修改11个已有文件、新增38个文件；FlagGems-vllm 相对官方main修改4个已有文件、新增11个算子及6个测试文件。迁移中复制了与上游相同的reference实现、通用backend方法和注册声明，另有调参文件整体重排，应消除这些维护负担。

## 内容与边界

目标仅PPU-13、`glm5.3-flash-opt-20260911`、8011；保持MBT32768/maxseq64/threshold0/TP16/BF16/FULL_DECODE_ONLY/关闭前缀缓存。沿用点43隔离环境，不改源适配容器、vLLM、FlagGems、权重/tokenizer、DB或交付脚本，不提交推送。

优先复用上游函数和backend继承，仅保留不同的BF16接口与shape特化。旧PPU BF16模型/cache/graph路径、初始化顺序和MQA host修复已有失败复现证明必要，不能为了文件数直接删除。算子实现继续留在FlagGems-vllm，Plugin仅承担接入和兼容。

在新私有副本整理，不覆盖点43原树。所有删除均限新副本中已核对的重复文件，原树和外部归档可恢复。配置去除无关重排，测试保留用于证明必要边界。

### 精简结果

| 项目 | 精简前 | 精简后 | 说明 |
| --- | ---: | ---: | --- |
| Plugin相对PR454修改已有文件 | 11 | 11 | 保留必要注册、初始化与ABI接入 |
| Plugin新增文件 | 38 | 35 | 移除4个重复模块，增加1个回归测试 |
| Plugin新增文件总行数 | 8232 | 7530 | 净减少702行，包含注释及测试，不当作运行时加速 |
| FlagGems-vllm修改已有文件 | 4 | 4 | 算子Python内容不改 |
| FlagGems-vllm新增文件 | 17 | 17 | 11个必要算子、6个边界/graph/shape测试 |
| FlagGems-vllm调参YAML diff行数 | 426 | 8 | 恢复上游格式和版权头；仅新增MQA配置，解析结果与点43相同 |

移除的候选重复模块为FlagGems `thead_normalization.py`以及reference的`thead_normalization.py`、`thead_quantization.py`、`thead_rotary.py`；先验证实现AST与上游相同，再让窄backend子类继承上游方法。reference backend仅保留BF16两个接口差异；FlagGems backend复用一致的normalization、Triton量化fallback及普通attention路径。保留不同的旧FlagGems activation/RoPE/quant host/MoE provider，避免去重时换算子。旧量化文件中的重复Triton kernel移除，使用上游相同实现；旧注册长列表改为等价数据表，impl ID、priority及可用性策略不变。

兼容性核查同时发现两个旧BF16 adapter仍引用已重命名的`.top_k_per_row`，改为实际存在的`.thead_top_k_per_row`，并增加导入契约；没有替换kernel或扩大shape支持范围。其余数值实现、模型、KPool/cache/graph和调度均未改。完整逐文件保留理由在`necessity-inventory.json`，包括PPU模型/processor/配置为什么不能直接替换成PR的新公共路径。

### 必须保留的部分

- PPU BF16模型、cache/KPool布局、vendor Sparse MLA和graph兼容路径：与PR454公共FP8/portable接口不同；此前直接切换已有初始化/OOM失败证据，不能按文件数删除。
- 初始化顺序、MLA Prefill provider注册、bounded activation双接口、graph前CachedOp解析和新旧注册表组合：维持当前ABI并保留上游新增能力。
- 已保留的MoE小M/M64 GEMM2、padded align、长Prefill conv/KDA、MQA固定调参与BF16 MQA host修复：本轮不更换实现或参数。
- 不迁入点40未安装候选、点41未保留阈值或点42无收益调度器；不删除必要fallback和回归测试以缩小统计。

## 正确性与命中

调用本地`inference-accuracy-evaluation`、能力`e2e/accuracy`、显式模式`minimal-regression`。先比较复用函数AST、接口/注册元数据、非目标分支和所有原选路，再执行CPU契约；通过后受控切换精确服务，检查实际导入、目标graph capture/至少两次replay、C1/C8明确答案及16K边界。失败回到点43原目录和原参数，不叠加新优化。

历史补充171/198仅属于点43，不改写为新源码的精度结论。若精简改变数值/算法/graph覆盖则停止该项去重，不将维护任务升级为未授权的大规模适配重构。

实际结果：Plugin 46/46、FlagGems-vllm 29/29 CPU通过；精简前后全部41个selected impl一致；原C1/C8请求、11个明确答案（北京/2/5）通过；P16383/16384/16385各D8边界输出与点43原结果逐项相同。服务日志FULL Decode graph 11/11 capture完成，多token C1/C8和边界请求覆盖至少两次replay；不是逐rank设备trace。非PPU硬件和其他模型没有实测。

最终实例`PPU-13:glm5.3-flash-opt-20260911:2865123:512203485`，8011 health200、空闲；argv/环境/DB/thead/权重/tokenizer不变，vLLM/FlagGems源码不变，镜像谱系和`/mnt:/mnt` RW rprivate挂载复核通过。

| 组件 | 当前真实editable目录 | 内容SHA256 |
| --- | --- | --- |
| Plugin，PR454 `f7696963` + 精简补丁 | `/workspace/e2e-opt/glm53-20260911/vllm-plugin-FL-minimal-20261019-p44-v2` | `c185fbbdedeb17a589629aec171cc74f938574a458290c6dedb44efb1871f020` |
| FlagGems-vllm，main `b4d3382b` + 保留算子 | `/workspace/e2e-opt/glm53-20260911/FlagGems-vllm-minimal-20261019-p44-v2` | `fe3891750fd02c2f766c15795c7453fe20255bfad640ea0f7405de9882d9898a` |

两库本地分支均`e2e-glm53-minimal-p44`，无PYTHONPATH覆盖；`start-model-opt.sh`不变，通过新editable生效。尚未commit/push。

## 性能效果

not_run。没有baseline/candidate/revert性能数据，不把旧收益归属精简版本；本轮目标是补丁必要性和维护面收敛。

## 决定、风险与回退

保留本轮维护性精简，`pr_readiness=experimental`；不是纯净PR454 PPU验收，也未完成新身份的GPQA/性能四场景。没有自动重跑GPQA、继续性能优化或恢复旧monitor。原始169/198和用户认可补充171/198不改写，不当作精简版本的新实测分数。

回退：两个point43私有目录均完整保留，重新editable安装其原目录并按本点`switch-before.json`中的原argv启动目标服务，再执行同一最小回归。重复模块仅从新交付候选中移除，均可从原目录/点43归档恢复；不清理远端证据、失败轮或原用户dirty文件。

## 外部证据

父证据：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261019-point43-upstream-migration`。

本点：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261019-point44-minimal-patch`，可执行命令先保存`commands/`并记录SHA。临时本地审查副本在`/tmp/glm-p44-eEOQvX`，不进入项目`scripts/`或模型目录。

- `final-review.json` SHA `8f4f78be4d767bb45cc5839da72321cf2cd55008b1b89531eb9cc8a020e1655b`；`runtime-final.json` SHA `c69d1ee346d3cfceff675d559239212fc0df743d21a426b1833a52b5d719ca45`。
- `necessity-inventory.json` SHA `ca502d2c999e0d0d83841710a40bf7afd9845dd99cad8924140dd1ef0e4c9f89`，逐项说明所有保留文件。
- `vllm-plugin-FL-complete.patch` SHA `a653b11a3bd0a1251289c9e6c7a645463d52d9d7840c39474fa9b4e9cf88ec4d`；`FlagGems-vllm-complete.patch` SHA `92ba9cca3358f68d32b3980acf4e85a57bc58bdff4235dfeddb433813c2632fc`。原生`git apply --numstat`分别确认46/21个文件，包含全部untracked新增，不只导出`git diff`。
- `source-v3/plugin-cpu.log`、`flaggems-cpu.log`、`source-v3/routes-result.json`、`consolidated/minimal.json`、`consolidated/semantic.json`、`consolidated/final-audit.json`保留原生结果；必要SHA见state。
