# Migrationsleitfaden - Digitale Telefonanlage

Dieser Leitfaden beschreibt den vollständigen Prozess zum Umzug der digitalen Telefonanlage auf einen neuen Server/Rechner.

## Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Vorbereitungen am alten Server](#vorbereitungen-am-alten-server)
3. [Vorbereitung des neuen Servers](#vorbereitung-des-neuen-servers)
4. [Installation auf dem neuen Server](#installation-auf-dem-neuen-server)
5. [Datenübertragung](#datenübertragung)
6. [Konfiguration](#konfiguration)
7. [Test und Inbetriebnahme](#test-und-inbetriebnahme)
8. [Placetel Webhook umstellen](#placetel-webhook-umstellen)
9. [Fehlerbehebung](#fehlerbehebung)

---

## Übersicht

### Was wird migriert?

- ✅ Anwendungscode (Python-Skripte)
- ✅ Datenbank mit allen Anrufdaten (`database.db`)
- ✅ Webhook-Logs (`placetel_logs.jsonl`)
- ✅ Konfiguration (`.env` Datei)
- ✅ Start-Skripte

### Geschätzte Ausfallzeit

- **Mit Vorbereitung:** 5-15 Minuten
- **Ohne Vorbereitung:** 30-60 Minuten

---

## Vorbereitungen am alten Server

### 1. Server stoppen

```bash
# Falls systemd Service läuft:
sudo systemctl stop telefonanlage

# Oder manuell laufenden Python-Prozess beenden:
pkill -f webhook_server
```

### 2. Daten sichern

Erstellen Sie ein Backup-Verzeichnis und kopieren Sie alle wichtigen Dateien:

```bash
# Backup-Verzeichnis erstellen
mkdir -p ~/telefonanlage-backup
cd ~/telefonanlage-backup

# Alle Projektdateien kopieren
cp -r /pfad/zum/projekt/* .

# Oder als tar.gz archivieren
cd /pfad/zum/projekt
tar -czf ~/telefonanlage-backup.tar.gz \
    webhook_server_prod.py \
    webhook_server_dev.py \
    start_prod.sh \
    start_dev.sh \
    .env \
    .env.example \
    database.db \
    placetel_logs.jsonl \
    README.md \
    MIGRATION.md \
    install.sh
```

### 3. Konfiguration dokumentieren

Notieren Sie wichtige Informationen:

```bash
# Aktuellen Port prüfen (sollte 54351 sein)
grep PORT webhook_server_prod.py

# Environment Variables sichern
cat .env

# Python-Version notieren
python3 --version

# Installierte Pakete notieren
pip3 list | grep -i flask
```

### 4. Letzte Daten sicherstellen

```bash
# Größe der Datenbank prüfen
ls -lh database.db

# Anzahl der Log-Einträge zählen
wc -l placetel_logs.jsonl

# Letzten Eintrag in der DB prüfen (optional)
sqlite3 database.db "SELECT COUNT(*) FROM calls;"
```

---

## Vorbereitung des neuen Servers

### Systemanforderungen

- **Betriebssystem:** Linux (Ubuntu/Debian/CentOS) oder macOS
- **Python:** Version 3.7 oder höher
- **RAM:** Mindestens 512 MB (1 GB empfohlen)
- **Speicher:** Mindestens 500 MB frei
- **Netzwerk:** Port 54351 muss erreichbar sein

### 1. System aktualisieren

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt upgrade -y
```

**CentOS/RHEL:**
```bash
sudo yum update -y
```

**macOS:**
```bash
brew update
brew upgrade
```

### 2. Python 3 installieren (falls nicht vorhanden)

**Ubuntu/Debian:**
```bash
sudo apt install python3 python3-pip -y
```

**CentOS/RHEL:**
```bash
sudo yum install python3 python3-pip -y
```

**macOS:**
```bash
brew install python3
```

### 3. Benutzer und Verzeichnis erstellen (optional, aber empfohlen)

```bash
# Neuer Benutzer für die Anwendung (optional)
sudo useradd -m -s /bin/bash telefonanlage

# Installationsverzeichnis erstellen
sudo mkdir -p /opt/telefonanlage
sudo chown $USER:$USER /opt/telefonanlage
cd /opt/telefonanlage
```

---

## Installation auf dem neuen Server

### Option A: Automatische Installation (empfohlen)

1. **Dateien auf den neuen Server übertragen:**

```bash
# Von Ihrem lokalen Rechner aus (mit scp):
scp ~/telefonanlage-backup.tar.gz user@neuer-server:/opt/telefonanlage/

# Auf dem neuen Server entpacken:
cd /opt/telefonanlage
tar -xzf telefonanlage-backup.tar.gz
```

2. **Installationsskript ausführen:**

```bash
cd /opt/telefonanlage
chmod +x install.sh
./install.sh
```

Das Skript wird:
- ✅ Python-Abhängigkeiten installieren
- ✅ `.env` Datei konfigurieren (oder vorhandene nutzen)
- ✅ Systemd-Service einrichten (optional, nur Linux)
- ✅ Firewall-Hinweise geben

### Option B: Manuelle Installation

1. **Python-Abhängigkeiten installieren:**

```bash
pip3 install flask Flask-HTTPAuth
```

2. **`.env` Datei konfigurieren:**

```bash
cp .env.example .env
nano .env  # Oder vi/vim zum Bearbeiten
```

Tragen Sie Ihre Werte ein:
```
PLACETEL_SECRET=ihr-secret-hier
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=ihr-passwort
FLASK_ENV=production
```

3. **Berechtigungen setzen:**

```bash
chmod 600 .env
chmod +x start_prod.sh start_dev.sh
```

---

## Datenübertragung

### Wichtige Dateien übertragen

Falls noch nicht geschehen, übertragen Sie diese Dateien:

```bash
# Von Ihrem alten Server:
scp database.db user@neuer-server:/opt/telefonanlage/
scp placetel_logs.jsonl user@neuer-server:/opt/telefonanlage/
scp .env user@neuer-server:/opt/telefonanlage/
```

### Dateien verifizieren

```bash
cd /opt/telefonanlage

# Prüfen, ob alle Dateien vorhanden sind
ls -lh database.db placetel_logs.jsonl .env

# Datenbankintegrität prüfen
sqlite3 database.db "PRAGMA integrity_check;"
# Sollte ausgeben: ok

# Anzahl Einträge prüfen
sqlite3 database.db "SELECT COUNT(*) FROM calls;"
```

---

## Konfiguration

### 1. Environment Variables überprüfen

```bash
cat .env
```

Stellen Sie sicher, dass folgende Werte gesetzt sind:
- `PLACETEL_SECRET`
- `DASHBOARD_USERNAME`
- `DASHBOARD_PASSWORD`

### 2. Firewall konfigurieren

**Ubuntu/Debian (UFW):**
```bash
sudo ufw allow 54351/tcp
sudo ufw reload
sudo ufw status
```

**CentOS/RHEL (firewalld):**
```bash
sudo firewall-cmd --add-port=54351/tcp --permanent
sudo firewall-cmd --reload
sudo firewall-cmd --list-ports
```

**macOS:**
```
Systemeinstellungen > Sicherheit > Firewall > Firewall-Optionen
```

### 3. Systemd Service einrichten (Linux, optional)

Falls nicht durch `install.sh` erledigt:

```bash
sudo nano /etc/systemd/system/telefonanlage.service
```

Inhalt:
```ini
[Unit]
Description=Digitale Telefonanlage Webhook Server
After=network.target

[Service]
Type=simple
User=IHR_BENUTZER
WorkingDirectory=/opt/telefonanlage
EnvironmentFile=/opt/telefonanlage/.env
ExecStart=/usr/bin/python3 /opt/telefonanlage/webhook_server_prod.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Service aktivieren und starten:
```bash
sudo systemctl daemon-reload
sudo systemctl enable telefonanlage
sudo systemctl start telefonanlage
sudo systemctl status telefonanlage
```

---

## Test und Inbetriebnahme

### 1. Server starten

**Mit systemd (Linux):**
```bash
sudo systemctl start telefonanlage
sudo systemctl status telefonanlage
```

**Manuell:**
```bash
cd /opt/telefonanlage
./start_prod.sh
```

### 2. Logs prüfen

**Systemd-Logs:**
```bash
sudo journalctl -u telefonanlage -f
```

**Direkte Ausgabe:**
Falls manuell gestartet, sehen Sie die Logs direkt im Terminal.

### 3. Dashboard testen

```bash
# Lokaler Test
curl http://localhost:54351/dashboard

# Oder im Browser öffnen
firefox http://localhost:54351/dashboard
```

Sie sollten zur Login-Seite weitergeleitet werden.

### 4. Login testen

- Öffnen Sie: `http://SERVER-IP:54351/dashboard`
- Geben Sie Ihre Anmeldedaten ein (aus `.env`)
- Prüfen Sie, ob alle Anrufdaten angezeigt werden

### 5. Funktionstest

- [ ] Dashboard lädt korrekt
- [ ] Alle Anrufe werden angezeigt
- [ ] Suchfunktion funktioniert
- [ ] Status kann geändert werden (auf "Erledigt" setzen)
- [ ] Statistiken werden korrekt angezeigt
- [ ] Auto-Refresh funktioniert (30 Sekunden warten)

### 6. Webhook-Endpunkt testen

```bash
# Test mit curl (von einem anderen Rechner)
curl -X POST http://SERVER-IP:54351/webhook \
  -H "Authorization: Bearer IHR-PLACETEL-SECRET" \
  -H "Content-Type: application/json" \
  -d '{"event":"call","peer":"1234567890","start":"2024-01-01T10:00:00"}'
```

Erwartete Antwort: `{"status": "success"}`

---

## Placetel Webhook umstellen

### 1. Neue URL ermitteln

**Lokaler Server / VPN:**
```
http://SERVER-IP:54351/webhook
```

**Mit Reverse Proxy (empfohlen):**
```
https://ihre-domain.de/webhook
```

**Mit ngrok (nur für Tests):**
```bash
ngrok http 54351
# Notieren Sie die ngrok-URL: https://xxxxx.ngrok.io
```

### 2. In Placetel eintragen

1. Login bei Placetel: https://web.placetel.de
2. Navigieren zu: **Einstellungen > API & Webhooks**
3. Webhook bearbeiten oder neu erstellen:
   - **URL:** `http://ihre-server-ip:54351/webhook`
   - **Methode:** POST
   - **Authorization:** `Bearer IHR-PLACETEL-SECRET`
   - **Events:** Call events aktivieren

4. Speichern und testen

### 3. Test-Anruf durchführen

- Führen Sie einen Test-Anruf durch
- Prüfen Sie, ob er im Dashboard erscheint
- Prüfen Sie die Logs:

```bash
# Systemd
sudo journalctl -u telefonanlage -n 50

# Oder Log-Datei
tail -f placetel_logs.jsonl
```

---

## Fehlerbehebung

### Problem: Server startet nicht

**Ursache: Environment Variables fehlen**

```bash
# Prüfen
cat .env

# Testen
source .env
python3 webhook_server_prod.py
```

**Ursache: Port bereits belegt**

```bash
# Port 54351 prüfen
sudo lsof -i :54351
sudo netstat -tlnp | grep 54351

# Prozess beenden
sudo kill -9 PID
```

**Ursache: Python-Pakete fehlen**

```bash
pip3 install flask Flask-HTTPAuth
```

### Problem: Dashboard nicht erreichbar

**Firewall prüfen:**

```bash
# UFW
sudo ufw status
sudo ufw allow 54351/tcp

# firewalld
sudo firewall-cmd --list-ports
sudo firewall-cmd --add-port=54351/tcp --permanent
sudo firewall-cmd --reload
```

**Server-IP prüfen:**

```bash
# Interne IP
ip addr show
# Oder
ifconfig

# Externe IP
curl ifconfig.me
```

### Problem: Login funktioniert nicht

**Credentials prüfen:**

```bash
cat .env | grep DASHBOARD
```

**Browser-Cache leeren** oder Inkognito-Modus verwenden

### Problem: Webhook kommt nicht an

**Server-Logs prüfen:**

```bash
sudo journalctl -u telefonanlage -f
```

**Placetel-Konfiguration prüfen:**
- URL korrekt?
- Authorization Header korrekt?
- Secret stimmt überein?

**Test mit curl:**

```bash
curl -v -X POST http://localhost:54351/webhook \
  -H "Authorization: Bearer $(grep PLACETEL_SECRET .env | cut -d'=' -f2)" \
  -H "Content-Type: application/json" \
  -d '{"event":"call","peer":"TEST"}'
```

### Problem: Daten fehlen

**Datenbank prüfen:**

```bash
sqlite3 database.db "SELECT COUNT(*) FROM calls;"
sqlite3 database.db "SELECT * FROM calls ORDER BY id DESC LIMIT 5;"
```

**Backup wiederherstellen:**

```bash
cp database.db database.db.backup
cp ~/backup/database.db .
sudo systemctl restart telefonanlage
```

---

## Zusammenfassung: Schnell-Migration

Für erfahrene Nutzer - die komplette Migration in Kurzform:

```bash
# 1. ALTER SERVER: Backup erstellen
cd /pfad/zum/projekt
tar -czf ~/telefonanlage-backup.tar.gz *

# 2. NEUER SERVER: Vorbereiten
sudo apt update && sudo apt install -y python3 python3-pip
sudo mkdir -p /opt/telefonanlage
cd /opt/telefonanlage

# 3. Dateien übertragen
scp user@alter-server:~/telefonanlage-backup.tar.gz .
tar -xzf telefonanlage-backup.tar.gz

# 4. Installation
chmod +x install.sh
./install.sh

# 5. Service starten
sudo systemctl start telefonanlage
sudo systemctl enable telefonanlage

# 6. Test
curl http://localhost:54351/dashboard

# 7. Placetel Webhook umstellen
# → In Placetel-Interface neue Server-IP eintragen

# FERTIG!
```

---

## Support und weitere Informationen

- **README:** Siehe `README.md` für detaillierte Dokumentation
- **Logs:** `sudo journalctl -u telefonanlage -f`
- **Datenbank-Schema:** SQLite mit Tabelle `calls`
- **Port:** 54351 (änderbar in `webhook_server_*.py`)

Bei Problemen:
1. Logs prüfen
2. `.env` Datei verifizieren
3. Firewall-Regeln prüfen
4. Python-Abhängigkeiten neu installieren

---

**Viel Erfolg bei der Migration!**
