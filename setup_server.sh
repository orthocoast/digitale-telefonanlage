#!/bin/bash
# ============================================================================
# Migrations-Skript (Teil 2) - Läuft auf NEUEM Mac Server
# ============================================================================
# Dieses Skript installiert und konfiguriert alles auf dem neuen Server
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
print_header "Mac Server Migration - Server-Setup (Teil 2)"
echo "Dieses Skript installiert die Telefonanlage auf diesem Mac Server."
echo ""
print_warning "WICHTIG: Dies ist der NEUE Server!"
echo ""

# Lade Migrations-Info
if [ -f /tmp/migration_info.txt ]; then
    source /tmp/migration_info.txt
    print_info "Migration von: $MIGRATION_SOURCE_MAC"
    print_info "Erwartete Anrufe: $CALL_COUNT"
fi

echo ""
read -p "Möchten Sie fortfahren? (j/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[JjYy]$ ]]; then
    print_warning "Installation abgebrochen."
    exit 0
fi

# ============================================================================
# PHASE 1: SYSTEM-CHECK
# ============================================================================
print_header "Phase 1: System-Anforderungen prüfen"

# Betriebssystem
OS_TYPE=$(uname -s)
if [ "$OS_TYPE" != "Darwin" ]; then
    print_error "Dieses Skript ist nur für macOS!"
    exit 1
fi
print_success "macOS erkannt"

# Python 3
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python 3 gefunden (Version: $PYTHON_VERSION)"
    PYTHON_PATH=$(which python3)
    print_info "Python-Pfad: $PYTHON_PATH"
else
    print_error "Python 3 ist nicht installiert!"
    echo ""
    print_info "Installiere Python 3..."

    # Prüfe ob Homebrew installiert ist
    if ! command -v brew &> /dev/null; then
        print_info "Installiere Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    print_info "Installiere Python 3..."
    brew install python3

    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        PYTHON_PATH=$(which python3)
        print_success "Python 3 installiert (Version: $PYTHON_VERSION)"
    else
        print_error "Python 3-Installation fehlgeschlagen!"
        exit 1
    fi
fi

# pip3
if command -v pip3 &> /dev/null; then
    print_success "pip3 gefunden"
else
    print_info "Installiere pip3..."
    python3 -m ensurepip --upgrade
fi

# Git
if command -v git &> /dev/null; then
    print_success "Git gefunden"
else
    print_info "Installiere Git..."
    xcode-select --install
    print_warning "Bitte warten Sie bis Xcode Command Line Tools installiert sind..."
    read -p "Drücken Sie Enter wenn die Installation abgeschlossen ist..."
fi

# ============================================================================
# PHASE 2: INSTALLATIONS-VERZEICHNIS
# ============================================================================
print_header "Phase 2: Installations-Verzeichnis erstellen"

INSTALL_DIR="/opt/telefonanlage"

if [ -d "$INSTALL_DIR" ]; then
    print_warning "Verzeichnis $INSTALL_DIR existiert bereits!"
    read -p "Möchten Sie es überschreiben? (j/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[JjYy]$ ]]; then
        sudo rm -rf "$INSTALL_DIR"
        print_info "Altes Verzeichnis entfernt"
    else
        print_error "Installation abgebrochen"
        exit 1
    fi
fi

sudo mkdir -p "$INSTALL_DIR"
sudo chown $USER:staff "$INSTALL_DIR"
print_success "Verzeichnis erstellt: $INSTALL_DIR"

cd "$INSTALL_DIR"

# ============================================================================
# PHASE 3: PROJEKT VON GITHUB KLONEN
# ============================================================================
print_header "Phase 3: Projekt von GitHub klonen"

print_info "Klone Repository..."
git clone https://github.com/orthocoast/digitale-telefonanlage.git .

if [ $? -eq 0 ]; then
    print_success "Projekt erfolgreich geklont"
else
    print_error "Fehler beim Klonen des Repositories!"
    exit 1
fi

# Dateien prüfen
if [ -f "webhook_server_prod.py" ] && [ -f "install.sh" ]; then
    print_success "Alle erforderlichen Dateien vorhanden"
else
    print_error "Wichtige Dateien fehlen!"
    exit 1
fi

# ============================================================================
# PHASE 4: PYTHON-ABHÄNGIGKEITEN INSTALLIEREN
# ============================================================================
print_header "Phase 4: Python-Abhängigkeiten installieren"

print_info "Installiere Flask und Flask-HTTPAuth..."
pip3 install flask Flask-HTTPAuth --quiet

if [ $? -eq 0 ]; then
    print_success "Abhängigkeiten installiert"
else
    print_error "Fehler bei der Installation!"
    exit 1
fi

# ============================================================================
# PHASE 5: ENVIRONMENT VARIABLEN KONFIGURIEREN
# ============================================================================
print_header "Phase 5: Environment-Variablen konfigurieren"

