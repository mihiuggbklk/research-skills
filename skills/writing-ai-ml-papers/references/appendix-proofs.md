# Appendix Proof Writing

Use this reference for theorem proofs, supporting lemmas, technical appendices, and asymptotic derivations. Scale the structure to the proof. A short direct argument should remain short; a long proof should make its dependencies, probability events, and limits visible.

The patterns below synthesize useful practices from Wu et al., Takanami and Pehlevan, Shamir, and Li et al. They are writing patterns, not authority for a mathematical claim. Verify every step from the manuscript's own assumptions and cited results.

## Proof Integrity Gate

Run this gate before drafting prose.

1. Copy the exact target statement into a working note. Preserve its quantifiers, domains, probability level, constants, and order of limits.
2. List every object used in the conclusion. Check that each object is defined and measurable on the full domain or probability space claimed by the theorem. If an optimizer can be nonunique, require a deterministic rule or a measurable selection.
3. List the assumptions available at the point of use. Do not borrow an assumption from a later theorem, an experiment, or an unstated convention.
4. Test the claim at boundary cases and inspect every inverse, denominator, logarithm, square root, optimizer, and selected branch.
5. Assign one status:

| Status | Meaning | Required action |
|---|---|---|
| `PROVABLE AS STATED` | The assumptions define all objects and support the complete conclusion. | Draft the proof. |
| `PROVABLE AFTER AUTHOR REVISION` | A specific correction or added assumption makes the claim valid. | Mark `[AUTHOR DECISION NEEDED]`, give the smallest repair, and do not present it as accepted. |
| `NOT JUSTIFIED` | A material step, condition, or result is unavailable. | Stop the proof at the exact gap and state what evidence is needed. |

Never define an estimator arbitrarily outside a favorable event merely to obtain convergence on the full probability space. Never strengthen an assumption, weaken a conclusion, change a limit order, or discard a case without saying so. A proposed correction belongs outside the proof until the author accepts it.

When the statement is incomplete, use language such as:

> The current assumptions define $\widehat w_n$ only on $\mathcal G_n$, whereas the convergence claim concerns the full probability space. We therefore cannot prove the theorem as stated. One possible repair is [precise repair]. `[AUTHOR DECISION NEEDED]`

## Choose the Proof Mode

Choose the lightest mode that exposes every obligation.

| Mode | Use when | Expected structure |
|---|---|---|
| Concise direct proof | The result follows through one short argument and has no hidden event or limit bookkeeping. | State the idea, perform the argument, recover the exact claim. |
| Structured proof | The result depends on several lemmas, cases, random events, or coupled quantities. | Give a roadmap, dependency map, named steps, and a synthesis paragraph. |
| Asymptotic derivation | The result uses deterministic equivalents, generating functions, resolvents, cavity arguments, or several limits. | State the rigor contract, maintain an asymptotic ledger, derive a closed system, select the valid solution, and separate formal conclusions from heuristics. |

Do not add a five step roadmap to a five line proof. Conversely, do not compress a multistage proof into "the result follows by standard arguments."

## Build the Dependency Map

Write the proof dependency map before writing the appendix:

```text
Main claim
  <- synthesis inequality or identity
  <- supporting lemmas
  <- deterministic or probabilistic tools
  <- assumptions and imported results
```

For each edge, record the exact output that the next node consumes. A lemma called "operator control" is too vague; record whether it supplies a norm bound, a spectral interval, invertibility, or a recursion coefficient.

Make the main text proof overview and the appendix follow the same conceptual order. The overview should name the obstacle, identify the few major stages, and say what each stage enables. The appendix may introduce preliminaries first, but its theorem proof should recover that same route explicitly.

The four source papers suggest complementary structures:

