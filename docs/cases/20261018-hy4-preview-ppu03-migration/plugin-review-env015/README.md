# env015：直接调用 FGV triton_scaled_mm

已部署到PPU-03 / hy4-preview的实际安装源码`/workspace/vllm-plugin-FL/vllm_fl/quantization/w8a8/linear.py`。本轮只有这一个文件变化，两个执行入口都函数内直接`from flaggems_vllm import triton_scaled_mm`并调用该函数；删除scaled_mm别名、FlagGems导入及此处的环境变量选择，遵循用户最新明确确认。其他算子的环境变量逻辑不变。

原dynamic_per_token_quant_int8 CachedOp、PPU opaque custom op/fake、权重/scale/bias/out_dtype不变，没有重新引入int8_scaled_mm dispatch、注册或包装文件，Plugin测试仍与官方一致。真正使用此W8A8 kernel时需要FGV，缺包明确抛错，不静默fallback；模块导入仍不提前加载该可选库。两gems-opt源码/分支/clean及tracked摘要均保持固定FGV46387d7f / FG3ba1d1d9。

本轮单文件diff（历史路径当前不可用：`/tmp/hy4-direct-triton-mm-20261019-01/from-env014.patch`；须从原 revision 或远端证据恢复） · 相对官方完整diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env015/full-diff.md`） · 完整Git补丁（历史路径当前不可用：`/tmp/hy4-direct-triton-mm-20261019-01/full.patch`；须从原 revision 或远端证据恢复）

官方基线8b2033e417a535a828a1d7594d36bd33e36e3b57；完整11文件（6新增/5修改）+1139/-6。补丁SHA256 `e44e8b8ae4e6a11a99bdb7d57ad8edc13fe30ac869a014f8eb2d4f95ce363843`，单文件delta SHA `6aacba6e75104e0dc5180bd5b2d50aad64995e57e525d8f5f08bfb8346ef4d54`；部署后615文件清单与候选一致，tracked mode/symlink不变。原始补丁、回执、备份及命令保存在`/workspace/.hy4-preview-migration-20261018-01/direct-triton-mm-20261019-01`。

语法、两基准strict git apply、Ruff F及7项隔离AST导入/参数契约通过：env0/1下opaque、PPU apply和非PPU apply均选择FGV，FlagGems不参与矩阵乘，缺FGV不fallback；原量化CachedOp/fake/权重处理AST不变。仅stub/static证据，无真实算子/硬件运行，不代表关闭环境变量后整个HY4服务已兼容。

未重启服务、未发模型请求、未开始评测，原service07身份前后相同；新源码启动/graph/分页/精度仍待验证，旧env011证据不绑定本版本。87%完整198题GPQA gate未签发，heartbeat仍暂停。BF16 Indexer及parser本轮未改；BF16方案的唯一/最小必要性未证明。无性能提升声明，PR readiness待模型验证。

单文件备份plugin-env014-before.tar.gz，SHA `151b293a3556b0d5f511ff0ec8a243284ab3bcaaec3a1522b3ddf56c266a436a`；commands/rollback.py只恢复本轮linear.py且校验后续修改，不操作服务。
