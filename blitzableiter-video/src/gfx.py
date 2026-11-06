# -*- coding: utf-8 -*-
"""Zeichen-Helfer (pycairo): Formen, Text, Blitze, Häuser, Wetter."""
import math
import random

import cairo

W, H, FPS = 1920, 1080, 30

YEL = (1.0, 0.83, 0.22)
WHITE = (1, 1, 1)
RED = (0.95, 0.28, 0.27)
GREEN = (0.32, 0.86, 0.47)
BLUE = (0.38, 0.62, 1.0)
ORANGE = (1.0, 0.55, 0.15)
INK = (0.04, 0.05, 0.09)
WALL = (0.20, 0.24, 0.36)
WALL_D = (0.14, 0.17, 0.27)
ROOF = (0.33, 0.20, 0.24)
ROOF_D = (0.24, 0.14, 0.18)
GROUND = (0.07, 0.09, 0.13)
SOIL = (0.17, 0.12, 0.10)
METAL = (0.78, 0.82, 0.90)
CLOUD = (0.13, 0.16, 0.26)
CLOUD_L = (0.20, 0.24, 0.37)
GROUND_Y = 800


# ---------- Zeit & Easing ----------
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def prog(t, t0, dur):
    return clamp((t - t0) / dur) if dur > 0 else (1.0 if t >= t0 else 0.0)


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def pop(x):
    """Überschwingen beim Erscheinen (0..1 -> Skalierung)."""
    x = clamp(x)
    if x >= 1:
        return 1.0
    c = 1.70158 * 1.4
    x -= 1
    return 1 + (c + 1) * x ** 3 + c * x ** 2


def fade(t, t0, t1=None, fin=0.35, fout=0.35):
    a = prog(t, t0, fin)
    if t1 is not None:
        a *= 1 - prog(t, t1 - fout, fout)
    return a


def lerp(a, b, x):
    return a + (b - a) * x


def mix(c1, c2, x):
    return tuple(lerp(a, b, x) for a, b in zip(c1, c2))


# ---------- Grundformen ----------
def rgba(ctx, col, a=1.0):
    if len(col) == 4:
        ctx.set_source_rgba(col[0], col[1], col[2], col[3] * a)
    else:
        ctx.set_source_rgba(col[0], col[1], col[2], a)


def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def fill_rrect(ctx, x, y, w, h, r, col, a=1.0):
    rrect(ctx, x, y, w, h, r)
    rgba(ctx, col, a)
    ctx.fill()


def circle(ctx, x, y, r, col, a=1.0):
    ctx.new_path()
    ctx.arc(x, y, r, 0, 2 * math.pi)
    rgba(ctx, col, a)
    ctx.fill()


def ring(ctx, x, y, r, col, a=1.0, w=4):
    ctx.new_path()
    ctx.arc(x, y, r, 0, 2 * math.pi)
    rgba(ctx, col, a)
    ctx.set_line_width(w)
    ctx.stroke()


def poly(ctx, pts, col, a=1.0, close=True):
    ctx.new_path()
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    if close:
        ctx.close_path()
    rgba(ctx, col, a)
    ctx.fill()


def line(ctx, pts, col, a=1.0, w=4, cap=cairo.LINE_CAP_ROUND, dash=None):
    ctx.new_path()
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    rgba(ctx, col, a)
    ctx.set_line_width(w)
    ctx.set_line_cap(cap)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    if dash:
        ctx.set_dash(*dash) if isinstance(dash[0], (list, tuple)) else ctx.set_dash(dash)
    ctx.stroke()
    ctx.set_dash([])


def glow_line(ctx, pts, col, a=1.0, w=6, core=WHITE):
    line(ctx, pts, col, 0.13 * a, w * 5)
    line(ctx, pts, col, 0.30 * a, w * 2.4)
    line(ctx, pts, col, 0.95 * a, w)
    line(ctx, pts, core, 0.9 * a, max(w * 0.35, 1.5))


def arrow(ctx, x0, y0, x1, y1, col, a=1.0, w=6, head=22, both=False):
    line(ctx, [(x0, y0), (x1, y1)], col, a, w)
    ang = math.atan2(y1 - y0, x1 - x0)

    def hd(x, y, an):
        poly(ctx, [(x, y), (x - head * math.cos(an - 0.45), y - head * math.sin(an - 0.45)),
                   (x - head * math.cos(an + 0.45), y - head * math.sin(an + 0.45))], col, a)
    hd(x1 + w * 0.6 * math.cos(ang), y1 + w * 0.6 * math.sin(ang), ang)
    if both:
        hd(x0 - w * 0.6 * math.cos(ang), y0 - w * 0.6 * math.sin(ang), ang + math.pi)


