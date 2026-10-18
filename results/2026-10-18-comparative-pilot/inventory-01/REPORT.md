# Inventory of the five pinned tokenizer profiles

Generated from cached, hash-verified assets; no new tokenizer download or text encoding.

| Profile | Algorithm in JSON | Base vocabulary | Effective vocabulary | Added records marked special | Merge rules |
| --- | --- | ---: | ---: | ---: | ---: |
| Qwen | BPE | 248,044 | 248,077 | 21 | 247,587 |
| Bonsai | BPE | 151,643 | 151,669 | 14 | 151,387 |
| LFM | BPE | 64,400 | 64,402 | 503 | 63,683 |
| Gemma | BPE | 262,144 | 262,144 | 24 | 514,906 |
| MiniCPM* | BPE | 130,072 | 130,560 | 30 | 129,794 |

Base vocabulary counts entries in the tokenizer model. Effective vocabulary counts the union
of base and added-token strings; an added record can refer to an existing base entry.
Special-token records are not tokens automatically appended to every input.
*MiniCPM is the pinned HF JSON asset; GGUF/browser equivalence is unverified.

## Processing stages

### Qwen

Source: `onnx-community/Qwen3.5-4B-ONNX-OPT` at `57b13b4dce7be073be0df3eaf1c842a6bbb2e0a7`.

