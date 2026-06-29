"""Bracket and scorecard layout configuration for DLG FIFA World Cup Pickems."""

from __future__ import annotations

from collections import OrderedDict

FIFA_COMPETITION_ID = "17"
FIFA_2026_SEASON_ID = "285023"
FIFA_MATCHES_URL = (
    "https://api.fifa.com/api/v3/calendar/matches"
    f"?language=en&count=200&idCompetition={FIFA_COMPETITION_ID}&idSeason={FIFA_2026_SEASON_ID}"
)

SUPPORT_SHEET_NAMES = {
    "results",
    "teams",
    "research notes",
    "top 32 projection",
    "setup",
}

ROUND_LABELS = {
    "round_of_32": "Round of 32",
    "round_of_16": "Round of 16",
    "quarterfinals": "Quarterfinals",
    "semifinals": "Semifinals",
    "final": "Final",
}

ROUND_WEIGHTS = {
    "round_of_32": 1,
    "round_of_16": 2,
    "quarterfinals": 4,
    "semifinals": 8,
    "final": 16,
}

ROUND_BY_STAGE = {
    "Round of 32": "round_of_32",
    "Round of 16": "round_of_16",
    "Quarter-final": "quarterfinals",
    "Quarterfinals": "quarterfinals",
    "Semi-final": "semifinals",
    "Semifinals": "semifinals",
    "Final": "final",
}

# The workbook's visual bracket order is not strictly numeric by FIFA match number.
# These coordinates are the submitted winner-pick cells, mapped to official FIFA match numbers.
MATCH_PICK_CELLS = OrderedDict(
    [
        # Round of 32
        (74, "C9"),
        (77, "C11"),
        (73, "C13"),
        (75, "C15"),
        (83, "C17"),
        (84, "C19"),
        (81, "C21"),
        (82, "C23"),
        (76, "C25"),
        (78, "C27"),
        (79, "C29"),
        (80, "C31"),
        (86, "C33"),
        (88, "C35"),
        (85, "C37"),
        (87, "C39"),
        # Round of 16
        (89, "D10"),
        (90, "D14"),
        (93, "D18"),
        (94, "D22"),
        (91, "D26"),
        (92, "D30"),
        (95, "D34"),
        (96, "D38"),
        # Quarterfinals
        (97, "E11"),
        (98, "E19"),
        (99, "E27"),
        (100, "E35"),
        # Semifinals
        (101, "F14"),
        (102, "F30"),
        # Champion
        (104, "G19"),
    ]
)

BRACKET_ROUND_ORDER = OrderedDict(
    [
        # Public bracket progression order. MATCH_PICK_CELLS above keeps the workbook cells
        # mapped to their official match numbers, even though the sheet order differs.
        ("round_of_32", [74, 77, 73, 75, 83, 84, 81, 82, 76, 78, 79, 80, 86, 88, 85, 87]),
        ("round_of_16", [89, 90, 93, 94, 91, 92, 95, 96]),
        ("quarterfinals", [97, 98, 99, 100]),
        ("semifinals", [101, 102]),
        ("final", [104]),
    ]
)

MATCH_ROUND = {}
for round_key, match_numbers in BRACKET_ROUND_ORDER.items():
    for match_number in match_numbers:
        MATCH_ROUND[match_number] = round_key
