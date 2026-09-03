#!/usr/bin/env python3
"""Génère un dashboard HTML moderne et interactif à partir des statistiques des profils Recalbox."""

import argparse
import html
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    USERSCRIPTS_DIR = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(USERSCRIPTS_DIR))
    from others.recalbox_favorites import system_display_name
    from others.recalbox_logging import get_logger
except (ImportError, OSError):

    def system_display_name(system_key):
        return system_key

    def get_logger(name):
        import logging

        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(name)


logger = get_logger("generate_dashboard")

DEFAULT_PROFILES_DIR = Path("/recalbox/share/profiles")
DEFAULT_OUTPUT = Path("/recalbox/share/profiles/dashboard.html")

CSS_STYLE = """
:root {
  --bg-color: #0f0c29;
  --panel-color: #1b1a3a;
  --panel-hover: #25234d;
  --text-main: #f1f5f9;
  --text-muted: #94a3b8;
  --accent: #00d4ff;
  --accent-secondary: #ff00ff;
  --border: #3b3a5d;
  --shadow: 0 10px 20px rgba(0, 0, 0, 0.6);
  --radius: 16px;
}

[data-theme="light"] {
  --bg-color: #f0f2f5;
  --panel-color: #ffffff;
  --panel-hover: #f8fafc;
  --text-main: #1e293b;
  --text-muted: #64748b;
  --accent: #007acc;
  --accent-secondary: #d946ef;
  --border: #cbd5e1;
  --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

* { box-sizing: border-box; transition: background 0.3s, color 0.3s; }

body {
  margin: 0;
  background: var(--bg-color);
  color: var(--text-main);
  font: 15px/1.6 "Inter", "Segoe UI", system-ui, sans-serif;
}

main {
  max-width: 1280px;
  margin: auto;
  padding: 40px 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.header-title h1 {
  margin: 0;
  font-size: 32px;
  font-weight: 800;
  letter-spacing: -0.025em;
}

.header-title .eyebrow {
  color: var(--accent);
  font: 700 12px monospace;
  text-transform: uppercase;
  margin-bottom: 4px;
  display: block;
}

.theme-toggle {
  cursor: pointer;
  background: var(--panel-color);
  border: 1px solid var(--border);
  color: var(--text-main);
  padding: 8px 16px;
  border-radius: 20px;
  font: 700 12px monospace;
  display: flex;
  align-items: center;
  gap: 8px;
  user-select: none;
}

.theme-toggle:hover { background: var(--panel-hover); }

/* Tab Navigation */
.tabs-nav {
  display: flex;
  gap: 8px;
  margin-bottom: 30px;
  overflow-x: auto;
  padding-bottom: 8px;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}

.tab-btn {
  cursor: pointer;
  background: var(--panel-color);
  border: 1px solid var(--border);
  color: var(--text-muted);
  padding: 10px 20px;
  border-radius: 12px;
  font: 600 14px "Inter", sans-serif;
  white-space: nowrap;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.tab-btn:hover {
  background: var(--panel-hover);
  color: var(--text-main);
  transform: translateY(-1px);
}

.tab-btn.active {
  background: var(--accent);
  color: #000;
  border-color: var(--accent);
  box-shadow: 0 4px 12px rgba(0, 212, 255, 0.4);
}

.tab-content {
  display: none;
  animation: fadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.tab-content.active {
  display: block;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(15px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Summary Grid */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.stat-card {
  background: var(--panel-color);
  border: 1px solid var(--border);
  padding: 24px;
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  text-align: center;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.7);
  border-color: var(--accent);
}

.stat-card .label {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 8px;
}

.stat-card .value {
  display: block;
  font-size: 28px;
  font-weight: 800;
  color: var(--accent);
  font-family: monospace;
}

/* Overview Table */
.overview-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--panel-color);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  font-size: 14px;
}

.overview-table th, .overview-table td {
  padding: 14px 16px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

.overview-table th {
  background: var(--panel-hover);
  color: var(--text-muted);
  font: 700 12px monospace;
  text-transform: uppercase;
}

.overview-table tr:last-child td { border-bottom: none; }

/* Profile Card */
.profile-card {
  background: var(--panel-color);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 32px;
  box-shadow: var(--shadow);
}

.profile-card header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.profile-card h2 {
  margin: 0;
  font-size: 28px;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 12px;
}

.profile-card .total-time {
  font: 700 24px monospace;
  color: var(--accent);
}

.persona-badge {
  font-size: 12px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 20px;
  text-transform: uppercase;
  background: var(--accent-secondary);
  color: white;
}

.insights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.insight-card {
  background: var(--panel-hover);
  border: 1px solid var(--border);
  padding: 20px;
  border-radius: 12px;
  text-align: center;
}

.insight-card .lbl {
  display: block;
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 8px;
  text-transform: uppercase;
}

.insight-card .val {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-main);
}

.insight-card .highlight {
  color: var(--accent);
}

.metrics-bar {
  display: flex;
  gap: 30px;
  padding: 20px 0;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  margin-bottom: 30px;
}

.metric {
  display: flex;
  flex-direction: column;
}

.metric .val {
  font: 700 22px monospace;
}

.metric .lbl {
  color: var(--text-muted);
  font-size: 13px;
}

.distribution {
  margin-bottom: 30px;
}

.dist-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 13px;
  white-space: nowrap;
}

.dist-label {
  width: 140px;
  text-align: right;
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
}

.dist-bar-bg {
  flex: 1;
  background: var(--border);
  height: 10px;
  border-radius: 5px;
  overflow: hidden;
}

.dist-bar-fill {
  background: linear-gradient(90deg, var(--accent), var(--accent-secondary));
  height: 100%;
}

.dist-perc {
  width: auto;
  min-width: 90px;
  text-align: left;
  font-family: monospace;
}

.dist-time {
  color: var(--text-muted);
  font-size: 11px;
  margin-left: 4px;
}

.top-games-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.top-games-table th {
  text-align: left;
  color: var(--text-muted);
  font: 700 11px monospace;
  text-transform: uppercase;
  padding: 12px 6px;
  cursor: pointer;
}

.top-games-table th:hover {
  color: var(--accent);
}

.top-games-table td {
  padding: 12px 6px;
  border-bottom: 1px solid var(--border);
}

.game-search {
  width: 100%;
  background: var(--panel-hover);
  border: 1px solid var(--border);
  color: var(--text-main);
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 13px;
  margin-bottom: 12px;
}

.muted { color: var(--text-muted); }

footer {
  margin-top: 40px;
  text-align: center;
  color: var(--text-muted);
  font: 12px monospace;
}

@media (max-width: 600px) {
  .summary-grid { grid-template-columns: 1fr; }
  .header { flex-direction: column; align-items: flex-start; gap: 20px; }
  .metrics-bar { gap: 15px; }
}
"""

