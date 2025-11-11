from flask import Flask, request, jsonify, render_template_string, Response
import json
import time
import pathlib
import sqlite3
from datetime import datetime
import os
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

# --- Konfiguration ---
PORT = 54351
SECRET = "inmeinemgarten" # Placetel Secret - bleibt vorerst hardcoded
LOG_FILE = pathlib.Path(__file__).with_name("placetel_logs.jsonl")
DB_FILE = pathlib.Path(__file__).with_name("database.db")

# --- Dashboard Authentifizierung ---
auth = HTTPBasicAuth()

DASHBOARD_USERNAME = os.environ.get('DASHBOARD_USERNAME', 'admin')
DASHBOARD_PASSWORD = os.environ.get('DASHBOARD_PASSWORD', 'password')

@auth.verify_password
def verify_password(username, password):
    if username == DASHBOARD_USERNAME and password == DASHBOARD_PASSWORD:
        return username
    return None

@auth.error_handler
def auth_error(status):
    return Response("Zugriff verweigert. Bitte melden Sie sich an.", 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

# --- HTML-Vorlage ---
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Anruf-Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {
            --primary-color: #007bff;
            --primary-light: #e6f2ff;
            --light-grey: #f8f9fa;
            --medium-grey: #dee2e6;
            --dark-grey: #343a40;
            --text-color: #212529;
            --success-bg: #e7f5e9;
            --success-text: #1d7a2e;
            --danger-color: #dc3545;
            --danger-light: #f8d7da;
            --white: #fff;
            --shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            background-color: var(--light-grey);
            color: var(--text-color);
            line-height: 1.6;
        }
        .container {
            max-width: 1400px;
            margin: 2em auto;
            padding: 2.5em;
            background-color: var(--white);
            border-radius: 16px;
            box-shadow: var(--shadow);
        }
        .header {
            display: flex;
            align-items: center;
            margin-bottom: 1.5em;
        }
        .header svg {
            color: var(--primary-color);
            margin-right: 0.5em;
        }
        h1 {
            color: var(--dark-grey);
            margin: 0;
            font-size: 2em;
        }
        #search-box {
            width: 100%;
            padding: 12px 15px;
            font-size: 16px;
            border-radius: 8px;
            border: 1px solid var(--medium-grey);
            box-sizing: border-box;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        #search-box:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.25);
        }
        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin-top: 2em;
        }
        th, td {
            padding: 16px 20px;
            border-bottom: 1px solid var(--medium-grey);
            vertical-align: middle;
        }
        thead th {
            background: linear-gradient(180deg, #fdfdff, #f1f3f5);
            font-weight: 600;
            color: var(--dark-grey);
            text-align: left;
        }
        thead th .icon {
            margin-right: 8px;
            vertical-align: -3px;
            opacity: 0.6;
        }
        thead th:first-child { border-top-left-radius: 12px; }
        thead th:last-child { border-top-right-radius: 12px; }
        tbody tr {
            transition: background-color 0.2s ease-in-out;
        }
        tbody tr:hover {
            background-color: var(--primary-light);
        }
        .no-results {
            text-align: center;
            padding: 40px;
            color: #6c757d;
        }
        tr[data-status="done"] {
            background-color: var(--success-bg) !important;
        }
        tr[data-status="done"] td {
            color: var(--success-text);
            text-decoration: line-through;
            opacity: 0.7;
        }
        .status-checkbox {
            cursor: pointer;
            width: 18px;
            height: 18px;
        }
        .delete-btn {
            background: none;
            border: none;
            cursor: pointer;
            padding: 5px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .delete-btn:hover {
            background-color: var(--danger-light);
        }
        .delete-btn svg {
            color: var(--danger-color);
            width: 18px;
            height: 18px;
        }
    </style>
</head>
<body>
    <main class="container">
        <div class="header">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" viewBox="0 0 16 16"><path d="M8 3.5a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-1 0v-1a.5.5 0 0 1 .5-.5zM7.5 6a.5.5 0 0 1 .5.5v3a.5.5 0 0 1-1 0v-3a.5.5 0 0 1 .5-.5z"/><path d="M4 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H4zm0 1h8a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1z"/></svg>
            <h1>Anruf-Dashboard</h1>
        </div>
        <div class="controls">
            <input type="search" id="search-box" placeholder="Tabelle durchsuchen...">
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Erledigt</th>
                    <th>Zeitpunkt</th>
                    <th>Name</th>
                    <th>Geburtsdatum</th>
                    <th>Telefonnummer</th>
                    <th>Anliegen</th>
                    <th>Löschen</th>
                </tr>
            </thead>
            <tbody>
                {% for call in calls %}
                <tr data-id="{{ call.id }}" data-status="{{ call.status }}">
                    <td><input type="checkbox" class="status-checkbox" {% if call.status == 'done' %}checked{% endif %}></td>
                    <td>{{ call.timestamp | format_ts }}</td>
                    <td>{{ call.caller_name }}</td>
                    <td>{{ call.caller_dob }}</td>
                    <td>{{ call.phone }}</td>
                    <td>{{ call.call_reason }}</td>
                    <td>
                        <button class="delete-btn">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/><path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/></svg>
                        </button>
                    </td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="7" class="no-results">Noch keine Anrufe in der Datenbank.</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </main>

    <script>
        // --- Suchfunktion ---
        const searchBox = document.getElementById('search-box');
        const tableBody = document.querySelector('table tbody');
        const rows = tableBody.getElementsByTagName('tr');

        searchBox.addEventListener('keyup', function() {
            const filter = searchBox.value.toLowerCase();
            for (let i = 0; i < rows.length; i++) {
                const cells = rows[i].getElementsByTagName('td');
                if (cells.length > 1) {
                    let found = false;
                    for (let j = 1; j < cells.length; j++) {
                        if (cells[j].textContent.toLowerCase().indexOf(filter) > -1) {
                            found = true;
                            break;
                        }
                    }
                    rows[i].style.display = found ? "" : "none";
                }
            }
        });

        // --- Event Delegation für dynamische Inhalte ---
        tableBody.addEventListener('click', function(event) {
            // --- "Erledigt"-Funktion ---
            if (event.target.classList.contains('status-checkbox')) {
                const checkbox = event.target;
                const callId = checkbox.closest('tr').dataset.id;
                const isDone = checkbox.checked;
                
                fetch(`/call/${callId}/status`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: isDone ? 'done' : 'new' })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'ok') {
                        const row = checkbox.closest('tr');
                        row.dataset.status = isDone ? 'done' : 'new';
                    } else {
                        alert("Fehler beim Speichern des Status.");
                        checkbox.checked = !isDone;
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert("Netzwerkfehler beim Speichern des Status.");
                    checkbox.checked = !isDone;
                });
            }

            // --- "Löschen"-Funktion ---
            if (event.target.closest('.delete-btn')) {
                const deleteBtn = event.target.closest('.delete-btn');
                const row = deleteBtn.closest('tr');
                const callId = row.dataset.id;
                const callName = row.cells[2].textContent;

                if (confirm(`Sind Sie sicher, dass Sie den Anruf von "${callName}" endgültig löschen möchten?`)) {
                    fetch(`/call/${callId}/delete`, {
                        method: 'POST', // Using POST for simplicity
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'ok') {
                            row.style.transition = 'opacity 0.5s ease';
                            row.style.opacity = '0';
                            setTimeout(() => row.remove(), 500);
                        } else {
                            alert("Fehler beim Löschen des Anrufs.");
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert("Netzwerkfehler beim Löschen des Anrufs.");
                    });
                }
            }
        });
        
        // --- Auto-Reload ---
        setTimeout(() => { window.location.reload(); }, 30000);
    </script>