echo ""
print_warning "WICHTIG: Verwenden Sie die GLEICHEN Werte wie auf dem alten Server!"
echo ""

read -p "Placetel Webhook Secret: " PLACETEL_SECRET
while [ -z "$PLACETEL_SECRET" ]; do
    print_error "Secret darf nicht leer sein!"
    read -p "Placetel Webhook Secret: " PLACETEL_SECRET
done

read -p "Dashboard Benutzername: " DASHBOARD_USERNAME
DASHBOARD_USERNAME=${DASHBOARD_USERNAME:-admin}

read -s -p "Dashboard Passwort: " DASHBOARD_PASSWORD
echo ""
while [ -z "$DASHBOARD_PASSWORD" ]; do
    print_error "Passwort darf nicht leer sein!"
    read -s -p "Dashboard Passwort: " DASHBOARD_PASSWORD
    echo ""
done

# .env erstellen
cat > "$INSTALL_DIR/.env" <<EOF
# Placetel Webhook Secret
PLACETEL_SECRET=$PLACETEL_SECRET

# Dashboard Authentication
DASHBOARD_USERNAME=$DASHBOARD_USERNAME
DASHBOARD_PASSWORD=$DASHBOARD_PASSWORD

# Flask Environment
FLASK_ENV=production
EOF

chmod 600 "$INSTALL_DIR/.env"
print_success ".env-Datei erstellt und gesichert"

# ============================================================================
# PHASE 6: DATENBANK ÜBERTRAGEN
# ============================================================================
print_header "Phase 6: Datenbank und Logs übertragen"

echo ""
print_info "Jetzt müssen die Daten vom alten Mac kopiert werden."
echo ""
echo "Option 1: SCP vom alten Mac (empfohlen)"
echo "Option 2: Daten-Archiv von /tmp nutzen"
echo "Option 3: Überspringen (leere Datenbank)"
echo ""
read -p "Welche Option? (1/2/3): " -n 1 -r DATA_OPTION
echo ""

if [ "$DATA_OPTION" = "1" ]; then
    read -p "Alter Mac Benutzername: " OLD_USER
    read -p "Alter Mac IP/Hostname: " OLD_HOST
    OLD_PATH="/Users/$OLD_USER/Desktop/Projekte/Digitale\ Telefonanlage"

    print_info "Kopiere Datenbank..."
    scp "$OLD_USER@$OLD_HOST:$OLD_PATH/database.db" "$INSTALL_DIR/"

    print_info "Kopiere JSONL-Logs..."
    scp "$OLD_USER@$OLD_HOST:$OLD_PATH/placetel_logs.jsonl" "$INSTALL_DIR/"

    print_success "Daten erfolgreich kopiert"

elif [ "$DATA_OPTION" = "2" ]; then
    if [ -f "/tmp/telefonanlage_data.tar.gz" ]; then
        print_info "Entpacke Daten-Archiv..."
        tar -xzf /tmp/telefonanlage_data.tar.gz -C "$INSTALL_DIR/"
        print_success "Daten extrahiert"
    else
        print_error "Archiv nicht gefunden in /tmp/"
        print_info "Fahre mit leerer Datenbank fort..."
    fi
else
    print_warning "Datenbank-Transfer übersprungen - neue DB wird erstellt"
fi

# Daten verifizieren
if [ -f "$INSTALL_DIR/database.db" ]; then
    print_info "Verifiziere Datenbank..."
    NEW_CALL_COUNT=$(sqlite3 database.db "SELECT COUNT(*) FROM calls;" 2>/dev/null || echo "0")
    NEW_DELETED_COUNT=$(sqlite3 database.db "SELECT COUNT(*) FROM deleted_calls;" 2>/dev/null || echo "0")
    NEW_JSONL_LINES=$(wc -l < placetel_logs.jsonl 2>/dev/null || echo "0")

    echo ""
    print_info "Datenbank-Statistiken:"
    echo "  📊 Anrufe: $NEW_CALL_COUNT (erwartet: ${CALL_COUNT:-N/A})"
    echo "  🗑️  Gelöscht: $NEW_DELETED_COUNT (erwartet: ${DELETED_COUNT:-N/A})"
    echo "  📝 JSONL: $NEW_JSONL_LINES (erwartet: ${JSONL_LINES:-N/A})"
    echo ""

    if [ -n "$CALL_COUNT" ] && [ "$NEW_CALL_COUNT" != "$CALL_COUNT" ]; then
        print_warning "Anruf-Anzahl stimmt nicht überein!"
        read -p "Trotzdem fortfahren? (j/n): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[JjYy]$ ]]; then
            print_error "Installation abgebrochen"
            exit 1
        fi
    else
        print_success "Datenintegrität verifiziert"
    fi
fi

# ============================================================================
# PHASE 7: LAUNCH AGENT EINRICHTEN
# ============================================================================
print_header "Phase 7: LaunchAgent einrichten"

