#!/bin/bash
set -e # Termina lo script in caso di errore

SCRIPT_DIR="$(dirname "$0")"
cd "$SCRIPT_DIR"
BASE_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)/"

# Colori per output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Funzione per stampare messaggi colorati
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Funzione per controllare se un pacchetto è installato
is_installed() {
    dpkg-query -W -f='${Status}' "$1" 2>/dev/null | grep -q "install ok installed"
}

# Funzione per controllare se l'ambiente desktop è MATE
is_mate_desktop() {
    if [ "$XDG_CURRENT_DESKTOP" = "MATE" ] || [ "$DESKTOP_SESSION" = "mate" ]; then
        return 0
    fi

    if pgrep -f "mate-session" >/dev/null 2>&1; then
        return 0
    fi

    if is_installed "mate-desktop" || is_installed "mate-desktop-environment"; then
        return 0
    fi

    return 1
}

# Verifica che lo script venga eseguito su Ubuntu
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$ID" != "ubuntu" ]]; then
        print_warning "Questo script è ottimizzato per Ubuntu. Sistema rilevato: $ID"
        read -p "Vuoi continuare comunque? (s/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Ss]$ ]]; then
            exit 1
        fi
    else
        print_info "Sistema Ubuntu rilevato: $VERSION"
    fi
else
    print_warning "Impossibile rilevare il sistema operativo"
fi

# Verifica se lo script viene eseguito come root o con sudo
if [ "$EUID" -ne 0 ]; then
    print_error "Questo script deve essere eseguito con sudo o come root"
    exit 1
fi

# Ottieni l'utente che ha invocato sudo (o root se eseguito direttamente come root)
REAL_USER="${SUDO_USER:-$USER}"
print_info "Installazione per l'utente: $REAL_USER"

# Installa sudo se non è presente (caso raro)
if ! command -v sudo &>/dev/null; then
    print_info "Installazione di sudo..."
    apt update
    apt install -y sudo
    chmod 644 /etc/sudo.conf
    chmod 440 /etc/sudoers
else
    print_info "sudo è già installato"
fi

# Aggiungi l'utente corrente al gruppo sudo se non è già presente
if [ "$REAL_USER" != "root" ]; then
    if ! groups "$REAL_USER" | grep -q sudo; then
        print_info "Aggiunta dell'utente $REAL_USER al gruppo sudo..."
        usermod -aG sudo "$REAL_USER"
        print_info "Utente $REAL_USER aggiunto al gruppo sudo"
    else
        print_info "L'utente $REAL_USER è già nel gruppo sudo"
    fi
fi

# Aggiorna l'indice dei pacchetti
print_info "Aggiornamento dell'indice dei pacchetti..."
apt update

# Rileva la versione di Python disponibile
print_info "Rilevamento versione Python..."
PYTHON_VERSION=""
for ver in 3.11 3.10 3.9 3.8; do
    if command -v python$ver &>/dev/null; then
        PYTHON_VERSION=$ver
        print_info "Python $ver trovato"
        break
    fi
done

if [ -z "$PYTHON_VERSION" ]; then
    print_warning "Nessuna versione Python 3.8+ trovata, installazione di python3..."
    apt install -y python3
    PYTHON_VERSION=$(python3 --version | awk '{print $2}' | cut -d. -f1,2)
fi

PYTHON_CMD="python$PYTHON_VERSION"
print_info "Utilizzo di Python $PYTHON_VERSION"

# Installa python venv se non è presente
VENV_PKG="python$PYTHON_VERSION-venv"
if ! is_installed "$VENV_PKG"; then
    print_info "Installazione di $VENV_PKG..."
    apt install -y "$VENV_PKG"
else
    print_info "$VENV_PKG è già installato"
fi

# Installa python-dev se non è presente
DEV_PKG="python$PYTHON_VERSION-dev"
if ! is_installed "$DEV_PKG"; then
    print_info "Installazione di $DEV_PKG..."
    apt install -y "$DEV_PKG" || {
        print_warning "Impossibile installare $DEV_PKG, provo con python3-dev..."
        apt install -y python3-dev
    }
else
    print_info "$DEV_PKG è già installato"
fi

# Installa python3-pip se non è presente
if ! is_installed python3-pip; then
    print_info "Installazione di python3-pip..."
    apt install -y python3-pip
else
    print_info "python3-pip è già installato"
fi

# Installa python3-tk se non è presente (richiesto per tkinter)
TK_PKG="python$PYTHON_VERSION-tk"
if ! is_installed "$TK_PKG"; then
    print_info "Installazione di $TK_PKG (richiesto per tkinter)..."
    apt install -y "$TK_PKG" || {
        print_warning "Impossibile installare $TK_PKG, provo con python3-tk..."
        apt install -y python3-tk
    }
else
    print_info "$TK_PKG è già installato"
fi

# Controlla e crea l'ambiente virtuale se non esiste
if [[ ! -d ".venv" ]]; then
    print_info "Creazione dell'ambiente virtuale .venv..."
    $PYTHON_CMD -m venv .venv
    VENV_NUOVO=true
else
    VENV_NUOVO=false
    print_info "L'ambiente virtuale .venv esiste già"
fi

# Attiva l'ambiente virtuale
source .venv/bin/activate

# Aggiorna pip, setuptools e wheel
print_info "Aggiornamento di pip, setuptools e wheel..."
pip install --upgrade pip setuptools wheel

