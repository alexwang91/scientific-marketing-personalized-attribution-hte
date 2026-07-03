#!/usr/bin/env python3
"""Generate the repository key-visual (KV) banner.

Assembles the core visual story of the skill into one 1280x640 image
(GitHub social-preview size): the causal-personalization thesis, a Qini
curve, the uplift four-quadrant, the four-force mechanism, and the
provenance contract. Pure matplotlib — no network, fully reproducible.

    python make_kv.py            # writes ../../../../assets/hero.png
    python make_kv.py out.png    # custom path

The output is committed so the README and GitHub social card can use it
without a build step; re-run after any palette or messaging change.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.lines import Line2D

# ── palette (mirrors generate_report.py :root) ───────────────────────────
BG       = "#0f172a"   # deep slate (KV uses a dark hero for contrast)
PANEL    = "#1e293b"
PANEL_2  = "#172033"
INK      = "#f8fafc"
INK_2    = "#cbd5e1"
MUTED    = "#94a3b8"
LINE     = "#334155"
ACCENT   = "#818cf8"   # indigo-400, legible on dark
ACCENT_D = "#4f46e5"
OK       = "#4ade80"
WARN     = "#fbbf24"
BAD      = "#f87171"

FONT = {"family": "DejaVu Sans"}
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "text.color": INK,
    "axes.edgecolor": LINE,
})


def _panel(fig, x, y, w, h, fc=PANEL, ec=LINE, lw=1.2, radius=0.018):
    """Rounded panel in figure coordinates."""
    p = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        transform=fig.transFigure, facecolor=fc, edgecolor=ec,
        linewidth=lw, zorder=0,
    )
    fig.patches.append(p)
    return p


def _chart_axes(fig, rect):
    """Add an axes that sits above the rounded panels."""
    ax = fig.add_axes(rect)
    ax.set_facecolor("none")
    ax.set_zorder(5)
    return ax


def main(out: str) -> None:
    W, H = 1280, 640
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    fig.patch.set_facecolor(BG)

    # subtle top accent bar
    fig.patches.append(Rectangle((0, 0.972), 1, 0.028, transform=fig.transFigure,
                                 facecolor=ACCENT_D, edgecolor="none", zorder=2))

    # ── header band ──────────────────────────────────────────────────────
    fig.text(0.046, 0.86, "Scientific Marketing", fontsize=30, fontweight="bold",
             color=INK, va="center")
    fig.text(0.046, 0.785, "Causal Personalization  ·  HTE / Uplift / Incrementality",
             fontsize=14.5, color=ACCENT, va="center", fontweight="bold")
    fig.text(0.046, 0.726,
             "Traditional personalization asks who is likely to buy.\n"
             "Causal personalization asks who buys MORE because of your action.",
             fontsize=12.5, color=INK_2, va="top", linespacing=1.5)

    # tau equation chip (top-right)
    _panel(fig, 0.66, 0.80, 0.295, 0.115, fc=PANEL_2, ec=ACCENT_D, lw=1.4)
    fig.text(0.807, 0.8575, r"$\tau(x) = \mathbb{E}[\,Y(1) - Y(0)\mid X = x\,]$",
             fontsize=17, color=INK, ha="center", va="center")

    # ── four mini-panels ────────────────────────────────────────────────
    # layout grid (figure coords)
    pad = 0.046
    gap = 0.022
    pw = (1 - 2 * pad - 3 * gap) / 4
    py = 0.085
    ph = 0.545
    xs = [pad + i * (pw + gap) for i in range(4)]

    for x in xs:
        _panel(fig, x, py, pw, ph)

    # Panel 1 — Qini curve
    ax1 = _chart_axes(fig, [xs[0] + 0.012, py + 0.07, pw - 0.024, ph - 0.16])
    ax1.set_facecolor(PANEL)
    f = np.linspace(0, 1, 200)
    model = 1 - (1 - f) ** 2.1           # concave: good model
    rand = f                              # diagonal
    perfect = np.minimum(1, f * 2.3)
    ax1.fill_between(f, rand, model, color=ACCENT, alpha=0.20, zorder=1)
    ax1.plot(f, perfect, color=MUTED, lw=1.2, ls=(0, (4, 3)), zorder=2)
    ax1.plot(f, model, color=ACCENT, lw=2.6, zorder=3)
    ax1.plot(f, rand, color=MUTED, lw=1.4, zorder=2)
    ax1.set_xlim(0, 1); ax1.set_ylim(0, 1.05)
    ax1.set_xticks([]); ax1.set_yticks([])
    for s in ax1.spines.values():
        s.set_color(LINE)
    ax1.text(0.04, 0.92, "value the\nmodel creates", transform=ax1.transAxes,
             fontsize=8.5, color=ACCENT, va="top", linespacing=1.2, fontweight="bold")
    fig.text(xs[0] + pw / 2, py + ph - 0.052, "Qini / AUUC", fontsize=12.5,
             color=INK, ha="center", fontweight="bold")
    fig.text(xs[0] + pw / 2, py + 0.032, "does the model beat random?",
             fontsize=9, color=MUTED, ha="center")

    # Panel 2 — uplift four-quadrant
    ax2 = _chart_axes(fig, [xs[1] + 0.012, py + 0.07, pw - 0.024, ph - 0.16])
    ax2.set_facecolor(PANEL)
    ax2.set_xlim(0, 1); ax2.set_ylim(0, 1)
    ax2.axhline(0.5, color=LINE, lw=1); ax2.axvline(0.5, color=LINE, lw=1)
    # persuadables (top-left) highlighted
    ax2.add_patch(Rectangle((0, 0.5), 0.5, 0.5, facecolor=ACCENT, alpha=0.28))
    ax2.text(0.25, 0.75, "Persuadables\n✓ target", ha="center", va="center",
             fontsize=8.5, color=INK, fontweight="bold", linespacing=1.2)
    ax2.text(0.75, 0.75, "Sure\nThings", ha="center", va="center",
             fontsize=8, color=MUTED, linespacing=1.2)
    ax2.text(0.25, 0.25, "Lost\nCauses", ha="center", va="center",
             fontsize=8, color=MUTED, linespacing=1.2)
    ax2.text(0.75, 0.25, "Sleeping\nDogs", ha="center", va="center",
             fontsize=8, color=BAD, linespacing=1.2)
    ax2.set_xticks([]); ax2.set_yticks([])
    for s in ax2.spines.values():
        s.set_color(LINE)
    fig.text(xs[1] + pw / 2, py + ph - 0.052, "Who to target", fontsize=12.5,
             color=INK, ha="center", fontweight="bold")
    fig.text(xs[1] + pw / 2, py + 0.032, "uplift, not propensity",
             fontsize=9, color=MUTED, ha="center")

    # Panel 3 — four forces
    ax3 = _chart_axes(fig, [xs[2] + 0.012, py + 0.07, pw - 0.024, ph - 0.16])
    ax3.set_facecolor(PANEL)
    ax3.set_xlim(0, 1); ax3.set_ylim(0, 1)
    ax3.set_xticks([]); ax3.set_yticks([])
    for s in ax3.spines.values():
        s.set_color(LINE)
    forces = [("Push", OK, 0.80), ("Pull", OK, 0.62),
              ("Habit", BAD, 0.40), ("Anxiety", BAD, 0.22)]
    for name, col, yy in forces:
        val = 0.72 if col == OK else 0.62
        ax3.add_patch(Rectangle((0.30, yy - 0.055), val * 0.55, 0.11,
                                facecolor=col, alpha=0.85, edgecolor="none"))
        ax3.text(0.27, yy, name, ha="right", va="center", fontsize=9,
                 color=INK, fontweight="bold")
    ax3.annotate("", xy=(0.92, 0.06), xytext=(0.30, 0.06),
                 arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.2))
    ax3.text(0.30, 0.93, "toward buy", fontsize=8, color=OK, fontweight="bold")
    ax3.text(0.30, 0.05, "against", fontsize=7.5, color=MUTED, va="bottom")
    fig.text(xs[2] + pw / 2, py + ph - 0.052, "Four Forces", fontsize=12.5,
             color=INK, ha="center", fontweight="bold")
    fig.text(xs[2] + pw / 2, py + 0.032, "which lever moves τ(x)",
             fontsize=9, color=MUTED, ha="center")

    # Panel 4 — provenance contract
    ax4 = _chart_axes(fig, [xs[3] + 0.012, py + 0.07, pw - 0.024, ph - 0.16])
    ax4.set_facecolor(PANEL)
    ax4.set_xlim(0, 1); ax4.set_ylim(0, 1)
    ax4.set_xticks([]); ax4.set_yticks([])
    for s in ax4.spines.values():
        s.set_color(LINE)
    states = [("Sourced", OK, "◆"), ("Assumed", WARN, "◇"),
              ("Derived", ACCENT, "⊕"), ("Missing", MUTED, "○")]
    for i, (name, col, mark) in enumerate(states):
        yy = 0.80 - i * 0.205
        ax4.add_patch(Rectangle((0.10, yy - 0.07), 0.80, 0.14,
                                facecolor=col, alpha=0.16, edgecolor=col, lw=1.1))
        ax4.text(0.18, yy, mark, ha="center", va="center", fontsize=11, color=col)
        ax4.text(0.30, yy, name, ha="left", va="center", fontsize=9.5,
                 color=INK, fontweight="bold")
    fig.text(xs[3] + pw / 2, py + ph - 0.052, "Provenance", fontsize=12.5,
             color=INK, ha="center", fontweight="bold")
    fig.text(xs[3] + pw / 2, py + 0.032, "no fabricated numbers",
             fontsize=9, color=MUTED, ha="center")

    # ── footer strip ────────────────────────────────────────────────────
    fig.text(0.046, 0.038,
             "experiment-first · provenance contract · adversarial review · "
             "6 validated scripts · 19 references",
             fontsize=10, color=MUTED, va="center")
    fig.text(0.954, 0.038, "packaged as a Claude Code skill", fontsize=10,
             color=ACCENT, va="center", ha="right", fontweight="bold")

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=100, facecolor=BG)
    print(f"KV banner written to {out_path}  ({W}x{H})")


if __name__ == "__main__":
    default = Path(__file__).resolve().parents[4] / "assets" / "hero.png"
    main(sys.argv[1] if len(sys.argv) > 1 else str(default))
