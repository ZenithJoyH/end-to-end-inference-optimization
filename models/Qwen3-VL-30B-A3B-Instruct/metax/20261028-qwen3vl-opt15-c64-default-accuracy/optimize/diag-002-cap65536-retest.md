# diag-002-cap65536-retest

状态：准备，accuracy-diagnosis范围的用户授权截断输出补测，无新正式gate。用户要求ERQA跑完后测这11条，并明确选择输出上限65,536 token。当前max_model_len=262144，等于原生text_config.max_position_embeddings，不修改/重启模型。

## 范围与契约

远端根：/public-flash/jinghao/qwen3-VL/20261028-qwen3vl-opt15-c64-default-accuracy/gpqa-cap65536。只测原doc_id36/48/68/74/79/98/115/127/138/187/194，各一次，总11，无自动retry/补位。C上限64，实际最多11；模型默认T.7/P.8/K20/repetition1，不传seed，prefixON，保持代码/设备/服务配置及现有cache。

原official evaluator的真实OpenAIChatCompletion._create_payload从原生sample arguments重建，再走原adapt剥离采样/seed；旧body序列化SHA必须等于原始upstream审计。只有max_completion_tokens由18000改65536，所有messages/stops等不变。原strict RegexFilter和exact_match_fn评分，保存全部原始响应/usage/finish_reason。11条选择性补测不覆盖125/198正式成绩、不签gate；小batch、warmcache、无seed轨迹变化不构成严格单变量，也不是原输出续写。

## 执行与停止

独立唯一controller仅等待父ERQA400完整终态、父controller退出和user-service-final passed后复核当前source/PID/ticks/config及models200，并等待服务running/waiting均0。父失败/服务漂移不发新请求。等待父最多12h/idle30min；每HTTP最多3h，无retry。全过程不stop/restart源、不clear cache、不新增smoke流量；仅11正文。结束CPU原提取/评分及source-preserved，所有HTTP错误/截断保留，不挑分。

## 执行前脚本SHA

prepare d2df00213ce98ee4079c812fa401ea0ffeab8017096cbe341f2276f09ec30e50；score 9be320691b853c4a2c2f4f539e00c4cf4faa5d06d3087a35906afcb2e22b545c；controller 1c6687ecea55bacb6d4093369aca31fd7e001d9296ae3bc19912ba84378b2afe；start 33676016648102502dbb36903f9486ab1984a9bd2e7fde635ca4b05a269e53f3。所有文件先归档commands/再执行，独立manifest防重复启动。沿用qwen3-vl-opt15-c64唯一监控，原全量和11条都终态后才删除。

## 性能与决定

未测性能。未改变推理实现，未签发精度gate。当前准备0补测请求。

CPU准备通过：全部11份由原registered factory构造的旧请求，其实际序列化upstreamSHA与正式轮逐条完全相同；新body唯一差异max_completion_tokens=65536。执行契约SHA af54248a59dafe83f776e60e131967eef0d989971c76a8317a1407d5fa5a5b0f，生成0模型请求。下一步启动唯一依赖等待控制器，ERQA完成/父控制器退出/源保留/空闲前不发补测请求。

14:56:10UTC唯一等待控制器2676812/ticks1151011704已启动，事件waiting-for-parent-ERQA-terminal，当前补测0请求。父ERQA392/400、无最终回执，等待中，未提前发送。监控已更新保留两项终态之后才停用。

15:05:11UTC父ERQA完成/源保留并退出确认；15:05:17当前source复核及idle后，唯一2676812/ticks1151011704发送全部11个请求，无额外请求或重试。实际上游仅max_completion_tokens/messages/model/stop，cap65536；读取时0/11返回。原source未停/未改。

11题于15:34:36UTC完成，原strict2/11、HTTP全200，source-preservedpassed、controller退出、running/waiting0。独立只读实际11请求/onlycap/defaultsampling/原判分及source当前对before/after精确passed。进一步检查stop+invalid发现doc194最终明确D但末尾无句号/空白。新增CPU ending审计脚本commands/audit_ending.py，执行前SHAc67b464e9d9f7435176f0b78ce9f2c13b0e64076930a779be354783e81408911，核对原正则以及仅附加句号/空白的CPU匹配，不发新模型请求/不覆盖原strict分数。


## 最终结果与独立核验：2026-10-28 23:35 BJT

全部11题HTTP200、每题一次，无retry/额外模型请求。原strict规则2/11：doc68(D)/doc74(A)正确；doc115(A但标准B)/doc138(A但标准D)错误；doc79/98/127/187全部finish_reason=length、输出65536且未提取；doc36/48为stop但没有明确最终答案。

**新增明确提取漏判：doc194**。输出4623token，finish_reason=stop，末尾严格为`The best answer is (D)`，D是标准答案。原正则结尾要求句号或空白，没有字符串结束分支；CPU仅在末尾加`.`或空格即可匹配D。原strict仍2/11不改，按明确最终选项另记录3/11，其中1题格式漏判。此题原18k正式响应未完成，新响应不同，不推翻旧全量125/198的提取审计。

| doc_id | 输出token | finish_reason | 原strict | 说明 |
|---:|---:|---|---|---|
|36|41477|stop|invalid|无明确最终答案|
|48|61259|stop|invalid|无明确最终答案|
|68|10178|stop|D，正确|小于原18k上限|
|74|186|stop|A，正确|小于原18k上限|
|79|65536|length|invalid|仍达上限|
|98|65536|length|invalid|仍达上限|
|115|15050|stop|A，错误|标准B|
|127|65536|length|invalid|仍达上限|
|138|6093|stop|A，错误|标准D|
|187|65536|length|invalid|仍达上限|
|194|4623|stop|invalid|最终D正确，末尾格式漏提取|

独立核验11个唯一request-started/finished、每body仅cap从18000->65536差异、无sampling/seed覆盖、原filter/metric重算精确一致、prompt_tokens与原题一致、响应SHA/结束原因全部吻合。source当前/before/after四仓/模型/tokenizer/argv/env/PID完全一致；API1718819/ticks1149208177，models200，running/waiting0；2676812已退出。全程0停源/0重启/0修改采样源码。

回执SHA：scored14539e505500cabb993d0bc031f409c4ce5b0bb6c24929ef2c11980601826cab；completed15536942ab0f15653fe3fb1bc7206dd5b43b157cba0abcd7e75a5837504149f0；source-preserved3e28eb6c900295dd3a9559346ac3c6f0f25fae653d38a94d87b3f939b459b734；ending-format-audit0c2625913e3b20a3b149f47116e326983cbe789ec7151c5729eb2858ab2d7673。原始响应/逐题结果留D/responses及D/results。

三条明确正确输出均小于原18000，不支持仅增加上限造成改善的因果结论。无seed/缩减batch/warmcache重生成改变轨迹，不能拼接成新的全量GPQA分数。原GPQA125/198=63.13、ERQA182/400=45.50保持；不改变正式提取规则、不自动重跑/优化。所有用户请求的评测与补测均完成，删除唯一监控。
