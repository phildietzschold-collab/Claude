# -*- coding: utf-8 -*-
"""Hochformat-Szenen für das Short "Warum bist du im Auto bei einem Blitzschlag sicher?"."""
import math

from gfx import *  # noqa: F401,F403
from scenes import Scene

SW = 1080
CAR_BODY = (0.75, 0.22, 0.22)
CAR_DARK = (0.52, 0.13, 0.14)
GLASS = (0.55, 0.72, 0.9)

# Auto (Seitenansicht, Front rechts) in Einheiten; y nach oben negativ
BODY = [(-320, -60), (-332, -120), (-300, -165), (-170, -178), (-120, -300), (110, -300), (190, -185),
        (300, -172), (332, -130), (326, -60)]
WIN_R = [(-150, -185), (-108, -285), (-8, -285), (-8, -185)]
WIN_F = [(12, -185), (12, -285), (100, -285), (168, -185)]
WHEELS = (-190, 205)
SHELL_FRONT = [(0, -300), (110, -300), (190, -185), (300, -172), (332, -130), (326, -60)]
SHELL_REAR = [(0, -300), (-120, -300), (-170, -178), (-300, -165), (-332, -120), (-320, -60)]


def tf(pts, cx, gy, s):
    return [(cx + x * s, gy + y * s) for x, y in pts]


def car(ctx, cx, gy, s=1.0, a=1.0, shell=0.0, tire_glow=0.0, windows_closed=0.0, person=True, inner=0.0):
    poly(ctx, tf(BODY, cx, gy, s), CAR_BODY, a)
    poly(ctx, tf([(-320, -60), (-332, -120), (326, -120), (326, -60)], cx, gy, s), CAR_DARK, a * 0.5)
    for w in (WIN_R, WIN_F):
        poly(ctx, tf(w, cx, gy, s), mix((0.1, 0.13, 0.2), GLASS, 0.35 + 0.4 * windows_closed), a)
    if inner > 0:
        line(ctx, tf(WIN_R + [WIN_R[0]], cx, gy, s), GREEN, a * inner, 5, dash=[12, 8])
        line(ctx, tf(WIN_F + [WIN_F[0]], cx, gy, s), GREEN, a * inner, 5, dash=[12, 8])
    if person:
        hx, hy = cx + 70 * s, gy - 238 * s
        circle(ctx, hx, hy, 24 * s, (0.95, 0.82, 0.68), a)
        fill_rrect(ctx, hx - 26 * s, hy + 22 * s, 52 * s, 40 * s, 12 * s, (0.2, 0.35, 0.6), a)
    line(ctx, tf([(-40, -180), (-40, -70)], cx, gy, s), CAR_DARK, a, 4)
    fill_rrect(ctx, cx + 250 * s, gy - 160 * s, 40 * s, 18 * s, 6, (1, 0.9, 0.6), a)
    for wx in WHEELS:
        x = cx + wx * s
        y = gy - 60 * s
        if tire_glow > 0:
            circle(ctx, x, y, 80 * s, YEL, 0.25 * tire_glow * a)
        circle(ctx, x, y, 62 * s, (0.08, 0.08, 0.1), a)
        circle(ctx, x, y, 30 * s, (0.7, 0.72, 0.78), a)
        circle(ctx, x, y, 10 * s, (0.4, 0.42, 0.48), a)
    if shell > 0:
        glow_line(ctx, tf(BODY + [BODY[0]], cx, gy, s), YEL, shell, 6)


def shell_paths(cx, gy, s):
    f = tf(SHELL_FRONT, cx, gy, s) + [(cx + 330 * s, gy)]
    r = tf(SHELL_REAR, cx, gy, s) + [(cx - 326 * s, gy)]
    return f, r


