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

import render  # liefert FLASHES, DUR, CH

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
with wave.open(str(ROOT / "build" / "atmo.wav"), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"Atmo: {N / SR:.1f} s, Donnerschläge: {len(render.FLASHES)}")
