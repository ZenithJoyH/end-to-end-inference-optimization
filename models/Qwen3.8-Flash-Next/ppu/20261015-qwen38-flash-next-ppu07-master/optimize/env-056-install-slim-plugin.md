# env-056：将eng055精简Plugin正式安装到优化容器

当前安装形态已按用户后续要求由[env-057](env-057-editable-slim-plugin.md)改为源码editable，实际导入指向`/opt/qwen38-plugin-eng055-final-20261021/vllm_fl`；本记录保留前次normal-wheel过程与回退证据，不代表最新绑定。

- 授权：用户2026-10-21“你直接将你最终收敛的这个版本安装到容器环境中吧”。范围为PPU-07容器`qwen3.8-flash-opt-ppu07-20261015`内Plugin安装；不重启/停止8010、不访问8035/物理0–7、不发模型请求/GPU测试，不提交/推送。
- 输入：eng055冻结645文件树SHA`c505f298e69587fbf0d333dc5cb7b04308e2e814a121e6e97eaab1334b3b63f5`，3文件/+242/-10（生产+66/-3）；原410 CPU验证及旧同生产树eng053模型证据保持原归属。
- 预检：唯一挂载`/mnt→/mnt`，`/opt`和`/usr/local/lib/python3.12/site-packages`均在目标容器私有层；现有Plugin editable绑定`/opt/qwen38-plugin-pr455-20261019`，metadata版本`0.3.0rc2.post1+ga696859b9.d20261019`。未打印/保存完整环境。
- 外部产物计划：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/env-056-install-slim-plugin-20261021`，排他新建；本地控制副本`/private/tmp/qwen38-plugin-install-056.SnSIdl`。执行前保存脚本/SHA，安装前备份原Plugin RECORD内元数据/绑定文件并记录旧源。

## 安装设计与门禁

1. 从冻结eng055复制至未挂载的`/opt/qwen38-plugin-eng055-final-20261021`，不修改共享候选原件或线上eng053树。
2. 离线构建普通wheel，显式禁用vendor扩展构建、清除该子进程PYTHONPATH，使用`--no-deps --no-build-isolation --no-index`，不升级Torch/vLLM/FlagGems/FlagGems-vllm/FlagTree。版本标记为本地构建`0.3.0rc2.post1+ga696859b9.eng055.d20261021`，不冒充新上游release。SCM生成的_version.py单列为构建元数据。
3. 仅将该wheel通过pip正常安装到容器私有site-packages；不新增永久PYTHONPATH/sitecustomize，不更改start-model.sh/容器ENV/运行实例。旧editable源码不删，包绑定文件单独备份可恢复。
4. 新Python进程核唯一distribution/entrypoints、默认及清除PYTHONPATH后的真实find_spec、wheel→installed字节、依赖来源/版本不变。CPU包级导入只做无GPU初始化核验；屏蔽实际设备数量/属性探测，不调用Plugin注册或模型推理。若无法在该约束下完整导入，明确报告限制，不扩大资源范围。
5. Host前后核8010精确PID/start/argv/health、源及token counters不变。仍运行eng053的已加载模块，安装不等于在线服务已切换，不伪造新graph/精度gate。

## 结果

**已完成一次离线wheel安装，普通安装（非editable）**。唯一distribution版本`0.3.0rc2.post1+ga696859b9.eng055.d20261021`，新进程默认与清除PYTHONPATH两种检查均解析至`/usr/local/lib/python3.12/site-packages/vllm_fl/__init__.py`。生产包仍为eng055冻结内容；没有进入eng054扩大重构。

### 构建、安装与依赖

- 新私有构建源`/opt/qwen38-plugin-eng055-final-20261021`来自645文件冻结整树；原E055共享候选、旧editable Plugin、在线eng053、env041 Gems、安装FGVLLM main与PLE051私有源全量文件指纹未变。
- 使用现有setuptools80.10.2、setuptools-scm10.0.5、wheel0.45.1，禁用vendor扩展、离线no-deps/no-build-isolation；无新下载、无CUDA编译或其他包升级。
- wheel：`wheels/vllm_plugin_fl-0.3.0rc2.post1+ga696859b9.eng055.d20261021-py3-none-any.whl`，795884字节，SHA`66c4f9611cde25ea024eecf450561750485037f0338cf6b876eae23e7fa6c0ec`。335份payload到installed逐份SHA核验；冻结源的全部运行Python原样保留，仅构建自动生成`vllm_fl/_version.py`版本元数据。
- pip仅一次安装，正常卸载旧editable**绑定/元数据**并安装wheel；没有删除旧`/opt/qwen38-plugin-pr455-20261019`源码。新默认绑定无需Plugin PYTHONPATH。
- Plugin外9个包的版本、metadata来源/direct_url前后相同，FlagGems i64/randn、QSA M16、PLE i64+CTA源码保持。原容器ENV仍含旧Gems的PYTHONPATH覆盖；本轮未更改该ENV/start-model.sh，清洁导入检查明确unset它，不将继承旧Gems路径当新版本命中。

### 导入检查与初次核验工具问题

默认环境检查通过：新origin、唯一distribution、两个原vLLM入口`vllm.platform_plugins/fl`和`vllm.general_plugins/fl`均正确。随后清除PYTHONPATH做真实Plugin根包导入，静态选择thead、把设备可用性/数量设为无设备并拦截属性查询与GPU初始化；**未调用注册入口或模型**。

初版核验已完成import及version/entrypoint断言，却因把3次“已在硬件访问前抛错并由FlagGems安全fallback的可选属性查询”也算必须为0而退出。保留`VERIFY_FAILED`、原log/exit，不当安装或模型故障，不重新pip。v2只区分可选属性探测与禁止GPU初始化：3个探测均被拦住，真正GPU初始化/子进程/网络尝试0，CUDA未初始化，真实root import通过。该检查证明受保护CPU条件下导入，不是完整硬件环境/Plugin注册/模型启动通过。

### 回执与回退

所有产物在上述E目录，commands脚本执行前保存并核SHA：

- `INSTALL_FINISHED.json` SHA`f001935db946de3da7da9bdae9e627e30d9ac98f534e156a739fae5bcf9ef77a`。
- `verify-default-resolution.json`、`verify-v2-clean-import.json`、wheel/build/pip日志与前后包metadata/源指纹。
- `FINAL_REPORT.json` SHA`3b42f3989e0c947ea6a66b33693a41e9f1f59a9a2a137375072e484706ccbf0f`，`FINAL_MANIFEST.json` SHA`754c50ec12432fe2b585123329c6349becc25feb5c857638f1e551afe6663f0c`。
- 原Plugin安装RECORD内文件逐份备份于`plugin-install-before.tar.gz`，SHA`656c184c590b9f6cfedf2851c03eecbff8b6d55f22f46b1d1c478ff752cad488`；配套`plugin-install-before-files.json`保存精确绝对路径与SHA。源码未删，可恢复，不覆盖整个site-packages。
- 如后续用户要求回退，仅离线重绑旧`/opt/qwen38-plugin-pr455-20261019`（固定原metadata版本、no-deps/no-build-isolation、VLLM_VENDOR空、原绑定备份可核），不自动执行或触碰服务；未创建新容器/挂载/全局sitecustomize。

### 当前8010与结论边界

8010 API2441711/start521315854、argv SHA`c146e2da4762690185e9b3573c5f48796a5cb42aa2037de0d08d9ada40595010`保持，health200；安装前后及核验后running/waiting和prompt/generation token计数一致。在线进程继续已加载的eng053包与原PYTHONPATH，不将包安装误报为在线重载。

本轮0服务重启/停止、0模型请求、0GPU kernel或真实设备查询、0次8035访问，无提交/推送。安装与受保护CPU导入通过，**没有新graph/C1/C8/formal精度/性能结果或gate**。默认新进程安装绑定已更新；任何服务重载/推理仍等用户新方向，monitor保持PAUSED。
