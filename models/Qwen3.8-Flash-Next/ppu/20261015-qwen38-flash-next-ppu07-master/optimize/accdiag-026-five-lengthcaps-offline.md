# accdiag-026：5个60K reasoning-only离线归因

用户2026-10-18要求基于已保存回复/token/状态继续定位doc32/71/79/81/88为何不结束。不重跑全量GPQA，不发送模型请求/进行GPU测试，不重启8010或修改埋点，不操作8035；任何新埋点/服务重启先说明并等待方向。采用inference-accuracy-diagnosis，仅CPU离线分析，不签精度gate或性能结论。

## 来源与冻结范围

PPU-07，CASE=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-015-full-gpqa-ppu07-c64-current-i64-qsa-20261018；R=CASE/diagnostics/accdiag-025-target-only-Mixed-C64-20261018/runtime-001。原128请求已全部终态，5条HTTP200/length60000、contentNone、无think-end，完整API token与rank0 non-discard前缀相同；doc178两次真实MixedC64正常。原FINAL17c4baea、audit8404b79e、addendum88712ff0绑定原件。原正式164/198 failed-score/no gate不改，旧heartbeat继续PAUSED。

只读连接已按inventory限定PPU-07并验证passed。当前8010/8035health200；不以诊断产生新服务负载。派生目录为CASE/diagnostics/accdiag-026-five-lengthcaps-offline-20261018，排他新建，不覆盖025证据。

## 检查计划

1. 对5条原始token全量核验special tokens/stop/usage，检查精确token循环、重复段落、重新推导/自我反驳、何时已提出答案而仍继续；对照本轮123健康回复，不以低重复率证明数值正确。
2. 逐prompt和prompt IDs匹配旧acc014/015正式与已有局部原始回复，比较是否长期难题、结束长度、是否不同轨迹；多实例/埋点/负载不同仅作观察，不当单变量A/B。旧NV原文件在当前PPU07原路径不存在，不能宣称重新核验NV；旧007已核历史73K/58K/86K及近90K记录仅作为有出处的历史背景。
3. 读取已冻结rank0首Prefill/采样及8rank索引、mask/graph；CPU-only在既有评测容器中解包首次state，核实际文件/shape/dtype/finite与请求映射。state在doc32结束后才冻结，只覆盖其余4条/共享pool last-writer，缺5题首步逐层/logits，不补造。
4. 只读核实际采样/结束处理源码，检查是否配置禁止think-end/EOS、忽略EOS或仅内容解析问题。无logits时明确不能判断结束token概率及数值分歧。

CPU派生脚本先apply_patch保存并记录SHA，再排他传输到CASE/commands后执行；只落新报告/证据manifest，不导入模型或改变已有进程。状态解包限定CUDA_VISIBLE_DEVICES空、OMP/MKL及torch线程1、map_location=cpu，不调用任何GPU API或推理。运行前补齐脚本SHA与命令。

已冻结：`CASE/commands/accdiag026-offline.py` SHA `6b63d7fc6d61c11ff0fc22d21c06924ece28fd521cbbe0935fb89888f5d7e4c4`，Host `python3 CASE/commands/accdiag026-offline.py`；新目录排他创建。`CASE/commands/accdiag026-state-cpu.py` SHA `fc16c7be924814b783ba4ecb4bf94e2d4c72a4a71bf2dc9627129d6b12d3d7fc`，仅在原评测容器qwen38-eval-ppu07-acc015-c64-20261018已运行且上份report已存在时，用`docker exec -e CUDA_VISIBLE_DEVICES= -e OMP_NUM_THREADS=1 -e MKL_NUM_THREADS=1 <eval> python3 CASE/commands/accdiag026-state-cpu.py`一次。只读288份既有状态PT并排他写新state-cpu报告，不导入模型/Plugin或执行算子。

继续只读源码/身份快照：`CASE/commands/accdiag026-source-audit.py` SHA `e990541a2e78daade773b20698b4064cd3d79df857a443755e137ae00d8a80a4`，Host python3执行一次，新写source-and-runtime.json/manifest；仅docker exec隐藏GPU的stdlib进程读取protocol/sampling_params/Qwen3 parser/017旧观察器函数原文及generation_config，和双服务/proc/health，不加载引擎或触碰服务。用于区分采样禁止结束与观察器快照覆盖范围；没有prob/logits时不宣称结束token概率异常。

## 结果：直接机制确认，数值根因未隔离

5条原始API均60000 token，无248069及248046/248044；完整API序列与025实际rank0 non-discard前缀一致。模型没发出think-end，因而一直停在reasoning，最终由max_tokens截断；不是解析器丢了已生成的结束标记/最终正文或网络超时。不能从“未采到”推断其logit概率为0。

原stop为`["</s>", "<|endoftext|>"]`、max60000、seed1234/temp1/top_p.95/top_k20/min_p0/presence0/repetition1。请求未设置ignore_eos/min_tokens/allowed_token_ids/logit_bias/bad_words/thinking_token_budget；当前protocol默认False/0/None/None/[]/None并按字段传给SamplingParams。generation_config EOS为248046和248044；同轮123条正常结束，未见统一禁用结束标记的配置证据。无5题logits，不能排除未观察到的运行时数值/概率问题。

### 逐题分析

