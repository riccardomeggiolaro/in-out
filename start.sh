#!/bin/bash
set -e # Termina lo script in caso di errore

# Ottieni la directory del file script e spostati lì
SCRIPT_DIR="$(dirname "$0")"
cd "$SCRIPT_DIR"

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

# Avvia lo script Python
python3 main.py