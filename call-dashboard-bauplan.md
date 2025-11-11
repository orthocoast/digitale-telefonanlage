# Bauplan: Anrufdaten-Dashboard
*Stand: 2025-11-10*

## 1. Ziel & Nutzen
**Ziel:** Mitarbeitende sehen auf einen Blick eingehende Anrufe (wer, Anliegen, Nummer, Geburtsdatum, etc.), können filtern/suchen und den Status je Anruf auf *Erledigt* setzen.  
**Nutzen:** Schneller Überblick, saubere Nachverfolgung, revisionssichere Historie, DSGVO-konform.

## 2. Anforderungen (funktional)
- **Anzeigen** einer Tabelle mit Spalten: Zeitpunkt, Name/Nummer, Anliegen, Geburtsdatum (optional), Quelle/Priorität, Status, Zugewiesen an, Letzte Änderung.
- **Suche & Filter**: Zeitraum, Status, Name/Nummer, Stichworte im Anliegen.
- **Aktionen** pro Eintrag: *Erledigt markieren*, *Zuweisen*, *Notiz hinzufügen*.
- **Echtzeit-Aktualisierung** bei neuen Anrufen/Änderungen.
- **Rollen & Rechte**: Agent (lesen/ändern), Admin (konfigurieren/auswerten).
- **Historie/Audit**: Wer hat wann was geändert?

## 3. Anforderungen (nicht-funktional)
- **Performance:** < 300 ms API-Antwortzeit für List/Filter bei bis zu 100k Datensätzen.
- **Verfügbarkeit:** Ziel 99,9% (Bürozeiten-kritisch).
- **Skalierung:** Wachsendes Volumen (Partitionierung/Archivierung vorgesehen).
- **Sicherheit & DSGVO:** PII-Schutz, Verschlüsselung at rest, Rollen, Protokollierung, Lösch-/Export-Prozesse.
- **Beobachtbarkeit:** Metriken, Logs, Alerts.

## 4. Architektur (High Level)
```
JSONL (append-only, Rohlog)  →  Importer/Worker  →  PostgreSQL (Operativdaten)
                                               ↘  Dead-Letter/Fehler
UI (Web)  ←→  Backend API (REST/GraphQL)  ←→  PostgreSQL
               ↑             ↑
            SSE/WebSocket    Auth (RBAC)
```
**Prinzip:** JSONL bleibt als Audit-Quelle; operative Arbeit in Postgres. Status-Änderungen ausschließlich über die API (transaktional).

## 5. Datenfluss & Ingestion
1. **Detection:** Importer überwacht JSONL (Offset gemerkt).
2. **Validierung:** Pflichtfelder, Formate (Datum/Telefon), Normalisierung.
3. **Deduplizierung:** stabiler Event-Key (`event_id` oder Hash aus Timestamp+Nummer+Payload).
4. **Upsert:** in `calls` (neu/Update). Anpassungen idempotent.
5. **Fehlerpfad:** ungültige Events → Dead-Letter-Tabelle + Alert.
6. **Realtime:** Nach erfolgreichem Upsert → Event an UI (SSE/WebSocket).

## 6. Datenmodell (schematisch, ohne Code)
**Tabelle `calls`**
- `id` (PK), `event_id` (unique), `received_at` (UTC), `caller_number`, `caller_name` (optional)
- `date_of_birth` (optional), `topic` (Anliegen), `priority` (optional), `source`
- `status` (enum: NEW, IN_PROGRESS, DONE)
- `assignee_id` (FK users, optional), `updated_at`
- `raw_payload` (JSONB, Originaldaten)

**Tabelle `call_status`** (Status-Historie)
- `id`, `call_id` (FK), `status` (enum), `changed_by` (FK users), `changed_at`, `comment` (optional)

**Tabelle `users`**
- `id`, `name`, `email`, `role` (AGENT|ADMIN), `created_at`, `is_active`

**Tabelle `actions_audit`** (generische Historie)
- `id`, `call_id`, `action_type` (status_change|edit|note), `actor_id`, `occurred_at`, `diff` (JSONB)

**Indexes (Minimum)**
- `calls(received_at)`, `calls(status)`, `calls(caller_number)`
- Volltext/GIN auf `topic` und optional Notizen
- Eindeutig auf `event_id`

**Partitionierung/Archiv**
- Zeitbasierte Partition auf `received_at` (monatlich) bei großem Volumen.
- `calls_archive` für alte erledigte Fälle nach X Monaten.

## 7. API-Entwurf (ohne Implementierung)
**Auth:** JWT/OIDC, Rollenprüfung serverseitig.  
**Ratenbegrenzung:** Schutz vor Missbrauch.

- `GET /calls`
  - Query: `q`, `status`, `from`, `to`, `assignee`, `page`, `page_size`, `sort`
  - Antwort: Liste (paginiert) + Meta (Total, Page, etc.)
- `GET /calls/<built-in function id>`
  - Antwort: Call-Objekt inkl. letzte Status-Historie.
