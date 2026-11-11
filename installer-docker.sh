#!/bin/bash
# ==============================================================
# Installer Docker per In-Out
#
# Uso:   sudo ./installer-docker.sh [-y] [--build]
#   -y        modalita' non interattiva (risponde si' a tutte le domande)
#   --build   costruisce l'immagine dal codice sorgente invece di scaricarla
#             da ghcr.io (richiede il progetto completo con il Dockerfile)
#
# Variabili per il login non interattivo al registry privato:
#   GHCR_USER, GHCR_TOKEN (token GitHub con permesso read:packages)
#
# Cosa fa:
#   1. installa Docker Engine + plugin compose (se mancanti)
#   2. copia il progetto in /opt/in-out
#   3. crea .env e le cartelle persistenti (/etc/in-out, /var/opt/in-out)
#   4. migra config.json da un'eventuale installazione nativa
#   5. ferma servizi in conflitto (in-out.service nativo, CUPS dell'host)
#   6. scarica l'immagine da ghcr.io (o la costruisce) e avvia il container
# ==============================================================
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

ASSUME_YES=false
BUILD=false
for arg in "$@"; do
    case "$arg" in
        -y) ASSUME_YES=true ;;
        --build) BUILD=true ;;
        *) print_error "Opzione sconosciuta: $arg"; exit 1 ;;
    esac
done

ask() {
    # ask "domanda" -> 0 se si'
    if [ "$ASSUME_YES" = true ]; then return 0; fi
    read -p "$1 (s/n) " -n 1 -r
    echo
    [[ $REPLY =~ ^[Ss]$ ]]
}

if [ "$EUID" -ne 0 ]; then
    print_error "Questo script deve essere eseguito con sudo o come root"
    exit 1
fi

SOURCE_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
INSTALL_DIR="/opt/in-out"
CONFIG_DIR="/etc/in-out"
DATA_DIR="/var/opt/in-out"
CUPS_DIR="/etc/in-out/cups"

# --- 1. Docker -------------------------------------------------
if ! command -v docker &>/dev/null; then
    print_info "Docker non trovato: installazione in corso..."
    apt-get update
    apt-get install -y ca-certificates curl
    curl -fsSL https://get.docker.com | sh
else
    print_info "Docker gia' installato: $(docker --version)"
fi

if ! docker compose version &>/dev/null; then
    print_info "Installazione del plugin docker compose..."
    apt-get update
    apt-get install -y docker-compose-plugin
fi

systemctl enable --now docker

# --- 2. Copia del progetto ------------------------------------
if [ "$SOURCE_DIR" != "$INSTALL_DIR" ]; then
    print_info "Copia dei file da $SOURCE_DIR a $INSTALL_DIR..."
    mkdir -p "$INSTALL_DIR"
    # Mantiene un eventuale config.json di un'installazione nativa gia' presente
    if [ -f "$INSTALL_DIR/config.json" ] && [ -f "$INSTALL_DIR/main.py" ] && [ ! -f "$CONFIG_DIR/config.json" ]; then
        mkdir -p "$CONFIG_DIR"
        cp "$INSTALL_DIR/config.json" "$CONFIG_DIR/config.json"
        print_info "config.json dell'installazione nativa migrato in $CONFIG_DIR"
    fi
    tar -C "$SOURCE_DIR" --exclude=.git --exclude=.venv --exclude=docker-data -cf - . | tar -C "$INSTALL_DIR" -xf -
fi
cd "$INSTALL_DIR"

# --- 3. Cartelle persistenti e .env ---------------------------
mkdir -p "$CONFIG_DIR" "$CUPS_DIR" "$DATA_DIR"/{pdf,csv,images,backup}

if [ -f "$CONFIG_DIR/config.json" ]; then
    print_info "Uso la configurazione esistente $CONFIG_DIR/config.json"
else
    print_info "Al primo avvio verra' creato $CONFIG_DIR/config.json con la configurazione di default"
fi

