"""Strict lm-eval sample structure validation; no inference from aggregate scores."""
import json
from pathlib import Path


def response_texts(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and value:
        return [text for item in value for text in response_texts(item)]
    raise ValueError("resps must contain nonempty lists of response strings")


def task_filters(task_config):
    """Expected lm-eval sample filters, taken from the frozen task definition."""
    definitions = task_config.get("filter_list")
    if definitions is None:
        return ["none"]  # ConfigurableTask's built-in default ensemble.
    if not isinstance(definitions, list) or not definitions:
        raise ValueError("task filter_list must be a nonempty list")
    names = [item.get("name") if isinstance(item, dict) else None for item in definitions]
    if any(not isinstance(name, str) or not name for name in names) or len(set(names)) != len(names):
        raise ValueError("task filter names must be explicit and distinct")
    return names


def validate_sample_file(path: Path, expected: int, expected_ids=None, allow_timeouts=False,
                         expected_filters=None):
    if isinstance(expected, bool) or not isinstance(expected, int) or expected < 1:
        raise ValueError("expected_samples must be a positive integer")
    ids = set()
    rows = set()
    raw_by_id = {}
    timeout_ids = set()
    if expected_filters is not None and (not expected_filters or any(
            not isinstance(name, str) or not name for name in expected_filters)
            or len(set(expected_filters)) != len(expected_filters)):
        raise ValueError("expected_filters must contain distinct nonempty names")
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"line {line_number}: expected an object")
            doc_id = record.get("doc_id")
            if isinstance(doc_id, bool) or not isinstance(doc_id, (int, str)) or str(doc_id).strip() == "":
                raise ValueError(f"line {line_number}: missing/invalid doc_id")
            key = str(doc_id)
            if expected_filters is None:
                if key in ids:
                    raise ValueError(f"line {line_number}: duplicate doc_id {key}")
            else:
                filter_name = record.get("filter")
                if filter_name not in expected_filters:
                    raise ValueError(f"doc_id {key}: missing/unexpected filter {filter_name!r}")
                row_key = (key, filter_name)
                if row_key in rows:
                    raise ValueError(f"duplicate doc_id/filter {row_key}")
                rows.add(row_key)
                # Separate metric filters may differ in filtered_resps/score,
                # but they must refer to the same model response and question.
                raw = json.dumps({name: record.get(name) for name in ("doc", "resps", "target", "arguments")},
                                 sort_keys=True, ensure_ascii=False, allow_nan=False)
                if key in raw_by_id and raw_by_id[key] != raw:
                    raise ValueError(f"doc_id {key}: conflicting raw content across filters")
                raw_by_id[key] = raw
            ids.add(key)
            texts = response_texts(record.get("resps"))
            if any(not text.strip() for text in texts):
                raise ValueError(f"doc_id {key}: empty response")
            if any("\ufffd" in text for text in texts):
                raise ValueError(f"doc_id {key}: Unicode replacement character")
            timeout = bool(record.get("timeout")) or any("<TIMEOUT>" in t for t in texts)
            if timeout:
                timeout_ids.add(key)
            if timeout and not allow_timeouts:
                raise ValueError(f"doc_id {key}: timeout")
            if record.get("finish_reason") in ("length", "max_tokens") or record.get("truncated") is True:
                raise ValueError(f"doc_id {key}: explicit truncation")
    if len(ids) != expected:
        raise ValueError(f"expected {expected} unique samples, found {len(ids)}")
    if expected_ids is not None and ids != {str(i) for i in expected_ids}:
        raise ValueError("sample IDs do not match the frozen dataset ID set")
    if expected_filters is not None and rows != {(key, name) for key in ids for name in expected_filters}:
        raise ValueError("samples do not contain the complete document/filter set")
    return {"unique_samples": len(ids), "timeouts": len(timeout_ids)}
