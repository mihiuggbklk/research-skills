# Research Skills

This repository contains three Codex skills for practical AI and ML research workflows:

- [`designing-minimal-ml-experiments`](skills/designing-minimal-ml-experiments/SKILL.md) turns a theory claim into a minimal, runnable PyTorch experiment with comparable smoke, local, and Colab tiers, exact resume requirements, and an evidence-grounded verdict.
- [`writing-ai-ml-papers`](skills/writing-ai-ml-papers/SKILL.md) supports English AI/ML manuscript planning, drafting, revision, evidence grounding, author voice, and prose auditing. Its audit command is `python skills/writing-ai-ml-papers/scripts/audit_paper.py PAPER.tex --strict`.
- [`publish-research-to-github`](skills/publish-research-to-github/SKILL.md) provides a guarded workflow for discovering publishable research files, scanning for secrets and oversized artifacts, generating `FILES.md`, and committing and pushing an exact file set. Its preparation command is `python skills/publish-research-to-github/scripts/repo_publish.py prepare --repo . --remote origin`.

## Layout

Each skill is self-contained under `skills/` and includes its instructions, supporting references or scripts, and tests where applicable. The generated [`FILES.md`](FILES.md) is the authoritative inventory of files included in this repository.

## Scope

These skills provide workflow guidance and small standard-library Python utilities. They do not include datasets, model weights, experiment outputs, credentials, or other generated runtime artifacts.
