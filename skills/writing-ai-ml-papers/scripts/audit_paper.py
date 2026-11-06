#!/usr/bin/env python3
"""Audit AI and ML paper prose for author voice and optional hyphens."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import sys
from typing import Iterable


DEFAULT_ALLOWED_HYPHENS = {
    "k-means",
    "p-value",
    "top-k",
    "x-axis",
    "y-axis",
}

FIRST_PERSON_ACTION = re.compile(
    r"\bwe\s+(?:"
    r"acknowledge|address|aim|analy[sz]e|apply|assume|build|characterize|"
    r"collect|compare|compute|conduct|consider|construct|define|derive|design|"
    r"develop|discuss|establish|evaluate|examine|find|formulate|introduce|"
    r"investigate|leave|measure|observe|optimize|present|propose|provide|prove|"
    r"quantify|release|report|show|study|test|train|use|validate"
    r")\b",
    re.IGNORECASE,
)

IMPERSONAL_AUTHOR_ACTION = re.compile(
    r"\b(?:"
    r"(?:(?:this|our)\s+(?:paper|work|study)|"
    r"the\s+present\s+(?:paper|work|study))\s+"
    r"(?:aims|analy[sz]es|defines|derives|demonstrates|establishes|evaluates|"
    r"finds|introduces|investigates|observes|presents|proposes|proves|shows|studies)"
    r"|it\s+(?:is|can\s+be)\s+"
    r"(?:demonstrated|established|found|observed|proved|shown)"
    r"|the\s+experiments?\s+(?:are|were)\s+"
    r"(?:conducted|performed|run)"
    r")\b",
    re.IGNORECASE,
)

HYPHENATED_TOKEN = re.compile(
    r"(?<![A-Za-z0-9])(?:[A-Za-z0-9]+(?:\.[0-9]+)?)(?:-[A-Za-z0-9]+)+"
)

BLOCK_ENVIRONMENTS = (
    "align",
    "align*",
    "equation",
    "equation*",
    "gather",
    "gather*",
    "lstlisting",
    "math",
    "multline",
    "multline*",
    "thebibliography",
    "tikzpicture",
    "verbatim",
)


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    token: str
    line: int
    suggestion: str


@dataclass(frozen=True)
class AuditReport:
    findings: list[Finding]
    summary: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        return {
            "summary": self.summary,
            "findings": [asdict(finding) for finding in self.findings],
        }


def _preserve_newlines(match: re.Match[str]) -> str:
    return "\n" * match.group(0).count("\n")


def _strip_comments(source: str) -> str:
    return re.sub(r"(?<!\\)%[^\n]*", "", source)


def _keep_href_text_preserving_lines(match: re.Match[str]) -> str:
    display_text = re.sub(r"\s+", " ", match.group(1)).strip()
    prefix = "\n" * match.group(0).count("\n")
    return f"{prefix} {display_text} "


def _mask_nonprose(source: str) -> str:
    text = _strip_comments(source)

    for environment in BLOCK_ENVIRONMENTS:
        pattern = re.compile(
            rf"\\begin\{{{re.escape(environment)}\}}.*?"
            rf"\\end\{{{re.escape(environment)}\}}",
            re.DOTALL,
        )
        text = pattern.sub(_preserve_newlines, text)

    math_patterns = (
        re.compile(r"\$\$.*?\$\$", re.DOTALL),
        re.compile(r"\\\[.*?\\\]", re.DOTALL),
        re.compile(r"\\\(.*?\\\)", re.DOTALL),
        re.compile(r"(?<!\\)\$(?!\$).*?(?<!\\)\$", re.DOTALL),
    )
    for pattern in math_patterns:
        text = pattern.sub(_preserve_newlines, text)

    inline_verbatim = re.compile(
        r"\\(?:verb\*?|lstinline)(?:\[[^\]]*\])?"
        r"(?P<delimiter>[^\w\s]).*?(?P=delimiter)"
    )
    text = inline_verbatim.sub(_preserve_newlines, text)

    href_pattern = re.compile(
        r"\\href\s*\{[^{}]*\}\s*\{([^{}]*)\}"
    )
    text = href_pattern.sub(_keep_href_text_preserving_lines, text)

    ignored_commands = (
        "Cpageref",
        "Cref",
        "Autocite",
        "Parencite",
        "Textcite",
        "addbibresource",
        "affiliation",
        "author",
        "autocite",
        "autoref",
        "bibliography",
        "bibliographystyle",
        "cite",
        "citealp",
        "citeauthor",
        "citep",
        "citet",
        "cref",
        "crefrange",
        "email",
        "eqref",
        "footcite",
        "fullcite",
        "include",
        "includegraphics",
        "input",
        "institute",
        "label",
        "lstinputlisting",
        "orcidlink",
        "pageref",
        "parencite",
        "path",
        "ref",
        "smartcite",
        "supercite",
        "thanks",
        "textcite",
        "url",
    )
    ignored = "|".join(ignored_commands)
    ignored_pattern = re.compile(
        rf"\\(?:{ignored})\*?(?:\[[^\]]*\])*"
        rf"(?:\s*\{{[^{{}}]*\}})+",
    )
    text = ignored_pattern.sub(_preserve_newlines, text)

    text = re.sub(r"\\begin\{[^{}]+\}|\\end\{[^{}]+\}", " ", text)
    text = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])*", " ", text)
    text = text.replace("\\&", "&").replace("\\%", "%")
    text = text.replace("~", " ")
    text = text.replace("{", " ").replace("}", " ")
    return text


def extract_prose(source: str) -> str:
    """Return plain prose while omitting common LaTeX nonprose constructs."""
    return re.sub(r"\s+", " ", _mask_nonprose(source)).strip()


def _normalized_allowlist(extra: Iterable[str] | None) -> set[str]:
    allowed = {term.casefold() for term in DEFAULT_ALLOWED_HYPHENS}
    if extra:
        allowed.update(term.casefold() for term in extra)
    return allowed


def audit_text(
    source: str,
    *,
    allow_hyphens: Iterable[str] | None = None,
) -> AuditReport:
    """Audit source text and return actionable findings with line numbers."""
    masked = _mask_nonprose(source)
    allowed = _normalized_allowlist(allow_hyphens)
    findings: list[Finding] = []
    first_person_count = 0
    impersonal_count = 0
    optional_hyphen_count = 0

    for line_number, line in enumerate(masked.splitlines(), start=1):
        first_person_count += len(FIRST_PERSON_ACTION.findall(line))

        for match in IMPERSONAL_AUTHOR_ACTION.finditer(line):
            token = match.group(0)
            impersonal_count += 1
            findings.append(
                Finding(
                    code="impersonal_author_action",
                    message="Prefer first person for an action owned by the authors.",
                    token=token,
                    line=line_number,
                    suggestion="Rewrite with 'we' and an active verb.",
                )
            )

        for match in HYPHENATED_TOKEN.finditer(line):
            token = match.group(0)
            if token.casefold() in allowed:
                continue
            if re.fullmatch(r"\d+(?:\.\d+)?-\d+(?:\.\d+)?", token):
                continue
            optional_hyphen_count += 1
            findings.append(
                Finding(
                    code="optional_hyphen",
                    message="Review this hyphenated compound.",
                    token=token,
                    line=line_number,
                    suggestion="Rewrite as an open phrase, possessive, or clause when possible.",
                )
            )

    prose = extract_prose(source)
    word_count = len(re.findall(r"\b[A-Za-z0-9]+\b", prose))
    summary = {
        "lines": len(source.splitlines()),
        "words": word_count,
        "first_person_actions": first_person_count,
        "impersonal_author_actions": impersonal_count,
        "optional_hyphens": optional_hyphen_count,
        "actionable_findings": len(findings),
    }
    return AuditReport(findings=findings, summary=summary)


def _render_text(path: Path, report: AuditReport) -> str:
    lines = [
        f"Paper prose audit: {path}",
        f"Words: {report.summary['words']}",
        f"First person author actions: {report.summary['first_person_actions']}",
        f"Impersonal author actions: {report.summary['impersonal_author_actions']}",
        f"Optional hyphenated compounds: {report.summary['optional_hyphens']}",
    ]
    if not report.findings:
        lines.append("No actionable findings.")
        return "\n".join(lines)

    lines.append("Findings:")
    for finding in report.findings:
        token = f" [{finding.token}]" if finding.token else ""
        lines.append(
            f"  line {finding.line}: {finding.code}{token}: "
            f"{finding.suggestion}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit LaTeX prose for first person author voice and optional hyphens."
    )
    parser.add_argument("paper", type=Path, help="Path to a UTF-8 text or LaTeX file")
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return exit code 1 when actionable findings exist",
    )
    parser.add_argument(
        "--allow-hyphen",
        action="append",
        default=[],
        metavar="TERM",
        help="Allow one additional hyphenated term; repeat as needed",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        source = args.paper.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        print(f"error: cannot read {args.paper}: {error}", file=sys.stderr)
        return 2

    report = audit_text(source, allow_hyphens=args.allow_hyphen)
    if args.format == "json":
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(_render_text(args.paper, report))

    if args.strict and report.findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
