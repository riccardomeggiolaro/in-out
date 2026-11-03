#!/usr/bin/env bash

# Esegue una SELECT su un AS/400 (IBM i, DB2 for i) via ODBC.

#

# Requisiti (Debian/Ubuntu):

#   sudo apt install unixodbc

#   + driver "IBM i Access Client Solutions ODBC" (pacchetto ibm-iaccess)

#     verifica con: odbcinst -q -d   -> deve comparire "IBM i Access ODBC Driver"

#

# Uso:

#   ./s400_query.sh "SELECT * FROM MIALIB.MIATABELLA FETCH FIRST 10 ROWS ONLY"

#

# Le credenziali si possono passare anche da ambiente (consigliato per la password):

#   S400_PASS='segreta' ./s400_query.sh "SELECT ..."


set -euo pipefail


# --- Configurazione ---------------------------------------------------------

S400_HOST="${S400_HOST:-192.168.1.100}"   # IP del S400

S400_USER="${S400_USER:-MIOUTENTE}"       # username

S400_PASS="${S400_PASS:-}"                # password (meglio via variabile d'ambiente)

S400_DRIVER="${S400_DRIVER:-IBM i Access ODBC Driver}"

DELIM="${DELIM:-;}"                       # separatore colonne in output

# -----------------------------------------------------------------------------


QUERY="${1:-}"


if [[ -z "$QUERY" ]]; then

    echo "Uso: $0 \"SELECT ...\"" >&2

    exit 1

fi


# Solo letture: blocca istruzioni diverse da SELECT/WITH

if ! [[ "${QUERY^^}" =~ ^[[:space:]]*(SELECT|WITH) ]]; then

    echo "Errore: questo script accetta solo query SELECT." >&2

    exit 1

fi


# Se la password non è impostata, chiedila senza mostrarla a schermo

if [[ -z "$S400_PASS" ]]; then

    read -r -s -p "Password per $S400_USER@$S400_HOST: " S400_PASS

    echo >&2

fi


if ! command -v isql >/dev/null 2>&1; then

    echo "Errore: isql non trovato. Installa unixodbc (sudo apt install unixodbc)." >&2

    exit 1

fi


CONN="DRIVER={${S400_DRIVER}};SYSTEM=${S400_HOST};UID=${S400_USER};PWD=${S400_PASS};NAM=1;"


# -b = batch (niente banner), -c = nomi colonne in prima riga, -d = delimitatore

# La query viene passata via stdin, così non compare nella lista processi.

printf '%s\n' "$QUERY" | isql -k "$CONN" -b -c -d"$DELIM"
