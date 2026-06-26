import unittest

from scripts.score_pickems import build_standings


class ScoringTests(unittest.TestCase):
    def test_scores_completed_matches_only_and_uses_round_weights(self):
        picks = {
            "participants": [
                {
                    "name": "Player One",
                    "picks": {
                        "74": {"pick": "United States", "cell": "C9"},
                        "89": {"pick": "Brazil", "cell": "D10"},
                        "104": {"pick": "France", "cell": "G19"},
                    },
                },
                {
                    "name": "Player Two",
                    "picks": {
                        "74": {"pick": "Mexico", "cell": "C9"},
                        "89": {"pick": "Brazil", "cell": "D10"},
                        "104": {"pick": "Germany", "cell": "G19"},
                    },
                },
            ]
        }
        bracket = {
            "generatedAt": "2026-07-20T00:00:00+00:00",
            "matches": [
                {"matchNumber": 74, "round": "round_of_32", "status": "completed", "winner": "USA"},
                {"matchNumber": 89, "round": "round_of_16", "status": "scheduled", "winner": ""},
                {"matchNumber": 104, "round": "final", "status": "completed", "winner": "France"},
            ],
        }

        standings = build_standings(picks, bracket)

        self.assertEqual(standings["participants"][0]["name"], "Player One")
        self.assertEqual(standings["participants"][0]["totalPoints"], 17)
        self.assertEqual(standings["participants"][1]["totalPoints"], 0)


if __name__ == "__main__":
    unittest.main()
