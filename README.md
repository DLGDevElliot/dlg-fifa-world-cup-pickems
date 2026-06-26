# DLG FIFA World Cup Pickems

Static GitHub Pages site for the DLG FIFA World Cup Pickems bracket pool.

The site has:

- A Home page with the top three participants and the live official knockout bracket.
- A Leaderboard page with all participants sorted by total points.
- Python data scripts that ignore the workbook's embedded scoring and recalculate from official FIFA match winners.
- A scheduled GitHub Actions workflow that updates the data daily and deploys GitHub Pages.

## Project Structure

```text
scorecards/                 Submitted bracket workbooks
scripts/                    Extraction, FIFA fetch, and scoring code
site/                       Static GitHub Pages site
site/data/                  Generated JSON consumed by the site
.github/workflows/          Daily update and Pages deployment workflow
```

## Data Source

The updater uses FIFA's public API as the primary official source:

```text
https://api.fifa.com/api/v3/calendar/matches?language=en&count=200&idCompetition=17&idSeason=285023
```

`idCompetition=17` is the FIFA World Cup and `idSeason=285023` is FIFA World Cup 2026.

ESPN's public World Cup scoreboard can be used manually as a fallback reference if FIFA changes the API shape:

```text
https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates=20260611-20260719&limit=200
```

## Scoring

The workbook's score cells are ignored. Scoring is recalculated from official knockout winners only:

| Round | Points |
| --- | ---: |
| Round of 32 | 1 |
| Round of 16 | 2 |
| Quarterfinals | 4 |
| Semifinals | 8 |
| Final champion | 16 |

The scorecard cell-to-match mapping lives in `scripts/bracket_config.py`.

## Add New Scorecards

1. Add the new submitted `.xlsx` workbook to `scorecards/`.
2. Keep participant bracket tabs in the same scorecard layout. The participant name should be in cell `B3`.
3. Support tabs named `Results`, `Teams`, `Research Notes`, `Top 32 Projection`, or `Setup` are ignored.
4. Run:

```bash
python -m pip install -r requirements.txt
python scripts/update_site_data.py
```

5. Commit the new workbook and regenerated `site/data/*.json` files.

You can also place multiple participant tabs in a single workbook, as the initial scorecard does.

## Daily Automation

The workflow at `.github/workflows/update-site.yml` runs every day at 10:18 UTC and can also be run manually with `workflow_dispatch`.

It does the following:

1. Installs Python dependencies.
2. Pulls latest official FIFA match data.
3. Extracts every participant bracket from `scorecards/*.xlsx`.
4. Recalculates scores from official knockout winners.
5. Writes `site/data/picks.json`, `site/data/bracket.json`, and `site/data/standings.json`.
6. Commits changed data files back to the repository.
7. Deploys the `site/` folder to GitHub Pages.

In your GitHub repository, set Pages to deploy from GitHub Actions.

## Local Preview

Run the updater and serve the static site:

```bash
python scripts/update_site_data.py
python -m http.server 8000 --directory site
```

Then open:

```text
http://localhost:8000
```

