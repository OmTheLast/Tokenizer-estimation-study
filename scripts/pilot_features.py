"""Raw-text character measurements; no normalization before raw class counts."""
from collections import Counter
import hashlib
import unicodedata
from localmind_estimator import token_class_index

CLASSES = ['latin', 'sym', 'deva', 'beng', 'guru', 'gujr', 'orya', 'taml', 'telu', 'knda', 'mlym', 'arab', 'cyrl', 'cjk', 'other']


def features(text):
    counts = Counter(token_class_index(ord(ch)) for ch in text)
    points = list(map(ord, text))
    return {
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "characters": len(text), "utf8_bytes": len(text.encode("utf-8")),
        "utf16_units": len(text.encode("utf-16-le")) // 2,
        **{f"class_{name}": counts[i] for i, name in enumerate(CLASSES)},
        "han_named_characters": sum(unicodedata.name(ch, "").startswith(("CJK UNIFIED IDEOGRAPH", "CJK COMPATIBILITY IDEOGRAPH")) for ch in text),
        "kana_block_characters": sum(0x3040 <= p <= 0x30FF for p in points),
        "hangul_syllable_characters": sum(0xAC00 <= p <= 0xD7AF for p in points),
        "hangul_jamo_block_characters": sum(0x1100 <= p <= 0x11FF or 0x3130 <= p <= 0x318F or 0xA960 <= p <= 0xA97F or 0xD7B0 <= p <= 0xD7FF for p in points),
        "cjk_punctuation_block_characters": sum(0x3000 <= p <= 0x303F for p in points),
        "combining_mark_characters": sum(unicodedata.category(ch).startswith("M") for ch in text),
    }
