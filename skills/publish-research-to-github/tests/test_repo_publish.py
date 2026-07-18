from __future__ import annotations

import importlib.util
import os
import subprocess
import tempfile
import unittest
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
            }
            for relative, category in expected.items():
                write(root, relative)
                decision = repo_publish.classify_path(root, relative, tracked=False)
                self.assertEqual("include", decision.action, relative)
                self.assertEqual(category, decision.category, relative)

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
            token = "gh" + "p_abcdefghijklmnopqrstuvwxyz123456"
            path = write(root, "experiments/config.py", f'GITHUB_TOKEN = "{token}"\n')
            finding = repo_publish.scan_secret(path)
            self.assertIsNotNone(finding)
            self.assertNotIn(token, finding or "")

    def test_detects_secret_near_end_of_large_publishable_text_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            token = "gh" + "p_abcdefghijklmnopqrstuvwxyz123456"
            path = write(root, "experiments/large.py", ("# padding\n" * 300_000) + f'TOKEN = "{token}"\n')
            finding = repo_publish.scan_secret(path, max_bytes=50 * 1024 * 1024)
            self.assertIsNotNone(finding)
            self.assertNotIn(token, finding or "")

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
                    "Features:\n- TOKEN=" + "gh" + "p_abcdefghijklmnopqrstuvwxyz123456",
                ),
                changes,
            )


class RepositoryIntegrationTests(unittest.TestCase):
    def test_prepare_generates_manifest_without_staging_or_committing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = init_repository(Path(tmp))
            write(repo, "paper/main.pdf", "%PDF-test")
            write(repo, "figures/overview.png", "image")
            write(repo, "experiments/train.py", "print('train')\n")
            write(repo, "paper/main.aux", "temporary")
            write(repo, "AI_PLAN.md", "internal plan")
            before = git(repo, "rev-parse", "HEAD").stdout.strip()

            report = repo_publish.prepare_repository(repo)

            self.assertEqual(before, git(repo, "rev-parse", "HEAD").stdout.strip())
            self.assertEqual("", git(repo, "diff", "--cached", "--name-only").stdout)
            manifest = (repo / "FILES.md").read_text(encoding="utf-8")
            self.assertIn("paper/main.pdf", manifest)
            self.assertIn("experiments/train.py", manifest)
            self.assertNotIn("main.aux", manifest)
            self.assertNotIn("AI_PLAN.md", manifest)
            self.assertIn("paper/main.aux", {item["path"] for item in report["excluded"]})

    def test_publish_stages_exact_files_commits_and_pushes_to_local_remote(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, remote = init_repository(root)
            write(repo, "README.md", "# Reproducible Research\n\nPaper and experiment runner.\n\nSee [FILES.md](FILES.md).\n")
            write(repo, "paper/main.pdf", "%PDF-test")
            write(repo, "figures/new.png", "image")
            write(repo, "experiments/run.py", "print('run')\n")
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
            message_file.write_text(message, encoding="utf-8")

            report = repo_publish.publish_repository(repo, message_file)

            remote_tree = set(
                git(root, "--git-dir", str(remote), "ls-tree", "-r", "--name-only", "main")
                .stdout.splitlines()
            )
            self.assertIn("paper/main.pdf", remote_tree)
            self.assertIn("figures/new.png", remote_tree)
            self.assertIn("experiments/run.py", remote_tree)
            self.assertIn("FILES.md", remote_tree)
            self.assertNotIn("paper/main.aux", remote_tree)
            self.assertNotIn("TODO.md", remote_tree)
            self.assertEqual(git(repo, "rev-parse", "HEAD").stdout.strip(), report["commit"])
            self.assertEqual("main", report["branch"])
            committed_message = git(repo, "log", "-1", "--format=%B").stdout
            self.assertIn("Files:", committed_message)
            self.assertIn("Features:", committed_message)

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
            message_file.write_text(message, encoding="utf-8")

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
            write(repo, ".env", "GITHUB_TOKEN=" + "gh" + "p_abcdefghijklmnopqrstuvwxyz123456\n")

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
            message_file.write_text(message, encoding="utf-8")

            report = repo_publish.publish_repository(repo, message_file)

            self.assertEqual("main", report["branch"])
            self.assertIn("README.md", git(root, "--git-dir", str(remote), "ls-tree", "-r", "--name-only", "main").stdout)

    def test_secret_added_after_prepare_is_caught_on_publish(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, remote = init_repository(root)
            write(repo, "experiments/run.py", "print('safe')\n")
            repo_publish.prepare_repository(repo)
            write(repo, "experiments/run.py", 'GITHUB_TOKEN = "' + "gh" + 'p_abcdefghijklmnopqrstuvwxyz123456"\n')
            message_file = root / "message.txt"
            message_file.write_text(
                "Add experiment runner\n\n"
                "Files:\n- Added: experiments/run.py\n- Modified: None\n- Deleted: None\n\n"
                "Changes:\n- Add the experiment entry point.\n\n"
                "Features:\n- Add a reproducible runner.\n",
                encoding="utf-8",
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
            write(repo, "config.py", 'GITHUB_TOKEN = "' + "gh" + 'p_abcdefghijklmnopqrstuvwxyz123456"\n')
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

    def test_actual_remote_tip_defines_outbound_history_not_stale_tracking_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, _ = init_repository(root)
            write(repo, "config.py", 'GITHUB_TOKEN = "' + "gh" + 'p_abcdefghijklmnopqrstuvwxyz123456"\n')
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


if __name__ == "__main__":
    unittest.main()
