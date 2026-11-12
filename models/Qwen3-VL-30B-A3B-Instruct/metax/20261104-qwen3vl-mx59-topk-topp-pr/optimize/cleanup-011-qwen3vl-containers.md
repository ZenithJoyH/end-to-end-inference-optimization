# cleanup-011: mx-59 Qwen3-VL 历史容器清理

状态：completed，18 个相关历史容器已删除，qwen3vl 服务保留核验通过。2026-11-09 用户明确要求保留 `qwen3vl`，停止并删除其余 Qwen3-VL 类容器。

远端归档目录：`/public-flash/jinghao/qwen3-VL/20261104-qwen3vl-mx59-topk-topp-pr/cleanup011-containers-20261109`。精确冻结 18 个容器 ID，8 running/10 exited；运行中的目标只有 tail/sleep/shell，无模型或评测进程。另一个通用名称 `metax-native-moe-inspect-20261013` 已通过本项目 Qwen3-VL op-011 记录确认归属。通用且未证实属于 Qwen3-VL 的 qwen-gpqa-eval-c8 保留。

只对冻结 ID 逐一 docker stop --time 20、docker rm（无 -v/--force）执行；不删镜像、volume、bind 数据或日志。保留源容器配置和当前 opt18/8030 服务 PID/ticks/argv/env/cwd；所有无关容器前后 ID/config/state 对照。

## 删除清单

- `qwen3vl-topk-guard1069-20261106`
- `qwen3vl-topk-prefix1069-20261106`
- `qwen3vl-opt17-erqa-mx59-20261105`
- `qwen3vl-opt17-gpqa-mx59-20261105`
- `qwen3vl-hot1k-mx59-20261105`
- `qwen3vl-topk-opt1069-20261104`
- `qwen3vl-split1-erqa-20261023`
- `qwen3vl-split1-gpqa-20261022`
- `qwen3vl-gpqa-diag-20261022`
- `qwen3vl-pr943-erqa-20261022`
- `qwen3vl-pr943-gpqa-20261022`
- `qwen3vl-pr977-20261022`
- `qwen3vl-erqa-20261022`
- `qwen3vl-accuracy-20261022`
- `qwen3vl-p1k-opt9-20261021`
- `qwen3vl-p64k-opt-20261015`
- `qwen-vl-sampling-opt-20261012-mount-rejected`
- `metax-native-moe-inspect-20261013`

## 执行前归档 SHA256

- `cleanup.py`: `79fe1ba533816c410cb668868402942e9da293007a79c7afdfa5c4b9b963a23f`
- `contract.json`: `f2dbc21ae4af91bc26996d826468868c248a80fda35825f6a7352db00cd7b69e`
- `baseline.json`: `f17886f278222c582a8103da049bd6b15d5f2c5d1ad58e85150aaba8ec488315`

本地唯一上传/执行命令 `/tmp/qwen3vl-cleanup-mx59-20261109/launch.py` SHA256 `4a42ef266f192bc80f3b973bebc5392d50598fd6f5c1a32c3277ad76a7731ab1`。先以 exclusive create 归档命令和清单，验证字节后执行冻结清理脚本。

## 保护检查工具事件及修正

初始脚本在任何 stop/rm 前因 raw Mounts 顺序不同拒绝，removed=[]；原 failure.json 保留。只读连续8次 inspect 证实 /data 和 /public-flash 顺序可互换，配置/挂载内容/PID/StartedAt 均未变。v2 对挂载完整字段做无序精确比较，再按原排序计算 Config/HostConfig 摘要；不削弱挂载内容检查、不变更目标。新独立归档目录 `/public-flash/jinghao/qwen3-VL/20261104-qwen3vl-mx59-topk-topp-pr/cleanup011-containers-20261109/v2`。

- v2 `cleanup.py`: `c4cd6ad506c2808390e5365b4d4c45d0d855539738e4168457b94706891e6049`
- v2 `contract.json`: `682575ae056846bfb9a180d239cb90f8aeebb19bfb6a8d2bf484c1a500296bd5`
- v2 `baseline.json`: `f17886f278222c582a8103da049bd6b15d5f2c5d1ad58e85150aaba8ec488315`
- v2 `launch.py`: `a373fc14e44b948ce5de2a0940e95e28c5b17d22179b18744785fb45a28c4641`

补充只读核对：`docker diff qwen-gpqa-eval-c8` 显示 `qwen38_flash_next_gpqa_diamond_c8_*` 配置和 `qwennext-pr455` 原生输出，确认其为 Qwen Next 评测，非 Qwen3-VL，保留。

只读独立核验脚本 `/tmp/qwen3vl-cleanup-mx59-20261109/verify.py` SHA256 `04fdfbc193db2bdaf419f8ece413fe104891923ff32f067ee0e5385dd1191cf3`；最终回执归档命令 `archive_final.py` SHA256 `3b4d97b16e45d1db17faa0a556709bb5fddfd24c37aca0f9a1dea4d1c924a751`，仅写本次清理目录中的新回执/命令，不再做容器变更。

## 完成及独立核验

18 个冻结目标均已删除，其中8个运行中的空闲容器已先停止。当前相关容器仅 `qwen3vl`；其容器 ID、配置、挂载、init PID、opt18/8030 模型 PID/ticks/argv/env/cwd 保持相同，models HTTP200。脚本无任何对保留容器或其他模型的 stop/rm，未删除镜像、volume、宿主 bind 数据。

v2 在已完成18项后，因为无关容器并发变化触发额外 postcheck：MiniCPM 容器被外部删除；独立核验还发现 qwen36-35b 的 runtime-state 外部变化。这些对象不在冻结清单中，所有 stop/remove events 的 ID 均逐条核验只属于18个目标。原 v2 failure.json 保留，不能声称所有无关容器前后状态相同；其余37个无关容器检查一致。未重复删除或重启任务。

最终独立核验 `results/final-audit.json` 状态 `passed-cleanup-and-source-preserved`，SHA256 `13b31ef38d0445df03c068b845c8678db70ecc6f96ec34f5a0b161d9746d057d`。原始清单、命令、逐项事件和旧失败回执在远端 `cleanup011-containers-20261109/` 保留。