| doc | 本轮轨迹 | 历史同题（prompt IDs完全相同） | 16-token非重叠片段唯一率 |
|---|---|---|---|
|32|在A/B、exo/endo和R/S坐标几何之间反复重建，末尾仍在推导|acc015正式43897/B；acc01454426/A（错）；旧015局部57530/B；017/022局部60K；019局部53126/A（错）|99.60%|
|71|不断改变反应中间体/碳骨架及氢等价类，得出不在选项中的数目后又重构|acc01454281/A；acc015/022局部均60K|98.93%|
|79|不断尝试字母权重、ASCII、base4、DNA统计等规则，被例子否定后换路线|acc014/015均60K；旧007记载NV近90K仍无final，仅历史背景|100%|
|81|反复比较立体描述与对称性；约99.56%字符处写“I'll choose D”，仍继续复核而未切出reasoning|acc01448308/D；022局部47578/D；acc01560K|98.99%|
|88|不能稳定确定反应产物，在笼状/重排结构和triplet/pentet/tt等裂分间切换|acc014/015均60K；旧007记载NV86306/A，仅异环境历史背景|99.79%|

5题分别268/335/463/312/475个至少60字符段落，归一空白后无完全重复段落；末4096 token的16-token非重叠片段唯一率均100%。不支持简单短token/整段机械复制循环，表现为题目相关但不收敛的多分支推理/自我复核；这只是行为分类，不是数值正确证明。reasoning内答案倾向不能代替final重算正式分数。正常历史与本轮在第9–103个token内已出现轨迹差异，实例/源码/埋点/负载历史不同，不能当单变量A/B或只归因RNG。

### 执行与索引

doc32首Prefill为step9322、42请求、slot32、452prompt，其中20个scheduled1 Decode peers及多个fresh/chunked项，**不是63Decode+1Prefill特定边界**。其余4题为step10001/10326/10372/11077、slot63实际MixedC64，prompt343/263/778/402，63个scheduled1/computed>0 peers。首Prefill均graphNONE，不能直接当FULL replay故障；前序graph影响未排除。

每题首步有36GDN×3stage=108条generic记录，真实i64地址均有效，最大索引分别3221/6064/6460/6502/8092，未触达20972，不支持旧i32跨界直接解释本次首步。doc32为batch级多Prefill，mask混有True/False，不能逐条冒充doc32专属索引或认定初始化错；其余4条单fresh mask为False。缺5题实际device首Prefill输入/逐层hidden/logits，025只对两个doc178抓完整张量，API prompt一致不能替代设备输入证明。

### 状态检查与新增覆盖缺口

CPU逐一torch.load原288份PT成功，CUDA未初始化，1728个保存tensor中浮点无NaN/Inf、原manifest/SHA匹配。**并不证明4条在途请求全部状态正确**：freeze_runtime每层实际只选metadata的第0行及最大索引行；target_req=None，未为异常目标额外选行。以layer0为例保存state_rows6460/8608，当时请求为doc79/81/71/88，不是四条完整状态。indices仍含64长度及非活动尾部，selected_pre_post/record按pool键复用，是有界last-writer而非36层独立历史。finite/flags正常不能排除未保存行、错误有限值、写回时序或logits偏差；doc32在freeze前已完成，更无其故障全链。

## 回执与下一步

| 派生回执 | SHA256 |
|---|---|
|report.json|808ce07d817992f43ed3bb38d59cdd75742ef3877eb532853649833e2a5b2f15|
|manifest.json|8efe76b0d7962fec8be4503925beee9ec0515de166fc032597db5e69db395759|
|state-cpu-report.json|62d8622b2a45046a5b2a66e01799dff369f263be909f28b34647f52c38897763|
|state-cpu-manifest.json|2dc6e1ad620405a61536d8a04a5fb63ff386318dc5d14925a5f3de7bdf0202bf|
|source-and-runtime.json|6430ae5058971864c4f6de37910675881375ed221685054e164d3220e1978ee0|
|source-and-runtime-manifest.json|c0772330162bf36874dc50f6ba07b33ad9a93a900df7b948b4b8ff985f88be92|

全部新manifest独立SHA核验通过。CPU脚本输出过长被工具展示截断后用紧凑只读摘要补齐，非模型或脚本失败，无重跑。源取证时双服务PID/start/argv与025精确相同、health200；本轮模型请求0/GPU测试0/服务信号或重启0/源码埋点改动0，未操作8035，monitor保持PAUSED。

**判定**：confirmed直接机制=未生成think-end→60000预算耗尽；supported行为=反复复核/不收敛；numerical root=not-isolated。doc71/81历史48K–54K可结束，不能只加预算就视为修复；doc32结束也可能答错。旧NV不同代码且90K，不当数值reference；本轮PPU07原NV路径不存在，没有访问PPU01/重验NV，旧NV仅引用007已归档事实。原正式164/198 failed-score/no gate与性能阻塞不改。

下一项最有区分力的是doc71/81正常/不收敛轨迹在**相同token前缀上的logits及think-end概率对照**，先用短前缀找首个分歧，不是再跑198题或盲目加预算。现有5题没有此现场，不能仅凭状态文件继续证明哪个GDN/QSA/采样环节出错。新受控请求/定点概率记录，尤其需要新埋点或8010重载时，先说明范围并等待用户方向；**本轮未实施**。不按GPQA题号/答案做模型特判或强制终止修改。
