# -*- coding: utf-8 -*-
"""YouTube-Short (1080x1920, 9:16) im gleichen Look wie das lange Video.

  CONTENT=content_short BUILD=build_short python3 short.py            # Video rendern
  CONTENT=content_short BUILD=build_short python3 short.py --preview 3 12
Wichtige Inhalte bleiben aus den Zonen, die YouTube in Shorts überdeckt (unten, rechter Rand).
"""
import json
import math
import os
import random
import re
import subprocess
import sys
import time
from multiprocessing import Process
from pathlib import Path

import cairo

import gfx
from content_short import CHAPTERS
from gfx import *  # noqa: F401,F403
from scenes import Cue, Scene

SW, SH = 1080, 1920
gfx.W, gfx.H = SW, SH  # Wetter/Boden zeichnen im Hochformat
ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build_short"
FINAL = ROOT / "Short_Blitzableiter.mp4"
SCENE_MODULE = sys.modules[__name__]

T = json.load(open(BUILD / "timing.json"))
DUR = T["duration"]
NFRAMES = int(math.ceil(DUR * FPS))


# =====================================================================
class Hook(Scene):
    def setup(self):
        c = self.c
        self.t_open = 0.1
        self.b_open = bolt_points(200, -20, 140, 1170, seed=11, n=16, jit=50)
        self.flash(self.t_open + 0.12, 1.0)
        self.t_hit = c.w(2, "Haus") - 0.35
        self.flash(self.t_hit + 0.12, 0.9)

    def draw(self, ctx, t):
        c = self.c
        ground(ctx, 1180)
        strike(ctx, t, self.t_open, self.b_open, w=7)
        hs = house(ctx, 540, 1180, 440, 250, 170)
        tip, path = draw_rod(ctx, hs, rod_h=120, soil=0)
        if not hasattr(self, "b_hit"):
            self.b_hit = bolt_points(470, -20, tip[0], tip[1] - 14, seed=5, n=16, jit=45)
        a0 = fade(t, c.s(1) + 0.2, c.e(1) + 0.6)
        if a0 > 0:
            sc = pop(prog(t, c.s(1) + 0.2, 0.45))
            fill_rrect(ctx, 70, 560, 330, 140, 28, (0, 0, 0), 0.55 * a0)
            sun_icon(ctx, 150, 630, 30 * sc, a0)
            text(ctx, "<", 235, 628, 64, WHITE, a0)
            bolt_icon(ctx, 320, 630, 100 * sc, YEL, a0)
            a1 = fade(t, c.w(1, "20.000"), c.e(1) + 0.6)
            badge(ctx, "≈ 20.000 A", 790, 630, 56, YEL, a=a1, scale=pop(prog(t, c.w(1, "20.000"), 0.45)))
        ag = fade(t, c.w(2, "Metallstange") - 0.1)
        if ag > 0:
            pulse = 0.6 + 0.4 * math.sin(t * 8)
            circle(ctx, tip[0], tip[1] + 40, 60, YEL, 0.12 * ag * pulse)
            line(ctx, [tip, hs["apex"]], YEL, ag, 8)
        strike(ctx, t, self.t_hit, self.b_hit, w=8)
        fa = fade(t, self.t_hit + 0.12, None, 0.1)
        if fa > 0:
            flow(ctx, path, t, YEL, fa, 7, f=ease(prog(t, self.t_hit + 0.12, 0.55)))
            ctx.save()
            ctx.rectangle(0, 1180, SW, 600)
            ctx.clip()
            for i in range(5):
                r = 30 + ((t - self.t_hit) * 200 + i * 40) % 200
                ring(ctx, path[-1][0], 1180, r, YEL, fa * (1 - r / 230) * 0.7, 3)
            ctx.restore()


