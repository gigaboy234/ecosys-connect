import re
from typing import Optional


def validate_url(url: str) -> bool:
    pattern = re.compile(
        r"^https?://"
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|localhost|\d{1,3}(?:\.\d{1,3}){3})"
        r"(?::\d+)?"
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return bool(pattern.match(url))


def validate_year(text: str) -> Optional[int]:
    try:
        year = int(text.strip())
        return year if 1 <= year <= 6 else None
    except ValueError:
        return None


def validate_availability(text: str) -> Optional[int]:
    try:
        hours = int(text.strip())
        return hours if 1 <= hours <= 168 else None
    except ValueError:
        return None


def validate_text_length(text: str, min_len: int = 2, max_len: int = 500) -> bool:
    return min_len <= len(text.strip()) <= max_len


def parse_comma_list(text: str, max_items: int = 10) -> list[str]:
    items = [item.strip() for item in text.split(",") if item.strip()]
    return items[:max_items]
