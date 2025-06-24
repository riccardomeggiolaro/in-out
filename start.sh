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

cd /etc/in-out

# Controlla e crea l'ambiente virtuale se non esiste
if [[ ! -d ".env" ]]; then
    echo "Creazione dell'ambiente virtuale .env..."
    python3 -m venv .env
    VENV_NUOVO=true
else
    VENV_NUOVO=false
    echo "L'ambiente virtuale .env esiste già, procedo..."
fi

# Attiva l'ambiente virtuale
source .env/bin/activate

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