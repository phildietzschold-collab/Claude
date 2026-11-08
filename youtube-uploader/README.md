# YouTube-Uploader

Lädt Videos mit **Titel, Beschreibung, Tags, Sichtbarkeit, geplantem Termin, Thumbnail und Playlist** auf deinen YouTube-Kanal. Dafür nutzt es die offizielle YouTube Data API v3.

So funktioniert es: Du legst `clip.mp4` und `clip.json` in den Ordner `videos/` und startest `python upload.py batch`. Fertig hochgeladene Videos wandern nach `videos/uploaded/`, zusammen mit einer JSON-Datei, die Video-ID und Link enthält.

---

## ⚠️ Zwei Dinge, die du vorher wissen musst

1. **Ohne Google-Prüfung bleiben Videos privat.** Bei API-Projekten, die nach Juli 2020 angelegt und nicht von Google geprüft wurden, sperrt YouTube **jedes** hochgeladene Video auf „Privat“. Das passiert auch dann, wenn du `public` einstellst. **Diese Sperre lässt sich nachträglich nicht aufheben**, das Video musst du dann neu hochladen. Die Lösung ist das kostenlose *YouTube API Services Audit*. Den Antrag stellst du in der Google Cloud Console, die Bearbeitung dauert ein paar Wochen.
   → Bis die Prüfung durch ist, lädst du am besten mit `"privacy": "private"` hoch (Standard). Danach kannst du sie entweder **im YouTube Studio von Hand** veröffentlichen, oder du lädst nach bestandener Prüfung neu hoch.

2. **Tageskontingent.** Jedes Projekt hat 10.000 Einheiten pro Tag. Ein Upload kostete früher ca. 1.600 Einheiten (≈ 6 Videos/Tag). Laut Googles Revision History sind es seit Dezember 2025 nur noch ca. 100 (≈ 100 Videos/Tag). Den aktuellen Wert findest du im Quota Calculator der API-Doku.

---

## Einrichtung (einmalig, ca. 15 Minuten)

### 1. Google-Cloud-Projekt anlegen
1. <https://console.cloud.google.com/> öffnen → oben **Neues Projekt** anlegen (z. B. „YouTube Uploader“).
2. **APIs & Dienste → Bibliothek** → „YouTube Data API v3“ suchen → **Aktivieren**.

### 2. OAuth-Zustimmungsbildschirm
1. **APIs & Dienste → OAuth-Zustimmungsbildschirm** (heißt teils „Google Auth Platform“).
2. Nutzertyp **Extern** wählen, App-Name eintragen, deine E-Mail angeben.
3. Unter **Zielgruppe / Testnutzer** dein Google-Konto eintragen, also das Konto, dem der YouTube-Kanal gehört.
4. **Wichtig:** Den Status später auf **„In Produktion“** stellen. Im Status „Testen“ läuft dein Login nach **7 Tagen** ab, danach müsstest du `auth` jede Woche neu ausführen. Google zeigt dir beim Login dann einen Hinweis „App nicht überprüft“. Das ist für deine eigene Nutzung okay: Klick auf *Erweitert → Weiter zu …*.

### 3. Zugangsdatei herunterladen
1. **APIs & Dienste → Anmeldedaten → Anmeldedaten erstellen → OAuth-Client-ID**.
2. Anwendungstyp: **Desktop-App**.
3. JSON herunterladen und als `client_secret.json` in diesen Ordner legen.

### 4. Installieren und einloggen
```bash
cd youtube-uploader
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python upload.py auth
```
Ein Browserfenster öffnet sich. Wähle das Konto mit deinem Kanal und erlaube den Zugriff. Danach liegt `token.json` im Ordner und das Skript kann ab jetzt allein hochladen.

> `client_secret.json` und `token.json` sind deine Schlüssel zum Kanal. `.gitignore` schließt sie bereits aus, **committe sie nie**.

---

## Benutzung

