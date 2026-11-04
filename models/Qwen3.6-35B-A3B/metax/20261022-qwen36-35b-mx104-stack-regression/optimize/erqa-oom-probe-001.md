# ERQA OOM short memory evidence at original0.9

User explicitly authorizes restoring original service at gpu-memory-utilization0.9 and one short memory evidence run, no full evaluation. Same current B/TP2/GPU4/5/8020/opt3/prefix-on/8192tokens/maxseq64/source/model/env. Prior failed ERQA400 partial preserved, no GPQA/ERQA full rerun or score.

Use external process-scoped observer/import loader in CASE/operator/erqa-oom-probe-001/runtime, no inference repo edits. Observe ModelRunnerFL runtime boundaries, allocator history/OOM callback, encoder logical versus unique-storage bytes and public Triton kernel-load hooks. Skip queries during graph capture, no CUDA synchronization or numerical modification. Hook exception propagation/idempotency/atomic install checked before real service.

Finite plan: instrumented original-argv service, twoC8 qualifications; C64 text control64requests(max8tokens) then96 original ERQA requests(doc178..273,max300,temp0/thinkingFalse), no retries/score, first HTTP/engine error latches new wire. One short sentinel may trigger final snapshot if healthy. Total diagnostic scope161 requests plus qualification16; no post-hoc escalation if not reproduced. Capture native allocator snapshot at OOM. Finally stop exact diagnostic PID/start/argv only and restore ordinary service with no observer, same original argv/keyenv and own16 qualification. All old sources and failed outputs retained; other GPUs/services untouched.

First unique bootstrap checks source case/space/Bidentity/currentjobnull/port8020/GPU4/5 idle, then tests native allocator memory-history/snapshot/OOM callback registration and public Triton hooks using one4096byte allocation without model or GPU kernels. Script commands/erqa-oom-probe-bootstrap-001.py SHA5fa9270ca52e869aa0c242cd1a8d1b455cafca6bebb0257af9f71a1b859b7665. No forced OOM; capability registration is not actual failure reproduction.

Reviewed bounded implementation before execution: native history max8192, OOM callback, existing public Triton hook chaining, atomic class wrapper/signature/exception checks. Original inference argv and 6850 source files protected. Two originalC8 qualifications before and after.

- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/erqa-oom-probe-service-helper-001.py` SHA256 `cc8fb04aebba6e1265e4b4ee9dfb0e764c812981842fa8a8078676385c33703d`
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/erqa-oom-probe-client-001.py` SHA256 `cc241aaff4cf7de34b76b9f9b2dad1f638aee49ec4210a7d222c760d7df2e875`
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/erqa-oom-probe-cpu-test-001.py` SHA256 `11ee51ec979eddcec8c37f4333750c1d5c93a3149c958d7d10214ad62383224a`
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/erqa-oom-probe-controller-001.py` SHA256 `738008279d59afdcd397ec7dc2dc1383d97d4595391e53184bf5999084e7a82b`
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/erqa-oom-probe-analyze-001.py` SHA256 `86627ef1b0df4c95922f72144fbd598923b26162f9c92d12d602041c0bc88aa9`
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/erqa-oom-probe-prepare-001.py` SHA256 `553b650a14bdcd7ad1a006de0dafd3b8caebc5f60204faade88dea102693d63d`
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/erqa-oom-probe-supervisor-001.py` SHA256 `6aac372814b7f584599ac957e41b51c7a4d326cc1d2d0f791612a374f2b32559`
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/erqa-oom-probe-starter-001.py` SHA256 `a05ccacd9a64063b1fe52a517ebd0cad80b9d3489ed36cf8ca3b6e77559ad08b`
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/operator/erqa-oom-probe-001/runtime/q35_oom_observer.py` SHA256 `859ba75b9a5e24767af9ba05842e6e8fbe4feff7dea8d2c84ea2f38ba2c53d6b`
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/operator/erqa-oom-probe-001/runtime/sitecustomize.py` SHA256 `c02417d00f85e73f4f04e15e1b700d1e0121535606022a11b823184f7036aaa7`

Next execute prepare001 once (CPU wiring, zero model requests), then starter001 once only if plan/source/currentjob/port/GPU guards pass.

