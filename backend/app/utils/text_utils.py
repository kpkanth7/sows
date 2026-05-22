import re


def canonicalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def compact_text(value: str | None, max_length: int = 5000) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()[:max_length]
