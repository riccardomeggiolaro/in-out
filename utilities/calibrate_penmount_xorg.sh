#!/bin/bash
# calibrate_penmount_xorg.sh
# Taratura touch IEI PenMount su XOrg/evdev
# Uso: ./calibrate_penmount_xorg.sh

set -euo pipefail

DEVICE="/dev/input/event0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="$SCRIPT_DIR/calibrate_penmount_xorg_gui.py"
XORG_CONF="/etc/X11/xorg.conf.d/99-penmount-calibration.conf"

echo "================================================"
echo "  Taratura Touch IEI PenMount - XOrg"
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

# ── Controllo DISPLAY (XOrg) ────────────────────────

if [ -z "${DISPLAY:-}" ]; then
    echo "[ERRORE] DISPLAY non impostato."
    echo "  Assicurati di lanciare lo script nella sessione XOrg."
    echo "  Esempio: DISPLAY=:0 ./calibrate_penmount_xorg.sh"
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

# ── Dipendenze xinput ───────────────────────────────

if ! command -v xinput &>/dev/null; then
    echo "[INFO] Installazione xinput..."
    sudo apt install -y xinput
fi

# ── Info corrente (facoltativo) ─────────────────────

echo "[INFO] Device: $DEVICE"
udevadm info --query=property "$DEVICE" 2>/dev/null \
    | grep -E "^(ID_VENDOR=|ID_MODEL=|ID_VENDOR_ID=|ID_MODEL_ID=)" \
    | sed 's/^/        /'

if [ -f "$XORG_CONF" ]; then
    echo ""
    echo "[INFO] Calibrazione esistente in $XORG_CONF:"
    cat "$XORG_CONF" | sed 's/^/        /'
fi

echo ""
echo "  Tocca i 4 punti che appariranno sullo schermo."
echo "  La calibrazione sarà applicata automaticamente."
echo ""
read -rp "  Premi INVIO per avviare... " _

# ── Avvio GUI ───────────────────────────────────────

export GDK_BACKEND=x11

OUTPUT=$(python3 "$PY_SCRIPT" 2>&1)
EXIT_CODE=$?

echo "$OUTPUT"
echo ""

if [ $EXIT_CODE -ne 0 ]; then
    echo "[ERRORE] Lo script è uscito con codice $EXIT_CODE."
    echo "================================================"
    exit $EXIT_CODE
fi

# ── Estrai valori di calibrazione ───────────────────

CALIB_LINE=$(echo "$OUTPUT" | grep "^CALIB:" | tail -1)

if [ -z "$CALIB_LINE" ]; then
    echo "[ERRORE] Nessun valore di calibrazione prodotto dallo script."
    echo "================================================"
    exit 1
fi

read -r _ MIN_X MAX_X MIN_Y MAX_Y <<< "$CALIB_LINE"

echo "[INFO] Valori calcolati: MinX=$MIN_X MaxX=$MAX_X MinY=$MIN_Y MaxY=$MAX_Y"

# ── Individua il nome del device xinput ─────────────

XINPUT_NAME=$(xinput list --name-only 2>/dev/null \
    | grep -i -E "penmount|touch" | head -1 || true)

if [ -n "$XINPUT_NAME" ]; then
    echo "[INFO] Device xinput: $XINPUT_NAME"
fi

# ── Scrivi xorg.conf.d ──────────────────────────────

sudo mkdir -p "$(dirname "$XORG_CONF")"

if [ -f "$XORG_CONF" ]; then
    sudo cp "$XORG_CONF" "${XORG_CONF}.bak"
    echo "[INFO] Backup salvato: ${XORG_CONF}.bak"
fi

PRODUCT_NAME="${XINPUT_NAME:-PenMount}"

sudo tee "$XORG_CONF" > /dev/null <<EOF
Section "InputClass"
    Identifier "PenMount Calibration"
    MatchProduct "$PRODUCT_NAME"
    MatchDevicePath "/dev/input/event*"
    Driver "evdev"
    Option "Calibration" "$MIN_X $MAX_X $MIN_Y $MAX_Y"
    Option "SwapAxes" "0"
EndSection
EOF

echo "[OK] Configurazione scritta in: $XORG_CONF"

# ── Risultato ───────────────────────────────────────

echo ""
echo "[OK] Taratura completata."
echo ""
echo "  La calibrazione è già attiva per questa sessione (via xinput)."
echo "  Diventerà persistente al prossimo avvio di XOrg."
echo ""
echo "  Per ripristinare la calibrazione precedente:"
if [ -f "${XORG_CONF}.bak" ]; then
    echo "    sudo cp ${XORG_CONF}.bak $XORG_CONF"
    echo "  Poi riavvia XOrg."
else
    echo "    sudo rm -f $XORG_CONF"
    echo "  Poi riavvia XOrg."
fi

echo "================================================"
