#!/bin/bash
# =============================================================================
# Installa i servizi AS400 per in-out (Debian 13):
#   - as400-sync:    sincronizzazione prenotazioni AS400 -> in-out (timer 5 min)
#   - as400-transit: watcher dei CSV delle pesate -> transiti (sempre attivo)
#
# Lo script lavora sulla cartella in cui si trova (quella con as400.py),
# ovunque essa sia. Se sposti la cartella, rilancia l'installer.
#
# Cosa fa:
#   1. installa i pacchetti di sistema (python3-venv, unixodbc)
#   2. crea il venv .venv nella cartella e installa pyodbc
#   3. controlla che il driver ODBC IBM sia presente (non lo installa)
#   4. crea il file .env con le credenziali AS400 (se non esiste)
#   5. crea e avvia as400-sync.service + as400-sync.timer (ogni 5 minuti)
#   6. ottiene il token API di in-out (login baronpesi) e salva in .env
#   7. crea e avvia as400-transit.service (transit_watcher.py)
#
# Uso:
#   sudo ./install-debian13.sh              # installa / aggiorna
#   sudo ./install-debian13.sh --uninstall  # rimuove servizi e timer
# =============================================================================
set -euo pipefail

SERVICE_NAME="as400-sync"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
TIMER_FILE="/etc/systemd/system/${SERVICE_NAME}.timer"
INTERVAL="5min"

APP_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
VENV_DIR="$APP_DIR/.venv"
ENV_FILE="$APP_DIR/.env"
SCRIPT="$APP_DIR/as400.py"

TRANSIT_NAME="as400-transit"
TRANSIT_FILE="/etc/systemd/system/${TRANSIT_NAME}.service"
TRANSIT_SCRIPT="$APP_DIR/transit_watcher.py"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

if [ "$(id -u)" -ne 0 ]; then
    error "Lancia lo script come root: sudo $0"
    exit 1
fi

# -----------------------------------------------------------------------------
# Disinstallazione
# -----------------------------------------------------------------------------
if [ "${1:-}" = "--uninstall" ]; then
    systemctl disable --now "${SERVICE_NAME}.timer" 2>/dev/null || true
    systemctl stop "${SERVICE_NAME}.service" 2>/dev/null || true
    systemctl disable --now "${TRANSIT_NAME}.service" 2>/dev/null || true
    rm -f "$SERVICE_FILE" "$TIMER_FILE" "$TRANSIT_FILE"
    systemctl daemon-reload
    info "Servizi ${SERVICE_NAME} (con timer) e ${TRANSIT_NAME} rimossi."
    echo "    La cartella $APP_DIR (script, .venv, .env, file .db) non è stata toccata."
    exit 0
fi

if [ ! -f "$SCRIPT" ]; then
    error "as400.py non trovato in $APP_DIR"
    exit 1
fi

# -----------------------------------------------------------------------------
# Controllo sistema operativo
# -----------------------------------------------------------------------------
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [ "${ID:-}" != "debian" ] || [ "${VERSION_ID:-}" != "13" ]; then
        warn "Script pensato per Debian 13. Sistema rilevato: ${PRETTY_NAME:-sconosciuto}"
        read -r -p "Vuoi continuare comunque? (s/n) " REPLY
        [[ "$REPLY" =~ ^[Ss]$ ]] || exit 1
    fi
fi

echo "Cartella di installazione: $APP_DIR"

# -----------------------------------------------------------------------------
# 1. Pacchetti di sistema
# -----------------------------------------------------------------------------
MISSING=()
for pkg in python3 python3-venv unixodbc; do
    dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q "install ok installed" || MISSING+=("$pkg")
