#!/bin/bash
# ============================================================================
# Digitale Telefonanlage - Alles stoppen
# ============================================================================
# Stoppt FritzBox Monitor und Webhook-Server
# ============================================================================

cd "$(dirname "$0")"

echo "🛑 Stoppe Digitale Telefonanlage..."
echo ""

# FritzBox Monitor stoppen
if [ -f fritzbox_monitor.pid ]; then
    FRITZBOX_PID=$(cat fritzbox_monitor.pid)
    if kill -0 $FRITZBOX_PID 2>/dev/null; then
        kill $FRITZBOX_PID
        echo "✓ FritzBox Monitor gestoppt (PID: $FRITZBOX_PID)"
    else
        echo "ℹ FritzBox Monitor läuft nicht"
    fi
    rm fritzbox_monitor.pid
else
    echo "ℹ FritzBox Monitor PID-Datei nicht gefunden"
    # Versuche trotzdem zu stoppen
    pkill -f fritzbox_monitor.py && echo "✓ FritzBox Monitor gestoppt"
fi

# Webhook Server stoppen
if [ -f webhook_server.pid ]; then
    WEBHOOK_PID=$(cat webhook_server.pid)
    if kill -0 $WEBHOOK_PID 2>/dev/null; then
        kill $WEBHOOK_PID
        echo "✓ Webhook Server gestoppt (PID: $WEBHOOK_PID)"
    else
        echo "ℹ Webhook Server läuft nicht"
    fi
    rm webhook_server.pid
else
    echo "ℹ Webhook Server PID-Datei nicht gefunden"
    # Versuche trotzdem zu stoppen
    pkill -f webhook_server_dev.py && echo "✓ Webhook Server gestoppt"
fi

echo ""
echo "✅ Digitale Telefonanlage gestoppt!"
echo ""
