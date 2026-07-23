# Concise Experiment Writing

Use this reference for experiment, evaluation, results, ablation, robustness,
efficiency, and qualitative sections. The main paper should explain the
evidence, while tables, figures, and appendices preserve the complete record.

## Contents

- Core rule
- Experiment block
- Detail placement
- Common experiment types
- Internal artifact boundary
- Compression example
- Revision pass
- Final checks

## Core Rule

Write the experiment section as a selective argument, not as a result log.
Each paragraph should help the reader answer a claim question. Do not narrate
every table cell, seed, dataset value, hyperparameter, or implementation step.

Use exact numbers where they carry the claim. Otherwise summarize with an
average, range, coverage count, trend, or representative comparison. In a
normal claim block, use one aggregate and at most two representative numerical
contrasts. A third exact contrast is reserved for a genuine contradiction or
boundary case; it is not a license to enumerate the remaining rows. If a claim
has several distinct regimes, give one representative case per regime and
summarize the rest with coverage or a figure.

Do not split one ablation or sensitivity family into several two-row paragraphs
just to bypass this limit. Separate paragraphs are justified only when they
answer genuinely different claim questions; the remaining variants still
belong in a table or figure, including one placed in the appendix.

Set the claim questions and any scientifically meaningful regimes before
writing the section. Across the whole experiment section, do not create a new
claim block, regime, or variant family merely to expose another row or cell.
Regimes must be defined by the hypothesis or protocol before inspecting the
results; a dataset, seed, or variant label is not a new regime by itself. The
number of prose blocks must not grow with the number of table rows.

## Experiment Block

Build each block in this order:

1. **Question:** State the claim or prediction being tested.
2. **Protocol:** Give only the conditions needed to judge the comparison.
3. **Result:** Report the main trend and the minimum decisive evidence.
4. **Interpretation:** Say what the result supports and why it matters.
5. **Boundary:** Name the relevant exception, uncertainty, or scope limit.

The order matters more than using these labels. A short block may combine the
question and protocol or the interpretation and boundary in one sentence.

Do not begin a paragraph with a list of models, datasets, or settings unless
the list itself defines the claim. Prefer `We ask whether...`, `Across the four
datasets...`, or `Under matched compute...` to a procedural chronology.

## Detail Placement

Use the following division of labor:

| Location | Put here | Keep out |
|---|---|---|
| Main prose | Claim, matched comparison, main trend, representative evidence, interpretation, boundary | Full grids, every standard deviation, exhaustive settings, procedural history |
| Table or figure | Complete values needed for comparison, uncertainty notation, visual trends | Paragraph length interpretation |
| Caption | Setting, metric direction, uncertainty definition, one sentence takeaway | A second results discussion |
| Appendix or supplement | Reproducibility details, extended results, secondary baselines, full hyperparameters in tables or figures | Internal filesystem or job metadata, cell by cell prose |

Report the evaluated scope, metric, data split, matched baseline conditions,
number of runs, and uncertainty definition once where readers can find them.
Repeat a detail only when it changes the validity of a later comparison.

When a table contains the complete result grid:

- Summarize the dominant trend instead of reading rows aloud.
- Identify the strongest relevant baseline, not every baseline in sequence.
- Give one representative case or the largest meaningful exception.
- Use an aggregate, range, or coverage statement when it preserves the claim.
- Refer readers to the table for complete values.

Do not move a cell by cell results paragraph into the appendix or supplement.
Exhaustive values belong in tables or figures; reader facing prose in those
sections must still summarize trends and interpret the evidence.

Do not compress away a result that contradicts the claimed trend. State the
exception and narrow the claim. Do not claim statistical significance without
a valid test. Report uncertainty compactly in the setup, caption, or table
rather than repeating every deviation in prose.

## Common Experiment Types

### Main Results

Answer whether the proposed method improves the target metric under matched
conditions. State the overall trend, compare against the strongest relevant
baseline, and use one representative result or a compact aggregate. Mention a
dataset separately only when it is central, exceptional, or explains scope.

### Ablations

Organize ablations around component questions, not a tour of all variants.
Compare the full method with the one or two removals most diagnostic of the
claim, then summarize the remaining pattern. An ablation supports a component's
contribution under the tested intervention; it does not prove a unique causal
mechanism. If a variant family has more than two rows, retain at most one
representative removal and one boundary or exception in the prose. Summarize
all other rows by direction, range, or monotonicity, even when the table has a
value for each row. Put exhaustive variant values and pairwise tests in a table
or figure, including one placed in the appendix. Do not turn each remaining row
into its own nominally separate block.