class Teile(Scene):
    sky = 0.5

    def setup(self):
        c = self.c
        self.t_hit = c.s(3) - 0.2
        self.flash(self.t_hit + 0.12, 1.0)

    def draw(self, ctx, t):
        c = self.c
        gy = 1060
        ground(ctx, gy, hills=False, col=SOIL)
        fill_rrect(ctx, 0, gy - 4, SW, 10, 0, (0.18, 0.32, 0.2), 1)
        for i in range(50):
            circle(ctx, (i * 397) % SW, gy + 25 + (i * 131) % 300, 4, (0.24, 0.17, 0.14))
        hs = house(ctx, 470, gy, 440, 230, 160)
        tip, path = rod_path(hs, 110, 130)
        wx = path[3][0]
        p1, p2, p3 = path[0:2], path[1:4], [path[3], path[4]]
        band = [(wx, gy + 25), (hs["x0"] + 10, gy + 25)]
        his = [fade(t, c.s(i + 1) - 0.1, c.s(i + 2) if i < 2 else None, 0.3, 0.4) for i in range(3)]
        ons = [fade(t, c.s(i + 1) - 0.1) for i in range(3)]

        def part(pts, on, hi, w):
            if hi > 0:
                glow_line(ctx, pts, YEL, hi * (0.75 + 0.25 * math.sin(t * 7)), w)
            line(ctx, pts, mix(METAL, YEL, hi), 0.35 + 0.65 * on, w)

        part(p2, ons[1], his[1], 9)
        part(p3, ons[2], his[2], 9)
        part(band, ons[2], his[2], 8)
        part(p1, ons[0], his[0], 8)
        poly(ctx, [(tip[0], tip[1] - 18), (tip[0] - 8, tip[1] + 4), (tip[0] + 8, tip[1] + 4)], mix(METAL, YEL, his[0]))
        # Nummern an den Teilen
        for i, (px, py) in enumerate(((tip[0] + 70, tip[1] + 10), (wx + 70, 930), (wx + 70, gy + 110))):
            a = ons[i]
            if a > 0:
                sc = pop(prog(t, c.s(i + 1) - 0.1, 0.45))
                circle(ctx, px, py, 40 * sc, YEL, a)
                text(ctx, str(i + 1), px, py + 1, 50, INK, a, scale=sc)
        # Großes Etikett des aktuellen Teils
        names = ["Fangeinrichtung", "Ableitung", "Erdung"]
        a3 = fade(t, c.s(0) - 0.1, c.s(1) - 0.1, 0.3, 0.2)
        badge(ctx, "3 Teile", 540, 480, 64, INK, YEL, a3, 1, scale=pop(prog(t, c.s(0) - 0.1, 0.45)))
        for i, nm in enumerate(names):
            a = fade(t, c.s(i + 1) - 0.1, c.s(i + 2) - 0.1 if i < 2 else None, 0.25, 0.2)
            badge(ctx, f"{i + 1}  {nm}", 540, 480, 64, INK, YEL, a, 1, scale=pop(prog(t, c.s(i + 1) - 0.1, 0.45)))
        if not hasattr(self, "bolt"):
            self.bolt = bolt_points(380, -20, tip[0], tip[1] - 18, seed=31, n=16, jit=45)
        strike(ctx, t, self.t_hit, self.bolt, w=8)
        af = fade(t, self.t_hit + 0.12, None, 0.1)
        if af > 0:
            flow(ctx, path, t, YEL, af, 7, f=ease(prog(t, self.t_hit + 0.12, 0.8)))
            flow(ctx, band, t, YEL, af * fade(t, self.t_hit + 0.8), 6)
            if t > self.t_hit + 0.8:
                ctx.save()
                ctx.rectangle(0, gy + 6, SW, 700)
                ctx.clip()
                for i in range(5):
                    r = 30 + ((t - self.t_hit) * 180 + i * 55) % 300
                    ring(ctx, wx, gy + 130, r, YEL, af * (1 - r / 320) * 0.8, 4)
                ctx.restore()


