# env-003 FlagGems-vllm 更新并确认 topk_sigmoid

状态：installed，导入与接口核验通过；硬件计算、graph、模型推理和新组合正式精度未测。用户于2026-10-18明确要求更新FlagGems-vllm，以获取新版本的topk_sigmoid。本轮仅当前PPU-13/minimaxM3容器依赖更新，不修改Plugin、不提交或推送代码、不重启或新启模型服务，不运行正式性能或GPQA。

## 当前事实与范围

容器fad201d7b6ec、原有/mnt和/data挂载未变。旧editable路径`/workspace/FlagGems-vllm`，HEAD `1f9ac0e0caf3c32111f6be44c8e4d2fef2359546`为本地完整快照；两个未提交文件为packed SwiGLU实现及测试，diff SHA256 `1acdb40e31b333fd29328574160265fa6051c5b6e7498e7a38d65f418a38a764`。更新前原模型PID30544不存在，8024拒绝连接，容器内无vLLM服务进程；这是更新前现场，不由本轮停止。

官方origin `https://github.com/flagos-ai/FlagGems-vllm.git`，默认main，冻结更新目标`46387d7f96050204c1b932f35680a3ea03896fa6`。实际源码已有topk_sigmoid及ops导出，CUDA device门禁、E≤256、k≤min(32,E)、连续输入、FP32权重/bias、int32/int64索引；PPU是否正确执行仍需实测，不把源码存在当作硬件通过。新main已有独立MiniMax预处理实现，但无swigluoai_uninterleave；保留旧实现及其未提交修正并补导出，不覆盖新main的预处理算子。不改FlagGems、vLLM、Plugin或权重。

## 执行计划与回退

在原案例下新建唯一外部目录`/mnt/nfs/users/jinghao/minimaxM3/20261017-minimax-m3-ppu13-plugin-support/dep-update-001-20261018`；执行脚本先保存到commands。保存旧diff、两个SwiGLU文件、安装身份与版本；在本机准备官方main的bundle，传至该目录，再在容器未挂载的私有目录`/workspace/FlagGems-vllm.main-46387d7-20261018`克隆并补入原有SwiGLU文件/导出。先在候选PYTHONPATH下核验导入，再以`pip install --no-deps --no-build-isolation -e <candidate>`切换容器私有安装；不安装或升级其他依赖。原源码目录完全不动，回退用同参数重装旧editable路径。

更新后核验包路径、版本、HEAD、目标接口、必要MiniMax/SwiGLU符号及Plugin导入；模型未运行，不宣称服务推理/graph/新组合精度通过。原accformal006的90.40%仅为更新前历史组合结果；变更依赖后不能复用为新组合gate。若候选导入或安装失败，保留现场并恢复旧安装，不自动修复其他组件或启动服务。

## 结果

已安装官方main `46387d7f96050204c1b932f35680a3ea03896fa6`，版本`0.3.0.dev1`，实际导入路径`/workspace/FlagGems-vllm.main-46387d7-20261018/src/flaggems_vllm/__init__.py`。仅该私有候选的ops导出增加一项，外加原有SwiGLU实现与测试两个文件；保留文件与旧目录逐字节SHA一致，不是新开发kernel。候选PYTHONPATH导入和editable切换后导入均通过，topk_sigmoid/topk_softmax/grouped_topk/MiniMax预处理/packed SwiGLU接口均可导入，Plugin仍从原refine001路径导入。新topk_sigmoid的参数顺序与vLLM wrapper一致，实际函数来自新版本ops/topk_sigmoid.py；未接入Plugin分发、未执行算子或模型计算。

`pip install --no-index --no-deps --no-build-isolation -e <candidate>`成功，从0.1.0切到0.3.0.dev1；没有升级其他依赖。原FlagGems-vllm仍为1f9ac0e0且dirty patch SHA未变；Plugin仍为原HEAD620892ab + 同一三文件diff（SHA `468e5432772c16c36279734978e7dbe4a132768742fb239e6bd99f15723b4507`），未影响此前发布的远端43e0980。未启动模型，旧90.40%结果仅保留为历史组合证据。

外部证据均在上文run目录：

- `upstream.bundle` SHA256 `4710d978b8cb4007676810aad988e5d00f12c5ff0d33f6e9426263cc51ddab9d`。
- `backup/old-local.patch` SHA256 `1acdb40e31b333fd29328574160265fa6051c5b6e7498e7a38d65f418a38a764`。
- `backup/swigluoai_uninterleave.py` SHA256 `13d2afdbadb260b45fdb0edeea0d2247f813b2f6d9c97eac5023f2a06f140764`；`backup/test_swigluoai_uninterleave.py` SHA256 `2322599c433c645de6a3ea6497e1bdf42665ceb79036d9d19d0c690c445d5ba0`。
- `__init__.py`为候选ops导出文件，SHA256 `33d0e947740a56c4b9e8ed15d6981edae1e25299cef0d5dad1315d0cef77313d`。
- `commands/install.sh` SHA256 `4dcd1c0bdc419bfb235c4cea53b976f9400fb1bc093a654dfbdad9dda5b77f7d`。
- `logs/install.log` SHA256 `fd0c7a32316be4b0337a3135a8679848e869910514914296b355d407f8ce09f5`；`logs/installed-import.log` SHA256 `bd532e51a4ad83bc4f601fba3ed13a628205cc09aeb257a735eb2ccbd6f82056`。
- `commands/rollback.sh` SHA256 `d0bd3788c92ccb4394d3c538f5578b4adc41773e90066d6bb922c7c5dcc2117a`；回退只重装旧editable，不启动服务，本轮未执行。

传输过程中普通SFTP/SCP因堡垒机路径视图失败，目标SSH目录实际存在；改用传统SCP `-O`成功，未绕过主机校验。第一次准备脚本因未传到而未执行，成功传输后才正式备份/安装，无重复安装或删除操作。下一步由用户决定是否将新算子接入Plugin；需要按新算子的实际支持范围做功能/graph及正式精度验证，不能继承旧gate。
