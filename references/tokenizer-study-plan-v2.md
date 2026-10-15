# Token counts without the tokenizer — study plan (owner: Om)

Handed to Om 2026-09-26 by Chirag. Source: the parked research path in the vault,
`~/Code/knowledge/notes/tokenizer-free-token-estimation-research-path.md`.
Estimated effort: about 2 weeks part-time. CPU only; a laptop is enough.

## 1. Background

Apps that run small language models on the device need to know how many tokens a chat history
costs before sending it to the model. If the count is too low, the context window overflows
without warning. If it is too high, the app drops turns that would have fit.

LocalMind used to estimate `ceil(chars / 3.5)`, one constant for every language and model.
Measured against each model's own `tokenizer.json` (2026-09-24):

- Kannada on LFM2.5 was counted at 11% of its real cost (−89%). English was overcounted by ~40%.
- The same Tamil text costs 0.25 tokens/char on Gemma 4 and 2.16 on LFM2.5, 8.8× apart.
- English costs about 0.21 tokens/char on all five tokenizers tested.

The fix now in LocalMind (public repo `NakliTechie/LocalMind`, commit `b39f0bc`):
classify each character by Unicode block (Latin, ASCII symbols, 9 Indic blocks, Arabic,
Cyrillic, CJK, other), multiply by a per-tokenizer weight, and sum. Unknown tokenizers get the
densest weight seen plus 15%.

| estimator (38 samples × 5 tokenizers) | worst under | worst over | median error | within ±20% |
|---|---|---|---|---|
| `chars ÷ 3.5` | −89% | +48% | 39% | 28% |
| tokenx (calibrated to `o200k_base`) | −93% | +72% | 45% | 35% |
| per-script, per-tokenizer profile, held out | −18% | +37% | 0% | 98% |

It costs 1 ms for 268,000 characters and needs no tokenizer download.

The weakness: 38 hand-written samples, 5 tokenizers, and one person's judgement. This study
tests the idea properly.

## 2. What is already known — do not claim it as new

- Tokenizers charge some languages far more than others: up to 15× on FLORES-200.
  Petrov et al., NeurIPS 2023, https://arxiv.org/abs/2305.15425
- Indian languages specifically: 8.0× mean, 13.0× for Malayalam.
  The Tokenizer Tax, https://arxiv.org/abs/2607.24276
- A cause in abugida scripts: GPT-2's `\p{L}+` pre-tokenizer splits words at every vowel sign.
  63.3% of top HF text models carry that pattern. https://arxiv.org/abs/2608.26449
- Estimating tokens without a tokenizer: tokenx (MIT), calibrated to one OpenAI tokenizer,
  with documented Indic and Arabic gaps. https://github.com/johannschopplich/tokenx

What looks new: a per-model estimator for current open-weight tokenizers (Qwen3.x, Gemma 4,
LFM2.5, MiniCPM5 and others), tested on held-out languages and held-out tokenizers, with its
effect on real context budgets.

## 3. Research questions

- **RQ1.** How much does the cost per character vary across open-weight tokenizers and scripts?
- **RQ2.** Does a per-script linear profile stay within ±20% on sentences and languages it has not seen?
- **RQ3.** Can a profile be derived from `tokenizer.json` alone, with no fitting on text?
- **RQ4.** How often does each estimator let a context budget overflow without warning?

## 4. Materials

**Ground truth.** Python `tokenizers` (Hugging Face) on each model's `tokenizer.json`, and
`tiktoken` for `o200k_base` and `cl100k_base`. Count content tokens only; exclude BOS, EOS and
other special tokens. LocalMind measured with the JS `@huggingface/tokenizers`. Check that
Python gives identical counts on the 38 LocalMind samples before trusting it.

**Text.**
- FLORES+ `openlanguagedata/flores_plus` (CC-BY-SA-4.0). It is gated: accept the terms on HF with
  your account. Use `dev` (997 sentences per language) to fit and `devtest` (1,012) to test.
  The same sentences exist in every language, so content is held constant.
- All FLORES+ languages for RQ1. Report two focus groups on their own: the Indian scheduled
  languages, and **Chinese, Japanese and Korean** (added 2026-09-26, see section 4a).
- A small code and JSON set (JS, Python, JSON, mixed prose + code), since chat histories contain
  code. Record the source and licence of every file.
