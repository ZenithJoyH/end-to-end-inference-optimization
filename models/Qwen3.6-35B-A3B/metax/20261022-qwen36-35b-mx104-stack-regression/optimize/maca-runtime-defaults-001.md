# MACA SDK discovery and dynamic library defaults

用户要求修复每次手动export MACA_PATH/LD_LIBRARY_PATH的使用问题；当前明确授权是专用B容器内部基础SDK运行时配置，不改Docker Config.Env、不恢复模型/算子预设、不改共享Host、vLLM/Torch/Plugin/FGV/Gems/模型代码，不重启或发请求到用户当前opt3服务。

只读确认B40794ce/imagebf9、挂载只有/data与/public-flash；待修改/etc是容器私有可写层。Docker Config.Env=null，交互Bash自动激活Conda base但MACA_PATH/LD_LIBRARY_PATH都为空。mcPyTorch cpp_extension._find_cuda_home使用由MACA_PATH取得的MACA_HOME，缺失时os.path.exists(None)会失败；现有/etc/ld.so.conf.d/maca.conf已包含/opt/maca/lib，但缺/opt/maca/ompi/lib，ldconfig缓存无libmpi.so.40。SDK实际为/opt/maca→/opt/maca-3.7.0，真实MPI库存在。用户当前服务PID702104/start1146203102，8020/qwen36-35b-opt3，TP2/原启动argv；只读保护，不操作此服务或其他任务。

## 实施前冻结

- 新文件/etc/profile.d/maca-sdk-runtime.sh：仅当MACA_PATH未设置/为空时默认/opt/maca，保留用户非空覆盖。不设置MACA_HOME或任何模型/算子变量。
- /etc/bash.bashrc追加一次幂等source该文件：覆盖普通新交互Bash；登录shell原有/etc/profile.d机制也自动生效。已有终端需重新进入或exec bash一次。原root bashrc/Conda脚本不修改。
- 新/etc/ld.so.conf.d/maca-ompi.conf仅一行/opt/maca/ompi/lib；私有容器内ldconfig -X刷新缓存，不创建/改动SDK库链接，不再需要为MPI设置LD_LIBRARY_PATH。
- Docker直接exec某个binary不加载shell初始化；需要环境发现的这类执行采用bash -lc。不会用Python .pth/sitecustomize注入隐藏环境、不会重建Docker或修改Torch源码。
- 控制脚本先CASE/commands唯一归档与SHA，本地记录后执行；原配置和ld.so.cache备份到CASE/environment/maca-runtime-defaults-001，创建前核验owner/权限/可用空间/新目录不存在。
- 先保存无SDK环境时真实cpp_extension/MPI加载错误；再只读CLI/import验证新交互和登录shell自动发现、显式MACA覆盖不被改写、库映射实际来自SDK。原生vllm bench serve --help退出0/usage即可，不要求默认帮助列出--max-concurrency（历史观察误判保留）。无模型/HTTP/设备kernel性能测试。
- 修改前后完整当前package内容清单/当前API PID+start+argv+env摘要、Docker Env/mounts、共享用户启动脚本SHA保持一致。目标旧formal c2已被用户重启，当前opt3未做新gate，本环境维护不复用旧服务精度gate。
- 失败只按精确已写配置SHA恢复本次三文件和本次ldcache，不覆盖用户并发变化；所有失败/部分证据保留，绝不停止模型服务。

执行前归档控制器commands/maca-runtime-defaults-001.py SHAca8669149453de96d6a08821887842623d70d5d3b6fda04c86e8bdcb3959b152；Python及全部嵌套脚本AST/精确/proc NUL解析已核验。唯一命令以--execute-reviewed-repair显式执行。当前新目录不存在，case owner0/mode755可写，空间约15TB；只在私有/etc新增SDK默认和MPI缓存项，使用ldconfig -X避免SDK符号链接改动。执行器先快照配置/完整当前四仓源码/当前服务准确身份及env摘要，备份ldcache；两项无环境CPU失败取证后才变更。交互/登录/显式覆盖/MPI原路径/原生bench help五项都通过才保留；失败CAS回退仅自己写的配置。不改共享启动脚本、不启动模型、不发送HTTP，不采用历史精度gate给当前opt3重新绑定。

## 已完成验证