# ---------- Polylinien ----------
def poly_len(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def poly_part(pts, f):
    """Anfangsstück einer Polylinie (Anteil f der Länge)."""
    if f >= 1:
        return list(pts)
    total = poly_len(pts) * max(f, 0)
    out = [pts[0]]
    for i in range(len(pts) - 1):
        d = math.dist(pts[i], pts[i + 1])
        if total <= d:
            k = total / d if d else 0
            out.append((lerp(pts[i][0], pts[i + 1][0], k), lerp(pts[i][1], pts[i + 1][1], k)))
            return out
        total -= d
        out.append(pts[i + 1])
    return out


def poly_point(pts, f):
    return poly_part(pts, clamp(f))[-1]


def flow(ctx, pts, t, col=YEL, a=1.0, w=7, f=1.0, speed=420, gap=70):
    """Leuchtender Strompfad mit wandernden Impulsen."""
    part = poly_part(pts, f)
    if len(part) < 2:
        return
    glow_line(ctx, part, col, a, w)
    L = poly_len(pts)
    off = (t * speed) % gap
    d = off
    while d < L * f:
        x, y = poly_point(pts, d / L)
        circle(ctx, x, y, w * 1.25, WHITE, 0.85 * a)
        d += gap


# ---------- Text ----------
def set_font(ctx, size, weight="bold", family="Inter"):
    wt = cairo.FONT_WEIGHT_BOLD if weight == "bold" else cairo.FONT_WEIGHT_NORMAL
    ctx.select_font_face(family, cairo.FONT_SLANT_NORMAL, wt)
    ctx.set_font_size(size)


def text_w(ctx, s, size, weight="bold", family="Inter"):
    set_font(ctx, size, weight, family)
    return ctx.text_extents(s).x_advance


def text(ctx, s, x, y, size, col=WHITE, a=1.0, align="c", weight="bold", family="Inter",
         stroke=None, sw=8, scale=1.0):
    """Text vertikal zentriert auf y. align: l / c / r."""
    if a <= 0:
        return
    set_font(ctx, size * scale, weight, family)
    ext = ctx.text_extents(s)
    fe = ctx.font_extents()
    w = ext.x_advance
    bx = x - (w / 2 if align == "c" else w if align == "r" else 0)
    by = y + (fe[0] - fe[1]) / 2 * 0.92
    ctx.new_path()
    ctx.move_to(bx, by)
    ctx.text_path(s)
    if stroke is not None:
        rgba(ctx, stroke, a)
        ctx.set_line_width(sw * scale)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke_preserve()
    rgba(ctx, col, a)
    ctx.fill()
    return w


def badge(ctx, s, cx, cy, size=40, fg=WHITE, bg=(0, 0, 0), a=1.0, bga=0.55, pad=26, scale=1.0,
          border=None):
    if a <= 0:
        return
    w = text_w(ctx, s, size * scale) + 2 * pad * scale
    h = size * 1.65 * scale
    fill_rrect(ctx, cx - w / 2, cy - h / 2, w, h, h / 2, bg, bga * a)
    if border:
        rrect(ctx, cx - w / 2, cy - h / 2, w, h, h / 2)
        rgba(ctx, border, a)
        ctx.set_line_width(3)
        ctx.stroke()
    text(ctx, s, cx, cy, size, fg, a, scale=scale)
    return w


def label_card(ctx, lines, cx, cy, size=38, a=1.0, scale=1.0, accent=YEL):
    """Karte mit mehreren Zeilen [(text, farbe), ...]."""
    if a <= 0:
        return
    ws = [text_w(ctx, s, size) for s, _ in lines]
    w = (max(ws) + 64) * scale
    lh = size * 1.35
    h = (lh * len(lines) + 40) * scale
    fill_rrect(ctx, cx - w / 2, cy - h / 2, w, h, 22 * scale, (0.03, 0.04, 0.08), 0.78 * a)
    rrect(ctx, cx - w / 2, cy - h / 2, w, h, 22 * scale)
    rgba(ctx, accent, 0.55 * a)
    ctx.set_line_width(3)
    ctx.stroke()
    y0 = cy - (lh * (len(lines) - 1)) / 2 * scale
    for i, (s, col) in enumerate(lines):
        text(ctx, s, cx, y0 + i * lh * scale, size, col, a, scale=scale)


# ---------- Symbole ----------
def check(ctx, x, y, s, col=GREEN, a=1.0, w=None, f=1.0):
    pts = [(x - 0.5 * s, y), (x - 0.15 * s, y + 0.35 * s), (x + 0.55 * s, y - 0.4 * s)]
    line(ctx, poly_part(pts, f), col, a, w or s * 0.22)


def cross(ctx, x, y, s, col=RED, a=1.0, w=None, f=1.0):
    f1, f2 = clamp(f * 2), clamp(f * 2 - 1)
    if f1 > 0:
        line(ctx, poly_part([(x - s / 2, y - s / 2), (x + s / 2, y + s / 2)], f1), col, a, w or s * 0.2)
    if f2 > 0:
        line(ctx, poly_part([(x + s / 2, y - s / 2), (x - s / 2, y + s / 2)], f2), col, a, w or s * 0.2)


def check_badge(ctx, x, y, r, a=1.0, scale=1.0, ok=True):
    if a <= 0:
        return
    r *= scale
    circle(ctx, x, y, r, GREEN if ok else RED, a)
    if ok:
        check(ctx, x, y + r * 0.05, r * 1.0, WHITE, a, r * 0.24)
    else:
        cross(ctx, x, y, r * 0.9, WHITE, a, r * 0.24)


def bolt_icon(ctx, x, y, s, col=YEL, a=1.0):
    pts = [(0.15, -0.5), (-0.28, 0.06), (-0.02, 0.06), (-0.15, 0.5), (0.3, -0.1), (0.03, -0.1), (0.15, -0.5)]
    poly(ctx, [(x + px * s, y + py * s) for px, py in pts], col, a)


def sun_icon(ctx, x, y, r, a=1.0):
    for i in range(12):
        an = i * math.pi / 6
        line(ctx, [(x + math.cos(an) * r * 1.3, y + math.sin(an) * r * 1.3),
                   (x + math.cos(an) * r * 1.7, y + math.sin(an) * r * 1.7)], ORANGE, a, r * 0.16)
    circle(ctx, x, y, r, (1.0, 0.72, 0.2), a)


def ground_symbol(ctx, x, y, s, col=YEL, a=1.0, w=7):
    line(ctx, [(x, y - s * 0.6), (x, y)], col, a, w)
    for i, k in enumerate((1.0, 0.65, 0.3)):
        line(ctx, [(x - s * k / 2, y + i * s * 0.25), (x + s * k / 2, y + i * s * 0.25)], col, a, w)


def thermometer(ctx, x, y, s, fill_f=1.0, a=1.0):
    fill_rrect(ctx, x - s * 0.12, y - s * 0.5, s * 0.24, s * 0.8, s * 0.12, WHITE, a)
    circle(ctx, x, y + s * 0.35, s * 0.2, WHITE, a)
    circle(ctx, x, y + s * 0.35, s * 0.14, RED, a)
    hh = s * 0.7 * fill_f
    fill_rrect(ctx, x - s * 0.06, y + s * 0.3 - hh, s * 0.12, hh, s * 0.06, RED, a)


def person(ctx, x, y, s, col=(0.85, 0.88, 0.95), a=1.0, arm_up=0.0):
    """Einfache flache Figur; (x,y) = Füße Mitte; s = Höhe."""
    circle(ctx, x, y - s * 0.88, s * 0.11, col, a)
    line(ctx, [(x, y - s * 0.75), (x, y - s * 0.38)], col, a, s * 0.12)
    line(ctx, [(x, y - s * 0.4), (x - s * 0.12, y)], col, a, s * 0.09)
    line(ctx, [(x, y - s * 0.4), (x + s * 0.12, y)], col, a, s * 0.09)
    line(ctx, [(x, y - s * 0.68), (x - s * 0.2, y - s * 0.45)], col, a, s * 0.08)
    hx, hy = x + s * 0.2, y - s * (0.45 + 0.35 * arm_up)
    line(ctx, [(x, y - s * 0.68), (hx, hy)], col, a, s * 0.08)
    return hx, hy


# ---------- Haus ----------
def house(ctx, cx, gy, w, wall_h, roof_h, a=1.0, wall=WALL, roof=ROOF, door=True, windows=True,
          over=0.07, lit=0.0):
    x0, x1 = cx - w / 2, cx + w / 2
    top = gy - wall_h
    apex = (cx, top - roof_h)
    wcol = mix(wall, (0.55, 0.6, 0.75), lit)
    fill_rrect(ctx, x0, top, w, wall_h, 4, wcol, a)
    ov = w * over
    poly(ctx, [(x0 - ov, top + 6), apex, (x1 + ov, top + 6)], mix(roof, (0.6, 0.4, 0.45), lit), a)
    poly(ctx, [(x0 - ov, top + 6), apex, (cx, top + 6)], mix(ROOF_D, roof, 0.4), a * 0.35)
    if door:
        dw, dh = w * 0.16, wall_h * 0.45
        fill_rrect(ctx, cx - dw / 2, gy - dh, dw, dh, 6, WALL_D, a)
    if windows:
        ww = w * 0.17
        for wx in (x0 + w * 0.12, x1 - w * 0.12 - ww):
            fill_rrect(ctx, wx, top + wall_h * 0.18, ww, ww * 0.9, 5, (0.98, 0.83, 0.45), a * 0.85)
            line(ctx, [(wx + ww / 2, top + wall_h * 0.18), (wx + ww / 2, top + wall_h * 0.18 + ww * 0.9)], WALL_D, a, 4)
    return {"apex": apex, "x0": x0, "x1": x1, "top": top, "gy": gy, "ov": ov, "w": w}


def rod_path(hs, rod_h=110, soil=60):
    """Fangstange -> Dach -> Außenwand rechts -> Erde. Liefert (stange, pfad)."""
    ax, ay = hs["apex"]
    tip = (ax, ay - rod_h)
    ex, ey = hs["x1"] + hs["ov"], hs["top"] + 6
    wx = hs["x1"] + hs["ov"] * 0.6
    ry = ay + (wx - ax) / (ex - ax) * (ey - ay) - 5
    return tip, [tip, (ax, ay - 5), (wx, ry), (wx, hs["gy"]), (wx, hs["gy"] + soil)]


def draw_rod(ctx, hs, a=1.0, rod_h=110, col=METAL, w=7, conductor=True, soil=60):
    tip, path = rod_path(hs, rod_h, soil)
    line(ctx, [tip, hs["apex"]], col, a, w)
    poly(ctx, [(tip[0], tip[1] - 16), (tip[0] - 7, tip[1] + 4), (tip[0] + 7, tip[1] + 4)], col, a)
    if conductor:
        line(ctx, path[1:], col, a * 0.9, w * 0.6)
    return tip, path


# ---------- Blitz ----------
def bolt_points(x0, y0, x1, y1, seed, n=14, jit=38):
    rnd = random.Random(seed)
    pts = [(x0, y0)]
    for i in range(1, n):
        k = i / n
        x = lerp(x0, x1, k) + rnd.uniform(-jit, jit) * (1 - 0.6 * k)
        y = lerp(y0, y1, k) + rnd.uniform(-jit * 0.25, jit * 0.25)
        pts.append((x, y))
    pts.append((x1, y1))
    branches = []
    for _ in range(3 if n >= 8 else 0):
        i = rnd.randint(2, n - 4)
        bx, by = pts[i]
        bp = [(bx, by)]
        d = rnd.choice((-1, 1))
        for j in range(1, 5):
            bx += d * rnd.uniform(18, 45)
            by += rnd.uniform(25, 55)
            bp.append((bx, by))
        branches.append(bp)
    return pts, branches


def draw_bolt(ctx, bolt, f=1.0, a=1.0, w=6, col=(0.75, 0.82, 1.0)):
    pts, branches = bolt
    if a <= 0 or f <= 0:
        return
    part = poly_part(pts, f)
    if len(part) < 2:
        return
    for b in branches:
        if f >= 0.6:
            glow_line(ctx, b, col, a * 0.55, w * 0.45)
    glow_line(ctx, part, col, a, w)


def strike(ctx, t, t0, bolt, w=7, hold=0.45, lead=0.12):
    """Blitz-Animation: Leitblitz wächst, Hauptentladung flackert, verblasst."""
    dt = t - t0
    if dt < 0 or dt > lead + hold + 0.35:
        return
    if dt < lead:
        draw_bolt(ctx, bolt, dt / lead, 0.6, w * 0.5)
        return
    k = dt - lead
    flick = 1.0 if k < 0.07 else 0.45 if k < 0.11 else 0.95 if k < 0.18 else 1.0
    a = flick * (1 - prog(k, hold, 0.35))
    draw_bolt(ctx, bolt, 1.0, a, w)


def flash_env(dt):
    """Helligkeitsverlauf eines Blitzes (Doppelflackern)."""
    if dt < 0 or dt > 0.9:
        return 0.0
    if dt < 0.05:
        return dt / 0.05
    if dt < 0.09:
        return 0.35
    if dt < 0.15:
        return 0.85
    return 0.85 * math.exp(-(dt - 0.15) * 7)


# ---------- Wetter ----------
class Weather:
    def __init__(self, seed=3):
        rnd = random.Random(seed)
        self.drops = []
        for layer, n, sp, ln, wd, al in ((0, 170, 1100, 22, 1.3, 0.16), (1, 110, 1750, 42, 2.0, 0.26)):
            for _ in range(n):
                self.drops.append((layer, rnd.uniform(-200, W + 100), rnd.uniform(0, H), sp * rnd.uniform(0.85, 1.15),
                                   ln * rnd.uniform(0.7, 1.3), wd, al))
        self.clouds = []
        for row, (y, col, n, sp) in enumerate(((-30, (0.075, 0.09, 0.15), 14, 9), (40, CLOUD, 12, 16),
                                               (95, (0.10, 0.12, 0.20), 10, 24))):
            for i in range(n):
                x = i * (W + 600) / n + rnd.uniform(-60, 60)
                blobs = [(rnd.uniform(-120, 120), rnd.uniform(-30, 30), rnd.uniform(60, 120)) for _ in range(5)]
                self.clouds.append((row, x, y + rnd.uniform(-15, 15), col, sp, blobs))

    def sky(self, ctx):
        g = cairo.LinearGradient(0, 0, 0, H)
        g.add_color_stop_rgb(0, 0.025, 0.035, 0.075)
        g.add_color_stop_rgb(0.55, 0.07, 0.09, 0.17)
        g.add_color_stop_rgb(1, 0.10, 0.12, 0.21)
        ctx.set_source(g)
        ctx.paint()

    def draw_clouds(ctx_self, ctx, t, flash=0.0, amount=1.0):
        if amount <= 0:
            return
        for row, x, y, col, sp, blobs in ctx_self.clouds:
            xx = (x + t * sp) % (W + 600) - 300
            c = mix(col, (0.45, 0.5, 0.7), flash * 0.6)
            for bx, by, r in blobs:
                circle(ctx, xx + bx, y + by, r, c, amount)

    def draw_rain(self, ctx, t, amount=1.0):
        if amount <= 0:
            return
        for layer in (0, 1):
            ctx.new_path()
            wd = al = 0
            for (ly, x, y, sp, ln, w_, a_) in self.drops:
                if ly != layer:
                    continue
                wd, al = w_, a_
                yy = (y + t * sp) % (H + 80) - 40
                xx = x + yy * 0.16
                ctx.move_to(xx, yy)
                ctx.line_to(xx + ln * 0.16, yy + ln)
            ctx.set_source_rgba(0.68, 0.78, 0.98, al * amount)
            ctx.set_line_width(wd)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.stroke()


def ground(ctx, y=GROUND_Y, a=1.0, col=GROUND, hills=True):
    ctx.new_path()
    ctx.move_to(0, y)
    if hills:
        for i in range(0, W + 1, 80):
            ctx.line_to(i, y - 10 * math.sin(i / 260) - 6 * math.sin(i / 97))
    ctx.line_to(W, y)
    ctx.line_to(W, H)
    ctx.line_to(0, H)
    ctx.close_path()
    rgba(ctx, col, a)
    ctx.fill()


def cloud_shape(ctx, cx, cy, s, col=CLOUD, a=1.0):
    for bx, by, r in ((-0.55, 0.1, 0.32), (-0.25, -0.15, 0.42), (0.15, -0.22, 0.46), (0.5, 0.0, 0.36),
                      (0.0, 0.12, 0.4), (-0.75, 0.22, 0.2), (0.78, 0.2, 0.22)):
        circle(ctx, cx + bx * s, cy + by * s, r * s, col, a)
