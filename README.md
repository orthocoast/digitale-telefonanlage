# Digitale Telefonanlage

## 1. Projektübersicht

Dieses Projekt ist eine digitale Telefonanlage zur Erfassung und Verwaltung von Anrufdaten. Es empfängt Anrufinformationen über einen Webhook vom Telefonie-Dienst Placetel, speichert diese in einer Datenbank und stellt sie in einem interaktiven Web-Dashboard dar. Mitarbeiter können den Status von Anrufen einsehen und als "erledigt" markieren.

## 2. Architektur

Die Anwendung basiert auf einer einfachen und robusten Architektur:

- **Webserver (Python/Flask):** Ein Webserver, der zwei Hauptaufgaben erfüllt:
    1.  Er empfängt Daten vom Placetel-Webhook.
    2.  Er stellt das interaktive Dashboard als Webseite bereit.
- **Rohdaten-Log (`placetel_logs.jsonl`):** Eine reine Textdatei, in der alle eingehenden Webhook-Daten unverändert als Backup und zur Nachverfolgung gespeichert werden (Append-only).
- **Operative Datenbank (`database.db`):** Eine **SQLite**-Datenbank, in der die Anrufdaten strukturiert abgelegt werden. Hier wird auch der Status (z.B. "erledigt") eines Anrufs gespeichert.

## 3. Kernfunktionen

- **Live-Dashboard:** Anzeige aller erfassten Anrufe in einer tabellarischen Übersicht.
- **Status-Update:** Anrufe können direkt im Dashboard als "erledigt" markiert werden. Der Status wird gespeichert und die Zeile zur visuellen Kenntlichmachung grün eingefärbt.
- **Client-seitige Suche:** Ein Suchfeld ermöglicht das Filtern der angezeigten Anrufe in Echtzeit.
- **Auto-Refresh:** Das Dashboard aktualisiert sich automatisch, um neue Anrufe anzuzeigen (aktuell alle 30 Sekunden).

## 4. Wichtige Dateien

- `webhook_server_dev.py`: Das **Entwicklungsskript**. Alle neuen Features und Änderungen werden hier implementiert und getestet.
- `webhook_server_prod.py`: Das **Produktionsskript**. Es repräsentiert die stabile, für den Einsatz freigegebene Version der Anwendung.
- `database.db`: Die SQLite-Datenbankdatei.
- `placetel_logs.jsonl`: Die Roh-Logdatei aller Webhook-Events.
- `call-dashboard-bauplan.md`: Das ursprüngliche, detaillierte Planungsdokument für die Architektur.
- `GEMINI.md`: Dokumentation über den Entwicklungsprozess mit dem Gemini-Agenten.

## 5. Anleitung zum Starten

Um die Anwendung (im Entwicklungsmodus) zu starten, folgen Sie diesen Schritten:

### Schritt 1: Voraussetzungen installieren

Stellen Sie sicher, dass Python 3 auf Ihrem System installiert ist. Installieren Sie dann die benötigte Python-Bibliothek mit `pip`:

```bash
pip install flask Flask-HTTPAuth
```

### Schritt 2: Entwicklungs-Server starten

Führen Sie das folgende Kommando in Ihrem Terminal aus:

```bash
python3 webhook_server_dev.py
```
Der Server startet, initialisiert die Datenbank (falls nicht vorhanden), importiert bestehende Logs und ist unter `http://localhost:54351` erreichbar.

### Schritt 3: Dashboard aufrufen

Öffnen Sie einen Webbrowser und navigieren Sie zu folgender Adresse:

[http://localhost:54351/dashboard](http://localhost:54351/dashboard)

### Schritt 4: Webhook mit Ngrok einrichten (Optional)

Um den lokalen Server für den Placetel-Webhook aus dem Internet erreichbar zu machen, benötigen Sie `ngrok`.

1.  Installieren Sie `ngrok` gemäß der offiziellen Anleitung.
2.  Öffnen Sie ein **zweites Terminalfenster** und führen Sie folgenden Befehl aus:
    ```bash
    ngrok http 54351
    ```
3.  `ngrok` zeigt Ihnen eine öffentliche URL an (z.B. `https://<zufall>.ngrok.io`). Diese URL müssen Sie in Ihrem Placetel-Account als Webhook-Ziel eintragen.

## 6. Entwicklungsprozess

Die Entwicklung folgt einem einfachen `dev` -> `prod` Modell:

1.  **Entwicklung:** Alle Änderungen werden ausschließlich in der `webhook_server_dev.py` vorgenommen.
2.  **Test:** Die Änderungen werden durch Ausführen des `dev`-Skripts und Testen im Browser validiert.
3.  **Übertragung (Deployment):** Wenn eine neue Version stabil ist und in den "Produktionseinsatz" übergehen soll, werden die Änderungen von der `dev`- in die `prod`-Datei übertragen. Dies geschieht durch einfaches Kopieren:

    ```bash
    cp webhook_server_dev.py webhook_server_prod.py
    ```
