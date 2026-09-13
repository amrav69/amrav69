#!/usr/bin/env python3
"""Generate a self-hosted top-languages SVG (top_langs.svg) for the profile README.

Data source: GitHub REST API only (no third-party services).
- Counts the user's commits per repo over the last 30 days (UTC),
  attributes each repo's commits to its primary language, shows top 5 + other.
- Forks and archived repos are excluded.
- Never fails the workflow: on API errors it renders a graceful empty state.
- Style matches card.svg / card2.svg / activity.svg: dark bg, monospace,
  cyan/green/orange accents.

Usage:
    python gen_top_langs.py
Env:
    GITHUB_USER   (default: amrav69)
    GITHUB_TOKEN  (optional, raises API rate limit)
    DAYS          (default: 30)
    OUT           (default: top_langs.svg)
    TOP_N         (default: 5)
"""

import datetime
import json
import os
import re
import urllib.request
import urllib.error

USERNAME = os.environ.get("GITHUB_USER", "amrav69")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
DAYS = int(os.environ.get("DAYS", "30"))
TOP_N = int(os.environ.get("TOP_N", "5"))
OUT = os.environ.get("OUT", "top_langs.svg")

API = "https://api.github.com"

# GitHub linguist colors for common languages.
LANG_COLORS = {
    "Python": "#3572A5", "Rust": "#dea584", "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6", "Go": "#00ADD8", "Java": "#b07219",
    "C": "#555555", "C++": "#f34b7d", "C#": "#178600",
    "HTML": "#e34c26", "CSS": "#563d7c", "Shell": "#89e051",
    "Dockerfile": "#384d54", "Ruby": "#701516", "PHP": "#4F5D95",
    "Swift": "#F05138", "Kotlin": "#A97BFF", "Dart": "#00B4AB",
    "R": "#198CE7", "Scala": "#c22d40", "Jupyter Notebook": "#DA5B0B",
    "Vue": "#41b883", "Svelte": "#ff3e00", "Lua": "#000080",
    "Zig": "#ec915c", "Elixir": "#6e4a7e", "Haskell": "#5e5086",
    "Astro": "#ff5a03", "PowerShell": "#012456", "Batchfile": "#C1F12E",
    "Nix": "#7e7aab", "HCL": "#844FBA", "CMake": "#DA3434",
    "Makefile": "#427819", "Vim Script": "#199f4b", "MDX": "#fcb32c",
}
DEFAULT_COLOR = "#8b949e"


def api_get(url):
    """Return (data, link_header)."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "amrav69-profile-top-langs",
        "Accept": "application/vnd.github+json",
        **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode()), r.headers.get("Link", "")
    except urllib.error.HTTPError as e:
        if e.code in (409, 422):  # empty repo / uncomparable: zero commits
            return [], ""
        raise


def count_commits(full_name, since):
    """User's commit count in a repo since `since` (Link-header trick)."""
    data, link = api_get(
        f"{API}/repos/{full_name}/commits?author={USERNAME}"
        f"&since={since}&per_page=1")
    m = re.search(r"[?&]page=(\d+)>;\s*rel=\"last\"", link)
    if m:
        return int(m.group(1))
    return len(data)


def collect_lang_commits():
    """Return [(language, commits)] sorted desc, last-DAYS window."""
    since_dt = (datetime.datetime.now(datetime.timezone.utc)
                - datetime.timedelta(days=DAYS))
    since = since_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    totals = {}
    try:
        for page in (1, 2):
            repos, _ = api_get(
                f"{API}/users/{USERNAME}/repos?per_page=100&page={page}&type=owner")
            if not repos:
                break
            for repo in repos:
                if repo.get("fork") or repo.get("archived"):
                    continue
                lang = repo.get("language")
                if not lang:
                    continue
                try:
                    n = count_commits(repo["full_name"], since)
                except Exception as exc:
                    print(f"warning: {repo['full_name']}: {exc}")
                    continue
                if n:
                    totals[lang] = totals.get(lang, 0) + n
            if len(repos) < 100:
                break
    except Exception as exc:
        print(f"warning: GitHub API unavailable ({exc}), rendering empty state")

    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    top = ranked[:TOP_N]
    rest = sum(n for _, n in ranked[TOP_N:])
    if rest:
        top.append(("Other", rest))
    return top


