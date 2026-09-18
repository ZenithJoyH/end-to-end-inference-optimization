from flag_gems import runtime


for name in ("linear", "mm"):
    configs = runtime.get_tuned_config(name)
    print(name, len(configs))
    for config in configs:
        print(config)
