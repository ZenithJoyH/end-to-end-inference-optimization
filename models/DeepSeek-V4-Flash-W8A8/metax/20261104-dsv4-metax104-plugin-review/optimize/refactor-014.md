# refactor-014：12个FGV PR最新head的CI失败处理

用户2026-11-12要求处理CI失败。仅检查/处理既有#1136–#1147，不改正在运行的服务、整改容器、安装源码或主聊天活动实验，不增加本地/远端GPU实验。共享state/README交主聊天串行合并独立小条目。

## 初始核验

12个PR head均等于refactor013已发布merge head。11个basic-ci已success，全部12个rule-check及CLA成功。唯一最新head失败为#1145 `570da319cdd679aaa9157c7e7c9f647130b51e8b`，run `43146130372`。

首错位于MetaX maca3720 job `130944902255`的FlagGems vendor环境安装：包镜像`mirrors.aliyun.com/pypi/simple/flash-attn/`连接超时，5次重试后安装退出1，GPU检查和算子测试尚未执行。其他后端smoke及MetaX maca3810 job成功；summary job `130948895172`随前者失败，非第二个算子错误。不能将此环境失败算作算子数值/graph回归。

## 有界处理

预先保存`/private/tmp/dsv4-pr-ci-20261112/plan.json`及12PR初始CI回执。首选仅rerun该workflow的failed jobs，保留已经成功的jobs，不加空提交、不改测试断言、不跳过失败后端。如果重试仍失败，重新取首错判别，不重复盲试。当前未修改PR代码/分支；旧性能数据和Draft状态保持。

## 重跑权限与最终边界

调用GitHub原生`rerun_failed_workflow_run_jobs`对run43146130372执行一次精确重试，返回403 `Resource not accessible by integration`，未创建新attempt。随后只读核验浏览器已登录ZenithJoyH，运行页面仅有Create status badge菜单，没有重跑入口；未改账户权限或索取/读取token。无法通过当前账号实际执行上游Actions重跑，需上游有Actions写权限的维护者点击该run的Re-run failed jobs。没有为触发CI加空提交、改测试/后端门禁或重推数值代码。

本地证据：`/private/tmp/dsv4-pr-ci-20261112/{plan.json,initial-ci.json,rerun-result.json,failure-excerpt.txt}`。失败原run链接：https://github.com/flagos-ai/FlagGems-vllm/actions/runs/43146130372 ，首错job130944902255。本轮只确定网络超时导致环境安装失败，尚不能宣称重试成功或后续算子验证通过。

状态：`blocked_upstream_actions_write`。最新12个rule-check及CLA通过，11个basic-ci通过，#1145 basic-ci仍failure。代码/PR head/body/draft/整改容器/服务和主聊天GPU实验均未改动。这里的阻塞仅指外部CI重跑权限，不回滚历史验证，也不误报整个旧优化项目失败。
