"""Team-name normalization used for comparing picks to official FIFA results."""

from __future__ import annotations

import re
import unicodedata


ALIASES = {
    "bosnia herzegovina": "bosnia and herzegovina",
    "bosnia and herzegovina": "bosnia and herzegovina",
    "cabo verde": "cape verde",
    "cape verde": "cape verde",
    "congo dr": "dr congo",
    "dr congo": "dr congo",
    "democratic republic of the congo": "dr congo",
    "cote divoire": "ivory coast",
    "cote d ivoire": "ivory coast",
    "columbia": "colombia",
    "ivory coast": "ivory coast",
    "ir iran": "iran",
    "iran": "iran",
    "korea republic": "south korea",
    "republic of korea": "south korea",
    "south korea": "south korea",
    "usa": "united states",
    "u s a": "united states",
    "united states": "united states",
    "united states of america": "united states",
}


def normalize_team_name(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    if not text:
        return ""

    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return ALIASES.get(text, text)


def same_team(left: object, right: object) -> bool:
    return normalize_team_name(left) == normalize_team_name(right)
