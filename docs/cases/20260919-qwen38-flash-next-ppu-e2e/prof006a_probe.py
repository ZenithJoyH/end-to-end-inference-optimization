"""Low-overhead prof006a host/device handoff recorder.

This file is copied to ``vllm_fl/prof006a.py`` by the frozen
installer.  It is deliberately inert unless VLLM_FL_PROF006A_ARM is exactly
``event`` or ``event_host``.
"""

from __future__ import annotations

from array import array
import json
import os
from pathlib import Path
import signal
import time
from typing import Any, Callable


_ARMS = {"event", "event_host"}
_ENGINE_PROBE: EngineProbe | None = None
_EXECUTOR_PATCHED = False
_SCHEDULER_PATCHED = False
_EXECUTOR_INSTANCE: Any | None = None


def _config() -> tuple[str, Path, int] | None:
    arm = os.environ.get("VLLM_FL_PROF006A_ARM", "")
    if arm not in _ARMS:
        return None
    output_dir = os.environ.get("VLLM_FL_PROF006A_DIR", "")
    if not output_dir.startswith("/"):
        raise RuntimeError("VLLM_FL_PROF006A_DIR must be an absolute path")
    capacity = int(os.environ.get("VLLM_FL_PROF006A_CAPACITY", "1024"))
    if capacity < 1024 or capacity > 16384:
        raise RuntimeError("VLLM_FL_PROF006A_CAPACITY must be in [1024, 16384]")
    return arm, Path(output_dir), capacity


def enabled() -> bool:
    return _config() is not None


def _self_start_ticks() -> int:
    raw = Path(f"/proc/{os.getpid()}/stat").read_text(encoding="utf-8")
    return int(raw[raw.rfind(")") + 2 :].split()[19])


