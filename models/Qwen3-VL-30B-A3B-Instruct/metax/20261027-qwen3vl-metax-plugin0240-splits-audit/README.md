# metax-plugin0240-base 原始镜像 splits 核验

mx-104；固定latest manifest `a5d8d34d437e…`，Harbor与本机一致。原镜像Plugin Attention省略num_splits，native默认0；Torch2.10/MetaX3.8.2.2/native二进制已更新。

在原始新版native上，24项同输入FP64/普通重复检查及16次graph capture/48次replay通过；六个B1/B8首序列对照在auto0下均有数值差异，fixed1下全部exact。真实rank0例最大差2.44140625e-4。原镜像推理文件没有改动，两个临时诊断容器已删除，GPU7释放。

结论仅限组件数值行为仍存在，不是kernel语义错误或本镜像GPQA/ERQA分数结论；未运行完整模型或性能。[详细记录](optimize/op-001-original-image-split-audit.md)。