done
if [ ${#MISSING[@]} -gt 0 ]; then
    echo "Installazione pacchetti: ${MISSING[*]}"
    apt-get update -qq
    apt-get install -y "${MISSING[@]}"
fi
info "Pacchetti di sistema presenti"

# -----------------------------------------------------------------------------
# 2. Virtualenv + pyodbc
# -----------------------------------------------------------------------------
# Un venv copiato o spostato da un'altra cartella ha gli script (pip, ...)
# che puntano ancora al vecchio percorso: in quel caso lo ricreiamo.
if [ -d "$VENV_DIR" ]; then
    if ! "$VENV_DIR/bin/python3" -c "import sys" 2>/dev/null \
       || ! head -n 1 "$VENV_DIR/bin/pip" 2>/dev/null | grep -qF "#!$VENV_DIR/bin/python"; then
        warn "Il venv in $VENV_DIR è stato copiato da un'altra cartella o è danneggiato: lo ricreo"
        rm -rf "$VENV_DIR"
    fi
fi
if [ ! -x "$VENV_DIR/bin/python3" ]; then
    echo "Creazione venv in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/python3" -m pip install -q --upgrade pip
"$VENV_DIR/bin/python3" -m pip install -q -r "$APP_DIR/requirements.txt"
if ! "$VENV_DIR/bin/python3" -c "import pyodbc" 2>/dev/null; then
    error "pyodbc installato ma non importabile (manca libodbc?). Controlla: $VENV_DIR/bin/python3 -c 'import pyodbc'"
    exit 1
fi
info "Venv pronto con pyodbc"

# -----------------------------------------------------------------------------
# 3. File .env con le credenziali
# -----------------------------------------------------------------------------
if [ ! -f "$ENV_FILE" ]; then
    echo
    echo "Configurazione connessione AS400 (salvata in $ENV_FILE):"
    read -r -p "  Indirizzo AS400 (IP o nome host): " AS400_SYSTEM
    read -r -p "  Utente AS400: " AS400_UID
    read -r -s -p "  Password AS400: " AS400_PWD; echo
    read -r -p "  Database in-out [/var/opt/in-out/database.db]: " MAIN_DB_PATH
    MAIN_DB_PATH="${MAIN_DB_PATH:-/var/opt/in-out/database.db}"
    # Il .env è letto da as400.py, che toglie solo gli apici esterni:
    # apici singoli, oppure doppi se la password contiene un apice singolo.
    if [[ "$AS400_PWD" == *"'"* ]]; then Q='"'; else Q="'"; fi
    umask 077
    cat > "$ENV_FILE" <<EOF
AS400_SYSTEM=$AS400_SYSTEM
AS400_UID=$AS400_UID
AS400_PWD=${Q}${AS400_PWD}${Q}
AS400_DRIVER='IBM i Access ODBC Driver'
MAIN_DB_PATH=$MAIN_DB_PATH
EOF
    info "Creato $ENV_FILE"
else
    info "Uso il file .env esistente: $ENV_FILE"
fi
chown root:root "$ENV_FILE"
chmod 600 "$ENV_FILE"

# -----------------------------------------------------------------------------
# 4. Controllo driver ODBC IBM (solo verifica)
# -----------------------------------------------------------------------------
DRIVER_NAME="$(grep -E '^\s*(export\s+)?AS400_DRIVER=' "$ENV_FILE" | tail -1 | cut -d= -f2- | sed -E "s/^['\"]//; s/['\"]\s*$//")"
DRIVER_NAME="${DRIVER_NAME:-IBM i Access ODBC Driver}"
if odbcinst -q -d 2>/dev/null | grep -qF "[$DRIVER_NAME]"; then
    info "Driver ODBC trovato: $DRIVER_NAME"
else
    warn "Driver ODBC \"$DRIVER_NAME\" NON trovato (odbcinst -q -d)."
    warn "Installa IBM i Access Client Solutions (pacchetto ibmiaccess) prima che il timer possa collegarsi."
fi

MAIN_DB="$(grep -E '^\s*(export\s+)?MAIN_DB_PATH=' "$ENV_FILE" | tail -1 | cut -d= -f2- | sed -E "s/^['\"]//; s/['\"]\s*$//")"
MAIN_DB="${MAIN_DB:-/var/opt/in-out/database.db}"
if [ -f "$MAIN_DB" ]; then
    info "Database in-out trovato: $MAIN_DB"
else
    warn "Database in-out non trovato: $MAIN_DB (la sincronizzazione fallirà finché non esiste)"
fi

# -----------------------------------------------------------------------------
# 5. Servizio e timer systemd
# -----------------------------------------------------------------------------
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Sincronizzazione prenotazioni AS400 -> in-out
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=root
Group=root
WorkingDirectory=$APP_DIR
Environment=AS400_ENV_FILE=$ENV_FILE
ExecStart=$VENV_DIR/bin/python3 $SCRIPT
TimeoutStartSec=4min
EOF

cat > "$TIMER_FILE" <<EOF
[Unit]
Description=Esegue ${SERVICE_NAME} ogni ${INTERVAL}

[Timer]
OnBootSec=2min
OnUnitActiveSec=${INTERVAL}
AccuracySec=10s
Unit=${SERVICE_NAME}.service

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now "${SERVICE_NAME}.timer" >/dev/null
info "Timer ${SERVICE_NAME}.timer attivo (ogni ${INTERVAL})"

echo
echo "Prima sincronizzazione di prova..."
if systemctl start "${SERVICE_NAME}.service"; then
    info "Sincronizzazione riuscita"
else
    warn "La sincronizzazione di prova è fallita, controlla il log qui sotto."
fi
journalctl -u "${SERVICE_NAME}.service" -n 10 --no-pager || true

# -----------------------------------------------------------------------------
# 6. Token API di in-out per il watcher dei transiti
# -----------------------------------------------------------------------------
env_value() {
    grep -E "^\s*(export\s+)?$1=" "$ENV_FILE" | tail -1 | cut -d= -f2- | sed -E "s/^['\"]//; s/['\"]\s*$//"
}

TRANSIT_ENABLED=1
if [ ! -f "$TRANSIT_SCRIPT" ]; then
    warn "transit_watcher.py non trovato in $APP_DIR: servizio ${TRANSIT_NAME} non installato"
    TRANSIT_ENABLED=0
elif [ -z "$(env_value IN_OUT_TOKEN)" ]; then
    echo
    echo "Configurazione API in-out per i transiti (salvata in $ENV_FILE):"
    read -r -p "  Indirizzo in-out [http://localhost:80]: " IN_OUT_URL
    IN_OUT_URL="${IN_OUT_URL:-http://localhost:80}"
    read -r -p "  Cartella CSV pesate [/var/opt/in-out/csv]: " CSV_DIR
    CSV_DIR="${CSV_DIR:-/var/opt/in-out/csv}"
    read -r -p "  Utente in-out [baronpesi]: " IN_OUT_USER
    IN_OUT_USER="${IN_OUT_USER:-baronpesi}"

    TOKEN=""
    for attempt in 1 2 3; do
        read -r -s -p "  Password di $IN_OUT_USER: " IN_OUT_PWD; echo
        # password passata via ambiente: non compare nella lista dei processi
        if TOKEN="$(IN_OUT_URL="$IN_OUT_URL" IN_OUT_USER="$IN_OUT_USER" IN_OUT_PWD="$IN_OUT_PWD" \
            "$VENV_DIR/bin/python3" - <<'PY'
import json, os, sys, urllib.request, urllib.error
req = urllib.request.Request(
    os.environ["IN_OUT_URL"].rstrip("/") + "/api/auth/login",
    data=json.dumps({"username": os.environ["IN_OUT_USER"],
                     "password": os.environ["IN_OUT_PWD"]}).encode(),
    headers={"Content-Type": "application/json"}, method="POST")
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        print(json.loads(r.read())["access_token"])
except urllib.error.HTTPError as e:
    sys.stderr.write(f"login rifiutato (HTTP {e.code})\n"); sys.exit(1)
except Exception as e:
    sys.stderr.write(f"in-out non raggiungibile: {e}\n"); sys.exit(1)
PY
        )" && [ -n "$TOKEN" ]; then
            break
        fi
        TOKEN=""
        warn "Login non riuscito (tentativo $attempt di 3)"
    done
    unset IN_OUT_PWD

    if [ -n "$TOKEN" ]; then
        cat >> "$ENV_FILE" <<EOF
IN_OUT_URL=$IN_OUT_URL
IN_OUT_TOKEN=$TOKEN
CSV_DIR=$CSV_DIR
EOF
        info "Token API di $IN_OUT_USER salvato in $ENV_FILE"
    else
        warn "Nessun token: servizio ${TRANSIT_NAME} non installato. Rilancia l'installer quando in-out è raggiungibile."
        TRANSIT_ENABLED=0
    fi
else
    info "Token API in-out già presente in $ENV_FILE"
fi

# -----------------------------------------------------------------------------
# 7. Servizio del watcher dei transiti
# -----------------------------------------------------------------------------
if [ "$TRANSIT_ENABLED" = "1" ]; then
    cat > "$TRANSIT_FILE" <<EOF
[Unit]
Description=Transiti da CSV pesate (riferimento documento diverso da ITA)
After=network-online.target in-out.service
Wants=network-online.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$APP_DIR
Environment=AS400_ENV_FILE=$ENV_FILE
ExecStart=$VENV_DIR/bin/python3 $TRANSIT_SCRIPT
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable "${TRANSIT_NAME}.service" >/dev/null
    systemctl restart "${TRANSIT_NAME}.service"
    sleep 2
    if systemctl is-active --quiet "${TRANSIT_NAME}.service"; then
        info "Servizio ${TRANSIT_NAME} attivo"
    else
        warn "Il servizio ${TRANSIT_NAME} non è partito, controlla il log qui sotto."
    fi
    journalctl -u "${TRANSIT_NAME}.service" -n 5 --no-pager || true
fi

cat <<EOF

Comandi utili:
  Prossime esecuzioni:  systemctl list-timers ${SERVICE_NAME}.timer
  Log in tempo reale:   journalctl -u ${SERVICE_NAME}.service -f
  Lancia subito:        sudo systemctl start ${SERVICE_NAME}.service
  Ferma il timer:       sudo systemctl stop ${SERVICE_NAME}.timer
  Log transiti:         journalctl -u ${TRANSIT_NAME}.service -f
  Riavvia transiti:     sudo systemctl restart ${TRANSIT_NAME}.service
  Disinstalla:          sudo $APP_DIR/$(basename "$0") --uninstall
EOF
