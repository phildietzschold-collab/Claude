# YouTube-Uploader

Lädt Videos mit **Titel, Beschreibung, Tags, Sichtbarkeit, geplantem Termin, Thumbnail und Playlist** auf deinen YouTube-Kanal, über die offizielle YouTube Data API v3. Komplett kostenlos.

Es gibt zwei Wege:

| | Wie | Wann |
|---|---|---|
| **📱 iPad / Handy** | Video + Text in den Google-Drive-Ordner `YouTube-Upload` legen. GitHub lädt es innerhalb einer Stunde hoch | Standardweg, ohne Laptop |
| **💻 Laptop** | Video + Text in `videos/` legen, `python upload.py batch` | Wenn du am Rechner sitzt |

---

## ⚠️ Zwei Dinge, die du vorher wissen musst

1. **Ohne Google-Prüfung bleiben Videos privat.** Bei API-Projekten, die nach Juli 2020 angelegt und nicht von Google geprüft wurden, sperrt YouTube **jedes** hochgeladene Video auf „Privat“. Das passiert auch dann, wenn du „öffentlich“ einstellst. **Diese Sperre lässt sich nicht aufheben**, das Video müsstest du neu hochladen. Die Lösung ist das kostenlose *YouTube API Services Audit*. Den Antrag stellst du in der Google Cloud Console, die Bearbeitung dauert ein paar Wochen.
   → Bis die Prüfung durch ist, lädst du privat hoch (Standard) und veröffentlichst **im YouTube Studio von Hand**. Das geht auch in der YouTube-Studio-App auf dem iPad.

2. **Tageskontingent.** 10.000 Einheiten pro Tag. Laut Googles Revision History kostet ein Upload seit Dezember 2025 ca. 100 Einheiten (≈ 100 Videos/Tag), vorher ca. 1.600 (≈ 6/Tag). Den aktuellen Wert findest du im Quota Calculator der API-Doku.

---

## Einrichtung (einmalig, ca. 20 Minuten, **einmal am Laptop**)

Den Google-Login musst du einmal auf einem Rechner mit Browser machen. Danach brauchst du den Laptop nicht mehr.

### 1. Google-Cloud-Projekt anlegen
1. <https://console.cloud.google.com/> öffnen → **Neues Projekt** (z. B. „YouTube Uploader“).
2. **APIs & Dienste → Bibliothek**: „YouTube Data API v3“ **aktivieren** und „Google Drive API“ **aktivieren**.

### 2. OAuth-Zustimmungsbildschirm
1. **APIs & Dienste → OAuth-Zustimmungsbildschirm** (heißt teils „Google Auth Platform“).
2. Nutzertyp **Extern**, App-Name eintragen, deine E-Mail angeben.
3. Unter **Zielgruppe / Testnutzer** das Google-Konto eintragen, dem der Kanal gehört.
4. **Status auf „In Produktion“ stellen.** Im Status „Testen“ läuft der Login nach **7 Tagen** ab, dann stoppt die Automatik. Beim Login erscheint „Google hat diese App nicht überprüft“. Das ist für deine eigene Nutzung okay: *Erweitert → Weiter zu …*.

### 3. Zugangsdatei herunterladen
**APIs & Dienste → Anmeldedaten → Anmeldedaten erstellen → OAuth-Client-ID** → Typ **Desktop-App** → JSON herunterladen → als `client_secret.json` in diesen Ordner legen.

### 4. Einloggen
```bash
cd youtube-uploader
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python upload.py auth
```
Wähle im Browser das Konto mit deinem Kanal und erlaube beides: **YouTube-Upload** und **Google Drive**. Drive wird für den iPad-Weg gebraucht. Danach liegt `token.json` im Ordner.

### 5. Login an GitHub geben (für den iPad-Weg)
1. Öffne `token.json` mit einem Texteditor und kopiere **den ganzen Inhalt**.
2. Auf GitHub im Repo: **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `YOUTUBE_TOKEN_JSON`
   - Secret: den kopierten Inhalt einfügen
