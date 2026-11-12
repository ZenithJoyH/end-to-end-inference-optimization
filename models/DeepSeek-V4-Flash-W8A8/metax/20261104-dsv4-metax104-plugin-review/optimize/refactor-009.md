# refactor-009：模型限域编译配置默认值与启动脚本简化

用户要求：在 Plugin 按模型范围合并原生默认 splitting_ops 与 FL 边界；验证配置等效后简化启动脚本。不重启服务、不提交推送。

目标：mx-104 / deepseekV4-flash-refactor-20261104，Plugin /opt/vllm-plugin-fl；用户脚本 /public-flash/jinghao/deepseekV4/start-model.sh。沿用已有独立容器及私有源码，FlagGems/FlagGems-vllm/vLLM/权重/编译器不修改。

设计：复用 configs/deepseek_v4_metax.py 的 configure_for_model 模型配置边界，在既有 MetaX + model_type deepseek_v4 + expert_dtype int8 及 TP8/PP1/hidden4096/MBT4096/mode3/FULL_DECODE_ONLY 检查范围内，使用已安装 vLLM 原生 set_splitting_ops_for_v1；未显式指定列表时保留原生分割策略并加入 FL attention 边界。显式列表（含空列表）保持原生替换优先级。不得复制硬编码17项表、修改类级共享列表或产生重复边界；保留原生 fusion/SP 空列表决策。

等效验证：纯CPU执行当前安装源码提取的配置解析逻辑，比较原长配置与新短配置的最终split、custom_ops、mode、capture/max、warmup及全部pass_config；覆盖原列表/None/[]/custom/重复初始化/非目标平台模型/错误路径。记录真实源码SHA，既有kernel和数值逻辑不变。用户明确不重启，因此新服务graph/runtime验证不执行，不使用旧gate声称新代码通过GPU。

规范：Plugin A2/A4/C1/C2/D1/D2/D4/F1/F5/F7，配置不引入环境变量、进程状态或反向算子依赖。原生拓展点复用；数值测试不适用，本轮无数学改动；graph启动验证not_run（用户不重启）。

产物：D=/public-flash/jinghao/deepseekV4/20261104-dsv4-metax104-plugin-review/refactor01；D/compile-config01 保存原始源码/脚本SHA、CPU结果、限定文件备份及回退元数据；所有变更脚本先写入D/commands并冻结SHA。更新前后核验API PID/startticks/argv/health、容器状态及源码共享边界；源码/脚本并发变化停止，不覆盖用户新修改。回退仅本轮明确路径原字节/模式，Git index保持。

当前只读检查18001无API进程、health不可达；保持该既有状态，不启动服务。快照读取最初发生于SSH传输尚未结束导致本地JSON未完整，完成后正常解析，未执行远端变更或模型请求。

## 执行前CPU检查与资产冻结

16/16标准CPU单元测试通过，Ruff0.14按Plugin规则check/format通过，bash -n通过。等效审计复用安装vLLM源码AST执行相关host配置路径，比对35个compilation投影字段和15个pass字段一致、其他脚本argv不变。该投影没有执行完整CompilationConfig/VllmConfig构造、compile ranges或device路径，不等于完整运行时配置/hash；独立静态review确认省略路径对本次新旧参数共同作用。审计脚本早期缺IntEnum、AST括号匹配与显式mode枚举规范化问题均在本地修正，生产候选不因此改变；失败输出保留。

安装脚本独立review补齐CPU检查后外部脚本的冻结SHA并发守卫；保存限定三路径原字节/模式及Plugin索引和patch，先候选CPU等效、再应用、再已安装CPU等效。原有FGV/FG/vLLM未改，Plugin Git index保持。不启动服务，无GPU请求。

冻结资产（执行前）：
{
  "ref009-input01.tar.gz": "4fc3018df9eb3b88fa47a40054b450abccddaff682672c3457c67ff90e7d021d",
  "ref009-apply01.py": "c2809a437d406cf10ef5be2a21d37e284a2c46f5bba1eec011cd8aedc3c282d7",
  "ref009-equivalence01.py": "fbcdee96ca832319f46605744a1bfbc87e93719f3209b1ff7cb6c582c02aa956"
}

最终执行前增加等效检查工具SHA守卫，以上apply SHA被下列最终资产覆盖；此前均未远端执行：
{
  "ref009-input01.tar.gz": "4fc3018df9eb3b88fa47a40054b450abccddaff682672c3457c67ff90e7d021d",
  "ref009-apply01.py": "d5c267db7056306d8d1e2e6d7b2be0136fe89209cde066761645ec6457dfa71a",
  "ref009-equivalence01.py": "fbcdee96ca832319f46605744a1bfbc87e93719f3209b1ff7cb6c582c02aa956"
}

apply01候选16CPU、shell、配置投影等效门禁均通过；写生产源码之前，备份start-model.sh时shutil.copy2尝试复制外部文件系统xattr触发OSError EIO。保留compile-config01全部产物和失败日志；尚未写PATHS，无服务操作。新apply02仅将备份改为独占字节复制+mode+SHA，并使用compile-config01/install02独立新输出；所有冻结源码/脚本/索引守卫不变，不重放apply01。执行前D/commands/ref009-apply02.py SHA 475f5d0ff33a58359f654dfa2ff37a81440fa74cb95aa9bec87769cd1a677f68。

