---
name: publish-research-to-github
description: Use when publishing a research repository to GitHub that contains papers, LaTeX sources, PDFs, figures, compilation assets, or experiment code and requires README.md, FILES.md, and a detailed commit record.
---

# Publish Research To GitHub

Use this skill when the user asks to upload or publish a paper project, LaTeX article, compiled PDF, paper figures, build inputs, or experiment code to GitHub. The default behavior is automatic commit and push after every safety gate passes.

## Core Rule

Separate semantic judgment from deterministic repository operations:

- Read the paper and code to update `README.md` accurately and explain functionality changes.
- Use `scripts/repo_publish.py` for file discovery, exclusion, secret scanning, `FILES.md`, exact staging, commit, and push.
- Never claim success without the commit hash and push result returned by the script.

## Workflow

Run every step in order from the target repository root.

1. Inspect the repository with `git status --short`, `git branch --show-current`, `git remote`, and the relevant paper/code diffs. Do not print remote URLs because they may contain credentials. Require a named branch, configured remote, clean index, no conflicts, and no merge/rebase operation. Do not create a GitHub repository, change remotes, fetch, rebase, merge, or force-push.
2. Run the non-destructive preparation phase:

   ```text
   python <skill-root>/scripts/repo_publish.py prepare --repo . --remote origin
   ```

   Use the bundled Python runtime when the system `python` command is unavailable. Read the JSON report and stop on any blocked path.

3. Review the actual paper source, PDF, figures, bibliography, build files, and experiment entry points. Update `README.md` when it is missing or stale. Preserve useful human-authored sections. Document only commands and prerequisites supported by repository evidence:

   - project or paper purpose;
   - source and PDF entry points;
   - verified LaTeX compilation command and prerequisites;
   - verified experiment setup and execution command;
   - repository layout and a link to `FILES.md`.

4. Rerun `prepare` after any README change. `FILES.md` is generated on every preparation and must contain only publishable files, including `README.md` and itself. It must not list excluded or blocked paths.
5. Derive the commit message from the final diff. Write it to a UTF-8 temporary file outside the repository. Use this exact structure:

   ```text
   <concise imperative subject>

   Files:
   - Added: <paths, or None>
   - Modified: <paths, or None>
   - Deleted: <paths, or None>

   Changes:
   - <concrete implementation or documentation change>

   Features:
   - <new or changed functionality, or No functional change>
   ```

   Reconcile every path with the staged diff; do not infer functionality from filenames alone.
6. Run the publishing phase. This reruns all checks, stages only the approved paths, commits, and pushes the current branch:

   ```text
   python <skill-root>/scripts/repo_publish.py publish --repo . --remote origin --message-file <temp-message-file>
   ```

7. Report the commit hash, remote name, branch, added/modified/deleted paths, and any excluded paths. Remove the temporary message file after the command succeeds.

## File Policy

### Publish

- Paper sources: `.tex`, `.ltx`, `.bib`, `.bbl`, `.bst`, `.sty`, `.cls`, and related LaTeX support files.
- Final `.pdf` documents.
- Referenced figures and assets: common raster/vector image formats, fonts, and small table assets.
- Experiment source code, notebooks, shell scripts, environment specifications, and configuration files.
- `README.md`, `FILES.md`, licenses, citation metadata, and reproducibility build files.

### Exclude

- LaTeX intermediates: `.aux`, `.log`, `.out`, `.toc`, `.fls`, `.fdb_latexmk`, `.synctex.gz`, `.blg`, and similar generated state.
- Caches, editor state, bytecode, build directories, package directories, run directories, and generated logs.
- AI planning/process Markdown such as `AI_PLAN.md`, `TODO.md`, `*_PLAN.md`, `TASKS.md`, `DESIGN.md`, brainstorming notes, and `docs/superpowers/**`. Keep `README.md` and `FILES.md` as explicit exceptions.
- Untracked files with unsupported types.

### Block and Stop

- `.env` and credential exports, private keys, token files, and high-confidence secret content.
- Raw datasets, model weights, checkpoints, database files, and files larger than 50 MiB by default.
- Symlinks that resolve outside the repository.
- Conflicts, detached HEAD, missing remote, pre-existing staged changes, dirty submodules, or an active merge/rebase.

Do not print secret values. Do not silently override a block. A tracked excluded temporary or planning file is removed from Git's index while its local copy is retained; a tracked blocked file stops the operation.

## Script Reference

The bundled script is intentionally standard-library-only and has two commands:

| Command | Effect |
| --- | --- |
| `prepare` | Validate repository state, discover non-ignored files, scan safety rules, regenerate `FILES.md`, and emit a JSON report. It never stages, commits, or pushes. |
| `publish` | Repeat preparation checks, validate `README.md` and the structured message, stage the exact approved set, commit, and push `HEAD` to the configured branch. |

Use `--max-size-mib N` only when the repository owner has explicitly chosen a different limit. A push failure leaves the local commit intact and never retries destructively.

## Common Mistakes

- Do not use `git add .`, `git add -A`, or a blanket pathspec. The script owns the staging set.
- Do not put excluded files in `FILES.md` as an informational appendix; the inventory is the publishable set only.
- Do not invent compile or experiment commands from convention. Say that a command is unavailable when repository evidence is missing.
- Do not put the commit message file inside the repository.
- Do not create a remote repository, alter authentication, or print credential-bearing remote URLs as part of this skill.
- Do not use `--force`, `reset --hard`, history rewriting, or automatic fetch/rebase.
- Do not report a successful upload before verifying the returned commit hash and push response.
