#!/usr/bin/env python3
"""Causal producer/consumer fence probe for PPU common-slot CUDA graphs."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import torch
from flag_gems.fused import compute_common_slot_mapping


NUM_REQS = 64
MAX_TOKENS = 4096
BLOCK_SIZE = 128
BLOCK_TABLE_COLS = 320


def sync() -> None:
    torch.cuda.synchronize()


def capture(fn):
    sync()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph, capture_error_mode="thread_local"):
        fn()
    sync()
    return graph


def producer(
    block_table: torch.Tensor,
    slot_mapping: torch.Tensor,
    query_start_loc: torch.Tensor,
    positions: torch.Tensor,
    seq_lens: torch.Tensor,
    num_computed_tokens: torch.Tensor,
) -> None:
    compute_common_slot_mapping(
        block_table,
        slot_mapping,
        NUM_REQS,
        query_start_loc,
        positions,
        seq_lens,
        num_computed_tokens,
        max_num_batched_tokens=MAX_TOKENS,
        block_size=BLOCK_SIZE,
        total_cp_world_size=1,
        total_cp_rank=0,
        cp_kv_cache_interleave_size=1,
        null_block_id=0,
        pad_slot_id=-1,
        update_num_computed_tokens=True,
    )


def make_inputs(offset: int):
    device = "cuda"
    block_table = torch.arange(
        1 + offset,
        1 + offset + NUM_REQS * BLOCK_TABLE_COLS,
        dtype=torch.int32,
        device=device,
    ).reshape(NUM_REQS, BLOCK_TABLE_COLS)
    query_start_loc = torch.arange(NUM_REQS + 1, dtype=torch.int32, device=device)
    positions = torch.zeros(MAX_TOKENS, dtype=torch.int64, device=device)
    positions[:NUM_REQS] = torch.arange(
        offset, offset + NUM_REQS, dtype=torch.int64, device=device
    )
    seq_lens = torch.arange(
        offset + 1, offset + 1 + NUM_REQS, dtype=torch.int32, device=device
    )
    return block_table, query_start_loc, positions, seq_lens


def reference(inputs):
    slot = torch.full((MAX_TOKENS,), -777, dtype=torch.int64, device="cuda")
    computed = torch.full((NUM_REQS,), -777, dtype=torch.int32, device="cuda")
    producer(inputs[0], slot, inputs[1], inputs[2], inputs[3], computed)
    sync()
    return slot.clone(), computed.clone()


def make_consumer(slot, computed, expected_slot, expected_computed, mismatch):
    def consume():
        mismatch.add_((slot != expected_slot).to(torch.int64).sum())
        mismatch.add_((computed != expected_computed).to(torch.int64).sum())

    return consume


def run_arm(
    arm: str,
    producer_graphs,
    consumer_graphs,
    producer_fns,
    mismatch: torch.Tensor,
    repeats: int,
) -> dict:
    producer_stream = torch.cuda.current_stream()
    consumer_stream = torch.cuda.Stream()
    event = torch.cuda.Event(blocking=False)
    mismatch.zero_()
    sync()
    start = time.perf_counter()
    for i in range(repeats):
        idx = i & 1
        if arm == "host_sync":
            with torch.cuda.stream(producer_stream):
                producer_graphs[idx].replay()
                producer_stream.synchronize()
                consumer_graphs[idx].replay()
                producer_stream.synchronize()
        elif arm == "no_fence":
            with torch.cuda.stream(producer_stream):
                producer_graphs[idx].replay()
                consumer_graphs[idx].replay()
                producer_stream.synchronize()
        elif arm == "event_wait":
            with torch.cuda.stream(producer_stream):
                producer_graphs[idx].replay()
                event.record(producer_stream)
            consumer_stream.wait_event(event)
            with torch.cuda.stream(consumer_stream):
                consumer_graphs[idx].replay()
            consumer_stream.synchronize()
        elif arm == "eager_same_stream":
            with torch.cuda.stream(producer_stream):
                producer_fns[idx]()
                consumer_graphs[idx].replay()
            producer_stream.synchronize()
        else:
            raise ValueError(arm)
    sync()
    elapsed = time.perf_counter() - start
    return {
        "arm": arm,
        "repeats": repeats,
        "mismatch_count": int(mismatch.item()),
        "wall_seconds": elapsed,
        "wall_us_per_pair": elapsed * 1e6 / repeats,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--repeats", type=int, default=1000)
    parser.add_argument("--rounds", type=int, default=3)
    args = parser.parse_args()

    torch.manual_seed(20260920)
    torch.cuda.set_device(0)
    inputs = [make_inputs(0), make_inputs(257)]
    references = [reference(item) for item in inputs]
    slot = torch.full((MAX_TOKENS,), -999, dtype=torch.int64, device="cuda")
    computed = torch.full((NUM_REQS,), -999, dtype=torch.int32, device="cuda")
    mismatch = torch.zeros((), dtype=torch.int64, device="cuda")

    producer_fns = [
        lambda item=item: producer(
            item[0], slot, item[1], item[2], item[3], computed
        )
        for item in inputs
    ]
    producer_graphs = [capture(fn) for fn in producer_fns]
    consumer_fns = [
        make_consumer(slot, computed, refs[0], refs[1], mismatch)
        for refs in references
    ]
    consumer_graphs = [capture(fn) for fn in consumer_fns]

    # Captures execute once and mutate shared buffers/counters; reset before tests.
    mismatch.zero_()
    slot.fill_(-999)
    computed.fill_(-999)
    sync()

    arms = ["host_sync", "no_fence", "event_wait", "eager_same_stream"]
    results = []
    for arm in arms:
        for round_idx in range(args.rounds):
            row = run_arm(
                arm,
                producer_graphs,
                consumer_graphs,
                producer_fns,
                mismatch,
                args.repeats,
            )
            row["round"] = round_idx
            results.append(row)

    summaries = {}
    for arm in arms:
        rows = [row for row in results if row["arm"] == arm]
        summaries[arm] = {
            "mismatch_counts": [row["mismatch_count"] for row in rows],
            "wall_us_per_pair_median": statistics.median(
                row["wall_us_per_pair"] for row in rows
            ),
            "correct": all(row["mismatch_count"] == 0 for row in rows),
        }

    payload = {
        "schema_version": 1,
        "device": torch.cuda.get_device_name(0),
        "torch_version": torch.__version__,
        "shape": {
            "num_reqs": NUM_REQS,
            "max_num_batched_tokens": MAX_TOKENS,
            "block_size": BLOCK_SIZE,
            "block_table_cols": BLOCK_TABLE_COLS,
        },
        "capture_and_two_replay_gate": {},
        "results": results,
        "summaries": summaries,
        "interpretation_boundary": (
            "Exact common-slot producer kernels with alternating outputs and a "
            "GPU consumer. This is a causal stream-ordering probe, not an end-to-end "
            "performance result; service graph/canonical and same-device A/B/R remain "
            "mandatory for any promoted candidate."
        ),
    }

    # Explicitly prove each graph can replay at least twice after all measurements.
    for idx in range(2):
        mismatch.zero_()
        for _ in range(2):
            producer_graphs[idx].replay()
            torch.cuda.current_stream().synchronize()
            consumer_graphs[idx].replay()
            torch.cuda.current_stream().synchronize()
        payload["capture_and_two_replay_gate"][str(idx)] = {
            "passed": int(mismatch.item()) == 0,
            "mismatch_count": int(mismatch.item()),
        }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
