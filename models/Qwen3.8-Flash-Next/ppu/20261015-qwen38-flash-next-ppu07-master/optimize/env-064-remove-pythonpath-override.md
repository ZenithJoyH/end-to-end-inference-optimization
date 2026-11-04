# env-064：移除root交互shell的旧PYTHONPATH覆盖

- 授权：2026-10-22用户在容器中看到旧FlagGems版本，明确要求去掉PYTHONPATH。
- 范围：PPU-07 / `qwen3.8-flash-opt-ppu07-20261015`，仅root shell环境整理；不重建容器、不重启8010、不访问8035、不安装包或改算子、不提交推送。
- 状态：completed，3种新root bash模式及pip/editable环境验证通过。

## 原因与边界

Docker Config.Env固化了`PYTHONPATH=/opt/qwen38-acc011-cachefix-20260924/FlagGems/src`，使pip优先发现旧源码egg-info，显示`5.5.0.dev0+g85cc5efb1.d20261015`。env063实际源码editable安装已为`/opt/FlagGems`及`5.5.0.dev0+gf0aa7f121.env041`；安装本身无需重做。

root shell为bash，`/root/.bashrc`及`/root/.profile`无PYTHONPATH赋值，`.profile`会source `.bashrc`。Docker创建ENV不能在不重建的前提下经正常Docker接口删除；不编辑Host上的Docker内部配置。旧终端已继承的环境也不能从另一进程直接取消，不注入用户终端或修改/proc。

## 实施计划

完整备份两份root启动文件后，在二者末尾加入有界、幂等清理：仅当PYTHONPATH**恰等于上述旧值**时unset。这样新root交互非login与login shell默认使用editable安装，同时保留用户将来显式设置的其他PYTHONPATH和当前8010的私有模型/算子/固定调优路径。原始文件SHA/权限、源路径与有效包metadata先核对，不改/etc全局配置、sitecustomize、pth或容器ENV。

