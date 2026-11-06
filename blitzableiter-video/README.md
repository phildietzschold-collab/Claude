# Wie funktioniert ein Blitzableiter? – Erklärvideo

| Datei | Inhalt |
|---|---|
| `Wie_funktioniert_ein_Blitzableiter.mp4` | fertiges Video, 1920×1080, 30 fps, H.264 + AAC, Ton = Stimme + Regen/Donner + Musik + Effekte (alles selbst erzeugt) |
| `Sprachaufnahme.mp3` | reine Sprachspur (Piper TTS, Stimme „Thorsten high“, CC0, lokal erzeugt) |
| `Thumbnail.png` | YouTube-Thumbnail 1280×720 |
| `Untertitel.srt` | Untertitel als Datei (z. B. zum Hochladen bei YouTube) |
| `src/` | Pipeline-Skripte |
| `voices/` | Stimm-Konfiguration; Modell `de_DE-thorsten-high.onnx` von huggingface.co/rhasspy/piper-voices laden |

## Pipeline neu bauen

```bash
cd src
python3 tts.py        # 1. Sprache erzeugen  -> build/voice.wav + tts_timing.json
ffmpeg -y -i ../build/voice.wav -af "highpass=f=70,aresample=44100:resampler=soxr,loudnorm=I=-16:TP=-1.5:LRA=11" \
       -ac 1 -c:a libmp3lame -b:a 192k ../build/sprache.mp3
python3 align.py      # 2. Pausen + Satzzeiten aus der MP3 -> build/timing.json
python3 render.py     # 3.–5. Video rendern (nur Stimme)
./mix_audio.sh        # 6. Atmo, Musik und Soundeffekte (alles synthetisch) unter die Stimme mischen
python3 thumbnail.py  # Thumbnail
python3 render.py --preview 12.5 40   # nur Einzelbilder (build/preview/)
```

**Eigene MP3 (z. B. TTSMaker):** als `build/sprache.mp3` ablegen und dann `python3 align.py` und `python3 render.py` laufen lassen.
`align.py` findet die Satzgrenzen allein über die Pausen in der MP3; Wortzeiten werden dann innerhalb jedes Satzes anteilig geschätzt.

Benötigt: `pip install piper-tts onnx pycairo scipy`, ffmpeg, Schrift „Inter“.
