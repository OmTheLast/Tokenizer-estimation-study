# Collection implementation and review record

Started 2026-10-19, before any encoding. Parent rules:
[published-text sampling v1](PUBLISHED_TEXT_SAMPLING_V1.md). Same sources, seed,
quotas, length limits and six future tokenizer profiles. This document records
implementation decisions; the frozen parent document remains unchanged.

## Conservative paragraph extraction refinement

The collector operates on maximal runs of nonblank lines and preserves byte
offsets. A sample includes the line terminator on its final nonblank line, if
present, but not blank separator lines. It does not strip or rewrite the text.
Code fences and RST directives/literal blocks are tracked across blank lines.
UTF-8 decoding is strict; CRLF is not converted to LF.

The implementation narrows passage eligibility to top-level narrative blocks:
blocks containing indented lines, blockquotes, and blocks starting with HTML or
image badges are excluded conservatively. This is a refinement of the parent
plan's narrative-text requirement, not a claim that all such excluded blocks
are non-narrative. It avoids ambiguous extraction without rewriting documents.
Inline links and markup in accepted narrative remain intact. Any missed syntax,
license boilerplate or non-narrative block is rejected in recorded review.
No selection or refinement uses token counts.

An HTML source can reference images, scripts or stylesheets: those resources are
not fetched, embedded into the input or executed. Review rejects a file that
itself carries an unclear third-party embedded-content exception. The input is
the original HTML bytes, not rendered browser content.

## What review means

Automated checks verify download Git blob identities, byte boundaries, strict
JSON parsing, size rules, script counts and duplicate screening. Codex then
inspects selected passages, complete small files/file headers and applicable
notices for narrative/language eligibility, generated content and source terms.
Reviews are saved by stable file and sample IDs with reasons; rejected candidates
remain in the decision log. This is AI-assisted review, not an independent human
review or a certification of translation quality.

Terms evidence includes the root license and ancestor-directory license,
copyright and notice documents discoverable in the pinned Git tree. File headers
and JSON license fields are also reviewed. Notices about unrelated dependencies
do not automatically license the sampled file. Original notices remain in local
raw files; public manifests link to their pinned originals and record hashes.
Source text and review-preview text stay ignored locally.

Each collection run uses a new output directory. Downloads are written atomically
and verified on reuse; the manifest and decision log are saved after each selected
file. Interrupted work can resume by rerunning into a new directory with the same
review file and cached raw files. No upstream program is executed.

## Review and freeze sequence

1. Collect provisional candidates in the saved rank order.
2. Review text and source terms; save accept/reject labels without source text.
3. Replay the sampler with those labels. A rejected paragraph advances to the
   next ranked eligible paragraph; a rejected file advances to the next file.
4. Review any replacements, repeat until all selected files/samples are reviewed,
   and report any quota shortfalls without borrowing other strata's samples.
5. Independently check hashes, offsets, labels, quotas, known lesson families and
   pairwise duplicates. Replay selection offline to check the final manifest.
6. Publish metadata, scripts, decisions, checks and readable findings before
   any tokenizer measurement. JSON formatting variants are a later measurement
   preparation step, not additional independent samples in this collection.

## Completed review outcome — 2026-10-19

All 100 targets were filled. Eight focused tests passed, a separate verifier checked
all bytes/metadata and 4,950 duplicate pairs, and an offline replay matched the
manifest and decisions exactly. See the [collection report](../results/2026-10-19-published-corpus/REPORT.md).

Review caught an image-caption block and a translated disclaimer missed by the
initial parser. URL-only ASCII text was rejected under the parent's mixed-text
rule; a supplemental script records conservative rejection labels but never
generates acceptance labels. Roman-script personal/company names alone were not
treated as English words or technical identifiers. Library/product names, function
identifiers and acronyms used in narrative were eligible. No language-quality
claim follows from these labels.

The code-source rule excludes actual unit tests even where directories are named
`idle_test` rather than exactly `test` or `tests`; one such file was rejected in
review. The separate JSON group permits a test-tool's package manifest because it
is a real package configuration rather than fixture/test-code content. HTML demos
remain eligible when their titles say “test”; source-category context matters.

Only source bytes are measured later: referenced images, fonts, scripts, dependency
packages and runtime output are not part of these inputs. Shared exercise templates
and the npm manifests' template tooling are disclosed, not evidence of independent
authorship. No source/seed/quota/length/duplicate-threshold changes were made.
