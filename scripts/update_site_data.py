"""Regenerate all JSON files consumed by the static GitHub Pages site."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from extract_picks import extract_scorecards
from fetch_results import build_bracket, fetch_fifa_matches
from score_pickems import build_standings


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Update DLG FIFA World Cup Pickems site data.")
    parser.add_argument("--scorecards-dir", default="scorecards", type=Path)
    parser.add_argument("--site-data-dir", default="site/data", type=Path)
    args = parser.parse_args()

    picks = extract_scorecards(args.scorecards_dir)
    bracket = build_bracket(fetch_fifa_matches())
    standings = build_standings(picks, bracket)

    write_json(args.site_data_dir / "picks.json", picks)
    write_json(args.site_data_dir / "bracket.json", bracket)
    write_json(args.site_data_dir / "standings.json", standings)

    print(f"Updated {standings['participantCount']} participants.")
    print(f"Top three: {', '.join(row['name'] for row in standings['topThree'])}")


if __name__ == "__main__":
    main()

