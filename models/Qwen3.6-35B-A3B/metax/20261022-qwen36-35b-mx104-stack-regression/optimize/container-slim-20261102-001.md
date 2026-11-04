# 当前B容器瘦身

- 状态：已完成清理与内容指纹校验。
- 用户请求：清理 `qwen36-35b-regression-b-20261022`，给容器瘦身。
- 范围：mx-104、当前B私有可写层；不改变模型服务参数或源码，不启动模型或评测。
- 远端产物：`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/environment/container-slim-20261102-001`。

## 依据与范围

2026-11-02只读核验当前B容器ID40794ce，镜像bf9f76b；仅`/data`与`/public-flash`两个共享挂载，容器可写层26,050,981,888字节。容器运行但没有模型/编译/安装进程，仅交互shell。continuation当前job为空，旧ERQA思考轮次已失败、暂停状态不改变。

大项：FlagTree源码构建目录14.73GB，其中build7.31GB、dependency-cache5.17GB、triton-build-home1.14GB；pip缓存1.56GB；两份旧编译器验证/诊断安装副本共1.84GB。当前FlagTree从容器外冻结wheel正常安装，import与动态库依赖落在Conda site-packages，不依赖上述构建目录。其他四组件仍editable，全部保留实际源码。

## 计划与保护

执行前归档唯一脚本与SHA及路径清单。先保留两份旧编译器副本的完整压缩回退档，再清理明确的构建中间目录、下载缓存及两份冗余验证副本；不修改已安装包、MoE/GDN/采样/KV预算源码、SDK、启动脚本、模型和原评测/故障产物。保留当前TorchInductor、vLLM和Triton运行缓存，避免本次瘦身触发大规模冷编译。

清理前后核验实际导入位置/包版本、全部当前推理源码与已安装Python包内容指纹、动态依赖、容器ID/挂载及服务空闲状态；检测到服务/编译任务启动或路径不符立即停止。不执行全量精度/性能或新GPU请求，不宣称旧编译故障已修复。保留原镜像不变，删除原镜像层文件不能回收镜像本身大小。

## 结果

已执行一次并exit0。Docker SizeRw从26,050,981,888降到10,139,402,240字节，减少15,911,579,648字节（15.91GB，61.08%）。六个目录du分配空间合计17.01GB，与Docker SizeRw口径不同，不能把17.01GB冒充实际可写层回收量。镜像层不变，容器根文件系统的共享镜像内容不在本次回收范围。

59,535条受保护记录前后SHA完全一致，当前包版本、导入spec、原生Triton动态库依赖均保持。三个运行缓存du分配空间合计11,523,571,712字节，清理前后一致。完整保留模型/全部评测与故障证据、当前优化及原source checkout。无服务/模型/评测/编译任务操作，旧暂停状态继续。

两份旧编译器副本回退档位于远端本实验目录`redundant-compiler-copies-before.tar.gz`；如需恢复，可按成员清单恢复到B私有`/opt`，无需改包安装。构建/下载中间文件日后需要源码重新构建时再生成；当前源码、源包和已安装wheel保留。

正式验证报告 `verification.json` SHA `068b221e4721ea0141be6b0f56f945b263023ce6af65b7a7709df90fa58d5202`；执行命令SHA `b159ac3e39e719d91c685f2fd0fe57c24e948468a437422e49a884fcca9a6a39`。本次仅存储维护，不作为模型精度/性能回归，不表示此前MetaX编译错误已解决。

执行入口 `CASE/commands/container-slim-20261102-001.py` SHA `c9eeacddc34ba2f3554588eb42baa210d8ed41017f852b0ffb43fd60ef57cf0a`。`--prepare` 仅生成清单、完整保护指纹和压缩回退档；`--execute-reviewed-plan <planSHA>` 绑定已审阅清单、一次性执行、每步新核验空闲及身份。该入口不接收任意删除路径，不执行包管理器或服务命令。

准备已exit0，命令SHA `9568d1a7a52ea452ab43c2803f1ad611a61f163d10f85e6169c4e96dd0637e70`。冻结planSHA `7821becc04bf142901a80a49e5bd1f2ee4a4d217199c8bce1f713dac17da9976`，六个目录分配空间合计17,014,738,944字节。59,535条源码/安装包保护记录（内容7,340,729,212字节）SHA `bfecc4b21963827eeab5ae67cbc2e889d6e5c2f36bfd7c07345ce5b60f274217`；容器外632,034,279字节回退档SHA `2fe3a9f308e6d8d5097943a64ab30383f88b673b2bfe8ca1609f56addcd9826f`，tar完整可读。实际spec与ldd均不依赖待删路径，原安装wheel SHA7b839254保持，开始一次性执行此plan。

清理后真实导入检查exit0：Torch、Triton原生C++扩展、FlagGems、FlagGems-vllm、vLLM与Plugin全部可导入，实际路径保持。报告`import-check.json` SHA `3065d70ebe9fe51831dcf6d5e39abc117d4d44ba77044607a5114e9f98dcbc11`，命令SHA `834b8b0fee5f27309629be15fc053f8c679250d8085e826533ab1e66719f36b6`。没有模型请求或GPU计算测试。