- `PATCH /calls/<built-in function id>/status`
  - Body: `status`, `comment` (optional), `version` (optimist. Lock)
  - Effekt: Neuer Eintrag in `call_status`, Update `calls.status`.
- `POST /calls/<built-in function id>/notes`
  - Body: `note`
  - Effekt: Eintrag in `actions_audit`.
- `POST /calls/<built-in function id>/assign`
  - Body: `assignee_id`
  - Effekt: Update `calls.assignee_id`, Audit-Eintrag.
- **Echtzeit:** `GET /events/stream` (SSE) oder WebSocket-Kanal `calls`

## 8. UI/UX-Konzept
- **Tabelle** mit fixierbaren Spalten, Badge für Status, Avatar/Initialen für Zuständigkeit.
- **Schnellfilter:** Heute/Letzte Stunde/Offen/Meine.
- **Globale Suche** (Name, Nummer, Anliegen).
- **Inline-Aktion:** *Erledigt* (mit Undo), *Zuweisen*, *Notiz*.
- **Detail-Drawer:** vollständige Daten, Historie, Rohpayload (read-only).
- **Bulk-Aktionen:** mehrere Einträge auswählen und Status ändern/zuweisen.
- **Leerzustände & Fehlerstates** klar gestaltet.

## 9. Sicherheit & DSGVO
- **Datenminimierung:** nur notwendige PII speichern; Aufbewahrungsfristen definieren.
- **Verschlüsselung:** at rest (DB/Disk), in transit (TLS). Gegebenenfalls Feldverschlüsselung (z. B. Geburtsdatum).
- **RBAC:** Rollen, Least Privilege, Admin-Operationen getrennt protokollieren.
- **Protokollierung:** Zugriffe/Änderungen an PII auditieren.
- **Betroffenenrechte:** Export/Löschung einzelner Datensätze umsetzbar.
- **Maskierung im UI:** z. B. Teile der Nummer nur für Rollen sichtbar.
- **Backups & Tests:** regelmäßige Wiederherstellungstests, Schlüsselrotation.

## 10. Betrieb & Qualität
- **Monitoring:** Import-Lag, Dead-Letter-Anzahl, API-Latenzen, Fehlerquoten, DB-Health.
- **Alerts:** Schwellenwerte (z. B. >1% Importfehler, >1s Latenz P95).
- **Backups:** täglich, Aufbewahrung 30–90 Tage.
- **CI/CD:** Linting, Tests, Datenbankmigrationen, Zero-Downtime-Deploy.
- **Observability:** strukturierte Logs, Tracing, Metriken (OpenTelemetry).
- **Konfiguration:** Priorisierungsregeln (VIP-Nummern, Keywords), Eskalation.

## 11. Meilensteine (empfohlen)
1. **MVP (2–3 Wochen)**
   - Postgres-Schema + Importer (JSONL → DB, idempotent).
   - API: `GET /calls`, `PATCH /calls/{id}/status`.
   - UI: Tabelle, Filter (Status/Zeitraum), *Erledigt*-Button.
2. **Phase 2**
   - Historie/Audit, Zuweisen, Notizen, Volltextsuche.
   - SSE/WebSockets für Live-Updates.
3. **Phase 3**
   - KPIs/Kacheln, Archivierung, Partitionierung, RBAC-Feinschliff.
   - DSGVO-Exports/Löschprozesse, erweiterte Monitoring/Alerts.

## 12. Akzeptanzkriterien (Auszug)
- Neue Anrufe erscheinen ohne Reload binnen ≤ 5 s.
- „Erledigt“-Aktion ist idempotent und auditierbar.
- Suche nach Nummer/Name liefert Ergebnisse in ≤ 1 s (P95) bei 100k Datensätzen.
- Alle Änderungen sind einem Nutzer zuordenbar (Audit vollständig).
- DSGVO-Check: Export/Löschung pro Datensatz nachweisbar.
- Backups wiederherstellbar (regelmäßig getestet).

## 13. Risiken & Mitigations
- **Doppelte Events:** strikter `event_id`-Unique + idempotente Upserts.
- **Rennen bei Statuswechsel:** optimistisches Locking (`version`/`updated_at`).
- **Leistungseinbruch bei Wachstum:** Indizes, Partitionierung, Archivierung.
- **DSGVO-Verstöße:** Privacy by Design, Rollen, Monitoring, Schulung.
- **Formatänderungen JSONL:** Versionierung im Rohpayload, Schemaprüfungen.

## 14. Glossar
- **JSONL:** JSON Lines, eine Zeile = ein Event (append-only).
- **Upsert:** Insert oder Update, abhängig von vorhandener Kennung.
- **SSE:** Server-Sent Events, unidirektionaler Realtime-Stream vom Server.
- **RBAC:** Role-Based Access Control.
- **PII:** Personenbezogene Daten.

---

## 15. LLM Integration (GDPR-konform)

