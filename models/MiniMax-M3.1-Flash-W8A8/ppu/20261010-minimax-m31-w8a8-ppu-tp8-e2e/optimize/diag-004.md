# diag-004：FlagTree 上游问题报告及最新版核验

用户明确授权向flagos-ai/FlagTree创建issue并核查最新版本是否修复。当前生产仍是Plugin H16 padding绕行，编译器未修改。复用diag-003生成IR及A-only因果证据，公开内容仅独立合成矩阵，无私有模型/目录/评测/机器身份。

截至本轮，最新相关发布为0.7.0+triton3.6，官方PPU指南使用flagtree0.7.0+ppu3.6；main固定69148faf...。API releases/latest指向较旧0.6.0，与完整release列表有冲突，采用完整发布时间列表和当前官方PPU指南，记录此差异。当前目标安装0.6.2a1+ppu3.6。尚不能以版本号或没有搜索到issue认定修复。

计划在原优化容器的新独立Python进程、空闲PPU8使用案例私有目录里的官方最新版wheel，保留系统安装/服务/根脚本/源码；同一公开repro先测原版再测隔离新版，分别保存实际import/发行版/编译IR/数值结果。如下载或兼容性阻塞，报告未硬件验证，不伪称已修复。所有命令先归档后执行。

## 官方最新版硬件复测

已完成同设备、同公开脚本的0.6.2a1+ppu3.6与0.7.0+ppu3.6对照。新版实际导入案例私有package/triton，未替换系统安装。两版M8/BLOCK_M8 random相对L2均1.006577/maxabs37.84861，onehot相对L2均1.061466/maxabs2.703125；两次eager和graph两次replay均复现。M4、M16、M8补齐16均通过，random相对L2约1.4–1.6e-7，onehot精确一致。官方最新PPU wheel未解决该问题；main HEAD仅源码核查，未编译/硬件验证。

结果目录：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261010-minimax-m31-w8a8-ppu-tp8-e2e/profiles/diag004-latest-01/`。review SHA464af577f88750e98d3b8a47b4a7320a6549dbc2888c69113265fb3aaa24aae8；baseline-result SHAd8abda6ce7e6880b8ceee4dea5897ba10f6dc7d94258fd6ebd9151055f32f0b2；latest-result SHA7f5c5475f939f18def8c9414433d974c6db41e1244cf85f152697b80d25c3357。wheel SHA98fa0c4488e06c904adfb55a8059ef64f2c1bddf5938f6faa7edfc8650dead09。控制回执确认生产服务/四仓库源码/根脚本保持，诊断设备退出后空闲。

## 上游报告准备

用户直接授权公开issue。报告只含合成矩阵复现、公开版本/硬件、数值结果和短IR因果片段，不含私有模型路径、主机/容器身份、评测数据或原始debug路径；明确IR干预在旧版完成，新版只做相同数值复测，未宣称已修复C++源码。提交前归档命令JSON：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261010-minimax-m31-w8a8-ppu-tp8-e2e/commands/flagtree-issue.json`，SHAcc4925b5382cc990ddec2a90da7faee07538f04a7938ecbb1e448ea61d26a48e；正文SHA15bd04ae8fb9544edabe47e5a0e2dc7e774e640c0898e849507ac9fbe5437827。

## 提交回执

已提交并通过GitHub原生fetch核验：[FlagTree #1350](https://github.com/flagos-ai/FlagTree/issues/1350)，Open，创建时间2026-10-12T04:17:18Z。发布标题/正文与事先归档JSON逐字一致。GitHub connector写入返回403 Resource not accessible by integration，未创建；使用已有登录浏览器会话完成，未调整账号/集成权限。提交回执归档`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261010-minimax-m31-w8a8-ppu-tp8-e2e/commands/flagtree-issue-receipt.json`，SHAc33e45ca2e675821e752111636c267b6cf1c18e03bbe7a4e5e76562eac196565；截图`/private/tmp/flagtree-issue-1350.jpg`。

本子任务完成：报告已提交，最新版正式PPU wheel仍有错误。生产继续保留fix-001 H16 workaround；编译器源码未修复。没有新的模型GPQA或端到端性能验收，也不把issue提交作为整体优化完成。
