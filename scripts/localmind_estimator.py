"""Python port of LocalMind b39f0bc's estimator for text strings and None.

Weights are extracted unchanged from the pinned upstream source. This is a port,
not a newly fitted predictor. See THIRD_PARTY_NOTICES.md for MIT attribution.
"""
import json
import math
from pathlib import Path

PROFILE = Path(__file__).resolve().parents[1] / "config/localmind-profiles.json"


def token_class_index(cp):
    if cp < 0x80:
        return 0 if 65 <= cp <= 90 or 97 <= cp <= 122 or cp == 32 else 1
    if cp <= 0x24F:
        return 0
    for low, high, index in [
        (0x0400, 0x052F, 12), (0x0600, 0x06FF, 11),
        (0x0900, 0x097F, 2), (0x0980, 0x09FF, 3), (0x0A00, 0x0A7F, 4),
        (0x0A80, 0x0AFF, 5), (0x0B00, 0x0B7F, 6), (0x0B80, 0x0BFF, 7),
        (0x0C00, 0x0C7F, 8), (0x0C80, 0x0CFF, 9), (0x0D00, 0x0D7F, 10),
        (0x3040, 0x30FF, 13), (0x3400, 0x4DBF, 13),
        (0x4E00, 0x9FFF, 13), (0xAC00, 0xD7AF, 13),
    ]:
        if low <= cp <= high:
            return index
    return 14


class LocalMindEstimator:
    def __init__(self, profiles=None):
        self.profiles = profiles if profiles is not None else json.loads(PROFILE.read_text())

    def count_tokens(self, text, model_key):
        if text is None or text == "":
            return 0
        if not isinstance(text, str):
            raise TypeError("This research port accepts str or None, not JavaScript object coercion")
        name = self.profiles["model_profiles"].get(model_key, "unknown")
        weights = self.profiles["weights"][name]
        total = 0.0
        i = 0
        while i < len(text):
            cp = ord(text[i])
            # Also match JS codePointAt for explicit UTF-16 surrogate pairs.
            if 0xD800 <= cp <= 0xDBFF and i + 1 < len(text):
                low = ord(text[i + 1])
                if 0xDC00 <= low <= 0xDFFF:
                    cp = 0x10000 + ((cp - 0xD800) << 10) + low - 0xDC00
                    i += 1
            # Preserve JS left-to-right binary64 addition, not Python's sum().
            total += weights[token_class_index(cp)]
            i += 1
        return math.ceil(total)
