# Reading token pieces and reconstruction

These examples were authored for this study and selected before counting.
Full IDs, tokenizer pieces, normalized strings and decoded strings are in [token-examples.json](run-01/token-examples.json).

## Indentation probe

Original:
```python
def ready():
    return True
```

| Profile | Token count | Decoded text (JSON escaping shows spaces/newlines) |
| --- | ---: | --- |
| qwen35-4b | 8 | `"def ready():\n    return True\n"` |
| bonsai-ternary-4b | 7 | `"def ready():\n    return True\n"` |
| lfm2-1.2b | 7 | `"def ready():\n    return True\n"` |
| gemma4-e2b | 8 | `"def ready():\n    return True\n"` |
| minicpm5-2b-gguf | 7 | `"def ready():\n    return True\n"` |
| xlm-roberta-base | 7 | `"def ready(): return True"` |

XLM-R changes the layout here; this particular one-line function can retain its behavior.
An exact-text mismatch is not automatically semantic damage. Code with other structures needs its own checks.

## Unknown characters

| Probe | XLM-R original | XLM-R decoded | Unknown token count |
| --- | --- | --- | ---: |
| probe/emoji | Status: ready ✅ 🧪 🚀. | `Status: ready ✅ <unk> 🚀.` | 1 |
| probe/rare_characters | Symbols: 𠮷 𓀀. | `Symbols: <unk> <unk>.` | 2 |

The other five profiles produced no unknown tokens on these probes. None of the six profiles
produced unknown tokens on the 180 primary fixtures. This is sample coverage, not universal coverage.

## Pieces for a short English probe

The ASCII probe is `A = 1\nB = 2\n`. Piece spellings are vocabulary notation,
not always literal source characters. Read decoded text alongside pieces.

- **qwen35-4b**: `["A", "Ġ=", "Ġ", "1", "Ċ", "B", "Ġ=", "Ġ", "2", "Ċ"]`
- **bonsai-ternary-4b**: `["A", "Ġ=", "Ġ", "1", "Ċ", "B", "Ġ=", "Ġ", "2", "Ċ"]`
- **lfm2-1.2b**: `["A", "Ġ=", "Ġ", "1", "Ċ", "B", "Ġ=", "Ġ", "2", "Ċ"]`
- **gemma4-e2b**: `["A", "▁=", "▁", "1", "\n", "B", "▁=", "▁", "2", "\n"]`
- **minicpm5-2b-gguf**: `["A", "Ġ=", "Ġ", "1", "Ċ", "B", "Ġ=", "Ġ", "2", "Ċ"]`
- **xlm-roberta-base**: `["▁A", "▁=", "▁1", "▁B", "▁=", "▁2"]`
