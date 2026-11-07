"""Builds assets/stats.svg for the profile README (black/red, animated). Runs in GitHub Actions."""
import os, sys, json, html, datetime, urllib.request

USER = os.environ.get("GH_USER", "CringeDaddy")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "stats.svg")
COLORS = {"Jupyter Notebook": "#DA5B0B", "CSS": "#8a4fff", "Python": "#3572A5", "JavaScript": "#f1e05a",
          "HTML": "#e34c26", "Shell": "#89e051", "C": "#aaaaaa", "C++": "#f34b7d", "Java": "#b07219"}


def api(path):
    req = urllib.request.Request("https://api.github.com" + path,
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "stats-bot"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", "Bearer " + tok)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch():
    u = api(f"/users/{USER}")
    own = [r for r in api(f"/users/{USER}/repos?per_page=100&type=owner") if not r.get("fork")]
    langs = {}
    for r in own:
        if r.get("language"):
            langs[r["language"]] = langs.get(r["language"], 0) + 1
    return dict(repos=u["public_repos"], followers=u["followers"], following=u["following"],
                stars=sum(r["stargazers_count"] for r in own), langs=langs)


def render(d, stamp):
    e = html.escape
    tiles = [("PUBLIC REPOS", d["repos"]), ("FOLLOWERS", d["followers"]),
             ("FOLLOWING", d["following"]), ("TOTAL STARS", "-" if d["stars"] is None else d["stars"])]
    out = []
    for i, (lab, val) in enumerate(tiles):
        x, y = 30 + (i % 2) * 215, 72 + (i // 2) * 84
        out.append(f'<g class="t" style="animation-delay:{0.2 + i * 0.25}s"><rect x="{x}" y="{y}" width="200" height="70" rx="10" fill="#0b0003" stroke="#ff0033" stroke-opacity=".55"/>'
                   f'<text x="{x + 14}" y="{y + 24}" class="lb">{lab}</text><text x="{x + 14}" y="{y + 56}" class="vl">{e(str(val))}</text></g>')
    langs = sorted(d["langs"].items(), key=lambda kv: -kv[1])[:5]
    total = sum(v for _, v in langs) or 1
    out.append('<text x="480" y="62" class="lb">TOP LANGUAGES</text>')
    for i, (n, v) in enumerate(langs):
        y = 92 + i * 30
        pct = v * 100 / total
        c = COLORS.get(n, "#ff0033")
        out.append(f'<text x="480" y="{y + 12}" class="tx">{e(n)}</text><rect x="625" y="{y}" width="150" height="14" rx="7" fill="#1a0006"/>'
                   f'<rect class="bar" style="animation-delay:{0.6 + i * 0.2}s" x="625" y="{y}" width="{max(8, 1.5 * pct):.0f}" height="14" rx="7" fill="{c}"/>'
                   f'<text x="786" y="{y + 12}" class="tx">{pct:.0f}%</text>')
    if not langs:
        out.append('<text x="480" y="100" class="tx">no language data yet</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 260" width="860" height="260" role="img" aria-label="GitHub stats for {e(USER)}">
<style>
text{{font-family:'Courier New',Courier,monospace}}
.lb{{font-size:12px;fill:#8b8b8b;letter-spacing:2px}}.vl{{font-size:30px;font-weight:700;fill:#fff}}.tx{{font-size:13px;fill:#ddd}}
.ti{{font-size:16px;font-weight:700;fill:#ff0033}}.up{{font-size:10px;fill:#666}}
.t{{animation:fi .8s ease-out both}}@keyframes fi{{from{{opacity:0;transform:translateY(8px)}}}}
.bar{{transform-box:fill-box;transform-origin:0 50%;animation:gr 1.6s ease-out both}}@keyframes gr{{from{{transform:scaleX(0)}}}}
.bd{{animation:gl 2.4s ease-in-out infinite alternate}}@keyframes gl{{from{{stroke-opacity:.35}}to{{stroke-opacity:1}}}}
.sc{{animation:sc 5s linear infinite}}@keyframes sc{{from{{transform:translateY(-20px)}}to{{transform:translateY(270px)}}}}
</style>
<rect width="860" height="260" rx="14" fill="#000"/><rect class="sc" width="860" height="16" fill="#ff0033" opacity=".07"/>
<rect class="bd" x="1" y="1" width="858" height="258" rx="14" fill="none" stroke="#ff0033" stroke-width="2"/>
<text x="30" y="40" class="ti">&gt; {e(USER)} / github-stats</text>
{chr(10).join(out)}
<text x="830" y="246" text-anchor="end" class="up">updated {stamp} UTC</text>
</svg>'''


if __name__ == "__main__":
    if "--offline" in sys.argv:
        data = dict(repos=5, followers=6, following=3, stars=None, langs={"Jupyter Notebook": 2, "CSS": 1})
    else:
        data = fetch()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render(data, datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")))
    print("wrote", OUT, data)
