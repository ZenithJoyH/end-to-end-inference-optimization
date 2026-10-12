#!/usr/bin/env python3
"""Prepare a private FlagGems cache-lock fix without modifying live imports."""

import difflib
import hashlib
import json
import shutil
import sqlite3
import subprocess
from pathlib import Path

SOURCE = Path('/workspace/FlagGems')
PRIVATE = Path('/opt/qwen38-acc011-cachefix-20260924')
CASE = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-011-full-gpqa-dual-cachefix-20260924')
EXPECTED_SQL_SHA256 = '6dc19cb581d70154f14b95ed9112d682c6b5919b6cf3f8dea01a78a75ec0efd7'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(content, old, new):
    if content.count(old) != 1:
        raise RuntimeError(f'expected exactly one occurrence, found {content.count(old)}: {old[:80]!r}')
    return content.replace(old, new, 1)


def patch_sql(content):
    content = replace_once(content, 'import os\nfrom hashlib import md5',
                           'import os\nimport time\nfrom functools import wraps\nfrom hashlib import md5')
    marker = 'from .session import RollbackSession\n\n\nclass Base'
    addition = '''from .session import RollbackSession


def retry_sqlite_locked(method):
    """Retry transient inter-process SQLite locks; preserve other SQL failures."""

    @wraps(method)
    def wrapped(self, *args, **kwargs):
        for attempt in range(4):
            try:
                return method(self, *args, **kwargs)
            except sqlalchemy.exc.OperationalError as error:
                if (
                    self.engine.dialect.name != "sqlite"
                    or "database is locked" not in str(error).lower()
                    or attempt == 3
                ):
                    raise
                time.sleep(0.1 * (2**attempt))

    return wrapped


class Base'''
    content = replace_once(content, marker, addition)
    content = replace_once(
        content,
        'self.engine: Final[sqlalchemy.engine.Engine] = sqlalchemy.create_engine(db_url)',
        '''# TP workers may create the same autotune table concurrently. Give the
        # SQLite writer a bounded wait before the lock-specific retry below.
        connect_args = {"timeout": 15.0} if db_url.startswith("sqlite:") else {}
        self.engine: Final[sqlalchemy.engine.Engine] = sqlalchemy.create_engine(
            db_url, connect_args=connect_args
        )''',
    )
    for old, new in (
        ('    def get_sql_model(\n', '    @retry_sqlite_locked\n    def get_sql_model(\n'),
        ('    @override\n    def get_config(\n', '    @override\n    @retry_sqlite_locked\n    def get_config(\n'),
        ('    @override\n    def get_benchmark(\n', '    @override\n    @retry_sqlite_locked\n    def get_benchmark(\n'),
        ('    def put_config(\n', '    @retry_sqlite_locked\n    def put_config(\n'),
        ('    def put_benchmark(\n', '    @retry_sqlite_locked\n    def put_benchmark(\n'),
    ):
        content = replace_once(content, old, new)
    return content


def main():
    original_sql = SOURCE / 'src/flag_gems/utils/models/sql.py'
    if sha(original_sql) != EXPECTED_SQL_SHA256:
        raise RuntimeError('source SQL SHA changed; refusing patch')
    if PRIVATE.exists() or CASE.exists():
        raise RuntimeError('private source or acc-011 case already exists; refusing overwrite')
    if SOURCE.is_symlink() or not SOURCE.is_dir():
        raise RuntimeError('unexpected source path')
    CASE.mkdir(parents=True, exist_ok=False)
    for name in ('commands', 'evidence', 'services', 'evaluation', 'results'):
        (CASE / name).mkdir()
    shutil.copytree(SOURCE, PRIVATE / 'FlagGems')
    target = PRIVATE / 'FlagGems/src/flag_gems/utils/models/sql.py'
    original = target.read_text()
    updated = patch_sql(original)
    target.write_text(updated)
    (CASE / 'evidence/flag_gems_sql.patch').write_text(''.join(difflib.unified_diff(
        original.splitlines(keepends=True), updated.splitlines(keepends=True),
        fromfile='a/src/flag_gems/utils/models/sql.py',
        tofile='b/src/flag_gems/utils/models/sql.py')))
    subprocess.run(['python3', '-m', 'py_compile', str(target)], check=True)
    source_db = Path('/root/.flaggems/config_cache/TunedConfig_thead_triton_3_6.db')
    if not source_db.is_file():
        raise RuntimeError('source cache DB missing')
    caches = PRIVATE / 'caches'
    caches.mkdir()
    for port in (8000, 8010):
        destination = caches / f'port{port}.db'
        with sqlite3.connect(f'file:{source_db}?mode=ro', uri=True) as src:
            with sqlite3.connect(destination) as dst:
                src.backup(dst)
        with sqlite3.connect(destination, timeout=30) as dst:
            mode = dst.execute('PRAGMA journal_mode=WAL').fetchone()[0]
            if mode.lower() != 'wal':
                raise RuntimeError(f'WAL mode not enabled for {port}: {mode}')
            check = dst.execute('PRAGMA integrity_check').fetchone()[0]
            if check != 'ok':
                raise RuntimeError(f'cache copy integrity check failed for {port}: {check}')
    receipt = {
        'source': str(SOURCE), 'private': str(PRIVATE), 'case': str(CASE),
        'source_git_head': subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip(),
        'source_git_status': subprocess.check_output(['git', '-C', str(SOURCE), 'status', '--short'], text=True).strip().splitlines(),
        'sql_source_sha256': sha(original_sql), 'sql_private_sha256': sha(target),
        'patch_sha256': sha(CASE / 'evidence/flag_gems_sql.patch'),
        'cache_source_sha256': sha(source_db),
        'cache_copies': {str(port): {'path': str(caches / f'port{port}.db'),
                                     'sha256': sha(caches / f'port{port}.db')}
                         for port in (8000, 8010)},
        'rollback': 'Stop only scoped target services, then relaunch with original /workspace/FlagGems/src and original FLAGGEMS_DB_URL environment; keep original DB untouched.',
    }
    (CASE / 'evidence/cachefix-preparation.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
