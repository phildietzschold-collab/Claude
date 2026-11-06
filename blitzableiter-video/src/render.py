# -*- coding: utf-8 -*-
"""Schritt 3-5: Video rendern (pycairo -> ffmpeg, H.264 + AAC).

  python3 render.py                 # komplettes Video
  python3 render.py --preview 12.5 40 ...   # Einzelbilder als PNG nach build/preview/
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

from content import CHAPTERS
from gfx import *  # noqa: F401,F403
from scenes import SCENES, Cue

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
OUT_DIR = ROOT
AUDIO = BUILD / "sprache.mp3"
FINAL = OUT_DIR / "Wie_funktioniert_ein_Blitzableiter.mp4"

T = json.load(open(BUILD / "timing.json"))
DUR = T["duration"]
NFRAMES = int(math.ceil(DUR * FPS))

# ---------------- Kapitel-Fenster ----------------
CH = []
for i, ch in enumerate(T["chapters"]):
    meta = CHAPTERS[i]
    a = 0.0 if i == 0 else (T["chapters"][i - 1]["end"] + ch["start"]) / 2
    CH.append({"meta": meta, "t": ch, "a": a, "cue": Cue(ch)})
for i, c in enumerate(CH):
    c["b"] = CH[i + 1]["a"] if i + 1 < len(CH) else DUR + 1
    c["scene"] = SCENES[c["meta"]["id"]](c["cue"])

# ---------------- Blitz-Flashes ----------------
FLASHES = []
for c in CH:
    FLASHES += c["scene"].flashes
    if c["a"] > 0:
        FLASHES.append((c["a"], 0.35))  # Übergangsblitz zwischen Kapiteln
rnd = random.Random(12)
tt = 6.0
while tt < DUR - 8:
    if all(abs(tt - f) > 2.5 for f, _ in FLASHES):
        FLASHES.append((tt, rnd.uniform(0.15, 0.28)))
    tt += rnd.uniform(8, 13)


def flash_at(t):
    return min(1.0, sum(k * flash_env(t - t0) for t0, k in FLASHES))


# ---------------- Untertitel ----------------
def norm(w):
    return re.sub(r"[^\wäöüÄÖÜß.]", "", w).strip(".").lower()


def mark_keywords(words, keywords):
    toks = [norm(w) for w in words]
    hit = [False] * len(words)
    for kw in keywords:
        kt = [norm(x) for x in kw.split()]
        for i in range(len(toks) - len(kt) + 1):
            ok = True
            for j, k in enumerate(kt):
                tok = toks[i + j]
                if not (tok == k or (len(k) >= 4 and tok.startswith(k) and len(tok) - len(k) <= 3)):
                    ok = False
                    break
            if ok:
                for j in range(len(kt)):
                    hit[i + j] = True
    return hit


SUB_SIZE = 62
SUB_MAXW = 1640
_meas = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 10, 10))
SPACE_W = text_w(_meas, " ", SUB_SIZE)


def wlen(w):
    return text_w(_meas, w, SUB_SIZE)


def split_lines(words):
    ws = [wlen(w) for w in words]
    total = sum(ws) + SPACE_W * (len(words) - 1)
    if total <= SUB_MAXW * 0.62 or len(words) < 3:
        return [list(range(len(words)))]
    best, bi = 1e9, 1
    for i in range(1, len(words)):
        l1 = sum(ws[:i]) + SPACE_W * (i - 1)
        l2 = sum(ws[i:]) + SPACE_W * (len(words) - i - 1)
        cost = max(l1, l2) + (0 if words[i - 1][-1] in ",:;" else 110 if words[i].lower() in CONJ else 260)
        if max(l1, l2) > SUB_MAXW:
            cost += 5000
        if cost < best:
            best, bi = cost, i
    return [list(range(bi)), list(range(bi, len(words)))]


CONJ = {"und", "oder", "dass", "damit", "statt", "aber", "denn", "wie", "ob", "weil", "wenn", "zum", "in", "an"}
CHUNK_MAX = 70


def chunk_words(words, idx):
    """Satz rekursiv an natürlichen Stellen (Komma, Bindewort) in Untertitel-Blöcke teilen."""
    L = len(" ".join(words[j] for j in idx))
    if L <= CHUNK_MAX or len(idx) < 4:
        return [idx]
    best, bi = 1e9, 1
    for i in range(1, len(idx)):
        left = len(" ".join(words[j] for j in idx[:i]))
        right = len(" ".join(words[j] for j in idx[i:]))
        prev, nxt = words[idx[i - 1]], words[idx[i]]
        cost = abs(left - right) * 0.6
        cost += 0 if prev[-1] in ",:;" else 35 if nxt.lower() in CONJ else 90
        if min(left, right) < 16:
            cost += 300
        if cost < best:
            best, bi = cost, i
    return chunk_words(words, idx[:bi]) + chunk_words(words, idx[bi:])


SUBS = []  # (start, end, [(wort, gelb)], lines)
for ci, c in enumerate(CH):
    kws = c["meta"]["keywords"]
    sents = c["t"]["sentences"]
    for si, s in enumerate(sents):
        words = [w["w"] for w in s["words"]]
        hit = mark_keywords(words, kws)
        chunks = chunk_words(words, list(range(len(words))))
        nxt = sents[si + 1]["start"] if si + 1 < len(sents) else (
            T["chapters"][ci + 1]["start"] if ci + 1 < len(T["chapters"]) else DUR)
        for k, ch_ in enumerate(chunks):
            st = s["words"][ch_[0]]["s"] - 0.06
            if k + 1 < len(chunks):
                en = s["words"][chunks[k + 1][0]]["s"] - 0.06
            else:
                en = min(s["end"] + 0.5, nxt - 0.08)
            ww = [(words[j], hit[j]) for j in ch_]
            lines = split_lines([w for w, _ in ww])
            SUBS.append((st, en, ww, lines))


def fmt_srt(x):
    h, r = divmod(x, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


def write_srt(path):
    with open(path, "w", encoding="utf-8") as f:
        for i, (st, en, ww, lines) in enumerate(SUBS, 1):
            txt = "\n".join(" ".join(ww[j][0] for j in ln) for ln in lines)
            f.write(f"{i}\n{fmt_srt(max(st, 0))} --> {fmt_srt(en)}\n{txt}\n\n")


def draw_subs(ctx, t):
    for st, en, ww, lines in SUBS:
        if st <= t < en:
            a = prog(t, st, 0.08) * (1 - prog(t, en - 0.06, 0.06))
            rise = (1 - ease(prog(t, st, 0.15))) * 10
            lh = SUB_SIZE * 1.22
            base = 1012 - (len(lines) - 1) * lh + rise
            set_font(ctx, SUB_SIZE)
            fe = ctx.font_extents()
            placed = []
            for li, ln in enumerate(lines):
                lw = sum(wlen(ww[j][0]) for j in ln) + SPACE_W * (len(ln) - 1)
                x = 960 - lw / 2
                y = base + li * lh
                for j in ln:
                    placed.append((x, y, ww[j][0], ww[j][1]))
                    x += wlen(ww[j][0]) + SPACE_W
            # Kontur zuerst, dann Füllung
            for x, y, w, _ in placed:
                ctx.new_path()
                ctx.move_to(x, y)
                ctx.text_path(w)
                ctx.set_source_rgba(0, 0, 0, 0.9 * a)
                ctx.set_line_width(11)
                ctx.set_line_join(cairo.LINE_JOIN_ROUND)
                ctx.stroke()
            for x, y, w, hl in placed:
                ctx.new_path()
                ctx.move_to(x, y)
                ctx.text_path(w)
                rgba(ctx, YEL if hl else WHITE, a)
                ctx.fill()
            break


# ---------------- Kapitelzeile & Fortschritt ----------------
def draw_chapter_line(ctx, t, c):
    a = fade(t, c["a"] + 0.15, c["b"] - 0.05, 0.4, 0.35)
    if a <= 0:
        return
    slide = (1 - ease(prog(t, c["a"] + 0.15, 0.5))) * -70
    lab, title = c["meta"]["label"], c["meta"]["title"]
    if lab is None:
        lab, title = "Erklärt", "Wie funktioniert ein Blitzableiter?"
    lab = lab.upper()
    x, y, h = 56, 40 + slide, 62
    w1 = text_w(ctx, lab, 26)
    w2 = text_w(ctx, title, 32)
    w = 28 + w1 + 26 + w2 + 30
    fill_rrect(ctx, x, y, w, h, h / 2, (0.02, 0.03, 0.06), 0.72 * a)
    bolt_icon(ctx, x + 32, y + h / 2, 34, YEL, a)
    text(ctx, lab, x + 54, y + h / 2, 26, YEL, a, align="l")
    line(ctx, [(x + 54 + w1 + 14, y + 16), (x + 54 + w1 + 14, y + h - 16)], WHITE, a * 0.35, 2)
    text(ctx, title, x + 54 + w1 + 30, y + h / 2, 32, WHITE, a, align="l")


def draw_progress(ctx, t):
    y, h = H - 7, 7
    ctx.rectangle(0, y, W, h)
    ctx.set_source_rgba(1, 1, 1, 0.14)
    ctx.fill()
    ctx.rectangle(0, y, W * clamp(t / DUR), h)
    rgba(ctx, YEL, 0.95)
    ctx.fill()
    for c in CH[1:]:
        x = W * c["t"]["start"] / DUR
        ctx.rectangle(x - 1.5, y, 3, h)
        ctx.set_source_rgba(0.02, 0.03, 0.06, 0.9)
        ctx.fill()


# ---------------- Frame ----------------
WX = Weather()
_BG = None
_VIG = None


def statics():
    global _BG, _VIG
    if _BG is None:
        _BG = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        WX.sky(cairo.Context(_BG))
        _VIG = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        vc = cairo.Context(_VIG)
        g = cairo.RadialGradient(W / 2, H / 2, H * 0.45, W / 2, H / 2, H * 1.05)
        g.add_color_stop_rgba(0, 0, 0, 0, 0)
        g.add_color_stop_rgba(1, 0, 0, 0, 0.55)
        vc.set_source(g)
        vc.paint()


def render_frame(ctx, t):
    statics()
    ctx.set_source_surface(_BG)
    ctx.paint()
    fl = flash_at(t)
    # aktive Szenen (mit Überblendung)
    act = []
    for c in CH:
        if c["a"] - 0.45 <= t < c["b"] + 0.45:
            a = fade(t, c["a"] - 0.1, c["b"] + 0.1, 0.55, 0.55) if c["a"] > 0 else fade(t, -1, c["b"] + 0.1, 0.1, 0.55)
            if a > 0:
                act.append((c, a))
    sky = sum(c["scene"].sky * a for c, a in act) if act else 1.0
    rain = sum(c["scene"].rain * a for c, a in act) if act else 1.0
    WX.draw_clouds(ctx, t, fl, min(sky, 1))
    WX.draw_rain(ctx, t, min(rain, 1))
    for c, a in act:
        if a >= 0.999:
            c["scene"].draw(ctx, t)
        else:
            ctx.push_group()
            c["scene"].draw(ctx, t)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(a)
    if fl > 0.01:
        ctx.set_source_rgba(0.85, 0.9, 1.0, 0.36 * fl)
        ctx.paint()
    ctx.set_source_surface(_VIG)
    ctx.paint()
    for c in CH:
        draw_chapter_line(ctx, t, c)
    draw_subs(ctx, t)
    draw_progress(ctx, t)


def new_surface():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    return s, cairo.Context(s)


def worker(idx, f0, f1, path):
    surf, ctx = new_surface()
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-g", "60", "-threads", "2", str(path)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for f in range(f0, f1):
        ctx.save()
        render_frame(ctx, f / FPS)
        ctx.restore()
        surf.flush()
        p.stdin.write(surf.get_data())
        if idx == 0 and (f - f0) % 300 == 0 and f > f0:
            el = time.time() - t0
            print(f"  Segment 0: {f - f0}/{f1 - f0} Frames, {el / (f - f0) * 1000:.0f} ms/Frame", flush=True)
    p.stdin.close()
    p.wait()


def main():
    if "--preview" in sys.argv:
        outd = BUILD / "preview"
        outd.mkdir(exist_ok=True)
        for x in sys.argv[sys.argv.index("--preview") + 1:]:
            surf, ctx = new_surface()
            render_frame(ctx, float(x))
            surf.write_to_png(str(outd / f"t{float(x):07.2f}.png"))
        return
    write_srt(OUT_DIR / "Untertitel.srt")
    nseg = int(os.environ.get("SEGMENTS", "4"))
    bounds = [round(NFRAMES * i / nseg) for i in range(nseg + 1)]
    segs = [BUILD / f"seg{i}.mp4" for i in range(nseg)]
    print(f"Rendere {NFRAMES} Frames ({DUR:.1f} s) in {nseg} Segmenten ...", flush=True)
    t0 = time.time()
    ps = [Process(target=worker, args=(i, bounds[i], bounds[i + 1], segs[i])) for i in range(nseg)]
    for p in ps:
        p.start()
    for p in ps:
        p.join()
    assert all(p.exitcode == 0 for p in ps), "Render-Fehler"
    print(f"Frames fertig in {time.time() - t0:.0f} s", flush=True)
    lst = BUILD / "segs.txt"
    lst.write_text("".join(f"file '{s}'\n" for s in segs))
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-i", str(AUDIO), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-ac", "2", "-t", f"{NFRAMES / FPS:.3f}", "-movflags", "+faststart", str(FINAL)],
                   check=True)
    print("Fertig:", FINAL)


if __name__ == "__main__":
    main()
