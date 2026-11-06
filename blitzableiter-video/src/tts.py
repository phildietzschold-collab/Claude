# -*- coding: utf-8 -*-
"""Schritt 1: Sprachaufnahme mit Piper (lokal, offline) erzeugen.

Erzeugt build/voice.wav, ../blitzableiter_sprache.mp3 und build/tts_timing.json
(Satz- und Wortzeiten aus den Phonem-Alignments der Stimme).
"""
import json
import sys
import types
import unicodedata
from pathlib import Path

import numpy as np

import piper.phonemize_espeak as pe
from piper import PiperVoice, SynthesisConfig

from content import CHAPTERS, spoken


ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
BUILD.mkdir(exist_ok=True)
MODEL = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "voices" / "de_DE-thorsten-high.onnx")

LENGTH_SCALE = float(sys.argv[2]) if len(sys.argv) > 2 else 1.1
LEAD_IN = 0.5          # Stille am Anfang
SENT_GAP = 0.45        # Pause zwischen Sätzen
CHAPTER_GAP = 1.10     # Pause zwischen Kapiteln
TAIL = 12.0            # Stille am Ende (Endkarte)

voice = PiperVoice.load(MODEL, include_alignments=True)
if "\u0327" not in voice.config.phoneme_id_map:
    # Ältere Stimmen erwarten zusammengesetzte Zeichen (z. B. "ç" für den ich-Laut).
    pe.unicodedata = types.SimpleNamespace(normalize=lambda form, s: unicodedata.normalize("NFC", s))
SR = voice.config.sample_rate
cfg = SynthesisConfig(length_scale=LENGTH_SCALE, normalize_audio=False, noise_scale=0.6, noise_w_scale=0.8)


def trim(audio, thr=0.01):
    idx = np.where(np.abs(audio) > thr)[0]
    if len(idx) == 0:
        return audio, 0
    a, b = max(idx[0] - int(0.02 * SR), 0), min(idx[-1] + int(0.06 * SR), len(audio))
    return audio[a:b], a


def synth_sentence(text):
    audio_parts, groups = [], []  # groups: (start_sample, end_sample) je Wort
    offset = 0
    for chunk in voice.synthesize(text, cfg, include_alignments=True):
        a = chunk.audio_float_array
        if chunk.phoneme_alignments:
            pos = offset
            cur = None
            for al in chunk.phoneme_alignments:
                p = al.phoneme
                is_sound = p not in (" ", "^", "$", "_") and not unicodedata.category(p[0]).startswith("P") \
                    and p not in ("ˈ", "ˌ")
                if p == " ":
                    if cur:
                        groups.append(cur)
                        cur = None
                elif is_sound:
                    if cur is None:
                        cur = [pos, pos + al.num_samples]
                    else:
                        cur[1] = pos + al.num_samples
                pos += al.num_samples
            if cur:
                groups.append(cur)
        audio_parts.append(a)
        offset += len(a)
    audio = np.concatenate(audio_parts)
    audio, cut = trim(audio)
    groups = [(max(g0 - cut, 0) / SR, max(g1 - cut, 0) / SR) for g0, g1 in groups]
    return audio, groups


out = [np.zeros(int(LEAD_IN * SR), np.float32)]
t = LEAD_IN
timing = []
mismatch = 0
for ci, ch in enumerate(CHAPTERS):
    if ci > 0:
        out.append(np.zeros(int(CHAPTER_GAP * SR), np.float32))
        t += CHAPTER_GAP
    ch_t = {"id": ch["id"], "start": t, "sentences": []}
    for si, (disp, ov) in enumerate(ch["sentences"]):
        if si > 0:
            out.append(np.zeros(int(SENT_GAP * SR), np.float32))
            t += SENT_GAP
        text = spoken(disp, ov)
        audio, groups = synth_sentence(text)
        dur = len(audio) / SR
        words = disp.split()
        if len(groups) == len(words):
            wt = [[t + a, t + b] for a, b in groups]
            src = "alignment"
        else:
            mismatch += 1
            # Fallback: proportional nach Zeichenanzahl
            total = sum(len(w) + 1 for w in words)
            acc, wt = 0, []
            for w in words:
                s0 = t + dur * acc / total
                acc += len(w) + 1
                wt.append([s0, t + dur * acc / total])
            src = "proportional"
        ch_t["sentences"].append({"text": disp, "spoken": text, "start": t, "end": t + dur,
                                  "words": [{"w": w, "s": a, "e": b} for w, (a, b) in zip(words, wt)],
                                  "word_timing": src})
        out.append(audio.astype(np.float32))
        t += dur
    ch_t["end"] = t
    timing.append(ch_t)

out.append(np.zeros(int(TAIL * SR), np.float32))
t += TAIL
audio = np.concatenate(out)
audio = audio / max(np.max(np.abs(audio)), 1e-6) * 0.89

import wave
with wave.open(str(BUILD / "voice.wav"), "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((audio * 32767).astype(np.int16).tobytes())

json.dump({"sample_rate": SR, "duration": t, "chapters": timing}, open(BUILD / "tts_timing.json", "w"),
          ensure_ascii=False, indent=1)
n = sum(len(c["sentences"]) for c in timing)
print(f"Dauer: {t:.1f} s ({t/60:.2f} min), Sätze: {n}, Wort-Fallback: {mismatch}")
