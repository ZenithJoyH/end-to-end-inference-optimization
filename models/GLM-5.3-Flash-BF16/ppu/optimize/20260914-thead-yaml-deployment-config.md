# 20260914-thead-yaml-deployment-config thead YAML 配置收敛

- 状态：`retained`
- 分类：`deployment`
- 目标场景：GLM-5.3-Flash PPU 服务
- 目标阶段：Prefill / Decode / Mixed
- 依赖：Plugin thead 配置加载

## 优化方向与瓶颈依据

早期通过环境变量叠加 per-op 路由和黑名单，不利于部署、打包和复现。

## 优化内容与适用边界

把已验证的 per-op 路由以及 `index` 等黑名单收敛到 thead YAML；启动脚本显式
`unset VLLM_FL_PER_OP`、`VLLM_FL_FLAGOS_BLACKLIST_APPEND` 和旧 MoE 开关。

## 正确性与路径命中

YAML 解析、Plugin 导入和最终服务启动均通过；当前启动脚本不依赖这些环境变量覆盖。

## 性能效果

没有独立吞吐数字。效果是确保部署配置与测试配置一致，避免环境变量漂移改变实际
dispatch。

## 决定、风险与回退

决定保留。任何 YAML 变更都必须重新核验实际 backend 命中；回退为恢复上一版 YAML
及其 SHA，而不是重新叠加隐式环境变量。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/thead-yaml-deployment-config-20260914`
