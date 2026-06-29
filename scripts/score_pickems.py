"""Score participant brackets against official FIFA knockout winners."""

from __future__ import annotations

try:
    from .bracket_config import BRACKET_ROUND_ORDER, ROUND_LABELS, ROUND_WEIGHTS
    from .team_names import normalize_team_name, same_team
except ImportError:
    from bracket_config import BRACKET_ROUND_ORDER, ROUND_LABELS, ROUND_WEIGHTS
    from team_names import normalize_team_name, same_team


def score_participant(participant: dict, bracket: dict) -> dict:
    matches = {str(match["matchNumber"]): match for match in bracket.get("matches", [])}
    points_by_round = {round_key: 0 for round_key in ROUND_LABELS}
    correct_by_round = {round_key: 0 for round_key in ROUND_LABELS}
    possible_by_round = {round_key: 0 for round_key in ROUND_LABELS}
    details = []

    for round_key, order in BRACKET_ROUND_ORDER.items():
        for match_number in order:
            match = matches.get(str(match_number))
            if not match:
                continue

            pick_record = participant.get("picks", {}).get(str(match_number), {})
            pick = pick_record.get("pick", "")
            winner = match.get("winner", "")
            completed = match.get("status") == "completed" and bool(winner)
            correct = completed and same_team(pick, winner)
            points = ROUND_WEIGHTS[round_key] if correct else 0

            if completed:
                possible_by_round[round_key] += ROUND_WEIGHTS[round_key]
            if correct:
                correct_by_round[round_key] += 1
                points_by_round[round_key] += points

            details.append(
                {
                    "matchNumber": match_number,
                    "round": round_key,
                    "roundLabel": ROUND_LABELS[round_key],
                    "pick": pick,
                    "pickKey": normalize_team_name(pick),
                    "winner": winner,
                    "winnerKey": normalize_team_name(winner),
                    "completed": completed,
                    "correct": correct,
                    "points": points,
                    "weight": ROUND_WEIGHTS[round_key],
                    "cell": pick_record.get("cell", ""),
                }
            )

    total = sum(points_by_round.values())
    possible = sum(possible_by_round.values())
    return {
        "name": participant["name"],
        "sheet": participant.get("sheet", ""),
        "sourceFile": participant.get("sourceFile", ""),
        "totalPoints": total,
        "possiblePointsSoFar": possible,
        "pointsByRound": points_by_round,
        "correctByRound": correct_by_round,
        "details": details,
    }


def build_standings(picks: dict, bracket: dict) -> dict:
    participants = [score_participant(participant, bracket) for participant in picks.get("participants", [])]
    participants.sort(key=lambda row: (-row["totalPoints"], row["name"].casefold()))

        last_score = None
    rank = 0
    for participant in participants:
        if participant["totalPoints"] != last_score:
            rank += 1
            last_score = participant["totalPoints"]
        participant["rank"] = rank

    return {
        "generatedAt": bracket.get("generatedAt") or picks.get("generatedAt"),
        "participantCount": len(participants),
        "scoring": {
            "roundWeights": ROUND_WEIGHTS,
            "note": "Scores ignore workbook formulas and are recalculated from official FIFA knockout winners.",
        },
        "participants": participants,
        "topThree": participants[:3],
    }