- The 38 LocalMind samples in `scripts/token-fixtures.mjs`, as a continuity check.

**Tokenizers: at least 20 open-weight ones.** Suggested: Qwen3, Qwen3.5, Qwen3.8 (= Ternary
Bonsai 2; byte-identical to Qwen3.5, include once and note it), Gemma 3, Gemma 4, Llama 3.x,
LFM2 / LFM2.5, MiniCPM5, Mistral v0.3, Mistral Nemo (Tekken), Phi-4-mini, DeepSeek-V3,
SmolLM3, Granite, OLMo 2, Sarvam-1, BLOOM, plus `o200k_base` and `cl100k_base` for contrast.
Llama and Gemma repos are gated (manual approval). Either accept their licences or use an
ungated mirror of the same tokenizer, and record which. Pin every tokenizer by repo id **and
commit sha**.

## 4a. Chinese, Japanese and Korean (added 2026-09-26)

FLORES+ has `cmn_Hans` (Simplified Chinese), `cmn_Hant` (Traditional Chinese), `yue_Hant`
(Cantonese), `jpn_Jpan` (Japanese) and `kor_Hang` (Korean). Use all five.

Why they matter beyond "more languages": LocalMind's estimator puts Japanese kana, Chinese
characters and Korean Hangul syllables into **one** `cjk` class
(`index.html` TOKEN-COUNT block, the `0x3040–0x30FF | 0x3400–0x4DBF | 0x4E00–0x9FFF |
0xAC00–0xD7AF` test). These scripts tokenize very differently: a Hangul syllable is one
character built from 2–3 letters, and Japanese mixes kana with Chinese characters. Hangul Jamo
(`0x1100–0x11FF`) and CJK punctuation (`0x3000–0x303F`) currently fall into `other`.

- **Split the class** into Han, kana (Hiragana + Katakana) and Hangul, plus CJK punctuation.
  Report whether the split beats the single class, and by how much.
- **Report CJK as a group** in every table, next to the Indian group.
- **Watch pre-tokenization:** these languages do not put spaces between words, so a
  whitespace-based pre-tokenizer behaves differently. Note what each tokenizer's pre-tokenizer
  does with them.
- **Add CJK-focused tokenizers** (all ungated on HF, checked 2026-09-26):
  `LGAI-EXAONE/EXAONE-4.0-1.2B` (Korean), `upstage/SOLAR-10.7B-v1.0` (Korean),
  `llm-jp/llm-jp-3-1.8b` (Japanese), `sbintuitions/sarashina2.2-1b-instruct-v0.1` (Japanese).
  Qwen and DeepSeek already cover Chinese.

## 5. Phases

Each phase ends with something I can check. Send me phases 0 and 1 before going further.

### Phase 0 — reproduce (day 1)
- Create your own repo for the study.
- Read LocalMind `index.html` lines 9149–9221 (the `TOKEN-COUNT-START` … `TOKEN-COUNT-END`
  block), `scripts/test-token-count.mjs` and `scripts/token-fixtures.mjs`.
- Run `node scripts/test-token-count.mjs` in LocalMind.
- Port `countTokens` to Python and re-count the fixtures with Python `tokenizers`.
- **Check:** your port gives the same worst under (−16%) and worst over (+23%) as LocalMind.
  Any count that differs between JS and Python tokenizers gets listed and explained.