- [tokenizer.json](https://huggingface.co/onnx-community/Qwen3.5-4B-ONNX-OPT/resolve/57b13b4dce7be073be0df3eaf1c842a6bbb2e0a7/tokenizer.json): `89da80cc6689bef4d90cc1028249436975ffb0814618f1d93c65310e05801a9b`
- [tokenizer_config.json](https://huggingface.co/onnx-community/Qwen3.5-4B-ONNX-OPT/resolve/57b13b4dce7be073be0df3eaf1c842a6bbb2e0a7/tokenizer_config.json): `2de621ec071dd61438efdd6d0183bd3d612e98d05ac10d19ed75f1fef9299bc9`

- normalizer: NFC
- pre_tokenizer: Sequence(Split, ByteLevel)
- post_processor: ByteLevel
- decoder: ByteLevel
- Model options: `{"type": "BPE", "dropout": null, "unk_token": null, "continuing_subword_prefix": "", "end_of_word_suffix": "", "fuse_unk": false, "byte_fallback": false, "ignore_merges": false}`
- Wrapper settings explicitly present: `{"tokenizer_class": "TokenizersBackend", "clean_up_tokenization_spaces": false, "split_special_tokens": false}`
- Chat template present: True; pilot inserts special tokens: False.

### Bonsai

Source: `onnx-community/Ternary-Bonsai-4B-ONNX` at `9d085aaf786063cadb648fff1725c2c36fd28ade`.

- [tokenizer.json](https://huggingface.co/onnx-community/Ternary-Bonsai-4B-ONNX/resolve/9d085aaf786063cadb648fff1725c2c36fd28ade/tokenizer.json): `40ae5d1ee027b985684a3bbeef4ee16b2b5697d1d90658bec5bc5d2a73018bd7`
- [tokenizer_config.json](https://huggingface.co/onnx-community/Ternary-Bonsai-4B-ONNX/resolve/9d085aaf786063cadb648fff1725c2c36fd28ade/tokenizer_config.json): `a8342e0e0e791a478f628dd1adf825ab1f9afe4a1075959ad32d77f1318b9841`

- normalizer: NFC
- pre_tokenizer: Sequence(Split, ByteLevel)
- post_processor: ByteLevel
- decoder: ByteLevel
- Model options: `{"type": "BPE", "dropout": null, "unk_token": null, "continuing_subword_prefix": "", "end_of_word_suffix": "", "fuse_unk": false, "byte_fallback": false, "ignore_merges": false}`
- Wrapper settings explicitly present: `{"tokenizer_class": "Qwen2Tokenizer", "clean_up_tokenization_spaces": false, "split_special_tokens": false}`
- Chat template present: True; pilot inserts special tokens: False.

### LFM

Source: `LiquidAI/LFM2.5-1.2B-Instruct-ONNX` at `10f72e70abf67ac0fd7ebf15bc5854726891d864`.

- [tokenizer.json](https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct-ONNX/resolve/10f72e70abf67ac0fd7ebf15bc5854726891d864/tokenizer.json): `0a1f2cb9fc2769030ca1f4207e81c1af493319373d41b8d3cf5be53860c13760`
- [tokenizer_config.json](https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct-ONNX/resolve/10f72e70abf67ac0fd7ebf15bc5854726891d864/tokenizer_config.json): `0f11f4ffa5750369414bb24e41f26e2bbf23f1d01def533cad5f584e59ae3bef`
- [LICENSE](https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct-ONNX/resolve/10f72e70abf67ac0fd7ebf15bc5854726891d864/LICENSE): `5188f2b355da20647257a3156db5834c794e5fb5e6d8dc4d4cdbb3180e75b85b`

- normalizer: None
- pre_tokenizer: Sequence(Split, ByteLevel)
- post_processor: Sequence(ByteLevel, TemplateProcessing)
- decoder: Sequence(ByteLevel)
- Model options: `{"type": "BPE", "dropout": null, "unk_token": null, "continuing_subword_prefix": null, "end_of_word_suffix": null, "fuse_unk": false, "byte_fallback": false, "ignore_merges": false}`
- Wrapper settings explicitly present: `{"tokenizer_class": "TokenizersBackend", "clean_up_tokenization_spaces": false}`
- Chat template present: True; pilot inserts special tokens: False.

### Gemma

Source: `onnx-community/gemma-4-E2B-it-ONNX` at `9f4bef82ea6e296bc69f8a2f5939f73af81b07a6`.

- [tokenizer.json](https://huggingface.co/onnx-community/gemma-4-E2B-it-ONNX/resolve/9f4bef82ea6e296bc69f8a2f5939f73af81b07a6/tokenizer.json): `47bd35616c7c782aaca6ccf48c75f3461d5877170984b8836b375107d0a9f566`
- [tokenizer_config.json](https://huggingface.co/onnx-community/gemma-4-E2B-it-ONNX/resolve/9f4bef82ea6e296bc69f8a2f5939f73af81b07a6/tokenizer_config.json): `06afbf54e228050cba79c4a0afd83543cc89070a2d62b8337d0aa8b4cdc348c3`

- normalizer: Replace
- pre_tokenizer: Split
- post_processor: TemplateProcessing
- decoder: Sequence(Replace, ByteFallback, Fuse)
- Model options: `{"type": "BPE", "dropout": null, "unk_token": "<unk>", "continuing_subword_prefix": null, "end_of_word_suffix": null, "fuse_unk": true, "byte_fallback": true, "ignore_merges": false}`
- Wrapper settings explicitly present: `{"tokenizer_class": "GemmaTokenizer"}`
- Chat template present: True; pilot inserts special tokens: False.

### MiniCPM*

Source: `openbmb/MiniCPM5-2B` at `12a3808a956f869c767195e9266b59c4d21d92e2`.

- [tokenizer.json](https://huggingface.co/openbmb/MiniCPM5-2B/resolve/12a3808a956f869c767195e9266b59c4d21d92e2/tokenizer.json): `3e065a558a034185fe299917b398685c1facd0169a9eea1e629eb30c171fed81`
- [tokenizer_config.json](https://huggingface.co/openbmb/MiniCPM5-2B/resolve/12a3808a956f869c767195e9266b59c4d21d92e2/tokenizer_config.json): `e9b1064649e771d7a8e15637c68b2d2749724877ba3648bd74a4ece31c26303b`

- normalizer: None
- pre_tokenizer: Sequence(Split, Split, ByteLevel)
- post_processor: TemplateProcessing
- decoder: ByteLevel
- Model options: `{"type": "BPE", "dropout": null, "unk_token": "<unk>", "continuing_subword_prefix": null, "end_of_word_suffix": null, "fuse_unk": false, "byte_fallback": false, "ignore_merges": false}`
- Wrapper settings explicitly present: `{"tokenizer_class": "PreTrainedTokenizerFast", "add_bos_token": false, "add_eos_token": false, "clean_up_tokenization_spaces": false}`
- Chat template present: False; pilot inserts special tokens: False.

## What can be called a family here?

Observed algorithm classes: BPE.
Distinct serialized pipeline fingerprints: 5 of 5.
These are separate profiles, not five proven historical families. Identical algorithm labels
do not mean identical vocabulary, preprocessing or counts. The JSON report lists component
equalities for all ten unordered pairs; matching null components are not lineage evidence.
A cross-algorithm comparison needs additional representatives if only one class is present.

## Verification and limits

Verified 11 files against existing locks and checked base/effective vocabulary
sizes against the pinned tokenizer runtime. Full configurations for processing stages (with
very large strings represented by length and hash) and component fingerprints are in
[inventory.json](inventory.json). Vocabularies and third-party asset files are not republished.
Asset fingerprints describe serialized configuration, not lineage or runtime equivalence. Missing wrapper fields are unspecified, not false. Special-token settings do not describe full chat-template overhead.
