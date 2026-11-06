# -*- coding: utf-8 -*-
"""Eine Szene pro Kapitel. Alle Animationen hängen an den Satz-/Wortzeiten aus timing.json."""
import math
import random

from gfx import *  # noqa: F401,F403


class Cue:
    def __init__(self, ch):
        self.ch = ch
        self.S = [s["start"] for s in ch["sentences"]]
        self.E = [s["end"] for s in ch["sentences"]]

    def s(self, i):
        return self.S[i]

    def e(self, i):
        return self.E[i]

    def w(self, i, sub, n=0):
        """Startzeit des n-ten Wortes in Satz i, das `sub` enthält."""
        k = 0
        for wd in self.ch["sentences"][i]["words"]:
            if sub.lower() in wd["w"].lower():
                if k == n:
                    return wd["s"]
                k += 1
        raise KeyError(f"{sub!r} nicht in Satz {i}: {self.ch['sentences'][i]['text']}")


class Scene:
    sky = 1.0      # Wolken-Deckkraft
    rain = 1.0

    def __init__(self, cue):
        self.c = cue
        self.flashes = []  # (zeit, stärke)
        self.setup()

    def setup(self):
        pass

    def flash(self, t0, k=1.0):
        self.flashes.append((t0, k))

    def draw(self, ctx, t):
        pass


# =====================================================================
class Intro(Scene):
    def setup(self):
        c = self.c
        self.t_open = 0.15
        self.b_open = bolt_points(420, -20, 330, 790, seed=11)
        self.flash(self.t_open + 0.12, 1.0)
        self.t_hit = c.w(1, "Haus") - 0.35
        self.flash(self.t_hit + 0.12, 0.9)
        self.flash(c.s(3) + 0.1, 0.35)

    def draw(self, ctx, t):
        c = self.c
        ground(ctx)
        strike(ctx, t, self.t_open, self.b_open, w=6)
        hs = house(ctx, 960, GROUND_Y, 440, 250, 170)
        tip, path = draw_rod(ctx, hs, rod_h=120, soil=0)
        if not hasattr(self, "b_hit"):
            self.b_hit = bolt_points(880, -20, tip[0], tip[1] - 14, seed=5)
        # Satz 0: heißer als die Sonne, 20.000 A
        a0 = fade(t, c.s(0) + 0.6, c.s(2) + 0.2)
        if a0 > 0:
            sc = pop(prog(t, c.s(0) + 0.6, 0.45))
            fill_rrect(ctx, 220, 250, 330, 140, 28, (0, 0, 0), 0.5 * a0)
            sun_icon(ctx, 300, 320, 30 * sc, a0)
            text(ctx, "<", 385, 318, 64, WHITE, a0)
            bolt_icon(ctx, 470, 320, 100 * sc, YEL, a0)
            text(ctx, "heißer als die Sonnenoberfläche", 385, 425, 28, WHITE, a0 * 0.9, weight="normal")
            a1 = fade(t, c.w(0, "20.000"), c.s(2) + 0.2)
            sc1 = pop(prog(t, c.w(0, "20.000"), 0.45))
            badge(ctx, "≈ 20.000 A", 1540, 440, 50, YEL, a=a1, scale=sc1)
        # Satz 1: dünne Metallstange
        ag = fade(t, c.w(1, "Metallstange") - 0.1, c.s(2) + 0.5)
        if ag > 0:
            pulse = 0.6 + 0.4 * math.sin(t * 8)
            circle(ctx, tip[0], tip[1] + 40, 60, YEL, 0.10 * ag * pulse)
            line(ctx, [tip, hs["apex"]], YEL, ag, 8)
            text(ctx, "dünne Metallstange", tip[0] + 300, tip[1] - 20, 38, YEL, ag)
            arrow(ctx, tip[0] + 150, tip[1] - 12, tip[0] + 30, tip[1] + 10, YEL, ag, 5, 18)
        strike(ctx, t, self.t_hit, self.b_hit, w=7)
        fa = fade(t, self.t_hit + 0.12, self.t_hit + 2.6, 0.1, 0.6)
        if fa > 0:
            flow(ctx, path, t, YEL, fa, 6, f=ease(prog(t, self.t_hit + 0.12, 0.55)))
            for i in range(5):
                r = 30 + ((t - self.t_hit) * 200 + i * 40) % 200
                ctx.save()
                ctx.rectangle(0, GROUND_Y, W, 300)
                ctx.clip()
                ring(ctx, path[-1][0], GROUND_Y, r, YEL, fa * (1 - r / 230) * 0.7, 3)
                ctx.restore()
        # Satz 2: Wie kann das sein?
        aq = fade(t, c.s(2), c.s(4) + 0.3)
        if aq > 0:
            sc = pop(prog(t, c.s(2), 0.5))
            circle(ctx, 1480, 560, 85 * sc, YEL, aq)
            text(ctx, "?", 1480, 562, 120, INK, aq, scale=sc)
        # Satz 3: Zieht er Blitze an?
        a3 = fade(t, c.s(3), None)
        if a3 > 0:
            sc = pop(prog(t, c.s(3), 0.5))
            label_card(ctx, [("Zieht ein Blitzableiter Blitze an?", WHITE)], 960, 205, 52, a3, sc)