### Robustness and Boundary Tests

State which factor changes and which conditions remain fixed. Summarize the
stability range, failure point, or number of settings that follow the predicted
trend. Give special attention to mismatches and boundary cases. Avoid listing
every perturbation level when a range or figure conveys the same evidence.

### Theory Validation

Test a prediction, mechanism, or separating condition directly. Use one
representative trace or comparison, then summarize agreement over the full
grid. Say that the evidence `supports`, `matches`, or `is consistent with` the
prediction. Experiments do not prove a theorem, and finite tests do not verify
an asymptotic guarantee.

### Efficiency

Report cost only when it affects fairness, feasibility, or the interpretation
of a quality gain. Use a matched comparison and state the resulting tradeoff.
Do not enumerate latency, memory, parameter count, and throughput for every
method in prose when a table already provides them. Usually give one quality
versus cost comparison; add a second baseline only when it changes the
conclusion. Name hardware only when it is needed to interpret or reproduce the
efficiency measurement.

### Qualitative Analysis

Choose one or two representative examples that reveal a mechanism, capability,
or failure mode. Explain what the example shows. Do not replace analysis with a
gallery or describe every displayed example separately.

## Internal Artifact Boundary

Evidence ledgers and private research notes may record exact provenance. The
reader facing manuscript must not expose internal working identifiers,
including:

- absolute or relative filesystem paths;
- artifact directories and raw result filenames;
- shell commands and script names;
- configuration filenames, private keys, or internal configuration IDs;
- run IDs, job IDs, checkpoint hashes, and storage object names;
- internal stage labels or temporary experiment nicknames.

This rule applies to every reader facing part of the submission: main text,
captions, footnotes, tables, appendix, supplement, and rebuttal. Reproducibility
is not a reason to copy workspace metadata into the paper. Translate provenance
into semantic descriptions such as `the full method`, `the held out split`,
`five independent runs`, or `details are provided in the supplementary
material`. A deliberate public code or data release may be cited only through
a stable citation, DOI, or landing page URL in the normal bibliography
mechanism, never a link directly to a file or directory.
That exception never permits a filesystem path, script name, configuration
name, run ID, hash, job label, or internal stage label in any reader facing
artifact.

## Compression Example

Avoid cell by cell narration:

> Ours obtains 76.4, 69.1, 84.0, and 62.8 on Datasets A through D, while the
> strongest baseline obtains 74.0, 67.9, 83.5, and 60.1. Removing module R
> gives 74.1, 67.0, 83.4, and 59.9.

Prefer a claim led summary:

> Across four datasets, our method improves average accuracy by 1.7 percentage
> points over the strongest baseline and performs best in every setting. The
> largest gain occurs on Dataset D, while the smaller margin on Dataset C
> marks the main boundary of the improvement. Removing module R eliminates
> most of the gain, which supports its contribution under the tested setup.
> Table 2 reports the complete results and uncertainty over five runs.

The revised paragraph preserves the conclusion, a representative contrast,
uncertainty location, and scope without duplicating the table.

## Revision Pass

For every experiment paragraph:

1. Underline the claim it answers. Delete or merge the paragraph if no claim is
   identifiable.
2. Mark each sentence as question, protocol, evidence, interpretation, or
   boundary. Remove sentences that only recite a table cell.
3. Replace long value sequences with an aggregate, range, coverage count,
   trend, or representative case when the claim remains unchanged.
4. Move exhaustive values to a table or figure. Move semantic settings and
   extended interpretation to an appendix or supplement without turning them
   into cell by cell prose.
5. Remove internal artifact names and rewrite them as reader facing semantic
   descriptions. Apply the same check to tables, captions, appendices, and
   supplementary material.
6. Check every remaining number and comparison against the evidence source.

## Final Checks

- Does each block answer one claim question?
- Can the reader identify the matched conditions and uncertainty definition?
- Does prose interpret the table instead of repeating it?
- Are exact numbers limited to claim bearing or exceptional cases?
- Are contradictory cases and scope limits visible?
- Are ablation conclusions narrower than causal proof?
- Are all local paths, filenames, scripts, run IDs, hashes, and internal labels
  absent from every reader facing part of the submission, including the
  supplement?
- Are exhaustive values confined to tables or figures rather than prose in any
  section?
