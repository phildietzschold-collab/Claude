# -*- coding: utf-8 -*-
"""Zeitpunkte für Soundeffekte aus den Szenen ablesen.

Jede Pop-Animation im Bild (Element erscheint) erzeugt einen "pop",
jeder Kapitelwechsel einen "whoosh". Schreibt build/sfx.json.
"""
import json
import sys

import cairo

import importlib
import os

import scenes

render = importlib.import_module(os.environ.get("RENDER", "render"))
scenes = getattr(render, "SCENE_MODULE", scenes)  # Modul, in dem die Szenen definiert sind

events = []
last = {}
state = {"t": 0.0}
orig_pop = scenes.pop


def pop_rec(x):
    if 0 < x < 0.12:
        line = sys._getframe(1).f_lineno
        if state["t"] - last.get(line, -9) > 0.25:
            last[line] = state["t"]
            events.append({"t": round(state["t"], 3), "type": "pop"})
    return orig_pop(x)


scenes.pop = pop_rec

surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 48, 48)
ctx = cairo.Context(surf)
ctx.scale(48 / 1920, 48 / 1920)
for f in range(render.NFRAMES):
    t = f / render.FPS
    state["t"] = t
    for c in render.CH:
        if c["a"] - 0.45 <= t < c["b"] + 0.45:
            ctx.save()
            c["scene"].draw(ctx, t)
            ctx.restore()

for c in render.CH[1:]:
    events.append({"t": round(c["a"] - 0.15, 3), "type": "whoosh"})

# gleichzeitige Pops zusammenfassen
events.sort(key=lambda e: e["t"])
merged = []
for e in events:
    if merged and e["type"] == "pop" and merged[-1]["type"] == "pop" and e["t"] - merged[-1]["t"] < 0.12:
        continue
    merged.append(e)
json.dump(merged, open(render.BUILD / "sfx.json", "w"), indent=0)
print(f"Soundeffekte: {sum(e['type'] == 'pop' for e in merged)} Pops, {sum(e['type'] == 'whoosh' for e in merged)} Whooshes")
