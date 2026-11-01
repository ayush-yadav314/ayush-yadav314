#!/usr/bin/env python3
"""Generate stats.svg, langs.svg and contrib-graph.svg for the profile README.
Uses only the Python standard library and the GitHub GraphQL API (public data)."""
import json, os, sys, urllib.request
from xml.sax.saxutils import escape as esc

OUT = os.environ.get("OUT_DIR", "assets")
LOGIN = os.environ.get("LOGIN", "ayush-yadav314")
TOKEN = os.environ.get("GH_TOKEN", "")
SANS = "'Segoe UI','Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono','Fira Code','Courier New',monospace"
CY, BL, VI, PU = "#00f7ff", "#2f6bff", "#7c3aed", "#a855f7"

QUERY = """
query($login:String!){
  user(login:$login){
    followers{totalCount}
    repositories(ownerAffiliations:OWNER, isFork:false, privacy:PUBLIC, first:100){
      totalCount
      nodes{ stargazerCount languages(first:10, orderBy:{field:SIZE, direction:DESC}){ edges{ size node{ name } } } }
    }
    contributionsCollection{
      totalCommitContributions totalPullRequestContributions totalIssueContributions
      contributionCalendar{ totalContributions weeks{ contributionDays{ contributionCount } } }
    }
  }
}"""

def fetch():
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "profile-stats"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
    if "errors" in d or not d.get("data", {}).get("user"):
        raise SystemExit(f"GraphQL error: {d}")
    return d["data"]["user"]

def wrap(w, h, body, defs="", style=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">'
            f'<defs>{defs}</defs><style>{style}</style>{body}</svg>')

PANEL_DEFS = f'''<linearGradient id="bd" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CY}"/><stop offset=".55" stop-color="{VI}"/><stop offset="1" stop-color="{BL}" stop-opacity=".7"/></linearGradient>
<linearGradient id="gl" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".10"/><stop offset="1" stop-color="#fff" stop-opacity=".01"/></linearGradient>
<radialGradient id="rg" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{VI}" stop-opacity=".35"/><stop offset="1" stop-color="{VI}" stop-opacity="0"/></radialGradient>'''

def panel(w, h, title):
    return (f'<clipPath id="pc"><rect x="2" y="2" width="{w-4}" height="{h-4}" rx="18"/></clipPath>'
            f'<g clip-path="url(#pc)"><rect width="{w}" height="{h}" fill="#080b17"/><circle cx="{w-50}" cy="30" r="150" fill="url(#rg)"/><rect width="{w}" height="{h}" fill="url(#gl)"/></g>'
            f'<rect x="2" y="2" width="{w-4}" height="{h-4}" rx="18" fill="none" stroke="url(#bd)" stroke-width="1.5"/>'
            f'<text x="26" y="42" font-family="{MONO}" font-size="14" font-weight="700" fill="{CY}" letter-spacing="3">{esc(title)}</text>'
            f'<rect x="26" y="54" width="40" height="2" fill="{PU}"/>')

def stats_svg(u):
    W, H = 480, 280
    cc = u["contributionsCollection"]
    repos = u["repositories"]["nodes"]
    stars = sum(r["stargazerCount"] for r in repos)
    items = [("PUBLIC REPOS", u["repositories"]["totalCount"]), ("TOTAL STARS", stars),
             ("FOLLOWERS", u["followers"]["totalCount"]), ("COMMITS (1Y)", cc["totalCommitContributions"]),
             ("PULL REQUESTS (1Y)", cc["totalPullRequestContributions"]), ("ISSUES (1Y)", cc["totalIssueContributions"])]
    b = [panel(W, H, "// GITHUB STATS")]
    for i, (k, v) in enumerate(items):
        col, row = i % 2, i // 2
        x = 26 + col * 220; y = 96 + row * 52
        c = CY if (i % 2 == 0) else PU
        b.append(f'<circle cx="{x+4}" cy="{y-6}" r="4" fill="{c}"><animate attributeName="opacity" values="1;.25;1" dur="2.4s" begin="{i*0.3:.1f}s" repeatCount="indefinite"/></circle>'
                 f'<text x="{x+18}" y="{y-2}" font-family="{MONO}" font-size="11" fill="#6f84ad" letter-spacing="1.5">{k}</text>'
                 f'<text x="{x+18}" y="{y+22}" font-family="{SANS}" font-size="24" font-weight="800" fill="#f2f6ff">{v}</text>')
    b.append(f'<rect x="26" y="{H-44}" width="{W-52}" height="1" fill="#1d2a4d"/>'
             f'<text x="26" y="{H-18}" font-family="{MONO}" font-size="12" fill="{CY}" letter-spacing="1.2">contributions, last year: {cc["contributionCalendar"]["totalContributions"]}</text>')
    return wrap(W, H, "".join(b), PANEL_DEFS)