# =====================================================================
class K1(Scene):
    sky = 0.35

    def setup(self):
        c = self.c
        rnd = random.Random(4)
        self.parts = [(rnd.uniform(0, 6.28), rnd.uniform(60, 320), rnd.uniform(30, 130), rnd.uniform(0.6, 1.3),
                       i % 2) for i in range(30)]
        self.plus = [((rnd.uniform(700, 1220), rnd.uniform(200, 470)), (rnd.uniform(720, 1200), rnd.uniform(150, 215)))
                     for _ in range(13)]
        self.minus = [((rnd.uniform(700, 1220), rnd.uniform(200, 470)), (rnd.uniform(700, 1220), rnd.uniform(430, 500)))
                      for _ in range(13)]
        self.bolt = bolt_points(1110, 520, 1135, 790, seed=21, n=12, jit=45)
        self.t_bolt = c.s(6) - 0.05
        self.flash(self.t_bolt + 0.12, 1.0)
        self.sparks = [bolt_points(1110, 520, 1110 + rnd.uniform(-90, 90), 520 + rnd.uniform(40, 90), seed=40 + i, n=4,
                                   jit=18) for i in range(6)]

    def draw(self, ctx, t):
        c = self.c
        ground(ctx)
        # kleine Silhouetten am Boden
        for x, h_ in ((300, 70), (380, 50), (1560, 60), (1660, 80)):
            poly(ctx, [(x - 30, GROUND_Y), (x, GROUND_Y - h_), (x + 30, GROUND_Y)], (0.1, 0.13, 0.18))
        cloud_shape(ctx, 960, 340, 440, (0.17, 0.2, 0.32))
        cloud_shape(ctx, 960, 350, 400, (0.21, 0.25, 0.38))
        # Eis & Wassertropfen
        ap = fade(t, c.s(1) - 0.2, c.s(3) + 0.8)
        if ap > 0:
            for ph, rx, ry, sp, kind in self.parts:
                x = 960 + rx * math.cos(t * sp + ph)
                y = 330 + ry * math.sin(t * sp * 1.3 + ph)
                if kind:
                    for k in range(3):
                        an = k * math.pi / 3 + t
                        line(ctx, [(x - 11 * math.cos(an), y - 11 * math.sin(an)),
                                   (x + 11 * math.cos(an), y + 11 * math.sin(an))], WHITE, ap * 0.9, 3)
                else:
                    circle(ctx, x, y, 9, BLUE, ap)
            a_l = fade(t, c.w(1, "Eis"), c.s(2) + 0.3)
            if a_l > 0:
                badge(ctx, "Eis", 420, 260, 36, WHITE, a=a_l)
                badge(ctx, "Wassertropfen", 1530, 260, 36, (0.6, 0.78, 1), a=fade(t, c.w(1, "Wasser"), c.s(2) + 0.3))
        # Ladungen
        ach = fade(t, c.s(2) + 0.3)
        if ach > 0:
            k = ease_io(prog(t, c.w(2, "oben") - 0.3, 1.6))
            for (p0, p1) in self.plus:
                x, y = lerp(p0[0], p1[0], k), lerp(p0[1], p1[1], k)
                circle(ctx, x, y, 17, (0.92, 0.33, 0.3), ach)
                line(ctx, [(x - 8, y), (x + 8, y)], WHITE, ach, 4)
                line(ctx, [(x, y - 8), (x, y + 8)], WHITE, ach, 4)
            for (p0, p1) in self.minus:
                x, y = lerp(p0[0], p1[0], k), lerp(p0[1], p1[1], k)
                circle(ctx, x, y, 17, (0.3, 0.5, 0.98), ach)
                line(ctx, [(x - 8, y), (x + 8, y)], WHITE, ach, 4)
            text(ctx, "positiv", 1470, 180, 40, (1, 0.5, 0.45), fade(t, c.w(2, "positiv")))
            text(ctx, "negativ", 1470, 470, 40, (0.55, 0.72, 1), fade(t, c.w(2, "negativ")))
        # Spannung
        av = fade(t, c.s(3) + 0.2, c.s(7))
        if av > 0:
            pulse = 0.75 + 0.25 * math.sin(t * 6)
            arrow(ctx, 760, 545, 760, 775, YEL, av * pulse, 7, 26, both=True)
            badge(ctx, "viele Millionen Volt", 520, 660, 38, YEL, a=fade(t, c.w(3, "Millionen"), c.s(7)))
        # Luft hält nicht aus: Funken
        if c.s(4) <= t < c.s(5):
            for i, sp in enumerate(self.sparks):
                if int(t * 12 + i * 3) % 4 == 0:
                    draw_bolt(ctx, sp, 1, 0.7, 2.5)
        # Leitfähig: Leitblitz wächst stufenweise
        if c.s(5) <= t < self.t_bolt:
            f = prog(t, c.s(5), max(self.t_bolt - c.s(5), 0.3))
            f = math.floor(f * 8) / 8
            draw_bolt(ctx, self.bolt, f, 0.7, 3)
        # Der Blitz
        strike(ctx, t, self.t_bolt, self.bolt, w=8, hold=1.2)
        # 30.000 Grad: heißer Kanal
        ah = fade(t, c.s(7) - 0.1, c.s(8) + 1.5)
        if ah > 0:
            draw_bolt(ctx, self.bolt, 1.0, ah * (0.8 + 0.2 * math.sin(t * 30)), 6, col=(1.0, 0.6, 0.3))
            sc = pop(prog(t, c.w(7, "30.000"), 0.5))
            a2 = fade(t, c.w(7, "30.000"), c.s(8) + 1.5)
            fill_rrect(ctx, 1290, 590, 420, 120, 28, (0, 0, 0), 0.55 * a2)
            thermometer(ctx, 1345, 645, 90 * sc, prog(t, c.w(7, "30.000"), 1.0), a2)
            text(ctx, "≈ 30.000 °C", 1530, 650, 50, YEL, a2, scale=sc)
        # Donner
        if t >= c.w(8, "dehnt") - 0.1:
            ad = fade(t, c.w(8, "dehnt") - 0.1)
            for side in (-1, 1):
                k = ((t - c.w(8, "dehnt")) * 1.5) % 1
                x0 = 1122 + side * (20 + k * 60)
                arrow(ctx, x0, 650, x0 + side * 45, 650, WHITE, ad * (1 - k), 5, 16)
        if t >= c.w(8, "Donner") - 0.15:
            ad = fade(t, c.w(8, "Donner") - 0.15)
            for i in range(4):
                r = 40 + ((t - c.w(8, "Donner")) * 260 + i * 90) % 360
                ring(ctx, 1122, 650, r, WHITE, ad * max(0, 1 - r / 380) * 0.8, 5)
            badge(ctx, "Donner", 760, 660, 46, WHITE, a=ad, scale=pop(prog(t, c.w(8, "Donner"), 0.5)))


# =====================================================================
WOOD = (0.62, 0.42, 0.24)