class Irrtum(Scene):
    def setup(self):
        c = self.c
        self.t_hit = c.s(4) - 0.2
        self.flash(self.t_hit + 0.12, 1.0)

    def draw(self, ctx, t):
        c = self.c
        ground(ctx, 1120)
        ah = fade(t, c.s(0) - 0.4, None, 0.5)
        hl = house(ctx, 290, 1120, 300, 180, 130, ah)
        tip, path = draw_rod(ctx, hl, ah, 90, soil=0)
        house(ctx, 790, 1120, 300, 180, 130, ah)
        am = fade(t, c.s(0) - 0.1, c.s(3) - 0.1)
        if am > 0:
            sc = pop(prog(t, c.s(0) - 0.1, 0.5))
            label_card(ctx, [("„Zieht Blitze an?“", WHITE)], 540, 500, 76, am, sc, accent=RED)
            fx = prog(t, c.s(1) - 0.05, 0.5)
            if fx > 0:
                cross(ctx, 540, 500, 190, RED, am, 24, f=fx)
        ag = fade(t, c.w(2, "hoch") - 0.2)
        if ag > 0:
            fk = ease(prog(t, c.w(2, "hoch") - 0.2, 0.8))
            ay = hl["apex"][1]
            line(ctx, [(100, ay), (lerp(100, 980, fk), ay)], YEL, ag, 4, dash=[14, 10])
            badge(ctx, "gleich hoch", 540, ay - 50, 44, YEL, a=ag, scale=pop(prog(t, c.w(2, "hoch") - 0.2, 0.45)))
        rows = [(c.s(3) - 0.1, False, "verhindert keinen Blitz"), (c.s(4) - 0.1, True, "verhindert den Schaden")]
        for i, (t0, ok, s) in enumerate(rows):
            a = fade(t, t0)
            if a <= 0:
                continue
            y = 470 + i * 120
            s2 = pop(prog(t, t0, 0.4))
            fill_rrect(ctx, 120, y - 50, 840, 100, 50, (0, 0, 0), 0.6 * a)
            check_badge(ctx, 185, y, 32, a, s2, ok=ok)
            text(ctx, s, 245, y, 52, WHITE if ok else (1, 0.75, 0.72), a, align="l")
        if not hasattr(self, "bolt"):
            self.bolt = bolt_points(220, -20, tip[0], tip[1] - 16, seed=13, n=16, jit=40)
        strike(ctx, t, self.t_hit, self.bolt, w=8)
        af = fade(t, self.t_hit + 0.12, None, 0.1)
        if af > 0:
            flow(ctx, path, t, YEL, af, 7, f=ease(prog(t, self.t_hit + 0.12, 0.7)))


class Fazit(Scene):
    sky = 0.6

    def draw(self, ctx, t):
        c = self.c
        steps = [("Fangen", c.w(0, "Fangen")), ("Ableiten", c.w(0, "Ableiten")), ("Erden", c.w(0, "Erden"))]
        base = fade(t, c.s(0) - 0.5, None, 0.3)
        for i, (s, t0) in enumerate(steps):
            x, y = 300, 520 + i * 220
            aa = fade(t, t0 - 0.12)
            if aa < 1:
                ring(ctx, x, y, 95, WHITE, base * 0.25 * (1 - aa), 4)
            if aa <= 0:
                continue
            sc = pop(prog(t, t0 - 0.12, 0.45))
            circle(ctx, x, y, 95 * sc, (0.04, 0.05, 0.1), aa * 0.85)
            ring(ctx, x, y, 95 * sc, YEL, aa, 6)
            if i == 0:
                line(ctx, [(x, y + 50 * sc), (x, y - 15 * sc)], METAL, aa, 7)
                poly(ctx, [(x, y - 35 * sc), (x - 8, y - 13 * sc), (x + 8, y - 13 * sc)], METAL, aa)
                bolt_icon(ctx, x - 35 * sc, y - 45 * sc, 60 * sc, YEL, aa)
            elif i == 1:
                line(ctx, [(x - 25 * sc, y - 50 * sc), (x - 25 * sc, y + 50 * sc)], METAL, aa, 7)
                arrow(ctx, x + 20 * sc, y - 42 * sc, x + 20 * sc, y + 38 * sc, YEL, aa, 7, 20)
            else:
                ground_symbol(ctx, x, y + 8 * sc, 90 * sc, YEL, aa, 7)
            text(ctx, s, 440, y, 78, WHITE, aa, align="l", scale=1)
            if i < 2:
                arrow(ctx, x, y + 108, x, y + 122, WHITE, aa * 0.6, 4, 14)
        ac = fade(t, c.s(1) - 0.1)
        if ac > 0:
            sc = pop(prog(t, c.s(1) - 0.1, 0.5))
            fill_rrect(ctx, 540 - 380 * sc, 1180 - 60 * sc, 760 * sc, 120 * sc, 60 * sc, RED, ac)
            poly(ctx, [(240, 1150), (240, 1210), (290, 1180)], WHITE, ac * min(sc, 1))
            text(ctx, "Ganzes Video im Kanal", 575, 1180, 50, WHITE, ac, scale=sc)


