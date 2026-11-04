# OP006：GDN prefill V-major接入修正与验证

用户2026-10-14明确要求去掉多余转置，按正确V-major重新做prefill数值/graph验证，通过后加入白名单。分类operator/improve（接入纠错，无kernel性能改动），scope minimal-regression，沿用本案例/同隔离容器，source8002/shared/vLLM/weights/tokenizer不改。

当前精确FG19实例296014/create1791945473.24；停止仅此实例及所属双rank。MetaX导出已为V-major，backend不再转初/末state，非MetaX generic仍转换K-major；13CPU/mock回归覆盖两backend ABI。只有GPU数值和graph全部通过才从19扩展为20项gdn_prefill，无blacklist，不缩减已开启集合。

冻结7GPU矩阵：保留历史seed42随机序列的K128/V128、长度64/96；非方形K96/V80长度64/96；K64/V64长度1/63；K128/V128长度1/63/65；零长度段0/64；零初始state长度64；非连续leadingstride-padding512长度64/96。BF16 QKV/beta、FP32 g/state；非零非对称V-major状态，输出与finalstate同CPU FP32逐步递推比较，原atol.002/rtol.02不变。每项capture+2次改变q/v/state后的graph回放，检查输入状态不被改写。首个失败保存逐项误差/样本范围，不放宽门槛；不把精度失败误归因于布局。

通过后FG20服务新双rankgraph/2smoke与固定10题/C8新样本，从冻结config.output_root查验，不复用旧同源C8。失败保留正确adapter但FG19服务，不启用新增prefill。正式cap50000 GPQA失败及gate缺口保留，不宣称正式精度或E2E收益。此轮不更新公开issue、无额外发布授权。

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op006-patch.json SHA b6480fd2b8a94f73e64710afcb6afd42f2e8aabd7360d40517986697768ba542

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op006-prefill-probe.py SHA 6eadb2dba9265195fe5aa2bb190bb4f359c1a2ec2bd838424706474342f9a58d

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op006-apply-private.py SHA 3014f52d593af1b979c4565cf6fae1092590b67e9ac1f9478aab62aad114cca2

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/start-op006-prefill-01.sh SHA e64ca843b4f9c91157f8b8ea5f6db240c51fcc35b008dacf84713b0265ba2c01

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op006-bind-op006-prefill-01.py SHA 320f1b003112feae41fa67db7f609cf62a100b1a6e494f3cb7edae308cf80b0b

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op006-op006-prefill-01-c8-config.json SHA bbbeb643c2a6665210e3c6d1c2d0cb4f663354afd10b63023ec9fe702d5f8c32

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/start-op006-decode-01.sh SHA 2889a18a9271555fc003d8ea632cae2c36ff11ec3ab06c88da6e96aa0efcdbfb

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op006-bind-op006-decode-01.py SHA 21b6d6baf6ebd5d7037e1acef937e4bc569c7d4c5240d40a113b87ce3f57045f

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op006-op006-decode-01-c8-config.json SHA c0d436f5d941427f4fe38a7538bcd516073e0650946f8c8a5d111ce485288075

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op006-controller.py SHA 01043e99ba79343b71ae61caa3bc03f73e3cff1b9de6d9e76110d0e75e69dac2

收尾只验现有结果/精确实例/source与白名单；命令/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op006-finalize-existing.py SHA891b4448e8d2e49e1e96852c30d0bdb1644928af0319b03773e9bf5485120434；不发送请求，不编辑上游issue。

阶段观察：历史失败输入correct-Vmajor输出max_abs .00048828125，finalstate max_abs .0036704540252685547但无元素超(.002+.02*abs(reference))，两改变输入replay通过；非方形K96V80通过。不能把最大绝对state误差大于.002误解为失败，冻结规则含相对容差。

真实新失败：correct Vmajor [0,64]输出无超限，但finalstate1/786432元素超原容差，max_abs.002556176856160164，relative .17338621616363525；前4矩阵/8graphreplay通过。FG19恢复/C8后串行diagnosis：保留原失败，不自动晋级；完整矩阵继续记录失败、保存空段输入.pt，pair删除空段且active输入/state相同，判断边界语义变化或BF16组块数值差异；末尾保持FG19，同源重启仅新graph/2smoke并关联前实例C8，不重跑C8。

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op006-prefill-diagnostic-v2.py SHA73d59950dd92197e5c4a154d2c48af096d1112dc2e4eadb7f826eaebb8d41d6c

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/start-op006-decode-02.sh SHA808c33cb86ddc66d262bdbde69aee651bb1011eb1808fc782283ff42bfe25eb9

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op006-bind-op006-decode-02.py SHA086637d45c0c6c22761a3b383208a7164ff20756beb6c63d4dff1596d6f1fcbb

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op006-diagnostic-v2-controller.py SHAaaed9217aecac7deb385c200d151324d670d746c607905f60514963e4da8461c

诊断终态只核验与保存已有配对/GPU矩阵/当前FG19精确实例与同源C8绑定；commands/op006-finalize-diagnostic-existing.py SHA757c088d375d04dcb52a6dd41b5ec0ecfbaf9b915f2ca806ea352d7c7605b355，不发模型请求。

终态：failed/prefill-not-enabled/FG19-restored。13CPU/mock测试通过；完整7GPU矩阵6通过/1数值失败，14改变输入graphreplay全部满足原容差，输出全无超限、finalstate1元素超限。失败位置[1,0,72,61] actual.012186499312520027 vs FP32ref.014742676168680191，abs.002556176856160164 >allowed.002294853562489152。移除空段后activefinalstate逐位相同/maxdifference0且仍同1元素超限，排除此state差异由空段语义导致；output bitwise不同但均在容差，不能声称全输出分布完全相同。BF16 chunk vs FP32递推有真实数值差异，具体中间步骤未定位，不将其等同于任意shape算术bug或历史GPQA根因。

正确adapter修复保留，MetaX无多余初/末state转置；原19项白名单完整、无blacklist/FGattention1，未新增gdn_prefill。当前qwen36-fa-opt:319960:1791948830.86/18002/2、3卡两rank各190graphlaunch+2880FGpacked+960FA split/merge；当前新2smoke/graph及先前同源decode01-C8按源码/完整启动参数等价绑定。vLLM/FG/FG-vLLM源码、权重/tokenizer和源8002未改，未发完整GPQA、性能或上游评论，未提交推送。

终态/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/results/op006-terminal-diagnostic-validation.json SHAbca490c34a4e6b84abf5915ce84b105ecb0a725bad2c47cc82e35919b0610279；输入保存在results/op006-zero-segment-inputs.pt，完整diagnostic-v2与原首失败probe并存，finaldiff/state.yml索引已归档。下一步只定位同输入BF16组块finalstate误差，不能放宽容差或偷偷开启prefill。