JS_LOGIC = """
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('active');
    if (btn.dataset.tab === tabId) btn.classList.add('active');
  });

  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.remove('active');
    if (content.id === tabId) content.classList.add('active');
  });

  localStorage.setItem('dashboard-last-tab', tabId);
}

function toggleTheme() {
  const htmlEl = document.documentElement;
  const current = htmlEl.getAttribute('data-theme');
  const target = current === 'dark' ? 'light' : 'dark';
  htmlEl.setAttribute('data-theme', target);
  localStorage.setItem('dashboard-theme', target);
  updateThemeButton(target);
}

function updateThemeButton(theme) {
  const btn = document.getElementById('theme-btn');
  if (btn) {
    btn.innerHTML = theme === 'dark' ? '☀️ Light Mode' : '🌙 Dark Mode';
  }
}

function filterGames(tableId, query) {
  const queryLower = query.toLowerCase();
  const table = document.getElementById(tableId);
  if (!table) return;
  const rows = table.tBodies[0].rows;

  for (let row of rows) {
    const text = row.textContent.toLowerCase();
    row.style.display = text.includes(queryLower) ? '' : 'none';
  }
}

function sortTable(tableId, colIndex) {
  const table = document.getElementById(tableId);
  if (!table) return;
  const tbody = table.tBodies[0];
  const rows = Array.from(tbody.rows);
  const isAsc = table.dataset.sortCol === colIndex.toString() && table.dataset.sortDir === 'asc';

  rows.sort((a, b) => {
    let valA = a.cells[colIndex].textContent.trim();
    let valB = b.cells[colIndex].textContent.trim();

    // Tri spécifique pour la colonne durée (colIndex == 2) ou les nombres (colIndex == 3)
    if (colIndex >= 2) {
      const parseVal = (v) => {
        if (v.includes('h')) {
          const parts = v.split(' h ');
          const h = parseInt(parts[0]) || 0;
          const m = parseInt(parts[1]) || 0;
          return (h * 3600) + (m * 60);
        }
        if (v.includes('min')) return (parseInt(v) || 0) * 60;
        return parseInt(v) || 0;
      };
      return isAsc ? parseVal(valA) - parseVal(valB) : parseVal(valB) - parseVal(valA);
    }
    return isAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
  });

  table.dataset.sortCol = colIndex;
  table.dataset.sortDir = isAsc ? 'desc' : 'asc';
  rows.forEach(row => tbody.appendChild(row));
}

document.addEventListener('DOMContentLoaded', () => {
  const savedTheme = localStorage.getItem('dashboard-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeButton(savedTheme);

  const lastTab = localStorage.getItem('dashboard-last-tab') || 'tab-global';
  if (document.getElementById(lastTab)) {
    switchTab(lastTab);
  }
});
"""


