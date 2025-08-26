# game/utils.py
import re
import unicodedata
from difflib import SequenceMatcher

UMLAUT_MAP = {
    "ä": "ae",
    "ö": "oe",
    "ü": "ue",
    "ß": "ss",
}

def normalize_text(s: str) -> str:
    """
    Normalisiert Eingaben für robustes Matching:
    - whitespace trim + collapse
    - lower
    - Umlaute & ß zu ae/oe/ue/ss
    - diacritics entfernen (é -> e)
    - nur alphanum + Leerzeichen (bindestriche zu Leerzeichen)
    """
    if not s:
        return ""
    s = s.strip().lower()
    s = s.replace("-", " ")

    # Umlaute/ß Mapping
    for k, v in UMLAUT_MAP.items():
        s = s.replace(k, v)

    # diacritics entfernen (NFKD + ASCII)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))

    # nur a-z0-9 + space
    s = re.sub(r"[^a-z0-9 ]+", "", s)
    # mehrfach spaces -> single
    s = re.sub(r"\s+", " ", s).strip()
    return s

def first_letter_upper(s: str) -> str:
    """
    Bestimmt den Anfangsbuchstaben (A–Z) des normalisierten Strings,
    sonst '' (leer).
    """
    s = normalize_text(s)
    return s[0].upper() if s else ""

def similarity(a: str, b: str) -> float:
    """
    Ähnlichkeit in [0, 1] mit difflib.
    """
    na = normalize_text(a)
    nb = normalize_text(b)
    if not na or not nb:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()
