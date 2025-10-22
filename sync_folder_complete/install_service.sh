#!/bin/bash

##############################################################################
# Script per installare il sincronizzatore come servizio systemd
##############################################################################

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Installazione come servizio systemd                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Controlla se eseguito come root
if [ "$EUID" -ne 0 ]; then
   echo "❌ Questo script deve essere eseguito come root"
   echo "   Esegui: sudo ./install_service.sh"
   exit 1
fi

read -p "📂 Cartella locale da sincronizzare: " cartella_locale
read -p "🌐 Cartella di rete: " cartella_rete
read -p "👤 Nome utente per il servizio [$SUDO_USER]: " username
username="${username:-$SUDO_USER}"

if ! id "$username" &>/dev/null; then
    echo "❌ Utente non trovato: $username"
    exit 1
fi

# Percorso dello script
if [ -f "/home/$username/.local/bin/sync_folder.sh" ]; then
    script_path="/home/$username/.local/bin/sync_folder.sh"
elif [ -f "sync_folder.sh" ]; then
    script_path="$(pwd)/sync_folder.sh"
else
    echo "❌ Script sync_folder.sh non trovato"
    exit 1
fi

# Crea il file del servizio
SERVICE_NAME="sync-folder"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Sincronizzatore Cartelle Locale <-> Rete
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$username
ExecStart=$script_path "$cartella_locale" "$cartella_rete"
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=sync-folder

[Install]
WantedBy=multi-user.target
EOF

echo "✅ File servizio creato: $SERVICE_FILE"

# Abilita e avvia il servizio
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

echo ""
read -p "🚀 Avviare il servizio ora? (y/n) [y]: " avvia
avvia="${avvia:-y}"

if [ "$avvia" = "y" ] || [ "$avvia" = "Y" ]; then
    systemctl start "$SERVICE_NAME"
    echo "✅ Servizio avviato"
    sleep 2
    systemctl status "$SERVICE_NAME" --no-pager
else
    echo "ℹ️  Per avviare il servizio in seguito:"
    echo "   sudo systemctl start $SERVICE_NAME"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Comandi Utili                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Visualizza lo stato:"
echo "  sudo systemctl status $SERVICE_NAME"
echo ""
echo "Visualizza i log:"
echo "  sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "Arresta il servizio:"
echo "  sudo systemctl stop $SERVICE_NAME"
echo ""
echo "Riavvia il servizio:"
echo "  sudo systemctl restart $SERVICE_NAME"
echo ""
echo "Disabilita l'avvio automatico:"
echo "  sudo systemctl disable $SERVICE_NAME"
echo ""
