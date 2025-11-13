# Mac Server Migration - Sichere Schritt-für-Schritt Anleitung

## WICHTIG: Sichere Migration ohne Datenverlust

Diese Anleitung garantiert eine **sichere Migration ohne Ausfall**. Du kannst jederzeit zurück zu deinem aktuellen Setup, falls etwas nicht funktioniert.

---

## Übersicht

**Aktuell:** Mac (Development) mit ngrok
**Ziel:** Mac Server (Production) mit fester URL
**Ausfallzeit:** 0 Minuten (parallel betreiben, dann umschalten)
**Risiko:** Minimal (alte Version läuft weiter als Backup)

---

## Phase 1: VORBEREITUNG (auf aktuellem Mac - NICHTS ändern!)

### ✅ Schritt 1.1: Git-Status prüfen

```bash
cd "/Users/bwl/Desktop/Projekte/Digitale Telefonanlage"
git status
```

**Erwartung:** "Your branch is up to date" und "nothing to commit, working tree clean"

**Falls nicht:** Erst `git add .` → `git commit` → `git push`

### ✅ Schritt 1.2: GitHub-Zugriff sicherstellen

```bash
git pull
```

**Erwartung:** "Already up to date"

### ✅ Schritt 1.3: Aktuelle Konfiguration dokumentieren

```bash
# Port merken (sollte 54351 sein)
grep "app.run" webhook_server_dev.py

# Environment Variablen merken
cat .env
```

**WICHTIG:** Notiere dir diese Werte in einem Textdokument!

- `PLACETEL_SECRET=_________`
- `DASHBOARD_USERNAME=_________`
- `DASHBOARD_PASSWORD=_________`

### ✅ Schritt 1.4: Datenbank-Status dokumentieren

```bash
sqlite3 database.db "SELECT COUNT(*) FROM calls;"
sqlite3 database.db "SELECT COUNT(*) FROM deleted_calls;"
```

**Notiere:** Anzahl Anrufe: _____ | Anzahl gelöschte: _____

### ✅ Schritt 1.5: JSONL-Status dokumentieren

```bash
wc -l placetel_logs.jsonl
```

**Notiere:** Anzahl Log-Einträge: _____

---

## Phase 2: MAC SERVER VORBEREITEN (Server bleibt offline - kein Risiko!)

### ✅ Schritt 2.1: Auf Mac Server einloggen

**Terminal auf deinem aktuellen Mac:**

```bash
ssh DEIN_BENUTZERNAME@MAC_SERVER_IP
```

**Falls SSH-Key fehlt, mit Passwort einloggen**

### ✅ Schritt 2.2: System-Check

```bash
# Python-Version prüfen
python3 --version

# Sollte >= 3.7 sein
```

**Falls Python fehlt:**
```bash
# Homebrew installieren (falls nicht vorhanden)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python installieren
brew install python3
```

### ✅ Schritt 2.3: Installations-Verzeichnis erstellen

```bash
# Wähle einen Ort für die Installation
sudo mkdir -p /opt/telefonanlage
sudo chown $USER:staff /opt/telefonanlage
cd /opt/telefonanlage
```

### ✅ Schritt 2.4: Projekt von GitHub klonen

```bash
cd /opt/telefonanlage
git clone https://github.com/orthocoast/digitale-telefonanlage.git .

# Prüfe ob Dateien da sind
ls -la
```

**Erwartung:** Du siehst `webhook_server_prod.py`, `install.sh`, `.env.example`, etc.

---

## Phase 3: INSTALLATION AUF MAC SERVER (Server bleibt offline!)

### ✅ Schritt 3.1: Installation durchführen

```bash
cd /opt/telefonanlage
chmod +x install.sh
./install.sh
```

**Das Skript fragt nach:**

1. **Placetel Secret:** Trage den Wert aus Schritt 1.3 ein
2. **Dashboard Username:** Trage den Wert aus Schritt 1.3 ein
3. **Dashboard Password:** Trage den Wert aus Schritt 1.3 ein

