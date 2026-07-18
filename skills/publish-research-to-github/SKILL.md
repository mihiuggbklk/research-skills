---
name: publish-research-to-github
description: Use when publishing a research repository to GitHub that contains papers, LaTeX/PDF assets, figures, experiment code, generated result directories, checkpoints, notebooks, or dirty Git history and needs a safe allowlist, FILES.md, and an audited commit/push.
---

# Publish Research To GitHub

Publish a reviewed source-and-paper snapshot, not a copy of the working directory. By default, retain reproducible code, tests, configs, build files, output-free notebooks, paper sources/PDFs, and referenced figures; exclude generated result/evidence trees.

## Core Rules

- The user's latest instruction controls whether data is public. Never relocate an excluded result directory to evade the policy.
- Use `scripts/repo_publish.py` for discovery, secret scanning, `FILES.md`, exact staging, commit, push, and remote-hash verification.
- Leave a dirty or diverged source worktree untouched. Build the publication in an isolated worktree or clone.
- Never create/change a remote, fetch, merge, rebase, force-push, or rewrite history under this skill.
- Never claim success without the returned local commit, matching remote commit, and tree hash.

## Workflow

1. **Lock scope and target.** Record the target branch and the newest user decision for:
   - `paper/results/` and `paper/evidence/`;
   - `artifacts/`, `outputs/`, checkpoints, and run state;
   - final PDFs and TeX-referenced figures.

   The bundled policy defaults all generated result/evidence/output trees to excluded. If the user later changes scope, discard the old publication plan and rerun every gate.

2. **Inspect without exposing credentials.**

   ```text
   git status --short --branch
   git branch --show-current
   git remote
   git ls-remote --heads origin refs/heads/<branch>
   git ls-files --stage
   ```

   Do not print remote URLs. Do not trust a stale `refs/remotes/origin/*`. Require a named branch, configured remote, clean index, no conflicts, and no active merge/rebase/cherry-pick. Reject sparse checkout, every `skip-worktree` entry, and every `assume-unchanged` entry: an absent tracked path is not proof that the path will be deleted from the published tree.

   Any mode `160000` entry is a hard block for this source snapshot. The script reports missing or mismatched `.gitmodules` mappings explicitly, but even a valid mapping must be removed or replaced with reviewed vendored source in the isolated publication worktree through a normal commit. Outbound commits are also scanned for gitlinks that were added and later removed.

3. **Run non-destructive preparation.**

   ```text
   python <skill-root>/scripts/repo_publish.py prepare --repo . --remote origin
   ```

   Stop on any blocked path. Review `included`, `excluded`, `remove_from_git`, and `changes`. Adding a `.gitignore` rule does not remove an already tracked file; the `remove_from_git` list must show that deletion.

4. **Review the public interface.**
   - Read the paper, code, tests, configs, and build files before updating `README.md`.
   - Preserve useful human-authored README sections and link to `FILES.md`.
   - If a root `Makefile` exists, it is a required deliverable. Verify:

     ```text
     git ls-files --error-unmatch Makefile
     git check-ignore -v --no-index Makefile
     ```

     The second command must produce no matching ignore rule. `prepare` blocks an ignored root `Makefile` and a tracked `Makefile` missing from the working tree. Ensure `Makefile` appears in `FILES.md` and the final committed tree.
   - If Makefile targets require excluded result/evidence directories, mark those targets as optional or document their external prerequisite. Do not claim a fresh source-only checkout can run them.

5. **Sanitize publishable notebooks structurally.** Every included `.ipynb` must be a JSON object with `nbformat >= 4`, a non-negative integer `nbformat_minor`, and a valid cells list. Every cell must have a supported `cell_type`, object-valued `metadata`, and string or string-list `source`; code cells additionally require:
   - `outputs: []` for every code cell;
   - `execution_count: null`;
   - no saved widget state;
   - no machine-specific paths such as `C:\\Users\\...`, `D:\\...`, `/home/<user>/`, or `/Users/<user>/` embedded in cells/metadata. Portable runtime paths such as `/content/drive/...` are allowed when they are part of the documented notebook protocol;
   - no credentials embedded in cells/metadata.

   Use a notebook/JSON parser, not line-oriented replacement. Missing fields and wrong empty types such as `outputs: {}` are blocks, not equivalents of `outputs: []`. Source arrays are joined before checking machine paths, so splitting a path across fragments does not bypass the gate. The bundled script applies the same structural/state checks to every notebook blob in outbound commits; sanitizing only the latest copy is insufficient. Rerun `prepare` after sanitizing.

