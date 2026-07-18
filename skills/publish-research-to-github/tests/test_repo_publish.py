from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from unittest import mock
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = SKILL_ROOT / "scripts" / "repo_publish.py"
SPEC = importlib.util.spec_from_file_location("repo_publish", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot load publishing module from {MODULE_PATH}")
repo_publish = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(repo_publish)


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=check,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def write(repo: Path, relative: str, content: str = "content\n") -> Path:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def write_message(path: Path, content: str) -> Path:
    path.write_bytes(content.encode("utf-8"))
    return path


def synthetic_github_token() -> str:
    return "gh" + "p_" + "abcdefghijklmnopqrstuvwxyz123456"


def write_hook(repo: Path, name: str, content: str) -> Path:
    path = repo / ".git" / "hooks" / name
    path.write_bytes(content.encode("utf-8"))
    path.chmod(0o755)
    return path


def init_repository(root: Path) -> tuple[Path, Path]:
    repo = root / "worktree"
    remote = root / "remote.git"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Skill Test")
    git(repo, "config", "user.email", "skill-test@example.invalid")
    write(
        repo,
        "README.md",
        "# Reproducible Research\n\nThis repository contains the paper and experiment code.\n\n"
        "See [FILES.md](FILES.md) for the complete file inventory.\n",
    )
    write(repo, "paper/main.tex", "\\documentclass{article}\n\\begin{document}Test\\end{document}\n")
    git(repo, "add", "--", "README.md", "paper/main.tex")
    git(repo, "commit", "-m", "Initialize research repository")
    git(root, "init", "--bare", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-u", "origin", "main")
    return repo, remote


class FilePolicyTests(unittest.TestCase):
    def test_test_module_contains_no_literal_secret_pattern(self) -> None:
        self.assertIsNone(repo_publish.scan_secret(Path(__file__)))

    def test_includes_paper_assets_and_experiment_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            expected = {
                "paper/main.tex": "paper-source",
                "paper/references.bib": "bibliography",
                "paper/main.pdf": "paper-pdf",
                "figures/overview.png": "figure",
                "experiments/train.py": "experiment-code",
                "configs/base.yaml": "configuration",
                "environment.yml": "configuration",
                "Makefile": "configuration",
                ".gitmodules": "configuration",
            }
            for relative, category in expected.items():
                write(root, relative)
                decision = repo_publish.classify_path(root, relative, tracked=False)
                self.assertEqual("include", decision.action, relative)
                self.assertEqual(category, decision.category, relative)

    def test_excludes_result_evidence_output_and_artifact_directories_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            excluded = [
                "paper/results/metrics.csv",
                "paper/evidence/claim.json",
                "outputs/figure.png",
                "artifacts/submission.pdf",
            ]
            for relative in excluded:
                write(root, relative)
                decision = repo_publish.classify_path(root, relative, tracked=False)
                self.assertEqual("exclude", decision.action, relative)

    def test_blocks_notebooks_with_saved_execution_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clean = {
                "cells": [
                    {
                        "cell_type": "code",
                        "execution_count": None,
                        "metadata": {},
                        "outputs": [],
                        "source": ["print('clean')\n"],
                    }
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
            clean_path = write(root, "notebooks/clean.ipynb", json.dumps(clean))
            clean_decision = repo_publish.classify_path(
                root, clean_path.relative_to(root).as_posix(), tracked=False
            )
            self.assertEqual("include", clean_decision.action)

            executed = dict(clean)
            executed["cells"] = [dict(clean["cells"][0])]
            executed["cells"][0]["execution_count"] = 1
            executed["cells"][0]["outputs"] = [
                {"name": "stdout", "output_type": "stream", "text": ["local result\n"]}
            ]
            executed_path = write(root, "notebooks/executed.ipynb", json.dumps(executed))
            executed_decision = repo_publish.classify_path(
                root, executed_path.relative_to(root).as_posix(), tracked=False
            )
            self.assertEqual("block", executed_decision.action)
            self.assertIn("saved execution", executed_decision.reason.lower())

            ignored_copy = write(root, "artifacts/executed.ipynb", json.dumps(executed))
            ignored_decision = repo_publish.classify_path(
                root, ignored_copy.relative_to(root).as_posix(), tracked=False
            )
            self.assertEqual("exclude", ignored_decision.action)

            malformed_root = write(root, "notebooks/malformed-root.ipynb", "[]")
            malformed = repo_publish.classify_path(
                root, malformed_root.relative_to(root).as_posix(), tracked=False
            )
            self.assertEqual("block", malformed.action)
            self.assertIn("root", malformed.reason.lower())

            malformed_cell = dict(clean)
            malformed_cell["cells"] = [dict(clean["cells"][0])]
            malformed_cell["cells"][0]["outputs"] = {}
            malformed_path = write(root, "notebooks/malformed-cell.ipynb", json.dumps(malformed_cell))
            malformed_decision = repo_publish.classify_path(
                root, malformed_path.relative_to(root).as_posix(), tracked=False
            )
            self.assertEqual("block", malformed_decision.action)
            self.assertIn("outputs", malformed_decision.reason.lower())

            missing_format = json.loads(json.dumps(clean))
            missing_format.pop("nbformat")
            missing_format_path = write(
                root, "notebooks/missing-format.ipynb", json.dumps(missing_format)
            )
            missing_format_decision = repo_publish.classify_path(
                root, missing_format_path.relative_to(root).as_posix(), tracked=False
            )
            self.assertEqual("block", missing_format_decision.action)
            self.assertIn("nbformat", missing_format_decision.reason.lower())

            malformed_markdown = json.loads(json.dumps(clean))
            malformed_markdown["cells"] = [{"cell_type": "markdown", "source": 42}]
            malformed_markdown_path = write(
                root, "notebooks/malformed-markdown.ipynb", json.dumps(malformed_markdown)
            )
            malformed_markdown_decision = repo_publish.classify_path(
                root, malformed_markdown_path.relative_to(root).as_posix(), tracked=False
            )
            self.assertEqual("block", malformed_markdown_decision.action)
            self.assertIn("metadata", malformed_markdown_decision.reason.lower())

            split_path_notebook = json.loads(json.dumps(clean))
            split_path_notebook["cells"][0]["source"] = ["D:", "\\dev\\private-project"]
            split_path_file = write(
                root, "notebooks/split-local-path.ipynb", json.dumps(split_path_notebook)
            )
            split_path_decision = repo_publish.classify_path(
                root, split_path_file.relative_to(root).as_posix(), tracked=False
            )
            self.assertEqual("block", split_path_decision.action)
            self.assertIn("machine-specific local path", split_path_decision.reason.lower())

    def test_blocks_machine_specific_notebook_paths_but_allows_colab_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            notebook = {
                "cells": [
                    {
                        "cell_type": "code",
                        "execution_count": None,
                        "metadata": {},
                        "outputs": [],
                        "source": [
                            'DRIVE_ROOT = "/content/drive/MyDrive/research"\n',
                        ],
                    }
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
            portable_path = write(root, "notebooks/portable.ipynb", json.dumps(notebook))
            portable = repo_publish.classify_path(
                root, portable_path.relative_to(root).as_posix(), tracked=False
            )
            self.assertEqual("include", portable.action)

            notebook["cells"][0]["source"] = [
                'LOCAL_REPO_ROOT = r"D:\\dev\\private-project"\n',
            ]
            local_path = write(root, "notebooks/local-path.ipynb", json.dumps(notebook))
            local = repo_publish.classify_path(
                root, local_path.relative_to(root).as_posix(), tracked=False
            )
            self.assertEqual("block", local.action)
            self.assertIn("machine-specific local path", local.reason.lower())

    def test_excludes_latex_temporaries_caches_logs_and_ai_plans(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            excluded = [
                "paper/main.aux",
                "paper/main.log",
                "paper/main.synctex.gz",
                "__pycache__/train.pyc",
                ".pytest_cache/state.json",
                "results/run.log",
                "logs/metrics.json",
                "run_states/state.yaml",
                "AI_PLAN.md",
                "docs/EXPERIMENT_PLAN.md",
                "TODO.md",
                "docs/superpowers/specs/design.md",
            ]
            for relative in excluded:
                write(root, relative)
                decision = repo_publish.classify_path(root, relative, tracked=False)
                self.assertEqual("exclude", decision.action, relative)

    def test_blocks_credentials_datasets_weights_and_large_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blocked = [
                ".env",
                "secrets/id_rsa",
                "data/raw.csv",
                "checkpoints/model.pt",
                "weights/model.safetensors",
            ]
            for relative in blocked:
                write(root, relative)
                decision = repo_publish.classify_path(root, relative, tracked=False)
                self.assertEqual("block", decision.action, relative)

            for relative in ["checkpoints/state.yaml", "weights/model.json"]:
                write(root, relative)
                decision = repo_publish.classify_path(root, relative, tracked=False)
                self.assertEqual("block", decision.action, relative)

            write(root, "paper/huge.pdf", "x" * 128)
            decision = repo_publish.classify_path(
                root, "paper/huge.pdf", tracked=False, max_size_bytes=64
            )
            self.assertEqual("block", decision.action)
            self.assertIn("size", decision.reason.lower())

    def test_env_example_is_allowed_when_it_contains_no_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, ".env.example", "API_KEY=your_api_key_here\n")
            decision = repo_publish.classify_path(root, ".env.example", tracked=False)
            self.assertEqual("include", decision.action)

    def test_tracked_files_do_not_bypass_policy_and_plan_tokens_are_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in ["archive.zip", "project-design-notes.md", "tasks-2026.md"]:
                write(root, relative)
                decision = repo_publish.classify_path(root, relative, tracked=True)
                self.assertEqual("exclude", decision.action, relative)

    def test_detects_secret_content_without_returning_the_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            token = synthetic_github_token()
            path = write(root, "experiments/config.py", f'GITHUB_TOKEN = "{token}"\n')
            finding = repo_publish.scan_secret(path)
            self.assertIsNotNone(finding)
            self.assertNotIn(token, finding or "")

    def test_detects_secret_near_end_of_large_publishable_text_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            token = synthetic_github_token()
            path = write(root, "experiments/large.py", ("# padding\n" * 300_000) + f'TOKEN = "{token}"\n')
            finding = repo_publish.scan_secret(path, max_bytes=50 * 1024 * 1024)
            self.assertIsNotNone(finding)
            self.assertNotIn(token, finding or "")

    def test_detects_secret_content_after_a_nul_byte(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            token = synthetic_github_token().encode("ascii")
            path = root / "experiments" / "nul.py"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"prefix\x00GITHUB_TOKEN=" + token + b"\n")
            finding = repo_publish.scan_secret(path)
            self.assertIsNotNone(finding)
            self.assertNotIn(token.decode("ascii"), finding or "")

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support unavailable")
    def test_blocks_symlink_that_resolves_outside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            outside_file = write(Path(outside), "private.txt", "private\n")
            link = root / "paper" / "external.txt"
            link.parent.mkdir(parents=True)
            try:
                link.symlink_to(outside_file)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            decision = repo_publish.classify_path(root, "paper/external.txt", tracked=False)
            self.assertEqual("block", decision.action)


class DocumentationTests(unittest.TestCase):
    def test_manifest_is_stable_complete_and_excludes_non_publishable_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in [
                "README.md",
                "paper/main.tex",
                "figures/z.png",
                "experiments/run.py",
                "main.aux",
            ]:
                write(root, relative)
            decisions = [
                repo_publish.classify_path(root, relative, tracked=False)
                for relative in [
                    "figures/z.png",
                    "README.md",
                    "paper/main.tex",
                    "experiments/run.py",
                    "main.aux",
                    "FILES.md",
                ]
            ]
            manifest = repo_publish.render_manifest(decisions)
            self.assertIn("generated", manifest.lower())
            self.assertIn("`FILES.md`", manifest)
            self.assertIn("`README.md`", manifest)
            self.assertIn("`paper/main.tex`", manifest)
            self.assertNotIn("main.aux", manifest)
            paths = [
                line.split("`")[1]
                for line in manifest.splitlines()
                if line.startswith("| `")
            ]
            self.assertEqual(sorted(paths, key=str.casefold), paths)

    def test_readme_requires_project_content_and_files_link(self) -> None:
        valid = (
            "# Research Project\n\nThis repository contains a paper and reproducible experiments.\n\n"
            "See [FILES.md](FILES.md) for the complete inventory.\n"
        )
        repo_publish.validate_readme(valid)
        with self.assertRaises(repo_publish.PublishError):
            repo_publish.validate_readme("# Project\n")

    def test_commit_message_requires_sections_and_every_changed_path(self) -> None:
        changes = {
            "added": ["FILES.md", "experiments/run.py"],
            "modified": ["README.md"],
            "deleted": ["figures/old.png"],
        }
        valid = (
            "Add reproducible experiment runner\n\n"
            "Files:\n"
            "- Added: FILES.md, experiments/run.py\n"
            "- Modified: README.md\n"
            "- Deleted: figures/old.png\n\n"
            "Changes:\n- Documented and implemented the new runner.\n\n"
            "Features:\n- Add a reproducible experiment entry point.\n"
        )
        repo_publish.validate_commit_message(valid, changes)
        with self.assertRaises(repo_publish.PublishError):
            repo_publish.validate_commit_message("Update files\n", changes)
        with self.assertRaises(repo_publish.PublishError):
            repo_publish.validate_commit_message(valid.replace("experiments/run.py", "None"), changes)
        with self.assertRaisesRegex(repo_publish.PublishError, "commas"):
            repo_publish.validate_commit_message(
                valid.replace("FILES.md, experiments/run.py", "FILES.md; experiments/run.py"),
                changes,
            )
        with self.assertRaises(repo_publish.PublishError):
            repo_publish.validate_commit_message(
                valid.replace(
                    "- Added: FILES.md, experiments/run.py\n- Modified: README.md",
                    "- Added: FILES.md\n- Modified: README.md, experiments/run.py",
                ),
                changes,
            )
        with self.assertRaises(repo_publish.PublishError):
            repo_publish.validate_commit_message(
                valid.replace("FILES.md, experiments/run.py", "FILES.md, experiments/run.py, extra.txt"),
                changes,
            )
        with self.assertRaises(repo_publish.PublishError):
            repo_publish.validate_commit_message(
                valid.replace(
                    "Features:\n- Add a reproducible experiment entry point.",
                    f"Features:\n- TOKEN={synthetic_github_token()}",
                ),
                changes,
            )

    def test_commit_message_file_requires_utf8_without_bom_and_one_lf(self) -> None:
        valid = (
            "Document publication scope\n\n"
            "Files:\n- Added: None\n- Modified: README.md\n- Deleted: None\n\n"
            "Changes:\n- Document the publication scope.\n\n"
            "Features:\n- No functional change\n"
        ).encode("utf-8")
        invalid_payloads = {
            "BOM": b"\xef\xbb\xbf" + valid,
            "terminal LF": valid.rstrip(b"\n"),
            "exactly one terminal LF": valid + b"\n",
            "blank terminal line": valid + b" \n",
            "LF-only": valid.replace(b"\n", b"\r\n"),
            "UTF-8": b"\xff" + valid,
        }
        with tempfile.TemporaryDirectory() as tmp:
            message_path = Path(tmp) / "commit-message.txt"
            message_path.write_bytes(valid)
            self.assertEqual(valid.decode("utf-8"), repo_publish.read_commit_message_file(message_path))

            for expected_error, payload in invalid_payloads.items():
                with self.subTest(expected_error=expected_error):
                    message_path.write_bytes(payload)
                    with self.assertRaisesRegex(repo_publish.PublishError, expected_error):
                        repo_publish.read_commit_message_file(message_path)

        changes = {"added": [], "modified": ["README.md"], "deleted": []}
        with self.assertRaisesRegex(repo_publish.PublishError, "Files"):
            repo_publish.validate_commit_message("preamble\n\n" + valid.decode("utf-8"), changes)
        with self.assertRaisesRegex(repo_publish.PublishError, "bullet"):
            repo_publish.validate_commit_message(
                valid.decode("utf-8").replace("Changes:\n- Document", "Changes:\nDocument"),
                changes,
            )
        with self.assertRaisesRegex(repo_publish.PublishError, "subject"):
            repo_publish.validate_commit_message(
                valid.decode("utf-8").removeprefix("Document publication scope\n"),
                changes,
            )
        with self.assertRaisesRegex(repo_publish.PublishError, "None"):
            repo_publish.validate_commit_message(
                valid.decode("utf-8").replace("- Added: None", "- Added:   "),
                changes,
            )


class RepositoryIntegrationTests(unittest.TestCase):
    def test_prepare_generates_manifest_without_staging_or_committing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = init_repository(Path(tmp))
            write(repo, "paper/main.pdf", "%PDF-test")
            write(repo, "figures/overview.png", "image")
            write(repo, "experiments/train.py", "print('train')\n")
            write(repo, "Makefile", "test:\n\tpython -m unittest\n")
            write(repo, "paper/main.aux", "temporary")
            write(repo, "AI_PLAN.md", "internal plan")
            before = git(repo, "rev-parse", "HEAD").stdout.strip()

            report = repo_publish.prepare_repository(repo)

            self.assertEqual(before, git(repo, "rev-parse", "HEAD").stdout.strip())
            self.assertEqual("", git(repo, "diff", "--cached", "--name-only").stdout)
            manifest = (repo / "FILES.md").read_text(encoding="utf-8")
            self.assertIn("paper/main.pdf", manifest)
            self.assertIn("experiments/train.py", manifest)
            self.assertIn("Makefile", manifest)
            self.assertNotIn("main.aux", manifest)
            self.assertNotIn("AI_PLAN.md", manifest)
            self.assertIn("paper/main.aux", {item["path"] for item in report["excluded"]})

    def test_prepare_rejects_ignored_or_missing_tracked_makefile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = init_repository(Path(tmp))
            write(repo, ".gitignore", "Makefile\n")
            write(repo, "Makefile", "test:\n\tpython -m unittest\n")
            with self.assertRaisesRegex(repo_publish.PublishError, "Makefile.*ignored"):
                repo_publish.prepare_repository(repo)

        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = init_repository(Path(tmp))
            write(repo, "Makefile", "test:\n\tpython -m unittest\n")
            git(repo, "add", "--", "Makefile")
            git(repo, "commit", "-m", "Add build entry point")
            git(repo, "push", "origin", "main")
            (repo / "Makefile").unlink()
            with self.assertRaisesRegex(repo_publish.PublishError, "Makefile.*missing"):
                repo_publish.prepare_repository(repo)

    def test_prepare_rejects_skip_worktree_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = init_repository(Path(tmp))
            result_path = write(repo, "paper/results/metrics.csv", "metric,value\naccuracy,1.0\n")
            git(repo, "add", "--", "paper/results/metrics.csv")
            git(repo, "commit", "-m", "Track a generated result")
            git(repo, "push", "origin", "main")
            git(repo, "update-index", "--skip-worktree", "paper/results/metrics.csv")
            result_path.unlink()

            with self.assertRaisesRegex(repo_publish.PublishError, "skip-worktree"):
                repo_publish.prepare_repository(repo)

    def test_prepare_rejects_assume_unchanged_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = init_repository(Path(tmp))
            result_path = write(repo, "paper/results/metrics.csv", "metric,value\naccuracy,1.0\n")
            git(repo, "add", "--", "paper/results/metrics.csv")
            git(repo, "commit", "-m", "Track a generated result")
            git(repo, "push", "origin", "main")
            git(repo, "update-index", "--assume-unchanged", "paper/results/metrics.csv")
            result_path.unlink()

            with self.assertRaisesRegex(repo_publish.PublishError, "assume-unchanged"):
                repo_publish.prepare_repository(repo)

    def test_prepare_manifest_omits_deleted_publishable_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = init_repository(Path(tmp))
            (repo / "paper" / "main.tex").unlink()

            report = repo_publish.prepare_repository(repo)

            manifest = (repo / "FILES.md").read_text(encoding="utf-8")
            self.assertNotIn("paper/main.tex", manifest)
            self.assertIn("paper/main.tex", report["changes"]["deleted"])

    def test_prepare_passes_custom_limit_to_change_collection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = init_repository(Path(tmp))
            with mock.patch.object(
                repo_publish,
                "collect_changes",
                wraps=repo_publish.collect_changes,
            ) as collect_changes:
                repo_publish.prepare_repository(repo, max_size_bytes=1_000_000)
            collect_changes.assert_called_once_with(repo, max_size_bytes=1_000_000)

    def test_publish_stages_exact_files_commits_and_pushes_to_local_remote(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, remote = init_repository(root)
            write(repo, "README.md", "# Reproducible Research\n\nPaper and experiment runner.\n\nSee [FILES.md](FILES.md).\n")
            write(repo, "paper/main.pdf", "%PDF-test")
            write(repo, "figures/new.png", "image")
            write(repo, "experiments/run.py", "print('run')\n")
            write(repo, "Makefile", "test:\n\tpython -m unittest\n")
            write(repo, "paper/main.aux", "temporary")
            write(repo, "TODO.md", "internal")
            repo_publish.prepare_repository(repo)
            changes = repo_publish.collect_changes(repo)
            message = (
                "Add reproducible experiment runner\n\n"
                f"Files:\n- Added: {', '.join(changes['added']) or 'None'}\n"
                f"- Modified: {', '.join(changes['modified']) or 'None'}\n"
                f"- Deleted: {', '.join(changes['deleted']) or 'None'}\n\n"
                "Changes:\n- Added the paper PDF, figure, inventory, and experiment entry point.\n\n"
                "Features:\n- Add a reproducible command-line experiment runner.\n"
            )
            message_file = root / "commit-message.txt"
            write_message(message_file, message)

            report = repo_publish.publish_repository(repo, message_file)

            remote_tree = set(
                git(root, "--git-dir", str(remote), "ls-tree", "-r", "--name-only", "main")
                .stdout.splitlines()
            )
            self.assertIn("paper/main.pdf", remote_tree)
            self.assertIn("figures/new.png", remote_tree)
            self.assertIn("experiments/run.py", remote_tree)
            self.assertIn("Makefile", remote_tree)
            self.assertIn("FILES.md", remote_tree)
            self.assertNotIn("paper/main.aux", remote_tree)
            self.assertNotIn("TODO.md", remote_tree)
            self.assertEqual(git(repo, "rev-parse", "HEAD").stdout.strip(), report["commit"])
            self.assertEqual(report["commit"], report["remote_commit"])
            self.assertEqual(git(repo, "rev-parse", "HEAD^{tree}").stdout.strip(), report["tree"])
            self.assertEqual("main", report["branch"])
            committed_message = git(repo, "log", "-1", "--format=%B").stdout
            self.assertIn("Files:", committed_message)
            self.assertIn("Features:", committed_message)

    def test_publish_blocks_secret_injected_by_clean_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, remote = init_repository(root)
            filter_source = (
                "import sys\n"
                "sys.stdin.buffer.read()\n"
                'sys.stdout.write("gh" + "p_" + "abcdefghijklmnopqrstuvwxyz123456" + "\\n")\n'
            )
            write(repo, "inject_filter.py", filter_source)
            write(repo, ".gitattributes", "experiments/filtered.py filter=inject\n")
            write(repo, "experiments/filtered.py", "print('safe worktree')\n")
            git(repo, "config", "filter.inject.clean", "python inject_filter.py")
            repo_publish.prepare_repository(repo)
            changes = repo_publish.collect_changes(repo)
            message = (
                "Add filtered experiment source\n\n"
                f"Files:\n- Added: {', '.join(changes['added']) or 'None'}\n"
                f"- Modified: {', '.join(changes['modified']) or 'None'}\n"
                f"- Deleted: {', '.join(changes['deleted']) or 'None'}\n\n"
                "Changes:\n- Add the filtered experiment fixture.\n\n"
                "Features:\n- Add a safe experiment source.\n"
            )
            message_file = root / "message.txt"
            write_message(message_file, message)
            before_remote = git(root, "--git-dir", str(remote), "rev-parse", "main").stdout.strip()

            with self.assertRaisesRegex(repo_publish.PublishError, "staged tree.*secret"):
                repo_publish.publish_repository(repo, message_file)

            self.assertEqual(
                before_remote,
                git(root, "--git-dir", str(remote), "rev-parse", "main").stdout.strip(),
            )

    def test_publish_blocks_index_changes_made_by_pre_commit_hook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, remote = init_repository(root)
            write(repo, "experiments/run.py", "print('safe')\n")
            repo_publish.prepare_repository(repo)
            changes = repo_publish.collect_changes(repo)
            message = (
                "Add experiment runner\n\n"
                f"Files:\n- Added: {', '.join(changes['added']) or 'None'}\n"
                f"- Modified: {', '.join(changes['modified']) or 'None'}\n"
                f"- Deleted: {', '.join(changes['deleted']) or 'None'}\n\n"
                "Changes:\n- Add the experiment runner.\n\n"
                "Features:\n- Add a safe runner.\n"
            )
            message_file = root / "message.txt"
            write_message(message_file, message)
            token = synthetic_github_token()
            write_hook(
                repo,
                "pre-commit",
                "#!/bin/sh\n"
                f"printf '%s\\n' 'GITHUB_TOKEN={token}' > experiments/run.py\n"
                "git add -- experiments/run.py\n",
            )
            before_remote = git(root, "--git-dir", str(remote), "rev-parse", "main").stdout.strip()

            with self.assertRaisesRegex(repo_publish.PublishError, "committed tree"):
                repo_publish.publish_repository(repo, message_file)

            self.assertEqual(
                before_remote,
                git(root, "--git-dir", str(remote), "rev-parse", "main").stdout.strip(),
            )

    def test_publish_blocks_commit_message_changed_by_hook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, remote = init_repository(root)
            write(repo, "experiments/run.py", "print('safe')\n")
            repo_publish.prepare_repository(repo)
            changes = repo_publish.collect_changes(repo)
            message = (
                "Add experiment runner\n\n"
                f"Files:\n- Added: {', '.join(changes['added']) or 'None'}\n"
                f"- Modified: {', '.join(changes['modified']) or 'None'}\n"
                f"- Deleted: {', '.join(changes['deleted']) or 'None'}\n\n"
                "Changes:\n- Add the experiment runner.\n\n"
                "Features:\n- Add a safe runner.\n"
            )
            message_file = root / "message.txt"
            write_message(message_file, message)
            write_hook(
                repo,
                "commit-msg",
                "#!/bin/sh\nprintf '\\n- Modified by hook\\n' >> \"$1\"\n",
            )
            before_remote = git(root, "--git-dir", str(remote), "rev-parse", "main").stdout.strip()

            with self.assertRaisesRegex(repo_publish.PublishError, "commit message differs"):
                repo_publish.publish_repository(repo, message_file)

            self.assertEqual(
                before_remote,
                git(root, "--git-dir", str(remote), "rev-parse", "main").stdout.strip(),
            )

    def test_tracked_temporary_file_is_removed_from_git_but_kept_locally(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, remote = init_repository(root)
            write(repo, "paper/main.aux", "temporary")
            write(repo, "AI_PLAN.md", "internal")
            git(repo, "add", "--", "paper/main.aux", "AI_PLAN.md")
            git(repo, "commit", "-m", "Track local artifacts by mistake")
            git(repo, "push", "origin", "main")
            repo_publish.prepare_repository(repo)
            changes = repo_publish.collect_changes(repo)
            message = (
                "Remove generated and planning artifacts\n\n"
                f"Files:\n- Added: {', '.join(changes['added']) or 'None'}\n"
                f"- Modified: {', '.join(changes['modified']) or 'None'}\n"
                f"- Deleted: {', '.join(changes['deleted']) or 'None'}\n\n"
                "Changes:\n- Removed generated LaTeX state and internal planning notes from Git.\n\n"
                "Features:\n- No functional change.\n"
            )
            message_file = root / "commit-message.txt"
            write_message(message_file, message)

            repo_publish.publish_repository(repo, message_file)

            remote_tree = set(
                git(root, "--git-dir", str(remote), "ls-tree", "-r", "--name-only", "main")
                .stdout.splitlines()
            )
            self.assertNotIn("paper/main.aux", remote_tree)
            self.assertNotIn("AI_PLAN.md", remote_tree)
            self.assertTrue((repo / "paper/main.aux").exists())
            self.assertTrue((repo / "AI_PLAN.md").exists())

    def test_secret_blocks_prepare_without_commit_or_push(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, remote = init_repository(Path(tmp))
            before_local = git(repo, "rev-parse", "HEAD").stdout.strip()
            before_remote = git(Path(tmp), "--git-dir", str(remote), "rev-parse", "main").stdout.strip()
            write(repo, ".env", f"GITHUB_TOKEN={synthetic_github_token()}\n")

            with self.assertRaises(repo_publish.PublishError):
                repo_publish.prepare_repository(repo)

            self.assertEqual(before_local, git(repo, "rev-parse", "HEAD").stdout.strip())
            self.assertEqual(
                before_remote,
                git(Path(tmp), "--git-dir", str(remote), "rev-parse", "main").stdout.strip(),
            )

    def test_publish_supports_an_empty_initialized_repository(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "worktree"
            remote = root / "remote.git"
            repo.mkdir()
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.name", "Skill Test")
            git(repo, "config", "user.email", "skill-test@example.invalid")
            git(root, "init", "--bare", str(remote))
            git(repo, "remote", "add", "origin", str(remote))
            write(repo, "README.md", "# Research\n\nA paper and reproducible experiment project.\n\nSee FILES.md.\n")
            write(repo, "paper/main.tex", "\\documentclass{article}\n")
            repo_publish.prepare_repository(repo)
            changes = repo_publish.collect_changes(repo)
            message = (
                "Publish initial research files\n\n"
                f"Files:\n- Added: {', '.join(changes['added']) or 'None'}\n"
                f"- Modified: {', '.join(changes['modified']) or 'None'}\n"
                f"- Deleted: {', '.join(changes['deleted']) or 'None'}\n\n"
                "Changes:\n- Add the initial paper sources and repository inventory.\n\n"
                "Features:\n- Provide the initial reproducible research project.\n"
            )
            message_file = root / "message.txt"
            write_message(message_file, message)

            report = repo_publish.publish_repository(repo, message_file)

            self.assertEqual("main", report["branch"])
            self.assertIn("README.md", git(root, "--git-dir", str(remote), "ls-tree", "-r", "--name-only", "main").stdout)

    def test_secret_added_after_prepare_is_caught_on_publish(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, remote = init_repository(root)
            write(repo, "experiments/run.py", "print('safe')\n")
            repo_publish.prepare_repository(repo)
            write(
                repo,
                "experiments/run.py",
                f'GITHUB_TOKEN = "{synthetic_github_token()}"\n',
            )
            message_file = root / "message.txt"
            write_message(
                message_file,
                "Add experiment runner\n\n"
                "Files:\n- Added: experiments/run.py\n- Modified: None\n- Deleted: None\n\n"
                "Changes:\n- Add the experiment entry point.\n\n"
                "Features:\n- Add a reproducible runner.\n",
            )
            before = git(repo, "rev-parse", "HEAD").stdout.strip()

            with self.assertRaises(repo_publish.PublishError):
                repo_publish.publish_repository(repo, message_file)

            self.assertEqual(before, git(repo, "rev-parse", "HEAD").stdout.strip())
            self.assertEqual(before, git(root, "--git-dir", str(remote), "rev-parse", "main").stdout.strip())

    def test_unpublished_history_with_deleted_secret_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "worktree"
            remote = root / "remote.git"
            repo.mkdir()
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.name", "Skill Test")
            git(repo, "config", "user.email", "skill-test@example.invalid")
            write(repo, "README.md", "# Research\n\nA paper and experiment project.\n\nSee FILES.md.\n")
            write(repo, "paper/main.tex", "\\documentclass{article}\n")
            write(repo, "config.py", f'GITHUB_TOKEN = "{synthetic_github_token()}"\n')
            git(repo, "add", "--", "README.md", "paper/main.tex", "config.py")
            git(repo, "commit", "-m", "Add initial project")
            (repo / "config.py").unlink()
            git(repo, "add", "-u", "--", "config.py")
            git(repo, "commit", "-m", "Remove local credential file")
            git(root, "init", "--bare", str(remote))
            git(repo, "remote", "add", "origin", str(remote))
            write(repo, "experiments/run.py", "print('safe')\n")

            with self.assertRaises(repo_publish.PublishError):
                repo_publish.prepare_repository(repo)

    def test_unpublished_history_with_secret_commit_message_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = init_repository(Path(tmp))
            write(repo, "experiments/run.py", "print('safe')\n")
            git(repo, "add", "--", "experiments/run.py")
            git(
                repo,
                "commit",
                "-m",
                f"Add runner {synthetic_github_token()}",
            )

            with self.assertRaisesRegex(repo_publish.PublishError, "commit message"):
                repo_publish.prepare_repository(repo)

    def test_unpublished_history_with_sanitized_notebook_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = init_repository(Path(tmp))
            notebook = {
                "cells": [
                    {
                        "cell_type": "code",
                        "execution_count": 1,
                        "metadata": {},
                        "outputs": [
                            {"name": "stdout", "output_type": "stream", "text": ["result\n"]}
                        ],
                        "source": ["print('result')\n"],
                    }
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
            notebook_path = write(repo, "notebooks/run.ipynb", json.dumps(notebook))
            git(repo, "add", "--", "notebooks/run.ipynb")
            git(repo, "commit", "-m", "Save an executed notebook")
            notebook["cells"][0]["execution_count"] = None
            notebook["cells"][0]["outputs"] = []
            notebook_path.write_text(json.dumps(notebook), encoding="utf-8")
            git(repo, "add", "--", "notebooks/run.ipynb")
            git(repo, "commit", "-m", "Clear notebook execution state")

            with self.assertRaisesRegex(repo_publish.PublishError, "historical notebook"):
                repo_publish.prepare_repository(repo)

    def test_unpublished_history_checks_shared_notebook_blob_by_tree_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = init_repository(Path(tmp))
            notebook = {
                "cells": [
                    {
                        "cell_type": "code",
                        "execution_count": 1,
                        "metadata": {},
                        "outputs": [
                            {"name": "stdout", "output_type": "stream", "text": ["result\n"]}
                        ],
                        "source": ["print('result')\n"],
                    }
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
            shared_content = json.dumps(notebook)
            write(repo, "aaa.txt", shared_content)
            notebook_path = write(repo, "notebooks/shared.ipynb", shared_content)
            git(repo, "add", "--", "aaa.txt", "notebooks/shared.ipynb")
            git(repo, "commit", "-m", "Add shared notebook payload")
            notebook_path.unlink()
            git(repo, "add", "-u", "--", "notebooks/shared.ipynb")
            git(repo, "commit", "-m", "Remove executed notebook path")
            outbound_objects = git(repo, "rev-list", "--objects", "origin/main..HEAD").stdout
            self.assertNotIn("notebooks/shared.ipynb", outbound_objects)

            with self.assertRaisesRegex(repo_publish.PublishError, "historical notebook"):
                repo_publish.prepare_repository(repo)

    def test_actual_remote_tip_defines_outbound_history_not_stale_tracking_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, _ = init_repository(root)
            write(repo, "config.py", f'GITHUB_TOKEN = "{synthetic_github_token()}"\n')
            git(repo, "add", "--", "config.py")
            git(repo, "commit", "-m", "Add local credential by mistake")
            secret_commit = git(repo, "rev-parse", "HEAD").stdout.strip()
            (repo / "config.py").unlink()
            git(repo, "add", "-u", "--", "config.py")
            git(repo, "commit", "-m", "Remove credential file")
            git(repo, "update-ref", "refs/remotes/origin/main", secret_commit)
            write(repo, "experiments/run.py", "print('safe')\n")

            with self.assertRaises(repo_publish.PublishError):
                repo_publish.prepare_repository(repo)

    def test_prepare_rejects_preexisting_staged_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = init_repository(Path(tmp))
            write(repo, "experiments/staged.py", "print('staged')\n")
            git(repo, "add", "--", "experiments/staged.py")
            with self.assertRaises(repo_publish.PublishError):
                repo_publish.prepare_repository(repo)

    def test_prepare_reports_gitlink_without_gitmodules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = init_repository(Path(tmp))
            head = git(repo, "rev-parse", "HEAD").stdout.strip()
            git(repo, "update-index", "--add", "--cacheinfo", "160000", head, "nested-repo")
            git(repo, "commit", "-m", "Add malformed nested repository link")

            with self.assertRaisesRegex(repo_publish.PublishError, r"Gitlink.*\.gitmodules"):
                repo_publish.prepare_repository(repo)

    def test_prepare_rejects_gitlink_even_with_a_valid_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = init_repository(Path(tmp))
            head = git(repo, "rev-parse", "HEAD").stdout.strip()
            git(repo, "update-index", "--add", "--cacheinfo", "160000", head, "nested-repo")
            write(
                repo,
                ".gitmodules",
                '[submodule "nested-repo"]\n\tpath = nested-repo\n'
                "\turl = https://example.invalid/nested-repo.git\n",
            )
            git(repo, "add", "--", ".gitmodules")
            git(repo, "commit", "-m", "Add mapped nested repository link")

            with self.assertRaisesRegex(repo_publish.PublishError, "Gitlink.*not publishable"):
                repo_publish.prepare_repository(repo)

    def test_prepare_reports_gitlink_with_a_mismatched_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = init_repository(Path(tmp))
            head = git(repo, "rev-parse", "HEAD").stdout.strip()
            git(repo, "update-index", "--add", "--cacheinfo", "160000", head, "nested-repo")
            write(
                repo,
                ".gitmodules",
                '[submodule "other"]\n\tpath = other\n'
                "\turl = https://example.invalid/other.git\n",
            )
            git(repo, "add", "--", ".gitmodules")
            git(repo, "commit", "-m", "Add mismatched nested repository metadata")

            with self.assertRaisesRegex(repo_publish.PublishError, "does not map"):
                repo_publish.prepare_repository(repo)

    def test_unpublished_history_with_removed_gitlink_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = init_repository(Path(tmp))
            head = git(repo, "rev-parse", "HEAD").stdout.strip()
            git(repo, "update-index", "--add", "--cacheinfo", "160000", head, "nested-repo")
            git(repo, "commit", "-m", "Add accidental nested repository link")
            git(repo, "rm", "--cached", "--", "nested-repo")
            git(repo, "commit", "-m", "Remove accidental nested repository link")

            with self.assertRaisesRegex(repo_publish.PublishError, "historical gitlink"):
                repo_publish.prepare_repository(repo)


if __name__ == "__main__":
    unittest.main()