# =====================================================================
class Hook(Scene):
    def setup(self):
        self.t_open = 0.15
        self.b_open = bolt_points(860, -20, 960, 1150, seed=4, n=16, jit=55)
        self.flash(self.t_open + 0.12, 1.0)

    def draw(self, ctx, t):
        c = self.c
        ground(ctx, 1150)
        strike(ctx, t, self.t_open, self.b_open, w=7)
        tg = fade(t, c.w(1, "Gummireifen") - 0.1, c.s(2) + 0.6)
        car(ctx, 540, 1150, 1.2, tire_glow=tg * (0.7 + 0.3 * math.sin(t * 8)))
        ab = fade(t, c.w(1, "Gummireifen") - 0.1)
        if ab > 0:
            sc = pop(prog(t, c.w(1, "Gummireifen") - 0.1, 0.45))
            badge(ctx, "Gummireifen?", 540, 600, 62, INK, YEL, ab, 1, scale=sc)
            for wx in WHEELS:
                arrow(ctx, 540 + wx * 0.5, 650, 540 + wx * 1.2, 1010, YEL, ab * 0.9, 6, 22)
            fx = prog(t, c.w(2, "stimmt") - 0.1, 0.5)
            if fx > 0:
                cross(ctx, 540, 600, 150, RED, ab, 22, f=fx)


class Gummi(Scene):
    sky = 0.7

    def setup(self):
        c = self.c
        self.bolt_big = bolt_points(280, 420, 300, 1150, seed=12, n=18, jit=50)
        self.t_big = c.w(0, "Blitz") - 0.1
        self.flash(self.t_big + 0.12, 0.8)
        self.t_tire = c.w(1, "halten") - 0.3
        self.bolt_tire = bolt_points(770, 420, 790, 1150, seed=19, n=14, jit=30)
        self.flash(self.t_tire + 0.12, 0.9)

    def draw(self, ctx, t):
        c = self.c
        ground(ctx, 1150)
        # links: Blitz durch mehrere Kilometer Luft
        strike(ctx, t, self.t_big, self.bolt_big, w=8, hold=1.6)
        ak = fade(t, c.w(0, "Kilometer") - 0.15)
        if ak > 0:
            arrow(ctx, 110, 440, 110, 1130, WHITE, ak * 0.8, 5, 22, both=True)
            badge(ctx, "km", 110, 790, 60, INK, YEL, ak, 1, scale=pop(prog(t, c.w(0, "Kilometer") - 0.15, 0.45)))
        # rechts: Reifen mit wenigen Zentimetern Gummi
        at = fade(t, c.s(1) - 0.3)
        if at > 0:
            sc = pop(prog(t, c.s(1) - 0.3, 0.5))
            x, y = 780, 860
            circle(ctx, x, y, 190 * sc, (0.08, 0.08, 0.1), at)
            ring(ctx, x, y, 175 * sc, (0.2, 0.2, 0.24), at, 8)
            circle(ctx, x, y, 110 * sc, (0.7, 0.72, 0.78), at)
            circle(ctx, x, y, 35 * sc, (0.4, 0.42, 0.48), at)
            ac = fade(t, c.w(1, "Zentimeter") - 0.1)
            if ac > 0:
                arrow(ctx, x + 205, y - 190, x + 205, y - 110, YEL, ac, 5, 16, both=True)
                badge(ctx, "cm", x + 205, y - 260, 52, INK, YEL, ac, 1, scale=pop(prog(t, c.w(1, "Zentimeter") - 0.1, 0.45)))
        strike(ctx, t, self.t_tire, self.bolt_tire, w=8, hold=0.9)


