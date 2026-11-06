from pathlib import Path
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]


class AppendixProofReferenceTests(unittest.TestCase):
    def test_main_skill_routes_appendix_proof_tasks(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("references/appendix-proofs.md", skill)
        self.assertIn("appendix proof", skill.casefold())

    def test_appendix_reference_contains_required_gates_and_ledgers(self):
        reference = (
            SKILL_DIR / "references" / "appendix-proofs.md"
        ).read_text(encoding="utf-8")

        required_headings = (
            "## Proof Integrity Gate",
            "## Choose the Proof Mode",
            "## Build the Dependency Map",
            "## Maintain a Probability Event Ledger",
            "## Maintain an Asymptotic Ledger",
            "## Close the Proof",
            "## Completion Checklist",
        )
        for heading in required_headings:
            with self.subTest(heading=heading):
                self.assertIn(heading, reference)

    def test_appendix_reference_records_all_four_source_patterns(self):
        reference = (
            SKILL_DIR / "references" / "appendix-proofs.md"
        ).read_text(encoding="utf-8")

        for source in ("Wu et al.", "Takanami and Pehlevan", "Shamir", "Li et al."):
            with self.subTest(source=source):
                self.assertIn(source, reference)

    def test_appendix_reference_preserves_derived_proof_behaviors(self):
        reference = (
            SKILL_DIR / "references" / "appendix-proofs.md"
        ).read_text(encoding="utf-8").casefold()

        required_patterns = (
            "master recursion",
            "coarse bound",
            "heuristic approximation",
            "select the admissible branch",
            "localization",
            "measurable selection",
            "positive margin",
            "mutually exclusive and exhaustive",
        )
        for pattern in required_patterns:
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, reference)

    def test_section_and_style_references_integrate_appendix_proofs(self):
        section_playbook = (
            SKILL_DIR / "references" / "section-playbook.md"
        ).read_text(encoding="utf-8")
        style_rules = (
            SKILL_DIR / "references" / "style-rules.md"
        ).read_text(encoding="utf-8")

        self.assertIn("## Appendix Proofs", section_playbook)
        self.assertIn("appendix-proofs.md", section_playbook)
        self.assertIn("## Proof Prose", style_rules)


if __name__ == "__main__":
    unittest.main()
