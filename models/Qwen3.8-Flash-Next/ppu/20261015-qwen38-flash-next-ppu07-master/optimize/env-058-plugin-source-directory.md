# env-058：将源码安装目录规范为/opt/vllm-plugin-FL

- 用户2026-10-21要求“安装的目录名字还是使用vllm-plugin-FL吧”。目标PPU-07容器`qwen3.8-flash-opt-ppu07-20261015`；新目录固定`/opt/vllm-plugin-FL`，仍使用editable源码安装，版本不变。
- 已只读确认新目录不存在且非symlink、父目录解析为/opt；当前绑定为`/opt/qwen38-plugin-eng055-final-20261021`。不覆盖任何同名目录，不删除旧源。
- 从已核验的eng055冻结源在容器私有新目录建立真实副本，保持业务代码字节；离线pip -e重新绑定，备份原editable元数据。旧目录保留作回退副本，不通过symlink假装改名。
- 不升级依赖、不改launch/ENV/数学源码，不重启8010、不访问8035/物理0–7、不推理/GPU测试、不提交推送；核新origin/direct_url/editable/CPU保护导入及8010身份/health/counters。
- 原始产物计划：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/env-058-plugin-source-directory-20261021`，排他目录与commands先保存。控制副本`/private/tmp/qwen38-plugin-path-058.CUSVBn`。

## 结果

已完成一次离线`pip install -e /opt/vllm-plugin-FL`。新目录为真实源码副本，非symlink；旧目录与原editable安装备份保留。版本仍为`0.3.0rc2.post1+ga696859b9.eng055.d20261021`，334份非生成版本payload与冻结交付一致，依赖及受保护源码未改。

- 默认解析与清洁环境CPU实际导入均为`/opt/vllm-plugin-FL/vllm_fl/__init__.py`，唯一distribution、原entrypoints、`editable=true`和`direct_url=file:///opt/vllm-plugin-FL`通过。
- CPU导入使用既有保护：3次可选设备属性探测在硬件访问前被拦截，CUDA未初始化、真实设备查询0，未调用Plugin注册入口。
- 8010身份和token counters前后不变，仍运行原eng053已加载模块；重启/新增请求/GPU测试/8035访问均0。源码路径切换不热重载在线模块，不产生新模型/graph/gate/性能结论，heartbeat仍暂停。
- `INSTALL_FINISHED.json` SHA256：`33b79441cf7fcd87b2af7ee842fd5e03844cf29fb9d8f046f88b888418a453b8`。
- `FINAL_REPORT.json` SHA256：`c9af8a884027d0305a34f59a44908ac7567bf35cf2f5cd97ac3e938593fa678b`。
- `FINAL_MANIFEST.json` SHA256：`0e8fc25d5b1f7e0a7de6ade72869ef88ef5bf79200d51c7eb2f30877f3d9eaeb`。
- `editable-install-before.tar.gz` SHA256：`7c7f0d95286d2774ba4aa17049c0ff0362ca6dcef2807852654122d9eea84aa5`。
