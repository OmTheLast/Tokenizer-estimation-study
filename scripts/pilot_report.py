"""Generate pilot summaries/figures from numeric measurements only."""
from collections import defaultdict
import json
import statistics
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from verify_all_profiles import save

LABELS = {"qwen35-4b": "Qwen", "bonsai-ternary-4b": "Bonsai", "lfm2-1.2b": "LFM", "gemma4-e2b": "Gemma", "minicpm5-2b-gguf": "MiniCPM*"}


def metrics(rows):
    errors = [r['error_percent'] for r in rows if r['error_percent'] is not None]
    return {"rows": len(rows), "total_tokens": sum(r['token_count'] for r in rows),
            "tokens_per_character": sum(r['token_count'] for r in rows) / sum(r['characters'] for r in rows),
            "median_absolute_error_percent": statistics.median(abs(e) for e in errors),
            "minimum_error_percent": min(errors), "maximum_error_percent": max(errors),
            "within_20_percent_count": sum(abs(e) <= 20 for e in errors),
            "undercount_count": sum(e < 0 for e in errors)}


def write_report(out, rows, smoke):
    cells, groups, models = defaultdict(list), defaultdict(list), defaultdict(list)
    for row in rows:
        cells[(row['model_key'], row['language'])].append(row)
        groups[(row['model_key'], row['group'])].append(row)
        models[row['model_key']].append(row)
    cell_metrics = [{"model_key": m, "language": lang, "label": cell[0]['language_label'], **metrics(cell)} for (m, lang), cell in cells.items()]
    group_metrics = [{"model_key": m, "group": group, **metrics(cell)} for (m, group), cell in groups.items()]
    model_metrics = {m: metrics(cell) for m, cell in models.items()}
    gaps = []
    for lang in dict.fromkeys(r['language'] for r in rows):
        entries = [c for c in cell_metrics if c['language'] == lang]
        low, high = min(entries, key=lambda c: c['total_tokens']), max(entries, key=lambda c: c['total_tokens'])
        gaps.append({"language": lang, "label": low['label'], "lowest_model": low['model_key'], "highest_model": high['model_key'],
                     "lowest_total_tokens": low['total_tokens'], "highest_total_tokens": high['total_tokens'],
                     "ratio_high_to_low": high['total_tokens'] / low['total_tokens']})
    gaps.sort(key=lambda g: (-g['ratio_high_to_low'], g['language']))
    save(out / "summary.json", {"smoke_only": smoke, "rows": len(rows), "models": model_metrics, "cells": cell_metrics, "groups": group_metrics, "largest_gaps": gaps[:10]})
    language_order = list(dict.fromkeys(r['language'] for r in rows))
    model_order = list(models)
    matrix = np.array([[next(c['tokens_per_character'] for c in cell_metrics if c['language'] == lang and c['model_key'] == m) for lang in language_order] for m in model_order])
    language_labels = [next(r['language_label'] for r in rows if r['language'] == lang) for lang in language_order]
    fig, ax = plt.subplots(figsize=(max(9, len(language_order) * 0.68), 4.8), layout='constrained')
    plot = ax.imshow(matrix, cmap='YlOrRd', aspect='auto', vmin=0)
    ax.set_xticks(range(len(language_order)), labels=language_labels, rotation=55, ha='right')
    ax.set_yticks(range(len(model_order)), labels=[LABELS[m] for m in model_order])
    for i in range(len(model_order)):
        for j in range(len(language_order)):
            ax.text(j, i, f'{matrix[i,j]:.2f}', ha='center', va='center', fontsize=8,
                    color='white' if matrix[i,j] > matrix.max() * 0.65 else '#242424')
    ax.set_title('SMOKE TEST — existing fixtures, not new evidence' if smoke else 'FLORES+ dev pilot: content tokens per Unicode character', pad=18)
    fig.colorbar(plot, ax=ax, label='Total tokens / total Unicode code points')
    fig.supxlabel('*MiniCPM uses HF JSON tokenizer; full chat overhead excluded.', fontsize=9)
    fig.savefig(out / 'tokens-per-character.png', dpi=180)
    fig.savefig(out / 'tokens-per-character.svg')
    plt.close(fig)
    title = 'Pipeline smoke test — not a multilingual pilot result' if smoke else 'Multilingual measurement pilot'
    lines = [f'# {title}', '',
             'This run uses existing LocalMind fixtures only to verify the pipeline. It adds no unseen-text evidence.' if smoke else 'Five frozen tokenizers and the unchanged LocalMind estimator, measured on 100 aligned dev sentence IDs across 18 language varieties. No fitting or calibration; devtest was not downloaded.', '',
             f'Numeric measurement rows: **{len(rows)}**. Raw texts and token IDs are excluded from the result table.', '',
             '![Tokens per character](tokens-per-character.png)', '',
             'Each cell is the sum of content tokens divided by the sum of Unicode code points. It is not a word count or a measure of model quality. Comparisons within a language use identical text.', '',
             '| Tokenizer | Median absolute prediction error | Worst under | Worst over | Within ±20% |',
             '| --- | ---: | ---: | ---: | ---: |']
    for m, s in model_metrics.items():
        lines.append(f"| {LABELS[m]} | {s['median_absolute_error_percent']:.2f}% | {s['minimum_error_percent']:+.2f}% | {s['maximum_error_percent']:+.2f}% | {s['within_20_percent_count']}/{s['rows']} |")
    lines.extend(['', '## Indian, CJK and other groups', '', '| Tokenizer | Group | Rows | Median absolute error | Within ±20% |', '| --- | --- | ---: | ---: | ---: |'])
    for s in group_metrics:
        lines.append(f"| {LABELS[s['model_key']]} | {s['group']} | {s['rows']} | {s['median_absolute_error_percent']:.2f}% | {s['within_20_percent_count']}/{s['rows']} |")
    lines.extend(['', '## Largest tokenizer gaps within a language', '', 'Ratio of the largest total token count to the smallest total count on that language’s same selected sentences. This compares tokenizers, not translations of different lengths.', '', '| Language | Most tokens | Fewest tokens | Ratio |', '| --- | --- | --- | ---: |'])
    for g in gaps[:10]:
        lines.append(f"| {g['label']} | {LABELS[g['highest_model']]} | {LABELS[g['lowest_model']]} | {g['ratio_high_to_low']:.2f}× |")
    lines.extend(['', '## Limits', '',
                  'The original LocalMind fitting corpus is not fully available, so absence of overlap with all its training examples cannot be proven. We check overlap with its 38 published fixtures. Model-training exposure to FLORES is not assessed. The dataset is evaluation-only; any new estimator must be fitted on separate text.', '',
                  'No model inference, new fitting, full chat templates, context-overflow simulation or browser benchmark was run. The pre-token count is a diagnostic of the tokenizer’s pre-tokenizer applied after its normalizer; added-token extraction is not emulated at that stage. Content-token counts use the full tokenizer with added special tokens disabled.', '',
                  'The pilot is smaller than the planned full study (20+ tokenizers and broader language coverage). See run.json, validation.json, summary.json and the local ground-truth.parquet. Downloaded text remains in the ignored cache; FLORES+ attribution and use conditions are in docs/PHASE1_PILOT.md.', ''])
    (out / 'REPORT.md').write_text('\n'.join(lines))
