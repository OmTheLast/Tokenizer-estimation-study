# Published technical text: source and sampling plan v1

Recorded 2026-10-18, before corpus collection or tokenization for this study.
Status: **source choices and sampling rules fixed; samples not yet collected**.
This is a follow-up to [the authored text-type pilot](TEXT_TYPES_V1.md), under
[the comparative study protocol](COMPARATIVE_STUDY_V2.md). Codex prepared this
design at Om's request. No new tokenizer or model weights are needed here.

## In simple language

Our previous experiment used examples we wrote ourselves. Now we will take a
small, repeatable sample of documents and files that other projects already
publish. Each of our six tokenizers will receive exactly the same text.

A **sample** is one passage or complete file. A **quota** is the number we aim
to take from each group. A **pinned revision** is a saved version of a project,
so later changes to that project cannot silently change our experiment.

We choose the sources and rules now, before seeing the answers. This plan is
progress in the research design; it is not a new finding about token counts.

## Questions and limits

1. Does the relative token count between our six profiles vary across these
   published technical text categories?
2. Do the JSON whitespace effects from our authored examples also appear in
   existing package files when we change only their serialization?
3. Do the tokenizers reconstruct the original text, including whitespace, and
   do any produce unknown-token IDs?

The population is **published technical documents and software files**. It is
not general web traffic, everyday conversation, news, or all natural language.
The selected projects are convenience sources, not a random sample of the web.
Files within a project are related; two MDN repositories share a publisher.
Source, topic, language and format are partly intertwined. This observational
comparison cannot prove that format or the BPE/Unigram algorithm causes an
observed difference. JSON reserialization is a separate paired intervention.

## Selected source pools

| Category | Source and eligible path pool | Target |
| --- | --- | ---: |
| English documentation passages | CPython `Doc/tutorial/**/*.rst`, `Doc/library/**/*.rst` | 10 |
| English documentation passages | Node.js `doc/api/*.md` | 10 |
| Python source files | CPython `Lib/**/*.py`, excluding tests and exclusions below | 10 |
| JavaScript source files | Node.js `lib/**/*.js` | 10 |
| JSON package manifests | npm CLI `workspaces/*/package.json` | 10 |
| JSON package manifests | VS Code `extensions/*/package.json` | 10 |
| HTML example files | MDN `dom-examples`, `**/*.html` | 10 |
| HTML example files | MDN `learning-area`, `**/*.html` | 10 |
| Hindi–English documentation passages | Microsoft ML for Beginners `translations/hi/*/*/README.md` | 10 |
| Tamil–English documentation passages | Same project, `translations/ta/*/*/README.md` | 10 |

Total target: **100 original inputs, 20 in each of five broad categories**.
Keep Python/JavaScript and Hindi/Tamil results separate as well as showing their
category summaries. These are quotas, not claims that 100 eligible inputs have
already been found. The exact path regular expressions, revisions, license
links and inventory counts are in [the source lock](../config/published-text-sources-v1.json).

The Microsoft README explicitly labels its translation support as automated.
These are existing published automatic translations with embedded English
technical terms, not verified human translations or conversational code-switching.
Translation quality is not evaluated here. This limitation must appear in reports.
Learn X in Y Minutes was considered but not selected: its inspected inventory
contained only four Hindi and four Tamil documents. We will not split those
eight files into twenty supposedly independent documents to fill a quota.

## Source terms and provenance

The lock pins seven full Git commit IDs, the root license paths and SHA-256
hashes, and Git tree identities. Root terms inspected: CPython's PSF license
and historical notices; Node's MIT terms with third-party notices; npm's Artistic
2.0 terms with separate dependency terms; VS Code and ML for Beginners MIT;
both selected MDN example repositories CC0 1.0. These labels summarize source
documents, not a blanket license for every file or for our repository.

Before including a file, inspect its header and any nearer license/notice files.
Record the applicable notices and skip exceptions whose reuse scope is unclear.
Exclude dependencies, images and third-party embeds. Root license hashes alone
do not establish file-level coverage. Retain attribution and any change notice
for excerpts or derived JSON. The collection manifest must record these checks.

