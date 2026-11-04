# OP005：更新FlagGems-vllm与GDN路由

用户2026-10-14明确批准升级优化容器私有FlagGems-vllm并扩展GDN白名单。原17项FG全部保留；MTP调用fused_recurrent_gated_delta_rule_fwd，非MTP调用fused_recurrent_gated_delta_rule_packed_decode。先实现调用与最小正确性/graph回归，端到端收益另行同配置三阶段与回退验证。

上游main核对29e80363b43bce4a25929989641015c1e734c9e3；新真实私有目录/workspace/FlagGems-vllm-gdn-20261014，旧/workspace/FlagGems-vllm保留，OP001两文件补丁3way重放，冲突不覆盖。原服务239394/create1791942156.85在18002/2、3卡。源8002、共享源码、vLLM、权重/tokenizer不操作。

变更执行命令：/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-stage-upstream.py，SHA256 ebf42750818fc84fc1367bd4440823932f93a953c23d320891ddda909f721cb4；先备份四repo diff与untracked到patches/op005-before，再建立私有新版本。当前正式50000精度158/198失败保留，不签gate；此工作属于用户授权诊断优化。MTP配置当前服务未启用，不能以路由测试宣称模型MTP端到端已验证。

接入设计：仅替换模块导入的packed函数，不改类级卷积或_fast-path标志；gdn_decode支持accepted-token，gdn_packed_decode新registry key按当前导出可用性注册。新版recurrent消费V-major，不再pack/unpack；generic chunk仍为K-major，prefill已gather的少量state需转置，final转回V-major。

保存命令/补丁 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-plugin-payload.json，SHA bb4d050c88445a223aaa4b40b7778d91f67cf2f935cf2ef2943a2be8478939d3。

保存命令/补丁 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-apply-plugin.py，SHA 768d252387ed8455cc76ccb4e68e91c79d0d56eb781806d57de970ff94dac403。

CPU tensor/mock路由测试命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-run-unit.py SHA e88df1f5c7f8116218036cab103c5a129d6eb8c780a563a3983cd40e96f93f13；MTP accepted索引、packed直通、hook幂等、无可用实现原路径、状态改写失败不retry、prefill非方形layout纳入覆盖。

GPU minimal-regression冻结：packed B1/8/64/H8HV24K128V128及非对齐K96V80，MTP varlen/accepted2,1/stridedQKV/V-major paddedcache，CPUFP32 oracle atol.002/rtol.02，null0、padding/alias、每项graphcapture两replay。精确停止239394及所属双rank后离线运行，不并行源模型或其他GPU请求。

命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-gpu-v1.py SHA 7fc44fb082fc5b659a2d16a754e8be2aa169256d0b127a1bed2a81a3acee7fbc

命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-isolated-gpu.py SHA fcd1fce9fcd09938a41a9b6409902858cfe0d4cb7adf8d8b7b0ce12ce478eae3

实测v1：4packed+有效MTP通过（每项2graphreplay）；MTP null0初始状态改写保留页0，最大状态误差.847155，失败证据results/op005-gpu-v1.json保留。只修复MetaX三个recurrent kernel的invalid0/negative初始读及final写保护；有效递推不变。新增null/negative/null-final与prefill真实数值测试；不把发现推定为历史GPQA根因。

命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-fwd-guard-payload.json SHA 93d05e167c8e78ea3828e8047ff92989358a891658b42f8d0b4883145e36e97a

命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-gpu-v2.py SHA 58cd8a2aa554e87b136b38d3c987c05b42f99b4294c96d0138980236289ed2c4

命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-guard-and-check.py SHA f8c20e51f01062451ad56abe6c1d030736704dc2167d6bf49923b2ca381a0f88