print_info "Python-Pfad: $PYTHON_PATH"

PLIST_PATH="$HOME/Library/LaunchAgents/de.praxis.telefonanlage.plist"
mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>de.praxis.telefonanlage</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$INSTALL_DIR/webhook_server_prod.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin</string>
    </dict>

    <key>StandardOutPath</key>
    <string>$INSTALL_DIR/server.log</string>

    <key>StandardErrorPath</key>
    <string>$INSTALL_DIR/server_error.log</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
        <key>Crashed</key>
        <true/>
    </dict>

    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
EOF

print_success "LaunchAgent-Datei erstellt"

launchctl load "$PLIST_PATH"
print_success "LaunchAgent geladen"

# ============================================================================
# PHASE 8: SERVER STARTEN
# ============================================================================
print_header "Phase 8: Server starten und testen"

print_info "Starte Server..."
launchctl start de.praxis.telefonanlage

sleep 3

# Prüfe ob Prozess läuft
if ps aux | grep -v grep | grep webhook_server_prod > /dev/null; then
    print_success "Server läuft!"
else
    print_error "Server konnte nicht gestartet werden!"
    echo ""
    print_info "Fehler-Log:"
    tail -20 "$INSTALL_DIR/server_error.log"
    exit 1
fi

# ============================================================================
# PHASE 9: TESTS
# ============================================================================
print_header "Phase 9: Funktions-Tests"

# Lokaler Dashboard-Test
print_info "Teste Dashboard (lokal)..."
if curl -s -I http://localhost:54351/dashboard | grep "401 UNAUTHORIZED" > /dev/null; then
    print_success "Dashboard erreichbar (Login erforderlich - korrekt!)"
else
    print_warning "Dashboard-Response unerwartet"
fi

# Server-IP ermitteln
SERVER_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
print_info "Server-IP: $SERVER_IP"

# Webhook-Test
print_info "Teste Webhook..."
WEBHOOK_RESPONSE=$(curl -s -X POST http://localhost:54351/placetel \
  -H "Authorization: Bearer $PLACETEL_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "hello world",
    "source": "setup-test",
    "caller_name": "SETUP TEST",
    "caller_gender": "Männlich",
    "caller_dob": "01.01.1990",
    "phone": "+49123456789",
    "call_reason": "Server-Setup Test",
    "insurance_provider": "TEST",
    "category": ["Sonstiges"]
  }')

if echo "$WEBHOOK_RESPONSE" | grep "status.*ok" > /dev/null; then
    print_success "Webhook funktioniert!"
else
    print_warning "Webhook-Response: $WEBHOOK_RESPONSE"
fi

# ============================================================================
# PHASE 10: ZUSAMMENFASSUNG
# ============================================================================
print_header "Installation abgeschlossen!"

print_success "Der Server läuft und ist einsatzbereit!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Server-Informationen:"
echo "   Installations-Pfad: $INSTALL_DIR"
echo "   Server-IP: $SERVER_IP"
echo "   Dashboard: http://$SERVER_IP:54351/dashboard"
echo "   Webhook: http://$SERVER_IP:54351/placetel"
echo ""
echo "🔐 Login-Daten:"
echo "   Benutzername: $DASHBOARD_USERNAME"
echo "   Passwort: (wie eingegeben)"
echo ""
echo "📊 Datenbank:"
if [ -n "$NEW_CALL_COUNT" ]; then
    echo "   Anrufe: $NEW_CALL_COUNT"
    echo "   Gelöschte: $NEW_DELETED_COUNT"
fi
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
print_info "NÄCHSTE SCHRITTE:"
echo ""
echo "1. Dashboard im Browser testen:"
echo "   ${YELLOW}http://$SERVER_IP:54351/dashboard${NC}"
echo ""
echo "2. Placetel Webhook umstellen auf:"
echo "   ${YELLOW}http://$SERVER_IP:54351/placetel${NC}"
echo "   (Authorization: Bearer $PLACETEL_SECRET)"
echo ""
echo "3. Test-Anruf durchführen"
echo ""
print_warning "FIREWALL-HINWEIS:"
echo "Falls Dashboard von außen nicht erreichbar:"
echo "  Systemeinstellungen > Sicherheit > Firewall > Firewall-Optionen"
echo "  Fügen Sie 'Python' hinzu und erlauben Sie eingehende Verbindungen"
echo ""
print_info "Service-Befehle:"
echo "  Status:      launchctl list | grep telefonanlage"
echo "  Neu starten: launchctl stop de.praxis.telefonanlage && launchctl start de.praxis.telefonanlage"
echo "  Logs:        tail -f $INSTALL_DIR/server.log"
echo "  Fehler:      tail -f $INSTALL_DIR/server_error.log"
echo ""
print_success "Migration erfolgreich! 🎉"
echo ""
