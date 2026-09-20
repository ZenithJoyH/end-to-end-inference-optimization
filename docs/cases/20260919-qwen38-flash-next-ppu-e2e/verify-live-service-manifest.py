#!/usr/bin/env python3
"""Bind a saved performance manifest to the currently running vLLM process."""

import argparse
import json
import os
import subprocess
from pathlib import Path


REMOTE_PROBE = r'''
import json
import os
import sys

model, port = sys.argv[1:]
found = []
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        args = [
            value.decode(errors="replace")
            for value in open(f"/proc/{entry}/cmdline", "rb").read().split(b"\0")
            if value
        ]
        start_ticks = open(f"/proc/{entry}/stat", encoding="utf-8").read().split()[21]
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    if not any(os.path.basename(value) == "vllm" for value in args):
        continue
    if "serve" not in args or model not in args or "--port" not in args:
        continue
    if args[args.index("--port") + 1] != port:
        continue
    found.append({"pid": int(entry), "start_ticks": start_ticks, "args": args})
if len(found) != 1:
    raise SystemExit(f"expected exactly one matching vLLM service, got {len(found)}")
print(json.dumps(found[0]))
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("container")
    parser.add_argument("port", type=int)
    parser.add_argument("max_num_seqs", type=int)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    container = json.loads(
        subprocess.check_output(["docker", "inspect", args.container], text=True)
    )[0]
    process = json.loads(
        subprocess.check_output(
            [
                "docker",
                "exec",
                "-i",
                args.container,
                "python3",
                "-c",
                REMOTE_PROBE,
                manifest["tokenizer_path"],
                str(args.port),
            ],
            text=True,
        )
    )
    expected_instance = (
        f"{container['Id'][:12]}-{args.port}-{process['pid']}-{process['start_ticks']}"
    )
    if manifest["service_instance_id"] != expected_instance:
        raise SystemExit(
            "stale service manifest: "
            f"saved={manifest['service_instance_id']} live={expected_instance}"
        )
    live_args = process["args"][process["args"].index("serve") :]
    if manifest["launch_config"]["launch_args"] != live_args:
        raise SystemExit("saved launch_args differ from the live vLLM process")
    if manifest["launch_config"].get("max_num_seqs") != args.max_num_seqs:
        raise SystemExit("saved structured max_num_seqs differs")
    index = live_args.index("--max-num-seqs")
    if live_args[index + 1] != str(args.max_num_seqs):
        raise SystemExit("live --max-num-seqs differs")
    if manifest["base_url"] != f"http://127.0.0.1:{args.port}/v1/completions":
        raise SystemExit("saved base_url differs")
    print(expected_instance)


if __name__ == "__main__":
    main()
