#!/bin/bash
# ============================================================================
# Digitale Telefonanlage - Installationsskript
# ============================================================================
# Dieses Skript installiert und konfiguriert die digitale Telefonanlage
# auf einem neuen Server/Rechner.
# ============================================================================

set -e  # Bei Fehler abbrechen

# Farben für Ausgaben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funktionen für formatierte Ausgaben
print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# ============================================================================
# 1. WILLKOMMENSNACHRICHT
# ============================================================================
clear
print_header "Digitale Telefonanlage - Installation"
echo "Dieses Skript wird die digitale Telefonanlage auf diesem System einrichten."
echo "Bitte stellen Sie sicher, dass Sie über Administratorrechte verfügen."
echo ""
read -p "Möchten Sie fortfahren? (j/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[JjYy]$ ]]; then
    print_warning "Installation abgebrochen."
    exit 0
fi

# ============================================================================
# 2. SYSTEMANFORDERUNGEN PRÜFEN
# ============================================================================
print_header "Systemanforderungen prüfen"

# Betriebssystem erkennen
OS_TYPE=$(uname -s)
print_info "Betriebssystem: $OS_TYPE"

# Python 3 prüfen
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python 3 gefunden (Version: $PYTHON_VERSION)"
else
    print_error "Python 3 ist nicht installiert!"
    echo ""
    echo "Bitte installieren Sie Python 3:"
    if [[ "$OS_TYPE" == "Darwin" ]]; then
        echo "  brew install python3"
    elif [[ "$OS_TYPE" == "Linux" ]]; then
        echo "  sudo apt-get install python3 python3-pip   # Debian/Ubuntu"
        echo "  sudo yum install python3 python3-pip       # CentOS/RHEL"
    fi
    exit 1
fi

# pip prüfen
if command -v pip3 &> /dev/null; then
    print_success "pip3 gefunden"
else
    print_error "pip3 ist nicht installiert!"
    echo ""
    echo "Bitte installieren Sie pip3:"
    if [[ "$OS_TYPE" == "Darwin" ]]; then
        echo "  curl https://bootstrap.pypa.io/get-pip.py | python3"
    elif [[ "$OS_TYPE" == "Linux" ]]; then
        echo "  sudo apt-get install python3-pip   # Debian/Ubuntu"
        echo "  sudo yum install python3-pip       # CentOS/RHEL"
    fi
    exit 1
fi

# ============================================================================
# 3. INSTALLATIONSVERZEICHNIS
# ============================================================================
print_header "Installationsverzeichnis"

INSTALL_DIR=$(pwd)
print_info "Aktuelles Verzeichnis: $INSTALL_DIR"
echo ""
echo "Die Anwendung wird in diesem Verzeichnis installiert."
read -p "Möchten Sie ein anderes Verzeichnis verwenden? (j/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[JjYy]$ ]]; then
    read -p "Bitte geben Sie den vollständigen Pfad ein: " INSTALL_DIR
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

print_success "Installationsverzeichnis: $INSTALL_DIR"

# ============================================================================
# 4. PYTHON-ABHÄNGIGKEITEN INSTALLIEREN
# ============================================================================
print_header "Python-Abhängigkeiten installieren"

print_info "Installiere Flask und Flask-HTTPAuth..."
pip3 install flask Flask-HTTPAuth --quiet

if [ $? -eq 0 ]; then
    print_success "Abhängigkeiten erfolgreich installiert"
else
    print_error "Fehler bei der Installation der Abhängigkeiten"
    exit 1
fi

# ============================================================================
# 5. KONFIGURATIONSDATEI (.env) ERSTELLEN
# ============================================================================
print_header "Konfiguration einrichten"

if [ -f "$INSTALL_DIR/.env" ]; then
    print_warning ".env-Datei existiert bereits"
    read -p "Möchten Sie die bestehende Konfiguration überschreiben? (j/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[JjYy]$ ]]; then
        print_info ".env-Datei wird beibehalten"
        ENV_SKIP=true
    fi
fi