class K2(Scene):
    def setup(self):
        c = self.c
        self.t_hit = c.w(1, "ein,") - 0.15
        self.flash(self.t_hit + 0.12, 1.0)
        self.bolt = bolt_points(930, -20, 860, 292, seed=8)
        self.path = [(860, 300), (860, 500), (1095, 500), (1095, 720), (1095, 800), (1095, 860)]
        rnd = random.Random(9)
        self.steam = [(rnd.uniform(640, 1080), rnd.uniform(380, 500), rnd.uniform(0, 2)) for _ in range(14)]
        self.flames = [(x, 300 + (abs(x - 860) / 315) * 206 - 8, rnd.uniform(0, 6)) for x in
                       (640, 700, 760, 960, 1020, 1080)]

    def house_x(self, ctx, a=1.0):
        x0, x1, top, gy = 580, 1140, 500, GROUND_Y
        fill_rrect(ctx, x0, top, x1 - x0, gy - top, 4, (0.11, 0.13, 0.21), a)
        line(ctx, [(x0 + 8, top), (x0 + 8, gy)], WALL, a, 16, cap=0)
        line(ctx, [(x1 - 8, top), (x1 - 8, gy)], WALL, a, 16, cap=0)
        poly(ctx, [(x0 - 40, top + 6), (860, 300), (x1 + 40, top + 6)], ROOF, a * 0.35)
        line(ctx, [(x0 - 40, top + 6), (860, 300), (x1 + 40, top + 6)], ROOF, a, 18)
        # Dachstuhl
        line(ctx, [(x0, top), (x1, top)], WOOD, a, 14)
        line(ctx, [(860, 305), (860, top)], WOOD, a, 12)
        line(ctx, [(720, top), (790, 380)], WOOD, a, 10)
        line(ctx, [(1000, top), (930, 380)], WOOD, a, 10)
        line(ctx, [(660, 420), (1060, 420)], WOOD, a, 10)
        # Leitung + Steckdose
        line(ctx, [(1095, top + 10), (1095, 720)], (0.85, 0.85, 0.85), a * 0.8, 4)
        fill_rrect(ctx, 1072, 700, 46, 46, 8, (0.85, 0.87, 0.92), a)
        circle(ctx, 1086, 723, 4, INK, a)
        circle(ctx, 1104, 723, 4, INK, a)

    def draw(self, ctx, t):
        c = self.c
        ground(ctx)
        self.house_x(ctx, fade(t, c.s(0) - 0.5, None, 0.6))
        ab = fade(t, c.w(1, "ohne"), c.s(3))
        badge(ctx, "ohne Schutz", 1460, 260, 44, WHITE, RED, ab, 0.9, scale=pop(prog(t, c.w(1, "ohne"), 0.45)))
        strike(ctx, t, self.t_hit, self.bolt, w=8)
        f = ease_io(prog(t, self.t_hit + 0.15, max(c.e(1) - self.t_hit, 1.0)))
        af = fade(t, self.t_hit + 0.12, c.s(4) + 0.2, 0.1)
        if af > 0 and f > 0:
            flow(ctx, self.path, t, RED, af, 7, f=f, speed=500)
            rnd = random.Random(int(t * 15))
            for (x, y) in self.path[1:4]:
                if poly_len(poly_part(self.path, f)) >= poly_len(poly_part(self.path, 0)) and \
                        math.dist((x, y), poly_point(self.path, f)) < 900:
                    for _ in range(5):
                        an = rnd.uniform(0, 6.28)
                        r = rnd.uniform(10, 40)
                        line(ctx, [(x, y), (x + r * math.cos(an), y + r * math.sin(an))], YEL, af * 0.9, 3)
        # Beschriftungen
        for i, (word, txt, y, px, py) in enumerate((("Holzbalken", "Holzbalken", 400, 1010, 420),
                                                    ("Wände", "Wände", 560, 1135, 590),
                                                    ("Leitungen", "Leitungen", 700, 1118, 722))):
            al = fade(t, c.w(2, word) - 0.05, c.s(4))
            if al > 0:
                line(ctx, [(1290, y), (px + 12, py)], WHITE, al * 0.8, 3)
                circle(ctx, px + 12, py, 7, WHITE, al)
                badge(ctx, txt, 1420, y, 38, WHITE, a=al, scale=pop(prog(t, c.w(2, word), 0.4)))
        # Dampf
        if t >= c.w(3, "verdampft") - 0.2:
            asx = fade(t, c.w(3, "verdampft") - 0.2, c.s(4) + 1.5)
            for x, y, ph in self.steam:
                k = ((t + ph) * 0.6) % 1
                circle(ctx, x + 10 * math.sin(t * 3 + ph), y - k * 120, 10 + k * 22, (0.85, 0.88, 0.95), asx * (1 - k) * 0.5)
        # Feuer
        if t >= c.w(3, "Brand") - 0.2:
            afl = fade(t, c.w(3, "Brand") - 0.2, None, 0.5)
            g = ease(prog(t, c.w(3, "Brand") - 0.2, 1.2))
            for x, y, ph in self.flames:
                hgt = (50 + 22 * math.sin(t * 13 + ph)) * g
                wdt = 26 * g
                poly(ctx, [(x - wdt, y), (x - wdt * 0.5, y - hgt * 0.6), (x, y - hgt), (x + wdt * 0.5, y - hgt * 0.55),
                           (x + wdt, y)], ORANGE, afl * 0.95)
                poly(ctx, [(x - wdt * 0.5, y), (x, y - hgt * 0.55), (x + wdt * 0.5, y)], YEL, afl)
        a4 = fade(t, c.w(4, "Blitzableiter") - 0.1, None)
        if a4 > 0:
            sc = pop(prog(t, c.w(4, "Blitzableiter") - 0.1, 0.5))
            fill_rrect(ctx, 1260, 200, 420, 120, 26, (0, 0, 0), 0.6 * a4)
            line(ctx, [(1330, 300), (1330, 220)], METAL, a4, 7)
            poly(ctx, [(1330, 205), (1322, 225), (1338, 225)], METAL, a4)
            bolt_icon(ctx, 1385, 250, 60, YEL, a4)
            text(ctx, "Blitzableiter", 1530, 262, 40, YEL, a4, scale=sc)


# =====================================================================
class K3(Scene):
    sky = 0.5

    def setup(self):
        c = self.c
        self.flash(c.s(4) + 0.2, 0.4)

    def draw(self, ctx, t):
        c = self.c
        ground(ctx, 650, hills=False)
        # Zeitleiste
        at = fade(t, c.s(0) - 0.6, None, 0.6)
        f = ease(prog(t, c.s(0) - 0.5, 1.2))
        line(ctx, [(260, 722), (lerp(260, 1660, f), 722)], WHITE, at * 0.8, 6)
        for yr, x in (("1700", 360), ("1800", 1560)):
            if f * 1400 + 260 > x:
                line(ctx, [(x, 707), (x, 737)], WHITE, at * 0.8, 4)
                text(ctx, yr, x, 762, 28, WHITE, at * 0.7, weight="normal")
        am = fade(t, c.w(0, "Mitte"))
        if am > 0:
            sc = pop(prog(t, c.w(0, "Mitte"), 0.5))
            circle(ctx, 960, 722, 22 * sc, YEL, am)
            badge(ctx, "Mitte des 18. Jahrhunderts", 960, 785, 32, YEL, a=am, scale=sc)
        # Haus mit Person auf dem Dach
        ah = fade(t, c.s(0) + 0.4, None, 0.6)
        hs = house(ctx, 760, 650, 340, 180, 130, ah)
        hx, hy = person(ctx, 718, 332, 150, a=ah, arm_up=0.6)
        line(ctx, [(hx + 4, hy + 50), (hx + 4, hy - 140)], METAL, ah, 7)
        poly(ctx, [(hx + 4, hy - 160), (hx - 4, hy - 136), (hx + 12, hy - 136)], METAL, ah)
        an = fade(t, c.w(1, "Benjamin") - 0.1)
        text(ctx, "Benjamin Franklin", 360, 300, 44, WHITE, an, scale=pop(prog(t, c.w(1, "Benjamin") - 0.1, 0.5)))
        # Idee: Blitz = elektrische Entladung
        ai = fade(t, c.w(1, "Idee") - 0.1, c.s(2) + 0.2)
        if ai > 0:
            sc = pop(prog(t, c.w(1, "Idee") - 0.1, 0.5))
            for i, (bx, by, r) in enumerate(((880, 300, 9), (920, 270, 14))):
                circle(ctx, bx, by, r * sc, WHITE, ai * 0.85)
            fill_rrect(ctx, 960, 170, 680, 150, 70, WHITE, 0.92 * ai)
            bolt_icon(ctx, 1040, 245, 90 * sc, YEL, ai)
            text(ctx, "= elektrische Entladung", 1330, 247, 42, INK, ai)
        # Vorschlag: spitze Stange + Kabel in die Erde
        ap = fade(t, c.s(2) - 0.1)
        if ap > 0:
            cable = [(hx + 4, hy + 50), (hs["x1"] + 30, hs["top"] + 20), (hs["x1"] + 30, 650), (hs["x1"] + 30, 690)]
            fk = ease(prog(t, c.w(2, "Kabel") - 0.1, 1.2))
            if fk > 0:
                line(ctx, poly_part(cable, fk), (0.85, 0.6, 0.35), ap, 5)
                if fk >= 1:
                    ground_symbol(ctx, hs["x1"] + 30, 690, 50, YEL, ap, 5)
            items = [("spitze Metallstange", c.w(2, "spitze")), ("Kabel", c.w(2, "Kabel")), ("sicher in die Erde", c.w(2, "Erde"))]
            for i, (s, t0) in enumerate(items):
                a_ = fade(t, t0 - 0.05, c.s(3) + 0.3)
                if a_ > 0:
                    badge(ctx, s, 1400, 330 + i * 95, 38, YEL if i != 1 else WHITE, a=a_, scale=pop(prog(t, t0 - 0.05, 0.4)))
        # Niemand wusste ...
        aw = fade(t, c.s(3), c.s(4) + 0.2)
        if aw > 0:
            for i, (qx, qy) in enumerate(((1250, 330), (1420, 270), (1560, 380), (1350, 450))):
                yy = qy + 10 * math.sin(t * 3 + i)
                text(ctx, "?", qx, yy, 90, WHITE, aw * 0.85, scale=pop(prog(t, c.s(3) + i * 0.15, 0.4)))
            bolt_icon(ctx, 1420, 380, 110, YEL, aw)
        # Heute Standard
        a5 = fade(t, c.w(4, "Standard") - 0.6)
        if a5 > 0:
            sc = pop(prog(t, c.w(4, "Standard") - 0.6, 0.5))
            for i, x in enumerate((1250, 1420, 1590)):
                hh = house(ctx, x, 650, 120, 90 + i * 15, 60, a5)
                draw_rod(ctx, hh, a5, 50, w=4, soil=0)
            badge(ctx, "Heute: Standard", 1420, 330, 44, WHITE, GREEN, a5, 0.9, scale=sc)


