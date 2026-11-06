# -*- coding: utf-8 -*-
"""Gewitter-Atmo (Regen + Donner) komplett synthetisch erzeugen.

Donner sitzt auf denselben Blitz-Zeitpunkten wie im Bild (render.FLASHES).
Schreibt build/atmo.wav (48 kHz, Stereo). Gemischt wird in mix_audio.sh.
"""
import random
import wave
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfilt

import importlib
import os
render = importlib.import_module(os.environ.get("RENDER", "render"))  # render oder short; liefert FLASHES, DUR, CH

SR = 48000
N = int((render.DUR + 0.5) * SR)
rng = np.random.default_rng(7)
ROOT = Path(__file__).resolve().parent.parent


def filt(x, kind, f):
    return sosfilt(butter(4, f, kind, fs=SR, output="sos"), x)


def env_curve(points):
    """Hüllkurve aus (zeit, wert)-Paaren."""
    t = np.arange(N) / SR
    xs, ys = zip(*points)
    return np.interp(t, xs, ys)


# ---------- Regen ----------
def rain_channel():
    w = rng.standard_normal(N)
    hiss = filt(filt(w, "highpass", 900), "lowpass", 9000) * 0.55
    body = filt(filt(rng.standard_normal(N), "highpass", 250), "lowpass", 2500) * 0.35
    # einzelne Tropfen
    drops = np.zeros(N)
    pos = rng.integers(0, N - 400, size=int(render.DUR * 90))
    for p in pos:
        L = int(rng.integers(60, 240))
        drops[p:p + L] += rng.standard_normal(L) * np.exp(-np.arange(L) / (L / 5)) * rng.uniform(0.2, 1.0)
    drops = filt(drops, "highpass", 1500) * 0.5
    slow = 1 + 0.18 * np.sin(np.arange(N) / SR * 2 * np.pi * 0.07 + rng.uniform(0, 6))
    return (hiss + body + drops) * slow


rain = np.stack([rain_channel(), rain_channel()])
# Regenmenge folgt den Szenen (im Zimmer, Kapitel 6, gedämpft)
pts = []
for c in render.CH:
    amt = c["scene"].rain
    pts += [(c["a"] + 0.6, amt), (c["b"] - 0.6, amt)]
pts.sort()
rain_env = env_curve([(0, 0.0), (0.8, 1.0)] + [p for p in pts if p[0] > 0.8])
fade_out = env_curve([(0, 1), (render.DUR - 3.0, 1), (render.DUR, 0)])
ins_pts = []
for c in render.CH:
    v = 1.0 if c["scene"].rain < 0.5 else 0.0  # Szene spielt drinnen
    ins_pts += [(max(c["a"] + 0.6, 0.01), v), (c["b"] - 0.6, v)]
inside = env_curve([(0, 0.0)] + sorted(ins_pts))
muffled = np.stack([filt(ch, "lowpass", 900) for ch in rain])
rain = rain * (1 - inside) + muffled * inside * 2.2
rain *= (0.35 + 0.65 * rain_env) * fade_out


# ---------- Donner ----------
def thunder(strength, close):
    dur = 2.5 + 2.0 * strength
    L = int(dur * SR)
    t = np.arange(L) / SR
    brown = np.cumsum(rng.standard_normal(L))
    brown = filt(brown - brown.mean(), "highpass", 25)
    rumble = filt(brown, "lowpass", 160 if close else 110)
    rumble /= np.max(np.abs(rumble)) + 1e-9
    # unregelmäßiges Grollen
    k = np.interp(t, np.linspace(0, dur, 14), rng.uniform(0.3, 1.0, 14))
    env = (1 - np.exp(-t / (0.04 if close else 0.35))) * np.exp(-t / (dur * 0.33)) * k
    out = rumble * env
    if close:
        cr = filt(rng.standard_normal(L), "highpass", 1200) * np.exp(-t / 0.06)
        cr += filt(rng.standard_normal(L), "bandpass", [300, 2500]) * np.exp(-t / 0.25) * 0.5
        out = out + cr * 0.45
    return out / (np.max(np.abs(out)) + 1e-9)


thun = np.zeros((2, N))
for t0, k in sorted(render.FLASHES):
    close = k >= 0.85
    delay = rng.uniform(0.05, 0.2) if close else rng.uniform(0.8, 1.8)
    start = int((t0 + delay) * SR)
    if start >= N:
        continue
    th = thunder(k, close) * (0.9 if close else 0.25 + 0.6 * k)
    pan = rng.uniform(-0.5, 0.5)
    L = min(len(th), N - start)
    thun[0, start:start + L] += th[:L] * (1 - pan) / 1.5
    thun[1, start:start + L] += th[:L] * (1 + pan) / 1.5