if [ ! -f "$INSTALL_DIR/.env" ]; then
    CUPS_PASSWORD="$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 12)"
    sed -e "s|^IN_OUT_CONFIG_DIR=.*|IN_OUT_CONFIG_DIR=$CONFIG_DIR|" \
        -e "s|^IN_OUT_DATA_DIR=.*|IN_OUT_DATA_DIR=$DATA_DIR|" \
        -e "s|^IN_OUT_CUPS_DIR=.*|IN_OUT_CUPS_DIR=$CUPS_DIR|" \
        -e "s|^CUPS_ADMIN_PASSWORD=.*|CUPS_ADMIN_PASSWORD=$CUPS_PASSWORD|" \
        .env.example > .env
    chmod 600 .env
    print_info "Creato $INSTALL_DIR/.env (password CUPS admin: $CUPS_PASSWORD)"
else
    print_info "Uso il file .env esistente"
fi

# --- 4. Servizi in conflitto ----------------------------------
if systemctl list-unit-files 2>/dev/null | grep -q '^in-out.service'; then
    print_warning "Trovato il servizio nativo in-out.service (usa la stessa porta)"
    if ask "Fermare e disabilitare in-out.service?"; then
        systemctl disable --now in-out.service || true
    fi
fi

if systemctl is-active --quiet cups 2>/dev/null; then
    print_warning "CUPS dell'host e' attivo sulla porta 631 (in conflitto con il CUPS del container)"
    if ask "Fermare e disabilitare CUPS sull'host?"; then
        systemctl disable --now cups cups.socket cups.path 2>/dev/null || true
    else
        print_warning "Imposto CUPS_ENABLED=0: il container non avviera' il proprio CUPS"
        sed -i 's/^CUPS_ENABLED=.*/CUPS_ENABLED=0/' .env
    fi
fi

# --- 5. Firewall ----------------------------------------------
if command -v ufw &>/dev/null && ufw status | grep -q "Status: active"; then
    print_info "Apertura porte nel firewall (80, 631)..."
    ufw allow 80/tcp comment 'HTTP in-out'
    ufw allow 631/tcp comment 'CUPS in-out'
fi

# --- 6. Immagine e avvio --------------------------------------
if [ "$BUILD" = true ]; then
    if [ ! -f Dockerfile ]; then
        print_error "--build richiede il codice sorgente completo (Dockerfile non trovato)"
        exit 1
    fi
    print_info "Build dell'immagine e avvio del container (puo' richiedere qualche minuto)..."
    docker compose up -d --build
else
    print_info "Download dell'immagine da ghcr.io..."
    if ! docker compose pull; then
        print_warning "Download non riuscito: il registry e' privato, serve il login a ghcr.io"
        echo "Serve un token GitHub (classic) con il solo permesso read:packages:"
        echo "  GitHub > Settings > Developer settings > Personal access tokens"
        if [ -z "$GHCR_USER" ]; then read -r -p "Utente GitHub: " GHCR_USER; fi
        if [ -z "$GHCR_TOKEN" ]; then read -r -s -p "Token: " GHCR_TOKEN; echo; fi
        echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USER" --password-stdin
        docker compose pull
    fi
    docker compose up -d --no-build
fi

sleep 5
if [ "$(docker inspect -f '{{.State.Running}}' in-out 2>/dev/null)" = "true" ]; then
    echo "========================================"
    echo "Installazione completata con successo!"
    echo "========================================"
    echo "In-Out:  http://<ip-macchina>/"
    echo "CUPS:    http://<ip-macchina>:631/  (credenziali in $INSTALL_DIR/.env)"
    echo ""
    echo "Comandi utili (da $INSTALL_DIR):"
    echo "  - Log:        docker compose logs -f"
    echo "  - Stato:      docker compose ps"
    echo "  - Riavvio:    docker compose restart"
    echo "  - Stop:       docker compose down"
    echo "  - Aggiorna:   docker compose pull && docker compose up -d"
else
    print_error "Il container non risulta in esecuzione"
    echo "Controllare con: cd $INSTALL_DIR && docker compose logs"
    exit 1
fi
