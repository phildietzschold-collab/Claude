#!/bin/bash
# Stimme + Atmo (Regen/Donner) + Musik + Soundeffekte mischen und ins fertige Video setzen.
# Atmo und Musik werden automatisch leiser, sobald gesprochen wird (Sidechain-Ducking).
set -e
cd "$(dirname "$0")"
python3 sfx_events.py
python3 ambience.py
cd ..
B=${BUILD:-build}
VIDEO=${VIDEO:-Wie_funktioniert_ein_Blitzableiter.mp4}
ffmpeg -hide_banner -loglevel error -y \
 -i $B/sprache.mp3 -i $B/atmo.wav -i $B/music.wav -i $B/sfx.wav -filter_complex \
 "[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0,asplit=2[v][sc];\
  [1:a]volume=-3dB[atmo];[2:a]volume=0.11[mus];[atmo][mus]amix=inputs=2:normalize=0[bed0];\
  [bed0][sc]sidechaincompress=threshold=0.015:ratio=8:attack=15:release=450:makeup=1[bed];\
  [3:a]volume=0.22[fx];\
  [v][bed][fx]amix=inputs=3:normalize=0:duration=first,loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000" \
 -c:a pcm_s16le $B/mix.wav
ffmpeg -hide_banner -loglevel error -y -i "$VIDEO" -i $B/mix.wav -map 0:v -map 1:a \
 -c:v copy -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart $B/with_mix.mp4
mv $B/with_mix.mp4 "$VIDEO"
echo "Fertig: Video mit Stimme, Atmo, Musik und Effekten"