Public artifacts will be the plan, source/file identifiers, hashes, eligibility
decisions, scripts, numeric measurements and graphs. Keep downloaded text and
derived text under ignored `data/raw/` or `data/processed/` by default. A future
decision to publish excerpts must follow their particular source terms.
No FLORES+ text, source tokens or reconstructable token sequences are involved
in this new corpus or its public artifacts. FLORES+ restrictions remain unchanged.

## Eligibility and sample boundaries

Read regular Git blobs (modes 100644 or 100755), decode strict UTF-8 and preserve
the bytes. Do not normalize Unicode, strip whitespace, repair spelling, change
line endings or replace tabs. Measure length in Unicode code points, not words,
UTF-8 bytes or JavaScript UTF-16 units; also record the other length units.

**Code, JSON and HTML:** one complete file, 200–12,000 code points inclusive.
No truncating a large file to make it eligible. JSON must parse as a strict JSON
object, with no duplicate keys or nonstandard numeric values. HTML is the source
file, not a DOM, screenshot, rendered page, downloaded asset bundle or visible-text
extraction. Code is source, not executed. HTML may include inline CSS/JavaScript;
record that fact rather than silently removing it.

**Documentation and mixed-script passages:** one unmodified paragraph per file,
200–2,000 code points inclusive. Split at blank lines, retaining exact byte offsets
for each maximal nonblank block; exclude the separating blank lines. Do not join
separate blocks or reflow lines. Keep inline Markdown/RST markup and links: these
are documentation-source passages, not guaranteed markup-free prose.

Exclude frontmatter, headings, tables, list-only blocks, link-definition blocks,
license/disclaimer boilerplate, fenced or indented code, RST literal/directive
bodies and HTML-only blocks. Context matters: a blank line inside a code fence
does not turn the next code block into a paragraph. The collection script must
track markup context; save review labels and exclusion reasons before encoding.
Review accepted passages for narrative text and language. Review may reject a
passage for these rules, never rewrite it or select it based on tokenizer output.

English passages must be predominantly English narrative. A mixed passage must
contain at least 20 alphabetic characters from the target script (Devanagari for
Hindi; Tamil for Tamil) and at least 20 ASCII letters, including at least one
English word or technical identifier in the narrative, not only a link destination.
This is an operational inclusion rule, not a linguistic definition of code-switching.
Record script counts and review labels. Do not translate or invent missing text.

Exclude path components `test`, `tests`, `fixtures`, `node_modules`, `vendor`,
`vendored`, `deps`, `dist`, `build`, `generated`, `__pycache__` (case-insensitive),
minified files, source maps, lockfiles and machine-generated code/data indicated
by file headers. Published automatic translations above are the explicitly
declared exception to the generated-content exclusion. Exclude secrets or private
personal records if encountered; never copy them into rejection logs.

## Selection order and duplicate handling

Use the literal seed `published-text-v1-2026-10-18`. A rank is the lowercase hex
SHA-256 digest of UTF-8 JSON for a string array, encoded with `ensure_ascii=False`
and separators `(',', ':')`. For files the array is `[seed, repo, revision, path]`.
Sort ascending by `(rank, path)`. This is a repeatable pseudo-random order; there
is no choosing a new seed because the eventual results look uninteresting.

For each file with eligible paragraphs, rank them using
`[seed, repo, revision, path, str(start_byte), str(end_byte)]` and take the first
eligible paragraph that survives the duplicate rules. End offsets are exclusive.
Proceed to the next ranked paragraph if a candidate is rejected; to the next
file if none remain. One selected sample per source file. Rank whole-file
candidates in the same file order. Record all examined candidates and decisions.

Process the five categories in table order; alternate the two source/language
strata within each category, one accepted sample per stratum per round, until
each reaches ten or exhausts its pool. For translation files, remove the language
prefix to form a lesson-family ID. Use a given lesson in **only one language**
in this sample; skip its other translation. This avoids counting two versions
of the same lesson as unrelated evidence. This study does not estimate a paired
Hindi/Tamil translation effect. The earlier aligned FLORES pilot is separate.

