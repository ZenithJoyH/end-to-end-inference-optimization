#!/usr/bin/env python3
"""Run op009 A/B/A with M32 config normalized to the TP16-observed stage4."""

import importlib
import json
from pathlib import Path
import runpy
import sys


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: op009-vendor-live-config-micro.py OUTPUT_JSON")
    case_dir = Path("/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e")
    test_path = case_dir / "commands/performance/op009-vendor-candidate-micro.py"
    if not test_path.is_file():
        raise SystemExit("op009 candidate micro script missing")
    module = importlib.import_module("flag_gems.fused.fused_moe")
    original = module.try_get_optimal_moe_config
    normalizations = 0

    def live_stage4(*args, **kwargs):
        nonlocal normalizations
        result = original(*args, **kwargs)
        if (
            len(args) >= 5
            and args[4] == 32
            and tuple(args[0]) == (128, 384, 6144)
            and tuple(args[1]) == (128, 6144, 192)
            and args[2] == 4
            and args[3] == "bf16"
        ):
            config, embedded = result
            if (
                config.get("BLOCK_SIZE_M") != 16
                or config.get("BLOCK_SIZE_N") != 64
                or config.get("BLOCK_SIZE_K") != 128
                or config.get("num_warps") != 4
                or config.get("num_stages") != 3
            ):
                raise RuntimeError(f"unexpected isolated config: {config}")
            config = dict(config)
            config["num_stages"] = 4
            normalizations += 1
            return config, embedded
        return result

    module.try_get_optimal_moe_config = live_stage4
    output = Path(sys.argv[1]).resolve()
    original_argv = sys.argv
    try:
        namespace = runpy.run_path(str(test_path), run_name="op009_vendor_micro")
        sys.argv = [str(test_path), str(output)]
        namespace["main"]()
        if normalizations == 0:
            raise RuntimeError("live config normalization did not hit")
        payload = json.loads(output.read_text())
        payload["micro_harness_live_config_normalizations"] = normalizations
        payload["micro_harness_live_config_change"] = "M32 num_stages 3 to live 4 for both A/B/R"
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"normalizations": normalizations, "result": str(output)}), flush=True)
    finally:
        sys.argv = original_argv
        module.try_get_optimal_moe_config = original


if __name__ == "__main__":
    main()