Initial controller nativeexit2: stdin process inspector matched itself, zero short text/image diagnostic requests. Probe8 qualification interrupted during cleanup; ordinary original0.9 service PID918162/start1148345153 subsequently passed16/16 ownC8 checks. Observer readiness2workers valid; preserve all outputs. New followup root and new unique002 scripts only fix precise inspector filter and explicit stop of that clean source before fresh observer launch; no model/engine/code/generation changes. New qualifications belong to new service identity, not retried ERQA diagnostics.
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/erqa-oom-probe-service-helper-002.py` SHA256 `00e15b89a921a037acb8e223f2c9cdff9ae4a1f77d1f5bd112468282f8124d2c`
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/erqa-oom-probe-client-002.py` SHA256 `996a73dd1d326dba42e2932f063bb54aa5aaae1e7c2e0ff2bc8f3094978c0722`
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/erqa-oom-probe-cpu-test-002.py` SHA256 `093c180dc36c9976476790f7f30768f10821e0b62e922c047ff86c3ec42b5614`
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/erqa-oom-probe-controller-002.py` SHA256 `fc53e16fc131f02e049cb3dcb3d57a8a1269482ed0bc10641d2704cf170d71e3`
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/erqa-oom-probe-analyze-002.py` SHA256 `201c2346814a45e4b53e74c27db5a0bd4214d80c4ffd1218eca00f1abcd0f807`
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/erqa-oom-probe-prepare-002.py` SHA256 `34c901c3079baadbbab8ddb5bc97ab496a404a6a7027f179beee15d76cc8fc54`
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/erqa-oom-probe-supervisor-002.py` SHA256 `9011a321d2230c18eb094022cfb63c7e93b067fe2ea2200d440ba6916a59b7ed`
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/erqa-oom-probe-starter-002.py` SHA256 `59c65353e3aa21cdd8c169f992c079f76b43fafe08ea72c0ad04084985957ffe`
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/erqa-oom-probe-independent-002.py` SHA256 `eb3988b8d259a65bc9dd78d4612eae041785fcf3097307d273de711606f7423f`
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/operator/erqa-oom-probe-001/followup-001/runtime/q35_oom_observer.py` SHA256 `859ba75b9a5e24767af9ba05842e6e8fbe4feff7dea8d2c84ea2f38ba2c53d6b`
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/operator/erqa-oom-probe-001/followup-001/runtime/sitecustomize.py` SHA256 `c02417d00f85e73f4f04e15e1b700d1e0121535606022a11b823184f7036aaa7`

followup root preparer SHA256 4fb05f9b4399b2e74a1bd994b89d42965cea10ced2fa9d0775f89c68e43dc205; execute once, then CPU prepare002 and starter002 once.

Followup001 actual started once: supervisor2055230/start1148448110, controller2055231/start1148448114, plan d943d1a3a5533423450eff47a548279d3dcec9180b9ae6afe22b2b3b1c418f78; starter command d486d5b4c70ed6245a9e7522d800f5de4e78abb7bb9d2b5627d724d43aa1f70d. Source ordinary918162 precisely stopped, new probe929719/start1148450598 original argv/0.9. No source edits. Do not replay launcher or any client phase.

Automatic approval blocked ordinary pickle.load snapshot inspection. Safely inactivate pending old analyzer at its existing-output precondition (no unpickle), preserve review-block evidence, use a new restricted parser (no global lookup/object construction/persistent IDs) and a new output directory. This is an observation-only repair, no service/model changes. Guard SHA256 270e5af995e2503db2fa49ab953f88f98d6fa18eeefebf659fd9ae2656031746

Followup finite control64/images96/sentinel1 all completed without OOM; native num_ooms0. No extension of frozen traffic. Clean restore running. Safe parser rejects all GLOBAL/STACK_GLOBAL/REDUCE/BUILD/object construction/extension/persistent-reference opcodes before restricted Unpickler; find_class and persistent_load always reject. Primitive-only recursive validation and bounded bytes/opcodes; two CPU parser checks, no model requests. New observation-only files (old native analyzer safely blocked at no-existing-output assertion):
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/erqa-oom-probe-analyze-003.py` SHA256 `df902c40dd44ebc9fd667ad25a78b4e5ed66f3d293a694d379b119f81ed7c0ed`
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/erqa-oom-probe-independent-003.py` SHA256 `ff64b6edd4bc4357907b82b141a8280e45b551ba32de0f5e5bd906b05d605897`
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/erqa-oom-budget-source-audit-002.py` SHA256 `cea6de07ea50e49c694f353d4b20f213011e3cd3e7e976620b93bfbd6e75f307`