SCENES = {"hook": Hook, "teile": Teile, "irrtum": Irrtum, "fazit": Fazit}

# ---------------- Kapitel-Fenster ----------------
CH = []
for i, ch in enumerate(T["chapters"]):
    a = 0.0 if i == 0 else (T["chapters"][i - 1]["end"] + ch["start"]) / 2
    CH.append({"meta": CHAPTERS[i], "t": ch, "a": a, "cue": Cue(ch)})
for i, c in enumerate(CH):
    c["b"] = CH[i + 1]["a"] if i + 1 < len(CH) else DUR + 1
    c["scene"] = SCENES[c["meta"]["id"]](c["cue"])

FLASHES = []
for c in CH:
    FLASHES += c["scene"].flashes
    if c["a"] > 0:
        FLASHES.append((c["a"], 0.35))


def flash_at(t):
    return min(1.0, sum(k * flash_env(t - t0) for t0, k in FLASHES))


# ---------------- Untertitel (groß, mittig) ----------------
def norm(w):
    return re.sub(r"[^\wäöüÄÖÜß.]", "", w).strip(".").lower()


def mark_keywords(words, keywords):
    toks = [norm(w) for w in words]
    hit = [False] * len(words)
    for kw in keywords:
        kt = [norm(x) for x in kw.split()]
        for i in range(len(toks) - len(kt) + 1):
            if all(toks[i + j] == k or (len(k) >= 4 and toks[i + j].startswith(k) and len(toks[i + j]) - len(k) <= 3)
                   for j, k in enumerate(kt)):
                for j in range(len(kt)):
                    hit[i + j] = True
    return hit


SUB_SIZE, SUB_MAXW, SUB_Y = 84, 840, 1370
_m = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 10, 10))
SPACE_W = text_w(_m, " ", SUB_SIZE)
CONJ = {"und", "oder", "dass", "damit", "statt", "aber", "denn", "wie", "ob", "nur"}


def wlen(w):
    return text_w(_m, w, SUB_SIZE)


def chunk_words(words, idx, mx=24):
    L = len(" ".join(words[j] for j in idx))
    if L <= mx or len(idx) < 3:
        return [idx]
    best, bi = 1e9, 1
    for i in range(1, len(idx)):
        left = len(" ".join(words[j] for j in idx[:i]))
        right = len(" ".join(words[j] for j in idx[i:]))
        cost = abs(left - right) * 0.6 + (0 if words[idx[i - 1]][-1] in ",:;?" else 12 if words[idx[i]].lower() in CONJ else 30)
        if min(left, right) < 8:
            cost += 200
        if cost < best:
            best, bi = cost, i
    return chunk_words(words, idx[:bi], mx) + chunk_words(words, idx[bi:], mx)


