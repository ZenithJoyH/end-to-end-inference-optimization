# deploy-004-container-sync 同步优化后的PR至qwen3vl

- 状态：完成；用户授权2026-11-04同步PR #1069优化后代码到mx-59/qwen3vl、核验调用接口、其他配置不变，执行正确性与graph验证。
- 目标固定公开head：ce0feddceb0d74a031081e57ce9ff9d24fef3b84。原PR/数值优化/CI证据保留。
- 范围：仅同步PR已有差异，不git pull/reset、不覆盖无关MoE等改动、不升级依赖、不改采样/blacklist/env/启动参数；调用方已对齐则不重写。先备份并以预期SHA保护，验证失败自动恢复本次文件。
- 验证模式：本地accuracy skill的minimal-regression原则，适用公开算子与实际Plugin hook；91项组件测试、受影响M1及M>1实际调用、input/RNG不变、fallback/幂等、变化输入graph capture/replay。没有模型服务时不擅自启动/停止模型；不把组件验证当全量GPQA或模型graph gate。
- 外部产物：/public-flash/jinghao/qwen3-VL/20261104-qwen3vl-mx59-topk-topp-pr/deploy004；命令先归档再执行，raw仅远端。本机临时工作目录/tmp/qwen3vl-topk-pr-20261104/deploy004。
- 部署前工具事件：sandbox中的Ansible本地RPC未启动，提权重试指定Host连接已通过；第一次只读probe假定Triton发行包名，实际元数据不是triton，0源码写入/0模型请求，v2对可选发行包名记null并后续核验模块版本。不把工具事件当模型失败。

## 落盘与接口

优化backend与公开PR ce0fedd精确一致，SHA256 `0f3f4eeb160032a6832e0ac214e947bb9fe435570f4de22eb1791f63d4befbb4`，真实导入为 `/workspace/FlagGems-vllm/src/flaggems_vllm/runtime/backend/_metax/ops/top_k_top_p.py`。

共同步6文件：backend、原MetaX导出列表排序、对应operator metadata块，以及PR reference/tests/benchmark。导出集合和其他metadata完全保持；容器FGV仍是bad340d6基础上的精确文件补丁，保留原MoE等改动，不伪称整个仓库等于PR tree。Plugin08da21c、FlagGems c3c5f5ab2源码树未变。

Plugin两文件本来已对齐，未重写。实际调用仍为 `top_k_top_p(logits, p=p, k=k)`，已核验新返回tensor被消费、输入/RNG不变、幂等安装、unsupported metadata执行前fallback、执行中错误不重试，无旧库兼容导出。

## 正确性与graph

- qwen3vl实际安装目录完整组件测试：91 passed，含6captures/18次变化输入replay。
- 同步前后20组N=1..262144、BF16-grid/FP32排序及k-only/p-only/combined结果逐位一致。
- 真实Plugin hook覆盖M1/V4096、M1/V151936、M8/V151936及两分布：6captures/18次变化输入replay全部通过。
- 当前没有模型服务，未启动/重启模型，不将上述12captures/36replay称为模型graph或完整GPQA gate；没有新性能测量。

## 工具incident与恢复

第一轮组件及位级测试已通过；随后hook脚本因直接执行时baseline模块不在sys.path，尚未执行hook数值验证即退出，controller自动恢复全部6文件。按accuracy-diagnosis归类measurement-invalid，非模型数值failure。全部三棵Python源码树及Docker配置独立核验已恢复。

v2仅把测试参考导入改为固定文件路径；重新安装同一SHA候选，复用明确绑定到同一容器/参数/文件SHA的91项和20组已通过证据，重做未覆盖的全部hook/graph场景。原failure与rollback保留，当前终态为 `results/completed-v2.json` 和独立 `results/final-audit.json`，均passed。

## 配置与最终状态

容器Config/HostConfig指纹、依赖revision以及Plugin/FlagGems全部Python文件未变，FGV仅预声明5个Python文件及1个operator metadata文件变动。qwen3vl仍运行、无模型进程；不影响其他服务。

裸进程默认 `VLLM_FL_USE_FLAGGEMS_VLLM=false` 保持原状，top_k_top_p策略允许。原 `/public-flash/jinghao/qwen3-VL/start-model.sh` 已有 `export VLLM_FL_USE_FLAGGEMS_VLLM=1`，SHA256 `86cd7f6222d6f293870478be0a47bdd852a29ace09a3dbb0f07564dec87a2a0a`；脚本未修改。hook验证只在测试进程显式启用同一已有开关，不写全局环境。

独立最终audit SHA256 `a2c91c250338ef0a2677debd5cad1d908d0d59c58ac3103a099199dfd136eb12`；原始证据、备份及命令均在deploy004。决定保留部署，不签模型精度gate、不扩大正式评测或性能任务。
