#!/bin/bash
set -e # Termina lo script in caso di errore

# Funzione per controllare se un pacchetto è installato
is_installed() {
    dpkg-query -W -f='${Status}' "$1" 2>/dev/null | grep -q "install ok installed"
}

# Installa sudo se non è presente
if ! command -v sudo &>/dev/null; then
    echo "Installazione di sudo..."
    apt update
    apt install -y sudo
else
    echo "sudo è già installato, procedo..."
fi

# Installa python3.11-venv se non è presente
if ! is_installed python3.11-venv; then
    echo "Installazione di python3.11-venv..."
    sudo apt update
    sudo apt install -y python3.11-venv
else
    echo "python3.11-venv è già installato, procedo..."
fi

# Installa python3-dev se non è presente
if ! is_installed python3-dev; then
    echo "Installazione di python3-dev..."
    sudo apt update
    sudo apt install -y python3-dev
else
    echo "python3-dev è già installato, procedo..."
fi

# Installa python3-pip se non è presente
if ! is_installed python3-pip; then
    echo "Installazione di python3-pip..."
    sudo apt update
    sudo apt install -y python3-pip
else
    echo "python3-pip è già installato, procedo..."
fi

# Installa CUPS e libcups2-dev se non sono presenti
if ! is_installed cups || ! is_installed libcups2-dev; then
    echo "Installazione di CUPS e libcups2-dev..."
    sudo apt update
    sudo apt install -y cups libcups2-dev
else
    echo "CUPS e libcups2-dev sono già installati, procedo..."
fi

# Installa le dipendenze necessarie per WeasyPrint
if ! is_installed libpango-1.0-0 || ! is_installed libcairo2 || ! is_installed libgdk-pixbuf2.0-0; then
    echo "Installazione di libpango, libcairo e libgdk-pixbuf..."
    sudo apt update
    sudo apt install -y libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0
else
    echo "Le librerie necessarie per WeasyPrint sono già installate, procedo..."
fi

# Installa le altre dipendenze di sviluppo per Python
if ! is_installed libjpeg-dev || ! is_installed libxml2-dev || ! is_installed libxslt1-dev; then
    echo "Installazione delle librerie di sviluppo per Python..."
    sudo apt update
    sudo apt install -y libjpeg-dev libxml2-dev libxslt1-dev
else
    echo "Le librerie di sviluppo per Python sono già installate, procedo..."
fi

# Installa ufw se non è presente e abilita le porte 80 e 443
if ! command -v ufw &>/dev/null; then
    echo "Installazione di ufw (Uncomplicated Firewall)..."
    sudo apt update
    sudo apt install -y ufw
else
    echo "ufw è già installato, procedo..."
fi

echo "Abilitazione delle porte 80 (HTTP) e 443 (HTTPS) su ufw..."
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Abilita ufw se non è già attivo
if ! sudo ufw status | grep -q "Status: active"; then
    echo "Abilitazione di ufw..."
    sudo ufw --force enable
else
    echo "ufw è già attivo."
fi

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