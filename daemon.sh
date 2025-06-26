#!/bin/bash
set -e # Termina lo script in caso di errore

# Crea il servizio systemd se non esiste
if [ ! -f /etc/systemd/system/in-out.service ]; then
    echo "Creazione del servizio systemd in-out.service..."
    sudo bash -c 'cat << EOF > /etc/systemd/system/in-out.service
[Unit]
Description=In-Out Service
After=network.target

[Service]
ExecStart=/bin/bash /etc/in-out/start.sh
WorkingDirectory=/etc/in-out
User=root
Group=root
Restart=always

[Install]
WantedBy=multi-user.target
EOF'
    echo "Servizio systemd in-out.service creato!"
else
    echo "Il servizio systemd in-out.service esiste già!"
fi

# Ricarica systemd per prendere in considerazione il nuovo servizio
sudo systemctl daemon-reload

# Abilita il servizio per farlo partire all'avvio
sudo systemctl enable in-out.service

# Avvia il servizio
sudo systemctl start in-out.service

echo "Il servizio in-out è stato avviato e verrà eseguito all'avvio della macchina."