def build_svg(entries):
    W = 720
    ROW_H, TOP = 32, 78
    rows = max(len(entries), 1)
    H = TOP + rows * ROW_H + 72
    LX, BAR_X, BAR_W, RX = 62, 200, 360, 680
    total = sum(n for _, n in entries)
    generated = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    body = []
    if not entries:
        body.append(
            f'<text x="360" y="{TOP + 20}" text-anchor="middle" '
            f'font-family="JetBrains Mono,monospace" font-size="11" fill="#8b949e">'
            f'No commits in the last {DAYS} days</text>')
    for i, (lang, n) in enumerate(entries):
        y = TOP + i * ROW_H
        color = LANG_COLORS.get(lang, DEFAULT_COLOR)
        pct = (n / total * 100) if total else 0
        w = max(6.0, BAR_W * (n / entries[0][1])) if entries[0][1] else 6.0
        plural = "s" if n != 1 else ""
        body.append(
            f'<g><title>{lang}: {n} commit{plural} ({pct:.0f}%)</title>'
            f'<circle cx="48" cy="{y + 9}" r="5" fill="{color}"/>'
            f'<text x="{LX}" y="{y + 13}" font-family="JetBrains Mono,monospace" '
            f'font-size="11" font-weight="700" fill="#e6edf3">{lang}</text>'
            f'<rect x="{BAR_X}" y="{y}" width="{BAR_W}" height="12" rx="6" fill="#21262d"/>'
            f'<rect x="{BAR_X}" y="{y}" width="{w:.1f}" height="12" rx="6" '
            f'fill="{color}" opacity="0.9"/>'
            f'<text x="{RX}" y="{y + 12}" text-anchor="end" '
            f'font-family="JetBrains Mono,monospace" font-size="10" fill="#8b949e">'
            f'{n} · {pct:.0f}%</text></g>')
    body_str = "\n  ".join(body)
    foot_y = TOP + rows * ROW_H

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0d1117"/>
      <stop offset="100%" stop-color="#111827"/>
    </linearGradient>
  </defs>

  <rect width="{W}" height="{H}" rx="12" fill="url(#bg)" stroke="#21262d" stroke-width="1"/>

  <rect width="{W}" height="36" rx="12" fill="#161b22"/>
  <rect y="24" width="{W}" height="12" fill="#161b22"/>
  <rect y="35" width="{W}" height="1" fill="#21262d"/>
  <circle cx="18" cy="18" r="5.5" fill="#FF5F57"/>
  <circle cx="36" cy="18" r="5.5" fill="#FFBD2E"/>
  <circle cx="54" cy="18" r="5.5" fill="#28C840"/>
  <text x="360" y="22" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="11" fill="#8b949e">TOP LANGUAGES · BY COMMITS · LAST {DAYS} DAYS</text>

  <text x="40" y="56" font-family="JetBrains Mono,monospace" font-size="9" font-weight="700" fill="#00D9FF">{USERNAME.upper()} / LANGS</text>
  <text x="680" y="56" text-anchor="end" font-family="JetBrains Mono,monospace" font-size="9" fill="#8b949e">total {total} commits · forks excluded</text>

  {body_str}

  <line x1="0" y1="{foot_y + 14}" x2="720" y2="{foot_y + 14}" stroke="#21262d" stroke-width="1"/>
  <text x="40" y="{foot_y + 32}" font-family="JetBrains Mono,monospace" font-size="9" fill="#484f58">generated {generated} · self-hosted, no third-party widgets</text>
  <text x="680" y="{foot_y + 32}" text-anchor="end" font-family="JetBrains Mono,monospace" font-size="9" fill="#484f58">$ git shortlog -sne</text>

  <line x1="0" y1="{foot_y + 42}" x2="720" y2="{foot_y + 42}" stroke="#21262d" stroke-width="1"/>
  <text x="360" y="{foot_y + 58}" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="9" fill="#484f58" font-style="italic">"Right tool for the job."</text>
</svg>
"""


def main():
    entries = collect_lang_commits()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(build_svg(entries))
    print(f"{OUT} written: " + (", ".join(f"{l}={n}" for l, n in entries) or "empty"))


if __name__ == "__main__":
    main()
