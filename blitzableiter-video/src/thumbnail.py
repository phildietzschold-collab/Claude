# -*- coding: utf-8 -*-
"""YouTube-Thumbnail (1280x720) im Stil des Videos."""
from pathlib import Path

import cairo

from gfx import *  # noqa: F401,F403

ROOT = Path(__file__).resolve().parent.parent
TW, TH = 1280, 720

surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, TW, TH)
ctx = cairo.Context(surf)
ctx.scale(TW / W, TH / H)

wx = Weather(seed=5)
wx.sky(ctx)
wx.draw_clouds(ctx, 3.0, flash=0.55)
wx.draw_rain(ctx, 1.3, 0.8)
# Lichtschein hinter dem Einschlag
g = cairo.RadialGradient(1380, 300, 20, 1380, 300, 700)
g.add_color_stop_rgba(0, 0.75, 0.82, 1.0, 0.55)
g.add_color_stop_rgba(1, 0.75, 0.82, 1.0, 0.0)
ctx.set_source(g)
ctx.paint()

ground(ctx, 900)
hs = house(ctx, 1380, 900, 560, 300, 210)
tip, path = draw_rod(ctx, hs, rod_h=150, soil=0, w=9)
bolt = bolt_points(1180, -40, tip[0], tip[1] - 20, seed=8, n=10, jit=70)
draw_bolt(ctx, bolt, 1.0, 1.0, 22)
flow(ctx, path, 0.3, YEL, 1.0, 10, speed=0)
circle(ctx, tip[0], tip[1] - 10, 60, WHITE, 0.35)
circle(ctx, tip[0], tip[1] - 10, 28, WHITE, 0.9)


def big(s, x, y, size, col):
    set_font(ctx, size, family="Inter")
    ctx.new_path()
    ctx.move_to(x, y)
    ctx.text_path(s)
    ctx.set_source_rgba(0, 0, 0, 1)
    ctx.set_line_width(size * 0.16)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke_preserve()
    rgba(ctx, col)
    ctx.fill()


big("ZIEHT ER", 70, 330, 190, WHITE)
big("BLITZE AN?", 70, 540, 190, YEL)
fill_rrect(ctx, 80, 640, 640, 110, 55, RED, 1)
text(ctx, "Blitzableiter erklärt", 400, 695, 56, WHITE)

out = ROOT / "Thumbnail.png"
surf.write_to_png(str(out))
print("Thumbnail:", out)
