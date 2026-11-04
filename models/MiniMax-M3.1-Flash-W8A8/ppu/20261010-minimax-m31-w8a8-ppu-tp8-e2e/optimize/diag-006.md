# diag-006 FlagTree 最新 PPU 版本与 MoE TLE 支持

用户于2026-10-13明确允许更新优化容器中的FlagTree，验证当前TLE路径。目标仅为PPU-07的minimaxM3.1-opt-20261008私有安装；不改变源适配容器、vLLM、权重或根启动脚本。

当前实际版本0.6.2a1+ppu3.6；官方release列表最新0.7.0+triton3.6，对应缓存的官方PPU wheel 0.7.0+ppu3.6，SHA98fa0c4488e06c904adfb55a8059ef64f2c1bddf5938f6faa7edfc8650dead09。官方来源：https://github.com/flagos-ai/FlagTree/releases 。此前该wheel的M8 dot测试仍失败，与本次TLE能力问题分别记录，H16绕行保留。

先在空闲PPU8的新进程中隔离加载新版，不改变正在进行的op-004完整198题精度环境。直接调用FV的MoE alignment cooperative TLE kernel，固定E128/top4/block64，覆盖M1/8/64/1024/8192及路由偏斜，使用CPU路由集合/专家归属/填充计数作为oracle，graph capture与两次replay。通用入口静默fallback不算通过；cluster路径须独立验证硬件与remote能力。明确编译失败即记录unsupported，不以随机重试或修改白名单绕过。

GPQA结束、无客户端后才可更新私有系统安装；原安装文件和发行版元数据必须在远端完整归档，可原样恢复。升级后的精度gate需重新生成，旧编译器score不能rebind；原P1迁移对照也不得混入编译器变量。生产启用TLE还需要模型最小回归和同配置端到端比较，孤立编译成功不表示收益。

当前状态：隔离probe准备中，尚未更新生产安装。

## 实测结果与决定

旧版和官方新版都进行了直接JIT调用，移除LibEntry/LibTuner装饰器，仅固定现有kernel launch参数，没有经通用入口fallback。M1/8/64/1024/8192分别均匀和偏斜路由共10组，每版全部在TTIR编译阶段报NotImplementedError：`unsupported TLE feature on the 'ppu' backend: tle.distributed_barrier`。未运行数值或graph，因为kernel未编译；不能说这些验证通过。

已核对新版实际import指向案例package/triton，发行版0.7.0+ppu3.6；compiler.py与tle_supported.py逐字等于官方wheel，排除隔离包历史修改。compiler.py的PPU_UNSUPPORTED_TLE_OPS明确列出distributed_barrier和remote，注释说明缺少lowering。Python primitive支持清单虽列barrier，但不能代表后端lowering已支持。810E capability8.0使现有cluster capability gate=False，且remote同样被编译器拒绝；没有强行绕过硬件gate运行cluster。当前GitHubmain代码同样存在拒绝逻辑，仅做公开源码核查，未build/硬件验证main。

对照结果：baseline SHA0a96f4b8ae1ce836e2876ff5af1e36d22513bd8ba28913e3c6bda0262a4656ee；latest SHAf62472da8ffaf0b6a211595fdd8362b589a91b58cf557342de7160ba1dde4927。capability-review：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261010-minimax-m31-w8a8-ppu-tp8-e2e/profiles/diag006-tle-01/capability-review.json`，SHA20c0f7ba0464c9d270a9d210373fd24cf7673c71cbc948b947fe2c81800a51ef。保护回执证明原服务身份/启动脚本/四仓库源码均未改变，PPU8已释放。

本次已在目标容器独立进程中加载官方新版完成支持验证；新编译器未晋级全局安装，现有四阶段PPU实现继续使用。升级版本本身不能解锁当前TLE路径，不新增性能收益。op-004完整GPQA继续原环境，最后只读96/198，原生exit尚未产生，尚不能发布迁移后精度分数；后续Matched P1及正式四场景仍未完成。
