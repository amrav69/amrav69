#!/usr/bin/env python3
"""Generate algo trading terminal SVG (card2.svg) for amrav69 GitHub profile."""

# Chart config
CX, CY, CW, CH = 20, 52, 400, 155

candles = [
    (100.0, 103.2, 98.1, 102.3),
    (102.3, 105.1, 101.0, 104.2),
    (104.2, 106.0, 101.5, 102.0),
    (102.0, 103.5, 97.8,  99.1),
    ( 99.1, 102.4, 97.2, 101.5),
    (101.5, 104.3, 100.2, 103.1),
    (103.1, 107.2, 102.0, 106.4),
    (106.4, 108.5, 104.1, 105.2),
    (105.2, 107.0, 103.3, 104.8),
    (104.8, 106.5, 102.8, 105.9),
    (105.9, 109.3, 104.5, 108.1),
    (108.1, 111.2, 107.0, 110.3),
    (110.3, 112.5, 108.4, 109.1),
    (109.1, 112.8, 108.0, 111.7),
    (111.7, 115.4, 110.2, 114.3),
    (114.3, 116.8, 112.1, 115.6),
    (115.6, 118.9, 114.0, 117.2),
    (117.2, 119.6, 115.8, 118.9),
    (118.9, 122.3, 117.1, 120.7),
    (120.7, 123.5, 118.5, 122.1),
]

MIN_P, MAX_P = 97.0, 124.5
P_RANGE = MAX_P - MIN_P

def py(price):
    return CY + CH - (price - MIN_P) / P_RANGE * CH

slot_w = CW / len(candles)
body_w = slot_w * 0.62
close_prices = [c[3] for c in candles]

# --- Grid lines ---
grid = []
for price in [99, 105, 111, 117, 123]:
    y = py(price)
    grid.append(
        f'<line x1="{CX}" y1="{y:.1f}" x2="{CX+CW}" y2="{y:.1f}" '
        f'stroke="#21262d" stroke-width="0.5" stroke-dasharray="3,5"/>'
    )
    grid.append(
        f'<text x="{CX-4}" y="{y+3:.1f}" text-anchor="end" '
        f'font-family="JetBrains Mono,monospace" font-size="8" fill="#484f58">{price}</text>'
    )
grid_str = "\n  ".join(grid)

# --- Candles ---
bodies = []
sma_pts = []
PERIOD = 5
for i, (o, h, l, c) in enumerate(candles):
    x = CX + i * slot_w + (slot_w - body_w) / 2
    mid = x + body_w / 2
    color = "#3fb950" if c >= o else "#f85149"

    bodies.append(
        f'<line x1="{mid:.1f}" y1="{py(h):.1f}" x2="{mid:.1f}" y2="{py(l):.1f}" '
        f'stroke="{color}" stroke-width="1" opacity="0.55"/>'
    )
    bt = py(max(o, c))
    bh = max(py(min(o, c)) - bt, 2.0)
    bodies.append(
        f'<rect x="{x:.1f}" y="{bt:.1f}" width="{body_w:.1f}" height="{bh:.1f}" '
        f'fill="{color}" rx="1.5"/>'
    )
    if i >= PERIOD - 1:
        sma = sum(close_prices[i - PERIOD + 1:i + 1]) / PERIOD
        sma_pts.append(f"{mid:.1f},{py(sma):.1f}")

bodies_str = "\n  ".join(bodies)
sma_path = "M " + " L ".join(sma_pts)
last_y = py(122.1)

SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="280" viewBox="0 0 720 280">
  <defs>
    <filter id="glow">
      <feGaussianBlur stdDeviation="2.5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="glow-sm">
      <feGaussianBlur stdDeviation="1.5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0d1117"/>
      <stop offset="100%" stop-color="#111827"/>
    </linearGradient>
  </defs>

  <!-- BG -->
  <rect width="720" height="280" rx="12" fill="url(#bg)" stroke="#21262d" stroke-width="1"/>

  <!-- Title bar -->
  <rect width="720" height="36" rx="12" fill="#161b22"/>
  <rect y="24" width="720" height="12" fill="#161b22"/>
  <rect y="35" width="720" height="1" fill="#21262d"/>
  <circle cx="18" cy="18" r="5.5" fill="#FF5F57"/>
  <circle cx="36" cy="18" r="5.5" fill="#FFBD2E"/>
  <circle cx="54" cy="18" r="5.5" fill="#28C840"/>
  <text x="360" y="22" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="11" fill="#8b949e">AGENTIC-QUANT-SANDBOX · LIVE ANALYSIS</text>

  <!-- Chart header -->
  <text x="{CX}" y="48" font-family="JetBrains Mono,monospace" font-size="9" font-weight="700" fill="#00D9FF">AQS / USD</text>
  <text x="120" y="48" font-family="JetBrains Mono,monospace" font-size="9" fill="#3fb950">&#9650; +22.1%</text>
  <text x="210" y="48" font-family="JetBrains Mono,monospace" font-size="9" fill="#8b949e">1D  SMA5</text>

  <!-- Grid -->
  {grid_str}

  <!-- Candles -->
  {bodies_str}

  <!-- SMA glow line -->
  <path d="{sma_path}" fill="none" stroke="#00D9FF" stroke-width="2" opacity="0.3" filter="url(#glow)"/>
  <path d="{sma_path}" fill="none" stroke="#00D9FF" stroke-width="1"/>

  <!-- Last price dashed line -->
  <line x1="{CX}" y1="{last_y:.1f}" x2="{CX+CW}" y2="{last_y:.1f}" stroke="#00D9FF" stroke-width="0.7" stroke-dasharray="3,4" opacity="0.45"/>
  <rect x="{CX+CW-35}" y="{last_y-8:.1f}" width="34" height="14" rx="3" fill="#00D9FF22" stroke="#00D9FF" stroke-width="0.8"/>
  <text x="{CX+CW-18}" y="{last_y+3.5:.1f}" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="8" fill="#00D9FF">122.1</text>

  <!-- Chart border -->
  <rect x="{CX}" y="{CY}" width="{CW}" height="{CH}" rx="2" fill="none" stroke="#21262d" stroke-width="1"/>

  <!-- X labels -->
  <text x="{CX}" y="218" font-family="JetBrains Mono,monospace" font-size="8" fill="#484f58">Aug</text>
  <text x="{CX+CW//2}" y="218" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="8" fill="#484f58">Sep</text>
  <text x="{CX+CW}" y="218" text-anchor="end" font-family="JetBrains Mono,monospace" font-size="8" fill="#484f58">Oct</text>

  <!-- Vertical divider -->
  <line x1="440" y1="40" x2="440" y2="258" stroke="#21262d" stroke-width="1"/>

  <!-- RIGHT: Agent Status -->
  <text x="456" y="57" font-family="JetBrains Mono,monospace" font-size="9" font-weight="700" fill="#00D9FF" letter-spacing="1">AGENT STATUS</text>

  <circle cx="460" cy="73" r="4" fill="#3fb950" filter="url(#glow-sm)"/>
  <text x="471" y="77" font-family="JetBrains Mono,monospace" font-size="10" fill="#e6edf3">RESEARCH</text>
  <rect x="638" y="66" width="64" height="16" rx="3" fill="#3fb95018" stroke="#3fb950" stroke-width="0.8"/>
  <text x="670" y="77" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="9" fill="#3fb950">ACTIVE</text>

  <circle cx="460" cy="95" r="4" fill="#FF6B35" filter="url(#glow-sm)"/>
  <text x="471" y="99" font-family="JetBrains Mono,monospace" font-size="10" fill="#e6edf3">CODEGEN</text>
  <rect x="628" y="88" width="74" height="16" rx="3" fill="#FF6B3518" stroke="#FF6B35" stroke-width="0.8"/>
  <text x="665" y="99" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="9" fill="#FF6B35">WRITING</text>

  <circle cx="460" cy="117" r="4" fill="#00D9FF" filter="url(#glow-sm)"/>
  <text x="471" y="121" font-family="JetBrains Mono,monospace" font-size="10" fill="#e6edf3">CRITIC</text>
  <rect x="622" y="110" width="80" height="16" rx="3" fill="#00D9FF18" stroke="#00D9FF" stroke-width="0.8"/>
  <text x="662" y="121" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="9" fill="#00D9FF">VALIDATING</text>

  <!-- Divider -->
  <line x1="452" y1="133" x2="712" y2="133" stroke="#21262d" stroke-width="1"/>

  <!-- Signal -->
  <text x="456" y="149" font-family="JetBrains Mono,monospace" font-size="9" font-weight="700" fill="#00D9FF" letter-spacing="1">LAST SIGNAL</text>
  <rect x="456" y="155" width="52" height="18" rx="4" fill="#3fb95025" stroke="#3fb950" stroke-width="1"/>
  <text x="482" y="167" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="11" font-weight="700" fill="#3fb950">BUY</text>
  <text x="516" y="167" font-family="JetBrains Mono,monospace" font-size="10" fill="#8b949e">CONF</text>
  <text x="558" y="167" font-family="JetBrains Mono,monospace" font-size="10" font-weight="700" fill="#e6edf3">94%</text>

  <text x="456" y="186" font-family="JetBrains Mono,monospace" font-size="9" fill="#8b949e">Strategy   </text>
  <text x="520" y="186" font-family="JetBrains Mono,monospace" font-size="9" fill="#e6edf3">Trend Following</text>

  <text x="456" y="201" font-family="JetBrains Mono,monospace" font-size="9" fill="#8b949e">Risk       </text>
  <text x="520" y="201" font-family="JetBrains Mono,monospace" font-size="9" fill="#FFBD2E">1.2% / trade</text>

  <text x="456" y="216" font-family="JetBrains Mono,monospace" font-size="9" fill="#8b949e">Sharpe     </text>
  <text x="520" y="216" font-family="JetBrains Mono,monospace" font-size="9" fill="#e6edf3">2.41</text>

  <!-- Divider -->
  <line x1="452" y1="228" x2="712" y2="228" stroke="#21262d" stroke-width="1"/>

  <!-- Blinking prompt -->
  <text x="456" y="245" font-family="JetBrains Mono,monospace" font-size="10" fill="#00D9FF">&#10095;</text>
  <text x="470" y="245" font-family="JetBrains Mono,monospace" font-size="10" fill="#e6edf3">python run_agents.py --live</text>
  <rect x="582" y="233" width="7" height="13" rx="1" fill="#00D9FF" opacity="0.9"/>

  <!-- Footer motto -->
  <line x1="0" y1="258" x2="720" y2="258" stroke="#21262d" stroke-width="1"/>
  <text x="360" y="272" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="9" fill="#484f58" font-style="italic">"Build systems that think. Trade systems that don't."</text>
</svg>"""

with open("card2.svg", "w", encoding="utf-8") as f:
    f.write(SVG)

print("card2.svg written")