</body>
</html>
"""

# --- Datenbankfunktionen ---
def get_db():
    """Stellt eine Verbindung zur DB her und gibt ein Connection-Objekt zurück."""
    db = sqlite3.connect(DB_FILE)
    db.row_factory = sqlite3.Row  # Ermöglicht den Zugriff auf Spalten per Namen
    return db

def init_db():
    """Initialisiert die Datenbank und erstellt die Tabelle, falls sie nicht existiert."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        log_ts REAL UNIQUE NOT NULL,
        status TEXT NOT NULL DEFAULT 'new',
        timestamp INTEGER,
        caller_name TEXT,
        caller_gender TEXT,
        caller_dob TEXT,
        phone TEXT,
        call_reason TEXT,
        insurance_provider TEXT
    );
    """)
    db.commit()
    db.close()
    print("Datenbank initialisiert.")

def import_logs_to_db():
    """Importiert neue Einträge aus der JSONL-Datei in die Datenbank."""
    if not LOG_FILE.exists():
        return

    db = get_db()
    cursor = db.cursor()
    
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            
            try:
                log_entry = json.loads(line)
                log_ts = log_entry.get("ts")
                if not log_ts: continue

                cursor.execute("SELECT id FROM calls WHERE log_ts = ?", (log_ts,))
                if cursor.fetchone() is not None:
                    continue

                body = log_entry.get("body", {})
                cursor.execute("""
                INSERT INTO calls (log_ts, timestamp, caller_name, caller_gender, caller_dob, phone, call_reason, insurance_provider)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    log_ts,
                    int(log_ts),
                    body.get("caller_name"),
                    body.get("caller_gender"),
                    body.get("caller_dob"),
                    body.get("phone"),
                    body.get("call_reason"),
                    body.get("insurance_provider")
                ))
                print(f"Neuer Anruf von {body.get('caller_name')} importiert.")
            except json.JSONDecodeError:
                print(f"Fehler beim Parsen einer Zeile in der Log-Datei: {line}")
    
    db.commit()
    db.close()