mix = rain * 0.10 + thun * 0.55
mix = np.tanh(mix * 1.2) / 1.2  # weiche Begrenzung
pcm = (np.clip(mix.T, -1, 1) * 32767).astype(np.int16)
with wave.open(str(render.BUILD / "atmo.wav"), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"Atmo: {N / SR:.1f} s, Donnerschläge: {len(render.FLASHES)}")


# =====================================================================
# Hintergrundmusik: ruhiger Synth-Pad in a-Moll (Am - F - C - G), selbst erzeugt
def note_hz(n):  # MIDI-Nummer -> Hz
    return 440.0 * 2 ** ((n - 69) / 12)


CHORDS = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]  # Am F C G
BAR = 6.0
music = np.zeros((2, N))
tt = np.arange(int((BAR + 3) * SR)) / SR
for k in range(int(render.DUR / BAR) + 1):
    notes = CHORDS[k % 4]
    s0 = int(k * BAR * SR)
    seg = np.zeros((2, len(tt)))
    env = np.clip(tt / 1.8, 0, 1) * np.clip((BAR + 3 - tt) / 3.0, 0, 1)
    for j, n in enumerate(list(notes) + [notes[0] - 12, notes[0] - 24]):
        f = note_hz(n)
        amp = 0.5 if n < 50 else 0.28
        for ch, det in ((0, -0.18), (1, 0.21)):
            ph = rng.uniform(0, 6.28)
            wv = np.sin(2 * np.pi * (f + det) * tt + ph) + 0.25 * np.sin(2 * np.pi * 2 * (f + det) * tt + ph) \
                + 0.08 * np.sin(2 * np.pi * 3 * (f - det) * tt)
            seg[ch] += wv * amp * env
    # leises Glocken-Arpeggio
    for i, n in enumerate((notes[0] + 12, notes[1] + 12, notes[2] + 12, notes[1] + 12)):
        on = i * BAR / 4
        a0 = int(on * SR)
        L = int(2.0 * SR)
        tb = np.arange(L) / SR
        bell = np.sin(2 * np.pi * note_hz(n) * tb) * np.exp(-tb * 2.2) * 0.12
        pan = 0.3 if i % 2 else -0.3
        seg[0, a0:a0 + L] += bell * (1 - pan)
        seg[1, a0:a0 + L] += bell * (1 + pan)
    e = min(s0 + seg.shape[1], N)
    music[:, s0:e] += seg[:, :e - s0]
music = np.stack([filt(ch, "lowpass", 1800) for ch in music])
# einfacher Raumhall (Feedback-Delay)
for d, g in ((0.23, 0.35), (0.37, 0.25), (0.53, 0.18)):
    D = int(d * SR)
    music[0, D:] += music[1, :-D] * g
    music[1, D:] += music[0, :-D] * g
music /= np.max(np.abs(music)) + 1e-9
music *= env_curve([(0, 0), (2.0, 1), (render.DUR - 4, 1), (render.DUR, 0)])

# =====================================================================
# Soundeffekte (Pop beim Erscheinen, Whoosh beim Kapitelwechsel)
import json
sfx = np.zeros((2, N))
for ev in json.load(open(render.BUILD / "sfx.json")):
    s0 = int(ev["t"] * SR)
    if ev["type"] == "pop":
        L = int(0.12 * SR)
        tb = np.arange(L) / SR
        f0 = rng.uniform(520, 700)
        freq = f0 * (1 + 0.6 * np.exp(-tb * 40))
        snd = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tb * 32) * 0.5
        snd += filt(rng.standard_normal(L), "highpass", 3000) * np.exp(-tb * 300) * 0.15
        pan = rng.uniform(-0.2, 0.2)
    else:
        L = int(0.9 * SR)
        tb = np.arange(L) / SR
        nz = rng.standard_normal(L)
        lo = filt(nz, "bandpass", [300, 1200])
        hi = filt(nz, "bandpass", [1200, 5000])
        sweep = np.clip(tb / 0.9, 0, 1)
        snd = (lo * (1 - sweep) + hi * sweep) * np.sin(np.pi * np.clip(tb / 0.9, 0, 1)) ** 2 * 0.6
        pan = 0.0
    e = min(s0 + L, N)
    if s0 < 0 or s0 >= N:
        continue
    sfx[0, s0:e] += snd[:e - s0] * (1 - pan)
    sfx[1, s0:e] += snd[:e - s0] * (1 + pan)


def write(name, x):
    pcm = (np.clip(x.T, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(render.BUILD / name), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


write("music.wav", music * 0.8)
write("sfx.wav", sfx / (np.max(np.abs(sfx)) + 1e-9) * 0.8)
print("Musik + Effekte geschrieben")
