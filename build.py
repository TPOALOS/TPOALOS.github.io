#!/usr/bin/env python3
"""Generate index.html, sitemap.xml and robots.txt for https://tpoalos.github.io from the live GitHub repo list.

    python3 build.py            # needs the GitHub CLI (`gh`) logged in; writes the files next to this script

No dependencies, no JavaScript on the page, no external requests.
"""
import datetime
import html
import json
import os
import re
import subprocess
import sys

OWNER = "TPOALOS"
SITE = "https://tpoalos.github.io/"
HERE = os.path.dirname(os.path.abspath(__file__))
GROUPS = [
    ("start", "Start here", "The bigger projects: each one is a full tool with its own documentation.",
     ["hostguard", "portlens", "pcaplens", "ctfhost", "pocketledger"]),
    ("ai", "AI assistants and agents", "Keep an AI agent from doing damage, and keep hidden instructions and secrets out of what it reads.",
     ["cmdguard", "mcpaudit", "injectscan", "ctxpack", "tokcount"]),
    ("ops", "Things that quietly break, until they cost you", "Backups, cron jobs, disks, certificates and expiry dates.",
     ["backupcheck", "jobwatch", "diskwatch", "expirywatch", "certwatch", "cronnext", "dupefind"]),
    ("privacy", "Privacy and leaks", "Photos, commits, logs, shell history, passwords and .env files.",
     ["exifstrip", "secretscan", "githook-guard", "gitidentity-audit", "logscrub", "shellhist-scrub", "envdrift", "pwlint"]),
    ("security", "Security checks for your own systems", "SSH, open ports, file integrity, HTTP headers, JWTs, phishing.",
     ["listenwatch", "sshcfg-audit", "sshkey-audit", "authlog-summary", "fimcheck", "permaudit", "headercheck", "jwtlint", "mailtriage", "urlcheck"]),
    ("dev", "Developer hygiene", "Repositories, CI workflows, Dockerfiles and requirements files.",
     ["repolint", "gha-audit", "dockerfile-audit", "reqpin"]),
    ("finance", "Finance", "Backtest leakage and honest performance statistics.", ["backtestlint", "riskmetrics"]),
]
SKIP = {OWNER, OWNER + ".github.io", "hashguard", "mini-tools"}


def fetch():
    out = subprocess.run(["gh", "repo", "list", OWNER, "--limit", "200", "--json", "name,description,url"],
                         capture_output=True, text=True, check=True).stdout
    return {r["name"]: r for r in json.loads(out)}


def short(desc):
    desc = re.sub(r"\s*\((stdlib-only|pure|stdlib).*?\)\s*$", "", desc or "", flags=re.I)
    return desc.strip()


def card(r):
    n = html.escape(r["name"])
    return ('<article class="card" id="%s"><h3><a href="%s">%s</a></h3><p>%s</p>'
            '<pre><code>pip install git+https://github.com/%s/%s</code></pre></article>'
            % (n, html.escape(r["url"]), n, html.escape(short(r["description"])), OWNER, n))


