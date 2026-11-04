# maint-009：采样测试/perf清理与导出说明

后续[maint010](maint-010-root-export-cleanup.md)进一步确认根目录新增API条目对当前显式导入冗余，已在实际导入私有副本撤销该一行，ops/backend导出保留。本页记载清理test/perf时的历史状态。

用户询问FlagGems-vllm顶层`__all__`的作用，并要求删除新增test/perf文件。当前HEAD f6fdb9b原本已有SUPPORTED_FP8_DTYPE、enable、only_enable、use_dnn/use_gems及注册查询函数的列表；本任务仅加入`apply_top_k_top_p`一项，未新增整段列表。`__all__`声明通配符导入的公开名称，本身不执行或注册算子；显式`from flaggems_vllm import apply_top_k_top_p`只要求包内已有该属性，不依赖顶层列表。通用ops与MetaX ops的既有导出链仍需保持，故本轮不改任何导出声明。

清理限定mx-59当前独立容器`qwen3vl-p64k-opt-20261015`内FlagGems-vllm的两项未跟踪文件：`tests/test_top_k_top_p.py`和`benchmark/test_top_k_top_p_perf.py`。先备份并校验，再删除；保留算子实现、Plugin调用与其采样路由测试、MoE JSON、gems-opt和sort。不会重新增加用户先前删除的MoE测试。

这是测试资产维护，不修改运行代码，不重启服务或重复设备数值/性能测量。验证清单/备份SHA、四仓库除目标文件外的指纹、显式导入及MetaX API来源、既有8111服务身份与readiness。此前49项算子测试是删除前的历史回执，不代表文件仍保留。

命令和原始证据位于本案例`commands/maint009-sampling-artifacts-20261016/`。两个文件已备份删除，四仓库内容比较确认只移除这两项，运行代码、导出声明及Plugin均未变。新的显式API导入通过，解析到库MetaX算子；Plugin入口仍为MetaX patch，8111同一进程就绪，没有执行kernel、重启或新数值/graph测试。

清理回执`results/maint009-cleanup.json` SHA256 `a8f2773625d0c2f4a03365cd327f2e5549c6ef2e3f4c2ef290171fbd6b31fbd4`，验证回执`results/maint009-verification.json` SHA256 `49072d4a9380b753051df9d8426ae240f39c9ec80ee4a3044d3e38474cb9e1de`。更新清单`manifests/maint009-service.json` SHA256 `80d7d05c84dd5671fa000d6daa15670237d983ee38beb562c2864cc1727537ee`引用op008原运行实例/graph证据，并明确只有测试资产变化；不签发新的正式精度gate。索引SHA256 `963ebd41f2c605e921d1124d55e10b7c5cb1d2cf13676113829c63fc2d9c9ca4`。完整命令SHA与备份位置见state。

用户明确要求删除库内新测试/perf，优先于仓库新增算子通常需保留测试/benchmark落点的规范；历史验证保留在案例外部产物，PR状态仍为experimental。本轮保留Plugin采样路由测试，删除范围为用户当前指定的FlagGems-vllm库。
