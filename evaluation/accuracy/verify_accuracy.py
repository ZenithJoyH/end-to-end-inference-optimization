#!/usr/bin/env python3
"""对 lm-eval 结果执行固定阈值或相对基线精度门禁。"""

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
    parser.add_argument("--minimum", type=float, help="candidate 的绝对最低分")
    parser.add_argument("--baseline", type=Path, help="可信 baseline 的 results_*.json")
    parser.add_argument(
        "--max-regression",
        type=float,
        default=0.0,
        help="相对 baseline 允许的绝对回退；指标为 0~1 时 0.01 表示 1 个百分点",
    )
    args = parser.parse_args()

    if args.minimum is None and args.baseline is None:
        parser.error("至少提供 --minimum 或 --baseline")
    if not math.isfinite(args.max_regression) or args.max_regression < 0:
        parser.error("--max-regression 必须为有限数且 >= 0")

    if args.minimum is not None and not math.isfinite(args.minimum):
        parser.error("--minimum 必须为有限数")

    candidate = metric_value(load_task_metrics(args.result, args.task), args.metric)
    failures = []
    print(f"candidate={candidate:.10g}")

    if args.minimum is not None:
        print(f"minimum={args.minimum:.10g}")
        if candidate < args.minimum:
            failures.append(
                f"candidate {candidate:.10g} < minimum {args.minimum:.10g}"
            )

    if args.baseline is not None:
        baseline = metric_value(load_task_metrics(args.baseline, args.task), args.metric)
        floor = baseline - args.max_regression
        print(
            f"baseline={baseline:.10g} max_regression={args.max_regression:.10g} "
            f"allowed_floor={floor:.10g}"
        )
        if candidate < floor:
            failures.append(f"candidate {candidate:.10g} < allowed floor {floor:.10g}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        raise SystemExit(1)
    print("PASS: score threshold satisfied (sample/service acceptance not checked)")


if __name__ == "__main__":
    main()