def split_lines(words):
    ws = [wlen(w) for w in words]
    if sum(ws) + SPACE_W * (len(words) - 1) <= SUB_MAXW or len(words) < 2:
        return [list(range(len(words)))]
    best, bi = 1e9, 1
    for i in range(1, len(words)):
        l1 = sum(ws[:i]) + SPACE_W * (i - 1)
        l2 = sum(ws[i:]) + SPACE_W * (len(words) - i - 1)
        if max(l1, l2) < best:
            best, bi = max(l1, l2), i
    return [list(range(bi)), list(range(bi, len(words)))]


SUBS = []
for ci, c in enumerate(CH):
    sents = c["t"]["sentences"]
    for si, s in enumerate(sents):
        words = [w["w"] for w in s["words"]]
        hit = mark_keywords(words, c["meta"]["keywords"])
        chunks = chunk_words(words, list(range(len(words))))
        nxt = sents[si + 1]["start"] if si + 1 < len(sents) else (
            T["chapters"][ci + 1]["start"] if ci + 1 < len(T["chapters"]) else DUR)
        for k, ch_ in enumerate(chunks):
            st = s["words"][ch_[0]]["s"] - 0.05
            en = s["words"][chunks[k + 1][0]]["s"] - 0.05 if k + 1 < len(chunks) else min(s["end"] + 0.4, nxt - 0.06)
            ww = [(words[j], hit[j]) for j in ch_]
            SUBS.append((st, en, ww, split_lines([w for w, _ in ww])))


def draw_subs(ctx, t):
    for st, en, ww, lines in SUBS:
        if st <= t < en:
            a = prog(t, st, 0.06) * (1 - prog(t, en - 0.05, 0.05))
            sc = 0.86 + 0.14 * pop(prog(t, st, 0.22))
            lh = SUB_SIZE * 1.2
            ctx.save()
            ctx.translate(540, SUB_Y)
            ctx.scale(sc, sc)
            ctx.translate(-540, -SUB_Y)
            base = SUB_Y - (len(lines) - 1) * lh / 2 + SUB_SIZE * 0.35
            placed = []
            set_font(ctx, SUB_SIZE)
            for li, ln in enumerate(lines):
                lw = sum(wlen(ww[j][0]) for j in ln) + SPACE_W * (len(ln) - 1)
                x = 540 - lw / 2
                for j in ln:
                    placed.append((x, base + li * lh, ww[j][0], ww[j][1]))
                    x += wlen(ww[j][0]) + SPACE_W
            for pss in (0, 1):
                for x, y, w, hl in placed:
                    ctx.new_path()
                    ctx.move_to(x, y)
                    ctx.text_path(w)
                    if pss == 0:
                        ctx.set_source_rgba(0, 0, 0, 0.92 * a)
                        ctx.set_line_width(16)
                        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
                        ctx.stroke()
                    else:
                        rgba(ctx, YEL if hl else WHITE, a)
                        ctx.fill()
            ctx.restore()
            break


# ---------------- Kopfzeile, Fortschritt, Kamera ----------------
def draw_header(ctx, t, c):
    a = fade(t, c["a"] + 0.1, c["b"] - 0.05, 0.3, 0.3)
    if a <= 0:
        return
    slide = (1 - ease(prog(t, c["a"] + 0.1, 0.45))) * -60
    m = c["meta"]
    if m["label"] is None:  # Hook: großer Titel
        set_font(ctx, 112)
        for i, (s, col) in enumerate((("ZIEHT ER", WHITE), ("BLITZE AN?", YEL))):
            text(ctx, s, 540, 240 + i * 125 + slide, 112, col, a, stroke=(0, 0, 0), sw=18)
        return
    lab = f"{m['label']}  |  {m['title'].upper()}"
    w = text_w(ctx, lab, 44) + 110
    fill_rrect(ctx, 540 - w / 2, 230 + slide - 40, w, 80, 40, (0.02, 0.03, 0.06), 0.75 * a)
    bolt_icon(ctx, 540 - w / 2 + 45, 230 + slide, 40, YEL, a)
    text(ctx, lab, 540 + 25, 230 + slide, 44, WHITE, a)


