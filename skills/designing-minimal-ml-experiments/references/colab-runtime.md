# Colab Runtime Adaptation

Read this when preparing or repairing a Colab environment, especially for
Qwen + LoRA + natural-gradient experiments on RTX PRO 6000 Blackwell.

## Observed Session, 2026-11-08

The user supplied the following session metadata. These are observed values,
not instructions to install these versions on every future Colab session.

| Component | Observed version/value |
| --- | --- |
| GPU | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| Compute capability | 12.0 (`sm_120`) |
| Python | 3.13.16 |
| OS | Linux 6.6.159+, x86_64, glibc 2.39 |
| PyTorch | 2.14.1+cu130 |
| PyTorch CUDA runtime | 13.0 |
| Transformers | 5.22.1 |
| PEFT | 0.21.2 |
| Accelerate | 1.15.0 |
| NumPy / SciPy | 2.4.6 / 1.16.3 |
| Matplotlib | 3.10.0 |
| Safetensors | 0.8.0 |
| Hugging Face Hub / Tokenizers | 1.33.0 / 0.23.3 |
| psutil / SymPy | 5.9.5 / 1.14.0 |
| math-verify | Missing |
| latex2sympy2-extended | Missing |
| antlr4-python3-runtime | Missing |

The library versions matched the [official GPU package snapshot at
066189cf](https://github.com/googlecolab/backend-info/blob/066189cf295672c892e931270c4b37bc2af5688f/pip-freeze.gpu.txt).
Colab images change; inspect the actual session again for a new deployment.
The supplied metadata did not include driver version or VRAM capacity. Read
those values when needed; do not infer them from CUDA version or GPU name.

## Minimal Setup For This Session

Reuse the current interpreter and native model libraries. For this experiment's
existing grader contract, only the missing packages needed installation:

```python
import subprocess
import sys

subprocess.run([
    sys.executable, "-m", "pip", "install", "--no-deps",
    "math-verify==0.9.0",
    "latex2sympy2-extended==1.11.0",
    "antlr4-python3-runtime==4.13.2",
], check=True)
```

This is an installation example, not a replacement launcher: first inspect
installed versions, omit packages already present at the required version,
and surface conflicting versions. SymPy 1.14.0 in this session already
satisfied the grader dependency. Inspect transitive requirements again if
changing this set; never apply `--no-deps` blindly to arbitrary packages.

Use fresh child processes for import checks after installation. Do not install
uv, replace Python/PyTorch/CUDA, or downgrade Transformers merely because an
older launcher pinned them. A GitHub 504 while downloading Python 3.11.11 was
a download failure, not evidence against the preinstalled Python 3.13 stack.
Stream setup output to the notebook and a redacted persistent log, so the next
failure includes the failed stage and underlying error rather than only a
`CalledProcessError`.

## Compatibility Lessons From This Stack

- Keep `dtype=...` when loading models; preserve the registered precision.
- Transformers 5.22.1 removed `use_model_defaults`. Check the installed API
  before passing it. Simply removing the argument is insufficient: unset
  generation options can inherit filters from `model.generation_config`.
- Use an explicit generation config. Fold generation options into that config
  instead of mixing them with duplicate generation kwargs. Preserve EOS/pad
  IDs, token budgets, temperature, full-vocabulary sampling and per-row RNG.
  When temporarily neutralizing defaults, handle both PEFT and the underlying
  model; PEFT can copy its config back to the base. Restore original config
  values and attribute ownership in `finally`, including CUDA OOM paths.
- New checkpointing input hooks may execute `requires_grad_` inside
  `torch.func.jvp`. In the tested Qwen LoRA setup, embeddings were frozen and
  excluded from adapter targets: computing detached embeddings outside JVP and
  passing `inputs_embeds` preserved the LoRA derivative. This workaround is
  invalid if the differentiated parameters include embeddings or their
  adapters; check the derivative boundary before applying it elsewhere.

## Verification Scope

When authorized, check real tiny-model generation, unequal-length padded
batches, independent seeds, model loading, adapter updates and the affected
Fisher/JVP path. Compare Fisher products against an independent Hessian oracle
when modifying that derivative path. Include inherited generation filters and
exception restoration in generation compatibility checks.

CPU tests using PyTorch 2.14.1+cpu, Transformers 5.22.1 and PEFT 0.21.2 passed
on Windows / Python 3.11.11 in this case. They did not validate Python 3.13,
CUDA 13.0, RTX PRO 6000 memory use or complete 3B training. A lightweight CUDA
forward/backward/JVP probe on the target can establish basic execution, not
full-workload throughput or memory safety. Respect the user's requested
verification scope; updating this skill does not authorize an experiment run.
