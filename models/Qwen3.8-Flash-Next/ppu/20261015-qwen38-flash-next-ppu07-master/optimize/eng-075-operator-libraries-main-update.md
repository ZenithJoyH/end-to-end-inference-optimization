# eng-075 FlagGems与FlagGems-vllm主线更新

2026-10-29后续用户重启的新三库组合[acc023 C32 GPQA](acc-023-full-gpqa-c32-main.md)在MambaBuffers/get_mamba_groups规格断言失败后服务退出，尚无有效精度，ERQA未启动。异常当前落在框架缓存规格路径，无证据直接归因本算子库更新；保留源码和备份，不自动修复／重启／复测。

- 状态：retained，两个canonical源码已更新，CPU及独立回读通过；非性能实验，runtime / graph / accuracy / performance均not_run。
- 授权：2026-10-29用户要求继续更新当前容器两个算子库。PPU-07，qwen3.8-flash-opt-ppu07-20261015，仅/opt/FlagGems和/opt/FlagGems-vllm。保留现有修复；不重启／推理／GPU／8035／提交推送，不更改Plugin和启动脚本。

## 当前事实与方案

已完成：FlagGems master `04dafa8b9a84fee9887188d5e8d4a5403b264867`，FlagGems-vllm main `31a2705d75bceeacb222670abf819e2177f75a87`。标准路径及editable绑定仍为/opt/FlagGems和/opt/FlagGems-vllm，源码管理分别保留2／6处差异。index_put使用已合入PR6892的更完整i64修复；index/randn、PLE i64与CTA同步、MoE PPU拦截／空输入／原始权重布局及所有原测试保留，上游新增marker保留。QSA源未改，14个Qwen公开接口存在。Plugin／BF16／启动脚本／安装metadata均未改。

6,896份Python AST、19个既有MoE CPU mock case、diff-check和源码／测试保留性通过；这不是设备数值或实际命中证据。最终独立核6866／1140新源码成员、6640／1087原备份成员及第二完整备份、36项证据manifest全部一致。RESULT SHA0252947ed1dcfe7cdd47e6c4d1c53ca37bf91c77b6e25ae93320ef8605275b2a；manifest SHAcc3f1ba30842523bb9a7a6d2c32acf9f1fcd3d76e29eca365a0ab33d7a313b0d；CPU_VALIDATION SHAba9c3a2dc2578aaa78757c721368ff9f31b71afa9cd2a0a8bbe4eb5552997c20；CPU_CONTRACT SHA598172e8e7b24598a41833f7e9baf55560454d7805da0ab066d2cf35fb5f15ce。

回退原目录分别为`/opt/qwen38-eng075-operator-libraries-20261029/FlagGems-original-canonical`及`/opt/qwen38-eng075-operator-libraries-20261029/FlagGems-vllm-original-canonical`；额外source-backup与E中两份tar.gz完整保留Git/index/ignored/符号链接。当前8010仍未监听，0服务操作／GPU推理／8035／提交推送。未重装包或升级环境，pip标签仍为Gems `5.5.0.dev0+gf0aa7f121.env041`、FGVLLM `0.3.0.dev1`；Git HEAD和文件SHA才是本轮源码身份。format/pre-commit未安装未执行，不称PR就绪。

保留新源码等待用户方向；三库更新和eng073环境收敛后的模型最小回归、capture/replay、完整精度与性能均未验证，不复用旧acc021/022 gate，也不自动启动新验证。以下为原始执行前及中间审计记录。

连接检查ok3 changed0 failed0；容器running，仅/mnt bind，/opt私有真实源码。8010未监听。Gems HEAD f0aa7f12180cea4776a2aba3f3889b8fb82a28b1，有index/index_put/randn三处修复；FGVLLM HEAD b4d3382bb04da4e0ab444849697865b4d5fcd86e，有PLE、MoE alignment、thead原始权重布局及对应测试共六处。官方默认分支分别master和main。维护前保留完整Git/index/未跟踪/符号链接备份及patch，隔离候选fetch主线并逐项核对已合入修复，避免重复覆盖上游。

## 执行前记录

