#!/usr/bin/env python3
# Compatibility-only: not the current GPQA/C8 accuracy workflow.
"""Legacy XingChen4 fixed-answer smoke check.

This module is retained for historical contract tests. New optimization work
uses the maintained evaluation and control entry points at the repository root.
"""

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import urllib.request
from urllib.parse import urlsplit, urlunsplit


QUESTIONS = (
    ("请只回答数字：1+1等于多少？", "2"),
    ("请只回答城市名：中国的首都是哪里？", "北京"),
    ("请只回答动物名：会发出喵声的常见宠物是什么？", "猫"),
)


def _plain_answer(value: str) -> str:
    value = value.strip()
    value = re.sub(r"[。！？!?；;，,]+\Z", "", value).strip()
    for marker in ("**", "__", "`"):
        if value.startswith(marker) and value.endswith(marker) and len(value) > 2 * len(marker):
            value = value[len(marker):-len(marker)].strip()
    value = re.sub(r"[。！？!?；;，,]+\Z", "", value).strip()
    return value


def answer_matches(content: str, expected: str) -> bool:
    """Accept one exact short answer, including equivalent decimal spelling."""
    if not isinstance(content, str) or not isinstance(expected, str):
        return False
    actual = _plain_answer(content)
    target = _plain_answer(expected)
    if not actual or not target:
        return False
    if actual == target:
        return True
    number = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)\Z")
    if not number.fullmatch(actual) or not number.fullmatch(target):
        return False
    try:
        return Decimal(actual) == Decimal(target)
    except InvalidOperation:
        return False


def endpoint(base_url: str) -> str:
    parsed = urlsplit(base_url.strip())
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("base URL must be HTTP(S) with a hostname")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("base URL must not contain credentials, query, or fragment")
    path = parsed.path.rstrip("/")
    if path in ("", "/v1"):
        path = "/v1/chat/completions"
    elif path != "/v1/chat/completions":
        raise ValueError("base URL path must be empty, /v1, or /v1/chat/completions")
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--base-url", required=True)
    result.add_argument("--model", required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--timeout", type=float, default=120)
    return result


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    if args.output.exists():
        parser().error(f"output already exists: {args.output}")
    if args.timeout <= 0:
        parser().error("--timeout must be positive")

    url = endpoint(args.base_url)
    records = []
    for prompt, expected in QUESTIONS:
        body = json.dumps({
            "model": args.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 16,
        }, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            payload = json.load(response)
        content = payload["choices"][0]["message"]["content"]
        records.append({
            "prompt": prompt,
            "expected": expected,
            "content": content,
            "passed": answer_matches(content, expected),
        })

    result = {
        "schema_version": 1,
        "model": args.model,
        "endpoint": url,
        "passed": all(record["passed"] for record in records),
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
