#!/usr/bin/env python3
"""Split prof005 rank traces into Prefill, Decode, Mixed and outside windows.

This is a narrow wrapper around the already-audited prof001 parser. It keeps
its event validation/category logic but prevents execute_new_1 and
execute_new_4 from being collapsed into one prefill_mixed bucket.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
import tempfile


def load_base(path: Path):
    spec = importlib.util.spec_from_file_location("prof001_phase_parser", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load base analyzer: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def marker_phase(name: str) -> str | None:
    if name.startswith("execute_new_0_cached_"):
        return "decode_graph"
    if name.startswith("execute_new_1_cached_"):
        return "prefill_graph"
    if name.startswith("execute_new_4_cached_"):
        return "mixed_graph"
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--base-analyzer",
        type=Path,
        default=Path(__file__).with_name("analyze-prof001-phases.py"),
    )
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)

    base = load_base(args.base_analyzer)
    base.marker_phase = marker_phase
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=".prof005-phase-", suffix=".json", dir=args.output.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
    temporary.unlink()
    old_argv = sys.argv
    try:
        sys.argv = [
            str(args.base_analyzer),
            str(args.trace),
            "--output",
            str(temporary),
        ]
        base.main()
        report = json.loads(temporary.read_text(encoding="utf-8"))
        report["method"] = {
            "prefill_graph": (
                "device-event start timestamp is inside execute_new_1_cached_* annotation"
            ),
            "decode_graph": (
                "device-event start timestamp is inside execute_new_0_cached_* annotation"
            ),
            "mixed_graph": (
                "device-event start timestamp is inside execute_new_4_cached_* annotation"
            ),
            "outside_graph_windows": (
                "device-event start timestamp is outside all classified graph annotations"
            ),
            "warning": (
                "all durations are cumulative and may overlap; profiler-on results are diagnostic only"
            ),
        }
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, sort_keys=True)
            stream.write("\n")
    finally:
        sys.argv = old_argv
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
