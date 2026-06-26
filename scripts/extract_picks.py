"""Extract participant picks from scorecard workbooks."""

from __future__ import annotations

import argparse
import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

import openpyxl

try:
    from .bracket_config import MATCH_PICK_CELLS, MATCH_ROUND, ROUND_LABELS, SUPPORT_SHEET_NAMES
except ImportError:
    from bracket_config import MATCH_PICK_CELLS, MATCH_ROUND, ROUND_LABELS, SUPPORT_SHEET_NAMES


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def is_bracket_sheet(sheet: openpyxl.worksheet.worksheet.Worksheet) -> bool:
    title = str(sheet["A1"].value or "").lower()
    has_name = str(sheet["A3"].value or "").strip().lower() == "name" and bool(sheet["B3"].value)
    has_rounds = str(sheet["A8"].value or "").strip().lower() == "round of 32"
    return "pick" in title and has_name and has_rounds


def clean_value(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def extract_workbook(path: Path) -> tuple[list[dict], list[str]]:
    participants: list[dict] = []
    ignored_sheets: list[str] = []

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        workbook = openpyxl.load_workbook(path, data_only=True)

    for sheet_name in workbook.sheetnames:
        sheet = workbook[sheet_name]
        if sheet_name.strip().lower() in SUPPORT_SHEET_NAMES or not is_bracket_sheet(sheet):
            ignored_sheets.append(sheet_name)
            continue

        name = clean_value(sheet["B3"].value) or sheet_name
        picks_by_match: dict[str, dict] = {}
        picks_by_round = {round_key: [] for round_key in ROUND_LABELS}

        for match_number, cell in MATCH_PICK_CELLS.items():
            round_key = MATCH_ROUND[match_number]
            pick = clean_value(sheet[cell].value)
            record = {
                "matchNumber": match_number,
                "round": round_key,
                "roundLabel": ROUND_LABELS[round_key],
                "cell": cell,
                "pick": pick,
            }
            picks_by_match[str(match_number)] = record
            picks_by_round[round_key].append(record)

        participants.append(
            {
                "name": name,
                "sheet": sheet_name,
                "sourceFile": path.name,
                "picks": picks_by_match,
                "picksByRound": picks_by_round,
            }
        )

    return participants, ignored_sheets


def extract_scorecards(scorecards_dir: Path) -> dict:
    paths = sorted(scorecards_dir.glob("*.xlsx"))
    all_participants: list[dict] = []
    sources: list[dict] = []

    for path in paths:
        participants, ignored_sheets = extract_workbook(path)
        all_participants.extend(participants)
        sources.append(
            {
                "file": path.name,
                "participants": [p["name"] for p in participants],
                "ignoredSheets": ignored_sheets,
            }
        )

    all_participants.sort(key=lambda participant: participant["name"].casefold())
    return {
        "generatedAt": utc_now_iso(),
        "participantCount": len(all_participants),
        "sources": sources,
        "matchPickCells": {str(match): cell for match, cell in MATCH_PICK_CELLS.items()},
        "participants": all_participants,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract DLG World Cup pick'em scorecards.")
    parser.add_argument("--scorecards-dir", default="scorecards", type=Path)
    parser.add_argument("--out", default="site/data/picks.json", type=Path)
    args = parser.parse_args()

    data = extract_scorecards(args.scorecards_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.out} with {data['participantCount']} participants.")


if __name__ == "__main__":
    main()