| Source pattern | Practice to reuse | Caution to add |
|---|---|---|
| Wu et al. | Map a technique overview to ordered appendix subsections; derive a master recursion before bounding its components; obtain coarse control before sharp control. | Track constants and assumptions locally, and make the final theorem synthesis explicit. |
| Takanami and Pehlevan | State a derivation roadmap; separate an exact error identity, a resolvent representation, order parameters, a closed system, and its solution. | Declare heuristic steps, limit order, convergence mode, and branch selection rather than calling them routine. |
| Shamir | Separate the deterministic perturbation core from the probability wrapper; localize an optimizer before invoking uniform convergence; use a positive margin set when transferring convergence to a discontinuous risk; enumerate parameter regimes. | Prove feasibility, measurability, positivity, compactness, and all sign cases, including boundary cases. |
| Li et al. | Separate preliminaries, technical lemmas, main theorem proofs, and deferred lemma proofs; use induction and case structure for multistage arguments. | Give local roadmaps around dense equations and explain why repeated cases are exhaustive. |

For a substantial theory appendix, consider this order:

1. Notation and proof only conventions.
2. Standard results and imported lemmas, with their conditions.
3. Technical lemmas in dependency order.
4. Proofs of the main theorems.
5. Deferred calculations or repeated cases that would interrupt the main route.

If readers need a technical lemma to understand the main proof, state it before the theorem proof even when its detailed proof appears later.

## Write Each Proof as a Proof Packet

For every theorem or lemma, include only the fields the proof needs:

1. **Target.** Restate the exact conclusion or the part proved in this packet.
2. **Idea.** Give one or two sentences that identify the mechanism.
3. **Inputs.** Name the assumptions, earlier lemmas, events, and limit regime used here.
4. **Argument.** Divide a long proof into named conceptual steps.
5. **Synthesis.** Substitute the established bounds or identities and recover the stated result.
6. **Closure.** Discharge cases, probability failures, parameter conditions, and quantifiers.

Use descriptive step titles such as `Control of the residual term` or `Closure of the recursion`. Avoid titles such as `Technical step` and `Some calculations`.

At the start of each long step, state its subgoal before displaying equations. After a long display, state what the display established and which later step uses it.

## Maintain a Probability Event Ledger

Create a ledger whenever the proof uses concentration, random invertibility, uniform convergence, or several favorable events.

| Event | Exact content | Failure probability | Conditions | Used in |
|---|---|---|---|---|
| $\mathcal E_1$ | The stated norm or spectral bound | $\delta_1$ | Sample size and parameter range | Lemma 2, Step 1 |
| $\mathcal E_2$ | The stated uniform deviation bound | $\delta_2$ | Compact set and covering radius | Theorem 1, Step 3 |

Then define one master event, for example

\[
\mathcal G = \mathcal E_1 \cap \mathcal E_2 \cap \cdots \cap \mathcal E_m,
\]

and compute its probability using the justified dependence structure. Use a union bound when no independence is available. Do not multiply probabilities unless independence has been proved.

Inside the proof, say explicitly when an argument is conditional on $\mathcal G$. At the end:

1. verify that every event condition follows from the theorem assumptions;
2. combine the failure probabilities;
3. remove the conditioning;
4. match the theorem's exact probability statement.

For convergence in probability, the random object must still be defined on the full probability space. A favorable event may control an object; it cannot silently create its missing definition.

When an optimizer or a supremum is involved, prove localization before applying a uniform bound. Establish that the relevant set is nonempty, feasible, and compact, or replace compactness with the exact coercivity or tightness argument that is used. If the optimizer is random and may be nonunique, specify a deterministic tie rule or cite a measurable selection result and verify its hypotheses.

## Maintain an Asymptotic Ledger

Before an asymptotic derivation, record:

| Item | Required entry |
|---|---|
| Indices and dimensions | Which variables tend to infinity or zero |
| Fixed quantities | Parameters held fixed during each limit |
| Growing quantities | Allowed rates and coupling between dimensions |
| Order of limits | For example, first $d\to\infty$ at fixed $t$, then $t\to\infty$ |
| Convergence mode | Almost sure, in probability, in distribution, in expectation, or formal |
| Uniformity | The set over which the error bound is uniform |
| Error scale | The explicit $o(1)$, $O(d^{-1})$, or other remainder |