Für die Nachbearbeitung oder Analyse von Anrufdaten mittels Large Language Models (LLMs) ist ausschließlich die folgende, DSGVO-konforme Schnittstelle zu verwenden:

**Ollama API Endpunkt:**
`OLLAMA_URL = "http://{tomedo_server_host}:{tomedo_server_port}/{tomedo_server_db}/llmservice/{userIdent}/v1/chat/completions"`

**Standardmodell:**
`MODEL = os.environ.get("USER_MODEL", "gemini-2.5-flash")`

Diese Konfiguration stellt sicher, dass alle LLM-Interaktionen innerhalb der definierten und kontrollierten Umgebung stattfinden und den Datenschutzanforderungen entsprechen.

---

### Checkliste (Kurz)
- [ ] Postgres-Schema angelegt (calls, call_status, users, actions_audit)
- [ ] Importer mit Offset, Validierung, Deduplizierung, Upsert
- [ ] API: List, Details, Statuswechsel (+ Auth, RBAC)
- [ ] UI: Tabelle, Filter, Erledigt-Button, Detail-Drawer
- [ ] Realtime: SSE/WebSocket
- [ ] Audit & DSGVO-Prozesse
- [ ] Monitoring, Backups, Alerts


## 15. Retention & Löschung (30 Tage)
**Ziel:** Operative Daten (inkl. PII) werden maximal **30 Tage** gespeichert und anschließend nachweisbar gelöscht. JSONL-Rohlogs werden ebenfalls nur 30 Tage aufbewahrt.

### 15.1 Grundsätze
- **Datenminimierung:** Nur für die operative Bearbeitung notwendige PII speichern (keine medizinischen Inhalte).
- **Zeitbezug:** Alle Zeitstempel in **UTC** speichern; Anzeige im UI in lokaler Zeitzone (Europe/Berlin).
- **Legal Check:** Prüfen, ob es rechtliche Anforderungen an Aufbewahrung/Löschung von Anrufdaten gibt (Abgrenzung zu medizinischer Dokumentation).

### 15.2 DB-TTL (SQLite)
- **Purge-Job täglich** (z. B. nachts): löscht alle `calls` mit `received_at < now() - 30 Tage`.
- **Kaskaden:** Fremdschlüssel mit **ON DELETE CASCADE** oder sequentielle Löschung in `call_status`/`actions_audit`.
- **VACUUM/ANALYZE:** Nach größeren Löschläufen (z. B. wöchentlich/monatlich) zur Dateigrößenrückgewinnung und Statistikpflege.
- **API-Garantie:** Endpunkte geben nur Datensätze der letzten 30 Tage zurück (Server-seitige Filter erzwingen Policy).

### 15.3 JSONL-Rohlog (Audit)
- **Rotation:** Täglich neue Datei (z. B. `calls-YYYY-MM-DD.jsonl`); Importer verfolgt Offsets pro Datei.
- **Aufbewahrung:** maximal 30 Dateien (30 Tage), automatische **Löschung** älterer Dateien.
- **Sicheres Löschen:** Datenträger-verschlüsselt betreiben; auf SSDs ist Überschreiben nicht zuverlässig → **Best Practice:** Verschlüsselung + Löschen der Schlüssel bzw. Standard-Delete innerhalb verschlüsselter Partition.
- **Fehlerpfad:** Dead-Letter-Ordner mit gleicher 30-Tage-Policy.

### 15.4 Backups & Wiederherstellung
- **Backup-Retention = 30 Tage** (spiegelt Löschpolicy, um „Wiederauftauchen“ alter PII zu verhindern).
- **Verschlüsselung:** Backups verschlüsseln; Schlüssel-Management dokumentieren.
- **Restore-Tests:** mindestens quartalsweise; sicherstellen, dass nach Restore sofort die TTL-Policy greift (Post-Restore-Purge).

### 15.5 Aggregation vor Löschung (optional)
- Vor dem Purge **anonymisierte/aggregierte Kennzahlen** erzeugen (z. B. Anrufe/Tag, Gründe, Wartezeit), ohne PII zu bewahren.
- Aggregationsspeicher (separate Tabelle/Datei) **ohne** personenbezogene Felder.

### 15.6 Sonderfälle & Rechte
- **Vorzeitige Löschung** auf Anfrage (Recht auf Vergessenwerden): einzelne `call`-Datensätze inkl. Historie vollständig entfernen.
- **Sperrvermerke:** Falls rechtlich erforderlich, statt Löschung **Sperrung** (Soft-Delete + Zugriffssperre) umsetzbar – bevorzugt jedoch echte Löschung bei 30-Tage-Policy.

### 15.7 Monitoring & Nachweis
- **Metriken:** Anzahl gelöschter Datensätze/Tag, verbleibende Datensätze > 30 Tage (sollte 0 sein), Fehler beim Purge.
- **Audit-Log:** Protokolliere Purge-Läufe (Start/Ende, Anzahl, Erfolg/Fehler) zur Nachweisführung.
