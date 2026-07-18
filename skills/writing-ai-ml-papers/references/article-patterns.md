# Structural Patterns From the Reference Paper

Use these patterns when planning a theoretical or hybrid AI and ML paper. They are distilled from Li et al. (2025), *Training Nonlinear Transformers for Chain-of-Thought Inference: A Theoretical Generalization Analysis*. Borrow the argument design, not the source wording.

## 1. Turn the Literature Gap Into a Question

Move from broad context to two neighboring lines of work, identify what neither line establishes, and state one precise question. Make the question answerable by the paper's main results. Avoid generic claims that a topic is merely underexplored.

Adapt the reference pattern:

1. Establish the practical phenomenon.
2. Summarize work on expressivity or existence.
3. Summarize work on optimization or generalization in a simpler setting.
4. Identify the missing bridge between training and generalization.
5. State the exact question that the paper answers.

## 2. Organize Contributions as a Dependency Chain

Use descriptive contribution leads followed by quantitative content. Order them so that later claims use earlier ones:

1. Analyze how training produces the target capability.
2. Characterize when that capability generalizes.
3. Compare it with the closest alternative under a condition that separates them.

Write each contribution with `we` and include the object, guarantee, controlling quantities, and consequence. Do not list implementation components as contributions.

## 3. Separate Insights From Formal Setup

Give readers a short map of the main results before introducing every symbol. For each insight, name the phenomenon, point to the formal result, state the dependence that matters, and explain the intuition. Then define the data, tasks, model, training procedure, inference procedure, and metric in a dedicated setup section.

This separation lets readers understand why a theorem matters before parsing its notation.

## 4. Pair Each Formal Result With Interpretation

Use four layers:

1. **Statement:** assumptions, quantified variables, guarantee, and probability.
2. **Scaling:** which quantities increase or decrease the requirement.
3. **Meaning:** what behavior the result explains.
4. **Boundary:** which simplifying condition limits the conclusion.

Do not claim that intuition proves the theorem. Do not omit an assumption when restating the theorem in prose.

## 5. Use a Separating Condition for Comparisons

When comparing method A with method B, identify a condition required by one but not the other. Present the comparison as cases:

- If the condition fails, state what cannot be guaranteed.
- If the condition holds, compare the remaining requirements.

This is stronger and clearer than saying that one method is generally better. Preserve the scope: `we show an advantage when Condition C fails`, not `A always outperforms B`.

## 6. Explain the Mechanism Before the Full Proof

State one proposition that captures the learned behavior, then explain the proof route as a sequence of changes in model behavior. Assign one role to each lemma. In the reference paper, the useful pattern is a two stage process: first eliminate irrelevant positions, then concentrate on relevant patterns. Generalize this as:

1. Identify the coarse structure learned first.
2. Identify the finer discrimination learned next.
3. Connect the final behavior to the main guarantee.

## 7. Make Experiments Test Theoretical Predictions

Use experiments to check trends, mechanisms, and boundary cases:

- Vary one quantity that appears in a bound while holding others fixed.
- Test the separating condition in both cases.
- Visualize the internal mechanism predicted by the analysis.
- Test whether the mechanism appears in a less simplified model.

Say that results `support`, `match`, or `are consistent with` a prediction. Do not say that an experiment proves a theorem.

## 8. Close With Scope, Value, and Limits

Restate what we establish, then acknowledge the simplified model or data assumptions. Explain why the result still advances understanding under those assumptions. End with future work that directly relaxes a named limitation.

## Adaptations Required by This Skill

The reference paper contains useful structure but also uses passive and paper centered phrasing and many hyphenated modifiers. Preserve its argument architecture while applying these changes:

- Use `we` for author actions.
- Replace optional hyphenated compounds with natural phrases.
- Avoid broad novelty claims unless the literature search verifies them.
- Separate observed experimental agreement from formal proof.
- Keep sentences shorter when notation and interpretation compete for attention.
