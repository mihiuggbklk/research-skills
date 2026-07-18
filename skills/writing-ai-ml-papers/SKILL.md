---
name: writing-ai-ml-papers
description: Use when an English AI or ML manuscript, outline, abstract, introduction, theory section, experiment section, conclusion, or LaTeX draft needs to be written, rewritten, or audited; especially when author voice, argument structure, evidence grounding, or excessive hyphenated compounds are concerns.
---

# Writing AI and ML Papers

## Core Principle

Build the paper as a chain from question to claim to evidence. Prefer direct first person author actions and remove optional hyphenated compounds without weakening technical precision.

## Load the Right References

- Read [references/article-patterns.md](references/article-patterns.md) before planning a paper, organizing a theory narrative, or adapting the structure of Li et al. (2025).
- Read [references/section-playbook.md](references/section-playbook.md) before drafting or revising a specific section.
- Read [references/style-rules.md](references/style-rules.md) before line editing, polishing, or applying the first person and hyphen constraints.
- Run `python scripts/audit_paper.py PAPER.tex --strict` after revising prose. Use `--format json` for machine readable output and repeat `--allow-hyphen TERM` only for a justified exception.

## Establish the Evidence Boundary

Inspect all supplied notes, source files, result tables, figures, logs, proofs, and bibliography entries before drafting. Build a compact evidence ledger with four fields:

| Claim | Exact support | Allowed scope | Missing evidence |
|---|---|---|---|
| What the paper may say | File, theorem, table, or user statement | Dataset, model, metric, and conditions | Experiment, proof, statistic, or citation still needed |

Do not invent results, assumptions, comparisons, novelty, significance, citations, or causal explanations. Mark unsupported material as `[EVIDENCE NEEDED]`, `[CITATION NEEDED]`, or `[AUTHOR DECISION NEEDED]`. Fetch and verify citations when tools and sources are available; never create plausible BibTeX from memory.

## Choose the Paper Route

| Available evidence | Route | Main result unit |
|---|---|---|
| Definitions, assumptions, lemmas, theorems, proofs | Theoretical | Formal guarantee plus interpretation |
| Models, datasets, metrics, runs, tables, ablations | Empirical | Measured claim plus uncertainty and scope |
| Both formal and measured evidence | Hybrid | Theory prediction followed by targeted validation |

Do not force a theorem shaped narrative onto empirical evidence or describe an observed trend as proof.

## Build the Claim Spine

Before writing full prose, state:

1. The concrete problem.
2. The unresolved question or precise limitation of prior work.
3. The paper's answer in one sentence.
4. Two to four contribution claims, ordered by dependency.
5. The evidence supporting each claim.
6. The boundary beyond which each claim does not extend.

Reject contribution lists that merely name components, datasets, or sections. Make every contribution state what we establish and why it matters.

## Draft in Dependency Order

Draft the argument before optimizing the opening. Use this order unless the user requests another:

1. Write the setup and evidence bearing sections.
2. Write the main results and their interpretations.
3. Write the mechanism, proof overview, ablations, or error analysis.
4. Write related work around the exact gap.
5. Write the introduction from the completed claim spine.
6. Write the abstract last.
7. Write the conclusion and limitations from the final supported claims.

For each result, use the sequence `question -> setup -> result -> interpretation -> boundary`. For each theorem, state assumptions and guarantees before discussing intuition. For each experiment, name the claim it tests and distinguish observation from explanation.

## Enforce Author Voice

Use `we` for actions owned by the authors:

- `we study`, `we consider`, `we define`
- `we introduce`, `we propose`, `we develop`
- `we prove`, `we establish`, `we derive`, `we show`
- `we evaluate`, `we compare`, `we observe`, `we find`
- `we discuss`, `we acknowledge`, `we leave`

Prefer `We prove that...` over `It is proved that...` and `We introduce...` over `This paper introduces...`. Keep scientific entities as subjects when they genuinely perform the action, as in `The bound decreases with the sample size` or `The model attends to relevant tokens`. Do not insert `we` into every sentence.

## Minimize Hyphenated Compounds

Rewrite optional `word-word` constructions as open phrases, possessives, or clauses:

- `multi-step reasoning` -> `reasoning with multiple steps`
- `one-layer Transformer` -> `Transformer with one layer`
- `in-distribution accuracy` -> `accuracy on the training distribution`
- `task-specific module` -> `module specific to each task`
- `2.8-point gain` -> `gain of 2.8 percentage points`
- `state-of-the-art methods` -> `the strongest prior methods`

Preserve a hyphen only when removing it would damage a conventional technical name, mathematical object, citation key, URL, command flag, or venue template. Treat every exception as deliberate, not automatic.

## Revise in Four Passes

1. **Grounding:** Match every number, comparison, theorem condition, and citation to the evidence ledger.
2. **Logic:** Check that each paragraph has one role and that each conclusion follows from the stated evidence.
3. **Reader guidance:** Add local roadmaps, result interpretations, and transitions only where they clarify dependency.
4. **Language:** Prefer first person author actions, remove optional hyphenated compounds, shorten overloaded sentences, and stabilize terminology.

## Completion Contract

Before delivery:

- Run the prose auditor on every changed `.tex` file.
- Search for placeholders and report each unresolved item.
- Verify that experiments support rather than overstate the claims.
- Verify that theorem interpretations preserve all conditions and quantifiers.
- Verify every citation against an external record and the cited claim when citation tools are available.
- Compile the LaTeX project when compilation is in scope.
- Report what changed, what was verified, and what evidence remains missing.

Never claim that a paper is submission ready based on prose quality alone.
