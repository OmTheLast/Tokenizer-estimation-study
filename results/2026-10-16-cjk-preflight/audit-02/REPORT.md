# CJK practice/exam data check

**Not ready for fitting.** This is an input audit, not an experiment result. No token counts, predictions, fitting or test errors were computed.

## What passed

All requested files were pinned and their checksums verified. Sentence text was extracted directly, without joining annotated words. Exact and near-duplicate checks used the prespecified normalization and 5-gram rule. Simplified/traditional test families were checked by shared parallel IDs.

| Candidate | Upstream set | Sentences | Pass available checks* | Verified original-source groups |
| --- | --- | ---: | ---: | ---: |
| zh_gsd | train | 3997 | 3997 | 0 |
| zh_gsd | dev | 500 | 500 | 0 |
| zh_gsd | test | 500 | 500 | 0 |
| ja_gsd | train | 7050 | 7050 | 0 |
| ja_gsd | dev | 507 | 507 | 0 |
| ja_gsd | test | 543 | 543 | 0 |
| ko_gsd | train | 4400 | 4249 | 0 |
| ko_gsd | dev | 950 | 919 | 0 |
| ko_gsd | test | 989 | 961 | 0 |
| zh_gsdsimp | test | 500 | 500 | 0 |
| yue_hk | test | 1004 | 974 | 4 |

*Passing available checks does not make a row approved for fitting. The document and text-rights gaps below still apply. Duplicate components are not substitutes for original documents.

## What prevents approval

- Original document IDs are absent for Chinese and Korean; Japanese newdoc IDs equal sentence IDs and are not verified source-document identities. The planned document-group isolation and minimum groups cannot be established.
- GSD source documentation distinguishes annotation licensing from underlying-text rights; the design source-text licensing requirement is not cleared.

Japanese newdoc metadata are sentence labels, not evidence of distinct articles. Cantonese has four documented source ranges and remains secondary, never practice data. Readme and licence links for every pinned source are in audit.json; the repository licence label alone does not resolve its source-text caveat.

## Next step

Find recoverable original-document mappings and clarify text provenance, or replace these primary sources with collections that provide those details. Keep the current plan unchanged until a dated amendment is written. Do not weaken the rules merely because the downloaded data fail them. No approved split manifest is created in this round.

## Reproduction

Run `.venv/bin/python scripts/fetch_cjk_candidates.py` to retrieve the pinned acquisition files, then `.venv/bin/python scripts/audit_cjk_candidates.py --output results/cjk-preflight-new`. The audit refuses to overwrite an existing output directory. Raw files stay in ignored .cache/cjk_ud; reports contain IDs, hashes and counts only.