6. **Verify the candidate.** Run the repository's locked tests and supported paper/source checks. On Windows, verify hash-sensitive official files from Git blobs or an archive, not a CRLF-converted working copy:

   ```text
   git hash-object --path=paper/aaai2027.sty paper/aaai2027.sty
   git rev-parse HEAD:paper/aaai2027.sty
   ```

   Honor committed `.gitattributes` `eol=lf` rules and avoid PowerShell text round-trips for official style files.

7. **Create the exact commit message.** Write UTF-8 without BOM, with LF-only line endings and exactly one terminal LF, to a temporary file outside the repository. `publish` reads the raw bytes and rejects an invalid encoding, BOM, CRLF, missing terminal LF, or an extra blank terminal line:

   ```text
   <imperative subject, at most 72 characters>

   Files:
   - Added: <comma-separated paths, or None>
   - Modified: <comma-separated paths, or None>
   - Deleted: <comma-separated paths, or None>

   Changes:
   - <concrete implementation or documentation change>

   Features:
   - <functionality change, or No functional change>
   ```

   Use commas, not semicolons. The three file lists must exactly equal the final diff.

8. **Publish.**

   ```text
   python <skill-root>/scripts/repo_publish.py publish --repo . --remote origin --message-file <temp-file>
   ```

   The script scans the staged Git tree after clean filters run, then scans the committed tree and raw committed message after hooks run but before pushing. It blocks if either tree contains excluded paths, secrets, unsafe notebooks, oversized blobs, external symlinks, or gitlinks; it also requires the committed tree and message to exactly match the approved staged tree and message.

   Require `remote_commit == commit`. Record `tree`, branch, changes, and exclusions. Delete the temporary message only after success.

9. **Audit the pushed tree.**

   ```text
   git ls-remote --heads origin refs/heads/<branch>
   git rev-parse HEAD^{tree}
   git ls-tree -r --name-only HEAD
   git ls-tree -r HEAD
   ```

   Verify:
   - the live remote OID equals the returned commit;
   - no path matches `(^|/)(results?|evidence|outputs?|artifacts|checkpoints?|run_states?)(/|$)`;
   - no blocked checkpoint/weight extension or mode `160000` is present;
   - `Makefile`, expected paper files, and only intended figures are present;
   - all tracked notebooks remain output-free.

## File Policy

### Publish

- Root repository metadata and build inputs, including `.gitignore`, `.gitattributes`, `README.md`, `FILES.md`, `Makefile`, lockfiles, environment specs, licenses, and citation metadata.
- Paper `.tex`, bibliography/style files, final document PDFs, and figures actually referenced by the paper.
- Experiment/library source, tests, scripts, configs, and output-free notebooks.
- Small structured assets outside generated result/data directories.

### Exclude

- Entire `paper/results/**`, `paper/evidence/**`, `artifacts/**`, `outputs/**`, `logs/**`, and `run_states/**` trees.
- LaTeX intermediates, caches, virtual environments, build/package directories, editor/agent state, run state, and generated logs.
- AI planning/process Markdown such as `TODO.md`, `*_PLAN.md`, `DESIGN.md`, and `docs/superpowers/**`.
- Unsupported untracked files and placeholders such as unnecessary `.gitkeep` files.

Tracked excluded files are removed from Git's index while their local copies remain.

### Block And Stop

- Credentials, private keys, token files, or high-confidence secret content.
- Raw datasets, model weights, checkpoints, databases, or files over 50 MiB by default. A `checkpoint(s)/` or `weight(s)/` directory blocks publication even when its contents use ordinary extensions such as `.json` or `.yaml`.
- Symlinks resolving outside the repository.
- Invalid gitlinks, dirty/uninitialized submodules, conflicts, detached HEAD, pre-staged changes, or active Git operations.

Do not silently override a block or print a secret value.

## Script Reference

| Command | Effect |
| --- | --- |
| `prepare` | Validate state/history and Makefile, classify files, scan current and outbound secrets, gitlinks, and notebook state, regenerate `FILES.md`, and emit JSON without staging. |
| `publish` | Repeat gates, validate README/message, stage exact paths, scan staged blobs, commit, verify hook-stable tree/message, push, query the live remote, and return `commit`, `remote_commit`, and `tree`. |

Use `--max-size-mib N` only after the owner explicitly changes the limit. A push failure leaves the local commit intact and never retries destructively.

## Common Mistakes

- Never use `git add .`, `git add -A`, or a blanket pathspec.
- Do not treat a file's presence on disk as proof it was uploaded; inspect `FILES.md` and `git ls-tree`.
- Do not put excluded paths in `FILES.md` as an appendix.
- Do not invent compile/experiment commands or a license.
- Do not put the commit-message file inside the repository.
- Do not assume clean filters or Git hooks preserve reviewed content; staged and committed Git objects are the publication boundary.
- Do not assume a tip deletion purges old blobs. Remote-history purge requires separate explicit authorization and is outside this skill.
- Do not report success before remote OID and tree verification.