# =====================================================================
class K4(Scene):
    sky = 0.5

    def setup(self):
        c = self.c
        self.t_hit = c.s(9) - 0.25
        self.flash(self.t_hit + 0.12, 1.0)
        self.flash(c.s(3) + 0.3, 0.4)

    def draw(self, ctx, t):
        c = self.c
        gy = 690
        ground(ctx, gy, hills=False, col=SOIL)
        fill_rrect(ctx, 0, gy - 4, W, 10, 0, (0.18, 0.32, 0.2), 1)
        for i in range(60):
            rx = (i * 397) % W
            ry = gy + 20 + (i * 131) % 150
            circle(ctx, rx, ry, 4, (0.24, 0.17, 0.14))
        hs = house(ctx, 700, gy, 500, 250, 170)
        tip, path = rod_path(hs, 110, 120)
        wx = path[3][0]
        p1, p2 = path[0:2], path[1:4]
        p3 = [path[3], path[4]]
        band = [(wx, gy + 25), (hs["x0"] + 10, gy + 25)]

        S = c.S
        on1 = fade(t, c.s(1) - 0.1)
        on2 = fade(t, c.s(4) - 0.1)
        on3 = fade(t, c.s(7) - 0.1)
        hi1 = fade(t, c.s(1) - 0.1, c.s(4), 0.3, 0.5)
        hi2 = fade(t, c.s(4) - 0.1, c.s(7), 0.3, 0.5)
        hi3 = fade(t, c.s(7) - 0.1, c.s(9) - 0.3, 0.3, 0.5)
        all_ = fade(t, c.s(10) - 0.1, c.s(11) + 0.1, 0.3, 0.3)
        thick = 6 + 6 * ease(prog(t, c.w(6, "dick"), 0.6))
        bad = fade(t, c.w(11, "schlecht") - 0.1)

        def part(pts, on, hi, w):
            col = mix(METAL, YEL, max(hi, all_))
            if max(hi, all_) > 0:
                glow_line(ctx, pts, YEL, max(hi, all_) * (0.75 + 0.25 * math.sin(t * 7)), w)
            line(ctx, pts, col, 0.35 + 0.65 * on, w)

        part(p2, on2, hi2, thick)
        ground_col_on = on3
        part(p3, on3, hi3, 9)
        part(band, on3 * fade(t, c.w(8, "Fundament") - 0.1), hi3, 8)
        part(p1, on1, hi1, 8)
        poly(ctx, [(tip[0], tip[1] - 18), (tip[0] - 8, tip[1] + 4), (tip[0] + 8, tip[1] + 4)],
             mix(METAL, YEL, max(hi1, all_)), 1)
        if bad > 0:
            line(ctx, p3, RED, bad, 10)
            check_badge(ctx, wx + 60, gy + 70, 26, bad, pop(prog(t, c.w(11, "schlecht") - 0.1, 0.4)), ok=False)

        # Nummern + Beschriftungen
        labels = [(1, "Fangeinrichtung", "Metallstangen oder Drähte, ganz oben", tip, c.s(1), c.s(2), 230),
                  (2, "Ableitung", "dicke Kabel oder Metallbänder, außen", (wx, 520), c.s(4), c.s(5), 450),
                  (3, "Erdung", "Metallstäbe oder Band im Fundament", (wx, gy + 70), c.s(7), c.s(8), 640)]
        for n, title, sub, (px, py), t0, t1, ly in labels:
            a = fade(t, t0 - 0.1)
            if a <= 0:
                continue
            sc = pop(prog(t, t0 - 0.1, 0.45))
            col = RED if (n == 3 and bad > 0) else YEL
            line(ctx, [(px + 14, py), (1210, ly)], WHITE, a * 0.55, 3, dash=[8, 8])
            circle(ctx, 1250, ly, 36 * sc, col, a)
            text(ctx, str(n), 1250, ly + 1, 44, INK, a, scale=sc)
            text(ctx, title, 1305, ly - 4, 48, WHITE, a, align="l")
            text(ctx, sub, 1305, ly + 44, 28, (0.8, 0.85, 0.95), fade(t, t1 - 0.1), align="l", weight="normal")

        # Blitz + Strom in die Erde
        if not hasattr(self, "bolt"):
            self.bolt = bolt_points(560, -20, tip[0], tip[1] - 18, seed=31)
        strike(ctx, t, self.t_hit, self.bolt, w=8)
        af = fade(t, self.t_hit + 0.12, c.s(10) + 0.4, 0.1, 0.5)
        if af > 0:
            flow(ctx, path, t, YEL, af, 7, f=ease(prog(t, self.t_hit + 0.12, 0.8)))
            flow(ctx, band, t, YEL, af * fade(t, self.t_hit + 0.8), 6)
            if t > self.t_hit + 0.8:
                ctx.save()
                ctx.rectangle(0, gy + 6, W, 400)
                ctx.clip()
                for i in range(5):
                    r = 30 + ((t - self.t_hit) * 180 + i * 55) % 280
                    ring(ctx, wx, gy + 120, r, YEL, af * (1 - r / 300) * 0.8, 4)
                    ring(ctx, (wx + band[1][0]) / 2, gy + 25, r * 1.2, YEL, af * (1 - r / 300) * 0.4, 3)
                ctx.restore()
        # Schlechte Erdung -> anderer Weg durchs Haus
        if bad > 0:
            alt = [(wx, 560), (hs["x1"] - 30, 575), (840, 600), (620, 650), (560, gy)]
            fk = ease(prog(t, c.w(11, "anderen") - 0.2, 0.9))
            flow(ctx, alt, t, RED, bad, 6, f=fk, speed=500)
            if all_ <= 0:
                pass