def langs_svg(u):
    W, H = 480, 280
    tot = {}
    for r in u["repositories"]["nodes"]:
        for e in r["languages"]["edges"]:
            tot[e["node"]["name"]] = tot.get(e["node"]["name"], 0) + e["size"]
    top = sorted(tot.items(), key=lambda kv: -kv[1])[:5]
    s = sum(tot.values()) or 1
    cols = [CY, BL, PU, VI, "#6aa0ff"]
    b = [panel(W, H, "// MOST USED LANGUAGES")]
    for i, (name, size) in enumerate(top):
        pct = size / s * 100
        y = 90 + i * 34
        bw = max(4, (W - 52) * pct / 100 * 0.78)
        b.append(f'<text x="26" y="{y}" font-family="{SANS}" font-size="13.5" font-weight="600" fill="#e8f1ff">{esc(name)}</text>'
                 f'<text x="{W-26}" y="{y}" text-anchor="end" font-family="{MONO}" font-size="12" fill="#9fb0cc">{pct:.1f}%</text>'
                 f'<rect x="26" y="{y+8}" width="{W-52}" height="8" rx="4" fill="#111a33"/>'
                 f'<rect x="26" y="{y+8}" width="0" height="8" rx="4" fill="{cols[i]}"><animate attributeName="width" values="0;{(W-52)*pct/100:.1f}" dur="1.4s" begin="{i*0.15:.2f}s" fill="freeze"/></rect>')
    if not top:
        b.append(f'<text x="26" y="110" font-family="{MONO}" font-size="13" fill="#9fb0cc">no language data yet</text>')
    return wrap(W, H, "".join(b), PANEL_DEFS)

def contrib_svg(u):
    W, H = 1100, 280
    weeks = u["contributionsCollection"]["contributionCalendar"]["weeks"]
    pts = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks]
    total = u["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    mx = max(pts) or 1
    x0, x1, y0, y1 = 40, W - 40, 100, H - 40
    step = (x1 - x0) / max(len(pts) - 1, 1)
    xy = [(x0 + i * step, y1 - (p / mx) * (y1 - y0)) for i, p in enumerate(pts)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in xy)
    area = f"{x0},{y1} " + line + f" {x1},{y1}"
    defs = PANEL_DEFS + f'''<linearGradient id="ar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CY}" stop-opacity=".45"/><stop offset="1" stop-color="{VI}" stop-opacity="0"/></linearGradient>
<linearGradient id="ln" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{CY}"/><stop offset=".6" stop-color="{BL}"/><stop offset="1" stop-color="{PU}"/></linearGradient>
<filter id="g" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'''
    b = [panel(W, H, "// CONTRIBUTION GRAPH - LAST 12 MONTHS")]
    for i in range(4):
        gy = y0 + i * (y1 - y0) / 3
        b.append(f'<line x1="{x0}" y1="{gy:.1f}" x2="{x1}" y2="{gy:.1f}" stroke="#1d2a4d" stroke-width="1" stroke-dasharray="3 6"/>')
    b.append(f'<polygon points="{area}" fill="url(#ar)" opacity="0"><animate attributeName="opacity" values="0;1" dur="1.5s" begin=".8s" fill="freeze"/></polygon>')
    b.append(f'<polyline points="{line}" fill="none" stroke="url(#ln)" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round" filter="url(#g)" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"><animate attributeName="stroke-dashoffset" values="1;0" dur="2.2s" fill="freeze"/></polyline>')
    lx, ly = xy[-1]
    b.append(f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="5" fill="{CY}" filter="url(#g)"><animate attributeName="opacity" values="1;.3;1" dur="1.8s" repeatCount="indefinite"/></circle>')
    b.append(f'<text x="{W-26}" y="42" text-anchor="end" font-family="{MONO}" font-size="13" fill="#9fb0cc" letter-spacing="1">total {total}  |  peak week {mx}</text>')
    return wrap(W, H, "".join(b), defs)

def placeholder(name, w, h, label):
    b = panel(w, h, label) + f'<text x="26" y="{h/2+10}" font-family="{MONO}" font-size="13" fill="#9fb0cc">waiting for the first Stats workflow run...</text>'
    return wrap(w, h, b, PANEL_DEFS)

def main():
    os.makedirs(OUT, exist_ok=True)
    if "--placeholder" in sys.argv:
        for n, w, h, l in [("stats.svg", 480, 280, "// GITHUB STATS"), ("langs.svg", 480, 280, "// MOST USED LANGUAGES"), ("contrib-graph.svg", 1100, 280, "// CONTRIBUTION GRAPH")]:
            open(f"{OUT}/{n}", "w", encoding="utf-8").write(placeholder(n, w, h, l))
        return
    if "--mock" in sys.argv:
        u = {"followers": {"totalCount": 1}, "repositories": {"totalCount": 2, "nodes": [{"stargazerCount": 1, "languages": {"edges": [{"size": 700, "node": {"name": "Python"}}, {"size": 200, "node": {"name": "Java"}}, {"size": 100, "node": {"name": "HTML"}}]}}]},
             "contributionsCollection": {"totalCommitContributions": 5, "totalPullRequestContributions": 0, "totalIssueContributions": 0,
              "contributionCalendar": {"totalContributions": 60, "weeks": [{"contributionDays": [{"contributionCount": (i * 7) % 11}]} for i in range(53)]}}}
    else:
        u = fetch()
    for n, f in [("stats.svg", stats_svg), ("langs.svg", langs_svg), ("contrib-graph.svg", contrib_svg)]:
        open(f"{OUT}/{n}", "w", encoding="utf-8").write(f(u))
    print("generated stats, langs, contrib-graph")

if __name__ == "__main__":
    main()
