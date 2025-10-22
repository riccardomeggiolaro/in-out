#!/bin/bash

##############################################################################
# Script di installazione per il sincronizzatore
##############################################################################

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Installazione Sincronizzatore Cartelle                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Controlla se eseguito come root per i pacchetti
if [ "$EUID" -ne 0 ]; then
   echo "⚠️  Alcuni comandi richiederanno sudo"
fi

# Installa dipendenze
echo "📦 Installazione dipendenze..."
if command -v apt &> /dev/null; then
    sudo apt update
    sudo apt install -y inotify-tools rsync
elif command -v yum &> /dev/null; then
    sudo yum install -y inotify-tools rsync
else
    echo "❌ Package manager non riconosciuto. Installa manualmente:"
    echo "   - inotify-tools"
    echo "   - rsync"
    exit 1
fi

echo "✅ Dipendenze installate"
echo ""

# Copia lo script
DEST_DIR="$HOME/.local/bin"
mkdir -p "$DEST_DIR"

if [ -f "sync_folder.sh" ]; then
    cp sync_folder.sh "$DEST_DIR/"
    chmod +x "$DEST_DIR/sync_folder.sh"
    echo "✅ Script copiato in: $DEST_DIR/sync_folder.sh"
else
    echo "❌ File sync_folder.sh non trovato"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Configurazione                                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

read -p "📂 Cartella locale da sincronizzare [$HOME/sync_local]: " cartella_locale
cartella_locale="${cartella_locale:-$HOME/sync_local}"

read -p "🌐 Cartella di rete (es. /mnt/condivisione) [/mnt/rete/sync]: " cartella_rete
cartella_rete="${cartella_rete:-/mnt/rete/sync}"

# Crea le cartelle se non esistono
mkdir -p "$cartella_locale"
echo "✅ Cartella locale creata: $cartella_locale"

if [ ! -d "$cartella_rete" ]; then
    echo "⚠️  Cartella di rete non esiste: $cartella_rete"
    echo "    Assicurati di montare la condivisione di rete prima di avviare lo script"
fi

echo ""
read -p "🚀 Avviare il sincronizzatore ora? (y/n) [n]: " avvia
if [ "$avvia" = "y" ] || [ "$avvia" = "Y" ]; then
    "$DEST_DIR/sync_folder.sh" "$cartella_locale" "$cartella_rete"
else
    echo ""
    echo "📝 Per avviare il sincronizzatore manualmente:"
    echo "   $DEST_DIR/sync_folder.sh $cartella_locale $cartella_rete"
    echo ""
    echo "📝 Per avviare il sincronizzatore al boot (opzionale):"
    echo "   Vedi il file: install_service.sh"
fi
