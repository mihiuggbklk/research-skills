---
name: publish-research-to-github
description: Use when publishing a research paper, experiment code, or experiment results from a local Git repository to GitHub.
---

# Publish Research To GitHub

Publish only the paper, experiment code, and experiment results from the currently checked-out branch.

## Rules

- Work in the current repository and current branch.
- Never create or switch branches, locally or remotely.
- Never use a Git worktree or clone.
- Never stage with `git add .` or `git add -A`.
- Never force-push or rewrite history.
- Never publish checkpoints, model weights, credentials, or private keys.

## Include

- Paper files: sources, bibliography/style files, final PDF, and figures used by the paper.
- Experiment files: source code, scripts, configs, dependency files, and clean notebooks.
- Result files: metrics, tables, summaries, and plots, including files under `result(s)/`, `output(s)/`, or `artifact(s)/`.

Do not add unrelated documentation, planning files, caches, datasets, logs, or build intermediates.

## Exclude Checkpoints

Exclude every path inside a directory named `checkpoint`, `checkpoints`, `weight`, or `weights`. Also exclude model files such as `*.ckpt`, `*.pt`, `*.pth`, and `*.safetensors`, even when stored elsewhere.

## Workflow

1. Inspect the current state without changing it:

   ```text
   git status --short --branch
   git branch --show-current
   git remote
   git rev-parse --abbrev-ref --symbolic-full-name '@{u}'
   git diff --cached --name-only
   ```

   Stop if HEAD is detached, the current branch has no existing upstream, or the index already contains unrelated staged changes.

2. Build an explicit list containing only the included files. Review it for checkpoint paths and secrets.

3. Stage only that list:

   ```text
   git add -- <paper-files> <experiment-code-files> <result-files>
   git diff --cached --name-status
   ```

   If an approved result file is ignored, stage only that exact file with `git add -f -- <result-file>`. Never force-add a directory.

   If the staged list contains any excluded or unrelated file, unstage that exact path with `git restore --staged -- <path>`.

4. Commit with a short message that describes the publication:

   ```text
   git commit -m "<message>"
   ```

5. Push the current branch and verify Git reports success:

   ```text
   git push
   git status --short --branch
   git rev-parse --short HEAD
   ```

Report the branch name and commit ID. Do not claim that an untracked, ignored, or unstaged file was uploaded.

## Common Mistakes

- A result directory is allowed; a checkpoint directory is not.
- A plot or metrics file is a result; a model-weight file is a checkpoint.
- `.gitignore` does not remove an already staged file. Inspect the staged file list before committing.
- Existing unrelated files in remote history are not removed by this workflow.
