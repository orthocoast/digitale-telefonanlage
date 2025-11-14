#!/bin/bash
# ============================================================================
# Migrations-Skript (Teil 1) - Läuft auf AKTUELLEM Mac
# ============================================================================
# Dieses Skript bereitet die Migration vor und kopiert Daten zum neuen Server
# ============================================================================

set -e  # Bei Fehler abbrechen

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }

# ============================================================================
# WILLKOMMEN
# ============================================================================
clear
print_header "Mac Server Migration - Vorbereitung (Teil 1)"
echo "Dieses Skript bereitet die Migration auf den neuen Mac Server vor."
echo "Es dokumentiert den aktuellen Stand und kopiert die Daten."
echo ""
print_warning "WICHTIG: Der alte Server läuft während der Migration weiter!"
echo ""

# Ins Projekt-Verzeichnis wechseln
cd "/Users/bwl/Desktop/Projekte/Digitale Telefonanlage"

# ============================================================================
# PHASE 1: AKTUELLEN STAND DOKUMENTIEREN
# ============================================================================
print_header "Phase 1: Aktuellen Stand dokumentieren"

print_info "Erstelle Migrations-Report..."

REPORT_FILE="migration_report_$(date +%Y%m%d_%H%M%S).txt"

cat > "$REPORT_FILE" <<EOF
================================================================================
MIGRATIONS-REPORT - $(date)
================================================================================

ENVIRONMENT VARIABLEN:
----------------------
EOF

cat .env >> "$REPORT_FILE"

cat >> "$REPORT_FILE" <<EOF

DATENBANK-STATISTIKEN:
----------------------
EOF

sqlite3 database.db "SELECT COUNT(*) FROM calls;" >> "$REPORT_FILE" 2>&1 || echo "Fehler beim Lesen" >> "$REPORT_FILE"
sqlite3 database.db "SELECT COUNT(*) FROM deleted_calls;" >> "$REPORT_FILE" 2>&1 || echo "Keine gelöschten Anrufe" >> "$REPORT_FILE"

echo "" >> "$REPORT_FILE"
echo "JSONL-EINTRÄGE:" >> "$REPORT_FILE"
wc -l placetel_logs.jsonl >> "$REPORT_FILE"

echo "" >> "$REPORT_FILE"
echo "DATEIGRÖSSEN:" >> "$REPORT_FILE"
ls -lh database.db placetel_logs.jsonl >> "$REPORT_FILE"

print_success "Report erstellt: $REPORT_FILE"

# Zeige wichtige Zahlen
print_info "Aktuelle Statistiken:"
CALL_COUNT=$(sqlite3 database.db "SELECT COUNT(*) FROM calls;")
DELETED_COUNT=$(sqlite3 database.db "SELECT COUNT(*) FROM deleted_calls;" 2>/dev/null || echo "0")
JSONL_LINES=$(wc -l < placetel_logs.jsonl)

echo "  📊 Anrufe in DB: $CALL_COUNT"
echo "  🗑️  Gelöschte Anrufe: $DELETED_COUNT"
echo "  📝 JSONL-Zeilen: $JSONL_LINES"
echo ""

# ============================================================================
# PHASE 2: GIT STATUS PRÜFEN
# ============================================================================
print_header "Phase 2: Git-Status prüfen"

if git status &>/dev/null; then
    if git diff-index --quiet HEAD --; then
        print_success "Git: Alles committed und aktuell"
    else
        print_warning "Es gibt uncommitted Änderungen!"
        echo ""
        git status --short
        echo ""
        read -p "Möchten Sie committen und pushen? (j/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[JjYy]$ ]]; then
            git add .
            git commit -m "Pre-migration commit"
            git push
            print_success "Änderungen committed und gepusht"
        else
            print_warning "Fahre ohne commit fort..."
        fi
    fi
else
    print_error "Git-Repository nicht gefunden!"
    exit 1
fi

# ============================================================================
# PHASE 3: SERVER-VERBINDUNG TESTEN
# ============================================================================
print_header "Phase 3: Server-Verbindung testen"

echo "Bitte geben Sie die Zugangsdaten für den neuen Mac Server ein:"
echo ""
read -p "Server IP-Adresse: " SERVER_IP
read -p "Benutzername: " SERVER_USER

print_info "Teste SSH-Verbindung zu $SERVER_USER@$SERVER_IP..."

