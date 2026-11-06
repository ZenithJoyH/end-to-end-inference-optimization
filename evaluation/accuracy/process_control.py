"""Cancellation-aware evaluator processes; no model or scoring behavior here."""
import os
import signal
import subprocess
import threading
import time
from datetime import datetime


def _signal_group(process, sig):
    # The session leader may already have exited while evaluator descendants
    # still own the PGID and stdout pipe. Its exit code is not group liveness.
    try:
        os.killpg(process.pid, sig)
    except ProcessLookupError:
        pass


def _group_exists(process):
    try:
        os.killpg(process.pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # EPERM is not ESRCH: the group may still exist (including a transient
        # orphan/zombie permission state). Keep waiting/escalating until absence
        # is proven. Real signal failures remain errors in _signal_group.
        return True
    return True


def _reap(process):
    """Bound cleanup of our own process group, including unresponsive children."""
    for sig in (None, signal.SIGTERM, signal.SIGKILL):
        if sig is not None:
            _signal_group(process, sig)
        deadline = time.monotonic() + 5
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            if sig == signal.SIGKILL:
                raise
            continue
        # Reap our direct child, then allow descendants (including temporarily
        # adopted zombies) to disappear. Escalate even when the leader exited 0.
        while _group_exists(process):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(0.02, remaining))
        else:
            return
    raise subprocess.TimeoutExpired(f"process group {process.pid}", 15)


class Cancellation:
    """Share cancellation across parallel shards, including retry delays."""

    def __init__(self):
        self.event = threading.Event()
        self._lock = threading.Lock()
        self._processes = set()

    def check(self):
        if self.event.is_set():
            raise KeyboardInterrupt("accuracy evaluation cancelled")

    def start(self, command, **kwargs):
        # Cancellation cannot race between launching and registering a child.
        # A main-thread SIGINT must also not interrupt Popen before we retain its
        # handle. Defer the standard KeyboardInterrupt until the caller stores
        # the registered process; unlike a signal mask, this does not make the
        # exec'd child inherit blocked SIGINT. Worker launches use the lock.
        defer_sigint = (threading.current_thread() is threading.main_thread()
                        and signal.getsignal(signal.SIGINT) is signal.default_int_handler)
        interrupted = False

        def defer(signum, frame):
            nonlocal interrupted
            interrupted = True

        if defer_sigint:
            signal.signal(signal.SIGINT, defer)
        try:
            with self._lock:
                self.check()
                process = subprocess.Popen(command, start_new_session=True, **kwargs)
                self._processes.add(process)
        finally:
            if defer_sigint:
                signal.signal(signal.SIGINT, signal.default_int_handler)
            if interrupted:
                self.event.set()
        return process

    def release(self, process):
        with self._lock:
            self._processes.discard(process)

    def cancel(self):
        with self._lock:
            self.event.set()
            processes = tuple(self._processes)
        # Signal every shard before waiting for any one of them.
        for process in processes:
            _signal_group(process, signal.SIGINT)
        for process in processes:
            _reap(process)

    def sleep(self, seconds):
        self.event.wait(seconds)
        self.check()


def run_streaming(command, log_file, sidecar_command=None, *, cancellation=None,
                  print_line=None):
    """Preserve ordinary exit codes, but never turn cancellation into a retry."""
    cancellation = cancellation or Cancellation()
    cancellation.check()
    print_line = print_line or (lambda line: print(line, end="", flush=True))
    process = sidecar = None
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(f"[{datetime.now().isoformat(timespec='seconds')}] command={' '.join(command)}\n")
        handle.flush()
        try:
            process = cancellation.start(command, stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT, text=True, bufsize=1)
            cancellation.check()
            if sidecar_command:
                sidecar = cancellation.start(sidecar_command + ["--pid", str(process.pid)])
                cancellation.check()
            assert process.stdout is not None
            for line in process.stdout:
                handle.write(line)
                handle.flush()
                print_line(line)
            return_code = process.wait()
            cancellation.check()
            if return_code in (-signal.SIGINT, -signal.SIGTERM):
                raise KeyboardInterrupt("evaluator was interrupted")
            return return_code
        except BaseException:
            cancellation.cancel()
            raise
        finally:
            if sidecar is not None:
                try:
                    _reap(sidecar)
                finally:
                    cancellation.release(sidecar)
            if process is not None:
                cancellation.release(process)
                if process.stdout is not None:
                    process.stdout.close()
