"""Draw char-model/images/char-loss-<epoch>.svg from results.json — the real loss curve, one highlighted epoch each.

    uv run --no-project python char-model/plot_loss.py
"""

import json
import math
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "images"
W, H, L, R, T, B = 420, 250, 56, 18, 20, 44
res = json.loads((HERE / "results.json").read_text())
pts = [(r["epoch"], r["val"]) for r in res["losses"]]
train = [(r["epoch"], r["train"]) for r in res["losses"]]
lo = math.floor(min(v for _, v in train) * 2) / 2
hi = math.ceil(max(v for _, v in pts + train) * 2) / 2
last = pts[-1][0]


def sx(e):  # log scale so epochs 1, 5, 10, 100 spread out
    return L + (W - L - R) * math.log10(e) / math.log10(last)


def sy(v):
    return T + (H - T - B) * (hi - v) / (hi - lo)


def line(series):
    return " ".join(f"{'M' if i == 0 else 'L'}{sx(e):.1f} {sy(v):.1f}" for i, (e, v) in enumerate(series))


path, train_path = line(pts), line(train)
best = min(pts, key=lambda p: p[1])
grid = "".join(
    f'<line x1="{L}" y1="{sy(v):.1f}" x2="{W - R}" y2="{sy(v):.1f}" stroke="#2a2f3c"/>'
    f'<text x="{L - 8}" y="{sy(v) + 5:.1f}" fill="#9aa0b0" font-size="13" text-anchor="end">{v:.1f}</text>'
    for v in [lo + i * 0.5 for i in range(int((hi - lo) / 0.5) + 1)][::2]
)
ticks = "".join(
    f'<text x="{sx(e):.1f}" y="{H - B + 20}" fill="#9aa0b0" font-size="13" text-anchor="middle">{e}</text>'
    for e in (1, 5, 10, last)
)
for epoch in (1, 5, 10, last):
    v = dict(pts)[epoch]
    mark = (
        f'<line x1="{sx(epoch):.1f}" y1="{T}" x2="{sx(epoch):.1f}" y2="{H - B}" stroke="#f5b301" stroke-dasharray="4 4" stroke-opacity=".6"/>'
        f'<circle cx="{sx(epoch):.1f}" cy="{sy(v):.1f}" r="7" fill="#f5b301" stroke="#0f1117" stroke-width="2"/>'
    )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Inter, system-ui, sans-serif">
  <rect width="{W}" height="{H}" rx="10" fill="#0f1117"/>
  {grid}
  <line x1="{L}" y1="{H - B}" x2="{W - R}" y2="{H - B}" stroke="#9aa0b0" stroke-width="1.5"/>
  {ticks}
  <text x="{(L + W - R) / 2:.0f}" y="{H - 6}" fill="#9aa0b0" font-size="13" text-anchor="middle">epoch (log scale)</text>
  <text x="16" y="{(T + H - B) / 2:.0f}" fill="#9aa0b0" font-size="13" text-anchor="middle" transform="rotate(-90 16 {(T + H - B) / 2:.0f})">loss</text>
  <path d="{train_path}" fill="none" stroke="#9aa0b0" stroke-width="2" stroke-dasharray="5 4"/>
  <path d="{path}" fill="none" stroke="#ffd45c" stroke-width="3" stroke-opacity=".85"/>
  <circle cx="{sx(best[0]):.1f}" cy="{sy(best[1]):.1f}" r="4" fill="#6fd08c"/>
  <text x="{sx(best[0]):.1f}" y="{sy(best[1]) - 12:.1f}" fill="#6fd08c" font-size="12" text-anchor="middle">best: epoch {best[0]}</text>
  <text x="{W - R}" y="{sy(pts[-1][1]) - 10:.1f}" fill="#ffd45c" font-size="12" text-anchor="end">unseen text</text>
  <text x="{W - R}" y="{sy(train[-1][1]) - 10:.1f}" fill="#9aa0b0" font-size="12" text-anchor="end">training text</text>
  {mark}
</svg>
"""
    OUT.mkdir(exist_ok=True)
    (OUT / f"char-loss-{epoch}.svg").write_text(svg)
print("wrote", [f"char-loss-{e}.svg" for e in (1, 5, 10, last)])
