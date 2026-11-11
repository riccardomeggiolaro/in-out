#!/bin/bash
# Entrypoint del container In-Out:
#  1. inizializza i volumi persistenti al primo avvio
#  2. avvia CUPS
#  3. avvia l'applicazione
set -e

CONFIG_DIR="${IN_OUT_CONFIG_DIR:-/etc/in-out}"

log() { echo "[entrypoint] $*"; }

# --- Configurazione in-out -------------------------------------
mkdir -p "$CONFIG_DIR"
if [ ! -f "$CONFIG_DIR/config.json" ]; then
    log "config.json non trovato in $CONFIG_DIR: copio la configurazione di default"
    cp /opt/in-out/config.default.json "$CONFIG_DIR/config.json"
fi

# --- Cartelle dati ----------------------------------------------
mkdir -p /var/opt/in-out/pdf /var/opt/in-out/csv /var/opt/in-out/images /var/opt/in-out/backup

# --- Fuso orario ------------------------------------------------
if [ -n "$TZ" ] && [ -f "/usr/share/zoneinfo/$TZ" ]; then
    ln -snf "/usr/share/zoneinfo/$TZ" /etc/localtime
    echo "$TZ" > /etc/timezone
fi

# --- CUPS -------------------------------------------------------
if [ "${CUPS_ENABLED:-1}" = "1" ]; then
    # Volume /etc/cups vuoto al primo avvio: lo popolo con la config dell'immagine
    if [ ! -f /etc/cups/cupsd.conf ]; then
        log "inizializzazione configurazione CUPS"
        cp -a /etc/cups.default/. /etc/cups/
    fi

    # Utente amministratore per l'interfaccia web di CUPS (http://host:631)
    CUPS_ADMIN_USER="${CUPS_ADMIN_USER:-admin}"
    if [ -n "$CUPS_ADMIN_PASSWORD" ]; then
        if ! id "$CUPS_ADMIN_USER" >/dev/null 2>&1; then
            useradd -M -s /usr/sbin/nologin -G lpadmin "$CUPS_ADMIN_USER"
        fi
        echo "$CUPS_ADMIN_USER:$CUPS_ADMIN_PASSWORD" | chpasswd
    fi

    # Demoni Epson usati dal backend delle stampanti TM-T (se installati)
    for svc in epson_pcsvcd epson_devicecontrollogserviced; do
        if [ -x "/etc/init.d/$svc" ]; then
            "/etc/init.d/$svc" start >/dev/null 2>&1 || log "impossibile avviare $svc"
        fi
    done

    mkdir -p /run/cups
    rm -f /run/cups/cupsd.pid
    log "avvio CUPS"
    /usr/sbin/cupsd
    for _ in $(seq 1 20); do
        lpstat -r >/dev/null 2>&1 && break
        sleep 0.5
    done
fi

cd /opt/in-out
log "avvio in-out"
exec "$@"
