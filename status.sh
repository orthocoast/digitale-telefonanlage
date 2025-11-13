#!/bin/bash
# ============================================================================
# Digitale Telefonanlage - Status prüfen
# ============================================================================
# Zeigt den Status der laufenden Dienste an
# ============================================================================

cd "$(dirname "$0")"

echo "📊 Status der Digitalen Telefonanlage"
echo "======================================"
echo ""

# FritzBox Monitor Status
echo "📞 FritzBox Monitor:"
if [ -f fritzbox_monitor.pid ]; then
    FRITZBOX_PID=$(cat fritzbox_monitor.pid)
    if kill -0 $FRITZBOX_PID 2>/dev/null; then
        echo "   ✅ Läuft (PID: $FRITZBOX_PID)"
    else
        echo "   ❌ Gestoppt (PID-Datei existiert, aber Prozess läuft nicht)"
    fi
else
    if pgrep -f fritzbox_monitor.py > /dev/null; then
        echo "   ⚠️  Läuft, aber keine PID-Datei gefunden"
    else
        echo "   ❌ Gestoppt"
    fi
fi

echo ""

# Webhook Server Status
echo "🌐 Webhook Server:"
if [ -f webhook_server.pid ]; then
    WEBHOOK_PID=$(cat webhook_server.pid)
    if kill -0 $WEBHOOK_PID 2>/dev/null; then
        echo "   ✅ Läuft (PID: $WEBHOOK_PID)"
    else
        echo "   ❌ Gestoppt (PID-Datei existiert, aber Prozess läuft nicht)"
    fi
else
    if pgrep -f webhook_server_dev.py > /dev/null; then
        echo "   ⚠️  Läuft, aber keine PID-Datei gefunden"
    else
        echo "   ❌ Gestoppt"
    fi
fi

echo ""

# Port Check
echo "🔌 Port 54351:"
if lsof -i :54351 > /dev/null 2>&1; then
    echo "   ✅ Offen (Server erreichbar)"
else
    echo "   ❌ Geschlossen (Server nicht erreichbar)"
fi

echo ""

# Dashboard URL
echo "📊 Dashboard: http://192.168.100.43:54351/dashboard"
echo ""

# Log-Dateien
echo "📝 Logs:"
if [ -f fritzbox_monitor.log ]; then
    FRITZBOX_LINES=$(wc -l < fritzbox_monitor.log)
    echo "   FritzBox Monitor: $FRITZBOX_LINES Zeilen"
else
    echo "   FritzBox Monitor: Keine Log-Datei"
fi

if [ -f webhook_server.log ]; then
    WEBHOOK_LINES=$(wc -l < webhook_server.log)
    echo "   Webhook Server:   $WEBHOOK_LINES Zeilen"
else
    echo "   Webhook Server:   Keine Log-Datei"
fi

echo ""
