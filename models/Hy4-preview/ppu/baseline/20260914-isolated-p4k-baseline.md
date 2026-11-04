# 20260914 isolated P4K baseline

## Purpose

Create an optimization container from the effective adapted state of `hy4`, pass
the image-lineage and mount-parity gates, and establish the no-profiler P4K
baseline before changing any performance variable.

## Frozen identities

- Host: `PPU-07`
- Source container: `hy4`
- Expected source container ID:
  `550e93f0ba4c3109f05002d3a39c55d10c42eee13d661f3062757d9505535ca2`
- Remote work root: `/mnt/nfs/users/jinghao/hy4-preview/optimize`
- Remote case directory:
  `/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e`
- Adapted snapshot tag: `hy4-preview-adapted:20260914-e2e-source`
- Optimization container: `hy4-opt-20260914`
- Targeted workload: `P4096/D256/C64/N64`, finite batch
- First optimization variable after baseline: `max_num_batched_tokens=4096`

## Safety and comparison boundary

The source container itself is retained. Its exact `hy4` vLLM API service is
resolved from the model path, served name and port, checked for readiness, and
terminated gracefully before snapshotting so that the 16 PPUs can be assigned
to the optimization service. No unrelated container or process is stopped.

The optimization container inherits the committed writable-layer adaptation and
must have exactly the same effective directory mounts as the source. Runtime
configuration equality and code-state fingerprints are checked independently.
No performance or correctness run is allowed unless all three gates pass.

The first container-create attempt preserved all effective execution settings
except Docker's `StdinOnce` lifecycle bit (`true` versus source `false`). The
runtime gate rejected it before service launch. Its manifests are retained with
the `attempt1-` prefix. The scoped repair recreates the empty task-owned
container with `docker run -dit`, which preserves `StdinOnce=false`, then reruns
all gates.

The baseline service freezes the inherited P4K service arguments, explicitly
disables prefix caching, uses an isolated task cache, and leaves the native
extension bundle unavailable. Its first measurement therefore represents the
adapted FlagGems/reference path rather than a bundled-operator experiment.

The first service-launch wrapper exited before spawning vLLM because the vendor
SDK `envsetup.sh` reads optional positional argument `$1` and is incompatible
with caller-side `set -u`. The failed launcher is retained as
`attempt1-start-baseline-service.sh`; the corrected wrapper keeps `errexit` and
`pipefail` while matching the adapted launcher's shell semantics.

The next pre-launch attempt also exited before spawning vLLM because vLLM 0.24
uses scoped help and the default help page omits this flag. The retained
`attempt2-start-baseline-service.sh` used the default page; the final launcher
queries `--help=enable-prefix-caching` and still requires the explicit negative
flag before launch.

The third attempt reached vLLM but failed before weight loading because the
case-scoped `TMPDIR` plus a generated UUID exceeded Linux's 107-byte UNIX socket
path limit. Its log and partial cache are retained with `attempt3-` names. The
final launcher uses the optimization container's private `/tmp/hy4-b2048` only
for ephemeral IPC sockets; durable logs, compile caches and evidence remain in
the authorized remote case directory.

Before starting baseline-sanity, the task created heartbeat automation
`hy4-p4k-baseline-sanity-monitor` at a 30-minute cadence. It monitors only the
bound smoke/C8 process and result artifacts and is paused at terminal state.

The first raw-completions check is retained but manually classified
`incomplete`: its 64-token cap forced `finish_reason=length` for all nine
responses. The replacement reproduces the adaptation's fixed chat arithmetic
guard (`temperature=0`, `max_tokens=128`), checks exact final content and a
normal stop for one smoke plus eight concurrent requests.

The corrected chat guard passed 9/9 with exact final integers and
`finish_reason=stop` in 31.06 seconds. The monitor was paused immediately after
terminal completion. This is sufficient for the isolated performance baseline
but is not a formal accuracy acceptance gate.

The first performance-runner preparation stopped before dry-run because its
controller-side plan path resolved to `optimize/baseline` instead of the
platform `baseline/` directory. No benchmark request was sent; the corrected
playbook uses `../../../baseline` and preserves the already copied tool files.

The maintained runner dry-run freezes one warmup and two measured rounds of
`P4096/D256/C64/N64`, seeds 105003--105005, a 10,800-second per-round timeout,
and the baseline service/plan/comparison SHA-256 references. The background
worker records PID, start/finish time and exit code without changing the runner's
native evidence semantics.

This experiment supports P4K conclusions only. It does not establish baselines
or claims for P16K, P32K or P64K.

The first `P4096/D256/C64/N64` warmup was stopped after live progress and the
inherited P4K evidence projected a multi-hour per-round cost. The maintained
runner emitted a failed native receipt with return code `-15`; it is retained
and excluded from metrics. A `P4096/D32/C8/N8` scout was then re-frozen for the
2048 -> 4096 token-budget experiment. Its first run-id was stopped during
warmup when review found that the comparison contract needed to declare both
the structured setting and its `launch_args/20` representation. The corrected
run uses `baseline-2048-p4k-scout-02`; neither stopped run is reused.

## Remote evidence

The complete runtime manifests, copied commands, mount comparison, lineage
report, logs and raw evaluation results are stored under the remote case
directory above. Local project records retain summaries and exact remote paths.
