# Third-party attribution

LocalMind fixture texts and estimator outputs in this study derive from
https://github.com/NakliTechie/LocalMind at
b39f0bc145a0c0926ba22247ee31cd369e0445b6. The original fixture text is preserved
in generated javascript.json files to make Python re-encoding reproducible.
LocalMind source remains in the ignored external/ checkout.

The Python port in scripts/localmind_estimator.py and extracted weights in
config/localmind-profiles.json also derive from the same LocalMind source and
are covered by the attribution below. The port was prepared with Codex assistance.

LocalMind licence:

```text
MIT License

Copyright (c) 2026 Chirag Patnaik

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

The Hugging Face tokenizer assets are downloaded separately into the ignored
.cache/ directory. See config/qwen-tokenizer.lock.json for provenance and licence
limitations. @huggingface/tokenizers and Python tokenizers are separate library
dependencies; their licence files remain in the installed distributions.

## DeepSeek tokenizer assets

Official `deepseek-ai/DeepSeek-V3` and `deepseek-ai/DeepSeek-R1` tokenizer revisions
are pinned in their respective `config/deepseek-*-tokenizer.lock.json` files.
Assets and source notices remain in ignored local caches; no weights are downloaded.
The pinned V3 model card distinguishes its MIT code license from its model license;
the pinned R1 card and LICENSE specify MIT. This repository does not relicense or
redistribute those tokenizer assets. Consult the immutable source-notice URLs in
the locks for the applicable upstream terms.
