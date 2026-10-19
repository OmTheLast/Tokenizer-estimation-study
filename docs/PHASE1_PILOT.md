# Phase 1 pilot: measuring new multilingual text

Started 2026-10-10.

## Status

**Completed 2026-10-15:** official authenticated access succeeded and the pilot
saved 9,000 measurements (1,800 texts × five tokenizers). All input/configuration
hashes, five shard checksums, row uniqueness and prediction-error calculations
were independently checked; the heat map was visually inspected. No overlap
with the 38 published fixtures was found. No weights were fitted, and devtest
was not accessed.

See the [generated report](../results/2026-10-15-phase1-pilot/run-02/REPORT.md),
[terminal output](../results/2026-10-15-phase1-pilot/run-02/terminal-output.txt)
and [validation](../results/2026-10-15-phase1-pilot/run-02/validation.json).
The earlier HTTP 403 and the 2026-10-15 restricted-network DNS failure are
preserved in their historical logs. Run-02 succeeded with network access.

## What we will measure

The frozen [pilot plan](../config/phase1-pilot.json) selects 100 common dev
sentence IDs across 18 language varieties: English; Hindi, Marathi, Bengali,
Gujarati, Kannada, Malayalam, Odia, Punjabi, Tamil, Telugu; Simplified and
Traditional Chinese, Cantonese, Japanese, Korean; Arabic and Russian.

Those same IDs align translations across languages. With five existing tokenizer
profiles, the intended table contains 1,800 texts × 5 = 9,000 measurement rows.
The pilot covers ten Indian languages and all five requested CJK varieties; it
does not yet cover all Indian scheduled languages or the full tokenizer roster.

IDs are ranked by a fixed SHA256 rule, without looking at token counts. The
chosen IDs and downloaded file hashes are saved before measurement. The pilot
does not access `devtest`. Raw text stays in the ignored dataset cache.

For each text/tokenizer pair we record content-token count, special-enabled count
and their difference, Unicode code-point count, UTF-8 bytes, UTF-16 units, existing
character classes, extra CJK block diagnostics, normalized text length, and a
pre-tokenizer diagnostic. The unchanged estimator and old chars/3.5 heuristic
produce predictions for comparison. We do not change weights in response.

The pre-token diagnostic runs the tokenizer's own normalizer followed by its
pre-tokenizer. It does not emulate the separate extraction of added-token strings;
the table flags inputs containing such strings. Content-token counts themselves
use the full tokenizer, with added special tokens explicitly disabled.

## Dataset provenance and a change from the original plan

Source: [FLORES+ maintained by OLDI](https://huggingface.co/datasets/openlanguagedata/flores_plus),
revision `e707e62e762a9e2faca3933aa315f4665cc3cd8f`, licensed CC-BY-SA-4.0. FLORES+
builds on the FLORES datasets from Meta/FAIR. See the dataset card and its
bibliography for attribution requirements. Its source sentences and translations
are not being redistributed here.

The current dataset card specifies evaluation use and says the data should not
be used for training. **We will evaluate frozen estimators on FLORES+, not fit
or calibrate new weights on its dev split.** This changes the earlier proposal
to fit on dev. Any future fitting corpus must be selected separately. Public
redistribution restrictions in the dataset card also mean raw text and token-ID
sequences are kept out of the project outputs.

The pilot checks exact overlap with the 38 published LocalMind fixtures before
measurement. We cannot prove absence of overlap with unpublished fitting text,
or with language-model training data. Results are exploratory evidence for the
unchanged estimator, not a claim of rigorously unseen model-training content.


## FLORES+ access conditions remembered on 2026-10-15

Dataset access conditions:

- "I agree not to re-host FLORES+ in places where it could be picked up by web crawlers"
- "If I evaluate using FLORES+, I will ensure that its contents are not in the training data"
- Accepting shares the account email and username with the repository authors.

Our project keeps FLORES+ evaluation-only, excluded from training, estimator
fitting and margin calibration. Raw text and reconstructable token-ID sequences
must stay out of public repositories, reports and logs. These commitments fit
our planned evaluation, but full historical training/fitting corpora for the
third-party tokenizers and existing estimator are unavailable. We cannot claim
that upstream exposure to FLORES+ has been ruled out.

The screenshot does not prove the access button was clicked. No acceptance,
download or experiment was performed during this documentation round.

## Running it after access is granted

Use the same account at the [FLORES+ access page](https://huggingface.co/datasets/openlanguagedata/flores_plus)
as the locally configured Hugging Face account. Accept/review conditions in your
browser; do not put access tokens in chat or in project files.

Install the separate phase-1 environment lock (earlier phase-0 locks are preserved):

```bash
.venv/bin/python -m pip install -r requirements-phase1.lock.txt
```

Then run, from the project root:

```bash
.venv/bin/python scripts/measure_pilot.py --output results/phase1-pilot-01
```

This downloads only the selected dev language files through normal authenticated
Hub access, freezes input hashes and sample IDs, measures tokens, writes one
ground-truth Parquet file, and creates a heat map, error summaries and a table of
the ten largest tokenizer gaps within languages. No model weights are downloaded.

After interruption, resume with the same command plus `--resume`. Completed
per-model shards are reused only when their checksums and the input/config/code
fingerprint agree. If inputs or code change, use a new output directory. A
resume can restart an incomplete model shard; it does not assume a process survived.

## Infrastructure checks

```bash
.venv/bin/python tests/test_pilot_inputs.py
.venv/bin/python scripts/measure_pilot.py --smoke --output results/pilot-smoke-new
```

Smoke output is prominently labelled and must never be used as new study evidence.
It checks 190 counts and estimates against the preserved phase-0 results, column
integrity, Unicode measurements, and Parquet round-trip fidelity. Input tests use
artificial records only to check shared-ID sampling, frozen-input protection and
safe error reporting without network access.

The heat map uses total content tokens / total Unicode code points in each cell.
Largest gaps compare total token counts across tokenizers on identical selected
text within one language. A separate group table reports Indian, CJK and other
groups. These are not measures of model quality or browser performance.

Review the pilot before expanding to 20+ tokenizers or later phases. No fitting,
model training, remote publication or Git push is part of this round.