3. Der Workflow `.github/workflows/youtube-upload.yml` muss auf dem **Standard-Branch (`master`)** liegen, sonst startet GitHub ihn nicht.
4. Test: **Actions → YouTube-Upload → Run workflow**. Beim ersten Lauf wird in deinem Drive der Ordner **`YouTube-Upload`** angelegt, darin der Unterordner `hochgeladen`.

> `client_secret.json` und `token.json` sind die Schlüssel zu deinem Kanal und deinem Drive. `.gitignore` schließt sie aus, **committe sie nie**. Im GitHub-Secret sind sie sicher: Secrets sind verschlüsselt und erscheinen nicht in den Logs.

---

## 📱 Vom iPad hochladen

1. **Video in den Drive-Ordner legen.** In der Google-Drive-App: Ordner `YouTube-Upload` → **+** → **Hochladen** → Video aus „Fotos“ wählen.
   Oder in der Fotos-App: **Teilen → In Dateien sichern → Drive → YouTube-Upload**.
2. **Text dazu anlegen**, mit **genau demselben Namen** wie das Video, nur ohne Endung. Zum Beispiel heißt das Video `Folge 12.mp4` und der Text `Folge 12`. Dafür hast du drei Möglichkeiten:
   - **Google Doc** (am einfachsten): In Drive **+ → Google Docs**, Name `Folge 12`.
   - **Textdatei** `Folge 12.txt`, z. B. aus der Notizen-App → Teilen → In Dateien sichern.
   - **Claude macht es**, siehe unten.
3. Innerhalb einer Stunde ist das Video auf YouTube. Sofort geht es so: Safari → GitHub → **Actions → YouTube-Upload → Run workflow**.
4. Danach liegt alles in `YouTube-Upload/hochgeladen`, zusammen mit **`Folge 12 – Link.txt`**. Darin steht der YouTube-Link und der Link zum Studio.

**Inhalt des Textes:**
```
Folge 12: So automatisierst du YouTube

Hier steht die Beschreibung.
Sie darf mehrere Zeilen haben.

0:00 Intro
1:23 Hauptteil
---
tags: tutorial, automatisierung
sichtbarkeit: privat
termin: 2026-11-15T17:00:00Z
```
- **Erste Zeile = Titel**, alles danach = Beschreibung.
- Der Block nach `---` ist **optional**. Erlaubte Einstellungen:

| Einstellung | Werte |
|---|---|
| `tags:` | kommagetrennt |
| `sichtbarkeit:` | `privat` (Standard), `nicht gelistet`, `öffentlich` |
| `termin:` | geplante Veröffentlichung in UTC, `2026-11-15T17:00:00Z` = 18:00 deutscher Winterzeit (im Sommer: 19:00). Setzt das Video bis dahin automatisch auf privat |
| `playlist:` | Playlist-ID (steht in der URL hinter `list=`) |
| `kategorie:` | Zahl, Standard `22` (Menschen & Blogs). `27` = Bildung, `28` = Wissenschaft & Technik, `24` = Unterhaltung, `20` = Gaming |
| `sprache:` | z. B. `de` |
| `kinder:` | `ja` / `nein` (Standard `nein`), die Kinder-Angabe, die YouTube verlangt |

**Thumbnail:** Leg ein Bild mit demselben Namen dazu, z. B. `Folge 12.jpg`. Das geht nur, wenn dein Kanal unter <https://www.youtube.com/verify> verifiziert ist.

**Wenn etwas schiefgeht,** entsteht im Ordner **`Folge 12.FEHLER.txt`** mit der Ursache, z. B. „Titel hat 112 Zeichen, erlaubt sind 100“. Korrigiere den Text und **lösche die FEHLER-Datei**. Beim nächsten Lauf wird es neu versucht. Solange die Datei da ist, rührt das Skript das Video nicht an, damit nichts doppelt hochgeladen wird.

