# FritzBox Call Monitor Integration

## Problem

Bei Rufnummernweiterleitungen über die FritzBox zu Placetel sieht Placetel nur noch die Praxisnummer, nicht die echte Anrufernummer des Patienten.

## Lösung: FritzBox Call Monitor

Die FritzBox hat einen integrierten **Call Monitor**, der alle eingehenden und ausgehenden Anrufe mit der **echten Anrufernummer** protokolliert - **BEVOR** die Weiterleitung erfolgt.

---

## Schritt 1: FritzBox Call Monitor aktivieren

### Per Telefon aktivieren:

1. **Wähle mit einem angeschlossenen Telefon:**
   ```
   #96*5*
   ```
   (Raute-96-Stern-5-Stern)

2. **Du hörst die Ansage:** "Call Monitor aktiviert"

### Deaktivieren (falls nötig):
```
#96*4*
```

---

## Schritt 2: Call Monitor testen

Der Call Monitor läuft auf **Port 1012** der FritzBox.

### Manueller Test:

```bash
# Verbindung zur FritzBox (ersetze 192.168.178.1 mit deiner FritzBox-IP)
telnet 192.168.178.1 1012
```

**Jetzt einen Testanruf tätigen!** Du siehst dann etwas wie:

```
01.01.25 10:30:00;RING;0;0151234567890;200893;SIP0;
01.01.25 10:30:05;CONNECT;0;1;200893;
```

**Erklärung:**
- `RING` = Eingehender Anruf
- `0151234567890` = **Echte Anrufernummer** (Patient!)
- `200893` = Angerufene Nummer (Praxis)

---

## Schritt 3: Python Script installieren

Das Script hört auf den FritzBox Call Monitor und schreibt die echten Nummern in die Datenbank.

### Installation:

```bash
cd "/Users/bwl/Desktop/Projekte/Digitale Telefonanlage"

# Script ausführbar machen
chmod +x fritzbox_monitor.py

# Testen
python3 fritzbox_monitor.py
```

### Als Hintergrunddienst starten (macOS):

```bash
# Im Hintergrund starten
nohup python3 fritzbox_monitor.py > fritzbox_monitor.log 2>&1 &

# Prozess-ID (PID) wird angezeigt, z.B.: [1] 12345
```

### Als Hintergrunddienst starten (Linux mit systemd):

Siehe `fritzbox-monitor.service.template`

---

## Schritt 4: Wie funktioniert die Integration?

### Variante A: Call Monitor + Webhook kombinieren

1. **FritzBox Call Monitor** erfasst die echte Telefonnummer
2. Speichert sie in einer **temporären Lookup-Tabelle** (z.B. Redis oder SQLite)
3. **Placetel Webhook** kommt an mit Praxisnummer
4. System schaut in der Lookup-Tabelle nach der echten Nummer
5. **Ersetzt** die Praxisnummer durch die echte Nummer

### Variante B: Nur Call Monitor (einfacher!)

1. **FritzBox Call Monitor** erfasst eingehende Anrufe
2. Erstellt sofort einen **Datenbank-Eintrag** mit echter Nummer
3. **Placetel Webhook** kommt später mit zusätzlichen Daten (Name, Anliegen, etc.)
4. System **updated** den bestehenden Eintrag

**Empfehlung: Variante B** - Einfacher und robuster!

---

## Call Monitor Event-Format

### RING (Eingehender Anruf)
```
Datum;RING;ConnectionID;CallerNumber;CalledNumber;SIPnumber;
```

Beispiel:
```
01.01.25 10:30:00;RING;0;0151234567890;200893;SIP0;
```

- `0151234567890` = **Anrufernummer (Patient)**
- `200893` = Angerufene Nummer (Praxis)

### CONNECT (Anruf angenommen)
```
Datum;CONNECT;ConnectionID;Extension;Number;
```

### DISCONNECT (Anruf beendet)
```
Datum;DISCONNECT;ConnectionID;Duration;
```

---

## Sicherheit

### FritzBox absichern:

1. **Lokales Netzwerk only:** Call Monitor ist nur im lokalen Netzwerk erreichbar
2. **VPN nutzen:** Falls der Server extern steht, per VPN verbinden
3. **IP-Filter:** In FritzBox nur bestimmte IPs zulassen

### Keine sensiblen Daten im Call Monitor:

Der Call Monitor liefert nur:
- Telefonnummern
- Zeitstempel
- Verbindungsstatus

Namen, Anliegen etc. kommen weiterhin vom Placetel Webhook.

---

## Fehlerbehebung

### Call Monitor reagiert nicht:

```bash
# Prüfen ob Port 1012 erreichbar ist
nc -zv 192.168.178.1 1012

# Oder mit telnet
telnet 192.168.178.1 1012
```

**Erwartete Ausgabe:** Verbindung steht, keine Daten bis ein Anruf kommt.

### FritzBox-IP herausfinden:

```bash
# macOS/Linux
route -n get default | grep gateway

# Oder
netstat -nr | grep default
```

Häufig: `192.168.178.1` oder `192.168.1.1`

### Keine Events sichtbar:

- Call Monitor aktiviert? (`#96*5*`)
- Firewall auf dem Server blockiert Port 1012?
- Falsche FritzBox-IP?

---

## Vorteile dieser Lösung

✅ **Echte Telefonnummern** werden erfasst
✅ **Unabhängig von Placetel** - funktioniert immer
✅ **Keine Änderung** an FritzBox-Weiterleitung nötig
✅ **Echtzeit-Erfassung** - Nummer ist sofort verfügbar
✅ **Minimaler Aufwand** - nur ein zusätzliches Script

---

## Alternative: CLI-Weiterleitung prüfen

**Bevor du den Call Monitor einrichtest, prüfe:**

Möglicherweise leitet die FritzBox die **Caller ID** gar nicht an Placetel weiter!

### In der FritzBox prüfen:

1. **Telefonie → Rufnummern → [Deine Nummer]**
2. **Rufnummernübermittlung:** Muss auf **"eigene Rufnummer"** stehen
3. **NICHT:** "anonym" oder "unterdrückt"

Falls das bereits richtig eingestellt ist, sollte Placetel die echte Nummer erhalten.

**Teste das zuerst!** Falls Placetel die Nummer bekommt, brauchen wir keinen Call Monitor.

---

## Zusammenfassung

**Schnellste Lösung:**
1. Prüfe FritzBox CLI-Einstellungen
2. Falls das nicht hilft: Call Monitor aktivieren (`#96*5*`)
3. Script `fritzbox_monitor.py` starten
4. Fertig! 🎉

Bei Fragen oder Problemen: Siehe Logs in `fritzbox_monitor.log`
