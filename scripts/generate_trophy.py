#!/usr/bin/env python3
"""
GitHub Trophy SVG Generator
Dış servis yok, GraphQL yok — sadece GitHub REST API v3.
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
TOKEN    = os.environ.get("GITHUB_TOKEN", "")
USERNAME = os.environ.get("GITHUB_USERNAME", os.environ.get("GITHUB_REPOSITORY_OWNER", ""))
OUT_FILE = os.environ.get("TROPHY_OUTPUT", "profile/trophy.svg")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "trophy-generator/1.0",
}

# ── GitHub REST API helper ────────────────────────────────────────────────────
def gh_get(path: str) -> dict | list:
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise SystemExit(f"GitHub API error {e.code} on {path}: {body[:300]}")


# ── Data fetching (REST only) ─────────────────────────────────────────────────
def fetch_stats() -> dict:
    print(f"→ /users/{USERNAME}")
    user = gh_get(f"/users/{USERNAME}")

    # Stars across all owned repos
    stars = 0
    page  = 1
    while True:
        print(f"→ repos page {page}")
        repos = gh_get(f"/users/{USERNAME}/repos?per_page=100&page={page}&type=owner")
        if not repos:
            break
        for r in repos:
            stars += r.get("stargazers_count", 0)
        if len(repos) < 100:
            break
        page += 1

    # Commits: sum default-branch commit counts via /repos/.../commits
    # Use search API for a fast total (authenticated, 30 req/min)
    print("→ search: commits")
    commit_res = gh_get(
        f"/search/commits?q=author:{USERNAME}&per_page=1"
    )
    commits = commit_res.get("total_count", 0)

    print("→ search: PRs")
    pr_res = gh_get(
        f"/search/issues?q=author:{USERNAME}+type:pr&per_page=1"
    )
    prs = pr_res.get("total_count", 0)

    print("→ search: issues")
    issue_res = gh_get(
        f"/search/issues?q=author:{USERNAME}+type:issue&per_page=1"
    )
    issues = issue_res.get("total_count", 0)

    return {
        "username":    USERNAME,
        "name":        user.get("name") or USERNAME,
        "followers":   user.get("followers", 0),
        "public_repos": user.get("public_repos", 0),
        "stars":       stars,
        "commits":     commits,
        "prs":         prs,
        "issues":      issues,
        "generated":   datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    }


# ── Trophy definitions ────────────────────────────────────────────────────────
TROPHY_DEFS = [
    {
        "id": "stars", "label": "Stars", "icon": "★", "key": "stars",
        "tiers": [(1000,"S","#ff9d00","#ffcc00"),(500,"A","#c084fc","#e879f9"),
                  (100,"B","#60a5fa","#3b82f6"),(10,"C","#4ade80","#22c55e"),(1,"D","#94a3b8","#64748b")],
    },
    {
        "id": "commits", "label": "Commits", "icon": "◆", "key": "commits",
        "tiers": [(2000,"S","#ff9d00","#ffcc00"),(1000,"A","#c084fc","#e879f9"),
                  (500,"B","#60a5fa","#3b82f6"),(100,"C","#4ade80","#22c55e"),(1,"D","#94a3b8","#64748b")],
    },
    {
        "id": "prs", "label": "Pull Requests", "icon": "⇄", "key": "prs",
        "tiers": [(500,"S","#ff9d00","#ffcc00"),(200,"A","#c084fc","#e879f9"),
                  (50,"B","#60a5fa","#3b82f6"),(10,"C","#4ade80","#22c55e"),(1,"D","#94a3b8","#64748b")],
    },
    {
        "id": "issues", "label": "Issues", "icon": "⚑", "key": "issues",
        "tiers": [(200,"S","#ff9d00","#ffcc00"),(100,"A","#c084fc","#e879f9"),
                  (30,"B","#60a5fa","#3b82f6"),(10,"C","#4ade80","#22c55e"),(1,"D","#94a3b8","#64748b")],
    },
    {
        "id": "repos", "label": "Repositories", "icon": "▤", "key": "public_repos",
        "tiers": [(100,"S","#ff9d00","#ffcc00"),(50,"A","#c084fc","#e879f9"),
                  (20,"B","#60a5fa","#3b82f6"),(5,"C","#4ade80","#22c55e"),(1,"D","#94a3b8","#64748b")],
    },
    {
        "id": "followers", "label": "Followers", "icon": "♥", "key": "followers",
        "tiers": [(1000,"S","#ff9d00","#ffcc00"),(200,"A","#c084fc","#e879f9"),
                  (50,"B","#60a5fa","#3b82f6"),(10,"C","#4ade80","#22c55e"),(1,"D","#94a3b8","#64748b")],
    },
]


def resolve_tier(value, tiers):
    for threshold, rank, c1, c2 in tiers:
        if value >= threshold:
            return rank, c1, c2
    return "?", "#475569", "#334155"


# ── SVG rendering ─────────────────────────────────────────────────────────────
CARD_W = 150
CARD_H = 150
COLS   = 6
GAP    = 14
PAD    = 24


def render_card(td, value, cx, cy):
    rank, c1, c2 = resolve_tier(value, td["tiers"])
    gid = f"g_{td['id']}"
    badge_top = {"S":"#ff9d00","A":"#9333ea","B":"#2563eb","C":"#16a34a","D":"#475569","?":"#475569"}
    badge_bot = {"S":"#ffcc00","A":"#c084fc","B":"#60a5fa","C":"#4ade80","D":"#94a3b8","?":"#94a3b8"}
    b1 = badge_top.get(rank, "#475569")
    b2 = badge_bot.get(rank, "#94a3b8")
    return f"""
  <g transform="translate({cx},{cy})">
    <defs>
      <linearGradient id="{gid}_bg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%"   stop-color="{c1}" stop-opacity="0.18"/>
        <stop offset="100%" stop-color="{c2}" stop-opacity="0.08"/>
      </linearGradient>
      <linearGradient id="{gid}_badge" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%"   stop-color="{b1}"/>
        <stop offset="100%" stop-color="{b2}"/>
      </linearGradient>
    </defs>
    <rect width="{CARD_W}" height="{CARD_H}" rx="14" ry="14"
          fill="url(#{gid}_bg)" stroke="{c1}" stroke-opacity="0.35" stroke-width="1.5"/>
    <text x="{CARD_W//2}" y="46" text-anchor="middle" dominant-baseline="middle"
          font-size="26" fill="{c1}" opacity="0.9" font-family="serif">{td['icon']}</text>
    <rect x="{CARD_W//2 - 20}" y="62" width="40" height="28" rx="8"
          fill="url(#{gid}_badge)" opacity="0.95"/>
    <text x="{CARD_W//2}" y="76" text-anchor="middle" dominant-baseline="middle"
          font-size="15" font-weight="700" fill="#ffffff"
          font-family="'JetBrains Mono','Courier New',monospace">{rank}</text>
    <text x="{CARD_W//2}" y="104" text-anchor="middle" dominant-baseline="middle"
          font-size="10.5" fill="{c1}"
          font-family="'Segoe UI',system-ui,sans-serif"
          font-weight="600" letter-spacing="0.5">{td['label']}</text>
    <text x="{CARD_W//2}" y="124" text-anchor="middle" dominant-baseline="middle"
          font-size="11" fill="#94a3b8"
          font-family="'JetBrains Mono','Courier New',monospace">{value:,}</text>
  </g>"""


def build_svg(stats):
    rows    = (len(TROPHY_DEFS) + COLS - 1) // COLS
    total_w = COLS * CARD_W + (COLS - 1) * GAP + PAD * 2
    total_h = 56 + rows * CARD_H + (rows - 1) * GAP + PAD * 2

    cards = ""
    for i, td in enumerate(TROPHY_DEFS):
        col = i % COLS
        row = i // COLS
        cx  = PAD + col * (CARD_W + GAP)
        cy  = 56  + PAD + row * (CARD_H + GAP)
        cards += render_card(td, stats[td["key"]], cx, cy)

    return f"""<svg xmlns="http://www.w3.org/2000/svg"
     width="{total_w}" height="{total_h}"
     viewBox="0 0 {total_w} {total_h}"
     role="img" aria-label="GitHub Trophies for {stats['username']}">
  <defs>
    <linearGradient id="bg_grad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%"   stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e1b4b"/>
    </linearGradient>
  </defs>
  <rect width="{total_w}" height="{total_h}" rx="18" ry="18" fill="url(#bg_grad)"/>
  <rect width="{total_w}" height="{total_h}" rx="18" ry="18"
        fill="none" stroke="#6366f1" stroke-opacity="0.25" stroke-width="1.5"/>
  <text x="{total_w//2}" y="32" text-anchor="middle" dominant-baseline="middle"
        font-size="15" font-weight="700" fill="#e2e8f0" letter-spacing="3"
        font-family="'Segoe UI',system-ui,sans-serif">
    🏆  {stats['name']}  ·  GitHub Trophies
  </text>
  <text x="{total_w//2}" y="48" text-anchor="middle" dominant-baseline="middle"
        font-size="9.5" fill="#475569"
        font-family="'JetBrains Mono','Courier New',monospace">
    {stats['generated']}
  </text>
  {cards}
</svg>"""


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    if not USERNAME:
        raise SystemExit("ERROR: GITHUB_USERNAME or GITHUB_REPOSITORY_OWNER not set")
    if not TOKEN:
        raise SystemExit("ERROR: GITHUB_TOKEN not set")

    print(f"Fetching stats for: {USERNAME}")
    stats = fetch_stats()
    print(json.dumps(stats, indent=2))

    svg = build_svg(stats)
    os.makedirs(os.path.dirname(OUT_FILE) or ".", exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(svg)

    size = len(svg.encode())
    print(f"\nSVG written → {OUT_FILE}  ({size:,} bytes)")
    if "<svg" not in svg:
        raise SystemExit("ERROR: Output does not look like valid SVG!")


if __name__ == "__main__":
    main()