def read_json(path, default):
    try:
        with path.open(encoding="utf-8") as json_file:
            return json.load(json_file)
    except (OSError, json.JSONDecodeError) as e:
        logger.debug(f"Erreur lecture JSON {path}: {e}")
        return default


def format_duration(seconds):
    seconds = max(0, int(seconds or 0))
    hours, remaining = divmod(seconds, 3600)
    minutes = remaining // 60
    if hours:
        return f"{hours} h {minutes:02d}"
    return f"{minutes} min"


def get_persona(seconds):
    if seconds < 36000:
        return "☕ Casual"
    if seconds < 180000:
        return "🎮 Enthusiast"
    if seconds < 720000:
        return "🔥 Hardcore"
    return "👑 Legend"


def load_profile(profile_dir):
    stats = read_json(profile_dir / "game_time.json", {})
    favorites = read_json(profile_dir / "favorites.json", [])
    games = []
    system_times = {}

    if isinstance(stats, dict):
        for system, system_games in stats.items():
            if not isinstance(system_games, dict):
                continue
            sys_total = 0
            for game, values in system_games.items():
                if not isinstance(values, dict):
                    continue
                time = int(values.get("timeplayed", 0) or 0)
                count = int(values.get("playcount", 0) or 0)
                games.append(
                    {
                        "name": str(game),
                        "system": str(system),
                        "timeplayed": time,
                        "playcount": count,
                        "lastplayed": values.get("lastplayed", ""),
                    }
                )
                sys_total += time
            system_times[system] = sys_total

    games.sort(key=lambda g: (g["timeplayed"], g["playcount"]), reverse=True)
    total_seconds = sum(g["timeplayed"] for g in games)
    play_count = sum(g["playcount"] for g in games)

    distribution = {}
    if total_seconds > 0:
        for sys, time in system_times.items():
            distribution[sys] = (time / total_seconds) * 100

    last_played_game = "Aucun"
    if games:
        sorted_by_date = sorted(games, key=lambda x: x["lastplayed"], reverse=True)
        last_played_game = f"{sorted_by_date[0]['name']} ({system_display_name(sorted_by_date[0]['system'])})"

    mvp_game = "N/A"
    if games:
        mvp_game = f"{games[0]['name']} ({format_duration(games[0]['timeplayed'])})"

    avg_session = 0
    if play_count > 0:
        avg_session = total_seconds / play_count

    return {
        "name": profile_dir.name,
        "games": games,
        "favorites": [item for item in favorites if isinstance(item, dict)],
        "total_seconds": total_seconds,
        "play_count": play_count,
        "distribution": distribution,
        "system_times": system_times,
        "persona": get_persona(total_seconds),
        "avg_session": avg_session,
        "last_played_game": last_played_game,
        "mvp_game": mvp_game,
    }


