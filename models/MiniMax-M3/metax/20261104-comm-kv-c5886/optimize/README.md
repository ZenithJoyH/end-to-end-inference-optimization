# 20261104-comm-kv-c5886 / optimize

<!-- e2e:summary:start -->

- 案例：20261104-comm-kv-c5886
- 当前状态：bounded_diagnosis_complete
- 当前候选：—
- 下一步：通信显存已定位策略差异、多套通信器及P2P资源差异；通道/BUFFSIZE/P2P、tuning与驱动的单独贡献及C588模型级优化待独立验证，不自动重启。

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| comm-001 | complete | — | [comm-001.md](comm-001.md) |
| kv-002 | complete | — | [kv-002.md](kv-002.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| comm-probe-tp16-8192x6144 | default_communication | communication_path_device_memory_delta | 3.9161605834960938 | GiB/die | memory_probe_only_not_E2E |
| comm-probe-tp16-8192x6144 | four_channels_1MiB | communication_path_device_memory_delta | 1.3591842651367188 | GiB/die | memory_probe_only_not_E2E |

<!-- e2e:summary:end -->

2026-11-05 只读再归因：TP/EP PyNccl与普通TP的PyTorch路径合计三套通信器；同C588通信策略对照省2.557GiB/die。C550原生日志P2P为4通道/128KiB，C588限额仍16通道/1MiB；两端当前MCCL/运行时库SHA相同。拓扑、驱动、tuning的独立贡献未拆，未进行新的模型/通信测试或重启。详见 [comm-001](comm-001.md)。
