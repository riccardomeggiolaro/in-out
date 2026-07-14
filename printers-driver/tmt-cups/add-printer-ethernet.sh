#!/bin/bash
set -e

QUEUE_NAME="TMT88VII"
PPD_PATH="./ppd/tm-t88v-rastertotmt.ppd"
PORT=9100

echo "=== Configurazione stampante $QUEUE_NAME ==="

read -p "Inserisci l'indirizzo IP della stampante: " PRINTER_IP

if [ -z "$PRINTER_IP" ]; then
    echo "Errore: IP non inserito."
    exit 1
fi

# Se la coda esiste già, lpadmin con lo stesso nome la modifica direttamente (nessuna rimozione necessaria)
if lpstat -p "$QUEUE_NAME" >/dev/null 2>&1; then
    echo "Trovata coda '$QUEUE_NAME' esistente, la aggiorno..."
fi

# Sceglie il PPD se presente, altrimenti driver raw
if [ -f "$PPD_PATH" ]; then
    echo "Uso PPD trovato in $PPD_PATH"
    sudo lpadmin -p "$QUEUE_NAME" -E \
        -v "socket://$PRINTER_IP:$PORT" \
        -P "$PPD_PATH"
else
    echo "PPD non trovato in $PPD_PATH, configuro come stampante RAW generica."
    sudo lpadmin -p "$QUEUE_NAME" -E \
        -v "socket://$PRINTER_IP:$PORT" \
        -m raw
fi

echo ""
echo "=== Coda configurata ==="
lpstat -v "$QUEUE_NAME"

read -p "Vuoi inviare una stampa di test ora? [s/N] " TEST
if [[ "$TEST" =~ ^[sS]$ ]]; then
    lp -d "$QUEUE_NAME" /etc/hosts
    echo "Job inviato. Controlla la stampante."
fi

echo "Fatto."