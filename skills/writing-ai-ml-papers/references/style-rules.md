# Style and Grounding Rules

## First Person Author Voice

Use `we` when the authors choose, construct, analyze, establish, observe, or interpret something.

| Avoid | Prefer |
|---|---|
| This paper studies... | We study... |
| This work introduces... | We introduce... |
| It is shown that... | We show that... |
| The experiments are conducted on... | We evaluate on... |
| It can be observed that... | We observe that... |
| The study aims to explain... | We aim to explain... |

Do not force first person onto facts outside author control. Prefer `Accuracy increases with context length` over `We increase accuracy` unless the authors caused and measured that change.

## Hyphen Rewrite Guide

Treat optional hyphenated compounds as revision candidates, including conventional academic habits.

| Avoid when possible | Rewrite |
|---|---|
| multi-step | with multiple steps |
| one-layer | with one layer |
| single-head | with one attention head |
| in-distribution | on the training distribution |
| out-of-distribution | under distribution shift |
| task-specific | specific to each task |
| step-wise | at each step |
| end-to-end | jointly; from input to output |
| state-of-the-art | strongest prior; current best |
| sample-efficient | uses fewer samples |
| 2.8-point gain | gain of 2.8 percentage points |
| zero-shot | without demonstrations |
| few-shot | with a few examples |

Keep conventional forms only when a precise name would otherwise become ambiguous, such as `p-value`, `x-axis`, `y-axis`, `k-means`, or `top-k`. Preserve citation keys, URLs, LaTeX commands, command flags, and mathematical minus signs. Add project specific exceptions to the auditor with `--allow-hyphen` only after reviewing each term.

## Claim Verbs

Match the verb to the evidence:

| Evidence | Appropriate verbs | Avoid |
|---|---|---|
| Complete proof | prove, establish, derive | suggest |
| Bound under assumptions | characterize, guarantee under | solve generally |
| Controlled measurements | find, observe, report | prove |
| Trend matching theory | support, agree with, are consistent with | verify the theorem |
| Ablation | indicate contribution, support importance | prove necessity |
| Qualitative examples | illustrate | demonstrate general superiority |

## Paragraph Structure

Give each paragraph one main role. Start with the role, place evidence in the middle, and end with the consequence or boundary. Keep old information near the start and new information near the end. Put the subject close to its verb. Split a sentence when notation, conditions, result, and interpretation compete for attention.

## Proof Prose

Use first person for proof actions and author choices: `We condition on...`, `We apply Lemma 2...`, and `We now combine the bounds...`. Use mathematical objects as subjects for mathematical facts: `The matrix is invertible on $\mathcal G$` and `The recursion contracts in this regime`. Announce the subgoal before a dense equation block and state its consequence afterward.

Do not use `clearly`, `obviously`, `similarly`, `by standard arguments`, or `it is easy to see` to hide a nontrivial step. Expand the step or cite the exact earlier lemma that supplies it. Preserve mathematical notation even when the prose rule prefers to avoid hyphenated compounds. See [appendix-proofs.md](appendix-proofs.md) for proof integrity, event, limit, and closure checks.

## Terminology

Choose one term for each concept and preserve it across prose, equations, figures, and tables. Do not alternate among `example`, `demonstration`, and `context item` unless they denote different objects. Define every acronym once and use it only when repeated often enough to help.

## Numbers and Comparisons

- Report the metric, direction, uncertainty definition, and number of runs.
- Compare methods only under matched conditions, or state the mismatch.
- Use `percentage points` for differences between percentages.
- Distinguish absolute and relative changes.
- Do not use `significant` without a statistical or clearly stated practical meaning.
- Do not hide a worse result or failed condition that changes the conclusion.

## Citations

Verify the paper identity, metadata, and attributed claim. Cite primary sources when possible. If verification is unavailable, use `[CITATION NEEDED]`; do not invent a key or BibTeX entry. Use citations to support prior work claims, not to outsource the paper's reasoning.

## LaTeX

Preserve commands, labels, references, citations, and math while editing prose. Do not rewrite notation solely to satisfy the prose hyphen rule. Keep sentence punctuation correct around display equations. Compile after structural edits when a complete LaTeX project is available.

## One Revision Example

Before:

> This paper presents a one-layer model for multi-step reasoning. It is shown that the model achieves state-of-the-art in-distribution accuracy, and a 2.8-point gain is observed.

After:

> We present a model with one layer for reasoning with multiple steps. We show that it achieves the highest accuracy among the evaluated methods on the training distribution, where we observe a gain of 2.8 percentage points.

The revision improves author voice and removes optional hyphenated compounds. It still requires evidence for `highest accuracy`, the comparison set, and the reported gain.
