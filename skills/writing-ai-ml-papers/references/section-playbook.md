# Section Playbook

Read only the entries relevant to the requested section.

## Title

Name the studied object and the main result or setting. Prefer a literal title over a slogan. Avoid claiming superiority or generality that the evidence does not establish.

## Abstract

Give each sentence one job:

1. State the concrete problem or observed capability.
2. State the precise missing understanding or limitation.
3. Say what we introduce, analyze, or prove.
4. State the strongest supported result with conditions.
5. State the comparison, robustness result, or broader implication.
6. Mention experiments only if they validate a central prediction.

Use first person for contributions. Do not open with a sentence that could introduce any AI paper. Do not include citations unless the venue expects them.

## Introduction

Use this paragraph sequence:

1. **Phenomenon and importance:** Define the specific capability and why it matters.
2. **Closest work:** Organize prior work into the few lines needed to expose the gap.
3. **Unresolved question:** State exactly what prior results do not explain.
4. **Our answer:** Summarize the model, analysis, or method and its main guarantee.
5. **Contributions:** Give two to four claim based contributions in dependency order.
6. **Scope:** Name the main simplifying assumptions without apologetic language.

Use `we` in the answer and contribution paragraphs. Avoid a chronological bibliography tour.

## Related Work

Group papers by the role they play in the argument, such as expressivity, optimization, generalization, or empirical capability. For each group, state what it establishes and what remains outside its scope. End each group by connecting it to the paper's exact distinction. Verify every citation and attributed claim.

## Problem Formulation

Define in dependency order:

1. Data and task.
2. Model and parameters.
3. Training input, objective, and algorithm.
4. Test input and inference procedure.
5. Evaluation metric and success criterion.

Use a running interpretation after dense definitions. State simplifying assumptions where they first matter. Do not hide a result inside the setup.

## Main Theoretical Results

Open with a roadmap and a short list of main insights. For every theorem:

1. State all conditions.
2. State the guarantee and probability.
3. Interpret the controlling quantities.
4. Give a sanity check or limiting case.
5. State what the theorem does not imply.

Use `we prove`, `we establish`, or `we characterize`. Preserve quantifiers when paraphrasing. If a comparison depends on a condition, present both the satisfied and failed cases.

## Mechanism and Proof Overview

Name the technical obstacle first. Describe the proof as a small number of conceptual stages, not a list of algebraic operations. State what each lemma establishes and how it enables the next result. Distinguish proof intuition from proof content. Point detailed derivations to the appendix only after the logical route is complete.

## Appendix Proofs

Read [appendix-proofs.md](appendix-proofs.md) before drafting or revising a proof appendix. Check first that the exact claim is provable as stated, and never repair a missing definition or assumption silently. Keep a direct proof concise. For a long proof, align the appendix with the main text overview, expose the dependency map, name probability events, record the order and mode of every limit, and end with an explicit synthesis that recovers the original statement.

## Experiments

Read [experiment-writing.md](experiment-writing.md) before drafting or revising this section. Use one claim question per experiment block:

1. `We ask whether...`
2. State only the protocol needed to judge scope and fairness.
3. Report the dominant trend with an aggregate, range, coverage count, or representative contrast.
4. Interpret what the result supports without turning observation into explanation.
5. State a boundary, alternative explanation, or missing test when relevant.

Report the data split, metric, matched baseline conditions, number of runs, and uncertainty definition once. Include compute only when it affects fairness or interpretation. Let tables and figures carry complete values; do not read them aloud in prose or repeat every standard deviation. Route exhaustive values to tables or figures, and route only semantic implementation details or extended interpretation to the appendix or supplementary material.

Do not split one variant or sensitivity family into multiple short paragraphs merely to enumerate its rows; separate blocks must answer distinct claim questions.

Never infer significance without a valid test. Treat an ablation as evidence about contribution, not proof of a unique causal mechanism. Keep contradictions and boundary cases visible. Remove all local paths, filenames, scripts, configuration names, run IDs, hashes, and internal stage labels from every reader facing artifact, including captions, tables, appendices, supplements, and rebuttals.

## Figures and Tables

Make captions self contained: define the setting, metric, direction, uncertainty, and takeaway. Use the same name for every method and quantity throughout the paper. Put the claim in the surrounding prose, not only in the caption.

## Conclusion and Limitations

Restate only supported claims. Use first person to summarize what we establish. Name concrete limitations in model class, data assumptions, evaluation scope, compute, or proof technique. Explain how each limitation narrows interpretation. Propose future work that relaxes a specific limitation rather than offering a generic wish list.

## Final Cross Section Check

- Make the abstract, introduction, results, and conclusion express the same claim hierarchy.
- Introduce every symbol and acronym before use.
- Give every contribution a corresponding result section and evidence item.
- Give every main table or theorem an explicit interpretation in the prose.
- Keep claims no broader than the evaluated models, data, metrics, and assumptions.
