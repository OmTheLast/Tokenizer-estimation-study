# CJK experiment v2: focused exploratory comparison

**Deferred as of 2026-10-18:** the [broader comparative study](COMPARATIVE_STUDY_V2.md)
is now the priority. This design is preserved, unstarted, and not an authorization
to fit coefficients. Its source-use question matters only if this experiment resumes.

Dated 2026-10-16. Om asked us not to add requirements that distract from the study.
This amendment follows the data audit, **before any candidate token counts,
fitting or exam-error results were computed**. It changes the strength of our
claims as well as the data requirement. The [v1 design](CJK_EXPERIMENT_V1.md),
[v1 configuration](../config/cjk-experiment-v1.json) and failed v1 audit remain
unchanged as historical records. [The v2 configuration](../config/cjk-experiment-v2.json)
is now the active plan. All v1 procedures not explicitly replaced below carry
forward, including the controlled comparison and no fitting on FLORES+.

## Plain-language explanation

We want to compare one shared multiplier with three separate multipliers.
We can do a useful first experiment using carefully separated sentences. We do
not need to recover every original article before learning anything.

Copies and known translations still belong together: practice should not include
an answer that reappears in the exam. But if we cannot identify all articles,
we say so and avoid claiming that every sentence is independent of the others.
The result describes performance on this particular test collection, not a
universal guarantee about new articles or languages.

## What changes

- Missing original-document IDs no longer automatically disqualify a candidate.
  Remove the requirement for at least 20 verified original-source groups in
  each primary train/test split. Keep the 500 practice/100 exam sentence floors
  and existing feature-coverage/rank checks as practical feasibility checks.
- Group exact/near duplicates and known translation/conversion families using
  the existing rules. Include trustworthy article/film groups where available.
  Unknown article relationships remain unknown; do not label each sentence or
  duplicate component as an independent original article.
- Retain upstream split roles and priority test > dev > train. Freeze exclusions
  and a new v2 split manifest before fitting. The existing provisional manifest
  is evidence to reuse, not automatically an approved training input.
- The primary outcome remains split-minus-pooled macro mean absolute percentage
  error, with equal weight for primary languages and tokenizer profiles. Report
  direction, size, all individual cells and the previously specified tradeoffs.
- **No bootstrap confidence interval or significance test in this bounded trial.**
  Unknown article dependence does not justify treating sentence rows as
  independent draws. Replace v1's interval-based support rule with a descriptive
  statement: whether the split arm had lower error on this fixed test set.
- Retain the prospective 10% relative-improvement flag and >5-percentage-point
  regression flags as descriptive study conventions. They are not deployment
  targets or proof of generalization. Show the underlying changes, even if a
  flag is missed. A later stronger study can use another dataset with known
  source groups and a separately specified uncertainty analysis.

## What stays fixed

The same five tokenizer assets, original non-CJK weights, block definitions,
same practice texts for both fitted arms, nonnegative relative least-squares
objective, rounding, baselines, primary/secondary language roles, dedup rule,
and unseen exam scoring remain as in v1. Keep code and candidate coefficients
frozen before looking at exam errors. No new formula, fitting, tokenizer run,
or test scoring was performed to make this amendment.

The source-text permission/provenance caveat found in the pinned GSD READMEs is
separate from missing article IDs. It remains a targeted source-use question,
not an instruction to conduct an unlimited provenance investigation. Record a
credible use basis or substitute a suitable source; do not assert that this
amendment grants a licence. Do not publish raw source text.

## Revised reading of the completed audit

The v1 audit remains correct under the rules that existed when it ran. Under v2,
the article-ID deficit becomes a limitation. Its duplicate findings still matter:
133 Korean practice rows and 30 development rows were excluded by the known-family
split-priority rule, with additional within-split exact-copy removal. Available
text counts and character-feature coverage passed the v1 count/rank checks.

No approved v2 manifest exists yet, and source-use documentation is unresolved.
The next action is that narrow check followed by the cleaned v2 manifest, not
recovering every original article. Explicit authorization is still needed before
fitting; this amendment authorizes neither training nor package deployment.

## Evidence we will publish

Every result figure must include a question, labelled axes and units, denominator,
source-data hash, plotting script, caption and stated limitations. Show all
comparison groups, including failures. Use tables for exact values and a dated
milestone log for progress; do not invent a numerical completion percentage.
The [evidence guide](EVIDENCE_GUIDE.md) links existing graphs and their claims.
Before/after fitting plots can be made only after the planned experiment runs;
current graphs compare the two already-measured frozen estimators.
