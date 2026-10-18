# Source design checkpoint — 2026-10-18

**Design completed; corpus collection and tokenization not started.**

Seven source repositories are pinned to exact commits. The metadata audit found
2,129 path-matching files across ten source/language strata. These are candidate
paths, not 2,129 eligible texts or measurements. Content, length, duplication and
file-specific terms still need checking during collection.

| Category / stratum | Path candidates | Target samples |
| --- | ---: | ---: |
| prose / english_cpython | 346 | 10 |
| code / python | 765 | 10 |
| prose / english_node | 70 | 10 |
| code / javascript | 431 | 10 |
| json / npm_package | 12 | 10 |
| json / vscode_extension | 96 | 10 |
| html / mdn_dom | 199 | 10 |
| html / mdn_learning | 154 | 10 |
| mixed / hindi_english | 28 | 10 |
| mixed / tamil_english | 28 | 10 |

The npm quota has only twelve path candidates for ten slots. A content or duplicate
shortfall must be reported, not filled with unplanned files. The Hindi/Tamil pools
contain translations of the same 28 lesson paths: we will select at most one
language per lesson, aiming for twenty different lessons. Eligibility is unverified.

## Source versions and primary evidence

| Repository | Pinned revision | Root terms inspected |
| --- | --- | --- |
| [python/cpython](https://github.com/python/cpython/tree/b953155e0d64b143546dd47554983fb73cfa6d1a) | `b953155e0d64` | [PSF license and historical notices](https://github.com/python/cpython/blob/b953155e0d64b143546dd47554983fb73cfa6d1a/LICENSE) |
| [nodejs/node](https://github.com/nodejs/node/tree/e2d55227730b77802c142519b7ef04487604cff3) | `e2d55227730b` | [MIT for Node-originated parts; separate third-party notices](https://github.com/nodejs/node/blob/e2d55227730b77802c142519b7ef04487604cff3/LICENSE) |
| [npm/cli](https://github.com/npm/cli/tree/ae98c62586b6fea44114f72e249e246a2981de70) | `ae98c62586b6` | [Artistic-2.0 for npm application; separate dependencies](https://github.com/npm/cli/blob/ae98c62586b6fea44114f72e249e246a2981de70/LICENSE) |
| [microsoft/vscode](https://github.com/microsoft/vscode/tree/00ab0906bad641d5be1d009da16baa5cec66a161) | `00ab0906bad6` | [MIT; check file-level exceptions](https://github.com/microsoft/vscode/blob/00ab0906bad641d5be1d009da16baa5cec66a161/LICENSE.txt) |
| [mdn/dom-examples](https://github.com/mdn/dom-examples/tree/93d7d40c7b14dc0dd208d4967905606339e1f0e6) | `93d7d40c7b14` | [CC0-1.0](https://github.com/mdn/dom-examples/blob/93d7d40c7b14dc0dd208d4967905606339e1f0e6/LICENSE) |
| [mdn/learning-area](https://github.com/mdn/learning-area/tree/d55e1c2e3ff401519811b64e5b2a7d3643b43d0f) | `d55e1c2e3ff4` | [CC0-1.0](https://github.com/mdn/learning-area/blob/d55e1c2e3ff401519811b64e5b2a7d3643b43d0f/LICENSE) |
| [microsoft/ML-For-Beginners](https://github.com/microsoft/ML-For-Beginners/tree/de2d4e12236445198213a0711855e348e7253cd4) | `de2d4e122364` | [MIT; automatic translations explicitly disclosed](https://github.com/microsoft/ML-For-Beginners/blob/de2d4e12236445198213a0711855e348e7253cd4/LICENSE) |

[Microsoft translation provenance](https://github.com/microsoft/ML-For-Beginners/blob/de2d4e12236445198213a0711855e348e7253cd4/README.md)
explicitly identifies automatic translation support. The mixed group is technical
documentation containing multiple scripts, not ordinary conversation. Both HTML
sources belong to MDN. These limitations will carry forward into the results.

## Reproducible checks

- Verified each commit-to-tree relationship and non-truncated recursive tree.
- Verified all seven root-license hashes and the translation-provenance README hash.
- Verified protocol and existing tokenizer-configuration hashes.
- Checked ten quotas sum to 100, with 20 per category; no samples selected.
- Produced deterministic path ranks and an inventory with Git blob IDs and byte sizes.

Artifacts: [source lock](../../config/published-text-sources-v1.json),
[path inventory](../../references/published-text-source-inventory-v1.json),
[machine-readable metadata check](metadata-check.json), and
[sampling protocol](../../docs/PUBLISHED_TEXT_SAMPLING_V1.md).

Reproduce from the project root (network needed only with `--fetch`):

```sh
python3 scripts/inspect_published_sources.py --fetch --output /tmp/published-source-inventory-reproduced.json
```

The output path must not exist. Fetching uses pinned commits/trees, not current
branch tips; only metadata, root licenses and translation README evidence are
downloaded by this script. Compare the output SHA-256 with `metadata-check.json`.
The ignored cache is not included in GitHub history.

## Next action

Implement the corpus collector and paragraph-boundary checks; review eligibility
and applicable file terms in ranked order; save exclusions and any shortfalls.
Commit the final sample manifest and sampler before measuring. Graphs follow
actual measurements. No new counts, fitting, inference, browser trials or FLORES+
devtest access occurred in this round.
