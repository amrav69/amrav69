#!/usr/bin/env python3
"""Generate a self-hosted commit activity SVG (activity.svg) for the profile README.

Data source: public PushEvents from the GitHub REST API (no third-party services).
- Counts commits per day over the last 30 days (UTC).
- Never fails the workflow: on API errors it renders a graceful empty state.
- Style matches card.svg / card2.svg: dark bg, monospace, cyan/orange accents.

Usage:
    python gen_activity.py
Env:
    GITHUB_USER   (default: amrav69)
    GITHUB_TOKEN  (optional, raises API rate limit)
    DAYS          (default: 30)
    OUT           (default: activity.svg)
"""

import datetime
import json
import os
import urllib.request
import urllib.error

USERNAME = os.environ.get("GITHUB_USER", "amrav69")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
DAYS = int(os.environ.get("DAYS", "30"))
OUT = os.environ.get("OUT", "activity.svg")

API = "https://api.github.com"
UA = {"User-Agent": "amrav69-profile-activity"}


def api_get(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA["User-Agent"],
        "Accept": "application/vnd.github+json",
        **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def collect_daily_counts():
    """Return (days, counts) for the last DAYS days (oldest -> newest, UTC)."""
    today = datetime.datetime.now(datetime.timezone.utc).date()
    start = today - datetime.timedelta(days=DAYS - 1)
    days = [start + datetime.timedelta(days=i) for i in range(DAYS)]
    counts = {d.isoformat(): 0 for d in days}

    try:
        events = []
        for page in range(1, 5):  # up to 400 events, plenty for this volume
            try:
                batch = api_get(
                    f"{API}/users/{USERNAME}/events/public?per_page=100&page={page}")
            except urllib.error.HTTPError as e:
                if e.code == 422:
                    break  # past the last available page: normal end of data
                raise
            if not batch:
                break
            events.extend(batch)
            oldest = min(e.get("created_at", "")[:10] for e in batch)
            if oldest < start.isoformat():
                break

        compares = 0
        for e in events:
            if e.get("type") != "PushEvent":
                continue
            day = e.get("created_at", "")[:10]
            if day < start.isoformat() or day > today.isoformat():
                continue
            n = 1
            payload = e.get("payload", {})
            repo = e.get("repo", {}).get("name", "")
            before, head = payload.get("before", ""), payload.get("head", "")
            # Resolve real commit count via compare API (events API omits it).
            if TOKEN and repo and before and head and not before.startswith("0000"):
                if compares < 50:
                    compares += 1
                    try:
                        cmp_data = api_get(
                            f"{API}/repos/{repo}/compare/{before}...{head}")
                        n = max(1, int(cmp_data.get("ahead_by", 1)))
                    except Exception:
                        n = 1
            counts[day] += n
    except Exception as exc:
        print(f"warning: GitHub API unavailable ({exc}), rendering empty state")

    return days, [counts[d.isoformat()] for d in days]


def build_svg(days, counts):
    W, H = 720, 280
    CX, CY, CW, CH = 40, 70, 640, 130
    total = sum(counts)
    active = sum(1 for c in counts if c > 0)
    max_c = max(counts) if counts else 0
    max_i = counts.index(max_c) if max_c else -1
    generated = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    def fmt(d):
        return d.strftime("%b %-d") if os.name != "nt" else d.strftime("%b %#d")

    # Gridlines
    grid = []
    for frac, label in ((1.0, max_c), (0.5, round(max_c / 2) if max_c else 0), (0, 0)):
        y = CY + CH - frac * (CH - 8)
        grid.append(
            f'<line x1="{CX}" y1="{y:.1f}" x2="{CX + CW}" y2="{y:.1f}" '
            f'stroke="#21262d" stroke-width="0.5" stroke-dasharray="3,5"/>'
            f'<text x="{CX - 6}" y="{y + 3:.1f}" text-anchor="end" '
            f'font-family="JetBrains Mono,monospace" font-size="8" fill="#484f58">{label}</text>'
        )
    grid_str = "\n  ".join(grid)

    # Bars
    bars = []
    slot = CW / len(counts)
    bw = slot * 0.58
    for i, c in enumerate(counts):
        x = CX + i * slot + (slot - bw) / 2
        if c <= 0:
            bars.append(
                f'<circle cx="{x + bw / 2:.1f}" cy="{CY + CH - 1:.1f}" r="1.2" fill="#21262d"/>')
            continue
        h = max(4.0, (c / max_c) * (CH - 8)) if max_c else 4.0
        y = CY + CH - h
        color = "#FF6B35" if i == max_i else "#00D9FF"
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" '
            f'fill="{color}" rx="2.5" opacity="0.92"/>')
    bars_str = "\n  ".join(bars)

    max_note = ""
    if max_c > 0:
        bx = CX + max_i * slot + slot / 2
        by = CY + CH - max(4.0, CH - 8) - 10
        max_note = (
            f'<text x="{bx:.1f}" y="{by:.1f}" text-anchor="middle" '
            f'font-family="JetBrains Mono,monospace" font-size="9" font-weight="700" '
            f'fill="#FF6B35">{max_c}</text>'
        )

    if total == 0:
        empty_msg = (
            f'<text x="{CX + CW / 2}" y="{CY + CH / 2}" text-anchor="middle" '
            f'font-family="JetBrains Mono,monospace" font-size="11" fill="#8b949e">'
            f'No public commits in the last {DAYS} days</text>'
        )
    else:
        empty_msg = ""

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
  <text x="360" y="22" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="11" fill="#8b949e">COMMIT ACTIVITY · LAST {DAYS} DAYS</text>

  <text x="{CX}" y="56" font-family="JetBrains Mono,monospace" font-size="9" font-weight="700" fill="#00D9FF">{USERNAME.upper()} / COMMITS</text>
  <text x="{CX + CW}" y="56" text-anchor="end" font-family="JetBrains Mono,monospace" font-size="9" fill="#8b949e">total {total} · {active} active days</text>

  {grid_str}

  {bars_str}
  {max_note}
  {empty_msg}

  <rect x="{CX}" y="{CY}" width="{CW}" height="{CH}" rx="2" fill="none" stroke="#21262d" stroke-width="1"/>

  <text x="{CX}" y="216" font-family="JetBrains Mono,monospace" font-size="8" fill="#484f58">{fmt(days[0])}</text>
  <text x="{CX + CW // 2}" y="216" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="8" fill="#484f58">{fmt(days[len(days) // 2])}</text>
  <text x="{CX + CW}" y="216" text-anchor="end" font-family="JetBrains Mono,monospace" font-size="8" fill="#484f58">{fmt(days[-1])}</text>

  <line x1="0" y1="232" x2="720" y2="232" stroke="#21262d" stroke-width="1"/>
  <text x="{CX}" y="250" font-family="JetBrains Mono,monospace" font-size="9" fill="#484f58">generated {generated} · self-hosted, no third-party widgets</text>
  <text x="{CX + CW}" y="250" text-anchor="end" font-family="JetBrains Mono,monospace" font-size="9" fill="#484f58">$ git log --since="30.days"</text>

  <line x1="0" y1="258" x2="720" y2="258" stroke="#21262d" stroke-width="1"/>
  <text x="360" y="272" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="9" fill="#484f58" font-style="italic">"Small commits daily beat heroic rewrites."</text>
</svg>
"""


def main():
    days, counts = collect_daily_counts()
    svg = build_svg(days, counts)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"{OUT} written: total={sum(counts)} active={sum(1 for c in counts if c)}")


if __name__ == "__main__":
    main()
