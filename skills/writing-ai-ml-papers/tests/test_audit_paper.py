import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from audit_paper import audit_text, extract_prose  # noqa: E402


class ExtractProseTests(unittest.TestCase):
    def test_ignores_comments_math_citations_and_urls_but_keeps_prose(self):
        source = r"""
We show that the error decreases \citep{smith2024}.
\url{https://example.com/state-of-the-art}
% hidden multi-step comment
The error is $x-y$, and the decrease is \emph{strict}.
"""

        prose = extract_prose(source)

        self.assertIn("We show that the error decreases", prose)
        self.assertIn("The error is", prose)
        self.assertIn("strict", prose)
        self.assertNotIn("smith2024", prose)
        self.assertNotIn("state-of-the-art", prose)
        self.assertNotIn("multi-step", prose)
        self.assertNotIn("x-y", prose)

    def test_ignores_includes_cross_references_verbatim_and_author_metadata(self):
        source = r"""
\input{related-work}
\include{appendix-long-form}
See \cref{sec:multi-step} and \autoref{fig:one-layer}.
See \crefrange{sec:setup}{sec:related-work}.
Prior evidence \parencite{smith-et-al-2024} supports the premise.
\verb|state-of-the-art| and \lstinline|task-specific|
\author{Jean-Pierre Dupont}
We study reasoning with multiple steps.
"""

        prose = extract_prose(source)

        self.assertIn("We study reasoning with multiple steps", prose)
        self.assertNotIn("related-work", prose)
        self.assertNotIn("appendix-long-form", prose)
        self.assertNotIn("multi-step", prose)
        self.assertNotIn("one-layer", prose)
        self.assertNotIn("state-of-the-art", prose)
        self.assertNotIn("task-specific", prose)
        self.assertNotIn("Jean-Pierre", prose)
        self.assertNotIn("smith-et-al-2024", prose)

    def test_preserves_following_line_number_after_multiline_href(self):
        source = (
            "\\href{\nhttps://example.com/resource\n}{supporting material}\n"
            "This paper presents a multi-step method."
        )
        expected_line = source[: source.index("This paper")].count("\n") + 1

        report = audit_text(source)
        relevant = [
            finding
            for finding in report.findings
            if finding.code in {"impersonal_author_action", "optional_hyphen"}
        ]

        self.assertTrue(relevant)
        self.assertEqual({expected_line}, {finding.line for finding in relevant})


class AuditTextTests(unittest.TestCase):
    def test_counts_first_person_author_actions(self):
        report = audit_text(
            "We study visual reasoning. We prove the main result. "
            "We observe the predicted trend."
        )

        self.assertEqual(report.summary["first_person_actions"], 3)
        self.assertNotIn(
            "missing_first_person",
            {finding.code for finding in report.findings},
        )

    def test_counts_common_theory_and_scope_actions(self):
        report = audit_text(
            "We aim to explain the mechanism. We characterize the bound. "
            "We quantify the sample requirement. We train the model. "
            "We test the prediction. We use five seeds."
        )

        self.assertEqual(report.summary["first_person_actions"], 6)
        self.assertNotIn(
            "missing_first_person",
            {finding.code for finding in report.findings},
        )

    def test_flags_impersonal_author_actions_and_optional_hyphens(self):
        report = audit_text(
            "This paper presents a multi-step method. "
            "Our work shows an inverse-quadratic trend."
        )
        findings = {(finding.code, finding.token) for finding in report.findings}

        self.assertIn(("impersonal_author_action", "This paper presents"), findings)
        self.assertIn(("impersonal_author_action", "Our work shows"), findings)
        self.assertIn(("optional_hyphen", "multi-step"), findings)
        self.assertIn(("optional_hyphen", "inverse-quadratic"), findings)

    def test_flags_passive_or_expletive_author_actions(self):
        report = audit_text(
            "It is shown that the estimator converges. "
            "It can be observed that the error decreases. "
            "The experiments are conducted on three datasets."
        )
        tokens = {
            finding.token.casefold()
            for finding in report.findings
            if finding.code == "impersonal_author_action"
        }

        self.assertEqual(
            {
                "it is shown",
                "it can be observed",
                "the experiments are conducted",
            },
            tokens,
        )

    def test_does_not_treat_a_cited_study_as_the_current_authors(self):
        report = audit_text(
            "The study shows that accuracy increases with context length."
        )

        self.assertNotIn(
            "impersonal_author_action",
            {finding.code for finding in report.findings},
        )

    def test_does_not_flag_minimal_conventional_allowlist(self):
        report = audit_text(
            "We report the p-value on the x-axis for k-means clustering."
        )

        self.assertEqual(
            [],
            [finding for finding in report.findings if finding.code == "optional_hyphen"],
        )

    def test_accepts_additional_allowed_hyphenated_terms(self):
        report = audit_text(
            "We compare a state-of-the-art baseline.",
            allow_hyphens={"state-of-the-art"},
        )

        self.assertEqual(
            [],
            [finding for finding in report.findings if finding.code == "optional_hyphen"],
        )

    def test_does_not_require_first_person_when_no_author_action_appears(self):
        report = audit_text(
            "Accuracy increases with context length on the benchmark. "
            "The bound decreases as the sample size grows."
        )

        self.assertNotIn(
            "missing_first_person",
            {finding.code for finding in report.findings},
        )

    def test_preserves_line_numbers_after_multiline_citation(self):
        source = "\\citep{\nsmith2024\n}\nThis paper presents a multi-step method."

        report = audit_text(source)
        relevant = [
            finding
            for finding in report.findings
            if finding.code in {"impersonal_author_action", "optional_hyphen"}
        ]

        self.assertTrue(relevant)
        self.assertEqual({4}, {finding.line for finding in relevant})


class CommandLineTests(unittest.TestCase):
    def run_audit(self, source, *args):
        script = SCRIPT_DIR / "audit_paper.py"
        with tempfile.TemporaryDirectory() as directory:
            paper = Path(directory) / "paper.tex"
            paper.write_text(source, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(script), str(paper), *args],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_strict_mode_fails_for_actionable_findings(self):
        result = self.run_audit(
            "This paper presents a multi-step method.",
            "--strict",
            "--format",
            "json",
        )

        self.assertEqual(1, result.returncode)
        payload = json.loads(result.stdout)
        self.assertGreater(payload["summary"]["actionable_findings"], 0)

    def test_strict_mode_passes_for_clean_first_person_prose(self):
        result = self.run_audit(
            "We study multistep reasoning. We prove the main result.",
            "--strict",
            "--format",
            "json",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(0, payload["summary"]["actionable_findings"])

    def test_strict_mode_fails_for_passive_author_action(self):
        result = self.run_audit(
            "It is shown that the estimator converges.",
            "--strict",
            "--format",
            "json",
        )

        self.assertEqual(1, result.returncode)
        payload = json.loads(result.stdout)
        self.assertEqual(1, payload["summary"]["impersonal_author_actions"])


if __name__ == "__main__":
    unittest.main()
