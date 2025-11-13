# FritzBox Call Monitor - Schnellstart

## Problem gelöst! 🎉

Deine Praxisnummer (200893) wird jetzt automatisch durch die **echte Patientennummer** ersetzt!

---

## ⚡ So funktionierts in 3 Schritten:

### Schritt 1: Call Monitor aktivieren (2 Minuten)

**Mit einem angeschlossenen Telefon wählen:**
```
#96*5*
```
(Raute-96-Stern-5-Stern)

Du hörst: **"Call Monitor aktiviert"** ✅

### Schritt 2: FritzBox-Monitor starten (1 Minute)

**Öffne ein neues Terminal und starte:**
```bash
cd "/Users/bwl/Desktop/Projekte/Digitale Telefonanlage"
python3 fritzbox_monitor.py
```

Du siehst:
```
🚀 FritzBox Call Monitor gestartet
✅ Verbunden mit FritzBox Call Monitor!
Warte auf Anrufe...
```

**Lass dieses Terminal-Fenster offen!**

### Schritt 3: Webhook-Server (neu) starten

**In einem ZWEITEN Terminal:**
```bash
cd "/Users/bwl/Desktop/Projekte/Digitale Telefonanlage"
./start_dev.sh
```

**Fertig!** 🎉

---

## 🧪 Test durchführen

1. **Beide Programme laufen** (FritzBox Monitor + Webhook Server)
2. **Testanruf tätigen** zur Praxisnummer
3. **Im FritzBox-Monitor-Terminal** siehst du:
   ```
   📞 Anruf gespeichert: +49157544xxxxx → 200893
   ```
4. **Im Webhook-Server-Terminal** siehst du:
   ```
   ⚠️  Praxisnummer erkannt in Webhook: +493836200893
   ✅ Ersetzt durch echte Nummer: +49157544xxxxx
   ```
5. **Im Dashboard** siehst du die **echte Patientennummer** statt 200893

---

## 📋 Was passiert technisch?

```
Patient ruft an (+49157...)
    ↓
FritzBox erfasst Nummer ← FritzBox Monitor hört mit!
    ↓
Weiterleitung zu Placetel
    ↓
Placetel sieht nur Praxisnummer (200893)
    ↓
Webhook an Server
    ↓
Server prüft: Enthält Praxisnummer? → JA!
    ↓
Server holt echte Nummer vom FritzBox Monitor ← Hier!
    ↓
Dashboard zeigt echte Nummer! ✅
```

---

## 🔧 Tipps

### FritzBox-IP anpassen (falls nötig)

Falls deine FritzBox eine andere IP hat:

```bash
nano fritzbox_monitor.py
```

Ändere Zeile 23:
```python
FRITZBOX_IP = "192.168.178.1"  # Deine FritzBox-IP hier eintragen
```

### FritzBox-IP herausfinden:

```bash
# macOS
route -n get default | grep gateway

# Häufig: 192.168.178.1 oder 192.168.1.1
```

### Im Hintergrund laufen lassen

**FritzBox Monitor im Hintergrund:**
```bash
nohup python3 fritzbox_monitor.py > fritzbox_monitor.log 2>&1 &
```

**Prozess später beenden:**
```bash
# PID finden
ps aux | grep fritzbox_monitor

# Beenden (ersetze 12345 mit der echten PID)
kill 12345
```

---

## ❓ Fehlerbehebung

### "Verbindung verweigert"

**Ursache:** Call Monitor nicht aktiviert

**Lösung:** Nochmal `#96*5*` wählen

### "Keine echte Nummer gefunden"

**Ursache:** FritzBox Monitor läuft nicht oder erfasst den Anruf nicht

**Prüfen:**
```bash
# Ist der Monitor verbunden?
ps aux | grep fritzbox_monitor

# Zeigt er Anrufe?
tail -f fritzbox_calls.log
```

### "Timeout: Keine Verbindung"

**Ursache:** Falsche FritzBox-IP

**Lösung:**
1. FritzBox-IP herausfinden (siehe oben)
2. In `fritzbox_monitor.py` anpassen
3. Neu starten

---

## 📊 Logs prüfen

**FritzBox Monitor Logs:**
```bash
tail -f "/Users/bwl/Desktop/Projekte/Digitale Telefonanlage/fritzbox_calls.log"
```

**Datenbank prüfen:**
```bash
sqlite3 database.db "SELECT * FROM phone_lookup ORDER BY id DESC LIMIT 10;"
```

---

## 🚀 Produktivbetrieb

Für den dauerhaften Betrieb:

### Als systemd Service (Linux):

Siehe `fritzbox-monitor.service.template`

### Mit launchd (macOS):

Kommt bald - oder einfach im Hintergrund laufen lassen (siehe oben)

---

## ✅ Checkliste

- [ ] Call Monitor aktiviert (`#96*5*`)
- [ ] `fritzbox_monitor.py` läuft
- [ ] Webhook-Server läuft (neu gestartet!)
- [ ] Testanruf durchgeführt
- [ ] Dashboard zeigt echte Nummer

**Alles grün? Perfekt! 🎉**

Bei Problemen: Siehe `FRITZBOX-CALLMONITOR.md` für Details