def collect_data(profiles_dir):
    current = read_json(profiles_dir / "current_profile.json", {})
    profiles = (
        [
            load_profile(p)
            for p in sorted(profiles_dir.iterdir())
            if p.is_dir() and (p / "profile_config.json").exists()
        ]
        if profiles_dir.exists()
        else []
    )

    global_total_time = sum(p["total_seconds"] for p in profiles)
    system_totals = {}
    for p in profiles:
        for sys, perc in p["distribution"].items():
            system_totals[sys] = system_totals.get(sys, 0) + (
                perc / 100 * p["total_seconds"]
            )

    top_system = "N/A"
    if system_totals:
        best_sys_key = max(system_totals, key=system_totals.get)
        top_system = system_display_name(best_sys_key)

    top_profile = "N/A"
    if profiles:
        top_prof = max(profiles, key=lambda p: p["total_seconds"])
        top_profile = top_prof["name"]

    all_games = set()
    for p in profiles:
        for g in p["games"]:
            all_games.add((g["system"], g["name"]))

    return {
        "current_profile": current.get("profile", ""),
        "profiles": profiles,
        "global": {
            "total_time": global_total_time,
            "total_games": len(all_games),
            "top_system": top_system,
            "top_profile": top_profile,
        },
    }


def render_profile_detail(profile):
    name = html.escape(profile["name"])
    persona = profile["persona"]

    dist_rows = (
        "".join(
            f'<div class="dist-row"><div class="dist-label">{html.escape(system_display_name(sys))}</div>'
            f'<div class="dist-bar-bg"><div class="dist-bar-fill" style="width:{p:.1f}%"></div></div>'
            f'<div class="dist-perc">{p:.1f}% <span class="dist-time">({format_duration(profile["system_times"].get(sys, 0))})</span></div></div>'
            for sys, p in sorted(
                profile["distribution"].items(), key=lambda x: x[1], reverse=True
            )[:5]
        )
        or '<div class="muted">Aucune donnée de système</div>'
    )

    top_games = profile["games"][:15]
    game_rows = (
        "".join(
            f"<tr><td>{html.escape(g['name'])}</td><td>{html.escape(system_display_name(g['system']))}</td>"
            f"<td>{format_duration(g['timeplayed'])}</td><td>{g['playcount']}</td></tr>"
            for g in top_games
        )
        or "<tr><td colspan='4' class='muted'>Aucun jeu enregistré</td></tr>"
    )

    table_id = f"table-{profile['name'].replace(' ', '_')}"

    return f"""
    <section id="tab-profile-{profile['name']}" class="tab-content">
      <div class="profile-card">
        <header>
          <div style="display:flex; align-items:center; gap:15px;">
            <h2 style="margin:0">{name}</h2>
            <span class="persona-badge">{persona}</span>
          </div>
          <div class="total-time">{format_duration(profile["total_seconds"])}</div>
        </header>

        <div class="insights-grid">
          <div class="insight-card">
            <span class="lbl">Session Moyenne</span>
            <span class="val highlight">{format_duration(profile["avg_session"])}</span>
          </div>
          <div class="insight-card">
            <span class="lbl">MVP Game</span>
            <span class="val">{profile["mvp_game"]}</span>
          </div>
          <div class="insight-card">
            <span class="lbl">Dernière Activité</span>
            <span class="val">{profile["last_played_game"]}</span>
          </div>
        </div>

        <div class="metrics-bar">
          <div class="metric"><span class="val">{len(profile["games"])}</span><span class="lbl">Jeux</span></div>
          <div class="metric"><span class="val">{profile["play_count"]}</span><span class="lbl">Lancements</span></div>
          <div class="metric"><span class="val">{len(profile["favorites"])}</span><span class="lbl">Favoris</span></div>
        </div>

        <div class="distribution">
          <div style="font-size:12px; font-weight:700; margin-bottom:10px; color:var(--text-muted);">RÉPARTITION PAR SYSTÈME</div>
          {dist_rows}
        </div>

        <div style="flex:1">
          <input type="text" class="game-search" placeholder="Rechercher un jeu, système..." oninput="filterGames('{table_id}', this.value)">
          <table class="top-games-table" id="{table_id}" data-sort-col="2" data-sort-dir="desc">
            <thead>
              <tr>
                <th onclick="sortTable('{table_id}', 0)">Jeu ↕</th>
                <th onclick="sortTable('{table_id}', 1)">Système ↕</th>
                <th onclick="sortTable('{table_id}', 2)">Durée ↕</th>
                <th onclick="sortTable('{table_id}', 3)">Fois ↕</th>
              </tr>
            </thead>
            <tbody>{game_rows}</tbody>
          </table>
        </div>
      </div>
    </section>"""


