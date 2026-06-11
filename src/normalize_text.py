import re
import unicodedata


def normalize_text(value: object) -> str:
    """Normalize user/file text for deterministic matching."""
    if value is None:
        return ""
    text = str(value)
    text = text.replace("â‰¥", ">=").replace("≥", ">=").replace("–", "-").replace("—", "-")
    text = unicodedata.normalize("NFKD", text)
    text = text.lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9<>+=/ -]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def strip_population_suffix(text: str) -> str:
    t = normalize_text(text)
    replacements = [
        " among adults", " in adults", " for adults", " adults", " adult",
        " among children", " in children", " for children", " children", " child",
        " self reported", " diagnosis self reported", " diagnosis",
        " measured more detail", " more detail"
    ]
    for rep in replacements:
        t = t.replace(rep, "")
    t = re.sub(r"\s+", " ", t).strip(" :,-")
    return t
