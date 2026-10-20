#!/usr/bin/env python3
"""Render a 31-day contribution line graph as an SVG.

    GH_TOKEN=... python3 scripts/activity_graph.py <user> <out.svg>

Colors come from the BG / ACCENT / ICON / TEXT env vars (hex, no #),
the same palette the cards workflow passes to the other cards.
"""
import json
import os
import sys
import urllib.request

DAYS = 31
W, H = 900, 320
PAD_L, PAD_R, PAD_T, PAD_B = 56, 28, 64, 48

QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch(user, token):
    body = json.dumps({"query": QUERY, "variables": {"login": user}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if data.get("errors"):
        raise SystemExit(f"graphql error: {data['errors']}")
    u = data["data"]["user"]
    weeks = u["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    return (u["name"] or user), days[-DAYS:]


def nice_max(v):
    for step in (4, 8, 12, 20, 40, 60, 100, 200, 400, 1000):
        if v <= step:
            return step
    return v


def render(name, days, c):
    counts = [d["contributionCount"] for d in days]
    top = nice_max(max(counts) or 1)
    plot_w, plot_h = W - PAD_L - PAD_R, H - PAD_T - PAD_B
    step = plot_w / (len(days) - 1)

    def xy(i, v):
        return PAD_L + i * step, PAD_T + plot_h - v / top * plot_h

    pts = [xy(i, v) for i, v in enumerate(counts)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    base = PAD_T + plot_h
    area = f"{PAD_L:.1f},{base:.1f} {line} {pts[-1][0]:.1f},{base:.1f}"

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="Segoe UI, Ubuntu, Helvetica, Arial, sans-serif">',
        f'<rect width="{W}" height="{H}" rx="10" fill="#{c["BG"]}"/>',
        f'<text x="{W / 2}" y="38" text-anchor="middle" font-size="20" font-weight="600" '
        f'fill="#{c["ACCENT"]}">{name.split()[0]}\'s Contribution Graph</text>',
    ]
    for k in range(5):
        v = top * k / 4
        y = base - k / 4 * plot_h
        out.append(f'<line x1="{PAD_L}" y1="{y:.1f}" x2="{W - PAD_R}" y2="{y:.1f}" stroke="#{c["TEXT"]}" stroke-opacity="0.08"/>')
        out.append(f'<text x="{PAD_L - 10}" y="{y + 4:.1f}" text-anchor="end" font-size="11" fill="#{c["TEXT"]}" fill-opacity="0.7">{v:g}</text>')
    for i, d in enumerate(days):
        if i % 2 == 0:
            x = PAD_L + i * step
            out.append(f'<text x="{x:.1f}" y="{base + 20}" text-anchor="middle" font-size="11" fill="#{c["TEXT"]}" fill-opacity="0.7">{int(d["date"][8:])}</text>')
    out.append(f'<text x="{W / 2}" y="{H - 6}" text-anchor="middle" font-size="11" fill="#{c["TEXT"]}" fill-opacity="0.5">'
               f'{days[0]["date"]} to {days[-1]["date"]}</text>')
    out.append(f'<polygon points="{area}" fill="#{c["ACCENT"]}" fill-opacity="0.18"/>')
    out.append(f'<polyline points="{line}" fill="none" stroke="#{c["ACCENT"]}" stroke-width="2.5" stroke-linejoin="round"/>')
    for (x, y), v in zip(pts, counts):
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#{c["ICON"]}"><title>{v}</title></circle>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    user, path = sys.argv[1:]
    colors = {k: os.environ.get(k, d) for k, d in
              (("BG", "151515"), ("ACCENT", "C13CCC"), ("ICON", "E4572E"), ("TEXT", "E6EDF3"))}
    name, days = fetch(user, os.environ["GH_TOKEN"])
    with open(path, "w") as f:
        f.write(render(name, days, colors))


if __name__ == "__main__":
    main()