控制器native退出0，执行命令SHAba371c364c131ab925d77d97eaa2b2fa18492d8099622cea4aff835dc38a1bd1，report `environment/maca-runtime-defaults-001/verification.json` SHAdf853ce42e4af216ecfe4b40df708b5077b076f447b40b1d570d7e4fd0182f70。无环境基线真实cpp_extension和libmpi加载均exit1；修复后MPI、交互shell、登录shell、显式MACA覆盖、原生CLI help五项全exit0。交互/登录实际MACA_PATH=/opt/maca、LD_LIBRARY_PATH=null；MPI实际映射/opt/maca-3.7.0/ompi/lib/libmpi.so.40.30.6；用户非空MACA_PATH显式覆盖保持不变。

新增SDK profile SHAce85373e0381929b9925162427ea01a3602328e3d84a0a940d43ccf199d19183；新增MPI ldconfig项SHAc02bf401030cc7998ae748540abf41adf1a0cf10b7df37f67dde2d30f6154900；系统交互bashrc追加source后SHAde6e5dca9a96997913e6692ebaedf97a655afe92a5198cc9bda1e46ab07ca35d；只刷新缓存SHA3dad0cb098d3876e2515dc20e67108b7300d536a9f7aeb0d9a3310b8f8d1a37d。SDK链接、原MACA ldconfig项、rootbashrc和Conda初始化脚本未变；DockerEnv仍null、image/mounts相同、当前四仓+Torch cpp_extension+共享launcher共6560文件字节不变，opt3/API702104/start1146203102的完整argv/env摘要/cwd都前后一致。0模型请求/0服务重启/0kernel测试/无新gate。

当前终端需要重新进入或`exec bash`一次，以后新交互或登录Bash自动获得SDK根目录；直接Docker exec二进制不读shell配置，要执行依赖SDK发现的命令时使用`bash -lc`。这是用户本次要求增加的基础SDK shell默认，不是恢复已清除的Docker/模型/算子预设；不更改共享模型启动脚本（其显式export可继续工作）。

收尾前归档commands/maca-runtime-defaults-checkpoint-001.py SHA5fc2ea0160b6dbee4e5c0502d0cd139e567c3ee7d2b27202323934d40189216d；再次只读精确当前opt3和所写配置，GEThealth/models确认后备份/CAS更新continuation维护结论与当前用户服务观察。旧opt2/c2正式158分及gate保持历史有效产物，不把不同身份opt3伪装成旧gate已绑定；不启动新正式测试或性能。无任务监控需创建。

收尾checkpoint已exit0，命令SHA4712fd7ea140c1f1c63aae7ad53e1f7f3086b22f322535be85be0e1b50d95994；checkpoint SHA14aa4d602f0275b5ed70cc1658acb83144c8ab526e17b8cc3645477fe026e94a，continuation SHAe66ec1a14b8637f9c573cd858c1829628d1d792dc5b9d3dbe67eecfd132f79d1/phase maca_runtime_defaults_completed/current_jobnull。精确opt3进程与配置再次核验、GET health/models通过；current_service按只读观察更新用户opt3身份，没有伪造启动回执。旧c2/opt2分数和gate只保留原评测证据，不绑定当前用户重启服务。当前optimize/state、README、env-cleanup补充与必要acceptance当前观察已同步；无新history/monitor/完整精度/性能/提交推送。


## 2026-10-28 当前 opt3 组合精度复测

用户重启后的当前组合、实际prefix-on/GPU4/5/TP2，原生GPQA198/滚动C64独立通过**161/198=81.3131% >= 77.53%**。198唯一doc/396filter行/原prompt-target-args/无旧回答缓存/前后fresh源码一致，旧160/147/161/154逐题重现。验证：`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/accuracy/user-gpqa-erqa-c64-20261028-001/gpqa-followup-001/independent-verification-001/verification.json` SHA c9437b838bd089152dc01a11c3f32076e89941334e545a89b8f175606366ebb9。此为保留组合精度，不证明本点独立贡献，不与旧prefix-off不同配置计算收益。随后官方ERQA多模态C64发生FGV MoE临时cache13申请256MiB OOM，服务退出；GPQA已测通过分数仍有效，旧实例gate不可直接用于新实例/新参数。ERQA部分证据保留、完整400分数缺失，不自动恢复/补跑/性能。详见[user-gpqa-erqa-c64-20261028-001.md](user-gpqa-erqa-c64-20261028-001.md)。