v2：4packed+4MTP/null/negative/final-null通过；prefill BF16chunk相对FP32逐步oracle有159元素超过既定容差，max.00393677。未放宽容差、不启动候选，先与同形状vLLM chunk reference配对定位。诊断命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-prefill-diag.py SHA c071c0375de4cf2b760cb23a560614691f7b738ac0ff5c83a4d38b1d393b1df2，只保存既定输入的baseline/candidate/FP32误差，不产生模型请求。

范围收敛到用户明确点名的GDN decode：原17FG键逐字保留，仅新增gdn_decode/gdn_packed_decode，未删除任何已开启算子。prefill新启用不合格（FP32误差超既定容差，vLLM generic reference该小shape共享内存69632>65536），保留失败，不启用此新增候选；不能声称全GDN prefill通过。新版decode v3覆盖4packed+9MTP，strided/contiguous/largeT66三kernel分支、NULL0/negative/final-null、每组2graph回放，同FP32容差不变。命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-decode-gpu-v3.py SHA f70cef408cbd834f275af2524f98795d66c348505ab9911280093c3385b298a8。

运行集成：GPU decode13项通过后才私有editable安装最新版本，新19项白名单保留原17+gdn_decode/gdn_packed_decode，独立compilecache。graph双rank至少2replay并要求FG packed实际kernel命中，C8固定10题非空样本与filter计数；失败只按精确出生停止候选，恢复原私有源码/原FG版本及8192服务，不停止容器/源8002。

命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/start-op005-gdn-01.sh SHA 5d84558f8cad8f0f9910b0f1f051074762eda0241aa6adc2a4dc0ff51b8cfb1d

命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-bind-op005-gdn-01.py SHA 728353f3cd7b9ebb83dbb91897bea82fb106795247816418c77ed3c450cd7a6e

命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-op005-gdn-01-c8-config.json SHA 9d98366d8da92ade8cd7830eac125109d19a7af347552ac6067230af66aa9ac1

命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/start-op005-revert-01.sh SHA 0c88f9f638b5600ed88ac7c2d43099a7a934edba7f79f2578d1c2021fd7387f2

命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-bind-op005-revert-01.py SHA 0a320ede8502be737df24377e5f768b8d4676e81c91127631701cefd5b37acf7

命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-op005-revert-01-c8-config.json SHA 47b65191ca69da887c69de70d688b68cc9b910f8b70ec915fc62b20449e92344

命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-original-restore-payload.json SHA 73f0a44c83ad8d6bedc1a5fb7d5bdfec3feb59f1dcf9f93952eedfa99e0a07ab

命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-activate-or-revert.py SHA 02a9e64a8cf77cff2fb63cbe343af34f09aa344b1dc1f52a8ffbe4676d89cf52

实际命中证据：FG/native packed的Triton kernel同名，不能仅凭trace名称判断来源；backend每worker只记录一次实际函数__module__/__name__与impl_id，服务日志必须两rank都出现MetaX FG模块，配合双rankgraph trace。

命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-runtime-hit-payload.json SHA 26ad4ac6ea4dcdf9f9280cc0c3f327dfc4d5e9069be44f4453b53ad9291005c5

命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-add-runtime-hits.py SHA a9c39a5e2fba317421dec3997e891bc2460f61964d724434d4a4dc39ceab94a5

更新binder真实worker命中校验，SHA 356169e43e06df63585743e1686cacb1ceefe4effa028569c6d69c392f0cb687。

收尾命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-finalize-integration.py SHA 6537bc699e6c0c851d263137ff3b1919f3281fa740d546f2a0821f23bef810ec；只核验现存terminal/精确模型身份/原17项FG保留并导出私有最终diff，不发送请求或改服务。

启动命令与回退文件最终SHA（decode-only白名单与worker命中校验补齐后）：

commands/start-op005-gdn-01.sh: 5d84558f8cad8f0f9910b0f1f051074762eda0241aa6adc2a4dc0ff51b8cfb1d

commands/op005-bind-op005-gdn-01.py: 356169e43e06df63585743e1686cacb1ceefe4effa028569c6d69c392f0cb687

