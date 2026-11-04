# env-001-script-scope-baseline

新入口基线：当前启动脚本20项FG（17 ATen+3 GDN），native attention，TP2 BF16/GPU2、3/8192/prefixoff/graph64。用户已明确授权暂停现役832568/18002，独立容器测试结束恢复原容器服务；其他卡不操作。anchor和算子范围变化，按项目规则新建案例，旧全21/旧精度/失败不迁移为新验收。

复用已安装de2298b+5补丁及原FP32/IEEE/atol.002/rtol.02，制作有效可写层快照，新容器挂载完全相同，/workspace与site-packages私有；先image lineage/mount parity，再启动/graph两replay/fresh10docC8。性能模式baseline/targeted，profiling capture→analyze；收益仅对应父P1K的三phase milestone，四场景formal需新精度gate。未实施新优化，不自动重新启用FA，不改原启动脚本。

阶段新基线及冻结比较随后保存；先解决历史Mixed不稳的证据缺口，再选择1个可证伪优化点。env001命令先保存并SHA绑定后执行，只创建快照和空闲克隆，不停止服务或发模型请求。

独立容器已就绪，快照 a6d57a99，四repo内容与实际editable安装完全相同，原生mountparity passed。唯一baseline/capture控制器源SHA `22f9967cba442d96405653e9e6dfd6c1354caf66337ee0e66d0a5b6b3a3294cf`，service helperSHA `141a5959836e07ee68932f85c75cc09c63663777c77c94efbe5fc5ad9a04e565`；当前脚本SHA0b638152，20项原样。执行前保存source精确进程/参数/有限环境、完整权重和tokenizer摘要；先graph两replay及C8，再Prefill6warm3measured/Decode6warm3measured/Mixed8warm3measured，固定末3throughput spread<=10%，所有measured保留。随后独立3phase capture各3round/2warm/lastprofile/max64iterations，两rank覆盖检查。没有提前选择候选/代码更改。该有界子周期终态finally停止独立模型，恢复原容器现役配置并等待ready；原服务重启使用当前已安装代码，不声称还原先前Python内存或旧gate。

V1在serverCLIhelp前置失败：错误清空Plugin使MetaXdevice不可识别；0模型请求、原832568未停止。完整25文件权重/tokenizer SHA已采集，v2仅核对其未变化metadata后复用；serverhelp恢复Plugin自动发现并用--help=all，不修改模型/平台源码。V2 workerSHA `5f934d4ca0ee1d549869dc7b34d3e2fa1d1f26d0b640165709aa11166e00c65e`，helperSHA `0b66fa34c0b8880e608fc179d61e0819a00a6d59fa04f25ff440a77a86206254`，计划/阈值/容差不变。旧终态SHA886bb580保留。

V2独立模型graph通过（两rank各GDN/WY/packed及>=2 replay，FG FA splitkv为0），但C8 runner路径不在旧评测容器挂载中，0 C8请求/0性能请求；属于measurement-invalid而非模型精度失败。原容器服务854491已同源码/原参数恢复ready。独立评测器 qwen36-fg20-eval-20261015 基于旧修正版评测容器快照c9443d6c（parent flageval:v1/62dac），保留旧映射并增加本案例映射，只影响评测容器；优化容器mount parity不变。任务源码全SHA相等，新runner可见SHA82cf6e83。V3先验证此可见性，捕获854491身份，再串行重开独立实例/graph/C8/phase/profile；所有旧失败和graph证据保留。V3代码不改模型/算子或数值参数，使用已验证同源码native20编译缓存以避免重复冷编译，不作为优化收益。

V3原模型停止已完成，但source-stop.json与v2重名；停止函数先执行后写回执，FileExists使控制器误判。854491现场为zombie，无新模型/C8/性能启动。V4只接管同一授权暂停窗口，先核验精确出生/无存活模型worker/端口空闲，预检所有后续输出路径，再用尚未使用的v3阶段产物路径继续；finally显式恢复源服务。修复为所有launch/stop回执在副作用前检查存在性，旧原件和失败不覆盖。workerSHA `647d4a77668d047ae7fe4fd02e91064b9315901618c00bc327fdb232338ea379`。

V4 nativeC8实际成功10doc/20filterrows，0empty/0garbled/0timeouts；sampleSHAe4776831由项目sample_validation再次只读验证。自写控制器str.splitlines错误拆分JSON字符串中的合法Unicode分隔符，造成JSONDecodeError，非模型或评测任务错误；原服务862147/1792073806.45已恢复ready，0性能请求。V5改用原有validate_sample_file（物理JSONL行、完整filter集合），不再维护自写parser；新实例仍按规范freshgraph/C8后测量。所有新输出独立v5命名，停止前检查回执存在性、停止责任预先登记，恢复函数对仍存活同源服务不重复启动。主变量/数值/20项/计划均未改变。

V5 fresh graph/C8通过：sampleSHA `da3128d6a0f896279cc078c66e36fa7b6183784fb18b96c2ec57cfba95f42c15`，10doc/20filter rows，0empty/garbled/timeouts；服务manifestSHA `f9078cffbbbb7ae33060fe4de390fbfcea3ab058ca3d0f8a3a7ef536277c8135`。这只验证最小回归与传输完整性，不是正式198题分数；sample的truncations字段只统计显式flags，不能据其0断言HTTP无触顶。

Prefill P1024/D1/C64/N128已完成6warm+3measured。测量轮总token吞吐分别5695.2623、5693.7046、5693.8251 token/s，中位5693.8251；平均TTFT中位8990.5956ms，p99 TTFT中位11727.2357ms。末3暖轮吞吐spread0.0477%，全部测量轮吞吐spread0.0274%，128请求/131072输入token/128输出token逐轮完整。原生run-record SHA `26656c7bfd5b1d7ed02f6914018f1da3a88ca97422dc2d673c68c2a089037e93`，路径为远端 `results/env001v5-baseline-E2E/env001v5-prefill/run-record.json`。首暖轮较慢保留；没有将暖轮计入测量。Decode/Mixed及trace尚未全部完成，暂不选择算子或声称收益。TTFT包括排队/网络/调度，不等于设备Prefill耗时。

后续Decode与Mixed的无profiler基线均完成。Decode P1024/D512/C64/N64的输出吞吐三轮942.5151、950.0955、950.4943 token/s，中位950.0955，spread0.8398%；平均TPOT中位53.8191ms，P99 ITL中位47.9076ms。原生record SHA `f777a33229974ffb566df640c3e20fea18a142f2e2ca5feab13b8608566c5702`。

Mixed P1024/D256/C64/N128输出吞吐三轮704.4797、703.8886、704.1775 token/s，中位704.1775，spread0.0840%；平均TTFT中位5802.1255ms，平均TPOT中位68.2106ms，P99 ITL中位1485.6886ms，P99 E2EL中位29457.6877ms。末3暖轮含664.5798 token/s，spread5.5811%仍满足原10%准入；8个暖轮及3测量轮均保留，不把历史不同配置数据混入。原生record SHA `8cba4b673d49edbd6d6bbf5a312c54c8d46865b9c50d8d4195948ea6f69197cf`。每轮128success/131072输入/32768输出完整。Mixed大ITL尚待trace归因，不据跨workload代理指标直接认定数值故障或GDN kernel根因。三阶段trace继续按既定计划串行采集；无新优化代码。
