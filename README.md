# Research Skills

This repository contains three Codex skills for practical AI and ML research workflows:

- [`designing-minimal-ml-experiments`](skills/designing-minimal-ml-experiments/SKILL.md) turns a theory claim into a minimal, runnable PyTorch experiment with comparable smoke, local, and Colab tiers, exact resume requirements, and an evidence-grounded verdict.
- [`writing-ai-ml-papers`](skills/writing-ai-ml-papers/SKILL.md) supports English AI/ML manuscript planning, theorem and appendix proofs, selective experiment reporting, evidence grounding, author voice, and prose auditing. Its audit command is `python skills/writing-ai-ml-papers/scripts/audit_paper.py PAPER.tex --strict`.
- [`publish-research-to-github`](skills/publish-research-to-github/SKILL.md) publishes paper files, experiment code and configuration, and experiment results from the current branch while excluding checkpoints and avoiding new branches, worktrees, and clones.

## Layout

Each skill is self-contained under `skills/` and includes its instructions, supporting references or scripts, and tests where applicable. [`FILES.md`](FILES.md) lists the files included in this repository.

## Scope

These skills provide workflow guidance and small standard-library Python utilities. They do not include datasets, model weights, experiment outputs, credentials, or other generated runtime artifacts.
