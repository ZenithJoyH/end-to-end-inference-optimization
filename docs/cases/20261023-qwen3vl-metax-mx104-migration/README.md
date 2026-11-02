# Qwen3-VL / MetaX：mx-59 验证环境迁移至 mx-104

完整源容器快照已迁入并验证：GPU4/5、TP2、端口18977、容器`qwen3vl-pr943-split1-mx104-20261023`。镜像/挂载/四仓库源码与模型/tokenizer、实际FlagOS/native路径及graph/C8通过，其他服务未动。

ERQA400原生182/398=45.73，2条超时拒答计错后的全部400为45.50，超过40。分数绑定原mx104评测实例，不跨Host复用GPQA gate；当前Host正式GPQA gate未签发。

初始targeted性能对照已完整结束：同GPU4/5、prefixON和其余配置不变，两个独立split0→1→0组，共180轮/36测量全部保留，逐条token长度、原始SHA和前后源码核验通过。split1相对split0的P1K输出/总吞吐下降11.37%、mean TPOT增加13.33%；缩减P64K/D128/C8/N16输出/总吞吐下降38.30%、mean TPOT增加85.27%。回退组输出聚合漂移+0.04656%/-0.08280%，稳定性/重复门禁通过。冻结比较failed表示性能回退，不是数据无效；完整P64K/D1K/C64/N128尚未扩大。

历史测量恢复项保留：5/W12预热失败、动态采样sort constexpr缓存键问题、SC64客户端cwd遮蔽零请求、CWD64输入多1token。未改算子/编译器，统一M1–64准备和只按输入有效性选择seed1042后完成当前对照；不混旧轮、不放宽门槛、不挑测量轮。

22:00:25UTC恢复原split1/helper；22:02独立核验prefixON、health200、MoE/attention/helper SHA及graph16/C8通过。控制器退出、本轮监控停用，服务保留。规划复盘04把扩大同契约长KV诊断列为下一步；未将缩减结果外推为完整/正式验收。

[结构化及详细记录](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261023-qwen3vl-metax-mx104-migration/README.md)。远端证据根：`/public-flash/jinghao/qwen3-VL/20261023-qwen3vl-metax-mx104-migration`，最终比较`results/performance-iv64-comparison.json`、恢复`results/restored-iv64.json`。