For duplicate screening only, normalize NFC and collapse Unicode whitespace to
one space, trimming endpoints. Keep the earlier selected candidate when these
screening strings match. Also reject a candidate if its set of character 5-grams
has Jaccard similarity at least 0.90 to an already selected sample (intersection
size divided by union size). Record the matching sample ID. Original text remains
unchanged for measurement. This rule reduces duplication; it does not prove all
remaining documents independent. Known file/translation relationships get family
IDs even when this heuristic misses them.

Do not borrow another source's quota or duplicate files to reach 100. Report any
shortfall. If meaningful coverage requires changed rules or a new source, publish
a dated amendment **before tokenization**. Token counts may not influence it.

Do not impose extra length quotas on this small pilot. Report the achieved
distribution and fixed bands 200–999, 1,000–3,999, 4,000–12,000 code points.
Passage groups will have no observations in the last band by design. A longer
file naturally needs more tokens; raw category totals are not a fair ranking.

## Freeze the corpus before measurement

Collection is the next round, not completed by this plan. Save a local raw snapshot
incrementally. The public manifest must contain repo, revision, path, Git blob ID,
full-file SHA-256, sample SHA-256, exact byte boundaries, category/stratum,
file/lesson family, length units, script counts, selection rank, attribution and
license-review references. Save candidate exclusions and shortfalls without text.
Hash the sampling script, review labels and manifest. Validate quotas, sample
hashes, boundaries, duplicate rules and source terms, then commit/push this corpus
manifest before any encoding. Freeze implementation details through this check;
changes to the rules require a dated amendment.

## Subsequent measurements and graphs (not run this round)

Reuse the exact six profiles, lock hashes and content-only encoding convention
in `config/text-types-v1.json`, including the existing XLM-R Unigram reference.
Do not add another profile in this round. Confirm all asset hashes again when
measuring. Preserve the MiniCPM runtime-equivalence caveat from the earlier pilot.

Primary input is each original passage/file. JSON has two extra paired variants:
compact and two-space-indented, no final newline, keys in original insertion
order, literal Unicode (`ensure_ascii=False`). Arrays keep their order. Before
encoding, freeze a serializer that preserves parsed numeric values exactly,
including large integers/decimals; demonstrate parse-value equality and reject
unsupported cases rather than silently rounding. Numeric spellings/escapes may
change versus the original: **pretty/compact** isolates whitespace because both
use the same serializer; comparisons to original do not isolate whitespace alone.
These variants are repeated measurements of the same sample, not new documents.

At the full target: 100 × 6 = 600 original measurements and 20 × 2 × 6 = 240
JSON-variant measurements. These are planned row counts, not existing results.
Save per-input content counts, counts with configured special tokens separately,
unknown-ID counts and exact decode-to-original checks. Verify Python/JS token-ID
sequence hashes using the prior harness pattern, without publishing source IDs.

Report each category, source stratum and mixed language separately. Use paired
per-input count ratios to Qwen (a fixed reference, not a quality standard), saving
all pairwise ratios as supporting data. Show medians, geometric means and 10th/90th
percentiles with sample counts; percentile ranges describe sample spread, not
confidence in a population estimate. Report source and length distributions.
Tokens per 100 code points is a descriptive density, not a universal measure of
information or cross-language efficiency. Do not pool the 100 texts into a web-wide
leaderboard or claim fewer tokens imply better understanding.

Planned figures: (1) per-sample ratio dots grouped by category and source,
(2) paired compact/pretty JSON ratios, (3) reconstruction/unknown-ID rates with
denominators, plus a sample-length distribution panel. Publish numeric inputs,
scripts and readable captions with every graph. Independently recompute summary
values and verify selected-source hashes before interpreting the results.

No fitting, final-exam/devtest access, model inference, browser-speed measurement
or general algorithm-family claim is part of this plan.
