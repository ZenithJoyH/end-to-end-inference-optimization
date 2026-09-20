#!/usr/bin/env python3
import importlib.util
from pathlib import Path

CASE_ROOT = Path("/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e")
source = CASE_ROOT / "commands/accuracy/run-m64-semantic-minreg.py"
spec = importlib.util.spec_from_file_location("m64_semantic_minreg", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

module.RUN_DIR = CASE_ROOT / "accuracy/m64-nontruncating-semantic-minreg-03"
module.CONTRACT = CASE_ROOT / "commands/accuracy/m64-nontruncating-semantic-minreg-contract.json"


def case(index):
    left = index * 17 + 113
    right = index * 29 + 71
    expected = left + right
    return {
        "index": index,
        "expected": expected,
        "payload": {
            "model": "Qwen3.8-Flash-Next",
            "prompt": (
                f"Compute {left} + {right}. Your response must end with exactly "
                f"FINAL={expected}. Do not use FINAL for any other number."
            ),
            "max_tokens": 512,
            "temperature": 0,
            "top_p": 1,
            "seed": 1234 + index,
            "ignore_eos": False,
        },
    }


module.case = case
module.main()