if [ -z "$ENV_SKIP" ]; then
    echo ""
    echo "Bitte geben Sie die folgenden Konfigurationswerte ein:"
    echo ""

    # Placetel Secret
    read -p "Placetel Webhook Secret: " PLACETEL_SECRET
    while [ -z "$PLACETEL_SECRET" ]; do
        print_error "Placetel Secret darf nicht leer sein!"
        read -p "Placetel Webhook Secret: " PLACETEL_SECRET
    done

    # Dashboard Username
    read -p "Dashboard Benutzername [admin]: " DASHBOARD_USERNAME
    DASHBOARD_USERNAME=${DASHBOARD_USERNAME:-admin}

    # Dashboard Password
    read -s -p "Dashboard Passwort: " DASHBOARD_PASSWORD
    echo ""
    while [ -z "$DASHBOARD_PASSWORD" ]; do
        print_error "Passwort darf nicht leer sein!"
        read -s -p "Dashboard Passwort: " DASHBOARD_PASSWORD
        echo ""
    done

    # Passwort bestätigen
    read -s -p "Dashboard Passwort (Bestätigung): " DASHBOARD_PASSWORD_CONFIRM
    echo ""
    while [ "$DASHBOARD_PASSWORD" != "$DASHBOARD_PASSWORD_CONFIRM" ]; do
        print_error "Passwörter stimmen nicht überein!"
        read -s -p "Dashboard Passwort: " DASHBOARD_PASSWORD
        echo ""
        read -s -p "Dashboard Passwort (Bestätigung): " DASHBOARD_PASSWORD_CONFIRM
        echo ""
    done

    # .env Datei erstellen
    cat > "$INSTALL_DIR/.env" <<EOF
# Placetel Webhook Secret
# This is the Bearer token that Placetel uses to authenticate webhook requests
PLACETEL_SECRET=$PLACETEL_SECRET

# Dashboard Authentication
# Username and password for accessing the web dashboard
DASHBOARD_USERNAME=$DASHBOARD_USERNAME
DASHBOARD_PASSWORD=$DASHBOARD_PASSWORD

# Optional: Flask Environment
# Set to 'development' for debug mode, 'production' for production
FLASK_ENV=production
EOF

    chmod 600 "$INSTALL_DIR/.env"  # Nur Owner kann lesen/schreiben
    print_success ".env-Datei erstellt und gesichert"
fi

# ============================================================================
# 6. DATENBANK VORBEREITEN
# ============================================================================
print_header "Datenbank vorbereiten"

if [ -f "$INSTALL_DIR/database.db" ]; then
    print_info "Bestehende Datenbank gefunden"
    read -p "Möchten Sie die bestehende Datenbank behalten? (j/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[JjYy]$ ]]; then
        rm "$INSTALL_DIR/database.db"
        print_info "Alte Datenbank entfernt - neue wird beim Start erstellt"
    else
        print_success "Bestehende Datenbank wird verwendet"
    fi
else
    print_info "Datenbank wird beim ersten Start automatisch erstellt"
fi

if [ -f "$INSTALL_DIR/placetel_logs.jsonl" ]; then
    print_success "Log-Datei gefunden und wird beibehalten"
else
    print_info "Log-Datei wird beim ersten Webhook-Empfang erstellt"
fi