Repeat the relevant part of this ledger when a proposition changes regimes. Do not let a local statement such as "for fixed $t$" become a final claim for growing $t$.

Tag the logical status of each major relation:

| Relation | Meaning |
|---|---|
| Exact identity | Holds at the stated finite dimensions. |
| Deterministic bound | Holds without a probability limit under named assumptions. |
| Probabilistic asymptotic | Has a stated convergence mode and limit regime. |
| Heuristic approximation | Uses an unproved self averaging, leave one out, cavity, replica, or closure step. |
| Numerical check | Supports behavior empirically but does not complete a proof. |

If the derivation is not fully rigorous, say so before the first heuristic transition and again when stating its consequence. Replace `we prove` with `we derive formally`, `we predict`, or `the calculation suggests`, as appropriate.

For a resolvent or generating function argument:

1. start from an exact target quantity;
2. express it through the generating function or resolvent;
3. define primary order parameters separately from auxiliary ones;
4. derive a closed system before attempting to solve it;
5. select the admissible branch using positivity, analyticity, boundary behavior, or another stated criterion;
6. verify that the solution returns the required real or positive quantity;
7. state the regime in which the deterministic equivalent is justified.

Do not use one symbol for asymptotic equality, order equivalence, and informal similarity.

## Track Constants and Scaling

Maintain a small constants ledger when a proof contains several concentration bounds or recursive estimates:

| Symbol | First definition | Depends on | Independent of | Required range |
|---|---|---|---|---|

State whether constants are universal or may depend on model parameters. Avoid changing the meaning of the same symbol between a lemma and a theorem. When a later condition absorbs several earlier ones, show the implication rather than saying "for a sufficiently large constant."

For a recursion or operator argument, use this sequence:

1. derive one master recursion or decomposition exactly;
2. identify the components that require separate control;
3. establish any coarse bound needed to enter a stable region;
4. prove the sharper component bounds;
5. substitute them into the master relation;
6. solve or iterate the relation under explicit parameter conditions.

For a perturbation argument, separate the layers:

1. prove the deterministic comparison under explicit norm, margin, invertibility, or spectral conditions;
2. verify that the random problem satisfies those conditions on named events;
3. combine the event probabilities;
4. translate the deterministic conclusion into the theorem's probabilistic claim.

When transferring parameter convergence or an $L_2$ bound to a discontinuous risk such as classification error, do not invoke continuity of the loss. For a chosen radius or truncation level, restrict first to a bounded set with positive margin. Use the parameter bound to preserve the sign on that set, control the probability of its complement separately, and only then take limits in the stated order. Treat zero margin and unbounded tails as explicit remainder terms.

For induction and case analysis:

1. state the induction invariant, including every index range and norm;
2. prove the base case under the same invariant;
3. identify exactly where the induction hypothesis is used;
4. enumerate cases using mutually exclusive and exhaustive conditions;
5. handle equality and zero boundary cases explicitly;
6. reassemble the cases into the original claim.

## Apply Imported Results Transparently

Before invoking an external theorem or a standard concentration result, map its hypotheses to local objects:

| Imported condition | Local object or assumption | Verification location |
|---|---|---|

State the instantiated conclusion, not merely the theorem name. If the imported result is used with changed notation, dimensions, conditioning, or normalization, explain the mapping. A citation does not discharge this obligation.

Do not write `by standard arguments`, `similarly`, `clearly`, `obviously`, or `it is easy to see` when the omitted step contains a sign choice, limit exchange, uniformity claim, optimizer argument, inverse, case split, or probability estimate. Either provide the step or identify a precise earlier lemma whose statement supplies it.

## Proof Prose and Equation Flow

Prefer first person for author decisions and proof actions:

