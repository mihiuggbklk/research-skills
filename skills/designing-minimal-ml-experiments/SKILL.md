---
name: designing-minimal-ml-experiments
description: Use when turning an AI/ML theory claim into a minimal runnable PyTorch experiment that must work locally and in Colab, especially with thin notebooks, external helpers, Drive resume, visible progress, calibrated scaling, or automatic result-bundle download.
---

# Designing Minimal ML Experiments

## Core Principle

Test one falsifiable mechanism claim with the smallest runnable evidence that
can distinguish it from a strong equal-compute baseline. Minimal means the
smallest understandable execution boundary, not necessarily one file. A thin
notebook plus a few ordinary Python modules is often more minimal than an
800-line self-contained notebook.

Do not build a framework, service, CI system, dashboard, or maintenance layer
unless the experiment cannot run without it. Keep only helpers that are used by
the experiment or by its verification.

## Workflow

### 1. Freeze The Research Contract

Write the contract before implementation:

| Field | Requirement |
| --- | --- |
| Claim | One mechanism-level claim |
| Prediction | Direction and comparison fixed before results |
| Baseline | Strongest minimal equal-compute alternative |
| Ablation | Remove only the claimed mechanism |
| Metrics | Mechanism metric plus task metric |
| Success | Fixed threshold, ordering, or confidence criterion |
| Failure | Meaning of negative, null, failed, or incomplete evidence |
| Scope | Exact dimensions, conditions, tasks, depths, and seed unit |

Define the inferential unit explicitly. If confidence intervals are across
independent seeds, preserve that seed count for confirmatory results. Tasks,
held-out examples, and repeated measurements are nested observations unless
the design says otherwise; do not count them as extra independent seeds.

Operationalize equal compute before running. Match the relevant examples or
tokens, optimizer updates, data order, initialization, precision, and schedule.
When exact equality is impossible, name the matched axis and quantify the gap.
Reject post-hoc thresholds, selective reporting, and requests to omit negative
or failed runs. Synthetic data is valid only when it is the stated theory
probe, never as a silent substitute for a requested dataset.

### 2. Choose The Smallest Artifact Boundary

Use an inline notebook only when the implementation is genuinely short and
will not be reused. Use a thin notebook plus external Python when the notebook
would contain repeated storage, progress, calibration, metrics, or plotting
logic. The external files are ordinary modules, not a new framework.

A useful minimal layout is:

```text
src/<package>/
  colab_runtime/       # only environment, progress, signatures, storage needed
  experiments/         # one module per experiment
  metrics.py           # shared metrics only when actually shared
  plotting.py          # shared plotting only when actually shared
configs/               # one small YAML/JSON profile per experiment
notebooks/             # thin launchers and result display
scripts/run_experiment.py
```

Do not create every directory by template. Add only the modules the experiment
uses. Keep the notebook responsible for settings, repository bootstrap,
Drive mounting, invoking the runner, displaying results, and downloading the
validated result bundle. Keep scientific computation, checkpointing, and
aggregation in importable Python. The local CLI and Colab notebook must call
the same importable runner/API with the same config schema; only checkout,
device discovery, storage root, and presentation may differ.

### 3. Build A Thin, Dual-Environment Notebook

Keep notebook cells short and deterministic. A practical order is:

1. Contract, scope, limitations, and claim status.
2. Settings: `RUN_TIER`, `COLAB_PROFILE`, `EXECUTE_EXPERIMENT`,
   `FORCE_RECALIBRATION`, `EXPERIMENT_VERSION`, and repository ref.
3. Local/Colab checkout and dependency detection.
4. Device, CUDA, total/free VRAM, dtype, and environment snapshot.
5. Local output root or Drive mount plus an atomic write/reload probe.
6. Plan counts, progress reporter, run, and resume.
7. Validated summaries, figures, verdict, and result-bundle download.

The default settings may be `RUN_TIER="smoke"` so the notebook is safe to
open. Make the full run an explicit setting change; never silently execute a
large CUDA job on a CPU fallback. A local checkout must be reused locally; a
Colab checkout may clone the private repository at an explicit branch/ref.
Never put credentials in a repository URL. Read a private-repository token
from Colab Secrets and clear it from process state after cloning.

Return a direct Colab URL for every notebook, for example:

```text
https://colab.research.google.com/github/<owner>/<repo>/blob/<branch>/notebooks/<name>.ipynb
```

### 4. Define Tiers Without Changing The Science

All tiers MUST call the same data semantics, model, method, baseline, ablation,
metrics, checkpoint format, and aggregation code. Change only an explicitly
registered scale profile. A changed result-affecting profile is a new signed
experiment version and cannot be pooled with the old one.

| Tier | Required behavior |
| --- | --- |
| `smoke` | CPU-safe or tiny CUDA run, one proxy cell, a few tasks, checkpoint/reload and resume check; diagnostic only |
| `local` | Smaller diagnostic profile on the available CUDA device; measure memory and throughput; never claim confirmation evidence |
| `colab` | Confirmation profile on the selected CUDA GPU with Drive persistence, all registered inferential units, and complete result export |

