# env-057：按用户要求切换最终Plugin源码editable安装

后续目录命名已由[env-058](env-058-plugin-source-directory.md)调整为`/opt/vllm-plugin-FL`；本轮旧源码与原始回执保留，不代表当前默认安装路径。

- 用户2026-10-21明确要求“需要用源码安装的方式安装到容器中”；本轮用已有最终源码执行`pip install -e`，不再普通wheel安装。
- 目标PPU-07 / `qwen3.8-flash-opt-ppu07-20261015`，私有源码`/opt/qwen38-plugin-eng055-final-20261021`；版本保持`0.3.0rc2.post1+ga696859b9.eng055.d20261021`。源码解析与pyproject存在已只读核验。
- 安装前普通wheel绑定在site-packages，原env056证据保留；本轮仅切换Plugin安装模式，不改业务源码、依赖、launch脚本或容器ENV，不重启8010、不访问8035/物理0–7、不发推理/GPU测试、不提交/推送。
- 新原始产物：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/env-057-editable-slim-plugin-20261021`；本地命令副本`/private/tmp/qwen38-plugin-editable-057.7wMPIS`。排他创建，命令先存再执行。

## 门禁与验证

1. 核源目录与site-packages均在目标容器私有层，冻结运行Python源、依赖身份与当前normal安装RECORD备份；旧wheel文件仍可回退。
2. 固定版本、离线`pip install --no-index --no-deps --no-build-isolation -e /opt/qwen38-plugin-eng055-final-20261021`，构建子进程unset PYTHONPATH/VLLM_VENDOR，不执行vendor扩展编译或升级依赖。
3. 新进程核唯一distribution的`direct_url.dir_info.editable=true`、URL精确指向源目录，find_spec和受保护CPU导入均指向源码而非site-packages拷贝；原entrypoints、业务字节保持。
4. 延用已明确区分的CPU导入保护：设备属性查询被拦截且允许库走安全fallback，实际GPU初始化/子进程/网络均禁止；不调用Plugin注册/模型。前后仅核8010身份/health/counters，不查询其他服务。

## 结果

**已完成一次源码editable安装**，直接执行离线`pip install -e /opt/qwen38-plugin-eng055-final-20261021`，未再做普通wheel安装。PEP660构建过程内部的临时editable wheel只是pip实现细节；最终代码从源码加载，已同时以find_spec和真实根包导入核验，不是site-packages中的拷贝。

### 实际安装与验证

- 新进程默认环境及unset PYTHONPATH的实际`vllm_fl.__file__`均为`/opt/qwen38-plugin-eng055-final-20261021/vllm_fl/__init__.py`。
- 唯一distribution版本保持`0.3.0rc2.post1+ga696859b9.eng055.d20261021`，`direct_url.json`精确为`{"dir_info":{"editable":true},"url":"file:///opt/qwen38-plugin-eng055-final-20261021"}`；原两个vLLM entrypoints不变。
- 334份非版本元数据payload与原eng055/wheel指纹相同，私有源/冻结eng055/运行eng053、Gems、安装及PLE051 FGVLLM源指纹不变；仅允许构建生成_version.py。没有修改业务代码或依赖版本/来源。
- 原普通wheel的包文件与绑定已备份后由pip正常卸载，替换为editable finder/metadata；没有删除最终源码或旧实验。无新永久PYTHONPATH/sitecustomize，原容器Gems PYTHONPATH仍未改，清洁导入显式unset它。
- 受保护CPU真实根导入通过：3次可选属性查询被访问硬件前拦截并fallback，无实际GPU初始化/真实设备探测/网络/子进程；没有调用Plugin注册或推理。不能由此宣称新服务/graph/精度通过。
- Host核验8010 API2441711/start521315854及argv SHA`c146e2da4762690185e9b3573c5f48796a5cb42aa2037de0d08d9ada40595010`不变，health200，running/waiting与prompt/generation token计数前后相同。现有8010仍已加载eng053，不是热重载；将来新Python进程会按editable绑定读取源码。

### 原始证据与回退

E为本记录开头所列env057远端目录；owner0、创建时可用约6.97TB，未改变容器挂载。脚本在`commands/`执行前保存，`pip-install.log`记录唯一安装，`verify-default-resolution.json`及`verify-clean-import.json`保留实际导入证据。

- `INSTALL_FINISHED.json` SHA`a75dce4158f3bbdfa7f1aa7257bb9170c2156f932a0df31c48390bdd991fb3b9`。
- `FINAL_REPORT.json` SHA`7590c32a240cd6e8ddb9b18e86548bd4654544a5df2c4b0e319a1730cb91864d`，`FINAL_MANIFEST.json` SHA`a8f14b501843a3c2d2dbb9a97b328191b036ea8359edaf3f5cbd0d16ef5031fa`。
- 原normal安装RECORD文件完整备份`normal-install-before.tar.gz` SHA`5f886e5fc4b3f2ac1d8e4070fa054031e7b02347a9d37ec65aa929b598a13574`，配套精确路径/文件SHA；原env056 wheel也保留。如用户要求回退，可仅离线重装该旧wheel，不覆盖整个site-packages，不自动执行。

本轮0服务重启/停止、0模型请求、0GPU测试/实际设备查询、0次8035访问，无提交/推送。FP32/i64/QSA M16/PLE保持；源码安装通过，新模型/graph/formal/性能均not_run，无新gate，monitor保持PAUSED。
