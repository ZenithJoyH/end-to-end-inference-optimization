#!/usr/bin/env python3
"""Exercise first-use FlagGems autotune tables from eight independent processes."""

import hashlib
import json
import multiprocessing as mp
import os
import sqlite3
import sys
import time
import traceback
from pathlib import Path

PRIVATE = Path('/opt/qwen38-acc011-cachefix-20260924')
CASE = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-011-full-gpqa-dual-cachefix-20260924')
DB = PRIVATE / 'caches/stress-first-use.db'


def worker(rank, barrier, queue):
    sys.path.insert(0, str(PRIVATE / 'FlagGems/src'))
    try:
        from flag_gems.utils.models.sql import SQLPersistantModel
        import flag_gems.utils.models.sql as sql_module

        if not str(Path(sql_module.__file__).resolve()).startswith(str(PRIVATE)):
            raise RuntimeError(f'wrong import path: {sql_module.__file__}')
        model = SQLPersistantModel(f'sqlite:///{DB}')
        barrier.wait(timeout=30)
        for item in range(8):
            table = f'acc011_first_use_{item}'
            model.put_benchmark(table, [item, 672, 32], {'num_warps': 4},
                                (float(rank + 1), float(rank + 1), float(rank + 1)))
            cls = model.get_sql_model(table, {'key_0': int, 'key_1': int,
                                              'key_2': int, 'num_warps': int})
            if cls is None:
                raise RuntimeError(f'missing table for {table}')
        queue.put({'rank': rank, 'ok': True, 'sql_path': sql_module.__file__})
    except BaseException:
        queue.put({'rank': rank, 'ok': False, 'error': traceback.format_exc()})


def main():
    if DB.exists():
        raise RuntimeError(f'stress DB already exists: {DB}')
    with sqlite3.connect(DB) as conn:
        if conn.execute('PRAGMA journal_mode=WAL').fetchone()[0].lower() != 'wal':
            raise RuntimeError('WAL not enabled')
    ctx = mp.get_context('spawn')
    barrier = ctx.Barrier(8)
    queue = ctx.Queue()
    workers = [ctx.Process(target=worker, args=(rank, barrier, queue)) for rank in range(8)]
    started = time.monotonic()
    for process in workers:
        process.start()
    results = [queue.get(timeout=180) for _ in workers]
    for process in workers:
        process.join(timeout=10)
    with sqlite3.connect(DB) as conn:
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'acc011_first_use_%'").fetchall()
        integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
    receipt = {'workers': results, 'table_count': len(tables), 'integrity': integrity,
               'elapsed_seconds': round(time.monotonic() - started, 3),
               'db_sha256': hashlib.sha256(DB.read_bytes()).hexdigest(),
               'child_exit_codes': [process.exitcode for process in workers]}
    path = CASE / 'evidence/sqlite-eight-process-stress.json'
    if path.exists():
        raise RuntimeError(f'receipt already exists: {path}')
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps(receipt, indent=2, sort_keys=True))
    if len(tables) != 8 or integrity != 'ok' or not all(item['ok'] for item in results) or any(process.exitcode != 0 for process in workers):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