### Phase 1 — ground-truth table (days 2–3) — RQ1
- For every tokenizer × language × split × sentence, record: token count, characters, UTF-8
  bytes, pre-token count (run the tokenizer's own pre-tokenizer), and the character count per
  Unicode class.
- Save as one Parquet file. One command rebuilds it from scratch.
- **Output:** a heat map of tokens per character (tokenizers × languages), and a short table of
  the 10 largest gaps between tokenizers for the same language.

### Phase 2 — estimators and held-out tests (days 4–6) — RQ2
Estimators to compare:
1. `chars / N` with N fitted over everything.
2. `bytes / N`.
3. tokenx, default settings.
4. tokenx with per-model `languageConfigs` fitted on dev.
5. The per-script linear profile (the LocalMind method), fitted per tokenizer. Use the
   closed-form coordinate-descent fit on relative error. Plain gradient descent did not
   converge for scripts with a single sample in LocalMind.
6. A pre-token model: pre-tokens × fitted tokens-per-pre-token per class.
7. A small learned model (for example gradient-boosted trees on the class counts), as a ceiling
   for what the features can do.

Held-out settings:
- **A. Unseen sentences:** fit on dev, score on devtest.
- **B. Unseen languages:** leave one language out, both within its script and across scripts.
- **C. Unseen tokenizers:** leave one tokenizer out. Only estimators that can use the file
  itself qualify (see Phase 3); the rest use the "densest weight + 15%" fallback.

Metrics, per estimator and per script group: signed relative error per sentence; median
absolute error; 5th and 95th percentile; worst under; worst over; share within ±20%; and the
**undercount rate** (share of sentences counted low), because undercounts are the dangerous side.

### Phase 3 — profile from the file alone (days 6–8) — RQ3
- Read features straight from `tokenizer.json`: the pre-tokenizer regex (does it split at
  combining marks, as the GPT-2 `\p{L}+` pattern does?), vocabulary entries per Unicode block,
  byte fallback on or off, and merges that touch each script.
- Build an estimator that predicts a tokenizer's profile from those features, with no text fit.
- **Check:** on held-out tokenizers (setting C), its median error is within 2× that of a
  profile fitted on text. If it fails, report by how much. A negative result is still a result.

### Phase 4 — does it matter downstream? (days 8–9) — RQ4
- Build multilingual chat histories from FLORES+ devtest: group sentences into turns, mix
  languages and code, keep 20–100 turns each.
- For budgets of 4K, 8K, 16K and 32K tokens: let each estimator trim the history to fit, then
  count with the real tokenizer.
- **Output:** per estimator and tokenizer, the overflow rate (real count above budget) and the
  wasted budget (real count far below budget, meaning turns were dropped for nothing).

### Phase 5 — write-up and package (days 10–12)
- **Paper:** a 4-page workshop short paper draft for a multilingual-NLP or efficient-NLP workshop,
  framed as token budgeting for on-device multilingual LLM apps. Cite section 2 for the
  disparity. Claim only the estimator, the per-model results and the downstream effect.
- **Package:** a ~1 kB npm package with one profile per tokenizer, plus a script that fits a new
  profile from any `tokenizer.json`. MIT or Apache-2.0.
- **Report back:** the tables and figures, plus one paragraph on what the Phase 2 results mean
  for LocalMind's current weights.

## 6. Rules

- Pin everything: tokenizer shas, dataset revision, library versions, random seeds.
- Every number in the write-up comes from a script in the repo. No hand-copied values.
- Keep dev and devtest apart. Never fit on devtest.
- Report failures and negative results next to the wins.
- Keep a dated log of what you tried and what happened, one line per attempt.

## 7. Credibility — the work must be visibly Om's

This study is meant to stand up to scrutiny, including from university admissions officers.

- **Om does the work and is the first author.** Chirag advises; the paper's acknowledgements say
  so. The LocalMind baseline is Chirag's prior work and is cited as such.
- **Om's commit history is the evidence.** Commit small and often, in Om's own name, from the
  first day. No squashed history.
- **Disclose AI assistance** honestly, following the venue's policy, in the paper and README.
- **Om must be able to explain every choice** in an interview: why FLORES+, why held-out
  tokenizers, what the undercount rate means.

## 8. Deliverables

1. The study repo: data build script, estimators, evaluation, figures, log.
2. The Parquet ground-truth table (or a script that rebuilds it).
3. Results tables for RQ1–RQ4.
4. Paper draft.
5. The npm package, unpublished until we review it together.

## 9. What Om has at the end

Each item is public, dated and checkable by a third party:

1. **An arXiv preprint** with Om as first author. A first-time submitter in `cs.CL` may need an
   endorsement from an existing arXiv author; arrange this before the deadline.
2. **A workshop submission** to a peer-reviewed multilingual-NLP or efficient-NLP workshop.
   Acceptance is not guaranteed; the submission and reviews are still a record.
3. **A public GitHub repo** that rebuilds every number with one command, archived on Zenodo for
   a citable DOI.
4. **A Hugging Face dataset** of the ground-truth counts, under Om's account.
5. **A published npm package** with Om as maintainer.
6. **Real adoption:** a pull request by Om that updates LocalMind's token counter from the
   study's results. A merged PR in a live app shows the work is used, not only written up.
7. **A one-page plain-language summary** for applications, linking all of the above.
