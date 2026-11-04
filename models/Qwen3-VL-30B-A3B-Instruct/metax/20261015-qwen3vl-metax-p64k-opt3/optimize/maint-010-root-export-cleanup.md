# maint-010：清理根目录冗余算子导出项

用户追问为什么ops已有公开算子声明，根目录还需要添加。实际导入链为：ops/__init__.py导入generic API并列入ops.__all__，根目录已有`from flaggems_vllm.ops import *`获得名称绑定，runtime替换为vendor实现。根目录__all__仅控制外部`from flaggems_vllm import *`，当前Plugin的显式`from flaggems_vllm import apply_top_k_top_p`不依赖它。因此此前给根目录补新条目对当前调用是冗余，本轮移除这一条，保留根目录原有helper列表和ops/backend导出。

用户给出的`/public-flash/jinghao/qwen3-VL/FlagGems-vllm`与当前验证容器实际使用的`/workspace/FlagGems-vllm`不是同一文件（不同device/inode），虽当前两文件内容相同。本轮仅清理已授权、已验证的独立容器qwen3vl-p64k-opt-20261015实际导入副本，不回写用户给出的共享路径。

变更前保存根文件及四仓库内容指纹，断言当前根文件仅比HEAD多这一条；移除后根文件逐字等于HEAD。其余源码、已删除测试状态、Plugin调用及配置保持。新进程验证显式API和MetaX实现绑定、Plugin入口；原8111进程就绪，不执行新kernel/数值/graph/性能测试，不重启服务。命令/备份和结果位于远端案例commands/maint010-root-export-20261016与results/maint010-*，完成后补state。

已完成：根文件恢复HEAD原文，其余三仓库及本库其他文件未改，用户共享路径SHA保持。新进程显式导入成功，仍为MetaX库算子，Plugin绑定正确；8111同一实例就绪。清理回执SHA256 `959d45f3ae4443cf217cfc6a7ba781d951dc3701594383665e085e91a9f7fa00`；验证回执SHA256 `b3b81e257efdf343efe4ccd14a0e93b9b2e32763f22b564b0d8bd69ec962005d`；更新清单`manifests/maint010-service.json` SHA256 `67c1755eca2017ee90f943c843f90fa3c05260c7a04326ae6f9334426611e402`；索引SHA256 `37cc11791b6fbc526026be3a53cc16e42a4e1cb5ea35aaa4653faec79e2106d6`。成功远端验证输出已回写state，重复本地JSON收集因SSH延迟停止，不影响已完成操作或远端原始证据。