def render_dashboard(data):
    profiles = data["profiles"]
    global_stats = data["global"]
    generated_at = datetime.now().strftime("%d/%m/%Y à %H:%M")

    tabs_html = f'<div class="tab-btn active" data-tab="tab-global" onclick="switchTab(\'tab-global\')">🏠 Global</div>'
    tabs_html += "".join(
        f'<div class="tab-btn" data-tab="tab-profile-{p["name"]}" onclick="switchTab(\'tab-profile-{p["name"]}\')">{html.escape(p["name"])}</div>'
        for p in profiles
    )

    profile_rows = (
        "".join(
            f"<tr><td>{html.escape(p['name'])}</td>"
            f"<td>{len(p['games'])}</td><td>{p['play_count']}</td>"
            f"<td>{format_duration(p['total_seconds'])}</td></tr>"
            for p in profiles
        )
        or "<tr><td colspan='4' class='muted'>Aucun profil trouvé</td></tr>"
    )

    global_content = f"""
    <section id="tab-global" class="tab-content active">
      <div class="summary-grid">
        <div class="stat-card"><span class="label">⏱️ Temps Total</span><span class="value">{format_duration(global_stats["total_time"])}</span></div>
        <div class="stat-card"><span class="label">🕹️ Jeux Uniques</span><span class="value">{global_stats["total_games"]}</span></div>
        <div class="stat-card"><span class="label">🏆 Système Favori</span><span class="value" style="font-size:20px">{global_stats["top_system"]}</span></div>
        <div class="stat-card"><span class="label">👤 Profil Actif</span><span class="value" style="font-size:20px">{global_stats["top_profile"]}</span></div>
      </div>

      <div style="margin-top:40px">
        <div style="font-size:18px; font-weight:700; margin-bottom:20px;">📊 Aperçu des profils</div>
        <table class="overview-table">
          <thead>
            <tr><th>Profil</th><th>Jeux</th><th>Lancements</th><th>Temps Total</th></tr>
          </thead>
          <tbody>{profile_rows}</tbody>
        </table>
      </div>
    </section>"""

    profile_tabs_content = "".join(render_profile_detail(p) for p in profiles)

    return f"""<!doctype html>
<html lang="fr" data-theme="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Recalbox · Dashboard</title>
  <style>{CSS_STYLE}</style>
</head>
<body>
  <main>
    <div class="header">
      <div class="header-title">
        <span class="eyebrow">Recalbox / Statistiques</span>
        <h1>Tableau de Bord</h1>
      </div>
      <div class="theme-toggle" id="theme-btn" onclick="toggleTheme()">🌙 Dark Mode</div>
    </div>

    <nav class="tabs-nav">
      {tabs_html}
    </nav>

    {global_content}
    {profile_tabs_content}

    <footer>Généré le {generated_at}</footer>
  </main>
  <script>{JS_LOGIC}</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profiles-dir", type=Path, default=DEFAULT_PROFILES_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        data = collect_data(args.profiles_dir)
        args.output.write_text(render_dashboard(data), encoding="utf-8")
        print(f"Dashboard généré avec succès : {args.output}")
    except Exception as e:
        logger.error(f"Erreur fatale lors de la génération : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
