# diag-002：TP8 MoE 真实参数元数据

plan-022 的诊断前置，未实施算子优化。当前正常服务为恢复7桶的fix-001，MF85892b、原7桶198重绑定gate d89a均有效。当前trace将MoE收敛为重要设备热点，但有效TP8权重/scale shape、stride和选定配置不能只从模型配置反推。

使用当前Plugin `WorkerFL.load_model` 公开扩展点，临时显式worker_cls，在父加载完成后只读torch参数元数据和当前Python配置选择函数。不执行额外模型forward，不读取/复制权重数值，不记录题目或响应。记录全部8rank，各MoE层w13/w2及scale的shape/dtype/stride、量化类、实际函数对象来源与M1/32/64/1024/8192的配置选择复现。选择器复现不是前向实际JIT参数观测。

保留原7Mixed+7Decode、11exports、KV/并行/模型/原四仓版本；只在优化容器私有Plugin增加临时模块并显式CLI接入。不存在当前元数据RPC，故采用Worker扩展，不修改vLLM。诊断采集后按SHA移除仅本任务新建模块，恢复源码F0及普通Worker，fresh105+2和原7桶schema3 native rebind后回到正式候选。

元数据异常写显式failed回执，父模型加载/推理在异常捕获范围之外；不吞掉推理错误，不提供算子fallback。缺rank、缺模块或shape不一致则停止猜测，保存证据并恢复。目标graph需capture并至少两次replay，其他平台/模型不运行此临时类。临时代码不是PR候选。

可复用经验限于FusedMoE地图的shape/stage/config与alignment一致性、vendor分层方法；GLM BF16/E288、Hy4 W8A8/E256的配置和加速比不迁移到本模型。当前_source_ `_thead` filename inventory只命中gemm_utils，不能宣称SDK不存在MoE。

控制源码、执行副本、SHA、取证及恢复回执持续写入state.yml；大产物留远端案例，未提交/推送。

控制文件已归档，SHA 见 state.yml。采集使用原 7 档 graph、TP8、11 个环境变量；恢复删除观察文件，重新运行 105+2 和原配置 native rebind。

本次 incomplete：实际 PlatformFL 无条件将 worker_cls 覆盖为 WorkerFL，CLI 中的观察子类没有被使用，8rank 文件均未生成。健康/capture 成功不能替代目标扩展命中。按缺rank停止条件撤除新模块并恢复普通服务，不重试本轮诊断。

恢复预检在空闲请求门禁处退出，未执行停止或写入恢复产物：24running/0waiting；另有新ERQA r2及Math500 r2客户端。保持当前健康服务，等待其退出或当前精确停止范围授权；历史停止授权不覆盖新客户端。

2026-10-12 只读核验：8025 仍为优化容器 diag002-probe-01 服务，917875:435271596，健康200；实际启动回执指向 commands/diag002-probe-01-service.sh（SHA db94ee984b92e6b25a3f5c20c4b14f5e89cb32b426446441bacb1e8da2ef472a）。根 start-model.sh SHA57442d... 不变，TP8/7档/11exports；两者不是同一执行脚本。源码修复仅在优化容器，未同步源容器。当前实例最小回归/精度绑定待完成；历史170/198结果不直接绑定当前实例。
