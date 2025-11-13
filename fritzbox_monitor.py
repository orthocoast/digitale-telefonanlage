#!/usr/bin/env python3
"""
FritzBox Call Monitor Integration
==================================

Dieses Script verbindet sich mit dem FritzBox Call Monitor und erfasst
eingehende Anrufe mit der ECHTEN Telefonnummer des Anrufers - BEVOR
die Rufnummerweiterleitung zu Placetel erfolgt.

Die echten Nummern werden in einer Lookup-Tabelle gespeichert, sodass
sie später den Webhook-Daten von Placetel zugeordnet werden können.

Verwendung:
    python3 fritzbox_monitor.py

Voraussetzungen:
    - FritzBox Call Monitor muss aktiviert sein: #96*5*
    - FritzBox muss im Netzwerk erreichbar sein
"""

import socket
import time
import sqlite3
import pathlib
from datetime import datetime
import sys

# --- Konfiguration ---
FRITZBOX_IP = "192.168.100.1"  # Deine FritzBox IP
FRITZBOX_PORT = 1012  # Call Monitor Port
PRAXIS_NUMBER = "200893"  # Deine Praxisnummer

DB_FILE = pathlib.Path(__file__).with_name("database.db")
LOG_FILE = pathlib.Path(__file__).with_name("fritzbox_calls.log")

