# Netzwerk-Zugriff einrichten

## Problem: Andere PCs im Netzwerk können sich nicht verbinden

### Häufigste Ursachen und Lösungen

---

## 1️⃣ Firewall auf dem Server-Mac blockiert den Zugriff

### Lösung A: Firewall-Regel hinzufügen (empfohlen)

**macOS Firewall konfigurieren:**

1. **Systemeinstellungen öffnen**
   - Apple-Menü > Systemeinstellungen > Netzwerk > Firewall

2. **Firewall-Optionen öffnen**
   - Klick auf "Firewall-Optionen..." oder "Erweitert..."

3. **Anwendung hinzufügen**
   - Klick auf das "+" Symbol
   - Navigiere zu Python: `/usr/bin/python3` oder `/usr/local/bin/python3`
   - Oder wähle "Python" aus der Liste
   - Setze auf "Eingehende Verbindungen erlauben"

4. **Alternative: Firewall komplett ausschalten (nur für Tests!)**
   - Systemeinstellungen > Netzwerk > Firewall
   - Firewall ausschalten
   - **ACHTUNG:** Nur für lokale Netzwerke / Tests empfohlen!

### Lösung B: Port über Terminal freigeben

Auf neueren macOS-Versionen:

```bash
# Port 54351 für eingehende Verbindungen öffnen
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /usr/bin/python3
```

---

## 2️⃣ Falsche IP-Adresse verwendet

### Die richtige IP-Adresse finden

**Auf dem Server-Mac (wo der Webhook-Server läuft):**

```bash
# IP-Adresse herausfinden
ifconfig | grep "inet " | grep -v 127.0.0.1
```

Oder einfacher:

```bash
# Nur die relevante IP
ipconfig getifaddr en0    # WiFi
ipconfig getifaddr en1    # Ethernet (falls verwendet)
```

**Beispiel-Ausgabe:**
```
192.168.1.42
```

### Von anderen PCs verbinden

Die anderen PCs müssen dann diese Adresse verwenden:

```
http://192.168.1.42:54351/dashboard
```

**NICHT verwenden:**
- ❌ `http://localhost:54351/dashboard` (funktioniert nur auf dem Server selbst)
- ❌ `http://127.0.0.1:54351/dashboard` (funktioniert nur auf dem Server selbst)

**SONDERN:**
- ✅ `http://ECHTE-IP:54351/dashboard` (z.B. `http://192.168.1.42:54351/dashboard`)

---

## 3️⃣ Server läuft nicht oder hört nicht auf allen Interfaces

### Überprüfen, ob der Server läuft

```bash
# Prozess prüfen
ps aux | grep webhook_server

# Port prüfen
lsof -i :54351
```

**Erwartete Ausgabe bei `lsof`:**
```
COMMAND    PID  USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
python3  12345  bwl    3u  IPv4 0x1234567890abcdef      0t0  TCP *:54351 (LISTEN)
```

Das `*:54351` bedeutet, dass auf allen Interfaces gehört wird. ✅

Falls `127.0.0.1:54351` steht, ist der Server nur lokal erreichbar. ❌

### Server mit korrekter Konfiguration starten

Die Server-Skripte (`webhook_server_prod.py` und `webhook_server_dev.py`) sind bereits korrekt konfiguriert mit:

```python
app.run(host="0.0.0.0", port=PORT, debug=True)
```

`host="0.0.0.0"` bedeutet: Auf allen Netzwerkschnittstellen hören. ✅

---

## 🧪 Test-Checkliste

Gehe diese Schritte durch:

### Auf dem Server-Mac:

```bash
# 1. Server läuft?
ps aux | grep webhook_server

# 2. Port offen?
lsof -i :54351

# 3. IP-Adresse herausfinden
ifconfig | grep "inet " | grep -v 127.0.0.1
# Oder:
ipconfig getifaddr en0
```

### Auf einem anderen PC im Netzwerk:

```bash
# 1. Verbindung zum Server-Port testen
telnet 192.168.1.42 54351
# Oder mit netcat:
nc -zv 192.168.1.42 54351

# 2. Im Browser öffnen:
# http://192.168.1.42:54351/dashboard
```

---

## 🔧 Schnelle Lösung für Tests

Falls du nur schnell testen willst, ob es funktioniert:

### 1. Firewall temporär ausschalten

**macOS:**
```
Systemeinstellungen > Netzwerk > Firewall > Firewall deaktivieren
```

### 2. Server neu starten

```bash
cd "/Users/bwl/Desktop/Projekte/Digitale Telefonanlage"
./start_prod.sh
```

### 3. IP-Adresse notieren

```bash
ipconfig getifaddr en0
```

### 4. Von anderem PC testen

```
http://DEINE-IP:54351/dashboard
```

### 5. Firewall wieder einschalten

Und diesmal Python als Ausnahme hinzufügen (siehe oben).

---

## 🌐 Für Produktivumgebung: Reverse Proxy einrichten

Für einen professionellen Produktivbetrieb empfehlen wir:

### Mit nginx als Reverse Proxy

1. **nginx installieren:**
   ```bash
   brew install nginx  # macOS
   sudo apt install nginx  # Linux
   ```

2. **nginx konfigurieren:**
   ```nginx
   server {
       listen 80;
       server_name ihre-domain.de;

       location / {
           proxy_pass http://127.0.0.1:54351;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. **SSL mit Let's Encrypt (optional):**
   ```bash
   sudo certbot --nginx -d ihre-domain.de
   ```

**Vorteile:**
- ✅ Standard HTTP-Port (80) statt 54351
- ✅ SSL/TLS-Verschlüsselung möglich
- ✅ Bessere Performance
- ✅ Professioneller

---

## 📋 Zusammenfassung: Häufigste Lösung

In 90% der Fälle hilft:

1. **Server-IP herausfinden:**
   ```bash
   ipconfig getifaddr en0
   ```

2. **Firewall-Regel hinzufügen:**
   - Systemeinstellungen > Firewall > Python erlauben

3. **Andere PCs verwenden:**
   ```
   http://SERVER-IP:54351/dashboard
   ```

Das war's! 🎉

---

## 🆘 Immer noch Probleme?

Führe auf dem Server-Mac aus:

```bash
# Debug-Informationen sammeln
echo "=== Server läuft? ==="
ps aux | grep webhook_server

echo ""
echo "=== Port 54351 offen? ==="
lsof -i :54351

echo ""
echo "=== Meine IP-Adressen: ==="
ifconfig | grep "inet " | grep -v 127.0.0.1

echo ""
echo "=== Firewall-Status: ==="
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

Sende die Ausgabe zur weiteren Diagnose.
