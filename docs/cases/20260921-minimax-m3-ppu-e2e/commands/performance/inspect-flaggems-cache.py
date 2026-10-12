#!/usr/bin/env python3
"""Read-only inventory of the live FlagGems tuning database."""

import json
from pathlib import Path
import sqlite3
from collections import Counter


path = Path("/root/.flaggems/config_cache/TunedConfig_thead_triton_3_6.db")
connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
tables = []
for (name,) in connection.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
):
    quoted = '"' + name.replace('"', '""') + '"'
    columns = [row[1] for row in connection.execute(f"PRAGMA table_info({quoted})")]
    count = connection.execute(f"SELECT count(*) FROM {quoted}").fetchone()[0]
    table = {"name": name, "columns": columns, "rows": count}
    if name.startswith("linear_kernel_"):
        table["sample_rows"] = [
            list(row) for row in connection.execute(f"SELECT * FROM {quoted} LIMIT 12")
        ]
        if "p50" not in columns:
            config_indexes = [
                index for index, column in enumerate(columns) if not column.startswith("key_")
            ]
            distribution = Counter(
                tuple(row[index] for index in config_indexes)
                for row in connection.execute(f"SELECT * FROM {quoted}")
            )
            table["config_columns"] = [columns[index] for index in config_indexes]
            table["best_config_distribution"] = [
                {"config": list(config), "rows": rows}
                for config, rows in distribution.most_common()
            ]
    tables.append(table)
stat = path.stat()
linear_tables = [table for table in tables if table["name"].startswith("linear_kernel_")]
print(
    json.dumps(
        {
            "path": str(path),
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "journal_mode": connection.execute("PRAGMA journal_mode").fetchone()[0],
            "summary": {
                "table_count": len(tables),
                "total_rows": sum(table["rows"] for table in tables),
                "linear_table_count": len(linear_tables),
                "linear_total_rows": sum(table["rows"] for table in linear_tables),
            },
            "tables": tables,
        },
        indent=2,
        sort_keys=True,
    )
)
