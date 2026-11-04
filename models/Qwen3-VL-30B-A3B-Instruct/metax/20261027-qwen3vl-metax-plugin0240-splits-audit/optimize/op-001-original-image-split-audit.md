# op-001：原始 metax-plugin0240-base 镜像 splits 静态核验

用户询问 `harbor.baai.ac.cn/flagos-inner-models-release/metax-plugin0240-base:latest` 是否存在此前 splits 行为。仅检查该镜像原始源文件/依赖，保持原始推理代码，不导入旧模型优化补丁，不启动模型、占用 GPU 或跑完整精度。latest 本机镜像 ID/manifest 摘要固定 `a5d8d34d437eb3dfe45158078421792b9e2e5fc48a9d3d25431625110756dc96`，created 2026-10-23；注册表 config digest 属于不同OCI对象，不能与manifest ID直接判不一致，另查verbose descriptor。

只读临时容器不绑定Host目录、不分配GPU、network none、read-only rootfs、CPU1/内存2G，entrypoint为镜像Python3.12。用标准库/AST/metadata读取Plugin实际包定位、nativeAPI默认值、native二进制SHA和仓库HEAD，不importTorch或执行GPU调用。完成/失败finally删除仅本次临时检查容器，镜像和当前用户容器不动，不留下新Qwen-VL容器。

既有结果参考：07cf发布镜像旧case组件24项通过原FP64容差/普通重复/graph，但auto0 B1/B8有数值差、fixed1精确。只有Plugin调用、nativePython接口和native二进制逐字节相同才能判断继承同实现；静态一致并非当前新镜像GPU重现，不自动转移旧GPQA/ERQA成绩，也不称vendorbug已确认。

远端 /public-flash/jinghao/qwen3-VL/20261027-qwen3vl-metax-plugin0240-splits-audit，执行脚本 commands/audit_image.py，SHA `5953edc9f60d98665d3d6d8a7b86d2e64e57ebd2ec4946c0e66ac514b6c2cede`，执行前已记录与归档；结果写results/image-static-audit.json、comparison.json以及temporary-container-removed.json。状态prepared，待执行。

## 静态结果及最小组件契约

Harbor最新manifest descriptor摘要与本机镜像一致（a5d8...）；其config digest 9ac19e...是不同OCI对象。Plugin Attention原文件与旧发布镜像逐字节一致（f81fa552...），native调用省略num_splits、默认仍0；但新Torch2.10/MetaX3.8.2.2，native接口SHA4b2d5b...、native二进制SHAf251391...均与旧版不同，不能声称同二进制继承。静态原始结果SHA `ee9e9f9ddf3a1fea92b24389b2c339e82b8a3c908c9d6ea6353cac8ca378f6f3`，comparison SHA `6f08926d6f374459c1b1253a6acc8e0c193f8c38fc492abdbe948d5045abbe9e`，comparison固定解释字符串只能条件性使用，应以三个组件match布尔值为准。临时CPU容器已删除。

按本地 inference-accuracy-diagnosis 的最小复现方法，GPU7只读检查无进程、显存859/65536MiB；不占用户GPU0/1或其他服务卡。启动前再次核对空闲。原镜像临时组件容器保持source容器的两项bind挂载完全一致，原镜像来源是用户指定新baseline，推理源码零修改；network none/private IPC/2G shm，仅做单GPU原生API，不启动模型。运行24项既有真实TP-rank输入/合成BF16+FP16，B1/B8、KV短长和num_splits0/1，同FP64容差/普通重复/graph3回放；900秒总预算，不重试。只改既有harness的任务R和新版native SHA，不主动注册FlagGems，以隔离直接nativeAPI数学行为；不将该隔离结果当作模型默认backend命中、所有组合软件的硬件验证或正式精度。实际probe/依赖脚本/输入SHA在GPU启动前冻结。

控制脚本 /public-flash/jinghao/qwen3-VL/20261027-qwen3vl-metax-plugin0240-splits-audit/commands/run_component.py，SHA `99c3ff636e4a1854b79aed5c5d213ccd9840da16a5d3645254ca5f05a1f11a0a`，结果保存native-component.json及component-completed.json；失败保留证据、不重新跑。finally只删除本次组件容器，不影响保留容器/模型服务或镜像。issue ID `accdiag-plugin0240-auto-split-001`，分类为待验证的继承数值行为，未签发新正式gate或判断新模型得分失败。

## 新镜像 GPU 最小复现结果

状态completed。原生API8项真实TP-rank输入重放+16项BF16/FP16/KV1024及65536合成用例，共24项全部通过冻结FP64容差；普通重复全部exact，省略num_splits与显式0全部exact。16次graph capture/48次replay通过，actual绑定的新版native Python和二进制SHA均核验。

| 同一逻辑首序列B1/B8 | split0最大绝对差 | split0不同元素 | split1 |
|---|---:|---:|---|
| 真实rank0，KV224+Q9 | 0.000244140625 | 2692 | exact |
| 真实rank1，KV224+Q9 | 0.00006103515625 | 2463 | exact |
| 合成BF16，KV1024/Q1 | 0.0009765625 | 566 | exact |
| 合成BF16，KV65536/Q1 | 0.0001220703125 | 857 | exact |
| 合成FP16，KV1024/Q1 | 0.0001220703125 | 507 | exact |
| 合成FP16，KV65536/Q1 | 0.0000152587890625 | 829 | exact |

结论：虽然新镜像已升级Torch2.10/MetaX3.8.2.2/native实现，原始auto0跨batch数值差异仍复现；这不是仅根据源码默认0推断。所有原FP64容差均通过，因此不能将本结果升级为确定kernel算错或新镜像GPQA低于64。固定1只是原API参数对照，未改镜像Plugin文件；直接native隔离未注册Gems，未运行模型级dispatch/TP2服务/GPQA/ERQA或性能，不能转移旧gate。

原生结果 /public-flash/jinghao/qwen3-VL/20261027-qwen3vl-metax-plugin0240-splits-audit/results/native-component.json，SHA `2ac563c506c9510f985c9734dee4899027ca581324d8bb880f98996ccc1aaa88`；组件总回执SHA `e1805d351676cbdb5f266780530f68c34eef346c2e8686b4d8f7230af185c114`。GPU组件probe SHA `1263ccccfae71179e0203aebbd9891686be8e9614de5e8200fd50859acda55b4`，执行前冻结的输入/依赖清单SHA `38156061f745a81d11134e6ed0db0ae20c71d99734a5726a5105d73b32da4e27`。

两临时检查容器均已删除，GPU7无剩余进程，原有保留容器ID/挂载/源码前后完全一致，无停止/重启/新启动模型。组件cleanup回执SHA `8c9b5f41211dd3c26be871da6338e146f0d8df0f00a91ed5c2ea8ac05af2a8ee`。无待跑任务/监控，无提交推送。