## 完成：安装源码与启动脚本已更新

在deepseekV4-flash-refactor-20261104实际Plugin安装目录更新一个生产函数和一个标准CPU测试；用户共享启动脚本仅替换compilation-config JSON，served-name opt3、端口18001、TP8、prefixOFF/.85、权重、exports等其余内容保持。FlagGems/FGV/vLLM不修改。脚本应在包含本轮Plugin更新的整改容器中使用；原始源容器未同步配置代码，旧脚本在备份中保留。

最终短配置：
```bash
--compilation-config '{"cudagraph_mode":"FULL_DECODE_ONLY","custom_ops":["all"],"cudagraph_capture_sizes":[1,2,4,8,16,32,64]}' \
```

仅None自动初始化原生默认列表；仅原生仍启用attention splitting时加入FL，显式列表（包括[]）原样保留。native fusion/SP空列表策略不覆盖，native将graph降级则初始化前报错。当前短配置投影仍为17边界/mode3/custom-all/7capture档/最大64/warmup1；CPU验证与静态review显示当前参数下等效，非完整VllmConfig运行时构造或hash证明。

候选与已安装位置分别16/16标准CPU测试通过，bash语法通过；本地Ruff检查/格式通过。独立全量642个Plugin文件核验仅两路径变化，Git HEAD/index未变，脚本SHA和候选匹配。首次copy2失败独立确认未改源，apply02独占备份字节/mode/SHA成功。源备份/索引/patch与全部CPU日志保存在D/compile-config01/install02/backup。

当前18001应用前后均无API进程且health不可达；本轮未启动、停止、重启模型/容器，没有GPU或模型请求，也无提交推送。不能据此声称ref008算子GPU/真实dispatch/graph通过；本次修改下次启动加载，当前验证仅CPU配置范围。

{
  "experiment_id": "refactor-009",
  "document": "refactor-009.md",
  "scenario_id": "model-scoped-compilation-defaults",
  "direction": "framework",
  "status": "installed_cpu_config_equivalent_no_restart",
  "main_variable": "Only default MetaX DeepSeek-V4 INT8 native splitting policy merges FL boundary; explicit lists unchanged",
  "remote_artifacts": "/public-flash/jinghao/deepseekV4/20261104-dsv4-metax104-plugin-review/refactor01/compile-config01/install02",
  "changed_files": {
    "/opt/vllm-plugin-fl/vllm_fl/configs/deepseek_v4_metax.py": "90fc1e36f213bb613d7cebcf9e8e257147bf75411fa6da875b2ae2a42a9167f7",
    "/opt/vllm-plugin-fl/tests/unit_tests/test_deepseek_v4_compilation_config_cpu.py": "2e928c6613dbbcfae111b73986b6e7f582bb91219ee33f9b6ed3e4c3532890f3",
    "/public-flash/jinghao/deepseekV4/start-model.sh": "f38a0f9769a4a04aab255f8b123c46533eb0899148bb012ad876172516e19ea4"
  },
  "cpu_unit_tests": 16,
  "configuration_equivalence": "35 compilation projection fields and 15 pass fields match; selected installed native AST/defaults plus independent static review; not full runtime config/hash",
  "script_compilation_config": {
    "cudagraph_mode": "FULL_DECODE_ONLY",
    "custom_ops": [
      "all"
    ],
    "cudagraph_capture_sizes": [
      1,
      2,
      4,
      8,
      16,
      32,
      64
    ]
  },
  "native_splitting_ops": 17,
  "other_script_args_unchanged": true,
  "git_head_and_index_unchanged": true,
  "service_unchanged": "before/after no 18001 API process, health unreachable; no service actions",
  "gpu_graph": "not_run_user_requested_no_restart",
  "performance": "not_run",
  "result_sha256": "5a0cbdc88ae0a66153ded5f2cad6998210de8abbd2d1b63b3aec77635b9867ed",
  "independent_review_sha256": "40360619508f9c4be7beb9b487579800b76e1e6689661073735490d1c2308a48",
  "commands_sha256": {
    "ref009-apply01.py": "d5c267db7056306d8d1e2e6d7b2be0136fe89209cde066761645ec6457dfa71a",
    "ref009-apply02.py": "475f5d0ff33a58359f654dfa2ff37a81440fa74cb95aa9bec87769cd1a677f68",
    "ref009-equivalence01.py": "fbcdee96ca832319f46605744a1bfbc87e93719f3209b1ff7cb6c582c02aa956"
  },
  "backup_failure": "apply01 shutil.copy2 filesystem xattr EIO before production writes; preserved; apply02 byte/mode/SHA backup succeeded",
  "engineering_review": {
    "plugin_clauses": "A2/A4/C1/C2/D1/D2/D4/F1/F5/F7",
    "PR_readiness": "CPU passed; no new graph proof; inherited ref008 GPU/dispatch/graph remains pending"
  },
  "committed": false,
  "pushed": false
}

独立安装审计：D/compile-config01/install02/independent-review01.json SHA40360619508f9c4be7beb9b487579800b76e1e6689661073735490d1c2308a48；最终资产execution-assets02.json SHA6f108443f764ebe6486904296b44eb39e8c4109098dedf999fb839a3e3f71a51。首次备份错误日志保存在D/compile-config01/install01-failure.log（原production未改）。
