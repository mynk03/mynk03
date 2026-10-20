#!/usr/bin/env python3
"""Write the section heading SVGs used by README.md into profile/headings/.

    python3 scripts/headings.py

Colors match the cards palette in .github/workflows/cards.yml. Readable on
both GitHub light and dark themes, so no <picture> switch is needed.
"""
import os
from xml.sax.saxutils import escape

ACCENT, ICON, MUTED = "C13CCC", "E4572E", "8B949E"
W, H = 900, 64
FONT = "Segoe UI, Ubuntu, Helvetica, Arial, sans-serif"
MONO = "SFMono-Regular, Consolas, Liberation Mono, Menlo, monospace"

SECTIONS = [
    ("about", "About Me", "who I am and what I build"),
    ("stack", "Tech Stack", "tools I ship with"),
    ("work", "Featured Work", "selected projects"),
    ("highlights", "Highlights", "a few milestones"),
    ("stats", "GitHub Stats", "activity at a glance"),
    ("connect", "Connect", "let's build something"),
]


def svg(num, title, sub):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="t" x1="0" x2="1">
      <stop offset="0" stop-color="#{ACCENT}"/>
      <stop offset="1" stop-color="#{ICON}"/>
    </linearGradient>
    <linearGradient id="u" x1="0" x2="1">
      <stop offset="0" stop-color="#{ACCENT}"/>
      <stop offset="0.45" stop-color="#{ICON}" stop-opacity="0.6"/>
      <stop offset="1" stop-color="#{ICON}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect x="1.5" y="12" width="46" height="30" rx="6" fill="none" stroke="url(#t)" stroke-width="2"/>
  <text x="24.5" y="32.5" text-anchor="middle" font-family="{MONO}" font-size="14" font-weight="700" fill="#{ICON}">{num:02d}</text>
  <text x="62" y="37" font-family="{FONT}" font-size="28" font-weight="700" fill="url(#t)">{escape(title)}</text>
  <text x="{W - 4}" y="37" text-anchor="end" font-family="{MONO}" font-size="13" fill="#{MUTED}">// {escape(sub)}</text>
  <rect x="0" y="54" width="{W}" height="2" rx="1" fill="url(#u)"/>
</svg>
'''


def main():
    out = os.path.join(os.path.dirname(__file__), "..", "profile", "headings")
    os.makedirs(out, exist_ok=True)
    for i, (slug, title, sub) in enumerate(SECTIONS, 1):
        with open(os.path.join(out, f"{slug}.svg"), "w") as f:
            f.write(svg(i, title, sub))


if __name__ == "__main__":
    main()