def build(repos):
    known = [n for _, _, _, names in GROUPS for n in names]
    missing = [n for n in known if n not in repos]
    if missing:
        raise SystemExit("repositories not found: %s" % ", ".join(missing))
    extra = sorted(set(repos) - set(known) - SKIP)
    if extra:
        print("note: not listed on the page (add them to GROUPS): %s" % ", ".join(extra), file=sys.stderr)
    total = len(known)
    sections = []
    for gid, title, blurb, names in GROUPS:
        cards = "\n".join(card(repos[n]) for n in names)
        sections.append('<section id="%s"><h2>%s</h2><p class="blurb">%s</p><div class="grid">\n%s\n</div></section>'
                        % (gid, html.escape(title), html.escape(blurb), cards))
    nav = " ".join('<a href="#%s">%s</a>' % (gid, html.escape(title.split(",")[0])) for gid, title, _, _ in GROUPS)
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": "Command-line tools by %s" % OWNER,
          "itemListElement": [
              {"@type": "ListItem", "position": i + 1, "item": {
                  "@type": "SoftwareSourceCode", "name": n, "description": short(repos[n]["description"]),
                  "codeRepository": repos[n]["url"], "programmingLanguage": "Python",
                  "license": "https://opensource.org/licenses/MIT", "author": {"@type": "Person", "name": OWNER}}}
              for i, n in enumerate(known)]}
    ld_json = json.dumps(ld, indent=1).replace("</", "<\\/")
    desc = ("%d small command-line tools in pure Python with zero dependencies: AI agent safety, backups, privacy, "
            "security audits, personal finance. Open source, MIT licensed, tested." % total)
    return TEMPLATE.format(desc=html.escape(desc, True), total=total, nav=nav, sections="\n".join(sections),
                           ld=ld_json, year=datetime.date.today().year, owner=OWNER, site=SITE)


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TPOALOS: small, sharp command-line tools in pure Python</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{site}">
<meta property="og:type" content="website">
<meta property="og:title" content="TPOALOS: small, sharp command-line tools">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{site}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="TPOALOS: small, sharp command-line tools">
<meta name="twitter:description" content="{desc}">
<meta name="color-scheme" content="light dark">
<script type="application/ld+json">
{ld}
</script>
<style>
:root{{--bg:#fafaf7;--fg:#16191d;--muted:#5d646b;--card:#fff;--line:#dcded6;--accent:#0f766e;--code:#f1f3ee}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0f1317;--fg:#e8eaed;--muted:#9aa3ad;--card:#171c22;--line:#2a3139;--accent:#5eead4;--code:#10151a}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}}
a{{color:var(--accent)}}main,header,footer{{max-width:1040px;margin:0 auto;padding:0 18px}}
header{{padding-top:56px;padding-bottom:12px}}h1{{font-size:clamp(30px,6vw,48px);line-height:1.1;margin:0 0 10px}}
.lead{{font-size:19px;color:var(--muted);max-width:720px;margin:0 0 18px}}
.facts{{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 18px;padding:0;list-style:none}}
.facts li{{border:1px solid var(--line);border-radius:999px;padding:3px 12px;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:14px}}
nav.jump{{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:14px;padding-bottom:10px;border-bottom:1px solid var(--line)}}
h2{{font-size:24px;margin:44px 0 4px}}.blurb{{color:var(--muted);margin:0 0 16px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:14px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}}
.card h3{{margin:0 0 4px;font-size:18px}}.card p{{margin:0 0 10px;color:var(--muted);font-size:15px}}
pre{{margin:0;background:var(--code);border-radius:8px;padding:8px 10px;font-size:12.5px;white-space:pre-wrap;word-break:break-all}}
code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
.principles{{margin:12px 0 0;padding-left:20px}}footer{{padding-top:36px;padding-bottom:48px;color:var(--muted);font-size:14px}}
</style>
</head>
<body>
<header>
<h1>Small, sharp command-line tools.</h1>
<p class="lead">Each one solves a single real problem, in pure Python with no dependencies: nothing to install, nothing to audit, nothing that phones home. They check, warn and report; none of them attacks anything.</p>
<ul class="facts"><li>{total} tools</li><li>0 dependencies</li><li>tested, CI on Linux and macOS</li><li>MIT</li></ul>
<nav class="jump" aria-label="Sections">{nav}</nav>
</header>
<main>
{sections}
<section id="principles">
<h2>How they are built</h2>
<ul class="principles">
<li><strong>Zero dependencies.</strong> Python's standard library only.</li>
<li><strong>Read-only by default.</strong> When a tool can change something it previews first, keeps a backup or writes a copy, and never deletes on its own.</li>
<li><strong>Honest about limits.</strong> These are checks, not oracles: a clean result means "nothing found", never "proven safe".</li>
<li><strong>Private by construction.</strong> No telemetry and no accounts; tools that must use the network only talk to hosts you name.</li>
</ul>
</section>
</main>
<footer>
<p>All source on <a href="https://github.com/{owner}">github.com/{owner}</a>. Issues and pull requests are welcome. Page generated from the live repository list (see <a href="https://github.com/{owner}/{owner}.github.io">build.py</a>).</p>
</footer>
</body>
</html>
"""


def main():
    repos = fetch()
    page = build(repos)
    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page)
    today = datetime.date.today().isoformat()
    with open(os.path.join(HERE, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                 '  <url><loc>%s</loc><lastmod>%s</lastmod></url>\n</urlset>\n' % (SITE, today))
    with open(os.path.join(HERE, "robots.txt"), "w", encoding="utf-8") as fh:
        fh.write("User-agent: *\nAllow: /\nSitemap: %ssitemap.xml\n" % SITE)
    print("wrote index.html (%d KB), sitemap.xml, robots.txt" % (len(page) // 1024))


if __name__ == "__main__":
    main()