def camera(ctx, t, c):
    i = CH.index(c)
    p = ease_io(clamp((t - c["a"]) / max(c["b"] - c["a"], 1.0)))
    zoom = 1.0 + 0.05 * p + (0.08 * (1 - ease(prog(t, c["a"] - 0.1, 0.7))) if c["a"] > 0 else 0)
    dx = (1 if i % 2 == 0 else -1) * 18 * p
    ctx.translate(540 + dx, 900)
    ctx.scale(zoom, zoom)
    ctx.translate(-540, -900)


WX = Weather(seed=9)
_BG = None


def render_frame(ctx, t):
    global _BG
    if _BG is None:
        _BG = cairo.ImageSurface(cairo.FORMAT_ARGB32, SW, SH)
        WX.sky(cairo.Context(_BG))
    ctx.set_source_surface(_BG)
    ctx.paint()
    fl = flash_at(t)
    act = [(c, fade(t, c["a"] - 0.1, c["b"] + 0.1, 0.4, 0.4) if c["a"] > 0 else fade(t, -1, c["b"] + 0.1, 0.1, 0.4))
           for c in CH if c["a"] - 0.35 <= t < c["b"] + 0.35]
    act = [(c, a) for c, a in act if a > 0]
    sky = min(sum(c["scene"].sky * a for c, a in act), 1) if act else 1
    WX.draw_clouds(ctx, t, fl, sky)
    WX.draw_rain(ctx, t, 1.0)
    for c, a in act:
        ctx.save()
        camera(ctx, t, c)
        ctx.push_group()
        c["scene"].draw(ctx, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
        ctx.restore()
    if fl > 0.01:
        ctx.set_source_rgba(0.85, 0.9, 1.0, 0.36 * fl)
        ctx.paint()
    g = cairo.RadialGradient(540, 960, 600, 540, 960, 1250)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.5)
    ctx.set_source(g)
    ctx.paint()
    for c in CH:
        draw_header(ctx, t, c)
    draw_subs(ctx, t)
    ctx.rectangle(0, 0, SW, 8)
    ctx.set_source_rgba(1, 1, 1, 0.15)
    ctx.fill()
    ctx.rectangle(0, 0, SW * clamp(t / DUR), 8)
    rgba(ctx, YEL)
    ctx.fill()


def worker(f0, f1, path):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SW, SH)
    ctx = cairo.Context(surf)
    p = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra",
                          "-s", f"{SW}x{SH}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                          "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high", "-g", "60", "-threads", "2",
                          str(path)], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        ctx.save()
        render_frame(ctx, f / FPS)
        ctx.restore()
        surf.flush()
        p.stdin.write(surf.get_data())
    p.stdin.close()
    p.wait()


def main():
    if "--preview" in sys.argv:
        outd = BUILD / "preview"
        outd.mkdir(exist_ok=True)
        for x in sys.argv[sys.argv.index("--preview") + 1:]:
            surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SW, SH)
            render_frame(cairo.Context(surf), float(x))
            surf.write_to_png(str(outd / f"t{float(x):06.2f}.png"))
        return
    n = 4
    b = [round(NFRAMES * i / n) for i in range(n + 1)]
    segs = [BUILD / f"seg{i}.mp4" for i in range(n)]
    t0 = time.time()
    ps = [Process(target=worker, args=(b[i], b[i + 1], segs[i])) for i in range(n)]
    for p in ps:
        p.start()
    for p in ps:
        p.join()
    assert all(p.exitcode == 0 for p in ps)
    (BUILD / "segs.txt").write_text("".join(f"file '{s}'\n" for s in segs))
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", str(BUILD / "segs.txt"), "-i", str(BUILD / "sprache.mp3"), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                    "-t", f"{NFRAMES / FPS:.3f}", "-movflags", "+faststart", str(FINAL)], check=True)
    print(f"Fertig in {time.time() - t0:.0f} s: {FINAL}")


if __name__ == "__main__":
    main()