# =====================================================================
class K5(Scene):
    def setup(self):
        c = self.c
        self.t_hit = c.w(5, "sicheren") - 0.3
        self.flash(self.t_hit + 0.12, 1.0)

    def draw(self, ctx, t):
        c = self.c
        ground(ctx)
        dim = 1 - 0.75 * fade(t, c.s(6) - 0.1, None, 0.5)
        hl = house(ctx, 600, GROUND_Y, 360, 220, 150, dim)
        tip, path = draw_rod(ctx, hl, dim, 100, soil=0)
        hr = house(ctx, 1320, GROUND_Y, 360, 220, 150, dim)
        badge(ctx, "mit Blitzableiter", 600, 842, 30, WHITE, a=dim * fade(t, c.s(1)), bga=0.6)
        badge(ctx, "ohne Blitzableiter", 1320, 842, 30, WHITE, a=dim * fade(t, c.s(1)), bga=0.6)
        # Mythos
        am = fade(t, c.s(1) - 0.1, c.s(6) - 0.1)
        if am > 0:
            sc = pop(prog(t, c.s(1) - 0.1, 0.5))
            g = 1 - 0.45 * fade(t, c.s(3))
            label_card(ctx, [("„Zieht Blitze an“", WHITE)], 960, 215, 74, am * g, sc, accent=RED)
            fx = prog(t, c.s(2), 0.6)
            if fx > 0:
                cross(ctx, 960, 215, 170, RED, am, 22, f=fx)
        # gleich hoch
        ah = fade(t, c.w(3, "hoch") - 0.2, c.s(5))
        if ah > 0:
            fk = ease(prog(t, c.w(3, "hoch") - 0.2, 0.8))
            ay = hl["apex"][1]
            line(ctx, [(380, ay), (lerp(380, 1560, fk), ay)], YEL, ah, 4, dash=[14, 10])
            for x in (390, 1530):
                arrow(ctx, x, GROUND_Y - 6, x, ay + 8, YEL, ah * fk, 5, 18, both=True)
            badge(ctx, "gleich hoch", 960, ay - 50 + 20, 38, YEL, a=ah)
        a4 = fade(t, c.s(4) - 0.1, c.s(6))
        if a4 > 0:
            sc = pop(prog(t, c.s(4) - 0.1, 0.5))
            text(ctx, "=", 960, 640, 130, WHITE, a4, scale=sc)
            badge(ctx, "nicht gefährdeter", 960, 520, 36, WHITE, GREEN, a4, 0.9, scale=sc)
        # sicherer Weg
        if not hasattr(self, "bolt"):
            self.bolt = bolt_points(520, -20, tip[0], tip[1] - 16, seed=13)
        strike(ctx, t, self.t_hit, self.bolt, w=8)
        af = fade(t, self.t_hit + 0.12, c.s(6), 0.1, 0.5)
        if af > 0:
            flow(ctx, path, t, YEL, af, 7, f=ease(prog(t, self.t_hit + 0.12, 0.7)))
            badge(ctx, "sicherer Weg", 260, 560, 36, INK, YEL, af * fade(t, c.w(5, "Weg") - 0.2), 0.95)
        # Name
        an = fade(t, c.s(6) - 0.1)
        if an > 0:
            sc = pop(prog(t, c.s(6) - 0.1, 0.5))
            set_font(ctx, 96)
            w1, w2 = text_w(ctx, "Blitz", 96), text_w(ctx, "ableiter", 96)
            x0 = 960 - (w1 + w2) / 2
            text(ctx, "Blitz", x0, 260, 96, WHITE, an, align="l", scale=1)
            text(ctx, "ableiter", x0 + w1, 260, 96, YEL, an, align="l", scale=1)
            line(ctx, [(x0 + w1, 320), (x0 + w1 + w2 * ease(prog(t, c.w(7, "leitet"), 0.6)), 320)], YEL, an, 6)
            rows = [(c.w(7, "leitet"), True, "leitet den Blitzstrom ab"),
                    (c.w(7, "verhindert"), False, "verhindert keinen Blitz"),
                    (c.w(8, "verhindert"), True, "verhindert den Schaden")]
            for i, (t0, ok, s) in enumerate(rows):
                a = fade(t, t0 - 0.1)
                if a <= 0:
                    continue
                y = 450 + i * 105
                s2 = pop(prog(t, t0 - 0.1, 0.4))
                fill_rrect(ctx, 560, y - 42, 800, 84, 42, (0, 0, 0), 0.55 * a)
                check_badge(ctx, 615, y, 28, a, s2, ok=ok)
                text(ctx, s, 670, y, 42, WHITE if ok else (1, 0.75, 0.72), a, align="l")