# --- Flask Routen ---
@app.template_filter('format_ts')
def format_timestamp(ts):
    """Jinja-Filter, um den Timestamp zu formatieren."""
    if ts is None:
        return "N/A"
    return datetime.fromtimestamp(ts).strftime('%d.%m.%Y %H:%M:%S')

@app.post("/placetel")
def placetel_webhook():
    """Empfängt den Webhook, schreibt ins Log und in die DB."""
    if request.headers.get("Authorization") != f"Bearer {SECRET}":
        return jsonify({"error": "forbidden"}), 403
    
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "bad request"}), 400

    log_ts = time.time()
    log_entry = {"ts": log_ts, "body": data}

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
    INSERT INTO calls (log_ts, timestamp, caller_name, caller_gender, caller_dob, phone, call_reason, insurance_provider)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        log_ts,
        int(log_ts),
        data.get("caller_name"),
        data.get("caller_gender"),
        data.get("caller_dob"),
        data.get("phone"),
        data.get("call_reason"),
        data.get("insurance_provider")
    ))
    db.commit()
    db.close()
    
    return jsonify({"status": "ok"}), 200

@app.get("/")
def health_check():
    return jsonify({"ok": True}), 200

@app.get("/dashboard")
@auth.login_required
def dashboard():
    """Zeigt das Dashboard mit Daten aus der SQLite-DB."""
    db = get_db()
    calls = db.execute("SELECT * FROM calls ORDER BY timestamp DESC").fetchall()
    db.close()
    return render_template_string(DASHBOARD_TEMPLATE, calls=calls)

@app.post("/call/<int:call_id>/status")
def update_call_status(call_id):
    """Aktualisiert den Status eines Anrufs (new/done)."""
    data = request.get_json()
    new_status = data.get("status")

    if new_status not in ['new', 'done']:
        return jsonify({"status": "error", "message": "Invalid status"}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE calls SET status = ? WHERE id = ?", (new_status, call_id))
    db.commit()
    
    if cursor.rowcount == 0:
        db.close()
        return jsonify({"status": "error", "message": "Call not found"}), 404
    
    db.close()
    return jsonify({"status": "ok"})

@app.post("/call/<int:call_id>/delete")
def delete_call(call_id):
    """Löscht einen Anruf aus der Datenbank."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM calls WHERE id = ?", (call_id,))
    db.commit()

    if cursor.rowcount == 0:
        db.close()
        return jsonify({"status": "error", "message": "Call not found"}), 404

    db.close()
    return jsonify({"status": "ok"})

@app.post("/import-logs")
def trigger_import():
    """Manueller Endpunkt, um den Import aus der JSONL-Datei anzustoßen."""
    import_logs_to_db()
    return jsonify({"status": "ok", "message": "Import finished."})


if __name__ == "__main__":
    init_db()
    import_logs_to_db()
    app.run(host="0.0.0.0", port=PORT, debug=True)