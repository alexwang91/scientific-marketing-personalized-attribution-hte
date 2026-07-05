"""Minimal inline-SVG chart primitives — pure stdlib, no JS, no network.

Shared by generate_report.py (document report) and dashboard_render.py
(interactive cockpit) so both render the identical frontier chart from the
identical (x, y) points — real markup a reader (and a test) can see with no
network access, not an ECharts placeholder.

Domain-agnostic: takes plain (x, y) tuples and colors, nothing else.
"""

from __future__ import annotations

from html import escape


def line_panel(points: list, cutoff_x: float | None = None, color: str = "#4f46e5",
               width: int = 520, height: int = 190) -> str:
    """Line + dot chart over arbitrary (x, y) points, sorted by x. Draws the
    zero line when the y-range straddles zero, and a dashed cutoff marker at
    cutoff_x when it falls inside the plotted x-range."""
    if not points:
        return '<div class="inv-svg-empty">—</div>'
    pts = sorted(points, key=lambda p: p[0])
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(0.0, min(ys)), max(ys)
    if x_max == x_min:
        x_max = x_min + 1
    if y_max == y_min:
        y_max = y_min + 1
    pad_l, pad_r, pad_t, pad_b = 50, 14, 12, 24
    plot_w, plot_h = width - pad_l - pad_r, height - pad_t - pad_b

    def sx(x): return pad_l + (x - x_min) / (x_max - x_min) * plot_w

    def sy(y): return pad_t + plot_h - (y - y_min) / (y_max - y_min) * plot_h

    poly = " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in pts)
    dots = "".join(f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="2.6" fill="{color}"/>' for x, y in pts)
    zero_y = sy(0.0) if y_min <= 0.0 <= y_max else None
    zero_line = (f'<line x1="{pad_l}" y1="{zero_y:.1f}" x2="{pad_l + plot_w}" y2="{zero_y:.1f}" '
                 f'stroke="#cbd5e1" stroke-width="1"/>') if zero_y is not None else ""
    cutoff_line = ""
    if cutoff_x is not None and x_min <= cutoff_x <= x_max:
        cx = sx(cutoff_x)
        cutoff_line = (f'<line x1="{cx:.1f}" y1="{pad_t}" x2="{cx:.1f}" y2="{pad_t + plot_h}" '
                       f'stroke="#dc2626" stroke-width="1.5" stroke-dasharray="4,3"/>')
    x_min_txt = escape(f"{x_min:,.0f}")
    x_max_txt = escape(f"{x_max:,.0f}")
    return f"""<svg class="inv-svg" viewBox="0 0 {width} {height}" role="img">
  <line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t + plot_h}" stroke="#94a3b8" stroke-width="1"/>
  <line x1="{pad_l}" y1="{pad_t + plot_h}" x2="{pad_l + plot_w}" y2="{pad_t + plot_h}" stroke="#94a3b8" stroke-width="1"/>
  {zero_line}
  {cutoff_line}
  <polyline points="{poly}" fill="none" stroke="{color}" stroke-width="2.2"/>
  {dots}
  <text x="{pad_l}" y="{height - 6}" font-size="9" fill="#64748b">{x_min_txt}</text>
  <text x="{pad_l + plot_w}" y="{height - 6}" font-size="9" fill="#64748b" text-anchor="end">{x_max_txt}</text>
</svg>"""
