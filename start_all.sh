#!/bin/bash
# ============================================================================
# Digitale Telefonanlage - Alles starten
# ============================================================================
# Startet FritzBox Monitor und Webhook-Server im Hintergrund
# ============================================================================

cd "$(dirname "$0")"

echo "🚀 Starte Digitale Telefonanlage..."
echo ""

# Prüfe ob .env existiert
if [ ! -f .env ]; then
    echo "❌ Fehler: .env Datei nicht gefunden!"
    echo "Bitte erstelle die .env Datei mit deinen Credentials."
    exit 1
fi

# 1. FritzBox Monitor starten
echo "📞 Starte FritzBox Monitor..."
nohup python3 fritzbox_monitor.py > fritzbox_monitor.log 2>&1 &
FRITZBOX_PID=$!
echo $FRITZBOX_PID > fritzbox_monitor.pid
echo "   ✓ FritzBox Monitor gestartet (PID: $FRITZBOX_PID)"
sleep 2

# 2. Webhook Server starten
echo "🌐 Starte Webhook Server..."
export $(grep -v '^#' .env | grep -v '^$' | xargs)
nohup python3 webhook_server_dev.py > webhook_server.log 2>&1 &
WEBHOOK_PID=$!
echo $WEBHOOK_PID > webhook_server.pid
echo "   ✓ Webhook Server gestartet (PID: $WEBHOOK_PID)"
sleep 2

echo ""
echo "✅ Digitale Telefonanlage läuft!"
echo ""
echo "📊 Dashboard: http://192.168.100.43:54351/dashboard"
echo ""
echo "📝 Logs anzeigen:"
echo "   FritzBox Monitor: tail -f fritzbox_monitor.log"
echo "   Webhook Server:   tail -f webhook_server.log"
echo ""
echo "🛑 Stoppen mit: ./stop_all.sh"
echo ""
