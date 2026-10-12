"""Diagnostic-only real-time-signal Python stack dump registration for fw-005 v3."""

import faulthandler
import os
from pathlib import Path
import sys


_signal_number = 40
_root = Path(os.environ["FW005_STACK_DIR"])
_root.mkdir(parents=True, exist_ok=True)
_stack_stream = (_root / f"python-stack-{os.getpid()}.log").open("a", buffering=1)
faulthandler.register(_signal_number, file=_stack_stream, all_threads=True, chain=False)
print(
    f"FW005V3_FAULTHANDLER_READY pid={os.getpid()} signal={_signal_number}",
    file=sys.stderr,
    flush=True,
)
