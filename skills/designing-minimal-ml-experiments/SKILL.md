---
name: designing-minimal-ml-experiments
description: Use when turning an AI or machine-learning theory claim into a minimal runnable PyTorch experiment, especially when the user wants one Jupyter notebook, smoke testing, an RTX 4060 run, Colab on A100 or RTX 6000 PRO, Google Drive checkpoints, or resume after disconnects.
---

# Designing Minimal ML Experiments

## Core Principle

Test one falsifiable claim with the smallest experiment that can distinguish the proposed mechanism from an equal-compute baseline. Optimize for runnable evidence, not project architecture.

Produce one complete task-specific `.ipynb` by default. Do not stop at an outline, plan, or proposed filename. Do not create auxiliary `.py` files, packages, CI, or dashboards unless one notebook is technically impossible and the user approves the exception. The notebook may import an existing repository when reuse is the shortest correct route.

## Workflow

### 1. Freeze The Research Contract

Before writing experiment code, state in the notebook:

| Field | Requirement |
| --- | --- |
| Claim | One mechanism-level claim |
| Prediction | Direction and comparison expected before results |
| Baseline | Strongest minimal equal-compute alternative |
| Ablation | Remove only the claimed mechanism |
| Metrics | Mechanism metric plus task metric |
| Success | Fixed threshold or ordering |
| Failure | Meaning of negative or ambiguous evidence |

Operationalize equal compute before running: match examples or tokens, optimizer updates, data order/augmentations, model initialization, and optimizer schedule. Report trainable parameters, examples/tokens, updates, wall time, peak VRAM, and measured or estimated FLOPs when method overhead differs. If exact equality is impossible, name the matched compute axis and quantify the remaining gap.

Reject post-hoc thresholds, selective reporting, and requests to omit negative runs. Use synthetic data only when it is explicitly the theory probe; never silently substitute it for a requested dataset.

### 2. Build One Self-Contained Notebook

Use this cell order:

1. Research contract and limitations.
2. One config cell with `RUN_TIER = "smoke" | "local" | "colab"` and an explicit `EXPERIMENT_VERSION`.
3. Environment detection: Colab, Python, PyTorch, CUDA, GPU, total/free VRAM, and BF16.
4. Minimal dependency bootstrap. Never reinstall local PyTorch or unconditionally upgrade packages; fail clearly when a required dependency cannot be provided.
5. Local output directory or Colab Google Drive mount. Before a Colab confirmation run, require a successful checkpoint write-reload probe; do not run large jobs without durable storage.
6. Seeds, deterministic settings where practical, and environment logging.
7. Data and fixed split/subset rules.
8. Baseline, proposed method, and mechanism-removing ablation.
9. Shared train, evaluate, checkpoint, and resume functions.
10. Tier profiles and local throughput calibration.
11. Run loop, aggregation, plots, and evidence verdict.

Fill every implementation cell. Deliver no `TODO`, `pass`, fake metric, missing function, or cell requiring manual code completion.

### 3. Keep Tiers Scientifically Comparable

All tiers MUST call the same data semantics, model architecture, method implementation, baseline, ablation, and metrics. Change only samples, steps, micro-batch/accumulation, precision, and seeds. If model scale must change, create a separately signed proxy experiment and never pool or directly compare it with the full-scale confirmation.

| Tier | Required behavior |
| --- | --- |
| `smoke` | Target 1-5 minutes; one seed, tiny subset, and a few steps. Verify data, forward/backward, metric, checkpoint, and resume. Label results diagnostic, never final evidence. |
| `local` | Target an 8 GB RTX 4060. Inspect free VRAM without killing processes. Prefer BF16 when supported. Warm up past one-time compilation, then measure data plus train steps, a full evaluation, and one checkpoint. Estimate setup plus all variants/seeds/steps/evaluations/checkpoints, multiply by a 1.25 safety factor, and reduce samples, steps, then seeds equally across variants until the estimate is at most 110 minutes. Once started, warn and log if runtime exceeds two hours; NEVER terminate because of elapsed time. |
| `colab` | Detect A100, RTX 6000 PRO, or other CUDA GPU and scale batch/data/seeds to memory. Mount Drive and assume disconnects. Use the full practical confirmation setting. |