# =====================================================================
class K6(Scene):
    sky = 0.0
    rain = 0.25

    def setup(self):
        c = self.c
        self.t_hit = c.w(1, "Nähe") - 0.3
        self.flash(self.t_hit + 0.12, 0.7)
        self.bolt = bolt_points(380, 200, 330, 420, seed=17, n=8, jit=25)
        self.wire = [(170, 760), (1050, 760)]
        self.devices = {"Fernseher": (740, 530, 330, 200), "Router": (1290, 475, 170, 46), "Computer": (1580, 520, 240, 160)}

    def room(self, ctx, t, a):
        fill_rrect(ctx, 150, 140, 1620, 650, 18, (0.12, 0.15, 0.25), a)
        fill_rrect(ctx, 150, 750, 1620, 40, 0, (0.09, 0.11, 0.18), a)
        # Fenster
        fill_rrect(ctx, 220, 200, 300, 230, 10, (0.03, 0.04, 0.08), a)
        ctx.save()
        rrect(ctx, 220, 200, 300, 230, 10)
        ctx.clip()
        for i in range(25):
            x = 220 + (i * 53) % 300
            y = 200 + ((i * 97) + t * 900) % 230
            line(ctx, [(x, y), (x + 3, y + 18)], (0.6, 0.7, 0.9), a * 0.5, 2)
        strike(ctx, t, self.t_hit, self.bolt, w=5)
        ctx.restore()
        rrect(ctx, 220, 200, 300, 230, 10)
        rgba(ctx, (0.35, 0.4, 0.55), a)
        ctx.set_line_width(10)
        ctx.stroke()
        line(ctx, [(370, 200), (370, 430)], (0.35, 0.4, 0.55), a, 8)

    def draw(self, ctx, t):
        c = self.c
        a = 1.0
        self.room(ctx, t, a)
        # Felder
        if t > self.t_hit:
            afd = fade(t, self.t_hit + 0.1, c.s(3), 0.2, 0.6)
            for i in range(4):
                r = 60 + ((t - self.t_hit) * 300 + i * 160) % 640
                ctx.save()
                ctx.set_dash([18, 14])
                ring(ctx, 370, 320, r, BLUE, afd * (1 - r / 700) * 0.8, 4)
                ctx.restore()
            badge(ctx, "elektrische & magnetische Felder", 960, 205, 34, (0.7, 0.82, 1), a=fade(t, c.w(1, "Felder") - 0.6, c.s(3)))
        # Möbel & Geräte
        tvx, tvy, tvw, tvh = self.devices["Fernseher"]
        fill_rrect(ctx, tvx - 40, 640, tvw + 80, 110, 8, (0.22, 0.16, 0.13), a)
        fill_rrect(ctx, tvx, tvy, tvw, tvh, 10, (0.05, 0.06, 0.1), a)
        fill_rrect(ctx, tvx + 10, tvy + 10, tvw - 20, tvh - 20, 6, (0.14, 0.25, 0.42), a)
        line(ctx, [(tvx + tvw / 2, tvy + tvh), (tvx + tvw / 2, 640)], (0.3, 0.3, 0.35), a, 10)
        rx, ry, rw, rh = self.devices["Router"]
        fill_rrect(ctx, rx - 40, ry + rh, rw + 80, 14, 3, (0.3, 0.22, 0.17), a)
        fill_rrect(ctx, rx, ry, rw, rh, 8, (0.85, 0.87, 0.92), a)
        for k in range(2):
            line(ctx, [(rx + 25 + k * 120, ry), (rx + 15 + k * 140, ry - 50)], (0.85, 0.87, 0.92), a, 6)
        for k in range(4):
            on = (int(t * 4) + k) % 3 != 0
            circle(ctx, rx + 40 + k * 28, ry + rh / 2, 5, GREEN if on else (0.2, 0.4, 0.25), a)
        mx, my, mw, mh = self.devices["Computer"]
        fill_rrect(ctx, mx - 70, 640, mw + 140, 16, 3, (0.3, 0.22, 0.17), a)
        line(ctx, [(mx - 50, 656), (mx - 50, 750)], (0.3, 0.22, 0.17), a, 10)
        line(ctx, [(mx + mw + 50, 656), (mx + mw + 50, 750)], (0.3, 0.22, 0.17), a, 10)
        fill_rrect(ctx, mx, my, mw, mh, 8, (0.05, 0.06, 0.1), a)
        fill_rrect(ctx, mx + 8, my + 8, mw - 16, mh - 16, 4, (0.16, 0.3, 0.3), a)
        line(ctx, [(mx + mw / 2, my + mh), (mx + mw / 2, 640)], (0.3, 0.3, 0.35), a, 10)
        # Leitung + Steckdose
        line(ctx, self.wire, (0.9, 0.9, 0.9), a, 6)
        fill_rrect(ctx, 1020, 690, 60, 60, 10, (0.88, 0.9, 0.95), a)
        circle(ctx, 1040, 720, 5, INK, a)
        circle(ctx, 1060, 720, 5, INK, a)
        for (x1, y1) in ((tvx + tvw * 0.7, 700), (1300, ry + rh + 14), (mx + 20, 656)):
            ctx.new_path()
            ctx.move_to(1050, 700)
            ctx.curve_to(1050, 620, x1, y1 + 60, x1, y1)
            rgba(ctx, (0.75, 0.75, 0.78), a * 0.8)
            ctx.set_line_width(4)
            ctx.stroke()
        # Spannungsspitzen
        prot = fade(t, c.w(4, "Überspannungsschutz") - 0.1)
        if c.s(2) - 0.2 <= t:
            per = 1.7
            k0 = (t - c.s(2) + 0.2)
            for n in range(2):
                k = ((k0 + n * per / 2) % per) / per
                x = lerp(170, 1050, k)
                amp = 80
                if prot > 0 and x > 850:
                    # Der Überspannungsschutz fängt die Spitze ab
                    amp = 80 * ((1 - prot) + prot * max(0.0, 1 - (x - 850) / 40))
                sa = fade(t, c.s(2) - 0.2, c.s(5) + 0.5)
                if amp > 2:
                    pts = [(x - 50, 760), (x - 20, 760), (x - 8, 760 - amp), (x + 4, 760 + amp * 0.3), (x + 16, 760), (x + 50, 760)]
                    glow_line(ctx, pts, RED, sa, 5)
            text(ctx, "Spannungsspitze", 450, 680, 32, (1, 0.6, 0.55), fade(t, c.w(2, "Spannungsspitzen") - 0.1, c.s(4)))
        # Geräte in Gefahr / geschützt
        for name, (x, y, w_, h_) in self.devices.items():
            t0 = c.w(3, name)
            ad = fade(t, t0 - 0.1, c.s(4) + 0.6) if prot < 1 else 0
            if ad > 0:
                pulse = 0.6 + 0.4 * math.sin(t * 10)
                rrect(ctx, x - 8, y - 8, w_ + 16, h_ + 16, 12)
                rgba(ctx, RED, ad * pulse)
                ctx.set_line_width(6)
                ctx.stroke()
                cx_, cy_ = x + w_ / 2, y - 55
                poly(ctx, [(cx_, cy_ - 30), (cx_ - 30, cy_ + 22), (cx_ + 30, cy_ + 22)], RED, ad)
                text(ctx, "!", cx_, cy_ + 5, 36, WHITE, ad)
            ag = fade(t, c.w(4, "Überspannungsschutz") + 1.6, c.s(5) + 2.5)
            if ag > 0:
                check_badge(ctx, x + w_ / 2, y - 50, 26, ag, pop(prog(t, c.w(4, "Überspannungsschutz") + 1.6, 0.4)))
        if prot > 0:
            sc = pop(prog(t, c.w(4, "Überspannungsschutz") - 0.1, 0.5))
            fill_rrect(ctx, 850 - 45 * sc, 760 - 38 * sc, 90 * sc, 76 * sc, 14, GREEN, prot)
            sx, sy = 850, 758
            poly(ctx, [(sx, sy - 26 * sc), (sx + 22 * sc, sy - 16 * sc), (sx + 18 * sc, sy + 12 * sc), (sx, sy + 26 * sc),
                       (sx - 18 * sc, sy + 12 * sc), (sx - 22 * sc, sy - 16 * sc)], WHITE, prot)
            badge(ctx, "Überspannungsschutz", 850, 650, 34, WHITE, GREEN, prot * fade(t, 0, c.s(5)), 0.95, scale=sc)
        # Zusammenfassung äußerer / innerer Schutz
        a5 = fade(t, c.s(5) - 0.1)
        if a5 > 0:
            fill_rrect(ctx, 150, 140, 1620, 650, 18, (0.02, 0.03, 0.06), 0.55 * a5)
            for i, (title, obj, t0) in enumerate((("Äußerer Blitzschutz", "→ Gebäude", c.w(5, "äußere")),
                                                  ("Innerer Blitzschutz", "→ Elektronik", c.w(5, "innere")))):
                aa = fade(t, t0 - 0.1)
                if aa <= 0:
                    continue
                cx_ = 600 + i * 720
                sc = pop(prog(t, t0 - 0.1, 0.45))
                label_card(ctx, [(title, YEL), (obj, WHITE)], cx_, 440, 50, aa, sc)