commands/op005-op005-gdn-01-c8-config.json: 9d98366d8da92ade8cd7830eac125109d19a7af347552ac6067230af66aa9ac1

commands/start-op005-revert-01.sh: 0c88f9f638b5600ed88ac7c2d43099a7a934edba7f79f2578d1c2021fd7387f2

commands/op005-bind-op005-revert-01.py: 0a320ede8502be737df24377e5f768b8d4676e81c91127631701cefd5b37acf7

commands/op005-op005-revert-01-c8-config.json: 47b65191ca69da887c69de70d688b68cc9b910f8b70ec915fc62b20449e92344

commands/op005-original-restore-payload.json: 73f0a44c83ad8d6bedc1a5fb7d5bdfec3feb59f1dcf9f93952eedfa99e0a07ab

commands/op005-activate-or-revert.py: 02a9e64a8cf77cff2fb63cbe343af34f09aa344b1dc1f52a8ffbe4676d89cf52

实例253939/create1791944403.74已完成graph绑定，服务SHA41e36c0f6852871dd8b38b27423be0a8ecd9feb3036a3f50979171b6fe0e6529。两rank各190graphlaunch、2880packed与960FA split/merge，日志明确FG模块来源；C8在跑，未发正式GPQA或性能。

最终验真脚本补齐已安装package版本和untracked hook/test副本导出；最终SHA c17f5e750e20c65ef28939798ff4e3290937a7274f7ab0be2ec1b20cfcdd5f1a，此前未执行的模板SHA保留为版本说明。

集成v1控制错误：C8原生10题/20行/0空/0timeout已完成strict6/10 flexible8/10（不是完整正式精度），但controller查找results/op005-op005-gdn-01-c8，实际config输出results/op005-gdn-01-c8，触发回退。原版revert01也存在同样预期目录错误；保留真实服务/样本，不删失败、不复发既有C8。v2从冻结config的output_root解析结果，当前同源重启执行新双rankgraph/2smoke，再按4repo+完整launch_config等价绑定前实例C8，明确其生成实例；不声称当前实例重新做10题。

命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-plugin-v2-payload.json SHA 66808073721a7e6d61d8385e5ae5da65cf157471404769b524565b45fe530e87

命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-reapply-private-v2.py SHA 8448b7ac1fffb533920f751ee87bdc7d2cfd27b386757c54d6afbdc07dcc34c6

命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/start-op005-gdn-02.sh SHA c64ac795224e3648b37ffccf7f19811613842ce8c2f8ca4b45646673235c977a

命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-bind-op005-gdn-02.py SHA 0867997ed09b203a62b454b6ddbe1f6f933bf84c1ca21a65f647378c40345478

命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/start-op005-revert-02.sh SHA 64af3a4dda1182a6cc55aa8f80087206f15c647f859b4b7223e59de3c411e84c

命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-bind-op005-revert-02.py SHA de1c8bb375af46c8c6e4b2b8c39e76046fd0a2c4b158df7cf5e41903ddba3bd8

命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op005-activate-v2.py SHA c06d936383ed39879c9a2a0829adc429559f2f745d7926a71a25d16173d7acc2

最终调用契约：

| 路径 | Plugin key | 实际FG函数 | 状态契约 |
|---|---|---|---|
| 无spec masks的non-MTP decode | gdn_packed_decode | fused_recurrent_gated_delta_rule_packed_decode | mixedQKV/a/b直接输入，out与V-major cache原地写入，NULL0/negative不写 |
| MTP/spec recurrent | gdn_decode | fused_recurrent_gated_delta_rule_fwd | 转换FP32 gate/beta，accepted-token与2D pageindices原样传入，原地保存每token状态 |

shim替换模块导入的packed函数；保留vLLM原始卷积、pure-decode选择、spec/non-spec分割及合并。状态ful dispatch strict模式，执行后异常不重试fallback；无可用packed导出时在执行前保留原vLLM函数。KDA不是GDN，仍原路径；非MetaX硬件及真实model MTP未实测，pr_readiness experimental。