class _Flushable:
    def __init__(self, role: str, arm: str, output_dir: Path, capacity: int):
        self.role = role
        self.arm = arm
        self.output_dir = output_dir
        self.capacity = capacity
        self.count = 0
        self.dropped = 0
        self.active = False
        if signal.getsignal(signal.SIGUSR1) is not signal.SIG_DFL:
            raise RuntimeError("SIGUSR1 already has a handler; refusing prof006a")
        if signal.getsignal(signal.SIGUSR2) is not signal.SIG_DFL:
            raise RuntimeError("SIGUSR2 already has a handler; refusing prof006a")
        self._flush_requested = False
        signal.signal(signal.SIGUSR1, self._activate)
        signal.signal(signal.SIGUSR2, self._request_flush)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        registration = self.output_dir / f"{self.role}-pid{os.getpid()}.registration.json"
        registration.write_text(
            json.dumps(
                {
                    "schema": "prof006a-registration-v1",
                    "role": self.role,
                    "arm": self.arm,
                    "pid": os.getpid(),
                    "start_ticks": _self_start_ticks(),
                    "source_path": str(Path(__file__).resolve()),
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    def _activate(self, _signum: int, _frame: Any) -> None:
        self.count = 0
        self.dropped = 0
        if hasattr(self, "_open_slot"):
            self._open_slot = -1
        self.active = True

    def _request_flush(self, _signum: int, _frame: Any) -> None:
        self.active = False
        if getattr(self, "_open_slot", -1) >= 0:
            # The controller promises a quiescent service before SIGUSR2.  If
            # that contract is violated, invalidate the capture explicitly.
            self.dropped += 1
            self._open_slot = -1
        self._flush_requested = True

    def _flush_if_requested(self) -> None:
        if not self._flush_requested:
            return
        self._flush_requested = False
        try:
            # The controller sends one unmeasured trigger request after SIGUSR2,
            # so this runs on the normal engine/worker execution thread rather
            # than a device-API-unsafe background thread.
            self.flush()
        except BaseException as exc:
            self._atomic_write(
                {
                    "schema": "prof006a-error-v1",
                    "role": self.role,
                    "arm": self.arm,
                    "pid": os.getpid(),
                    "error": f"{type(exc).__name__}: {exc}",
                },
                suffix="error",
            )

    def flush_now(self) -> None:
        self.active = False
        self._flush_requested = False
        self.flush()

    def _atomic_write(self, payload: dict[str, Any], suffix: str = "result") -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        destination = self.output_dir / f"{self.role}-pid{os.getpid()}.{suffix}.json"
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temporary, destination)

    def flush(self) -> None:
        raise NotImplementedError


class EngineProbe(_Flushable):
    """Preallocated engine-process ring for schedule and RPC handoff."""

    def __init__(self, arm: str, output_dir: Path, capacity: int):
        super().__init__("engine", arm, output_dir, capacity)
        self.num_new = array("i", [0]) * capacity
        self.num_cached = array("i", [0]) * capacity
        self.total_tokens = array("q", [0]) * capacity
        self.schedule_start = array("q", [0]) * capacity
        self.schedule_end = array("q", [0]) * capacity
        self.dispatch_start = array("q", [0]) * capacity
        self.dispatch_return = array("q", [0]) * capacity
        self._open_slot = -1

    @property
    def host_enabled(self) -> bool:
        return self.arm == "event_host"

    def begin_schedule(self) -> None:
        self._flush_if_requested()
        if not self.active or not self.host_enabled:
            return
        slot = self.count
        if slot >= self.capacity:
            self.dropped += 1
            self._open_slot = -1
            return
        self._open_slot = slot
        self.schedule_start[slot] = time.perf_counter_ns()

    def end_schedule(self, scheduler_output: Any) -> None:
        if not self.host_enabled or self._open_slot < 0:
            return
        slot = self._open_slot
        self.schedule_end[slot] = time.perf_counter_ns()
        self.num_new[slot] = len(scheduler_output.scheduled_new_reqs)
        self.num_cached[slot] = len(scheduler_output.scheduled_cached_reqs.req_ids)
        self.total_tokens[slot] = scheduler_output.total_num_scheduled_tokens

    def begin_dispatch(self) -> None:
        if self.host_enabled and self._open_slot >= 0:
            self.dispatch_start[self._open_slot] = time.perf_counter_ns()

    def end_dispatch(self) -> None:
        if not self.host_enabled or self._open_slot < 0:
            return
        self.dispatch_return[self._open_slot] = time.perf_counter_ns()
        self.count += 1
        self._open_slot = -1

    def flush(self) -> None:
        receipts = flush_worker_probes()
        rows = []
        for slot in range(self.count):
            rows.append(
                {
                    "step": slot,
                    "num_new": self.num_new[slot],
                    "num_cached": self.num_cached[slot],
                    "total_tokens": self.total_tokens[slot],
                    "schedule_start_ns": self.schedule_start[slot],
                    "schedule_end_ns": self.schedule_end[slot],
                    "dispatch_start_ns": self.dispatch_start[slot],
                    "dispatch_return_ns": self.dispatch_return[slot],
                }
            )
        self._atomic_write(
            {
                "schema": "prof006a-engine-v1",
                "role": self.role,
                "arm": self.arm,
                "pid": os.getpid(),
                "capacity": self.capacity,
                "count": self.count,
                "dropped": self.dropped,
                "worker_flush_receipts": receipts,
                "rows": rows,
            }
        )


class WorkerProbe(_Flushable):
    """Preallocated worker host ring and device-event pairs."""

    def __init__(
        self,
        rank: int,
        arm: str,
        output_dir: Path,
        capacity: int,
        device_api: Any,
    ):
        super().__init__(f"worker-rank{rank}", arm, output_dir, capacity)
        self.rank = rank
        self.device_api = device_api
        self.num_new = array("i", [0]) * capacity
        self.num_cached = array("i", [0]) * capacity
        self.total_tokens = array("q", [0]) * capacity
        self.worker_entry = array("q", [0]) * capacity
        self.graph_enqueue = array("q", [0]) * capacity
        self.graph_return = array("q", [0]) * capacity
        self.worker_return = array("q", [0]) * capacity
        self.previous_graph_complete_at_entry = array("b", [0]) * capacity
        self.starts = [device_api.Event(enable_timing=True) for _ in range(capacity)]
        self.ends = [device_api.Event(enable_timing=True) for _ in range(capacity)]
        if not hasattr(self.ends[0], "query") or not hasattr(
            self.starts[0], "elapsed_time"
        ):
            raise RuntimeError(
                "device Event.query and Event.elapsed_time are required for causal idle proof"
            )
        self._open_slot = -1

    @property
    def host_enabled(self) -> bool:
        return self.arm == "event_host"

    def begin_step(self, scheduler_output: Any) -> None:
        self._flush_if_requested()
        if not self.active:
            return
        slot = self.count
        if slot >= self.capacity:
            self.dropped += 1
            self._open_slot = -1
            return
        self._open_slot = slot
        self.num_new[slot] = len(scheduler_output.scheduled_new_reqs)
        self.num_cached[slot] = len(scheduler_output.scheduled_cached_reqs.req_ids)
        self.total_tokens[slot] = scheduler_output.total_num_scheduled_tokens
        if slot > 0:
            self.previous_graph_complete_at_entry[slot] = int(
                bool(self.ends[slot - 1].query())
            )
        if self.host_enabled:
            self.worker_entry[slot] = time.perf_counter_ns()

    def begin_graph(self) -> None:
        slot = self._open_slot
        if slot < 0:
            return
        if self.host_enabled:
            self.graph_enqueue[slot] = time.perf_counter_ns()
        self.starts[slot].record()

    def end_graph(self) -> None:
        slot = self._open_slot
        if slot < 0:
            return
        self.ends[slot].record()
        if self.host_enabled:
            self.graph_return[slot] = time.perf_counter_ns()

    def end_step(self) -> None:
        if self._open_slot < 0:
            return
        if self.host_enabled:
            self.worker_return[self._open_slot] = time.perf_counter_ns()
        self.count += 1
        self._open_slot = -1

    def flush(self) -> None:
        # Flush happens only after the benchmark client is complete and SIGUSR2
        # is sent.  There is no synchronize/item/logging in the measured path.
        self.device_api.synchronize()
        rows = []
        previous_end = None
        for slot in range(self.count):
            duration_us = float(self.starts[slot].elapsed_time(self.ends[slot])) * 1000.0
            idle_us = None
            if previous_end is not None:
                idle_us = float(previous_end.elapsed_time(self.starts[slot])) * 1000.0
            previous_end = self.ends[slot]
            row = {
                "step": slot,
                "num_new": self.num_new[slot],
                "num_cached": self.num_cached[slot],
                "total_tokens": self.total_tokens[slot],
                "graph_duration_us": duration_us,
                "inter_graph_idle_us": idle_us,
                "previous_graph_complete_at_entry": bool(
                    self.previous_graph_complete_at_entry[slot]
                ),
            }
            if self.host_enabled:
                row.update(
                    {
                        "worker_entry_ns": self.worker_entry[slot],
                        "graph_enqueue_ns": self.graph_enqueue[slot],
                        "graph_return_ns": self.graph_return[slot],
                        "worker_return_ns": self.worker_return[slot],
                    }
                )
            rows.append(row)
        self._atomic_write(
            {
                "schema": "prof006a-worker-v1",
                "role": self.role,
                "rank": self.rank,
                "arm": self.arm,
                "pid": os.getpid(),
                "capacity": self.capacity,
                "count": self.count,
                "dropped": self.dropped,
                "rows": rows,
            }
        )


def create_engine_probe() -> EngineProbe | None:
    global _ENGINE_PROBE
    config = _config()
    if config is None:
        return None
    if _ENGINE_PROBE is None:
        arm, output_dir, capacity = config
        _ENGINE_PROBE = EngineProbe(arm, output_dir, capacity)
    return _ENGINE_PROBE


def create_worker_probe(rank: int, device_api: Any) -> WorkerProbe | None:
    config = _config()
    if config is None:
        return None
    arm, output_dir, capacity = config
    return WorkerProbe(rank, arm, output_dir, capacity, device_api)


def install_multiproc_executor_probe() -> None:
    """Wrap the exact fixed-revision MultiprocExecutor dispatch boundary."""
    global _EXECUTOR_PATCHED
    config = _config()
    if _EXECUTOR_PATCHED or config is None:
        return
    from vllm.v1.executor.multiproc_executor import MultiprocExecutor

    original: Callable[..., Any] = MultiprocExecutor.execute_model
    if getattr(original, "_prof006a_wrapped", False):
        _EXECUTOR_PATCHED = True
        return

    def execute_model(self, scheduler_output, non_block=False):
        global _EXECUTOR_INSTANCE
        _EXECUTOR_INSTANCE = self
        probe = _ENGINE_PROBE
        if probe is not None and probe.host_enabled:
            probe.begin_dispatch()
        try:
            return original(self, scheduler_output, non_block=non_block)
        finally:
            if probe is not None and probe.host_enabled:
                probe.end_dispatch()

    execute_model._prof006a_wrapped = True  # type: ignore[attr-defined]
    MultiprocExecutor.execute_model = execute_model
    _EXECUTOR_PATCHED = True


def flush_worker_probes() -> list[Any]:
    executor = _EXECUTOR_INSTANCE
    if executor is None:
        raise RuntimeError("MultiprocExecutor instance was not observed before flush")
    receipts = executor.collective_rpc("prof006a_flush", timeout=120)
    if not isinstance(receipts, list) or len(receipts) != 8:
        raise RuntimeError(f"expected eight worker flush receipts, got {receipts!r}")
    return receipts


def install_scheduler_probe() -> None:
    """Install a lazy probe on the stock fixed-revision Scheduler class.

    The general Plugin entry point runs in several process roles.  Patching the
    class there is harmless; the registration and rings are created only in the
    process that actually constructs a Scheduler instance.
    """
    global _SCHEDULER_PATCHED
    config = _config()
    if _SCHEDULER_PATCHED or config is None:
        return
    from vllm.v1.core.sched.scheduler import Scheduler

    original_init: Callable[..., Any] = Scheduler.__init__
    original_schedule: Callable[..., Any] = Scheduler.schedule
    if getattr(original_schedule, "_prof006a_wrapped", False):
        _SCHEDULER_PATCHED = True
        return

    def scheduler_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self._prof006a_probe = create_engine_probe()
        install_multiproc_executor_probe()

    def schedule(self, *args, **kwargs):
        probe = getattr(self, "_prof006a_probe", None)
        if probe is None:
            return original_schedule(self, *args, **kwargs)
        probe.begin_schedule()
        scheduler_output = original_schedule(self, *args, **kwargs)
        probe.end_schedule(scheduler_output)
        return scheduler_output

    scheduler_init._prof006a_wrapped = True  # type: ignore[attr-defined]
    schedule._prof006a_wrapped = True  # type: ignore[attr-defined]
    Scheduler.__init__ = scheduler_init
    Scheduler.schedule = schedule
    _SCHEDULER_PATCHED = True
