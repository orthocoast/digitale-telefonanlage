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

## 4. Dashboard UI Verbesserungen

Das Dashboard wurde mit einer modernen und visuell ansprechenden Benutzeroberfläche neu gestaltet:

- **Farbiges modernes Design:** Gradienteneffekte und moderne Farbschemata für eine zeitgemäße Optik.
- **Statistik-Karten:** Übersichtliche Karten zeigen Gesamtzahl, offene Anrufe, erledigte Anrufe und heutige Anrufe auf einen Blick.
- **Verbesserte Tabelle:** Icons und Badges für bessere visuelle Kennzeichnung von Status und Informationen.
- **Live-Uhr in der Navigationsleiste:** Echtzeit-Uhrzeitanzeige für bessere Zeitverfolgung.
- **Sanfte Animationen:** Flüssige Übergänge und Animationen für eine bessere Benutzerfreundlichkeit.

## 5. Sicherheit und Konfiguration

Die Anwendung verwendet **Environment Variables** für sensible Konfigurationsdaten. Dies erhöht die Sicherheit, da keine Secrets im Quellcode gespeichert werden.

### Erforderliche Environment Variables

**Vor dem Start müssen folgende Variablen gesetzt werden:**

1. **PLACETEL_SECRET**: Das Bearer-Token für die Webhook-Authentifizierung von Placetel
2. **DASHBOARD_USERNAME**: Benutzername für den Dashboard-Zugang
3. **DASHBOARD_PASSWORD**: Passwort für den Dashboard-Zugang

### Einrichtung

Erstellen Sie eine `.env` Datei im Projektverzeichnis:

```bash
cp .env.example .env
```

Bearbeiten Sie die `.env` Datei und tragen Sie Ihre Werte ein:

```bash
PLACETEL_SECRET=ihr-webhook-secret-von-placetel
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=ein-sicheres-passwort
```

**Wichtig:** Die `.env` Datei wird nicht ins Git-Repository committed (ist in `.gitignore` ausgeschlossen).

### Laden der Environment Variables

**macOS/Linux:**
```bash
export $(cat .env | xargs)
python3 webhook_server_dev.py
```

**Oder mit einem Einzeiler:**
```bash
env $(cat .env | xargs) python3 webhook_server_dev.py
```

**Windows (PowerShell):**
```powershell
Get-Content .env | ForEach-Object {
    $name, $value = $_.split('=')
    Set-Item -Path "env:$name" -Value $value
}
python webhook_server_dev.py
```

### Sicherheitsverbesserungen

Die Anwendung implementiert folgende Sicherheitsmaßnahmen:

- **Keine hardcodierten Secrets** - Alle sensiblen Daten über Environment Variables
- **Webhook-Validierung** - Bearer-Token-Authentifizierung, Content-Type-Prüfung, JSON-Schema-Validierung
- **Dashboard-Schutz** - HTTP Basic Authentication für alle Dashboard- und API-Endpunkte
- **API-Absicherung** - Alle Status- und Delete-Endpunkte erfordern Authentifizierung
- **Error Handling** - Keine Offenlegung interner Details in Fehlermeldungen

## 6. Wichtige Dateien

- `webhook_server_dev.py`: Das **Entwicklungsskript**. Alle neuen Features und Änderungen werden hier implementiert und getestet.
- `webhook_server_prod.py`: Das **Produktionsskript**. Es repräsentiert die stabile, für den Einsatz freigegebene Version der Anwendung.
- `database.db`: Die SQLite-Datenbankdatei.
- `placetel_logs.jsonl`: Die Roh-Logdatei aller Webhook-Events.
- `.env.example`: Vorlage für die Konfigurationsdatei mit Environment Variables.
- `call-dashboard-bauplan.md`: Das ursprüngliche, detaillierte Planungsdokument für die Architektur.
- `GEMINI.md`: Dokumentation über den Entwicklungsprozess mit dem Gemini-Agenten.

## 7. Anleitung zum Starten

Um die Anwendung (im Entwicklungsmodus) zu starten, folgen Sie diesen Schritten:

### Schritt 1: Voraussetzungen installieren

Stellen Sie sicher, dass Python 3 auf Ihrem System installiert ist. Installieren Sie dann die benötigte Python-Bibliothek mit `pip`:

```bash
pip install flask Flask-HTTPAuth
```

### Schritt 2: Environment Variables konfigurieren

Erstellen Sie eine `.env` Datei mit Ihren Secrets (siehe Abschnitt 5 "Sicherheit und Konfiguration").

### Schritt 3: Entwicklungs-Server starten

Führen Sie das folgende Kommando in Ihrem Terminal aus:

```bash
env $(cat .env | xargs) python3 webhook_server_dev.py
```

Der Server startet, initialisiert die Datenbank (falls nicht vorhanden), importiert bestehende Logs und ist unter `http://localhost:54351` erreichbar.

**Hinweis:** Ohne korrekte Environment Variables wird der Server nicht starten und gibt eine Fehlermeldung aus.

### Schritt 4: Dashboard aufrufen

Öffnen Sie einen Webbrowser und navigieren Sie zu folgender Adresse:

[http://localhost:54351/dashboard](http://localhost:54351/dashboard)

Sie werden nach Benutzername und Passwort gefragt (die Sie in `.env` konfiguriert haben).

### Schritt 5: Webhook mit Ngrok einrichten (Optional)

Um den lokalen Server für den Placetel-Webhook aus dem Internet erreichbar zu machen, benötigen Sie `ngrok`.

1.  Installieren Sie `ngrok` gemäß der offiziellen Anleitung.
2.  Öffnen Sie ein **zweites Terminalfenster** und führen Sie folgenden Befehl aus:
    ```bash
    ngrok http 54351
    ```
3.  `ngrok` zeigt Ihnen eine öffentliche URL an (z.B. `https://<zufall>.ngrok.io`). Diese URL müssen Sie in Ihrem Placetel-Account als Webhook-Ziel eintragen.

## 7. Entwicklungsprozess

Die Entwicklung folgt einem einfachen `dev` -> `prod` Modell:

1.  **Entwicklung:** Alle Änderungen werden ausschließlich in der `webhook_server_dev.py` vorgenommen.
2.  **Test:** Die Änderungen werden durch Ausführen des `dev`-Skripts und Testen im Browser validiert.
3.  **Übertragung (Deployment):** Wenn eine neue Version stabil ist und in den "Produktionseinsatz" übergehen soll, werden die Änderungen von der `dev`- in die `prod`-Datei übertragen. Dies geschieht durch einfaches Kopieren:

    ```bash
    cp webhook_server_dev.py webhook_server_prod.py
    ```