最终v2验真命令只读当前精确实例与源码、关联当前graph/短smoke和前实例C8，导出最终patch；commands/op005-finalize-integration-v2.py SHA ec66c1ce045c58ad9bb8d48cd798e854e86b209c9bf317a9723dc7a4be9b2ae6，终态results/op005-integration-terminal-v2.json，不发送评测请求。

v2控制面错误：host侧reapply脚本被调用在docker内，而脚本内部使用docker CLI，因不存在该CLI在首个只读hash检查前失败；0源码写入/0新模型请求，原revert01已精确退出。v3修正为host python执行；启动前核对原PID出生/zombie、所属stopreceipt和无当前模型，再恢复已保存相同候选。新命令commands/op005-activate-v3.py SHA 72bdb37b6becae34655bf1484b268704a588c9e5f0c9409b43fd70019a85a086，保持既有C8不重跑。

最终验真绑定v3控制器：commands/op005-finalize-integration-v3.py SHA debbf0732d43156ce61f07893bd6b7d5c90f67bf5321ed68805fa8e5c855fb05；之前v1/v2验真模板均未执行，保留版本路径。

最终终态integration-passed/experimental。当前实例qwen36-fa-opt:296014:1791945473.24，18002/GPU2、3，新package0.3.0.dev1、upstream29e80363，FGvllm source-tree f23993c24c7ba937e1d0b5cfd0fef13d9b24315032a3bea40e8d348379e338b3，Plugin e6dba08c0b7505fc562e5bdcd8db5d838c83a7539ef0d652033fbc04e242c2d5。终态/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/results/op005-integration-terminal-v3.json SHAc9b630c76153e348b0338ee1a46301eafe68ce32454028ca84724948b3d28ce4；最终补丁/原件/untracked hook与tests全部在远端patches，state索引SHA。

当前双rank各190graph回放，真实FG模块日志及packed kernel命中；C8先前同源实例253939已生成10题20行、零空/零超时，当前296014仅新2条短smoke/graph，不重发C8。4repo/完整launchconfig相等的重启绑定回执已验证，明确不把旧C8改写成新实例生成。控制器目录及Host/容器调用错误均保留失败回执，现已修正，新版服务保持运行。源8002/共享源码/vLLM/FlagGems/权重/tokenizer未修改，未提交推送。

结论边界：用户指定的GDN decode调用接入完成；全量精度/E2E收益尚未验证。当前MTP服务配置未开启，MTP只做路由和真实kernel测试；新增prefill数值尚未通过，不加入新增启用集合。下一性能循环须先以最新19项FG同配置建立三阶段基线，选择operator/improve候选，再保留/回退对照；不能复用旧版本性能数字或历史gate。

2026-10-14用户要求发布prefill问题：核对实际函数对象后更正此前归因。top-level chunk_gated_delta_rule_fwd在MetaX实际解析到runtime/backend/_metax/fused/gdn_chunk.py，已是V-major；此前按generic K-major加转置的接入使初始状态语义改变，因此159元素/最大.00393677不能证明上游数值缺陷。此前“generic chunk仍K-major，因此当前backend必须转置”的应用判断不成立，原失败保留但解释已更正。正确V-major直接调用的GPU数值比较仍待完成；此次只读核验/发布issue，不修改当前运行源码或服务。

已发布https://github.com/flagos-ai/FlagGems-vllm/issues/923，聚焦公开源码中的MetaX/generic state ABI、输入校验与非方形/非零state测试覆盖。自动审批拒绝包含内部环境/诊断代码的原稿，安全替代版本仅引用公开上游源码；原稿未发布。公开稿与发布回执在docs/cases/20261012-qwen36-27b-metax-flash-attention/op005-gdn-prefill-issue-public-source-only.md及op005-gdn-prefill-issue-publication.json。