if ssh -o ConnectTimeout=5 -o BatchMode=yes "$SERVER_USER@$SERVER_IP" exit 2>/dev/null; then
    print_success "SSH-Verbindung erfolgreich (Key-basiert)"
else
    print_warning "SSH-Key-Authentifizierung fehlgeschlagen, versuche Passwort..."
    if ssh -o ConnectTimeout=10 "$SERVER_USER@$SERVER_IP" exit; then
        print_success "SSH-Verbindung erfolgreich (Passwort)"
    else
        print_error "SSH-Verbindung fehlgeschlagen!"
        echo ""
        echo "Bitte prüfen Sie:"
        echo "  - Ist die IP-Adresse korrekt?"
        echo "  - Ist 'Remote Login' am Server aktiviert?"
        echo "    (Systemeinstellungen > Sharing > Remote Login)"
        exit 1
    fi
fi

# ============================================================================
# PHASE 4: SETUP-SKRIPT AUF SERVER KOPIEREN
# ============================================================================
print_header "Phase 4: Setup-Skript auf Server kopieren"

print_info "Kopiere setup_server.sh zum Server..."

scp setup_server.sh "$SERVER_USER@$SERVER_IP:/tmp/"

print_success "Setup-Skript kopiert"

# ============================================================================
# PHASE 5: DATENBANK UND LOGS KOPIEREN
# ============================================================================
print_header "Phase 5: Datenbank und Logs vorbereiten"

print_warning "WICHTIG: Die Daten werden NACH der Server-Installation kopiert!"
print_info "Das setup_server.sh Skript wird Sie danach fragen."
echo ""

# Erstelle ein tar-Archiv für einfacheren Transfer
print_info "Erstelle Daten-Archiv..."
tar -czf /tmp/telefonanlage_data.tar.gz database.db placetel_logs.jsonl

print_success "Daten-Archiv erstellt: /tmp/telefonanlage_data.tar.gz"

# ============================================================================
# PHASE 6: ZUSAMMENFASSUNG UND NÄCHSTE SCHRITTE
# ============================================================================
print_header "Phase 6: Zusammenfassung"

print_success "Vorbereitung abgeschlossen!"
echo ""
echo "Migrations-Report: $REPORT_FILE"
echo "Server: $SERVER_USER@$SERVER_IP"
echo ""
print_info "NÄCHSTE SCHRITTE:"
echo ""
echo "1. Loggen Sie sich auf dem Server ein:"
echo "   ${YELLOW}ssh $SERVER_USER@$SERVER_IP${NC}"
echo ""
echo "2. Führen Sie das Setup-Skript aus:"
echo "   ${YELLOW}chmod +x /tmp/setup_server.sh${NC}"
echo "   ${YELLOW}/tmp/setup_server.sh${NC}"
echo ""
echo "3. Das Skript wird Sie durch die Installation führen"
echo ""
print_warning "Der alte Server läuft weiter - keine Sorge!"
echo ""

# ============================================================================
# AUTOMATISCHER SSH + SETUP (OPTIONAL)
# ============================================================================
echo ""
read -p "Möchten Sie sich jetzt direkt auf dem Server einloggen? (j/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[JjYy]$ ]]; then
    print_info "Verbinde mit Server und starte Setup..."
    echo ""
    print_warning "Nach dem Login führen Sie aus: chmod +x /tmp/setup_server.sh && /tmp/setup_server.sh"
    echo ""
    sleep 2

    # Speichere Server-Info für setup_server.sh
    echo "MIGRATION_SOURCE_MAC=$USER@$(hostname)" > /tmp/migration_info.txt
    echo "MIGRATION_DATE=$(date)" >> /tmp/migration_info.txt
    echo "CALL_COUNT=$CALL_COUNT" >> /tmp/migration_info.txt
    echo "DELETED_COUNT=$DELETED_COUNT" >> /tmp/migration_info.txt
    echo "JSONL_LINES=$JSONL_LINES" >> /tmp/migration_info.txt

    scp /tmp/migration_info.txt "$SERVER_USER@$SERVER_IP:/tmp/"

    ssh -t "$SERVER_USER@$SERVER_IP"
else
    print_info "OK - Sie können sich später manuell verbinden"
fi

echo ""
print_success "Migrations-Vorbereitung abgeschlossen!"
echo ""
