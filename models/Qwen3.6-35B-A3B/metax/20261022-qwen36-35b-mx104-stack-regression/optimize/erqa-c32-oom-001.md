# ERQA C32 OOM 定位（显存利用率保持 0.9）

用户在 C32 ERQA 再次 OOM 后要求继续定位，保持显存利用率 0.9，不重跑全量评测。当前精确失败实例 API1394978/start1155978179 已退出，评测和队列均终态；原 GPQA158/198 和 ERQA212提交/180成功/32失败/188未提交完整保留。

本轮先做纯文件取证：重建冻结 SchedulerOutput 的视觉批次、张量尺寸、分配失败位置；核对当前真实 Plugin/vLLM/Gems 显存预算、视觉 TP/批处理和缓存释放源码；与已归档的历史内存实测区分。无服务启动、源码修改、GPU请求、全量评测或性能实验。远端产物放入 CASE/operator/erqa-c32-oom-001；脚本在 CASE/commands 唯一归档并记录 SHA 后执行。

待区分：启动固定预分配与预算遗漏、单轮视觉编码峰值、allocator 碎片、仍存强引用。旧 LibTuner 修复确实释放约233 MiB/卡，但不是唯一根因证明。当前 OOM 时无 allocator snapshot，不能把保留未分配总量等同于可用连续块，或将旧 snapshot 冒充本次现场。

方法：本地 inference-accuracy-diagnosis，运行失败诊断，不改 GPQA 分数门槛。成功条件是用冻结现场和同源代码建立可审阅的失败因果链，并明确仍需现场验证的部分；如需新增短程硬件实验，先冻结具体范围和停止条件。禁止模型补跑/拼分/择优。

## 预归档纯文件分析

`commands/erqa-c32-oom-forensics-001.py` SHA `96a26cb92e2c064f5fdaa73b1be740ee2c6e412170c83d5e48e52331343d5424`。仅读取冻结日志与容器源码并生成新 JSON，不 import 模型、不操作设备或服务。静态 AST 通过。本地 py_compile 由于系统 cache 路径不可写失败，没有执行分析脚本；改为纯 AST 审阅，无需修改权限。

## 已完成取证

纯文件脚本只执行一次 exit0，command SHA `122706de8c94c67717c0259671826fb721300072009e91e154ecbcdea59c3c58`。首次上传 shell 引号解析失败，远端脚本未创建；改用 shlex 正确归档后 SHA 一致。原产物未覆盖。

远端报告：`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/operator/erqa-c32-oom-001/forensics.json`，SHA `97b2ce21ceddf540adb0902d608747eda15b343de965ea9eccc6e3904702d71d`。同目录 source-snapshot.json 保存本次只读真实源码及 SHA。未执行新模型/GPU请求；未重启或修改服务、源码、参数；未改 continuation。连接预检重新以允许的权限执行通过。最后精确检查当前 B 无 API 服务进程，continuation current_job=null，旧 OOM 服务没有被自动恢复。

### 本次直接证据

- 首次异常 TP0，2026-10-29 14:22:33（Asia/Shanghai）：Qwen3 vision block → MLP → GELU → FlagGems pointwise 输出 `torch.empty_like`，申请138 MiB失败，尚未进入该GELU kernel。不是这次 sampler 或 MoE 的分配点。
- 卡总量63.59 GiB，free0，PyTorch allocated58.16 GiB，私有graph池26 MiB，reserved未分配585.03 MiB。缺少本次OOM allocator快照，不能把585 MiB理解为一个可用连续块，也不能仅凭这行日志断言纯碎片或完全无泄漏。
- 冻结 SchedulerOutput：21 running/8 waiting；decoder8192 tokens；六个请求的11张图合成一个 image encoder group。11张图原始 patch 共33,148（空间merge2对应8,287嵌入token），其中一个请求有6张图。独立encoder预算存在单张最大媒体token下限，不等同decoder8192硬限制。
- 当前源码默认vision TP weights；intermediate4304、TP2、BF16。由grid与源码推算GELU输出 `[33148,2152]`，142,668,992 bytes =136.05975 MiB；按2 MiB段向上取整为138 MiB，与错误一致。这是现场grid+源码推算，不冒充hook读取了实际tensor shape。

| 现场 | 客户端并发 | 引擎running/waiting | 编码请求/图片 | 编码patch | decoder tokens | 首次申请失败 |
|---|---:|---:|---:|---:|---:|---:|
| 旧C64 | 64 | 33/21 | 11/14 | 31,524 | 8,192 | vision linear输出70 MiB |
| 本C32 | 32 | 21/8 | 6/11 | 33,148 | 8,192 | vision GELU输出138 MiB |

C32失败批次patch比C64高5.1516%。两次不是同负载A/B性能比较；此表只证明客户端并发不能替代视觉patch批次上限。更多图片也不必然等于更多patch。

### 预算和固定占用机制

当前 WorkerFL requested_memory=total_memory×0.9，KV预算再减weights、profile激活峰值和从init之后的nonTorch增量；初始nonTorch基线未作为全量扣除。之前同0.9独立硬件取证的两个rank均测到init基线4,387,360,768 bytes（4.086 GiB）、实际KV预分配22,351,380,480 bytes（20.816 GiB）、profile激活余量1.9375 GiB；capture后物理占用94.807%，非90%。这些数字是历史同公式取证，不是本次死进程新采样，也不把初始nonTorch全部归咎于driver或某个库。

本次KV slot使用率仅5.1838%，但KV张量启动时已预分配，空slot不返还为视觉算子可申请的显存。当前源码 image group 直接一次 embed_multimodal；只有特定video条件有逐item分拆，image无同等microbatch。这解释了减客户端并发仍可出现相近甚至更大的视觉峰值。

当前encoder缓存源码确有按free_encoder_mm_hashes释放，本次列出11个待释放hash；不能据此证明所有storage无滞留，但也没有“完成的图片永不释放”的证据。既有LibTuner修复仍通过6850源码一致检查；以前释放约233 MiB/卡的结论保留，不能扩展为已解决所有显存压力。

### 结论与边界

直接触发已锁定：当前固定显存占用下，合批视觉MLP额外输出申请138 MiB失败。支持的机制是固定预分配/预算余量不足与视觉patch合批峰值共同作用，C32请求数不能约束该峰值。不能据此宣称硬件一概无法运行32/64并发图片，也尚未证明唯一底层原因是碎片或另一个强引用。

若继续修复，优先在0.9不变的前提下核对真实物理余量与KV预算、给图像编码建立独立patch微批边界；先用失败批次形状短程验证，不再用全量评测当复现探针。要进一步归因剩余585 MiB，必须取得新短程OOM原生allocator快照，不能从已经退出的进程恢复。当前未实施这些修复或启动任何新实验，未宣称问题已经修好。