# --- Logging ---
def log(message):
    """Schreibt eine Log-Nachricht mit Timestamp."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"[{timestamp}] {message}"
    print(log_message)

    # Optional: In Datei schreiben
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_message + "\n")

# --- Datenbank ---
def get_db():
    """Verbindung zur SQLite-Datenbank."""
    db = sqlite3.connect(DB_FILE)
    db.row_factory = sqlite3.Row
    return db

def create_lookup_table():
    """Erstellt die Lookup-Tabelle für Telefonnummern."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS phone_lookup (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp INTEGER NOT NULL,
        caller_number TEXT NOT NULL,
        called_number TEXT NOT NULL,
        matched INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Index für schnelle Suche
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_timestamp ON phone_lookup(timestamp)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_matched ON phone_lookup(matched)
    """)

    db.commit()
    db.close()
    log("✓ Lookup-Tabelle erstellt/geprüft")

def save_caller_number(caller_number, called_number):
    """Speichert die echte Anrufernummer in der Lookup-Tabelle."""
    db = get_db()
    cursor = db.cursor()

    timestamp = int(time.time())

    # DUPLIKATS-FILTER: Verhindere mehrfache Speicherung der gleichen Nummer
    # FritzBox sendet oft mehrere RING-Events pro Anruf (bei jedem Klingelton!)
    # Prüfe ob diese Nummer in den letzten 10 Sekunden bereits gespeichert wurde
    duplicate_window = 10  # Sekunden
    min_timestamp = timestamp - duplicate_window

    # BEGIN IMMEDIATE: Atomische Transaktion gegen Race Conditions
    try:
        db.execute("BEGIN IMMEDIATE")

        cursor.execute("""
        SELECT id FROM phone_lookup
        WHERE caller_number = ?
        AND timestamp >= ?
        LIMIT 1
        """, (caller_number, min_timestamp))

        if cursor.fetchone() is not None:
            db.rollback()
            db.close()
            log(f"🔄 Duplikat ignoriert: {caller_number} (bereits gespeichert)")
            return

        # Nummer ist neu → speichern
        cursor.execute("""
        INSERT INTO phone_lookup (timestamp, caller_number, called_number)
        VALUES (?, ?, ?)
        """, (timestamp, caller_number, called_number))

        db.commit()
        db.close()

        log(f"📞 Anruf gespeichert: {caller_number} → {called_number}")

    except Exception as e:
        db.rollback()
        db.close()
        log(f"❌ Fehler beim Speichern: {e}")

def cleanup_old_entries():
    """Löscht alte Lookup-Einträge (älter als 24 Stunden)."""
    db = get_db()
    cursor = db.cursor()

    # Älter als 24 Stunden
    cutoff_time = int(time.time()) - (24 * 60 * 60)

    cursor.execute("""
    DELETE FROM phone_lookup
    WHERE timestamp < ? AND matched = 1
    """, (cutoff_time,))

    deleted_count = cursor.rowcount
    if deleted_count > 0:
        log(f"🗑️  {deleted_count} alte Einträge gelöscht")

    db.commit()
    db.close()

# --- Call Monitor Parser ---
def parse_call_monitor_line(line):
    """
    Parst eine Zeile vom FritzBox Call Monitor.

    Format RING (eingehender Anruf):
    Datum;RING;ConnectionID;CallerNumber;CalledNumber;SIPnumber;

    Beispiel:
    01.01.25 10:30:00;RING;0;0151234567890;200893;SIP0;
    """
    try:
        parts = line.strip().split(';')

        if len(parts) < 6:
            return None

        event_type = parts[1]

        # Nur RING Events (eingehende Anrufe) interessieren uns
        if event_type == "RING":
            caller_number = parts[3]  # Anrufernummer
            called_number = parts[4]  # Angerufene Nummer

            return {
                'type': 'RING',
                'caller': caller_number,
                'called': called_number,
                'timestamp': parts[0]
            }

        return None

    except Exception as e:
        log(f"⚠️  Fehler beim Parsen: {e}")
        return None

# --- FritzBox Verbindung ---
def connect_to_fritzbox():
    """Verbindet sich mit dem FritzBox Call Monitor."""
    log(f"🔄 Verbinde mit FritzBox auf {FRITZBOX_IP}:{FRITZBOX_PORT}...")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10 Sekunden Timeout
        sock.connect((FRITZBOX_IP, FRITZBOX_PORT))
        log(f"✅ Verbunden mit FritzBox Call Monitor!")
        return sock

    except socket.timeout:
        log(f"❌ Timeout: Keine Verbindung zur FritzBox")
        return None

    except ConnectionRefusedError:
        log(f"❌ Verbindung verweigert. Ist der Call Monitor aktiviert? (#96*5*)")
        return None

    except Exception as e:
        log(f"❌ Fehler bei Verbindung: {e}")
        return None

def monitor_calls():
    """Hauptschleife: Überwacht Anrufe von der FritzBox."""
    log("🚀 FritzBox Call Monitor gestartet")
    log(f"📋 Praxisnummer: {PRAXIS_NUMBER}")
    log(f"💾 Datenbank: {DB_FILE}")
    log("")
    log("Warte auf Anrufe...")
    log("(Drücke Ctrl+C zum Beenden)")
    log("")

    # Lookup-Tabelle erstellen
    create_lookup_table()

    retry_count = 0
    max_retries = 5

    while True:
        try:
            sock = connect_to_fritzbox()

            if not sock:
                retry_count += 1
                if retry_count >= max_retries:
                    log(f"❌ Max. Verbindungsversuche erreicht ({max_retries})")
                    log("💡 Prüfe:")
                    log("   1. Ist Call Monitor aktiviert? (#96*5*)")
                    log("   2. Ist die FritzBox-IP korrekt? (aktuell: {FRITZBOX_IP})")
                    log("   3. Läuft eine Firewall?")
                    sys.exit(1)

                wait_time = min(2 ** retry_count, 60)  # Exponentieller Backoff, max 60s
                log(f"⏳ Warte {wait_time} Sekunden vor erneutem Versuch...")
                time.sleep(wait_time)
                continue

            # Verbindung erfolgreich - Reset retry counter
            retry_count = 0

            # Buffer für empfangene Daten
            buffer = ""

            # Cleanup-Timer (alle 10 Minuten)
            last_cleanup = time.time()
            cleanup_interval = 600  # 10 Minuten

            while True:
                try:
                    # Daten empfangen
                    data = sock.recv(1024).decode('utf-8', errors='ignore')

                    if not data:
                        log("⚠️  Verbindung getrennt")
                        break

                    buffer += data

                    # Zeilen verarbeiten
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)

                        if line.strip():
                            call_data = parse_call_monitor_line(line)

                            if call_data:
                                # Nur Anrufe zur Praxisnummer speichern
                                if PRAXIS_NUMBER in call_data['called']:
                                    save_caller_number(
                                        call_data['caller'],
                                        call_data['called']
                                    )

                    # Periodisches Cleanup
                    if time.time() - last_cleanup > cleanup_interval:
                        cleanup_old_entries()
                        last_cleanup = time.time()

                except socket.timeout:
                    # Timeout ist OK - warte weiter
                    continue

                except KeyboardInterrupt:
                    log("\n⚠️  Beendet durch Benutzer")
                    sock.close()
                    sys.exit(0)

                except Exception as e:
                    log(f"⚠️  Fehler beim Empfangen: {e}")
                    break

            # Verbindung geschlossen - neu verbinden
            sock.close()
            log("🔄 Versuche erneut zu verbinden...")
            time.sleep(5)

        except KeyboardInterrupt:
            log("\n⚠️  Beendet durch Benutzer")
            sys.exit(0)

        except Exception as e:
            log(f"❌ Unerwarteter Fehler: {e}")
            time.sleep(5)

# --- Hilfsfunktion für Webhook-Server ---
def find_real_phone_number(webhook_timestamp, time_window=300):
    """
    Sucht die echte Telefonnummer für einen Webhook-Zeitpunkt.

    Diese Funktion verwendet FIFO (First In, First Out) Matching:
    - Nimmt immer den ÄLTESTEN ungematchten Anruf
    - Verhindert dass mehrere Webhooks die gleiche Nummer bekommen
    - Funktioniert wie eine Warteschlange

    Args:
        webhook_timestamp: Unix-Timestamp des Webhooks (nur für Zeitfenster-Prüfung)
        time_window: Maximales Zeitfenster in Sekunden (default: 5 Minuten)

    Returns:
        Echte Telefonnummer oder None
    """
    db = get_db()
    cursor = db.cursor()

    # Zeitfenster: Nur Anrufe der letzten X Minuten berücksichtigen
    # (verhindert uralte Einträge zu matchen)
    min_time = webhook_timestamp - time_window

    # FIFO: Nimm den ÄLTESTEN ungematchten Eintrag (ORDER BY id ASC)
    # Nicht nach Zeitstempel-Nähe, sondern strikt nach Reihenfolge!
    cursor.execute("""
    SELECT id, caller_number, timestamp
    FROM phone_lookup
    WHERE timestamp >= ?
    AND matched = 0
    ORDER BY id ASC
    LIMIT 1
    """, (min_time,))

    result = cursor.fetchone()

    if result:
        entry_id = result[0]
        caller_number = result[1]

        # Als "matched" markieren (wichtig: per ID, nicht timestamp!)
        cursor.execute("""
        UPDATE phone_lookup
        SET matched = 1
        WHERE id = ?
        """, (entry_id,))

        db.commit()
        db.close()

        log(f"🔗 Echte Nummer gefunden (FIFO #{entry_id}): {caller_number}")
        return caller_number

    db.close()
    return None

# --- Main ---
if __name__ == "__main__":
    try:
        monitor_calls()
    except KeyboardInterrupt:
        log("\n⚠️  Programm beendet")
        sys.exit(0)