# =====================================================================
class K7(Scene):
    sky = 0.6

    def setup(self):
        c = self.c
        self.flash(c.s(1) + 0.05, 0.3)

    def building(self, ctx, kind, x, gy, a, sc):
        if kind == "kh":
            fill_rrect(ctx, x - 110 * sc, gy - 190 * sc, 220 * sc, 190 * sc, 6, (0.75, 0.8, 0.9), a)
            fill_rrect(ctx, x - 32 * sc, gy - 260 * sc, 64 * sc, 64 * sc, 10, (0.2, 0.45, 0.85), a)
            text(ctx, "H", x, gy - 228 * sc, 48, WHITE, a, scale=sc)
            for r in range(2):
                for k in range(4):
                    fill_rrect(ctx, x - 90 * sc + k * 48 * sc, gy - 170 * sc + r * 60 * sc, 30 * sc, 34 * sc, 4,
                               (0.3, 0.4, 0.6), a)
        elif kind == "hh":
            fill_rrect(ctx, x - 70 * sc, gy - 330 * sc, 140 * sc, 330 * sc, 6, (0.5, 0.58, 0.75), a)
            for r in range(7):
                for k in range(3):
                    fill_rrect(ctx, x - 52 * sc + k * 40 * sc, gy - 310 * sc + r * 42 * sc, 24 * sc, 26 * sc, 3,
                               (0.98, 0.85, 0.5) if (r + k) % 3 else (0.25, 0.3, 0.45), a)
        elif kind == "vs":
            ctx.new_path()
            ctx.move_to(x - 150 * sc, gy)
            ctx.line_to(x - 150 * sc, gy - 110 * sc)
            ctx.curve_to(x - 100 * sc, gy - 200 * sc, x + 100 * sc, gy - 200 * sc, x + 150 * sc, gy - 110 * sc)
            ctx.line_to(x + 150 * sc, gy)
            ctx.close_path()
            rgba(ctx, (0.62, 0.55, 0.75), a)
            ctx.fill()
            for k in range(5):
                circle(ctx, x - 80 * sc + k * 40 * sc, gy - 55 * sc, 11 * sc, (0.25, 0.22, 0.35), a)
                fill_rrect(ctx, x - 92 * sc + k * 40 * sc, gy - 42 * sc, 24 * sc, 30 * sc, 8, (0.25, 0.22, 0.35), a)
        elif kind == "efh":
            house(ctx, x, gy, 200 * sc, 130 * sc, 100 * sc, a)

    def draw(self, ctx, t):
        c = self.c
        gy = 720
        ground(ctx, gy, hills=False)
        aq = fade(t, c.s(0) - 0.2, c.s(5) - 0.1)
        label_card(ctx, [("Muss jedes Haus einen Blitzableiter haben?", WHITE)], 960, 190, 46, aq,
                   pop(prog(t, c.s(0) - 0.2, 0.5)))
        an = fade(t, c.s(1) - 0.05, c.s(2) + 0.1, 0.15, 0.3)
        if an > 0:
            ctx.save()
            ctx.translate(960, 380)
            ctx.rotate(-0.12)
            sc = pop(prog(t, c.s(1) - 0.05, 0.35)) * 1.0
            rrect(ctx, -170 * sc, -75 * sc, 340 * sc, 150 * sc, 20)
            rgba(ctx, RED, an)
            ctx.set_line_width(10)
            ctx.stroke()
            text(ctx, "NEIN", 0, 0, 110, RED, an, scale=sc)
            ctx.restore()
        al = fade(t, c.w(2, "Landesbau") - 0.1)
        badge(ctx, "§  Landesbauordnungen", 960, 300, 42, YEL, a=al, scale=pop(prog(t, c.w(2, "Landesbau") - 0.1, 0.45)))
        items = [("kh", 380, "Krankenhäuser", c.w(3, "Krankenh")), ("hh", 760, "Hochhäuser", c.w(3, "Hochh")),
                 ("vs", 1160, "Versammlungsstätten", c.w(3, "Versammlungs")), ("efh", 1560, "Wohnhaus", c.s(4) - 0.1)]
        for kind, x, lbl, t0 in items:
            a = fade(t, t0 - 0.15)
            if a <= 0:
                continue
            sc = pop(prog(t, t0 - 0.15, 0.5))
            self.building(ctx, kind, x, gy, a, sc)
            text(ctx, lbl, x, gy + 40, 32, WHITE, a)
            if kind != "efh":
                check_badge(ctx, x + 95, gy - (350 if kind == "hh" else 230), 30, a, pop(prog(t, t0 + 0.3, 0.4)))
            else:
                ab = fade(t, t0 + 0.3)
                circle(ctx, x + 95, gy - 250, 32 * pop(prog(t, t0 + 0.3, 0.4)), YEL, ab)
                text(ctx, "?", x + 95, gy - 248, 48, INK, ab)
                badge(ctx, "oft freiwillig, aber sinnvoll", x - 90, gy - 340, 32, WHITE, a=fade(t, c.w(4, "freiwillig") - 0.1))
        ar = fade(t, c.s(5) - 0.1)
        if ar > 0:
            label_card(ctx, [("Regeln je nach Bundesland und Gebäude", WHITE)], 960, 190, 46, ar,
                       pop(prog(t, c.s(5) - 0.1, 0.5)))