**WICHTIG:** Verwende die **gleichen Werte** wie auf dem alten System!

### ✅ Schritt 3.2: Datenbank übertragen

**Auf deinem aktuellen Mac (in einem NEUEN Terminal-Fenster):**

```bash
cd "/Users/bwl/Desktop/Projekte/Digitale Telefonanlage"

# Datenbank zum Server kopieren
scp database.db DEIN_BENUTZERNAME@MAC_SERVER_IP:/opt/telefonanlage/

# JSONL-Logs zum Server kopieren
scp placetel_logs.jsonl DEIN_BENUTZERNAME@MAC_SERVER_IP:/opt/telefonanlage/
```

**Falls scp nicht funktioniert (Passwort-Probleme):**

Alternative über USB-Stick oder AirDrop:
1. Kopiere `database.db` und `placetel_logs.jsonl` auf USB-Stick
2. Stecke USB am Server ein
3. Kopiere Dateien nach `/opt/telefonanlage/`

### ✅ Schritt 3.3: Daten verifizieren (auf Mac Server)

```bash
cd /opt/telefonanlage

# Datenbank prüfen
sqlite3 database.db "SELECT COUNT(*) FROM calls;"
sqlite3 database.db "SELECT COUNT(*) FROM deleted_calls;"

# JSONL prüfen
wc -l placetel_logs.jsonl
```

**Vergleiche mit Schritt 1.4 und 1.5 - Zahlen müssen IDENTISCH sein!**

---

## Phase 4: LAUNCH AGENT EINRICHTEN (Automatischer Start)

### ✅ Schritt 4.1: Launch Agent Datei erstellen

**Auf dem Mac Server:**

```bash
nano ~/Library/LaunchAgents/de.praxis.telefonanlage.plist
```

**Füge folgenden Inhalt ein** (ersetze DEIN_BENUTZERNAME):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>de.praxis.telefonanlage</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/opt/telefonanlage/webhook_server_prod.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/opt/telefonanlage</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>

    <key>StandardOutPath</key>
    <string>/opt/telefonanlage/server.log</string>

    <key>StandardErrorPath</key>
    <string>/opt/telefonanlage/server_error.log</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
        <key>Crashed</key>
        <true/>
    </dict>

    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
```

**Speichern:** Ctrl+O, Enter, Ctrl+X

### ✅ Schritt 4.2: Python-Pfad verifizieren

```bash
which python3
```

**Falls Ausgabe NICHT `/usr/local/bin/python3` ist:**

Passe den Pfad in der plist-Datei an (Zeile 11).

### ✅ Schritt 4.3: Launch Agent laden (ABER NOCH NICHT STARTEN!)

```bash
launchctl load ~/Library/LaunchAgents/de.praxis.telefonanlage.plist
```

**Der Service ist jetzt geladen, startet aber noch nicht automatisch**

---

## Phase 5: ERSTER TEST (parallel zum alten Server!)

### ✅ Schritt 5.1: Server manuell starten (Testlauf)

**Auf dem Mac Server:**

```bash
cd /opt/telefonanlage
./start_prod.sh
```

**Erwartung:**
```
✓ Environment variables loaded from .env
Starting production server...
Datenbank initialisiert.
Neuer Anruf von ... importiert.
* Running on http://0.0.0.0:54351
```

### ✅ Schritt 5.2: Dashboard-Test (lokal auf Server)

**In einem NEUEN Terminal (auf dem Mac Server):**

```bash
curl -I http://localhost:54351/dashboard
```

**Erwartung:** `HTTP/1.1 401 UNAUTHORIZED` (Login erforderlich - korrekt!)

### ✅ Schritt 5.3: Server IP-Adresse ermitteln

**Auf dem Mac Server:**

```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Notiere die IP:** z.B. `192.168.1.100`

### ✅ Schritt 5.4: Dashboard-Test von deinem aktuellen Mac aus

**Auf deinem aktuellen Mac (Browser):**

Öffne: `http://MAC_SERVER_IP:54351/dashboard`