外部根：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/environment/env-064-remove-pythonpath-20261022`。命令先保存commands并核SHA，一次执行；备份仅保存在该根受限权限目录中，不把启动文件原文写入日志或项目。shell语法、全新bash交互/登录的环境、pip list/editable/spec路径，以及原8010身份/health/计数/显式PYTHONPATH前后核验；0模型请求或GPU测试。

## 验证和回退

当前已打开的用户shell需自行一次`unset PYTHONPATH`或新开终端。直接`docker exec <容器> pip ...`不经过shell，仍继承不可变Docker ENV；这种用法明确使用`env -u PYTHONPATH`，不能宣称容器Config.Env已删除。未来重建容器时才可从创建参数真正去除，需另获授权，不在本次自动执行。

回退仅还原两份精确备份，并先核当前marker/预期SHA，不重启服务或恢复旧包安装。此次不是新的精度/性能评测，无新gate。监控保持PAUSED。

## 执行前命令

已保存于`/private/tmp/qwen38-env064-pythonpath.Mx7leX`并AST检查：`control.py` SHA`e39cda1be601c3ba91af051a36df63fd8e43751b4ff44a7d85a0ab8ff658fc03`、`apply.py` SHA`6e3ec311f8c9228941d818d26f16148f0a64855d71651c3d95bdec9f3c6d84ef`、`verify.py` SHA`3e95c65656f9260e99bc8e07efdaab796f2745589e47e34ba8a581556a28baad`。排他传入上述新外部根commands并核SHA，仅一次`PYTHONDONTWRITEBYTECODE=1 python3 <根>/commands/control.py`。外部根权限0700、startup-backup权限0700/备份文件0600；不记录启动文件原文。

原文件SHA：bashrc `89f85eaff847ea2dac64357a91b624e1d4f19516654f9fe734c5c09239329f4f`、profile `bbee58b1e0787bb851e7f7a4d0c187a8122d68eb67e5fa464696310398ac005b`。工具修改前需逐份匹配，避免覆盖用户同期编辑。

## 完成结果

两份启动文件已在受限权限`startup-backup`保留并逐份核原SHA，只追加精确旧值的条件unset，shell语法通过。新`bash -ic`、`bash -lic`、`bash -lc`三种模式都以原Docker旧PYTHONPATH作为输入，验证进程未用env-u兜底，最终变量均不存在；两包spec和editable/direct_url均正确：

```text
flag_gems      5.5.0.dev0+gf0aa7f121.env041  /opt/FlagGems
flaggems_vllm  0.3.0.dev1                   /opt/FlagGems-vllm
flagtree       0.7.0+ppu3.6
```

对非旧值的显式私有PYTHONPATH另行验证保留。原8010 Host1924405/start531054985、argv、显式PYTHONPATH/health200/running0/waiting0、prompt82925/generated2446388前后相同；0重启/包安装/源码修改/推理/GPU/8035访问/提交推送。验证未导入torch或生产算子包；监控保持PAUSED，无新模型gate。

最终bashrc SHA`a2ba6d1e21daf0e08ef757b987d8309d638a4187090674ae9319c45c993c30db`，profile SHA`7db67385faa678880a19daaf858835674c5c378e3f326c066aa9e467a4c31344`。外部根19文件manifest SHA`605512143b9118919cfa33a797add14d5c3b2a1b4ef0cebad8677ca2752b4574`，summary SHA`7f1deb386c886de53409ef270068685e79e55242991984c6fab7c3e50a8813a8`；原始启动文件内容不进入日志或本项目。

边界仍有效：用户已打开窗口需一次`unset PYTHONPATH`，或重新进入bash；直接Docker exec非shell命令仍会继承Docker Config.Env，须明确`env -u PYTHONPATH`。本次没有声称该不可变ENV已被删除，也没有重建容器或修改现有进程。

## 2026-10-22 11:46 +08：按用户要求再次只读核验三库和修复

连接检查限定PPU-07通过。以显式去掉PYTHONPATH的新Python进程检查顶层spec与distribution direct_url；另以原Docker环境进入全新`bash -lc`，不显式env-u PYTHONPATH，得到相同的三个源码入口：

| 库 | 新进程解析入口 | editable根 |
|---|---|---|
| Plugin | `/opt/vllm-plugin-FL/vllm_fl/__init__.py` | `/opt/vllm-plugin-FL` |
| FlagGems | `/opt/FlagGems/src/flag_gems/__init__.py` | `/opt/FlagGems` |
| FlagGems-vllm | `/opt/FlagGems-vllm/src/flaggems_vllm/__init__.py` | `/opt/FlagGems-vllm` |

三库均`editable=true`。FlagGems版本`5.5.0.dev0+gf0aa7f121.env041`、FGVLLM `0.3.0.dev1`；Plugin metadata仍为`0.3.0rc2.post1+ga696859b9.eng055.d20261021`，版本后缀不用于判断是否FP32，实际BF16 model SHA `d458a1ce…`与已测私有副本完全相等，旧`gpu/tp_reduction.py`不存在。

七项源码SHA均与env062/063保存值相同：Plugin BF16、index i64、index_put i64、randn i64、MoE TLE能力门禁/零extent v2、PLE i64+CTA、QSA M16（实际文件`src/flaggems_vllm/runtime/backend/_thead/fused/qsa_attention.py`）。Gems src 3713份、FGVLLM src 397份非pycache有效文件与当前服务使用的私有源树逐文件同SHA；4个旧兼容模块亦保留。三库Git HEAD/分支及原有差异仍可见，未git add/commit/push。

当前8010仍为原Host1924405/start531054985，argv SHA `c146e2da…`及原私有PYTHONPATH前后相同；没有切换在线服务路径，不能以新进程spec检查冒充运行中每rank函数对象的新trace。核验只使用stdlib/spec/metadata/文件哈希及只读Git，未初始化生产包或torch，0源码/安装/配置改动、0服务动作、0推理/GPU测试、0次8035访问；不产生新精度gate。只读核验脚本SHA `cd97aa4d9abd04db8c698ab85a5d083e3acb44031d335db906d0e965c29cb8ed`，执行stdout保留在本次工具记录。
