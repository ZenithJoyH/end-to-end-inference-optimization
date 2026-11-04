# delivery-002-install-no-pythonpath

用户要求去掉启动脚本PYTHONPATH并安装优化代码。仅优化容器qwen36-27b-fa-opt-20261012私有/opt/conda，不修改源容器/共享源码。全21FG/原FP326ea/原容差/端口及GPU配置不变，未授权启动服务。

预检：容器挂载仅/public-flash及只读模型路径，site-packages不共享；无模型进程。现FG-vLLM和Plugin均editable安装，Plugin两entrypoints存在。此次把FG-vLLM原源码在私有tmp staging打wheel，no-index/no-deps/no-build-isolation；保留Plugin已有editable安装，避免生成版本文件改变原源码。安装前备份原distribution文件，失败恢复；成功后从/tmp无PYTHONPATH子进程实际导入、核对全部py/yaml字节及GDN FP32模块，再移除脚本唯一export行，备份旧脚本。不运行模型/数值/graph/GPQA或性能。

安装命令 `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/delivery002-20261015-install-no-pythonpath-package.py` SHA `83666992a5f183540451caad10bba62a3e650cdcf6ecc07cd5236a7bc67dd722`；控制命令 `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/delivery002-20261015-install-no-pythonpath-apply.py` SHA `1a0cbfd60450f95f8c80b85a5dbf70fa21e4df61c2d8d9fdc5b2acfaf8b062d7`。状态prepared。

首执行在修改前SHA检查退出，0安装/0脚本覆盖；只读核验用户已去掉缓存env、改为./service.log，保留当前内容，仅删除PYTHONPATH行。V2控制命令 `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/delivery002-20261015-install-no-pythonpath-apply-v2.py` SHA `7064893f0166af1dcfbc2372e6de0c8d10aa253e3fe2531cbb713e067a5bbf7f`，基于当前oldSHA `092702ee8a42bae27b2892afc63004e34abc53d21a3eca11d65bf027550ec289`。

## Completed

Installed non-editable FlagGems-vllm0.3.0.dev1 wheel in `/opt/conda/lib/python3.12/site-packages/flaggems_vllm`. Plugin existing editable install remains unchanged at `/workspace/vllm-plugin-FL/vllm_fl/__init__.py`. Fresh imports from /tmp without PYTHONPATH passed; both Plugin entrypoints exist; all378 Python/YAML files match retained FP326ea byte-for-byte, including GDN WY/Chunk. All4 repo fingerprints and all dependency versions unchanged. No model started, no graph/accuracy/performance test performed; no new live gate binding.

Wheel `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/delivery002-20261015-install-no-pythonpath/flaggems_vllm-0.3.0.dev1-py3-none-any.whl` SHA `9142dff4b2e4703e7807bd9ad1d7ce7154a9104522feac536103896c01937844`; previous install backup `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/delivery002-20261015-install-no-pythonpath-previous-install.tar.gz` SHA `690afe04780e15de0760761365e8b47a99f1c55c7dffd0704f2aa4b6da15688f`. Package receipt `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/results/delivery002-20261015-install-no-pythonpath-package-receipt.json` SHA `d9af9689252dc3082465670693b42591b67d4cb978d19d3a0e6a8ee14a0c4c2b`.

Removed only script PYTHONPATH line, preserving user edits to ./service.log and cache env removal. Script SHA `6baa3e089dbf0b9c111877764eb8ce8cd5ff9671b0afb35171e8adec16250a0b`; backup `/public-flash/jinghao/qwen3.6-27B/start-model-flagos.sh.bak.20261015T051009Z`. Host/container bash -n passed. Delivery receipt `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/results/delivery002-20261015-install-no-pythonpath-receipt.json` SHA `6b0790379dee64f4a790461c42a3296d2ae425795caf1ade3bfb8844cb06f965`. Full21FG/originalFP32/tolerance/GPU2,3/18002 retained.