Read-only final conclusion/checkpoint script SHA256 8b7de4b9aa1b03e817c3ccaff966dbb397aeadfd0260149a7e6a92677aee64a7. Fresh exact original0.9 clean service and verified161/161 diagnostic+32/32 qualification, protected6850 bytes. Preserve native controller exit2 caused by intentionally blocked unsafe analyzer; safe analysis003 and independent003 exit0 replace observation outcome only, no replay or status laundering. OOM not reproduced; unique cause not asserted.

2026-10-28 短程取证与清理完成：原0.9/TP2/GPU4/5/8020/opt3/prefix-on已恢复，当前API972456/start1148499863，日志在远端本实验followup-001/restored/service.log。两轮C8恢复检查16/16通过；全6850生产源码/编译器字节一致，观察器路径和token均已移除。没有新增完整GPQA/ERQA或gate。

冻结范围64文本+96图文(doc178..273)+1快照触发请求全部161/161成功，HTTP并发峰值64、零重试；本次服务自身资格和恢复资格共32请求。早期进程观察错误的24资格请求单独保留（8中断/16恢复成功），未进入短程子集、不与本次合并评分。独立核验SHA25c95fd1768ec3edc509750f67c607495d025d1b19485a82825d6f0fd590c2f8。

实际内存证据：每rank KV常驻22,351,380,480B=20.816GiB；profile激活预留2,080,375,296B=1.9375GiB。Plugin worker.py:195、200–201只把初始化后的非Torch增量(约1.49GiB)计入non-KV预算，初始化基线约4.09GiB不是该增量。公式KV=requested−weights−peak−nonTorchIncrease已逐字节复算；0.9不是运行时物理硬上限。两rank graph完成后物理已占94.807%，空闲3.302GiB，比0.9目标多占约3.057GiB。图文阶段rank1分配器reserved最高57.908GiB，非Torch约5.631GiB，最少空闲约56MiB；rank0 inactive_split最多1.276GiB。Encoder缓存底层存储峰值101,396,480B（约96.7MiB），split-view放大最高2.405倍；非Torch较startup峰值仅增28,868,608B（约27.5MiB），模块加载钩子未测到GiB级增长。短程中没有证据支持encoder缓存或模块缓存的GiB级异常膨胀。

原始OOM直接触发点仍明确是FGV MoE cache13的256MiB分配，实际8192tokens/32请求/10图的mixed step，设备free0。新短程**未复现OOM**（两个worker均num_ooms0、没有OOMcallback），故不能把历史最后一次分配失败唯一归因于碎片，也不能证明新的96题等价于旧完整运行历史。末尾快照normal pool总inactive约2.35/2.73GiB、最大单块恰为256MiB，此时该尺寸仍可复用；不能把这些末尾块状态冒充原失败瞬间。

已确认主压力链：预算与物理占用口径/初始化基线造成实际余量小，KV保持常驻，图文动态工作区和分配器保留/碎片进一步消耗余量；唯一历史根因未隔离，不做数值实现归因、不改0.9或源码、不自动扩展诊断/全量。

自动审批曾拒绝普通pickle快照读取。旧分析器在其existing-output前件处安全阻止，保留原exit1和controller exit2；新受限解析器禁止对象构造/全局lookup/持久引用，限制字节数/opcode数/递归深度，安全分析和独立核验均exit0。没有把原生错误改写成成功。8份快照、两rank全覆盖，observer_errors0。

远端最终证据（均在CASE/operator/erqa-oom-probe-001/followup-001）：
- diagnostic-conclusion-001.json SHA a457f9a58bfdd115d217f3a5da1be561d7e54aa7b7a1d9550f6b1aed6aa024d6
- analysis-safe-001/analysis.json SHA 3707ddd46bc92623bfffeece4c5dcfc4b08410fff5c9744e4ead903c14668e44
- budget-source-audit-001/audit.json SHA 84e6c65f3d7a68a9ff0860cd7d1975c13c46c17f6a086e36c50c08de66ef2272
- independent-verification-safe-001/verification.json SHA 25c95fd1768ec3edc509750f67c607495d025d1b19485a82825d6f0fd590c2f8
- independent-conclusion-checkpoint.json SHA 79451eace6b966a2edf81ef8787b127f404323857d3682dee38ed1e3f03dc962
current_job=null，continuation phase=user_ERQA_short_memory_evidence_complete_not_reproduced_clean_original0_9。无活动monitor，不空轮询。