# Installa i requisiti
if [ -f "requirements.txt" ]; then
    print_info "Installazione delle dipendenze da requirements.txt..."
    if [ "$VENV_NUOVO" = true ]; then
        pip cache purge
    fi
    pip install -r requirements.txt
else
    print_warning "File requirements.txt non trovato!"
fi

# Installa CUPS, libcups2-dev e libcupsimage2 se non sono presenti
if ! is_installed cups || ! is_installed libcups2-dev || ! is_installed libcupsimage2; then
    print_info "Installazione di CUPS, libcups2-dev e libcupsimage2..."
    apt install -y cups libcups2-dev libcupsimage2
else
    print_info "CUPS e le sue dipendenze sono già installati"
fi

# Controlla se l'ambiente desktop è MATE e installa system-config-printer
if is_mate_desktop; then
    print_info "Ambiente desktop MATE rilevato"
    if ! is_installed system-config-printer; then
        print_info "Installazione di system-config-printer per MATE..."
        apt install -y system-config-printer
    else
        print_info "system-config-printer è già installato"
    fi
else
    print_info "Ambiente desktop MATE non rilevato"
fi

# Installa TUTTE le dipendenze necessarie per WeasyPrint
print_info "Controllo e installazione delle dipendenze per WeasyPrint..."
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
        print_warning "Dipendenza mancante: $dep"
        INSTALL_NEEDED=true
    fi
done

if [ "$INSTALL_NEEDED" = true ]; then
    print_info "Installazione delle dipendenze per WeasyPrint..."
    apt install -y "${WEASYPRINT_DEPS[@]}"
else
    print_info "Tutte le dipendenze per WeasyPrint sono già installate"
fi

# Installa le altre dipendenze di sviluppo per Python
DEV_LIBS=("libjpeg-dev" "libxml2-dev" "libxslt1-dev")
INSTALL_DEV_NEEDED=false
for lib in "${DEV_LIBS[@]}"; do
    if ! is_installed "$lib"; then
        INSTALL_DEV_NEEDED=true
        break
    fi
done

if [ "$INSTALL_DEV_NEEDED" = true ]; then
    print_info "Installazione delle librerie di sviluppo per Python..."
    apt install -y "${DEV_LIBS[@]}"
else
    print_info "Le librerie di sviluppo per Python sono già installate"
fi

# Installa ufw se non è presente
if ! command -v ufw &>/dev/null; then
    print_info "Installazione di ufw (Uncomplicated Firewall)..."
    apt install -y ufw
else
    print_info "ufw è già installato"
fi

# Configura le regole del firewall
print_info "Configurazione delle regole del firewall..."
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw allow 22/tcp comment 'SSH'

# Abilita ufw se non è già attivo
if ! ufw status | grep -q "Status: active"; then
    print_warning "Abilitazione di ufw..."
    ufw --force enable
else
    print_info "ufw è già attivo"
fi

# Esegui l'installer nella cartella tmt-cups
TMT_CUPS_DIR="./tmt-cups"
if [ -d "$TMT_CUPS_DIR" ]; then
    print_info "Cartella tmt-cups trovata, esecuzione dell'installer..."
    if [ -f "$TMT_CUPS_DIR/install.sh" ]; then
        cd "$TMT_CUPS_DIR"
        bash install.sh
        cd "$BASE_DIR"
        print_info "Installer tmt-cups completato"
    else
        print_warning "File install.sh non trovato in $TMT_CUPS_DIR"
    fi
else
    print_warning "Cartella tmt-cups non trovata"
fi

# Crea il servizio systemd se non esiste
SERVICE_FILE="/etc/systemd/system/in-out.service"
if [ ! -f "$SERVICE_FILE" ]; then
    START_SCRIPT="${BASE_DIR}start.sh"

    if [ ! -f "$START_SCRIPT" ]; then
        print_error "File start.sh non trovato in $BASE_DIR"
        exit 1
    fi

    chmod +x "$START_SCRIPT"

    print_info "Creazione del servizio systemd in-out.service..."
    cat << EOF > "$SERVICE_FILE"
[Unit]
Description=In-Out Service
After=network.target

[Service]
ExecStart=$START_SCRIPT
WorkingDirectory=$BASE_DIR
User=root
Group=root
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    print_info "Servizio systemd in-out.service creato"
else
    print_info "Il servizio systemd in-out.service esiste già"
fi

# Ricarica systemd per prendere in considerazione il nuovo servizio
print_info "Ricaricamento della configurazione systemd..."
systemctl daemon-reload

# Abilita il servizio per farlo partire all'avvio
print_info "Abilitazione del servizio in-out..."
systemctl enable in-out.service

# Avvia il servizio
print_info "Avvio del servizio in-out..."
systemctl start in-out.service

# Verifica lo stato del servizio
sleep 2
if systemctl is-active --quiet in-out.service; then
    print_info "Il servizio in-out è stato avviato con successo"
else
    print_error "Il servizio in-out non si è avviato correttamente"
    print_info "Controllare lo stato con: sudo systemctl status in-out.service"
    exit 1
fi

print_info "========================================"
print_info "Installazione completata con successo!"
print_info "========================================"
print_info "Il servizio in-out è attivo e verrà eseguito all'avvio del sistema"
print_info ""
print_info "Comandi utili:"
print_info "  - Stato servizio: sudo systemctl status in-out.service"
print_info "  - Stop servizio: sudo systemctl stop in-out.service"
print_info "  - Restart servizio: sudo systemctl restart in-out.service"
print_info "  - Log servizio: sudo journalctl -u in-out.service -f"