# ============================================================================
# 7. SYSTEMD SERVICE EINRICHTEN (nur Linux)
# ============================================================================
if [[ "$OS_TYPE" == "Linux" ]]; then
    print_header "Systemd Service einrichten (optional)"

    read -p "Möchten Sie einen systemd-Service einrichten? (j/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[JjYy]$ ]]; then

        SERVICE_NAME="telefonanlage"
        SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

        print_info "Erstelle systemd Service-Datei..."

        sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Digitale Telefonanlage Webhook Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=/usr/bin/python3 $INSTALL_DIR/webhook_server_prod.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

        print_success "Service-Datei erstellt: $SERVICE_FILE"

        # Systemd neu laden
        sudo systemctl daemon-reload
        print_success "systemd neu geladen"

        # Service aktivieren
        read -p "Service automatisch beim Systemstart starten? (j/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[JjYy]$ ]]; then
            sudo systemctl enable "$SERVICE_NAME"
            print_success "Service aktiviert (startet automatisch beim Booten)"
        fi

        # Service starten
        read -p "Service jetzt starten? (j/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[JjYy]$ ]]; then
            sudo systemctl start "$SERVICE_NAME"
            sleep 2
            if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
                print_success "Service erfolgreich gestartet"
            else
                print_error "Service konnte nicht gestartet werden"
                echo ""
                echo "Überprüfen Sie die Logs mit:"
                echo "  sudo journalctl -u $SERVICE_NAME -f"
            fi
        fi

        echo ""
        print_info "Service-Befehle:"
        echo "  Status prüfen:    sudo systemctl status $SERVICE_NAME"
        echo "  Starten:          sudo systemctl start $SERVICE_NAME"
        echo "  Stoppen:          sudo systemctl stop $SERVICE_NAME"
        echo "  Neu starten:      sudo systemctl restart $SERVICE_NAME"
        echo "  Logs anzeigen:    sudo journalctl -u $SERVICE_NAME -f"

    fi
fi

# ============================================================================
# 8. FIREWALL-HINWEISE
# ============================================================================
print_header "Firewall-Konfiguration"

print_warning "WICHTIG: Bitte stellen Sie sicher, dass Port 54351 erreichbar ist!"
echo ""
echo "Für lokale Tests:"
echo "  Der Server ist erreichbar unter: http://localhost:54351/dashboard"
echo ""
echo "Für externe Zugriffe:"
if [[ "$OS_TYPE" == "Linux" ]]; then
    echo "  UFW (Ubuntu):     sudo ufw allow 54351/tcp"
    echo "  firewalld:        sudo firewall-cmd --add-port=54351/tcp --permanent"
    echo "                    sudo firewall-cmd --reload"
elif [[ "$OS_TYPE" == "Darwin" ]]; then
    echo "  macOS Firewall:   Systemeinstellungen > Sicherheit > Firewall"
fi
echo ""
echo "Für Produktionsumgebungen empfehlen wir:"
echo "  - Nginx als Reverse Proxy"
echo "  - SSL/TLS-Verschlüsselung (Let's Encrypt)"
echo ""

# ============================================================================
# 9. ABSCHLUSS
# ============================================================================
print_header "Installation abgeschlossen"

print_success "Die digitale Telefonanlage wurde erfolgreich installiert!"
echo ""
echo "Installationsverzeichnis: $INSTALL_DIR"
echo "Dashboard URL: http://localhost:54351/dashboard"
echo ""

if [[ "$OS_TYPE" != "Linux" ]] || [[ ! -f "/etc/systemd/system/telefonanlage.service" ]]; then
    print_info "Server manuell starten:"
    echo ""
    echo "  Entwicklungsmodus:"
    echo "    cd $INSTALL_DIR"
    echo "    ./start_dev.sh"
    echo ""
    echo "  Produktionsmodus:"
    echo "    cd $INSTALL_DIR"
    echo "    ./start_prod.sh"
    echo ""
fi

print_info "Nächste Schritte:"
echo "  1. Webhook-URL in Placetel konfigurieren"
echo "  2. Dashboard im Browser öffnen und testen"
echo "  3. Firewall-Regeln anpassen (falls nötig)"
echo "  4. Bei Problemen: Logs prüfen"
echo ""

print_warning "Wichtige Dateien:"
echo "  Konfiguration:    $INSTALL_DIR/.env"
echo "  Datenbank:        $INSTALL_DIR/database.db"
echo "  Logs:             $INSTALL_DIR/placetel_logs.jsonl"
echo "  Prod-Server:      $INSTALL_DIR/webhook_server_prod.py"
echo "  Dev-Server:       $INSTALL_DIR/webhook_server_dev.py"
echo ""

print_success "Viel Erfolg!"
echo ""
