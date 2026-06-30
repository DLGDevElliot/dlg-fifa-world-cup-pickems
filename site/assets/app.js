const dataUrl = (file) => `data/${file}`;

async function getJson(file) {
  const response = await fetch(dataUrl(file), { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Could not load ${file}`);
  }
  return response.json();
}

function formatDateTime(value) {
  if (!value) return "";
  const date = new Date(value);
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function formatUpdated(value) {
  if (!value) return "";
  const date = new Date(value);
  return `Updated ${new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date)}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function teamName(match, side) {
  const team = match[side];
  if (team && team.name) return team.name;
  return side === "home" ? match.placeholderA : match.placeholderB;
}

function teamAbbr(match, side) {
  const team = match[side];
  if (team && team.abbreviation) return team.abbreviation;
  return teamName(match, side);
}

function scoreText(match, side) {
  const value = match.score?.[side];
  const penalty = match.score?.[`${side}Penalty`];
  if (value === null || value === undefined) return "";
  if (penalty !== null && penalty !== undefined) {
    return `${value} (${penalty})`;
  }
  return value;
}

function allMatches(bracket) {
  if (Array.isArray(bracket.matches) && bracket.matches.length) return bracket.matches;
  return (bracket.rounds || []).flatMap((round) => round.matches || []);
}

function nextUpcomingMatch(bracket, now = new Date()) {
  return allMatches(bracket)
    .filter((match) => {
      const date = new Date(match.date);
      return !Number.isNaN(date.getTime()) && date > now;
    })
    .sort((a, b) => new Date(a.date) - new Date(b.date))[0];
}

function locationText(match) {
  return [match.venue, match.city, match.country].filter(Boolean).join(", ");
}

function renderNextTeam(match, side) {
  const abbr = teamAbbr(match, side);
  const name = teamName(match, side);
  const showName = name && name !== abbr;
  return `
    <div class="next-team">
      <span class="next-team-abbr">${escapeHtml(abbr)}</span>
      ${showName ? `<span class="next-team-name">${escapeHtml(name)}</span>` : ""}
    </div>
  `;
}

function renderNextMatch(bracket) {
  const container = document.getElementById("next-match");
  if (!container) return;

  const match = nextUpcomingMatch(bracket);
  if (!match) {
    container.innerHTML = `
      <div class="next-match-label">Next Match</div>
      <div class="next-match-empty">No remaining matches</div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="next-match-label">Next Match</div>
    <div class="next-match-teams">
      ${renderNextTeam(match, "home")}
      <span class="next-match-vs">vs</span>
      ${renderNextTeam(match, "away")}
    </div>
    <div class="next-match-details">
      <time datetime="${escapeHtml(match.date)}">${escapeHtml(formatDateTime(match.date))}</time>
      <span>${escapeHtml(locationText(match))}</span>
    </div>
  `;
}

function renderTopThree(standings) {
  const container = document.getElementById("top-three");
  if (!container) return;

  const rows = standings.topThree || [];
  container.innerHTML = rows
    .map(
      (row, index) => `
        <article class="podium-card rank-${index + 1}">
          <div class="rank-mark">#${row.rank}</div>
          <h3>${escapeHtml(row.name)}</h3>
          <p>${row.totalPoints} pts</p>
        </article>
      `,
    )
    .join("");
}

function renderBracket(bracket) {
  const container = document.getElementById("bracket");
  if (!container) return;

  const rounds = bracket.rounds || [];
  container.innerHTML = rounds
    .map(
      (round, roundIndex) => `
        <section class="round-column round-${roundIndex + 1}" aria-label="${escapeHtml(round.label)}">
          <h3>${escapeHtml(round.label)}</h3>
          <div class="match-list">
            ${(round.matches || [])
              .map((match, matchIndex) => renderMatch(match, matchIndex, roundIndex, rounds.length))
              .join("")}
          </div>
        </section>
      `,
    )
    .join("");

  const source = document.getElementById("bracket-source");
  if (source) {
    source.textContent = `${bracket.source?.name || "Tournament data"} - ${formatUpdated(bracket.generatedAt)}`;
  }
}

function renderMatch(match, matchIndex = 0, roundIndex = 0, roundCount = 1) {
  const homeWinner = match.winner && match.winner === teamName(match, "home");
  const awayWinner = match.winner && match.winner === teamName(match, "away");
  const hasPreviousRound = roundIndex > 0;
  const hasNextRound = roundIndex < roundCount - 1;
  const connectorClasses = [
    "match-node",
    hasPreviousRound ? "has-prev" : "",
    hasNextRound ? "has-next" : "",
    hasNextRound ? (matchIndex % 2 === 0 ? "pair-top" : "pair-bottom") : "",
  ]
    .filter(Boolean)
    .join(" ");
  return `
    <div class="${connectorClasses}">
      <article class="match-card ${match.status}" data-match="${match.matchNumber}">
        <div class="match-meta">
          <span>Match ${match.matchNumber}</span>
          <time datetime="${escapeHtml(match.date)}">${escapeHtml(formatDateTime(match.date))}</time>
        </div>
        <div class="team-row ${homeWinner ? "winner" : ""}">
          <span class="team-abbr">${escapeHtml(teamAbbr(match, "home"))}</span>
          <span class="team-name">${escapeHtml(teamName(match, "home"))}</span>
          <span class="score">${escapeHtml(scoreText(match, "home"))}</span>
        </div>
        <div class="team-row ${awayWinner ? "winner" : ""}">
          <span class="team-abbr">${escapeHtml(teamAbbr(match, "away"))}</span>
          <span class="team-name">${escapeHtml(teamName(match, "away"))}</span>
          <span class="score">${escapeHtml(scoreText(match, "away"))}</span>
        </div>
        <div class="venue">${escapeHtml([match.city, match.country].filter(Boolean).join(", "))}</div>
      </article>
    </div>
  `;
}

function renderLeaderboard(standings) {
  const body = document.getElementById("leaderboard-body");
  if (!body) return;

  body.innerHTML = (standings.participants || [])
    .map(
      (row) => `
        <tr>
          <td>${row.rank}</td>
          <td>${escapeHtml(row.name)}</td>
          <td>${row.totalPoints}</td>
        </tr>
      `,
    )
    .join("");
}

async function bootHome() {
  const [standings, bracket] = await Promise.all([getJson("standings.json"), getJson("bracket.json")]);
  const updated = document.getElementById("last-updated");
  if (updated) updated.textContent = formatUpdated(standings.generatedAt);
  renderTopThree(standings);
renderNextMatch(bracket);
window.setInterval(() => renderNextMatch(bracket), 60000);
renderBracket(bracket);
}

async function bootLeaderboard() {
  const standings = await getJson("standings.json");
  const updated = document.getElementById("leaderboard-updated");
  if (updated) updated.textContent = formatUpdated(standings.generatedAt);
  renderLeaderboard(standings);
}

async function boot() {
  try {
    if (document.body.dataset.page === "home") {
      await bootHome();
    } else if (document.body.dataset.page === "leaderboard") {
      await bootLeaderboard();
    }
  } catch (error) {
    document.body.insertAdjacentHTML(
      "beforeend",
      `<div class="error-banner">${escapeHtml(error.message)}</div>`,
    );
  }
}

boot();