Resolve OOM during the preflight probe when possible. If a formal run OOMs, discard partial gradients, mark that signed attempt failed, clear cached memory, halve the micro-batch, and raise accumulation when possible. Because the result-affecting config changed, create a new `run_id` and restart that seed from its initial state; never continue a mixed trajectory. Declare at most three OOM attempts. On NaN/Inf, preserve the last valid state and diagnostics, then mark the run failed.

If a dependency, Drive mount, storage probe, or dataset download fails, report the exact failure and stop the affected run. Never silently switch datasets or turn a persistent Colab confirmation into an ephemeral run.

### 4. Implement Exact Resume

In Colab, default to `/content/drive/MyDrive/ml-experiments/<experiment-name>/`. Build a stable `run_id` from `EXPERIMENT_VERSION`, method variant, seed, exact dataset revision and split-index hash, preprocessing, and every result-affecting setting, including precision, micro-batch, and accumulation. Record the notebook or git revision when available and dependency versions. Never resume across a result-affecting signature change.

Each checkpoint MUST contain:

- model, optimizer, scheduler, and AMP scaler state;
- epoch, global step, best/latest evaluation, every online metric accumulator or raw-log cursor used in final evidence, exact deterministic batch-plan identity, committed consumed-batch cursor, and DataLoader generator state;
- Python, NumPy, CPU PyTorch, and all CUDA RNG states;
- normalized config, data/code/environment signatures, and `run_id`.

Checkpoint only immediately after an optimizer update and `zero_grad`, never mid-accumulation. The committed cursor MUST count batches actually consumed through that boundary, never batches merely yielded or prefetched. Default to `num_workers=0` for exact resume; with workers, use an immutable batch-index plan plus a separately committed consumed-batch index, and make transforms stateless from seed/epoch/sample index. Write versioned checkpoints to a temporary sibling, close it, commit with `os.replace`, write a SHA-256 sidecar, and reload-validate schema, signature, and checksum. Keep at least one previous valid generation. Treat the completion manifest identically: version it, checksum it, reload-validate it, retain a prior generation, and update it only after checkpoint/final metrics are durable. On recovery, scan manifest and checkpoint generations newest to oldest; never skip from corrupt or unvalidated metadata, and fail explicitly if no valid matching state exists. Skip only completed runs whose stored signature exactly matches. Write compact checkpoints and metrics to Drive; do not stream large datasets or per-step logs there.

### 5. Produce A Grounded Verdict

Save raw per-run metrics plus CSV/JSON summaries. Report uncertainty appropriate to the paired design, such as per-seed deltas with mean and standard deviation or confidence interval. Predeclare the minimum dataset/step scale and paired seed count required for confirmation. Smoke is diagnostic and does not classify the claim. Local is provisional unless it meets that unchanged confirmation contract; a calibrated-down local run cannot claim `supported`. Colab is the default confirmation tier. At confirmation scale, classify the claim as `supported`, `partially supported`, or `not supported`, tied only to the predeclared criterion. Preserve negative and failed runs.

Run the smoke tier when execution is authorized and feasible. Otherwise state exactly what was not run and how to execute it; never imply success from unexecuted cells.

## Compact Example

For a gradient-alignment claim, compare equal-compute naive gradient summation against the proposed alignment rule, and ablate only the alignment operation. Measure conflicting-gradient rate and held-out accuracy. Predeclare that support requires both lower conflict and a positive paired accuracy delta across seeds; a positive smoke run alone is diagnostic.

## Common Failures

| Failure | Correction |
| --- | --- |
| Returning only a design or filename | Create the complete notebook artifact. |
| Changing the method across tiers | Change scale only. |
| Killing a local run at two hours | Calibrate before launch; warn after launch. |
| Saving model weights only | Save optimizer, scaler, progress, RNG, config, and manifest too. |
| Treating Smoke as paper evidence | Confirm at justified local/Colab scale. |
| Hiding negative evidence | Preserve it and weaken or reject the claim. |
