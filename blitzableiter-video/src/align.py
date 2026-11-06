# -*- coding: utf-8 -*-
"""Schritt 2: Pausen und Satzzeiten aus der MP3 ermitteln.

Funktioniert auch mit einer fremden MP3 (z. B. aus TTSMaker):
  python3 align.py pfad/zur/sprache.mp3
1. ffmpeg silencedetect findet alle Pausen.
2. Dynamische Programmierung wählt genau die Pausen als Satzgrenzen, bei denen die
   Satzlängen am besten zur erwarteten Länge passen (aus TTS-Zeiten, sonst Zeichenanzahl).
3. Wortzeiten: aus den Piper-Alignments (verschoben auf die erkannte Satzzeit) oder
   proportional innerhalb des Satzes.
Schreibt build/timing.json und die Untertitel als SRT.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import importlib
import os
CHAPTERS = importlib.import_module(os.environ.get("CONTENT", "content")).CHAPTERS

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / os.environ.get("BUILD", "build")
MP3 = Path(sys.argv[1]) if len(sys.argv) > 1 else BUILD / "sprache.mp3"


def silences(path, noise="-40dB", d=0.22):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", f"silencedetect=noise={noise}:d={d}",
                        "-f", "null", "-"], capture_output=True, text=True)
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    dur = float(re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr).group(3)) + \
        60 * int(re.search(r"Duration: (\d+):(\d+)", r.stderr).group(2)) + \
        3600 * int(re.search(r"Duration: (\d+):", r.stderr).group(1))
    if len(en) < len(st):
        en.append(dur)
    return list(zip(st, en)), dur


sil, total = silences(MP3, d=float(os.environ.get("SIL_D", 0.22)))
# Sprachbereich: nach der ersten Stille bis vor die letzte
speech_start = sil[0][1] if sil and sil[0][0] < 0.05 else 0.0
speech_end = sil[-1][0] if sil and sil[-1][1] >= total - 0.05 else total
inner = [s for s in sil if s[0] > speech_start + 0.05 and s[1] < speech_end - 0.05]

sents = [(ci, si, disp) for ci, ch in enumerate(CHAPTERS) for si, (disp, _) in enumerate(ch["sentences"])]
N = len(sents)

prior = None
tts_file = BUILD / "tts_timing.json"
if tts_file.exists() and MP3.resolve() == (BUILD / "sprache.mp3").resolve() and \
        abs(json.load(open(tts_file))["duration"] - total) < 0.3:
    prior = json.load(open(tts_file))
    flat_prior = [s for c in prior["chapters"] for s in c["sentences"]]
    exp = [s["end"] - s["start"] for s in flat_prior]
else:
    flat_prior = None
    chars = [len(d) for _, _, d in sents]
    speech_total = (speech_end - speech_start) - sum(e - s for s, e in inner) * 0.7
    exp = [c / sum(chars) * speech_total for c in chars]

# Kandidaten-Grenzen: Pausen (Satzende = Pausenbeginn, nächster Satzanfang = Pausenende)
B = [(speech_start, speech_start)] + [(s, e) for s, e in inner] + [(speech_end, speech_end)]
M = len(B)
INF = float("inf")
# dp[k][j]: beste Kosten, wenn Satz k an Grenze j endet
dp = [[INF] * M for _ in range(N + 1)]
bk = [[-1] * M for _ in range(N + 1)]
dp[0][0] = 0.0
for k in range(1, N + 1):
    for j in range(1, M):
        best, arg = INF, -1
        for i in range(max(0, j - 12), j):
            if dp[k - 1][i] == INF:
                continue
            d = B[j][0] - B[i][1]
            if d <= 0.15:
                continue
            # Abweichung von erwarteter Länge + Belohnung für lange Pausen als Grenze
            c = dp[k - 1][i] + ((d - exp[k - 1]) / max(exp[k - 1], 0.6)) ** 2
            if j < M - 1:
                c -= 0.15 * min(B[j][1] - B[j][0], 1.5)
            if c < best:
                best, arg = c, i
        dp[k][j], bk[k][j] = best, arg
assert dp[N][M - 1] < INF, "Keine passende Satzaufteilung gefunden"
path, j = [], M - 1
for k in range(N, 0, -1):
    i = bk[k][j]
    path.append((B[i][1], B[j][0]))
    j = i
path.reverse()

out = {"duration": total, "source": str(MP3.name), "chapters": []}
dev = []
for (ci, si, disp), (s0, s1), k in zip(sents, path, range(N)):
    if si == 0:
        out["chapters"].append({"id": CHAPTERS[ci]["id"], "sentences": []})
    words = disp.split()
    if flat_prior:
        p = flat_prior[k]
        dev.append(abs(p["start"] - s0))
        shift = s0 - p["start"]
        scale = (s1 - s0) / max(p["end"] - p["start"], 1e-3)
        wt = [(s0 + (w["s"] - p["start"]) * scale, s0 + (w["e"] - p["start"]) * scale) for w in p["words"]]
    else:
        tot = sum(len(w) + 1 for w in words)
        acc, wt = 0, []
        for w in words:
            a = s0 + (s1 - s0) * acc / tot
            acc += len(w) + 1
            wt.append((a, s0 + (s1 - s0) * acc / tot))
    out["chapters"][-1]["sentences"].append(
        {"text": disp, "start": s0, "end": s1, "words": [{"w": w, "s": a, "e": b} for w, (a, b) in zip(words, wt)]})
for ch in out["chapters"]:
    ch["start"] = ch["sentences"][0]["start"]
    ch["end"] = ch["sentences"][-1]["end"]

json.dump(out, open(BUILD / "timing.json", "w"), ensure_ascii=False, indent=1)
print(f"MP3: {total:.2f} s | Pausen gefunden: {len(sil)} | Sätze: {N}")
if dev:
    print(f"Abweichung erkannte vs. TTS-Satzanfänge: max {max(dev)*1000:.0f} ms, Mittel {sum(dev)/len(dev)*1000:.0f} ms")
