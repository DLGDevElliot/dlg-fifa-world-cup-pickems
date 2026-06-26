"""Fetch official FIFA World Cup 2026 match data and shape it for the website."""

from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    from .bracket_config import BRACKET_ROUND_ORDER, FIFA_MATCHES_URL, ROUND_BY_STAGE, ROUND_LABELS
except ImportError:
    from bracket_config import BRACKET_ROUND_ORDER, FIFA_MATCHES_URL, ROUND_BY_STAGE, ROUND_LABELS


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def localized_description(items: list[dict] | None) -> str:
    if not items:
        return ""
    for item in items:
        if item.get("Locale", "").lower().startswith("en"):
            return item.get("Description", "") or ""
    return items[0].get("Description", "") or ""


def team_from_fifa(team: dict | None) -> dict | None:
    if not team:
        return None
    return {
        "id": team.get("IdTeam"),
        "name": team.get("ShortClubName") or localized_description(team.get("TeamName")),
        "displayName": localized_description(team.get("TeamName")) or team.get("ShortClubName"),
        "abbreviation": team.get("Abbreviation"),
        "countryCode": team.get("IdCountry"),
    }


def winner_name(match: dict, home: dict | None, away: dict | None) -> str:
    winner_id = str(match.get("Winner") or "")
    if not winner_id:
        return ""
    if home and str(home.get("id")) == winner_id:
        return home.get("name") or home.get("displayName") or ""
    if away and str(away.get("id")) == winner_id:
        return away.get("name") or away.get("displayName") or ""
    return ""


def match_status(match: dict) -> str:
    home_score = match.get("HomeTeamScore")
    away_score = match.get("AwayTeamScore")
    if home_score is not None and away_score is not None and match.get("MatchStatus") == 0:
        return "completed"
    if match.get("MatchStatus") == 1:
        return "scheduled"
    return "live"


def shape_match(match: dict) -> dict:
    stage_name = localized_description(match.get("StageName"))
    round_key = ROUND_BY_STAGE.get(stage_name)
    home = team_from_fifa(match.get("Home"))
    away = team_from_fifa(match.get("Away"))
    stadium = match.get("Stadium") or {}
    match_number = int(match["MatchNumber"])

    return {
        "matchNumber": match_number,
        "id": match.get("IdMatch"),
        "round": round_key,
        "roundLabel": ROUND_LABELS.get(round_key, stage_name),
        "stageName": stage_name,
        "date": match.get("Date"),
        "localDate": match.get("LocalDate"),
        "status": match_status(match),
        "home": home,
        "away": away,
        "placeholderA": match.get("PlaceHolderA"),
        "placeholderB": match.get("PlaceHolderB"),
        "score": {
            "home": match.get("HomeTeamScore"),
            "away": match.get("AwayTeamScore"),
            "homePenalty": match.get("HomeTeamPenaltyScore"),
            "awayPenalty": match.get("AwayTeamPenaltyScore"),
        },
        "winnerId": match.get("Winner"),
        "winner": winner_name(match, home, away),
        "venue": localized_description(stadium.get("Name")),
        "city": localized_description(stadium.get("CityName")),
        "country": stadium.get("IdCountry"),
    }


def winner_team(match: dict) -> dict | None:
    winner_id = str(match.get("winnerId") or "")
    if not winner_id:
        return None
    for side in ("home", "away"):
        team = match.get(side)
        if team and str(team.get("id")) == winner_id:
            return team
    if match.get("winner"):
        return {"id": winner_id, "name": match["winner"], "displayName": match["winner"], "abbreviation": ""}
    return None


def resolve_team_placeholder(placeholder: str | None, matches_by_number: dict[int, dict]) -> dict | None:
    if not placeholder:
        return None
    match = re.fullmatch(r"W(\d+)", str(placeholder).strip())
    if not match:
        return None
    previous = matches_by_number.get(int(match.group(1)))
    if not previous or previous.get("status") != "completed":
        return None
    return winner_team(previous)


def resolve_knockout_progression(knockout: dict[int, dict]) -> None:
    for match_number in sorted(knockout):
        match = knockout[match_number]
        if not match.get("home"):
            match["home"] = resolve_team_placeholder(match.get("placeholderA"), knockout)
        if not match.get("away"):
            match["away"] = resolve_team_placeholder(match.get("placeholderB"), knockout)


def fetch_fifa_matches() -> list[dict]:
    request = urllib.request.Request(FIFA_MATCHES_URL, headers={"User-Agent": "DLG-Pickems/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not fetch FIFA match data: {exc}") from exc
    matches = payload.get("Results", [])
    validate_fifa_payload(matches)
    return matches


def validate_fifa_payload(matches: list[dict]) -> None:
    match_numbers = [match.get("MatchNumber") for match in matches if match.get("MatchNumber")]
    unique_numbers = set(match_numbers)
    if len(matches) != 104 or len(unique_numbers) != 104:
        raise RuntimeError(
            f"FIFA payload sanity check failed: expected 104 unique matches, "
            f"got {len(matches)} rows and {len(unique_numbers)} unique match numbers."
        )

    required_knockout_matches = set(range(73, 105))
    missing = required_knockout_matches - {int(number) for number in unique_numbers}
    if missing:
        raise RuntimeError(f"FIFA payload is missing knockout match numbers: {sorted(missing)}")

    by_number = {int(match["MatchNumber"]): match for match in matches if match.get("MatchNumber")}
    expected_placeholders = {
        97: ("W89", "W90"),
        98: ("W93", "W94"),
        99: ("W91", "W92"),
        100: ("W95", "W96"),
        101: ("W97", "W98"),
        102: ("W99", "W100"),
        104: ("W101", "W102"),
    }
    for match_number, placeholders in expected_placeholders.items():
        match = by_number.get(match_number, {})
        actual = (match.get("PlaceHolderA"), match.get("PlaceHolderB"))
        if actual != placeholders:
            raise RuntimeError(
                f"FIFA payload sanity check failed for match {match_number}: "
                f"expected placeholders {placeholders}, got {actual}."
            )


def build_bracket(matches: list[dict]) -> dict:
    shaped = [shape_match(match) for match in matches if match.get("MatchNumber")]
    knockout = {
        match["matchNumber"]: match
        for match in shaped
        if match["round"] in BRACKET_ROUND_ORDER and match["stageName"] != "Play-off for third place"
    }
    resolve_knockout_progression(knockout)

    rounds = []
    for round_key, order in BRACKET_ROUND_ORDER.items():
        rounds.append(
            {
                "key": round_key,
                "label": ROUND_LABELS[round_key],
                "matches": [knockout[number] for number in order if number in knockout],
            }
        )

    final_match = knockout.get(104)
    return {
        "generatedAt": utc_now_iso(),
        "source": {
            "name": "FIFA API",
            "url": FIFA_MATCHES_URL,
            "seasonId": "285023",
            "competitionId": "17",
        },
        "rounds": rounds,
        "matches": [knockout[number] for order in BRACKET_ROUND_ORDER.values() for number in order if number in knockout],
        "champion": final_match.get("winner") if final_match else "",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch official FIFA bracket data.")
    parser.add_argument("--out", default="site/data/bracket.json", type=Path)
    args = parser.parse_args()

    data = build_bracket(fetch_fifa_matches())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.out} with {len(data['matches'])} knockout matches.")


if __name__ == "__main__":
    main()