- `We first establish the deterministic comparison.`
- `We condition on the event $\mathcal G$.`
- `We apply Lemma 3 with $A=\Sigma$ and $r=\varepsilon$.`
- `We now combine the two bounds.`

Use mathematical objects as subjects for mathematical facts:

- `The recursion contracts when $\eta L<1$.`
- `The resolvent is analytic on the upper half plane.`
- `The two cases cover all signs of $p$.`

Avoid forcing `we` into every sentence. Prefer prose clauses over optional compounds joined by hyphens, but never alter notation, theorem names, citation keys, commands, or mathematically meaningful minus signs to satisfy this style preference.

Every displayed equation should have a role in a sentence. Before the display, say what we compute or bound. After a dense sequence, state the mathematical consequence. Number only equations that later text cites or that mark a real proof checkpoint.

## Close the Proof

A proof is not complete when all lemmas have merely been mentioned. End with an explicit synthesis:

1. state the event, regime, or deterministic conditions under which all preceding steps hold together;
2. substitute the lemma conclusions into the master identity or inequality;
3. simplify to the exact bound, equality, convergence claim, or optimizer characterization in the statement;
4. verify constant ranges, sample size conditions, and nonzero denominators;
5. combine probabilities and remove any conditioning;
6. discharge every case and boundary condition;
7. restore the original quantifiers and order of limits;
8. state that this is the claimed conclusion, then end the proof.

If one item remains open, do not write `\qed`. Mark the proof `INCOMPLETE` at the gap and state the smallest missing lemma, assumption, or author decision.

## Compact Templates

For a direct proof:

```latex
\begin{proof}
We use [identity or lemma] to reduce the claim to [subgoal].
[Complete argument, with every condition mapped.]
Substituting this relation into [starting expression] gives exactly
[claimed conclusion].
\end{proof}
```

For a structured probability proof:

```latex
\begin{proof}
We prove the result in three steps. First, we establish [deterministic fact].
Second, we show that [random conditions] hold on an event $\mathcal G$.
Third, we combine these facts and remove the conditioning.

\paragraph{Step 1: [descriptive subgoal].}
[Argument.]

\paragraph{Step 2: [descriptive subgoal].}
[Define events, verify assumptions, and bound failure probability.]

\paragraph{Step 3: Synthesis.}
On $\mathcal G$, [explicit substitution and conclusion]. Moreover,
$\Pr(\mathcal G)\geq 1-\delta$ by [justified calculation]. This proves
the stated claim for [original quantifiers and parameter range].
\end{proof}
```

For an asymptotic derivation, begin with:

```latex
We take $d\to\infty$ while [quantities] remain fixed. All convergence
statements in this section are [mode of convergence]. Equation~(...) is
exact at finite $d$; the approximation begins at Equation~(...), where
we invoke [named assumption or result].
```

## Completion Checklist

- The target statement is copied exactly, and every object is defined on its claimed domain.
- The proof status is explicit; no assumption or definition has been added silently.
- The proof mode matches the complexity of the argument.
- The dependency map has no missing or circular edge.
- The main text overview and appendix use the same conceptual stages.
- Every imported result has its conditions mapped to local notation.
- Every inverse, denominator, optimizer, branch, feasible set, and compact set is justified; every random object is measurable, with a selection rule when needed.
- Probability events are named, combined correctly, and closed against the theorem statement.
- The asymptotic ledger records fixed quantities, growing quantities, limit order, convergence mode, uniformity, and remainder scale.
- Exact, deterministic, asymptotic, heuristic, and numerical statements are not conflated.
- Constants and parameter ranges retain one meaning throughout the proof.
- Induction cases and sign regimes are exhaustive and include boundary cases.
- Dense equation blocks have a stated subgoal and a stated consequence.
- The synthesis recovers the exact conclusion, probability, quantifiers, and limit order.
- First person describes author actions, while mathematical objects remain subjects of mathematical facts.
- Optional hyphenated compounds have been rewritten without changing mathematical notation.
- `\qed` appears only after every proof obligation has been discharged.
