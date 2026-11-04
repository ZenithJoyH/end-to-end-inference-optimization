# pr-040：index/index_put i64修复的上游查重与证据补充

状态completed-existing-issues-PRs-evidence-published-no-new-duplicate。用户2026-10-19授权向FlagGems提交index/index_put修复Issue和PR。发布前实际GitHub查重发现已有同类记录，纠正此前仅检索本案例而声称未提交的错误；复用已有条目，不创建重复Issue/PR，不改他人分支、不合并、不强推、不解决冲突或重跑CI。

## 已核实的上游事实

- `index`：Issue [#4153](https://github.com/flagos-ai/FlagGems/issues/4153)，PR [#5882](https://github.com/flagos-ai/FlagGems/pull/5882)，作者bin913，head92db9ee5a011b9b297ffebc898bc9fd0e9ae9ee1；open/unmerged/mergeable=false。PR覆盖generic加载索引先扩i64、linearized安全宽度选择及测试，正文Fixes #4153。该PR为相关工作，不冒称本任务新建或本账号代码。
- `index_put`：Issue [#6411](https://github.com/flagos-ai/FlagGems/issues/6411)和PR [#6413](https://github.com/flagos-ai/FlagGems/pull/6413)均ZenithJoyH既有提交；head330dd99d5c661f4d6a9745b68c5dd1e30773210a，open/unmerged/mergeable=false。覆盖加载索引先扩i64、program offsets宽化、两入口与测试，正文Fixes #6411。另有bin913同类PR6892，只记录重叠，不重复评论或改动。
- 当前master冻结f0aa7f12180cea4776a2aba3f3889b8fb82a28b1。GitHub读取实际index.py blob2243d5a49f54b54eea911cfaf3a1377442920424与index_put.py blob7a6b052f2c72e07d7cf4aff7c511fa447a801856，generic加载语句仍无i64提升，不能因为有PR就说主线已修复。此轮只核覆盖范围，不声称已解决PR冲突或当前完整CI通过。

## 本次发布范围及证据限制

只在以上两组现有Issue/PR添加带日期的补充评论与互相链接。公开必要模型/硬件、dtype/shape/stride、算术边界、既有算子/IR验证摘要；不上传完整日志/PT/模型/数据集/私有路径或凭证。全部内容基于本地accdiag017已保存事实及GitHub现有公开代码，不访问PPU主机、8010或8035，不运行GPU/HTTP/全量GPQA，不改生产环境或当前源码。

本地独立修复并非上述PR当前head逐字节构建，不能将017的36链检查、24小布局检查、3次changed-index graph replay写成PR5882或6413新pytest通过；unsafe旧大索引内存kernel未执行。IR的load32→extsi64→muli64和安全小scratch偏移探针属于地址语义证据，不是事故完美A/B。后续模型曾跨generic36088但仍有reasoning-only/60K，故不声称已解决全部精度/长生成问题。

关键现场FP32 state shape[66758,6,128,128]、stride[102400,16384,128,1]、storage_offset1920。20971×102400=2147430400，20972×102400=2147532800；完整行98304元素使20971的行尾也越2**31，不能只看行基址20972。合法范围内的高索引23520/87528微测与模型后续实际高索引分别报告，不互相冒充覆盖。

评论采用每个目标一次提交；未知结果先读回查重，不能盲重试。提交后读回正文/URL，保留原Issue与PR正文，不改变关闭关系，记录已附加聊天的两PR。未解决冲突、未签gate、无性能结论。实际评论URL与结果在完成后补记。

## 发布结果

- index Issue[补充评论6263139805](https://github.com/flagos-ai/FlagGems/issues/4153#issuecomment-6263139805)，关联既有PR5882；PR[补充评论6263146203](https://github.com/flagos-ai/FlagGems/pull/5882#issuecomment-6263146203)反向链接该Issue现场。
- index_put Issue[补充评论6263140829](https://github.com/flagos-ai/FlagGems/issues/6411#issuecomment-6263140829)，关联既有PR6413；PR[补充评论6263147310](https://github.com/flagos-ai/FlagGems/pull/6413#issuecomment-6263147310)反向链接该Issue现场。
- 四份评论均通过GitHub原生读取正文逐字相等且各只命中一次，2份PR已attach当前聊天。原PR正文既有Fixes #4153/#6411保留，不改他人工作、不宣称本任务创建旧PR或合并修复。
- 公开Issue补充payload执行前保存在`/private/tmp/pr040-index-i64-followup-20261019.md`，SHA6128ed20c51092cf60e1da004554eedda7e3053fa3010112fb0c918a0492e83d；CPU标准库复核3个边界整数及完整行尾。Firecrawl公开源码页辅助获取，精确master源码/Issue/PR/补丁与状态以GitHub API核验；反馈返回窗口过期且retryable=false，未重试。
- 新Issue0/PR0/commit0/branch update0；复用既有记录而不是重复提交。两PR当前mergeable=false，冲突未解决，完整当前CI未验，不宣称已可合并。无PPU连接、8010/8035访问或任何模型/算子测试，未更改运行环境；旧正式164/198 failed/no gate与性能阻塞不变。

后续env041核验时GitHub重新计算PR5882/6413/6892为mergeable=true，仍全部open/merged=false。上面的false仅为发布时快照，不再代表当前冲突状态；本任务没有更新分支或解决冲突。不能用mergeable=true替代已合并/CI通过或主线已含修复。
