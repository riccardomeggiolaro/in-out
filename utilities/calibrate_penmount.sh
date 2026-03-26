#!/bin/bash
# calibrate_penmount.sh
# Taratura touch IEI PenMount su Wayland/libinput
# Uso: ./calibrate_penmount.sh

set -euo pipefail

DEVICE="/dev/input/event0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="$SCRIPT_DIR/calibrate_penmount_gui.py"
HWDB_FILE="/etc/udev/hwdb.d/99-penmount-calibration.hwdb"

echo "================================================"
echo "  Taratura Touch IEI PenMount - Wayland"
echo "================================================"
echo ""

# ── Controlli preliminari ───────────────────────────

if [ ! -f "$PY_SCRIPT" ]; then
    echo "[ERRORE] Script Python non trovato: $PY_SCRIPT"
    exit 1
fi

if [ ! -e "$DEVICE" ]; then
    echo "[ERRORE] Device non trovato: $DEVICE"
    echo "  Verifica che il touch USB sia collegato."
    exit 1
fi

if [ ! -r "$DEVICE" ]; then
    echo "[ERRORE] Permesso negato su $DEVICE"
    echo ""
    echo "  Soluzione: aggiungi l'utente al gruppo 'input':"
    echo "    sudo usermod -aG input \$USER"
    echo "  Poi rieffettua il login e rilancia lo script."
    exit 1
fi

# ── Dipendenze Python ───────────────────────────────

if ! python3 -c "import evdev" 2>/dev/null; then
    echo "[INFO] Installazione dipendenze Python..."
    sudo apt install -y python3-evdev
fi

if ! python3 -c "import gi; gi.require_version('Gtk','3.0')" 2>/dev/null; then
    echo "[INFO] Installazione dipendenze GTK..."
    sudo apt install -y python3-gi gir1.2-gtk-3.0
fi

# ── Configurazione display Wayland ──────────────────

# Trova automaticamente il socket Wayland se non impostato
if [ -z "${WAYLAND_DISPLAY:-}" ]; then
    for sock in /run/user/$(id -u)/wayland-{0,1,2}; do
        if [ -S "$sock" ]; then
            export WAYLAND_DISPLAY="$(basename "$sock")"
            echo "[INFO] WAYLAND_DISPLAY rilevato: $WAYLAND_DISPLAY"
            break
        fi
    done
fi

if [ -z "${WAYLAND_DISPLAY:-}" ]; then
    echo "[ATTENZIONE] WAYLAND_DISPLAY non trovato."
    echo "  Assicurati di lanciare lo script nella sessione grafica."
    read -rp "  Continuare comunque? [s/N] " ans
    [[ "$ans" =~ ^[sS]$ ]] || exit 0
fi

export GDK_BACKEND=wayland

# ── Info corrente (facoltativo) ─────────────────────

echo "[INFO] Device: $DEVICE"
udevadm info --query=property "$DEVICE" 2>/dev/null \
    | grep -E "^(ID_VENDOR=|ID_MODEL=|ID_VENDOR_ID=|ID_MODEL_ID=)" \
    | sed 's/^/        /'

if [ -f "$HWDB_FILE" ]; then
    echo ""
    echo "[INFO] Calibrazione esistente in $HWDB_FILE:"
    cat "$HWDB_FILE" | sed 's/^/        /'
fi

echo ""
echo "  Tocca i 4 punti che appariranno sullo schermo."
echo "  Lo script applicherà automaticamente la calibrazione."
echo ""
read -rp "  Premi INVIO per avviare... " _

# ── Avvio GUI ───────────────────────────────────────

python3 "$PY_SCRIPT"
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "[OK] Taratura completata."
    echo ""
    echo "  Per applicare senza riavviare:"
    echo "    sudo udevadm trigger --subsystem-match=input --action=change"
    echo "  Oppure scollega/ricollega il cavo USB del touch."
    echo ""
    echo "  Per ripristinare la calibrazione precedente:"
    if [ -f "${HWDB_FILE}.bak" ]; then
        echo "    sudo cp ${HWDB_FILE}.bak ${HWDB_FILE}"
        echo "    sudo systemd-hwdb update"
    else
        echo "    sudo rm -f $HWDB_FILE && sudo systemd-hwdb update"
    fi
else
    echo "[ERRORE] Lo script è uscito con codice $EXIT_CODE."
fi

echo "================================================"