**Erwartung:**
- Login-Maske erscheint
- Nach Login: Dashboard mit allen Anrufen sichtbar
- Alle Statistiken korrekt (Anzahl Anrufe wie in Schritt 1.4)

**WICHTIG:** Falls das nicht funktioniert:

```bash
# Auf dem Mac Server: Firewall-Regel hinzufügen
# Systemeinstellungen > Sicherheit > Firewall > Firewall-Optionen > "Python" hinzufügen
```

### ✅ Schritt 5.5: Webhook-Test

**Auf deinem aktuellen Mac:**

```bash
curl -X POST http://MAC_SERVER_IP:54351/placetel \
  -H "Authorization: Bearer DEIN_PLACETEL_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "hello world",
    "source": "migration-test",
    "caller_name": "TEST Migration",
    "caller_gender": "Männlich",
    "caller_dob": "01.01.1980",
    "phone": "+49123456789",
    "call_reason": "Migrations-Test",
    "insurance_provider": "TEST",
    "category": ["Sonstiges"]
  }'
```

**Erwartung:** `{"status": "ok", "log_ts": 123456789.123}`

### ✅ Schritt 5.6: Test-Anruf im Dashboard prüfen

Refresh das Dashboard - der Test-Anruf "TEST Migration" sollte erscheinen.

**Falls alles funktioniert:**  ✅ Phase 5 abgeschlossen
**Falls nicht:** STOPPE HIER und melde dich - alter Server läuft noch!

---

## Phase 6: PRODUCTION START (kein Risiko - alter Server läuft noch!)

### ✅ Schritt 6.1: Test-Server stoppen

**Auf dem Mac Server (im Terminal wo der Server läuft):**

Drücke `Ctrl+C` um den Server zu stoppen.

### ✅ Schritt 6.2: Launch Agent aktivieren

**Auf dem Mac Server:**

```bash
launchctl start de.praxis.telefonanlage
```

**Prüfe ob er läuft:**

```bash
ps aux | grep webhook_server_prod
```

**Erwartung:** Du siehst einen laufenden Python-Prozess

### ✅ Schritt 6.3: Logs prüfen

```bash
tail -f /opt/telefonanlage/server.log
```

**Erwartung:** Ähnliche Ausgabe wie in Schritt 5.1

---

## Phase 7: PLACETEL WEBHOOK UMSTELLEN (JETZT wird umgeschaltet!)

### ⚠️ WICHTIG: Erst NACH erfolgreichem Test!

### ✅ Schritt 7.1: Alte Webhook-URL notieren

Login bei Placetel: https://web.placetel.de

Navigiere zu: **Einstellungen > Webhooks** (oder wie auch immer bei Placetel)

**Notiere die aktuelle URL:** z.B. `https://handcrafted-leora-breathless.ngrok-free.dev/placetel`

### ✅ Schritt 7.2: Neue Webhook-URL eintragen

**Neue URL:** `http://MAC_SERVER_IP:54351/placetel`

**Oder falls du einen Domainnamen hast:** `https://deine-domain.de/placetel`

**WICHTIG:** Authorization Header muss bleiben: `Bearer DEIN_PLACETEL_SECRET`

### ✅ Schritt 7.3: Test-Anruf durchführen

Führe einen echten Test-Anruf durch (oder sende Test-Webhook von Placetel)

**Prüfe:**
- Anruf erscheint im Dashboard auf dem Server
- JSONL wird geschrieben: `tail -1 /opt/telefonanlage/placetel_logs.jsonl`

---

## Phase 8: ALTE UMGEBUNG ABSCHALTEN (optional - als Backup behalten!)

### ✅ Schritt 8.1: Alten Server stoppen (OPTIONAL)

**Auf deinem aktuellen Mac:**

```bash
# Stoppe den laufenden Server (Ctrl+C im Terminal)
# ODER finde den Prozess:
ps aux | grep webhook_server_dev | grep -v grep
kill PID
```

