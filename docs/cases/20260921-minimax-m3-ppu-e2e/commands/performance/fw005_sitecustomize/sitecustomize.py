"""Diagnostic-only SIGUSR2 Python stack dump registration for fw-005."""

import faulthandler
import os
from pathlib import Path
import signal
import sys


_root = Path(os.environ["FW005_STACK_DIR"])
_root.mkdir(parents=True, exist_ok=True)
_stack_stream = (_root / f"python-stack-{os.getpid()}.log").open("a", buffering=1)
faulthandler.register(signal.SIGUSR2, file=_stack_stream, all_threads=True, chain=False)
print(f"FW005_FAULTHANDLER_READY pid={os.getpid()}", file=sys.stderr, flush=True)
