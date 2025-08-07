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
    sudo chmod 644 /etc/sudo.conf
    sudo chmod 440 /etc/sudoers
else
    echo "sudo è già installato, procedo..."
fi

# Aggiungi l'utente baronpesi al gruppo sudo se esiste
if id "baronpesi" &>/dev/null; then
    if ! groups baronpesi | grep -q sudo; then
        echo "Aggiunta dell'utente baronpesi al gruppo sudo..."
        sudo usermod -aG sudo baronpesi
        echo "Utente baronpesi aggiunto al gruppo sudo."
    else
        echo "L'utente baronpesi è già nel gruppo sudo."
    fi
else
    echo "ATTENZIONE: L'utente baronpesi non esiste sul sistema."
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

# Installa TUTTE le dipendenze necessarie per WeasyPrint
echo "Controllo e installazione delle dipendenze per WeasyPrint..."
WEASYPRINT_DEPS=(
    "libpango-1.0-0"
    "libpangoft2-1.0-0"
    "libpangocairo-1.0-0"
    "libcairo2"
    "libgdk-pixbuf2.0-0"
    "libffi-dev"
    "shared-mime-info"
    "libcairo2-dev"
    "libpango1.0-dev"
    "libgdk-pixbuf2.0-dev"
)

INSTALL_NEEDED=false
for dep in "${WEASYPRINT_DEPS[@]}"; do
    if ! is_installed "$dep"; then
        echo "Dipendenza mancante: $dep"
        INSTALL_NEEDED=true
    fi
done

if [ "$INSTALL_NEEDED" = true ]; then
    echo "Installazione delle dipendenze per WeasyPrint..."
    sudo apt update
    sudo apt install -y "${WEASYPRINT_DEPS[@]}"
else
    echo "Tutte le dipendenze per WeasyPrint sono già installate, procedo..."
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
sudo ufw allow 22

# Abilita ufw se non è già attivo
if ! sudo ufw status | grep -q "Status: active"; then
    echo "Abilitazione di ufw..."
    sudo ufw --force enable
else
    echo "ufw è già attivo."
fi

# Crea le cartelle necessarie (senza errori se già esistono)
mkdir -p /var/lib/in-out
mkdir -p /var/lib/in-out/images
mkdir -p /var/lib/in-out/reports
mkdir -p /var/lib/in-out/pdf

# Copia tutti i file dalla cartella template (accanto a installer.sh) nella cartella reports
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$SCRIPT_DIR/template_reports" ]; then
    sudo cp -r "$SCRIPT_DIR/template_reports/." /var/lib/in-out/reports/
    echo "Template copiati in /var/lib/in-out/reports/"
else
    echo "ATTENZIONE: la cartella template non esiste nella directory dello script!"
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