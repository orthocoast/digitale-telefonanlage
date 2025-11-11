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

# Security: Secrets must be provided via environment variables
SECRET = os.environ.get('PLACETEL_SECRET')
if not SECRET:
    raise ValueError("PLACETEL_SECRET environment variable is required. Please set it before starting the server.")

LOG_FILE = pathlib.Path(__file__).with_name("placetel_logs.jsonl")
DB_FILE = pathlib.Path(__file__).with_name("database.db")

# --- Dashboard Authentifizierung ---
auth = HTTPBasicAuth()

# Security: Dashboard credentials must be provided via environment variables (no defaults)
DASHBOARD_USERNAME = os.environ.get('DASHBOARD_USERNAME')
DASHBOARD_PASSWORD = os.environ.get('DASHBOARD_PASSWORD')
if not DASHBOARD_USERNAME or not DASHBOARD_PASSWORD:
    raise ValueError("DASHBOARD_USERNAME and DASHBOARD_PASSWORD environment variables are required. Please set them before starting the server.")

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
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --success-gradient: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            --info-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            --warning-gradient: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            --danger-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);

            --primary-color: #667eea;
            --primary-light: #f0f3ff;
            --success-color: #38ef7d;
            --success-bg: #d4ffe9;
            --success-text: #0d6832;
            --info-color: #00f2fe;
            --warning-color: #feca57;
            --danger-color: #f5576c;
            --danger-light: #ffe6ea;

            --light-grey: #f7f9fc;
            --medium-grey: #e1e8ed;
            --dark-grey: #2c3e50;
            --text-color: #2c3e50;
            --white: #fff;

            --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.08);
            --shadow-md: 0 4px 20px rgba(0, 0, 0, 0.12);
            --shadow-lg: 0 8px 30px rgba(0, 0, 0, 0.15);
        }

        * {
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            background-attachment: fixed;
            color: var(--text-color);
            line-height: 1.6;
            min-height: 100vh;
        }

        .navbar {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 1.2rem 2rem;
            box-shadow: var(--shadow-md);
            position: sticky;
            top: 0;
            z-index: 1000;
            border-bottom: 3px solid transparent;
            border-image: var(--primary-gradient) 1;
        }

        .navbar-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .navbar-title {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .navbar-icon {
            width: 48px;
            height: 48px;
            background: var(--primary-gradient);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
            box-shadow: var(--shadow-sm);
            animation: pulse 2s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }

        .navbar h1 {
            margin: 0;
            font-size: 1.8rem;
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
        }

        .navbar-time {
            color: var(--dark-grey);
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .container {
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 2rem 2rem;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: var(--white);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: var(--shadow-md);
            position: relative;
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: var(--shadow-lg);
        }

        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--card-gradient);
        }

        .stat-card.total::before {
            background: var(--info-gradient);
        }

        .stat-card.new::before {
            background: var(--warning-gradient);
        }

        .stat-card.done::before {
            background: var(--success-gradient);
        }

        .stat-card.today::before {
            background: var(--primary-gradient);
        }

        .stat-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.5rem;
        }

        .stat-icon {
            width: 50px;
            height: 50px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            color: white;
        }

        .stat-card.total .stat-icon {
            background: var(--info-gradient);
        }

        .stat-card.new .stat-icon {
            background: var(--warning-gradient);
        }

        .stat-card.done .stat-icon {
            background: var(--success-gradient);
        }

        .stat-card.today .stat-icon {
            background: var(--primary-gradient);
        }

        .stat-content h3 {
            margin: 0 0 0.25rem;
            font-size: 0.85rem;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }

        .stat-content .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .main-content {
            background: var(--white);
            border-radius: 20px;
            padding: 2rem;
            box-shadow: var(--shadow-lg);
        }

        .search-container {
            margin-bottom: 2rem;
            position: relative;
        }

        .search-icon {
            position: absolute;
            left: 1rem;
            top: 50%;
            transform: translateY(-50%);
            color: #6c757d;
            font-size: 1.2rem;
            pointer-events: none;
        }

        #search-box {
            width: 100%;
            padding: 1rem 1rem 1rem 3rem;
            font-size: 1rem;
            border-radius: 12px;
            border: 2px solid var(--medium-grey);
            background: var(--white);
            transition: all 0.3s ease;
        }

        #search-box:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
        }

        .table-container {
            overflow-x: auto;
            border-radius: 12px;
            box-shadow: var(--shadow-sm);
        }

        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
        }

        th, td {
            padding: 1rem 1.25rem;
            text-align: left;
            border-bottom: 1px solid var(--medium-grey);
        }

        thead th {
            background: var(--primary-gradient);
            color: var(--white);
            font-weight: 600;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            position: sticky;
            top: 0;
            z-index: 10;
        }

        thead th:first-child {
            border-top-left-radius: 12px;
        }

        thead th:last-child {
            border-top-right-radius: 12px;
        }

        thead th i {
            margin-right: 0.5rem;
        }

        tbody tr {
            background: var(--white);
            transition: all 0.3s ease;
        }

        tbody tr:hover {
            background: var(--primary-light);
            transform: scale(1.01);
            box-shadow: var(--shadow-sm);
        }

        tbody tr:last-child td:first-child {
            border-bottom-left-radius: 12px;
        }

        tbody tr:last-child td:last-child {
            border-bottom-right-radius: 12px;
        }

        tr[data-status="new"] {
            border-left: 4px solid #feca57;
        }

        tr[data-status="done"] {
            background: var(--success-bg) !important;
            border-left: 4px solid var(--success-color);
            opacity: 0.7;
        }

        tr[data-status="done"] td {
            color: var(--success-text);
        }

        .status-checkbox {
            cursor: pointer;
            width: 22px;
            height: 22px;
            accent-color: var(--success-color);
            transition: transform 0.2s ease;
        }

        .status-checkbox:hover {
            transform: scale(1.2);
        }

        .phone-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.4rem 0.8rem;
            background: var(--info-gradient);
            color: white;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 500;
        }

        .reason-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.4rem 0.8rem;
            background: linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%);
            color: var(--dark-grey);
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 500;
        }

        .category-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.4rem 0.8rem;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 500;
            box-shadow: 0 2px 4px rgba(240, 147, 251, 0.2);
        }

        .name-cell {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .name-icon {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: var(--primary-gradient);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.9rem;
        }

        .delete-btn {
            background: var(--danger-gradient);
            border: none;
            cursor: pointer;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: white;
            transition: all 0.3s ease;
            box-shadow: var(--shadow-sm);
        }

        .delete-btn:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }

        .delete-btn i {
            font-size: 1rem;
        }

        .no-results {
            text-align: center;
            padding: 3rem;
            color: #6c757d;
        }

        .no-results i {
            font-size: 3rem;
            margin-bottom: 1rem;
            display: block;
            opacity: 0.5;
        }

        .time-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.4rem 0.8rem;
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 500;
            color: var(--dark-grey);
        }

        @media (max-width: 768px) {
            .navbar {
                padding: 1rem;
            }

            .navbar-content {
                flex-direction: column;
                gap: 1rem;
            }

            .container {
                padding: 0 1rem 1rem;
            }

            .stats-grid {
                grid-template-columns: 1fr;
            }

            .main-content {
                padding: 1rem;
            }

            table {
                font-size: 0.9rem;
            }

            th, td {
                padding: 0.75rem;
            }
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .stat-card, tbody tr {
            animation: slideIn 0.5s ease-out;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="navbar-content">
            <div class="navbar-title">
                <div class="navbar-icon">
                    <i class="bi bi-telephone-fill"></i>
                </div>
                <h1>Anruf-Dashboard</h1>
            </div>
            <div class="navbar-time">
                <i class="bi bi-clock-fill"></i>
                <span id="current-time"></span>
            </div>
        </div>
    </nav>

    <div class="container">
        <div class="stats-grid">
            <div class="stat-card total">
                <div class="stat-header">
                    <div class="stat-content">
                        <h3>Gesamt Anrufe</h3>
                        <p class="stat-number" id="total-calls">{{ calls|length }}</p>
                    </div>
                    <div class="stat-icon">
                        <i class="bi bi-telephone-inbound"></i>
                    </div>
                </div>
            </div>

            <div class="stat-card new">
                <div class="stat-header">
                    <div class="stat-content">
                        <h3>Offen</h3>
                        <p class="stat-number" id="new-calls">{{ calls|selectattr('status', 'equalto', 'new')|list|length }}</p>
                    </div>
                    <div class="stat-icon">
                        <i class="bi bi-exclamation-circle-fill"></i>
                    </div>
                </div>
            </div>

            <div class="stat-card done">
                <div class="stat-header">
                    <div class="stat-content">
                        <h3>Erledigt</h3>
                        <p class="stat-number" id="done-calls">{{ calls|selectattr('status', 'equalto', 'done')|list|length }}</p>
                    </div>
                    <div class="stat-icon">
                        <i class="bi bi-check-circle-fill"></i>
                    </div>
                </div>
            </div>

            <div class="stat-card today">
                <div class="stat-header">
                    <div class="stat-content">
                        <h3>Heute</h3>
                        <p class="stat-number" id="today-calls">0</p>
                    </div>
                    <div class="stat-icon">
                        <i class="bi bi-calendar-check-fill"></i>
                    </div>
                </div>
            </div>
        </div>

        <div class="main-content">
            <div class="search-container">
                <i class="bi bi-search search-icon"></i>
                <input type="search" id="search-box" placeholder="Nach Name, Telefonnummer oder Anliegen suchen...">
            </div>

            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th><i class="bi bi-check2-square"></i>Erledigt</th>
                            <th><i class="bi bi-clock-history"></i>Zeitpunkt</th>
                            <th><i class="bi bi-person-fill"></i>Name</th>
                            <th><i class="bi bi-calendar3"></i>Geburtsdatum</th>
                            <th><i class="bi bi-telephone-fill"></i>Telefonnummer</th>
                            <th><i class="bi bi-chat-left-text-fill"></i>Anliegen</th>
                            <th><i class="bi bi-tags-fill"></i>Kategorie</th>
                            <th><i class="bi bi-trash3"></i>Löschen</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for call in calls %}
                        <tr data-id="{{ call.id }}" data-status="{{ call.status }}" data-timestamp="{{ call.timestamp }}">
                            <td><input type="checkbox" class="status-checkbox" {% if call.status == 'done' %}checked{% endif %}></td>
                            <td><span class="time-badge"><i class="bi bi-clock"></i>{{ call.timestamp | format_ts }}</span></td>
                            <td>
                                <div class="name-cell">
                                    <div class="name-icon">{{ call.caller_name[:1] if call.caller_name else '?' }}</div>
                                    <strong>{{ call.caller_name }}</strong>
                                </div>
                            </td>
                            <td>{{ call.caller_dob }}</td>
                            <td><span class="phone-badge"><i class="bi bi-phone"></i>{{ call.phone }}</span></td>
                            <td><span class="reason-badge"><i class="bi bi-chat-dots"></i>{{ call.call_reason }}</span></td>
                            <td>
                                {% if call.category %}
                                <span class="category-badge"><i class="bi bi-tags"></i>{{ call.category }}</span>
                                {% else %}
                                <span style="color: #999;">-</span>
                                {% endif %}
                            </td>
                            <td>
                                <button class="delete-btn">
                                    <i class="bi bi-trash3-fill"></i>
                                </button>
                            </td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="8" class="no-results">
                                <i class="bi bi-inbox"></i>
                                <p>Noch keine Anrufe in der Datenbank.</p>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // --- Live Clock ---
        function updateClock() {
            const now = new Date();
            const timeString = now.toLocaleTimeString('de-DE', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            const dateString = now.toLocaleDateString('de-DE', {
                weekday: 'short',
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
            document.getElementById('current-time').textContent = `${dateString} - ${timeString}`;
        }
        updateClock();
        setInterval(updateClock, 1000);

        // --- Count Today's Calls ---
        function countTodayCalls() {
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const todayTimestamp = today.getTime() / 1000;

            const rows = document.querySelectorAll('tbody tr[data-timestamp]');
            let count = 0;
            rows.forEach(row => {
                const timestamp = parseInt(row.dataset.timestamp);
                if (timestamp >= todayTimestamp) {
                    count++;
                }
            });

            document.getElementById('today-calls').textContent = count;
        }
        countTodayCalls();

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
                        // Update statistics
                        const newCount = document.querySelectorAll('tr[data-status="new"]').length;
                        const doneCount = document.querySelectorAll('tr[data-status="done"]').length;
                        document.getElementById('new-calls').textContent = newCount;
                        document.getElementById('done-calls').textContent = doneCount;
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
                const nameCell = row.querySelector('.name-cell strong');
                const callName = nameCell ? nameCell.textContent : 'diesen Anruf';

                if (confirm(`Sind Sie sicher, dass Sie den Anruf von "${callName}" endgültig löschen möchten?`)) {
                    fetch(`/call/${callId}/delete`, {
                        method: 'POST',
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'ok') {
                            row.style.transition = 'opacity 0.5s ease';
                            row.style.opacity = '0';
                            setTimeout(() => {
                                row.remove();
                                // Update statistics
                                const totalCount = document.querySelectorAll('tbody tr[data-id]').length;
                                const newCount = document.querySelectorAll('tr[data-status="new"]').length;
                                const doneCount = document.querySelectorAll('tr[data-status="done"]').length;
                                document.getElementById('total-calls').textContent = totalCount;
                                document.getElementById('new-calls').textContent = newCount;
                                document.getElementById('done-calls').textContent = doneCount;
                                countTodayCalls();
                            }, 500);
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
        insurance_provider TEXT,
        category TEXT
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

                # Extract category (comes as array, store as comma-separated string)
                category_data = body.get("category")
                category_str = None
                if category_data:
                    if isinstance(category_data, list):
                        category_str = ", ".join(category_data)
                    else:
                        category_str = str(category_data)

                cursor.execute("""
                INSERT INTO calls (log_ts, timestamp, caller_name, caller_gender, caller_dob, phone, call_reason, insurance_provider, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    log_ts,
                    int(log_ts),
                    body.get("caller_name"),
                    body.get("caller_gender"),
                    body.get("caller_dob"),
                    body.get("phone"),
                    body.get("call_reason"),
                    body.get("insurance_provider"),
                    category_str
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
    # Security: Verify Bearer token
    if request.headers.get("Authorization") != f"Bearer {SECRET}":
        return jsonify({"error": "forbidden"}), 403

    # Security: Verify Content-Type
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    # Security: Parse JSON with error handling
    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({"error": "Invalid JSON", "details": str(e)}), 400

    if not data:
        return jsonify({"error": "Empty request body"}), 400

    # Security: Validate required fields (basic schema validation)
    # At minimum, we should have some caller information
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    log_ts = time.time()
    log_entry = {"ts": log_ts, "body": data}

    try:
        # Write to log file
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        # Write to database
        db = get_db()
        cursor = db.cursor()

        # Extract category (comes as array, store as comma-separated string)
        category_data = data.get("category")
        category_str = None
        if category_data:
            if isinstance(category_data, list):
                category_str = ", ".join(category_data)
            else:
                category_str = str(category_data)

        cursor.execute("""
        INSERT INTO calls (log_ts, timestamp, caller_name, caller_gender, caller_dob, phone, call_reason, insurance_provider, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log_ts,
            int(log_ts),
            data.get("caller_name"),
            data.get("caller_gender"),
            data.get("caller_dob"),
            data.get("phone"),
            data.get("call_reason"),
            data.get("insurance_provider"),
            category_str
        ))
        db.commit()
        db.close()

        return jsonify({"status": "ok", "log_ts": log_ts}), 200

    except Exception as e:
        # Log error but don't expose internal details to client
        print(f"Error processing webhook: {e}")
        return jsonify({"error": "Internal server error"}), 500

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
@auth.login_required
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
@auth.login_required
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
@auth.login_required
def trigger_import():
    """Manueller Endpunkt, um den Import aus der JSONL-Datei anzustoßen."""
    import_logs_to_db()
    return jsonify({"status": "ok", "message": "Import finished."})


if __name__ == "__main__":
    init_db()
    import_logs_to_db()
    app.run(host="0.0.0.0", port=PORT, debug=True)