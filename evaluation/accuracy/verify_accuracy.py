#!/usr/bin/env python3
"""对 lm-eval 结果执行大于或等于固定阈值的精度检查。"""

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict


def load_task_metrics(path: Path, task: str) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    metrics = payload.get("results", {}).get(task)
    if not isinstance(metrics, dict):
        raise ValueError(f"{path}: results 中不存在任务 {task!r}")
    return metrics


def metric_value(metrics: Dict[str, Any], requested: str) -> float:
    if requested in metrics:
        value = metrics[requested]
    else:
        matches = [key for key in metrics if key.split(",", 1)[0] == requested]
        if len(matches) != 1:
            raise ValueError(
                f"无法唯一定位指标 {requested!r}；可用指标：{sorted(metrics)}"
            )
        value = metrics[matches[0]]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"指标 {requested!r} 不是数值：{value!r}")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"指标 {requested!r} 不是有限数：{value!r}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path, help="candidate 的 results_*.json")
    parser.add_argument("--task", required=True)
    parser.add_argument("--metric", required=True)
    parser.add_argument("--threshold", required=True, type=float,
                        help="candidate 必须达到或超过的预冻结阈值")
    args = parser.parse_args()

    if not math.isfinite(args.threshold):
        parser.error("--threshold 必须为有限数")

    candidate = metric_value(load_task_metrics(args.result, args.task), args.metric)
    print(f"candidate={candidate:.10g}")
    print(f"threshold={args.threshold:.10g}")
    if candidate < args.threshold:
        print(f"FAIL: candidate {candidate:.10g} < threshold {args.threshold:.10g}")
        raise SystemExit(1)
    print("PASS: candidate score meets or exceeds the frozen threshold")


if __name__ == "__main__":
    main()