# =====================================================================
class K8(Scene):
    sky = 0.4

    def icon(self, ctx, i, x, y, a):
        if i == 0:
            house(ctx, x - 22, y + 30, 50, 36, 26, a, windows=False)
            fill_rrect(ctx, x + 10, y + 6, 46, 20, 8, (0.4, 0.6, 0.95), a)
            circle(ctx, x + 20, y + 28, 7, INK, a)
            circle(ctx, x + 46, y + 28, 7, INK, a)
        elif i == 1:
            line(ctx, [(x, y + 34), (x, y)], (0.5, 0.35, 0.2), a, 8)
            circle(ctx, x, y - 8, 24, GREEN, a)
            line(ctx, [(x - 34, y + 34), (x + 34, y - 34)], RED, a, 6)
        else:
            fill_rrect(ctx, x - 18, y - 16, 36, 34, 6, WHITE, a)
            line(ctx, [(x - 8, y - 16), (x - 8, y - 32)], WHITE, a, 6)
            line(ctx, [(x + 8, y - 16), (x + 8, y - 32)], WHITE, a, 6)
            line(ctx, [(x, y + 18), (x, y + 40)], WHITE, a, 6)

    def draw(self, ctx, t):
        c = self.c
        a0 = fade(t, c.s(0) - 0.3, None, 0.5)
        sc = pop(prog(t, c.s(0) - 0.3, 0.6))
        fill_rrect(ctx, 960 - 700 * sc, 140, 1400 * sc, 640, 34, (0.03, 0.04, 0.08), 0.8 * a0)
        rrect(ctx, 960 - 700 * sc, 140, 1400 * sc, 640, 34)
        rgba(ctx, YEL, 0.5 * a0)
        ctx.set_line_width(3)
        ctx.stroke()
        bolt_icon(ctx, 760, 225, 70, YEL, a0)
        text(ctx, "Bei Gewitter", 980, 228, 58, WHITE, a0)
        items = ["Gebäude oder Auto aufsuchen", "Freie Flächen, einzelne Bäume und Wasser meiden",
                 "Empfindliche Geräte vom Strom nehmen"]
        for i, s in enumerate(items):
            t0 = c.s(i + 1) - 0.1
            a = fade(t, t0)
            if a <= 0:
                continue
            y = 370 + i * 130
            s2 = pop(prog(t, t0, 0.45))
            hl = fade(t, c.s(4) - 0.1) if i == 2 else 0
            if hl > 0:
                fill_rrect(ctx, 330, y - 52, 1260, 104, 22, YEL, 0.16 * hl * (0.7 + 0.3 * math.sin(t * 6)))
            fill_rrect(ctx, 370, y - 32, 64, 64, 12, WHITE, a * 0.15)
            check(ctx, 402, y, 50, GREEN, a, 10, f=ease(prog(t, t0 + 0.35, 0.4)))
            self.icon(ctx, i, 510, y, a)
            text(ctx, s, 590, y, 38, WHITE, a, align="l", scale=1)
        a4 = fade(t, c.w(4, "Elektronik") - 0.2)
        badge(ctx, "sicherster Schutz für Elektronik", 960, 730, 34, INK, YEL, a4, 0.95,
              scale=pop(prog(t, c.w(4, "Elektronik") - 0.2, 0.45)))


# =====================================================================
class Outro(Scene):
    sky = 0.6

    def setup(self):
        c = self.c
        self.flash(c.s(3) - 0.2, 0.45)

    def draw(self, ctx, t):
        c = self.c
        a_main = fade(t, c.s(0) - 0.4, c.s(3) - 0.1, 0.4, 0.4)
        if a_main > 0:
            a = a_main * fade(t, c.w(0, "keine") - 0.1)
            if a > 0:
                sc = pop(prog(t, c.w(0, "keine") - 0.1, 0.5))
                fill_rrect(ctx, 960 - 340 * sc, 170, 680 * sc, 100, 50, (0, 0, 0), 0.6 * a)
                check_badge(ctx, 960 - 270 * sc, 220, 30, a, sc)
                text(ctx, "zieht keine Blitze an", 990, 220, 46, WHITE, a, scale=sc)
            steps = [("Fangen", c.w(1, "Fangen")), ("Ableiten", c.w(1, "Ableiten")), ("Erden", c.w(1, "Erden"))]
            for i, (s, t0) in enumerate(steps):
                aa = a_main * fade(t, t0 - 0.15)
                if aa <= 0:
                    continue
                x, y = 560 + i * 400, 470
                sc = pop(prog(t, t0 - 0.15, 0.5))
                circle(ctx, x, y, 115 * sc, (0.04, 0.05, 0.1), aa * 0.85)
                ring(ctx, x, y, 115 * sc, YEL, aa, 6)
                if i == 0:
                    line(ctx, [(x, y + 60 * sc), (x, y - 20 * sc)], METAL, aa, 8)
                    poly(ctx, [(x, y - 40 * sc), (x - 9, y - 16 * sc), (x + 9, y - 16 * sc)], METAL, aa)
                    bolt_icon(ctx, x - 40 * sc, y - 55 * sc, 70 * sc, YEL, aa)
                elif i == 1:
                    line(ctx, [(x - 30 * sc, y - 60 * sc), (x - 30 * sc, y + 60 * sc)], METAL, aa, 8)
                    arrow(ctx, x + 25 * sc, y - 50 * sc, x + 25 * sc, y + 45 * sc, YEL, aa, 8, 24)
                else:
                    ground_symbol(ctx, x, y + 10 * sc, 110 * sc, YEL, aa, 8)
                text(ctx, s, x, y + 165, 46, WHITE, aa, scale=sc)
                if i < 2:
                    arrow(ctx, x + 135, y, x + 265, y, WHITE, aa * 0.6, 5, 18)
            ai = a_main * fade(t, c.w(2, "innere") - 0.1)
            if ai > 0:
                badge(ctx, "+ innerer Blitzschutz → Elektronik", 960, 765, 38, INK, YEL, ai, 0.95,
                      scale=pop(prog(t, c.w(2, "innere") - 0.1, 0.45)))
        # Endkarte
        ae = fade(t, c.s(3) - 0.1, None, 0.6)
        if ae > 0:
            sc = pop(prog(t, c.s(3) - 0.1, 0.7))
            pulse = 0.85 + 0.15 * math.sin(t * 4)
            circle(ctx, 960, 360, 190 * sc, YEL, 0.08 * ae * pulse)
            circle(ctx, 960, 360, 145 * sc, (0.04, 0.05, 0.1), ae)
            ring(ctx, 960, 360, 145 * sc, YEL, ae, 8)
            bolt_icon(ctx, 960, 360, 190 * sc, YEL, ae)
            text(ctx, "Wie funktioniert ein Blitzableiter?", 960, 590, 52, WHITE, ae, scale=sc)
            text(ctx, "Wissen, kurz erklärt", 960, 655, 38, (0.8, 0.85, 0.95), ae * fade(t, c.w(3, "Wissen") - 0.1),
                 weight="normal")
            al = fade(t, c.w(3, "Like") - 0.15)
            ab = fade(t, c.w(3, "abonniere") - 0.15)
            badge(ctx, "LIKE", 820, 760, 40, INK, YEL, al, 1, scale=pop(prog(t, c.w(3, "Like") - 0.15, 0.45)))
            badge(ctx, "ABONNIEREN", 1060, 760, 40, WHITE, RED, ab, 1, scale=pop(prog(t, c.w(3, "abonniere") - 0.15, 0.45)))


SCENES = {"intro": Intro, "k1": K1, "k2": K2, "k3": K3, "k4": K4, "k5": K5, "k6": K6, "k7": K7, "k8": K8, "outro": Outro}