Treat a requested duration such as "about two A100 hours" as a planning
target, never as a runtime contract. Calibrate a representative profile,
compare its projection with the user-approved target before formal launch,
record the estimate and actual time, and let the complete run finish or resume.
If the projection is materially outside the agreed target, revise and re-sign
the profile before launch; never adapt it based on elapsed formal-run time.
Do not add `GPU_HOUR_LIMIT`, `gpu_hour_limit`, `limit_gpu_hours`,
`rejected_time`, `actual_budget_overrun`, a wall-clock kill switch, or a
partial-seed timeout branch. Do not add a soft guard or an elapsed-time
conditional under another name such as `deadline`, `max_seconds`, a timer
callback, or a scheduler signal. An observational ETA/progress display is
allowed, but it must not stop, truncate, skip, or alter the denominator. OOM,
nonfinite values, corrupt state, and unmet hardware/storage prerequisites are
correctness failures and may stop an affected attempt; they are not time gates.

### 5. Scale Compute While Preserving Inference

When a confirmation profile is too large, use this order:

1. Enumerate every compute axis and the inferential unit.
2. Preserve the independent seed count and condition axes required by the
   claim. If the contract says 12 seeds, encode the exact 12-seed list and test
   it. Do not halve confirmatory seeds just because they are easy to remove.
3. Reduce redundant dimensions, task count, held-out examples, depth, or
   exploratory condition levels according to the claim and a declared compute
   proxy. Keep the minimum contrast needed to distinguish the mechanism.
4. Compute current/candidate ratios before coding. For matrix experiments,
   include terms such as fit cost proportional to `D^2 * M` or `D^3`, plus
   inference cost proportional to tasks, held-out examples, context, depth,
   modes, and chunks. State the resulting counts (blocks, trajectories,
   rows, endpoints) in config tests.
5. Update the claim scope, `EXPERIMENT_VERSION`, protocol hash, and Drive
   namespace. Never let old checkpoints resume into a changed grid.
6. Calibrate on the actual target GPU and report `estimated_gpu_hours`,
   `safety_adjusted_gpu_hours`, and `actual_gpu_hours` as descriptive metadata.

If fewer seeds are scientifically acceptable only for exploration, label that
profile exploratory and exclude it from paper-level confidence intervals. Do
not silently pool a reduced profile with a full profile. Removing a
claim-critical condition axis creates a newly scoped claim or an exploratory
profile, never the originally registered confirmation.

### 6. Calibrate Memory And Throughput

Before formal execution, record GPU name, total/free VRAM, compute capability,
dtype, and framework versions. Probe the largest registered fit shape and the
largest reused/fresh inference shapes. Record `peak_vram_gib` or
`peak_memory_bytes` for each probe and the calibration duration.

The main profile should rely on the measured probe rather than an arbitrary
hard-coded VRAM number. An explicitly separate high-memory extension may have
its own prerequisite (for example, a larger-dimension profile requiring a
large-VRAM GPU), but it must not silently change the main profile.

On OOM, discard uncommitted work, record a failed signed attempt, clear the
CUDA cache, and retry with a smaller task chunk when the protocol allows it.
Give each changed attempt a new `run_id`; never mix chunks produced with
different result-affecting settings. Allow at most three attempts for one
unit. Stop a profile that cannot fit its solve or has an unmet hardware
prerequisite. Do not silently shrink the scientific grid or fall back to CPU.

### 7. Sign, Store, And Resume Exactly

Build a canonical scientific execution signature from:

- experiment name and version;
- full effective config, including dimensions, tasks, held-out examples,
  conditions, depth, chunking, dtype, and analysis settings;
- source-file hashes for every imported experiment/runtime/metric module;
- data or task-generator version and split/index hashes;
- the exact seed panel and inferential unit;
- result-affecting numerical settings such as dtype and deterministic flags.

Keep volatile observations such as free VRAM, wall time, and device load out of
the scientific identity. Record them in the environment snapshot. Define a
separate resume-compatibility contract for hardware/runtime fields: include a
field only when changing it can alter the numerical trajectory. A compatible
Colab reconnect may resume; an incompatible dtype, determinism, or required
compute-capability change starts a new signed attempt. Never use the git SHA or
GPU name alone as the scientific signature.

Use a versioned Drive root such as:
`/content/drive/MyDrive/ml-experiments/<experiment>/<version>/`. Keep the
execution signature below that root. A result-affecting change creates a new
version or namespace; exact matching signatures alone may resume.

Write checkpoints, manifests, and result tables to a temporary sibling, close
them, atomically replace the destination, write a SHA-256 sidecar, and reload-
validate. Retain at least one previous valid generation and recover newest to
oldest. A checkpoint must include all applicable mutable algorithm state
(model, optimizer, scheduler, and scaler only when present), progress and raw-
log cursors, exact batch-plan identity, config/source/environment signatures,
and Python/NumPy/CPU/CUDA RNG states. Checkpoint only at a committed update
boundary. Default to `num_workers=0` for exact replay; workers require an
immutable batch-index plan, a separately committed consumed index, and
stateless transforms. Never treat a partial or corrupt artifact as a completed
seed.

