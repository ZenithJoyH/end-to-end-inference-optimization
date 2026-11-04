# top-k去兼容验证

[compat-001](compat-001.md)：FlagTree0.7.1.dev1+ppu3.6下，8卡50项数值/graph检查与100次replay通过；原生编译阻塞消失。但同分输入中K64/K128会选择不同的block集合，已在相同warp配置下确认。生产patch保留，源码与服务实例未改；去补丁模型级精度尚未验证，无新gate或性能结论。首次跨卡测试的默认stream错误及修正补测完整保留。
