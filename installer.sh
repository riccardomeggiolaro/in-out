#!/bin/bash
set -e # Termina lo script in caso di errore

SCRIPT_DIR="$(dirname "$0")"
cd "$SCRIPT_DIR"
SOURCE_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
INSTALL_DIR="/opt/in-out"

# Funzione per controllare se un pacchetto è installato
is_installed() {
    dpkg-query -W -f='${Status}' "$1" 2>/dev/null | grep -q "install ok installed"
}

# Funzione per controllare se l'ambiente desktop è MATE
is_mate_desktop() {
    # Controlla diverse variabili e processi che indicano MATE
    if [ "$XDG_CURRENT_DESKTOP" = "MATE" ] || [ "$DESKTOP_SESSION" = "mate" ]; then
        return 0
    fi
    
    # Controlla se ci sono processi MATE in esecuzione
    if pgrep -f "mate-session" >/dev/null 2>&1; then
        return 0
    fi
    
    # Controlla se il pacchetto mate-desktop è installato
    if is_installed "mate-desktop" || is_installed "mate-desktop-environment"; then
        return 0
    fi
    
    return 1
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

# Installa python3-tk se non è presente (richiesto per tkinter)
if ! is_installed python3-tk; then
    echo "Installazione di python3-tk (richiesto per tkinter)..."
    sudo apt update
    sudo apt install -y python3-tk
else
    echo "python3-tk è già installato, procedo..."
fi

# Installa CUPS, libcups2-dev e libcupsimage2 se non sono presenti (PRIMA di installare pacchetti pip)
if ! is_installed cups || ! is_installed libcups2-dev || ! is_installed libcupsimage2; then
    echo "Installazione di CUPS, libcups2-dev e libcupsimage2..."
    sudo apt update
    sudo apt install -y cups libcups2-dev libcupsimage2
else
    echo "CUPS, libcups2-dev e libcupsimage2 sono già installati, procedo..."
fi

# Crea la directory di installazione /opt/in-out e copia i file
if [ "$SOURCE_DIR" != "$INSTALL_DIR" ]; then
    echo "Creazione directory di installazione $INSTALL_DIR..."
    sudo mkdir -p "$INSTALL_DIR"
    echo "Copia dei file da $SOURCE_DIR a $INSTALL_DIR..."
    sudo cp -r "$SOURCE_DIR"/* "$INSTALL_DIR/"
    sudo chown -R root:root "$INSTALL_DIR"
    cd "$INSTALL_DIR"
else
    echo "I file sono già in $INSTALL_DIR, procedo..."
fi

# Crea la directory /var/opt/in-out con le sottocartelle pdf, csv e images
echo "Creazione directory /var/opt/in-out con sottocartelle..."
sudo mkdir -p /var/opt/in-out/{pdf,csv,images}
sudo chown -R root:root /var/opt/in-out
echo "Directory /var/opt/in-out creata con sottocartelle pdf, csv e images."

# Controlla e crea l'ambiente virtuale se non esiste
if [[ ! -d ".venv" ]]; then
    echo "Creazione dell'ambiente virtuale .venv..."
    python3 -m venv .venv
    VENV_NUOVO=true
else
    VENV_NUOVO=false
    echo "L'ambiente virtuale .venv esiste già, procedo..."
fi

# Attiva l'ambiente virtuale
source .venv/bin/activate

# Controlla se `pip`, `setuptools` e `wheel` sono aggiornati
if ! python -c "import pkg_resources; pkg_resources.require(['pip', 'setuptools', 'wheel'])" &>/dev/null; then
    echo "Aggiornamento di pip, setuptools e wheel..."
    pip install --upgrade pip setuptools wheel
else
    echo "pip, setuptools e wheel sono già aggiornati, procedo..."
fi

# Installa i requisiti solo se l'ambiente è nuovo o se mancano pacchetti
if [ -f "requirements.txt" ] && { [ "$VENV_NUOVO" = true ] || ! pip freeze --quiet | grep -q -f requirements.txt; }; then
    echo "Installazione delle dipendenze da requirements.txt..."
    pip cache purge
    pip install -r requirements.txt
else
    echo "Tutte le dipendenze sono già installate, procedo..."
fi

# Controlla se l'ambiente desktop è MATE e installa system-config-printer
if is_mate_desktop; then
    echo "Ambiente desktop MATE rilevato."
    if ! is_installed system-config-printer; then
        echo "Installazione di system-config-printer per MATE..."
        sudo apt update
        sudo apt install -y system-config-printer
    else
        echo "system-config-printer è già installato, procedo..."
    fi
else
    echo "Ambiente desktop MATE non rilevato, salto l'installazione di system-config-printer."
fi

# Installa TUTTE le dipendenze necessarie per WeasyPrint
echo "Controllo e installazione delle dipendenze per WeasyPrint..."
WEASYPRINT_DEPS=(
    "libpango-1.0-0"
    "libpangoft2-1.0-0"
    "libpangocairo-1.0-0"
    "libcairo2"
    "libgdk-pixbuf-2.0-0"
    "libffi-dev"
    "shared-mime-info"
    "libcairo2-dev"
    "libpango1.0-dev"
    "libgdk-pixbuf-2.0-dev"
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

# Esegui l'installer nella cartella tmt-cups
TMT_CUPS_DIR="$INSTALL_DIR/tmt-cups"
if [ -d "$TMT_CUPS_DIR" ]; then
    echo "Cartella tmt-cups trovata, esecuzione dell'installer..."
    if [ -f "$TMT_CUPS_DIR/install.sh" ]; then
        echo "Esecuzione di $TMT_CUPS_DIR/install.sh..."
        cd "$TMT_CUPS_DIR"
        sudo bash install.sh
        cd "$INSTALL_DIR"
        echo "Installer tmt-cups completato."
    else
        echo "ATTENZIONE: File install.sh non trovato in $TMT_CUPS_DIR!"
    fi
else
    echo "ATTENZIONE: Cartella tmt-cups non trovata in $INSTALL_DIR!"
fi

# Crea il servizio systemd se non esiste
if [ ! -f /etc/systemd/system/in-out.service ]; then
    START="$INSTALL_DIR/start.sh"
    sudo chmod +x ${START}
    echo "Creazione del servizio systemd in-out.service..."
    sudo bash -c "cat << EOF > /etc/systemd/system/in-out.service
[Unit]
Description=In-Out Service
After=network.target

[Service]
ExecStart=${START}
WorkingDirectory=${INSTALL_DIR}
User=root
Group=root
Restart=always

[Install]
WantedBy=multi-user.target
EOF"
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

echo "Installazione completa!"