### ✅ Schritt 8.2: ngrok stoppen (OPTIONAL)

```bash
# Finde ngrok Prozess
ps aux | grep ngrok | grep -v grep
kill PID
```

**EMPFEHLUNG:** Lass den alten Server noch 1-2 Tage als Backup laufen!

---

## NOTFALL: Zurück zum alten System

Falls etwas schief geht und du zurück willst:

### 🚨 Rollback-Anleitung

**1. Auf Mac Server:**
```bash
launchctl stop de.praxis.telefonanlage
launchctl unload ~/Library/LaunchAgents/de.praxis.telefonanlage.plist
```

**2. Auf deinem aktuellen Mac:**
```bash
cd "/Users/bwl/Desktop/Projekte/Digitale Telefonanlage"
./start_dev.sh

# In anderem Terminal:
ngrok http 54351
```

**3. In Placetel:**
Trage die alte ngrok-URL wieder ein

**FERTIG - alles läuft wieder wie vorher!**

---

## Erfolgs-Checkliste

Nach erfolgreicher Migration:

- [ ] Mac Server läuft und ist erreichbar
- [ ] Dashboard zeigt alle Anrufe korrekt an
- [ ] Webhooks von Placetel kommen an
- [ ] Launch Agent startet automatisch
- [ ] Alle Daten sind vollständig (Schritt 1.4/1.5 = Schritt 3.3)
- [ ] Test-Anruf funktioniert
- [ ] Alte Umgebung als Backup noch verfügbar

---

## Support-Befehle

### Mac Server Status prüfen

```bash
# Service-Status
launchctl list | grep telefonanlage

# Prozess prüfen
ps aux | grep webhook_server_prod | grep -v grep

# Logs ansehen
tail -f /opt/telefonanlage/server.log
tail -f /opt/telefonanlage/server_error.log

# Datenbank-Status
cd /opt/telefonanlage
sqlite3 database.db "SELECT COUNT(*) FROM calls;"
```

### Service neu starten

```bash
# Stoppen
launchctl stop de.praxis.telefonanlage

# Starten
launchctl start de.praxis.telefonanlage

# Neu laden (nach plist-Änderungen)
launchctl unload ~/Library/LaunchAgents/de.praxis.telefonanlage.plist
launchctl load ~/Library/LaunchAgents/de.praxis.telefonanlage.plist
```

### Firewall-Problem lösen

Falls Dashboard von außen nicht erreichbar:

**Systemeinstellungen > Sicherheit > Firewall > Firewall-Optionen**

- Klicke auf "+"
- Wähle `/usr/local/bin/python3`
- Setze auf "Eingehende Verbindungen zulassen"

---

## Bei Problemen

**Dashboard nicht erreichbar:**
- Firewall prüfen (siehe oben)
- Server-IP korrekt? (`ifconfig`)
- Server läuft? (`ps aux | grep webhook_server_prod`)

**Webhooks kommen nicht an:**
- URL in Placetel korrekt?
- Authorization Header korrekt?
- Logs prüfen: `tail -f /opt/telefonanlage/server.log`

**Daten fehlen:**
- Schritt 3.3 wiederholen (Datenbank-Verifikation)
- Falls nötig: Datenbank nochmal kopieren (Schritt 3.2)

**Service startet nicht:**
- Logs: `tail -f /opt/telefonanlage/server_error.log`
- Python-Pfad: `which python3` → plist anpassen
- .env vorhanden? `cat /opt/telefonanlage/.env`

---

## WICHTIG: Backup-Strategie

**BEVOR du etwas löschst:**

```bash
# Auf Mac Server
cd /opt/telefonanlage
tar -czf ~/telefonanlage-backup-$(date +%Y%m%d).tar.gz .

# Sichert: Datenbank, JSONL, .env, alle Skripte
```

**Backup auf externen Speicher kopieren (empfohlen!)**

---

**Diese Migration ist darauf ausgelegt, dass DU JEDERZEIT zurück kannst!**
**Viel Erfolg! 🚀**
