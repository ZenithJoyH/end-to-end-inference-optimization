#!/usr/bin/env python3
"""Summarize decode/prefill linear ConfigCache rows without modifying SQLite."""

from collections import Counter
import json
from pathlib import Path
import sqlite3


path = Path("/root/.flaggems/config_cache/TunedConfig_thead_triton_3_6.db")
table = "linear_kernel_6e3c9826717f75de99c38873cec5a163-0f015d35c97293819201f206510edb40"
supported = {
    (128, 256, 64, 8, 1, 3),
    (64, 256, 32, 4, 1, 4),
    (128, 128, 32, 4, 1, 4),
    (128, 64, 32, 4, 1, 4),
    (64, 128, 32, 4, 1, 4),
    (128, 32, 32, 4, 1, 4),
    (64, 32, 32, 2, 1, 5),
    (32, 64, 32, 2, 1, 5),
}
conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
quoted = '"' + table.replace('"', '""') + '"'
rows = list(conn.execute(f"SELECT * FROM {quoted} ORDER BY key_0,key_1,key_2"))
columns = [row[1] for row in conn.execute(f"PRAGMA table_info({quoted})")]
key_columns = [column for column in columns if column.startswith("key_")]
config_columns = [column for column in columns if not column.startswith("key_")]
key_count = len(key_columns)


def record(row):
    key = row[:key_count]
    config = tuple(row[key_count:])
    return {
        "key": dict(zip(key_columns, key)),
        "config": dict(zip(config_columns, config)),
        "supported_by_current_linear": config in supported,
    }


decode_rows = [record(row) for row in rows if int(row[0]) == 32]
decode_unsupported = [row for row in decode_rows if not row["supported_by_current_linear"]]
unsupported_all = [record(row) for row in rows if tuple(row[key_count:]) not in supported]
shape_counts = Counter((row[0], row[1], row[2]) for row in rows)
print(json.dumps({
    "database": str(path),
    "table": table,
    "columns": columns,
    "current_supported_configs": [list(item) for item in sorted(supported)],
    "row_count": len(rows),
    "unsupported_row_count": len(unsupported_all),
    "decode_aligned_m32_row_count": len(decode_rows),
    "decode_aligned_m32_unsupported_row_count": len(decode_unsupported),
    "decode_aligned_m32_rows": decode_rows,
    "top_shapes": [
        {"m": key[0], "n": key[1], "k": key[2], "rows": count}
        for key, count in shape_counts.most_common(40)
    ],
}, indent=2, sort_keys=True))