E=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/eng-075-operator-libraries-main-update-20261029；W=/opt/qwen38-eng075-operator-libraries-20261029。均新建拒绝覆盖。prepare.py本地/private/tmp/eng075_prepare.py，SHA9db8cfd3fe462d253db7b15664e80ea2b78b193d21701aaa06e4895f530f02b5，传入E/commands核SHA后在指定容器CPU执行。只在candidate更新Git，生产保持原样。原始源码／完整.git备份仅留目标机器，不跨环境复制。

## 验证和回退

准备完成：FlagGems master冻结04dafa8b9a84fee9887188d5e8d4a5403b264867；FGVLLM main冻结31a2705d75bceeacb222670abf819e2177f75a87（拉取期间官方main继续前进，以实际fetch为准）。完整归档SHA分别fcc453aeac157761c53dc4c9d78695bcbe924b95e26f06515d1f578d5ab9344f、c617c99f7d0a1183922eafd1a83472abed290f44d31d0b764ce5e79dc2ebcb71。原始生产目录未改。

上游index_put已通过PR6892包含完整i64地址扩宽，直接采用不重复本地patch；其余Gems两处、FGVLLM六处patch继续保留，测试额外保留上游新marker。merge_validate.py SHA0ed5e50d46bae27a5e6a6c7701d35de2ae0715c5bf6db7d93b27d3e04b040bf7执行前保存E/commands并核SHA；逐文件字节／AST保留检查、全库语法、diff-check、依赖入口一致检查和metadata备份，禁止真实torch导入。保留原ignored安装产物和历史accuracy_result.json。上游运行依赖／entrypoints无变化；PPU配置新INT8条目及新导出保留，模型路径验证not_run。库内AGENTS/workflow已阅读，本轮不开发新kernel、不声称G5/G6设备验收。

CPU语法、补丁保留与公开入口／签名检查通过后才记录并执行canonical替换；保留原目录和归档回退，失败不启动服务。用户未要求运行验证，不执行GPU／capture/replay／模型最小回归／完整精度或性能，不继承旧gate。现有修复归属保持ATen在FlagGems、vLLM融合在FlagGems-vllm，不迁移无关历史实现。

merge_validate首轮完成补丁合并、语法和保留性检查后，在metadata收集误用distribution名vllm_fl而失败；不是库代码或服务故障。保留首轮脚本／日志，validate_v2.py SHAa5b2050a5b28c21d01becc523b51bfd76d62fe288f30fb2b1c3b44fbfc7cd5c4改用真实distribution名vllm-plugin-fl，并验证已合并候选、不重复apply。当前setuptools80.10.2/scm10.0.5不符Gems构建依赖上限，运行依赖和editable入口未变化，无需为源码更新额外变更构建环境；保留原安装metadata与生成_version.py，Git HEAD和内容SHA作为新版本身份，pip标签仍旧build。

v2通过Gems6165／FGVLLM731份Python AST及diff-check，剩余本地差异分别2／6路径。原修复和测试逐字保留，只有fused_moe测试增加上游marker且其余AST完全一致。进一步复用现有MoE测试的19个纯CPU mock case，只抽取真实Python wrapper函数并使用stub kernel，不导入torch／Triton／设备；另核Qwen公开符号及QSA源保持。cpu_contract.py SHA3b82f27950b358d16ec13bb7632947f3ab0fb26ca9e317626143c9ee922d411d保存核SHA后执行，不能当设备数值或graph通过。

CPU抽取器首轮漏设测试要monkeypatch的HAS_TLE属性，在首次测试前退出；未执行设备。保留cpu-contract.log，cpu_contract_v2.py SHA3dbdf731d5197c9b996a382ebd5d3dc761ff4714cd3a61f0372fd60d01afdad4只补stub初始属性，原测试逐case覆盖它，不改测试断言或生产代码。

19个既有CPU mock case及14个Qwen公开API检查通过，QSA attention源字节保持。部署脚本deploy.py SHAd68e31bbd136d62c7f1a3c33a65bb0c7ea890a43e3fb40bc52b262f140e26030已冻结：再次核容器/私有挂载/8010未监听、原完整源码与备份/候选清单、Plugin/启动脚本/安装metadata不漂移；两旧目录分别rename到W/FlagGems-original-canonical及W/FlagGems-vllm-original-canonical，candidate替换对应canonical。第二项rename失败立即恢复全部已移动目录；无安装／服务动作。替换后核完整源码／备份／clean editable origins及metadata，保存RESULT/manifest，之后独立回读。