### Ordner-Modus (empfohlen)
Lege je Video eine gleichnamige JSON-Datei daneben:
```
videos/
  folge-12.mp4
  folge-12.json
  folge-12.jpg      ← optional, wird automatisch als Thumbnail genommen
```

`folge-12.json`:
```json
{
  "title": "Folge 12: So automatisierst du YouTube",
  "description": "Beschreibung mit Zeilenumbrüchen.\n\n0:00 Intro\n1:23 Hauptteil",
  "tags": ["tutorial", "automatisierung"],
  "privacy": "private",
  "language": "de",
  "publish_at": "2026-11-15T17:00:00Z"
}
```

```bash
python upload.py batch --dry-run   # prüft alle JSONs, lädt nichts hoch
python upload.py batch             # lädt hoch
```

Alle Felder:

| Feld | Pflicht | Bedeutung |
|---|---|---|
| `title` | ✅ | max. 100 Zeichen, kein `<` oder `>` |
| `description` | | max. 5000 Bytes (Umlaute zählen doppelt), kein `<` oder `>` |
| `tags` | | Liste, zusammen max. 500 Zeichen |
| `privacy` | | `private` (Standard), `unlisted`, `public` |
| `publish_at` | | Geplante Veröffentlichung in UTC, z. B. `2026-11-15T17:00:00Z` (= 18:00 deutscher Winterzeit). Geht nur mit `"privacy": "private"` |
| `category_id` | | Standard `22` (Menschen & Blogs). `27` = Bildung, `28` = Wissenschaft & Technik, `24` = Unterhaltung, `20` = Gaming |
| `made_for_kids` | | `true`/`false` (Standard `false`), die Kinder-Angabe, die YouTube verlangt |
| `language` | | Sprache von Titel und Ton, z. B. `de` |
| `thumbnail` | | Dateiname eines Bilds. Geht nur, wenn dein Kanal telefonisch verifiziert ist |
| `playlist_id` | | ID einer deiner Playlists (steht in der URL hinter `list=`) |

Ein Tippfehler wie `"titel"` statt `"title"` wird gemeldet und nicht still ignoriert. Wenn ein Upload fehlschlägt, bleibt das Video im Ordner liegen und wird beim nächsten Lauf erneut versucht.

### Einzelnes Video
```bash
python upload.py upload video.mp4 \
  --title "Mein Titel" \
  --description "Meine Beschreibung" \
  --tags "tag1,tag2" \
  --privacy private
```

---

## Claude die Texte schreiben lassen

Das Skript übernimmt den Upload. Titel und Beschreibung kann Claude schreiben: Sag Claude Code (lokal auf deinem Rechner) zum Beispiel:

> „Schreib für `videos/folge-12.mp4` einen Titel und eine Beschreibung zum Thema X, speichere sie als `folge-12.json` und starte dann `python upload.py batch`.“

Claude legt dann die JSON an, prüft sie mit `--dry-run` und lädt hoch.

**Warum lokal?** Das Video und `token.json` liegen auf deinem Rechner. Eine Cloud-Sitzung von Claude hat weder deine Videodatei noch deinen Login, und es ist keine gute Idee, beides dorthin zu kopieren.

---

## Tests
```bash
python -m unittest -v
```
Die Tests ersetzen YouTube durch Attrappen, laden also nichts hoch.

## Typische Fehler

| Meldung | Ursache |
|---|---|
| `quotaExceeded` | Tageskontingent aufgebraucht. Wird um Mitternacht pazifischer Zeit zurückgesetzt (09:00 deutscher Zeit) |
| `invalid_grant` / Login ungültig | Token abgelaufen (Status „Testen“ = 7 Tage) → `python upload.py auth`, App auf „In Produktion“ stellen |
| `uploadLimitExceeded` | YouTubes eigenes Tageslimit für deinen Kanal erreicht |
| Video ist privat obwohl `public` | Projekt nicht geprüft, siehe Abschnitt ⚠️ oben |
| Thumbnail fehlgeschlagen | Kanal nicht verifiziert: <https://www.youtube.com/verify> |