class Grund(Scene):
    def setup(self):
        c = self.c
        self.t_hit = c.w(1, "einschlägt") - 0.2
        self.flash(self.t_hit + 0.12, 1.0)
        self.bolt = bolt_points(500, -20, 540, 1150 - 300 * 1.2 - 6, seed=7, n=16, jit=45)

    def draw(self, ctx, t):
        c = self.c
        ground(ctx, 1150)
        sh = fade(t, c.w(0, "Metallhülle") - 0.15, c.s(1) + 0.3, 0.3, 0.5)
        inner = fade(t, c.w(2, "Innenraum") - 0.15)
        car(ctx, 540, 1150, 1.2, shell=sh * (0.75 + 0.25 * math.sin(t * 7)), inner=inner)
        badge(ctx, "Metallhülle", 540, 600, 62, INK, YEL, sh, 1, scale=pop(prog(t, c.w(0, "Metallhülle") - 0.15, 0.45)))
        strike(ctx, t, self.t_hit, self.bolt, w=8)
        af = fade(t, self.t_hit + 0.12, None, 0.1)
        if af > 0:
            k = ease(prog(t, c.s(2) - 0.2, 1.4)) if t >= c.s(2) - 0.2 else 0.08
            for p in shell_paths(540, 1150, 1.2):
                flow(ctx, p, t, YEL, af, 7, f=k)
            if k >= 1:
                ctx.save()
                ctx.rectangle(0, 1150, SW, 500)
                ctx.clip()
                for x in (540 - 326 * 1.2, 540 + 330 * 1.2):
                    for i in range(4):
                        r = 20 + ((t - c.s(2)) * 180 + i * 50) % 200
                        ring(ctx, x, 1150, r, YEL, af * (1 - r / 220) * 0.7, 3)
                ctx.restore()
        ai = fade(t, c.w(2, "Innenraum") - 0.15)
        if ai > 0:
            check_badge(ctx, 540 + 70 * 1.2, 1150 - 340 * 1.2, 34, ai, pop(prog(t, c.w(3, "nichts") - 0.3, 0.45)) if t > c.w(3, "nichts") - 0.3 else 0.001)
            badge(ctx, "Innenraum sicher", 540, 600, 58, WHITE, GREEN, ai * fade(t, c.s(3) - 0.2), 1,
                  scale=pop(prog(t, c.s(3) - 0.2, 0.45)))


class Tipps(Scene):
    sky = 0.7

    def draw(self, ctx, t):
        c = self.c
        ground(ctx, 1150)
        wc = fade(t, c.w(1, "Fenster") - 0.1)
        car(ctx, 540, 1150, 1.0, windows_closed=wc)
        # Elektronik (Chip im Motorraum)
        ae = fade(t, c.w(0, "Elektronik") - 0.2, c.s(1) + 0.5)
        if ae > 0:
            x, y = 540 + 250, 1150 - 140
            pulse = 0.6 + 0.4 * math.sin(t * 10)
            fill_rrect(ctx, x - 34, y - 34, 68, 68, 8, (0.15, 0.17, 0.22), ae)
            for k in range(4):
                for sgn in (-1, 1):
                    line(ctx, [(x - 24 + k * 16, y + sgn * 34), (x - 24 + k * 16, y + sgn * 46)], METAL, ae, 4)
            ring(ctx, x, y, 62, RED, ae * pulse, 5)
            poly(ctx, [(x, y - 150), (x - 40, y - 85), (x + 40, y - 85)], RED, ae)
            text(ctx, "!", x, y - 110, 48, WHITE, ae)
        items = [("Fenster zu", c.w(1, "Fenster")), ("Keine Metallteile anfassen", c.w(1, "keine"))]
        ac = fade(t, c.s(1) - 0.2)
        if ac > 0:
            fill_rrect(ctx, 90, 470, 900, 300, 34, (0.03, 0.04, 0.08), 0.8 * ac)
            text(ctx, "Im Gewitter", 540, 530, 54, YEL, ac)
            for i, (s, t0) in enumerate(items):
                a = fade(t, t0 - 0.1)
                if a <= 0:
                    continue
                y = 625 + i * 95
                check_badge(ctx, 160, y, 30, a, pop(prog(t, t0 - 0.1, 0.4)))
                text(ctx, s, 215, y, 50, WHITE, a, align="l")


class Outro(Scene):
    sky = 0.7

    def draw(self, ctx, t):
        c = self.c
        a = fade(t, c.s(0) - 0.4)
        sc = pop(prog(t, c.s(0) - 0.4, 0.6))
        pulse = 0.85 + 0.15 * math.sin(t * 4)
        circle(ctx, 540, 700, 200 * sc, YEL, 0.08 * a * pulse)
        circle(ctx, 540, 700, 150 * sc, (0.04, 0.05, 0.1), a)
        ring(ctx, 540, 700, 150 * sc, YEL, a, 8)
        bolt_icon(ctx, 540, 700, 200 * sc, YEL, a)
        text(ctx, "Wissen, kurz erklärt", 540, 950, 64, WHITE, a, scale=sc)
        af = fade(t, c.s(1) - 0.15)
        badge(ctx, "FOLGEN", 540, 1090, 64, WHITE, RED, af, 1, scale=pop(prog(t, c.s(1) - 0.15, 0.45)))


SCENES = {"hook": Hook, "gummi": Gummi, "grund": Grund, "tipps": Tipps, "outro": Outro}
