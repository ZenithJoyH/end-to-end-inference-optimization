#!/usr/bin/env python3
"""Add one-time runtime hit evidence for the native Decode sparse-MLA path."""

from pathlib import Path


path = Path(
    "/workspace/vllm-plugin-FL/"
    "vllm_fl/dispatch/backends/vendor/thead/impl/mla_decode.py"
)
text = path.read_text()
old_import = "import torch\n\n\ndef native_sparse_mla_decode("
new_import = (
    "import torch\n"
    "from vllm.logger import init_logger\n\n\n"
    "logger = init_logger(__name__)\n\n\n"
    "def native_sparse_mla_decode("
)
if text.count(old_import) != 1:
    raise RuntimeError("unexpected T-Head native Decode helper imports")
text = text.replace(old_import, new_import, 1)
old_call = "    from flash_mla import flash_mla_sparse_fwd\n\n    output, _, _ ="
new_call = (
    "    from flash_mla import flash_mla_sparse_fwd\n\n"
    "    logger.info_once(\n"
    '        "T-Head HY4 pure Decode is using native flash_mla sparse attention."\n'
    "    )\n"
    "    output, _, _ ="
)
if text.count(old_call) != 1:
    raise RuntimeError("unexpected T-Head native Decode helper call site")
path.write_text(text.replace(old_call, new_call, 1))
print(path)
