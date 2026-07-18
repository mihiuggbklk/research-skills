#!/usr/bin/env python3
"""Prepare and publish research repositories with an explicit file policy."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, NamedTuple, Sequence


DEFAULT_MAX_SIZE_BYTES = 50 * 1024 * 1024


class PublishError(RuntimeError):
    """Raised when the repository cannot pass a publication gate."""


class FileDecision(NamedTuple):
    path: str
    action: str
    reason: str
    category: str
    purpose: str
    tracked: bool


PAPER_SOURCE_EXTENSIONS = {".tex", ".ltx", ".dtx", ".ins"}
BIBLIOGRAPHY_EXTENSIONS = {".bib", ".bbl", ".bst"}
LATEX_SUPPORT_EXTENSIONS = {".sty", ".cls", ".clo", ".def"}
FIGURE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".eps",
    ".ps",
    ".tif",
    ".tiff",
    ".webp",
}
FONT_EXTENSIONS = {".ttf", ".otf", ".woff", ".woff2"}
CODE_EXTENSIONS = {
    ".py",
    ".r",
    ".m",
    ".jl",
    ".sh",
    ".ps1",
    ".bat",
    ".cmd",
    ".ipynb",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".cu",
    ".cuh",
    ".java",
    ".go",
    ".rs",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
}
CONFIG_EXTENSIONS = {".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf"}
DOCUMENT_EXTENSIONS = {".md", ".rst", ".txt"}
SMALL_DATA_EXTENSIONS = {".csv", ".tsv", ".json", ".dat"}
REPOSITORY_FILENAMES = {
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    ".env.example",
    "citation.cff",
    "dockerfile",
    "environment.yml",
    "environment.yaml",
    "files.md",
    "license",
    "license.md",
    "license.txt",
    "makefile",
    "manifest.in",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "poetry.lock",
    "pyproject.toml",
    "readme.md",
    "readme.rst",
    "requirements.txt",
    "setup.cfg",
    "setup.py",
    "uv.lock",
}

EXCLUDED_DIRECTORIES = {
    ".git",
    ".idea",
    ".ipynb_checkpoints",
    ".latex-build",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    ".vscode",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "runs",
    "tmp",
    "temp",
}
EXCLUDED_EXTENSIONS = {
    ".acn",
    ".acr",
    ".alg",
    ".aux",
    ".bak",
    ".blg",
    ".dvi",
    ".fdb_latexmk",
    ".fls",
    ".glg",
    ".glo",
    ".gls",
    ".idx",
    ".ilg",
    ".ind",
    ".lof",
    ".log",
    ".lot",
    ".nav",
    ".out",
    ".pyc",
    ".pyo",
    ".snm",
    ".swp",
    ".toc",
    ".vrb",
}
BLOCKED_ARTIFACT_EXTENSIONS = {
    ".arrow",
    ".ckpt",
    ".db",
    ".feather",
    ".h5",
    ".hdf5",
    ".joblib",
    ".npy",
    ".npz",
    ".onnx",
    ".parquet",
    ".pickle",
    ".pkl",
    ".pt",
    ".pth",
    ".safetensors",
    ".sqlite",
}
BLOCKED_CREDENTIAL_NAMES = {
    "credentials",
    "credentials.json",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "id_rsa",
    "service-account.json",
}
BLOCKED_CREDENTIAL_DIRECTORIES = {"credentials", "private", "secrets"}
RAW_DATA_DIRECTORIES = {"data", "dataset", "datasets"}
RESULT_DIRECTORIES = {"logs", "outputs", "results"}
SECRET_PATTERNS = (
    ("private key", re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\b(?:github_pat_|gh[pousr]_)[A-Za-z0-9_]{20,}\b")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    (
        "assigned secret",
        re.compile(
            r"(?im)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|"
            r"github[_-]?token|password|passwd|secret[_-]?key)\b\s*[:=]\s*[\"']?"
            r"(?!your[_-]|example|changeme|replace[_-]|dummy)[A-Za-z0-9_./+=-]{12,}"
        ),
    ),
)


def _normalise(relative: str) -> str:
    value = relative.replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    if not value or value == "." or "\x00" in value:
        raise PublishError("Invalid empty or NUL-containing repository path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise PublishError(f"Path escapes the repository: {relative}")
    return path.as_posix()


def _plan_markdown(path: PurePosixPath) -> bool:
    if path.suffix.lower() != ".md":
        return False
    if path.name.lower() in {"readme.md", "files.md"}:
        return False
    lower_parts = tuple(part.lower() for part in path.parts)
    if len(lower_parts) >= 2 and lower_parts[:2] == ("docs", "superpowers"):
        return True
    tokens = set(re.findall(r"[a-z0-9]+", path.stem.lower()))
    workflow_tokens = {"plan", "plans", "todo", "task", "tasks", "design", "brainstorm", "brainstorming"}
    return bool(tokens & workflow_tokens) or {"review", "notes"}.issubset(tokens)


def _category_for(path: PurePosixPath) -> tuple[str, str] | None:
    suffix = path.suffix.lower()
    name = path.name.lower()
    if suffix in PAPER_SOURCE_EXTENSIONS:
        return "paper-source", "LaTeX paper source"
    if suffix in BIBLIOGRAPHY_EXTENSIONS:
        return "bibliography", "Bibliography or bibliography build input"
    if suffix in LATEX_SUPPORT_EXTENSIONS:
        return "latex-support", "LaTeX class, style, or support file"
    if suffix == ".pdf":
        return "paper-pdf", "Compiled paper or document PDF"
    if suffix in FIGURE_EXTENSIONS:
        return "figure", "Figure or visual compilation asset"
    if suffix in FONT_EXTENSIONS:
        return "compilation-asset", "Font required by the paper or project"
    if suffix == ".ipynb":
        return "experiment-notebook", "Experiment notebook"
    if suffix in CODE_EXTENSIONS:
        return "experiment-code", "Experiment or project source code"
    if suffix in CONFIG_EXTENSIONS or name in REPOSITORY_FILENAMES:
        if name.startswith("readme") or name == "files.md" or suffix in {".md", ".rst"}:
            return "documentation", "Repository documentation"
        return "configuration", "Build, environment, or repository configuration"
    if suffix in DOCUMENT_EXTENSIONS:
        return "documentation", "Project documentation"
    if suffix in SMALL_DATA_EXTENSIONS:
        return "compilation-asset", "Small table or structured project asset"
    return None


def classify_path(
    repo: Path | str,
    relative: str,
    *,
    tracked: bool,
    max_size_bytes: int = DEFAULT_MAX_SIZE_BYTES,
) -> FileDecision:
    repo_path = Path(repo).resolve()
    normalised = _normalise(relative)
    pure = PurePosixPath(normalised)
    lower_parts = tuple(part.lower() for part in pure.parts)
    name = pure.name.lower()
    suffix = pure.suffix.lower()
    candidate = repo_path.joinpath(*pure.parts)

    if candidate.is_symlink():
        target = candidate.resolve(strict=False)
        try:
            target.relative_to(repo_path)
        except ValueError:
            return FileDecision(normalised, "block", "Symlink resolves outside repository", "blocked", "", tracked)

    if candidate.exists() and candidate.is_file() and candidate.stat().st_size > max_size_bytes:
        return FileDecision(normalised, "block", "File exceeds publication size limit", "blocked", "", tracked)

    if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
        return FileDecision(normalised, "block", "Credential environment file", "blocked", "", tracked)
    if name in BLOCKED_CREDENTIAL_NAMES or any(part in BLOCKED_CREDENTIAL_DIRECTORIES for part in lower_parts[:-1]):
        return FileDecision(normalised, "block", "Credential or private material path", "blocked", "", tracked)
    if suffix in BLOCKED_ARTIFACT_EXTENSIONS:
        return FileDecision(normalised, "block", "Dataset, model weight, or checkpoint artifact", "blocked", "", tracked)
    if suffix in SMALL_DATA_EXTENSIONS and any(part in RAW_DATA_DIRECTORIES for part in lower_parts[:-1]):
        return FileDecision(normalised, "block", "Raw dataset path", "blocked", "", tracked)

    if any(part in EXCLUDED_DIRECTORIES for part in lower_parts[:-1]):
        return FileDecision(normalised, "exclude", "Generated, cache, or local directory", "excluded", "", tracked)
    if normalised.lower().endswith((".synctex.gz", ".run.xml")) or suffix in EXCLUDED_EXTENSIONS:
        return FileDecision(normalised, "exclude", "Generated or temporary file", "excluded", "", tracked)
    if any(part in RESULT_DIRECTORIES for part in lower_parts[:-1]) and suffix in {".log", ".txt", ".json"}:
        return FileDecision(normalised, "exclude", "Generated experiment result or log", "excluded", "", tracked)
    if _plan_markdown(pure):
        return FileDecision(normalised, "exclude", "AI planning or process Markdown", "excluded", "", tracked)

    category = _category_for(pure)
    if category is None:
        return FileDecision(normalised, "exclude", "Unsupported untracked file type", "excluded", "", tracked)
    return FileDecision(normalised, "include", "Publishable research project file", category[0], category[1], tracked)


def _scan_secret_bytes(data: bytes) -> str | None:
    if b"\x00" in data:
        return None
    text = data.decode("utf-8", errors="replace")
    for label, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            return label
    return None


def scan_secret(
    path: Path | str,
    *,
    max_bytes: int = DEFAULT_MAX_SIZE_BYTES,
) -> str | None:
    candidate = Path(path)
    if not candidate.exists() or not candidate.is_file() or candidate.stat().st_size > max_bytes:
        return None
    try:
        data = candidate.read_bytes()
    except OSError:
        return "Unreadable file during secret scan"
    return _scan_secret_bytes(data)


def render_manifest(decisions: Iterable[FileDecision]) -> str:
    included = {decision.path: decision for decision in decisions if decision.action == "include"}
    if "FILES.md" not in included:
        included["FILES.md"] = FileDecision(
            "FILES.md",
            "include",
            "Required generated inventory",
            "documentation",
            "Generated repository file inventory",
            False,
        )
    lines = [
        "# Repository Files",
        "",
        "> This file is generated by `publish-research-to-github`. Do not edit it manually.",
        "",
        "| Path | Category | Purpose |",
        "| --- | --- | --- |",
    ]
    for path in sorted(included, key=str.casefold):
        decision = included[path]
        escaped_path = path.replace("|", "\\|").replace("`", "\\`")
        category = decision.category.replace("|", "\\|")
        purpose = decision.purpose.replace("|", "\\|")
        lines.append(f"| `{escaped_path}` | {category} | {purpose} |")
    lines.append("")
    return "\n".join(lines)


def validate_readme(text: str) -> None:
    meaningful = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if len(text.strip()) < 60 or not meaningful:
        raise PublishError("README.md must contain a meaningful project description")
    if "files.md" not in text.lower():
        raise PublishError("README.md must link to FILES.md")


def validate_commit_message(message: str, changes: dict[str, list[str]]) -> None:
    text = message.strip()
    if not text:
        raise PublishError("Commit message is empty")
    subject = text.splitlines()[0].strip()
    if len(subject) > 72:
        raise PublishError("Commit subject must be at most 72 characters")
    if subject.lower() in {"update", "update files", "changes", "misc changes"}:
        raise PublishError("Commit subject is too generic")
    secret_rule = _scan_secret_bytes(text.encode("utf-8"))
    if secret_rule:
        raise PublishError(f"Commit message matched secret rule: {secret_rule}")
    section_match = re.search(
        r"(?ms)^Files:\s*(?P<files>.*?)^Changes:\s*(?P<changes>.*?)^Features:\s*(?P<features>.*)$",
        text,
    )
    if not section_match:
        raise PublishError("Commit message must contain Files, Changes, and Features sections")
    if not section_match.group("changes").strip(" \r\n-"):
        raise PublishError("Changes section must describe the implementation")
    if not section_match.group("features").strip(" \r\n-"):
        raise PublishError("Features section must describe functionality")
    files_section = section_match.group("files")
    parsed: dict[str, list[str]] = {}
    nonempty_lines = [line.strip() for line in files_section.splitlines() if line.strip()]
    if len(nonempty_lines) != 3:
        raise PublishError("Files section must contain exactly Added, Modified, and Deleted entries")
    for label, key in (("Added", "added"), ("Modified", "modified"), ("Deleted", "deleted")):
        matches = [
            match
            for line in nonempty_lines
            if (match := re.fullmatch(rf"-\s*{label}:\s*(.+)", line, flags=re.IGNORECASE))
        ]
        if len(matches) != 1:
            raise PublishError(f"Files section must contain exactly one {label} entry")
        raw_value = matches[0].group(1).strip()
        if raw_value.casefold() == "none":
            parsed[key] = []
            continue
        try:
            raw_paths = next(csv.reader([raw_value], skipinitialspace=True))
        except csv.Error as exc:
            raise PublishError(f"Unable to parse {label} file list: {exc}") from exc
        paths: list[str] = []
        for raw_path in raw_paths:
            cleaned = raw_path.strip()
            if cleaned.startswith("`") and cleaned.endswith("`") and len(cleaned) >= 2:
                cleaned = cleaned[1:-1]
            paths.append(_normalise(cleaned))
        if len(paths) != len(set(paths)):
            raise PublishError(f"{label} file list contains duplicate paths")
        parsed[key] = sorted(paths, key=str.casefold)

    expected = {key: sorted(value, key=str.casefold) for key, value in changes.items()}
    if parsed != expected:
        raise PublishError(f"Commit file lists do not match staged changes: expected {expected}, got {parsed}")


def _redact(text: str) -> str:
    redacted = re.sub(r"(?i)(https?://)[^/@\s]+@", r"\1***@", text)
    for _, pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted.strip()


def _git(
    repo: Path,
    *args: str,
    check: bool = True,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    process = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        encoding="utf-8",
        errors="replace",
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and process.returncode != 0:
        detail = _redact(process.stderr or process.stdout) or f"exit code {process.returncode}"
        raise PublishError(f"Git command '{args[0] if args else 'git'}' failed: {detail}")
    return process


def _nul_paths(output: str) -> list[str]:
    return [_normalise(item) for item in output.split("\0") if item]


def _repository_root(repo: Path | str) -> Path:
    candidate = Path(repo).resolve()
    if not candidate.is_dir():
        raise PublishError(f"Repository directory does not exist: {candidate}")
    result = _git(candidate, "rev-parse", "--show-toplevel", check=False)
    if result.returncode != 0:
        raise PublishError(f"Not a Git worktree: {candidate}")
    return Path(result.stdout.strip()).resolve()


def _operation_in_progress(repo: Path) -> str | None:
    markers = {
        "MERGE_HEAD": "merge",
        "CHERRY_PICK_HEAD": "cherry-pick",
        "REVERT_HEAD": "revert",
        "rebase-apply": "rebase",
        "rebase-merge": "rebase",
        "BISECT_LOG": "bisect",
    }
    for marker, operation in markers.items():
        marker_path = _git(repo, "rev-parse", "--git-path", marker).stdout.strip()
        candidate = Path(marker_path)
        if not candidate.is_absolute():
            candidate = repo / candidate
        if candidate.exists():
            return operation
    return None


def validate_repository(repo: Path | str, remote: str = "origin") -> tuple[Path, str]:
    root = _repository_root(repo)
    branch_result = _git(root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    if branch_result.returncode != 0 or not branch_result.stdout.strip():
        raise PublishError("Detached HEAD is not publishable; check out a named branch")
    branch = branch_result.stdout.strip()
    if _git(root, "remote", "get-url", remote, check=False).returncode != 0:
        raise PublishError(f"Git remote '{remote}' is not configured")
    conflicts = _git(root, "diff", "--name-only", "--diff-filter=U", "-z").stdout
    if conflicts:
        raise PublishError("Resolve merge conflicts before publishing")
    operation = _operation_in_progress(root)
    if operation:
        raise PublishError(f"Finish or abort the active Git {operation} before publishing")
    staged = _git(root, "diff", "--cached", "--name-only", "-z").stdout
    if staged:
        raise PublishError("Pre-existing staged changes detected; clear or commit them before publishing")
    submodules = _git(root, "submodule", "status", "--recursive", check=False)
    if submodules.returncode not in (0, 1):
        raise PublishError("Unable to inspect Git submodules")
    dirty_submodules = [line for line in submodules.stdout.splitlines() if line and line[0] in "+-U"]
    if dirty_submodules:
        raise PublishError("Dirty, conflicted, or uninitialized submodule detected")
    return root, branch


def _tracked_paths(repo: Path) -> set[str]:
    return set(_nul_paths(_git(repo, "ls-files", "-z").stdout))


def _untracked_paths(repo: Path) -> set[str]:
    return set(_nul_paths(_git(repo, "ls-files", "--others", "--exclude-standard", "-z").stdout))


def _outbound_revision(repo: Path, remote: str, branch: str) -> str | None:
    remote_ref = f"refs/heads/{branch}"
    result = _git(repo, "ls-remote", "--heads", remote, remote_ref, check=False)
    if result.returncode != 0:
        detail = _redact(result.stderr or result.stdout) or f"exit code {result.returncode}"
        raise PublishError(f"Unable to inspect remote branch '{remote}/{branch}': {detail}")
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if len(lines) > 1:
        raise PublishError(f"Remote branch lookup returned multiple matches for '{remote}/{branch}'")
    remote_tip: str | None = None
    if lines:
        remote_tip = lines[0].split("\t", 1)[0].strip()
        if not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", remote_tip):
            raise PublishError(f"Remote branch '{remote}/{branch}' returned an invalid object ID")

    has_head = _git(repo, "rev-parse", "--verify", "HEAD", check=False).returncode == 0
    if not has_head:
        if remote_tip:
            raise PublishError("The remote branch already has history, but the local branch has no commit")
        return None
    if remote_tip is None:
        return "HEAD"
    if _git(repo, "cat-file", "-e", f"{remote_tip}^{{commit}}", check=False).returncode != 0:
        raise PublishError(
            f"Remote tip for '{remote}/{branch}' is not available locally; fetch and reconcile it manually"
        )
    if _git(repo, "merge-base", "--is-ancestor", remote_tip, "HEAD", check=False).returncode != 0:
        raise PublishError(
            f"Remote branch '{remote}/{branch}' is not an ancestor of local HEAD; reconcile it manually"
        )
    return f"{remote_tip}..HEAD"


def _read_blob(repo: Path, object_id: str) -> bytes:
    process = subprocess.run(
        ["git", "cat-file", "blob", object_id],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.returncode != 0:
        detail = _redact(process.stderr.decode("utf-8", errors="replace"))
        raise PublishError(f"Unable to inspect outbound Git blob: {detail or 'unknown error'}")
    return process.stdout


def scan_outbound_history(
    repo: Path | str,
    *,
    remote: str,
    branch: str,
    max_size_bytes: int = DEFAULT_MAX_SIZE_BYTES,
) -> list[str]:
    root = _repository_root(repo)
    revision = _outbound_revision(root, remote, branch)
    if revision is None:
        return []

    messages = _git(root, "log", "--format=%B%x00", revision).stdout.encode("utf-8", errors="replace")
    message_rule = _scan_secret_bytes(messages)
    findings: set[str] = set()
    if message_rule:
        findings.add(f"outbound commit message (secret rule: {message_rule})")

    object_lines = _git(root, "rev-list", "--objects", revision).stdout.splitlines()
    object_paths: dict[str, set[str]] = {}
    for line in object_lines:
        object_id, separator, raw_path = line.partition(" ")
        if not separator or not raw_path:
            continue
        try:
            path = _normalise(raw_path)
        except PublishError:
            findings.add("outbound history contains an unsafe repository path")
            continue
        object_paths.setdefault(object_id, set()).add(path)
    if not object_paths:
        return sorted(findings, key=str.casefold)

    checks = _git(
        root,
        "cat-file",
        "--batch-check=%(objectname) %(objecttype) %(objectsize)",
        input_text="".join(f"{object_id}\n" for object_id in object_paths),
    ).stdout.splitlines()
    object_metadata: dict[str, tuple[str, int]] = {}
    for line in checks:
        parts = line.split()
        if len(parts) == 3 and parts[2].isdigit():
            object_metadata[parts[0]] = (parts[1], int(parts[2]))

    for object_id, paths in object_paths.items():
        object_type, size = object_metadata.get(object_id, ("", 0))
        if object_type != "blob":
            continue
        for path in paths:
            decision = classify_path(root, path, tracked=True, max_size_bytes=max_size_bytes)
            if decision.action in {"exclude", "block"}:
                findings.add(f"{path} ({decision.reason})")
            if size > max_size_bytes:
                findings.add(f"{path} (historical blob exceeds publication size limit)")
        if size <= max_size_bytes:
            secret_rule = _scan_secret_bytes(_read_blob(root, object_id))
            if secret_rule:
                for path in paths:
                    findings.add(f"{path} (historical secret rule: {secret_rule})")
    return sorted(findings, key=str.casefold)


def discover_repository(
    repo: Path | str,
    *,
    max_size_bytes: int = DEFAULT_MAX_SIZE_BYTES,
) -> list[FileDecision]:
    root = _repository_root(repo)
    tracked_paths = _tracked_paths(root)
    paths = tracked_paths | _untracked_paths(root) | {"FILES.md"}
    decisions: list[FileDecision] = []
    for path in sorted(paths, key=str.casefold):
        tracked = path in tracked_paths
        decision = classify_path(
            root,
            path,
            tracked=tracked,
            max_size_bytes=max_size_bytes,
        )
        candidate = root.joinpath(*PurePosixPath(path).parts)
        if decision.action == "include" and candidate.exists() and candidate.is_file():
            secret_rule = scan_secret(candidate, max_bytes=max_size_bytes)
            if secret_rule:
                decision = FileDecision(
                    decision.path,
                    "block",
                    f"Secret scan matched rule: {secret_rule}",
                    "blocked",
                    "",
                    tracked,
                )
        decisions.append(decision)
    return decisions


def _blocked_message(decisions: Sequence[FileDecision]) -> str:
    findings = [f"{item.path} ({item.reason})" for item in decisions if item.action == "block"]
    return "Publication blocked:\n- " + "\n- ".join(findings)


def _diff_paths(repo: Path, diff_filter: str) -> set[str]:
    if _git(repo, "rev-parse", "--verify", "HEAD", check=False).returncode != 0:
        return set()
    output = _git(
        repo,
        "diff",
        "--no-renames",
        "--name-only",
        f"--diff-filter={diff_filter}",
        "-z",
        "HEAD",
        "--",
    ).stdout
    return set(_nul_paths(output))


def collect_changes(repo: Path | str) -> dict[str, list[str]]:
    root = _repository_root(repo)
    decisions = discover_repository(root)
    included = {item.path for item in decisions if item.action == "include"}
    tracked_removals = {
        item.path
        for item in decisions
        if item.tracked and item.action == "exclude" and root.joinpath(*PurePosixPath(item.path).parts).exists()
    }
    added = _untracked_paths(root) & included
    modified = _diff_paths(root, "MRTUXB") & included
    deleted = _diff_paths(root, "D") | tracked_removals
    return {
        "added": sorted(added, key=str.casefold),
        "modified": sorted(modified, key=str.casefold),
        "deleted": sorted(deleted, key=str.casefold),
    }


def _decision_json(decision: FileDecision) -> dict[str, Any]:
    return {
        "path": decision.path,
        "action": decision.action,
        "reason": decision.reason,
        "category": decision.category,
        "purpose": decision.purpose,
        "tracked": decision.tracked,
    }


def prepare_repository(
    repo: Path | str,
    *,
    remote: str = "origin",
    max_size_bytes: int = DEFAULT_MAX_SIZE_BYTES,
) -> dict[str, Any]:
    root, branch = validate_repository(repo, remote)
    history_findings = scan_outbound_history(
        root,
        remote=remote,
        branch=branch,
        max_size_bytes=max_size_bytes,
    )
    if history_findings:
        raise PublishError("Publication blocked by outbound Git history:\n- " + "\n- ".join(history_findings))
    decisions = discover_repository(root, max_size_bytes=max_size_bytes)
    if any(item.action == "block" for item in decisions):
        raise PublishError(_blocked_message(decisions))

    manifest = render_manifest(decisions)
    manifest_path = root / "FILES.md"
    current = manifest_path.read_text(encoding="utf-8") if manifest_path.exists() else None
    if current != manifest:
        manifest_path.write_text(manifest, encoding="utf-8", newline="\n")

    decisions = discover_repository(root, max_size_bytes=max_size_bytes)
    if any(item.action == "block" for item in decisions):
        raise PublishError(_blocked_message(decisions))
    changes = collect_changes(root)
    return {
        "ok": True,
        "phase": "prepare",
        "repository": str(root),
        "remote": remote,
        "branch": branch,
        "included": [_decision_json(item) for item in decisions if item.action == "include"],
        "excluded": [_decision_json(item) for item in decisions if item.action == "exclude"],
        "remove_from_git": sorted(
            [
                item.path
                for item in decisions
                if item.tracked
                and item.action == "exclude"
                and root.joinpath(*PurePosixPath(item.path).parts).exists()
            ],
            key=str.casefold,
        ),
        "changes": changes,
    }


def _cached_changes(repo: Path) -> dict[str, list[str]]:
    return {
        "added": sorted(
            _nul_paths(
                _git(repo, "diff", "--cached", "--no-renames", "--name-only", "--diff-filter=A", "-z").stdout
            ),
            key=str.casefold,
        ),
        "modified": sorted(
            _nul_paths(
                _git(
                    repo,
                    "diff",
                    "--cached",
                    "--no-renames",
                    "--name-only",
                    "--diff-filter=MRTUXB",
                    "-z",
                ).stdout
            ),
            key=str.casefold,
        ),
        "deleted": sorted(
            _nul_paths(
                _git(repo, "diff", "--cached", "--no-renames", "--name-only", "--diff-filter=D", "-z").stdout
            ),
            key=str.casefold,
        ),
    }


def _stage_exact(repo: Path, changes: dict[str, list[str]], remove_from_git: set[str]) -> None:
    additions_and_modifications = changes["added"] + changes["modified"]
    if additions_and_modifications:
        _git(repo, "--literal-pathspecs", "add", "--", *additions_and_modifications)
    for path in changes["deleted"]:
        if path in remove_from_git:
            _git(repo, "--literal-pathspecs", "rm", "--cached", "--ignore-unmatch", "--", path)
        else:
            _git(repo, "--literal-pathspecs", "add", "-u", "--", path)
    actual = _cached_changes(repo)
    expected = {key: sorted(value, key=str.casefold) for key, value in changes.items()}
    if actual != expected:
        _git(repo, "reset", "--quiet", check=False)
        raise PublishError(f"Staged paths differ from the approved change set: expected {expected}, got {actual}")


def publish_repository(
    repo: Path | str,
    message_file: Path | str,
    *,
    remote: str = "origin",
    max_size_bytes: int = DEFAULT_MAX_SIZE_BYTES,
) -> dict[str, Any]:
    root = _repository_root(repo)
    message_path = Path(message_file).resolve()
    if not message_path.is_file():
        raise PublishError(f"Commit message file does not exist: {message_path}")
    try:
        message_path.relative_to(root)
    except ValueError:
        pass
    else:
        raise PublishError("Commit message file must be outside the repository")

    prepared = prepare_repository(
        root,
        remote=remote,
        max_size_bytes=max_size_bytes,
    )
    readme_path = root / "README.md"
    if not readme_path.is_file():
        raise PublishError("README.md is required before publishing")
    validate_readme(readme_path.read_text(encoding="utf-8", errors="replace"))
    changes = prepared["changes"]
    if not any(changes.values()):
        raise PublishError("No publishable changes found; no commit was created")
    message = message_path.read_text(encoding="utf-8", errors="replace")
    validate_commit_message(message, changes)

    remove_from_git = set(prepared["remove_from_git"])
    _stage_exact(root, changes, remove_from_git)
    staged_changes = _cached_changes(root)
    validate_commit_message(message, staged_changes)
    whitespace = _git(root, "diff", "--cached", "--check", check=False)
    if whitespace.returncode != 0:
        _git(root, "reset", "--quiet", check=False)
        raise PublishError(f"Staged diff failed whitespace validation: {_redact(whitespace.stdout)}")

    _git(root, "commit", "-F", "-", input_text=message)
    commit = _git(root, "rev-parse", "HEAD").stdout.strip()
    branch = prepared["branch"]
    try:
        _git(root, "push", "--porcelain", "--set-upstream", remote, f"HEAD:refs/heads/{branch}")
    except PublishError as exc:
        raise PublishError(f"Commit {commit} was created locally, but push failed: {exc}") from exc
    return {
        "ok": True,
        "phase": "publish",
        "commit": commit,
        "remote": remote,
        "branch": branch,
        "changes": staged_changes,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely prepare, commit, and push research repository files."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("prepare", "publish"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--repo", default=".", help="Path inside the target Git worktree")
        subparser.add_argument("--remote", default="origin", help="Configured Git remote name")
        subparser.add_argument(
            "--max-size-mib",
            type=float,
            default=50.0,
            help="Maximum publishable file size in MiB (default: 50)",
        )
        if command == "publish":
            subparser.add_argument(
                "--message-file",
                required=True,
                help="UTF-8 commit message file outside the repository",
            )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.max_size_mib <= 0:
        parser.error("--max-size-mib must be greater than zero")
    max_size_bytes = int(args.max_size_mib * 1024 * 1024)
    try:
        if args.command == "prepare":
            report = prepare_repository(
                args.repo,
                remote=args.remote,
                max_size_bytes=max_size_bytes,
            )
        else:
            report = publish_repository(
                args.repo,
                args.message_file,
                remote=args.remote,
                max_size_bytes=max_size_bytes,
            )
    except PublishError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
