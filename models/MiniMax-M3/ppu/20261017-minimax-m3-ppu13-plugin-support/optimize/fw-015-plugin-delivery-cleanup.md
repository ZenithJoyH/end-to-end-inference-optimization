# fw-015 Plugin 交付范围清理

状态：已完成，用户明确要求移除本轮新增测试文件及thead.yaml修改。不是性能实验，不重启服务，不重新评测。

后续：fw-016已由用户明确要求另行重启并通过最小回归；当前组合的[accformal-006](accformal-006-ppu13-gpqa-c64-60k.md)全量GPQA已完成，strict-match 179/198=90.40%≥88%，gate复验通过，14条60K截断单独记录；本文件清理时的历史验证边界保持不变。

目标为PPU-13 `minimaxM3` 内实际安装的私有源码 `/workspace/vllm-plugin-FL.support-minimaxM3-refine001-20261017`，HEAD620892ab。仅移出新增的 `test_biased_sigmoid_router_contract.py` 和 `test_minimax_m3_lifecycle.py`；将 `vllm_fl/dispatch/config/thead.yaml` 恢复该HEAD原文。保留3个源码文件中的路由dtype/边界、worker patch时机修正，不动原健康checkout、其他算子库或共享源码。

执行前保存commands、被移除材料备份和原diff，远端目录为 `/mnt/nfs/users/jinghao/minimaxM3/20261017-minimax-m3-ppu13-plugin-support/cleanup-001`。检查新增测试清单恰为两项、yaml补丁可应用、变更后yaml与HEAD相同、其他3个源码SHA不变及diff空白检查。

执行结果：两项新增测试已移出Plugin仓库，原有测试未删除；thead.yaml与HEAD逐字节一致；其余3个源码文件SHA不变，git diff只剩这3个源码文件，无yaml或新增测试。Python AST及git diff空白检查通过。未重新安装、重启或发起评测。

材料可恢复：`backup/removed-tests/`及`backup/removed-files.tar.gz`保留两个测试和清理前yaml；tar SHA256 `1ae7fe52f099c7445bc3b897b2d0d0c75d7aade071002bc66c1d781a6225ad2f`。干净交付补丁 `checks/candidate-clean.patch` SHA256 `468e5432772c16c36279734978e7dbe4a132768742fb239e6bd99f15723b4507`。生效脚本 `commands/cleanup-delivery-001-v2.sh` SHA256 `38885df5135ca40fc73c1b36f615c1d3b84c1d665011e763a61a9c770e58819c`；首版未向docker传递stdin，未改变源码，修正为`docker exec -i`后执行成功，未覆盖首版。

注意：撤销yaml后不再有本轮恢复的conv3d/cudnn_convolution黑名单。此前原样配置曾在conv3d autotune启动阶段长时间未ready；本次遵从用户要求清理配置，不自动重启尝试。已有运行实例保持原进程内状态；旧10/10结果仅属于清理前版本，不能证明新磁盘配置启动正常。完整精度和性能仍未测。