### 8. Show Progress And Export A Validated Bundle

Show progress at run, phase, and chunk level. Include completed/total counts,
elapsed time, ETA, mode, and peak VRAM when available. Persist the same events
to the output root so a disconnected notebook can be audited.

After complete result validation, create one deterministic ZIP containing the
completion manifest, checksums, effective config, raw/summary tables, verdict,
and figures. Exclude tokens, credentials, checkpoints, and unnecessary large
intermediate arrays. The final notebook cell must automatically download the
validated ZIP in Colab and print its absolute path locally:

```python
from pathlib import Path

bundle_value = result.get("bundle_path")
if result.get("execution") == "complete" and bundle_value:
    bundle = Path(bundle_value)
    if not validate_result_bundle(bundle):
        raise RuntimeError(f"invalid result bundle: {bundle}")
    if IN_COLAB:
        from google.colab import files
        files.download(str(bundle))
    else:
        print(f"Result bundle: {bundle.resolve()}")
```

Never download an incomplete or checksum-invalid bundle. Drive remains the
authoritative copy when browser download is blocked or interrupted.
`validate_result_bundle` must verify the completion manifest, required member
set, every member checksum, matching experiment version and execution
signature, exactly one completed result for every expected seed-condition
unit, and the absence of credentials and checkpoints. Reopening the ZIP alone
is not sufficient validation.

### 9. Produce A Grounded Verdict

Save raw per-run metrics plus compact CSV/JSON summaries. Use paired deltas,
seed-level uncertainty, and familywise correction appropriate to the design.
Declare the minimum seed count, scope, and criterion before execution. Smoke
and local results are diagnostic/provisional unless they satisfy the unchanged
confirmation contract. At confirmation scale classify the claim as
`supported`, `partially supported`, or `not supported`, and preserve negative,
failed, incomplete, and right-censored records.

Never imply success from an unexecuted notebook. State which tier actually ran,
which scope it covers, and where the validated bundle was saved/downloaded.

## Verification Checklist

Write structural tests before implementation for the highest-risk contracts:

- profile values and registered counts are exact;
- changed profiles have a new version/storage namespace;
- execution and protocol signatures include all result-affecting inputs;
- forbidden time-admission fields are absent, and injecting very large
  estimated/actual hours cannot change admission, truncate work, or skip units;
- smoke runs through the same CLI and completes with visible progress;
- notebook settings, private bootstrap, local/Colab branches, Drive path,
  seven-cell-or-similar thin structure, and automatic bundle download are
  present;
- an interrupted run resumes to the same terminal result as an uninterrupted
  run: exact equality under deterministic execution, or a predeclared numeric
  tolerance plus identical completeness/signatures otherwise;
- aggregation rejects missing, duplicate, or mismatched inferential units;
- ZIP validation rejects missing members, bad checksums, signature/version
  mismatches, missing/duplicate seed-condition units, credentials, and
  checkpoints;
- `compileall`, focused tests, full tests, and local/notebook smoke dispatchers
  pass.

Run the smoke tier unless a concrete dependency, credential, hardware, or
authorization blocker prevents it. Test private bootstrap, Drive persistence,
and browser download in live Colab when access exists; otherwise run structural
tests and state those paths were not executed. A passing structural test is not
a scientific result; a passing smoke run is not confirmation evidence.

## Compact Example

For a prompt-reuse theory claim, keep a thin launcher notebook and put the
registered plan, fit/evaluate code, metrics, progress, storage, and plotting
in small external modules. Retain all independent seeds, reduce task and
held-out counts only after computing the workload ratio, bump the version and
Drive namespace, calibrate the largest shape, run the complete profile, and
download the validated result ZIP from the final Colab cell.

## Common Failures

| Failure | Correction |
| --- | --- |
| One giant notebook because "minimal" means one file | Use a thin launcher and only the external modules that remove real duplication |
| Hard two-hour timeout or partial-seed stop | Treat duration as a measured planning target; finish/resume complete units |
| Halving confirmatory seeds first | Preserve the independent inferential unit; reduce redundant workload axes first |
| Old checkpoints reused after scale changes | Bump version and namespace; require exact signatures |
| Notebook only works in Colab or only locally | Use one runner with explicit local/Colab checkout and device branches |
| No visible progress or downloadable artifact | Emit run/phase/chunk progress and auto-download only a validated ZIP |
| CPU fallback after CUDA failure | Report the prerequisite failure and stop that tier |
| Adding a framework, service, or dashboard | Keep the smallest ordinary modules that make the experiment runnable |
| Claiming support from smoke or an unexecuted cell | Tie the verdict to the predeclared confirmation contract |
