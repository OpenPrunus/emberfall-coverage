#!/usr/bin/env python3
"""Publie la couverture d'un dépôt Emberfall sur ce site (GitHub Pages) : rapport HTML, pastille, historique, page d'accueil.

Appelé par la CI de chaque dépôt après `cargo llvm-cov` :
    publish.py --repo emberfall-server --html <dossier html> --summary <summary.json> --commit <sha> [--site <racine du site>]

`summary.json` : sortie de `cargo llvm-cov report --json --summary-only` (on en lit les totaux).
"""
import argparse
import datetime
import html
import json
import os
import shutil

REPOS = ["emberfall-common", "emberfall-server", "emberfall-client", "emberfall-integration"]
LABELS = {
    "emberfall-common": "Règles partagées, protocole, simulation",
    "emberfall-server": "Serveur, comptes, base de données",
    "emberfall-client": "Client (rendu et interface)",
    "emberfall-integration": "Tests fonctionnels : serveur et clients réels (couverture de bout en bout)",
}
HISTORY = 60


def colour(pct):
    """Couleur de la pastille, du rouge au vert (comme shields.io)."""
    for limit, c in ((90, "#4c1"), (80, "#97ca00"), (70, "#a4a61d"), (60, "#dfb317"), (50, "#fe7d37")):
        if pct >= limit:
            return c
    return "#e05d44"


def badge(label, value, fill):
    """Pastille SVG au format « plat » de shields.io (largeurs estimées : 6,5 px par caractère)."""
    lw, vw = int(len(label) * 6.5 + 10), int(len(value) * 7 + 10)
    w = lw + vw
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" role="img" aria-label="{label} : {value}">
<title>{label} : {value}</title>
<linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>
<clipPath id="r"><rect width="{w}" height="20" rx="3" fill="#fff"/></clipPath>
<g clip-path="url(#r)"><rect width="{lw}" height="20" fill="#555"/><rect x="{lw}" width="{vw}" height="20" fill="{fill}"/><rect width="{w}" height="20" fill="url(#s)"/></g>
<g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
<text x="{lw / 2}" y="15" fill="#010101" fill-opacity=".3">{label}</text><text x="{lw / 2}" y="14">{label}</text>
<text x="{lw + vw / 2}" y="15" fill="#010101" fill-opacity=".3">{value}</text><text x="{lw + vw / 2}" y="14">{value}</text>
</g></svg>
"""


def totals(summary_path):
    data = json.load(open(summary_path))
    t = data["data"][0]["totals"]
    return {k: {"count": t[k]["count"], "covered": t[k]["covered"], "percent": round(t[k]["percent"], 2)} for k in ("lines", "functions", "regions")}


def sparkline(points):
    if len(points) < 2:
        return ""
    w, h = 120, 24
    lo, hi = min(points), max(points)
    span = max(hi - lo, 1.0)
    xy = " ".join(f"{i * w / (len(points) - 1):.1f},{h - (p - lo) / span * (h - 4) - 2:.1f}" for i, p in enumerate(points))
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}"><polyline fill="none" stroke="currentColor" stroke-width="1.5" points="{xy}"/></svg>'


def index(site):
    rows = []
    for repo in REPOS:
        path = os.path.join(site, "data", f"{repo}.json")
        if not os.path.exists(path):
            continue
        d = json.load(open(path))
        last = d["history"][-1]
        pct = last["lines"]["percent"]
        trend = sparkline([h["lines"]["percent"] for h in d["history"]])
        rows.append(f"""<tr>
<td><a href="{repo}/index.html"><strong>{repo}</strong></a><br><small>{html.escape(LABELS.get(repo, ""))}</small></td>
<td><img src="badges/{repo}.svg" alt="{pct} %"></td>
<td class="n">{last["lines"]["covered"]} / {last["lines"]["count"]}</td>
<td class="n">{last["functions"]["percent"]} %</td>
<td class="n">{last["regions"]["percent"]} %</td>
<td class="trend">{trend}</td>
<td><small>{last["date"]}<br><code>{last["commit"][:8]}</code></small></td>
</tr>""")
    page = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Couverture Emberfall</title>
<style>
:root {{ color-scheme: light dark; --bg: #f6f3ec; --fg: #2c2a26; --muted: #6d675d; --line: #ddd5c4; --card: #fffdf8; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg: #1d1c1a; --fg: #ece6da; --muted: #a59e90; --line: #3a3732; --card: #262522; }} }}
body {{ margin: 0; background: var(--bg); color: var(--fg); font: 15px/1.5 system-ui, sans-serif; }}
main {{ max-width: 1000px; margin: 0 auto; padding: 32px 16px; }}
h1 {{ font-size: 1.6rem; margin: 0 0 4px; }} p {{ color: var(--muted); margin: 0 0 24px; }}
.wrap {{ overflow-x: auto; background: var(--card); border: 1px solid var(--line); border-radius: 8px; }}
table {{ border-collapse: collapse; width: 100%; min-width: 720px; }}
th, td {{ padding: 10px 12px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: middle; }}
th {{ font-size: .8rem; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }}
tr:last-child td {{ border-bottom: 0; }} td.n {{ font-variant-numeric: tabular-nums; }} .trend {{ color: var(--muted); }}
a {{ color: inherit; }} small {{ color: var(--muted); }}
</style></head>
<body><main>
<h1>Couverture de code d'Emberfall</h1>
<p>Part du code exécutée par les tests (cargo-llvm-cov), mise à jour à chaque poussée sur <code>main</code>. Cliquer sur un dépôt pour voir chaque fichier ligne par ligne.</p>
<div class="wrap"><table>
<thead><tr><th>Dépôt</th><th>Lignes</th><th>Lignes couvertes</th><th>Fonctions</th><th>Régions</th><th>Évolution</th><th>Dernière mesure</th></tr></thead>
<tbody>
{"".join(rows)}
</tbody></table></div>
</main></body></html>
"""
    open(os.path.join(site, "index.html"), "w").write(page)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, choices=REPOS)
    ap.add_argument("--html", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--site", default=os.path.join(os.path.dirname(__file__), ".."))
    a = ap.parse_args()
    site = os.path.abspath(a.site)
    t = totals(a.summary)
    # rapport ligne à ligne
    dest = os.path.join(site, a.repo)
    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(a.html, dest)
    # pastille
    os.makedirs(os.path.join(site, "badges"), exist_ok=True)
    pct = t["lines"]["percent"]
    open(os.path.join(site, "badges", f"{a.repo}.svg"), "w").write(badge("couverture", f"{pct:.1f} %", colour(pct)))
    # historique
    os.makedirs(os.path.join(site, "data"), exist_ok=True)
    path = os.path.join(site, "data", f"{a.repo}.json")
    d = json.load(open(path)) if os.path.exists(path) else {"repo": a.repo, "history": []}
    d["history"].append({**t, "commit": a.commit, "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")})
    d["history"] = d["history"][-HISTORY:]
    json.dump(d, open(path, "w"), indent=1)
    index(site)
    print(f"{a.repo} : {pct} % des lignes")


if __name__ == "__main__":
    main()