### Claude die Texte schreiben lassen (auch vom iPad)
In der Claude-App ist Google Drive als Connector verbunden. Sag zum Beispiel:

> „Schreib Titel und Beschreibung für mein Video ‚Folge 12‘ über *Thema X* und speichere den Text als Google Doc namens `Folge 12` in meinem Drive-Ordner `YouTube-Upload`. Format: erste Zeile Titel, dann Beschreibung, dann `---` und `tags:`.“

Claude legt das Doc an. Spätestens nach einer Stunde ist das Video oben.

### Gut zu wissen
- **Kosten:** 0 €. Das Repo ist öffentlich, und öffentliche Repos haben unbegrenzte GitHub-Actions-Minuten. Ein privates Repo hat 2.000 Gratis-Minuten pro Monat. Der stündliche Lauf braucht ca. 720, das reicht also auch.
- **Öffentliche Logs:** Weil das Repo öffentlich ist, kann jeder die Action-Logs sehen. Darin stehen **Dateinamen** und Video-Links, aber keine Titel und keine Zugangsdaten. Private Videos kann über den Link trotzdem niemand ansehen. Wenn dich das stört, stell das Repo auf privat.
- **60-Tage-Regel:** In öffentlichen Repos schaltet GitHub zeitgesteuerte Workflows ab, wenn es 60 Tage lang keine Aktivität im Repo gab. Du bekommst dann eine E-Mail. Reaktivieren geht unter **Actions → YouTube-Upload → Enable workflow**.
- Große Videos sind okay. Der GitHub-Rechner hat ca. 14 GB freien Platz, ein Lauf darf bis zu 3 Stunden dauern.

---

## 💻 Vom Laptop hochladen

```
videos/
  folge-12.mp4
  folge-12.txt      ← gleiches Format wie oben (oder folge-12.json)
  folge-12.jpg      ← optional: Thumbnail
```
```bash
python upload.py batch --dry-run   # prüft alles, lädt nichts hoch
python upload.py batch             # lädt hoch, Erledigtes wandert nach videos/uploaded/
python upload.py drive             # dasselbe wie die GitHub-Action, nur lokal
```

Statt `.txt` geht auch JSON. Ein Beispiel liegt in `videos/BEISPIEL.json`. Die Felder heißen `title`, `description`, `tags` (Liste), `privacy` (`private`/`unlisted`/`public`), `publish_at`, `category_id`, `made_for_kids`, `language`, `thumbnail` und `playlist_id`. Ein Tippfehler wie `"titel"` wird gemeldet und nicht still ignoriert.

Einzelnes Video ohne Textdatei:
```bash
python upload.py upload video.mp4 --title "Mein Titel" --description "Text" --tags "a,b" --privacy private
```

---

## Tests
```bash
python -m unittest -v
```
Die Tests ersetzen YouTube und Drive durch Attrappen, laden also nichts hoch.

## Typische Fehler

| Meldung | Ursache |
|---|---|
| `quotaExceeded` | Tageskontingent aufgebraucht, wird um 09:00 deutscher Zeit zurückgesetzt |
| `invalid_grant` / Login ungültig | Token abgelaufen (Status „Testen“ = 7 Tage) → App auf „In Produktion“, `python upload.py auth`, Secret `YOUTUBE_TOKEN_JSON` neu setzen |
| `insufficientPermissions` bei Drive | Beim Login nicht beide Häkchen gesetzt → `python upload.py auth` wiederholen |
| `uploadLimitExceeded` | YouTubes eigenes Tageslimit für deinen Kanal |
| Video privat obwohl „öffentlich“ | Projekt nicht geprüft, siehe ⚠️ oben |
| Action meldet „Secret fehlt“ | Schritt 5 der Einrichtung |
| Video wird nicht abgeholt | Text heißt anders als das Video, oder eine `.FEHLER.txt` liegt noch im Ordner |
