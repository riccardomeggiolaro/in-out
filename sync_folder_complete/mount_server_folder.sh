#!/bin/bash

set -e

# CONFIGURAZIONE
PASSWD="uPZa6eY2Ik"
CARTELLA_LOCALE="/var/lib/in-out"
MOUNT_POINT="/mnt/server_in_out"
SERVER="10.0.5.105"
SHARE="gh5/Dev"
USERNAME="Riccardo Meggiolaro"
DOMAIN="BARON"
SYNC_SCRIPT="./sync_folder.sh"

# ESCLUSIONI (file che non vengono sincronizzati)
EXCLUDE_PATTERNS=("*.db" "*.lock" ".*" "*.tmp" "*.log" "*.pid" "*.swp")

# Ottieni l'utente corrente
if [ -n "$SUDO_USER" ]; then
    CURRENT_USER="$SUDO_USER"
else
    CURRENT_USER=$(whoami)
fi
CURRENT_UID=$(id -u $CURRENT_USER)
CURRENT_GID=$(id -g $CURRENT_USER)

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Montaggio SMB e Sincronizzazione                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Controlla root
if [ "$EUID" -ne 0 ]; then
   echo "❌ Esegui con sudo"
   exit 1
fi

echo "👤 Utente: $CURRENT_USER (UID: $CURRENT_UID, GID: $CURRENT_GID)"
echo ""

# Installa dipendenze
echo "📦 Verifica dipendenze..."
if ! command -v mount.cifs &> /dev/null; then
    echo "Installazione cifs-utils..."
    apt-get update -qq
    apt-get install -y cifs-utils
fi
echo "✅ Dipendenze OK"
echo ""

# MONTAGGIO
echo "🔌 Inizio montaggio..."
echo "   Server: //$SERVER/$SHARE"
echo "   Utente SMB: $USERNAME"
echo "   Dominio: $DOMAIN"
echo "   Mount point: $MOUNT_POINT"
echo ""

sudo umount $MOUNT_POINT 2>/dev/null || true
sudo mkdir -p $MOUNT_POINT
sudo chown -R $CURRENT_USER:users $MOUNT_POINT
sudo chmod 7777 $MOUNT_POINT

sudo PASSWD=$PASSWD mount -t cifs -o rw,exec,username="$USERNAME",domain=$DOMAIN,password=$PASSWD,uid=$CURRENT_UID,gid=$CURRENT_GID,file_mode=0777,dir_mode=0777 //$SERVER/$SHARE $MOUNT_POINT

# VERIFICA MONTAGGIO
if mountpoint -q $MOUNT_POINT; then
    echo "✅ Server montato correttamente"
    echo ""
    echo "Contenuto di $MOUNT_POINT:"
    ls -lah $MOUNT_POINT
    echo ""
else
    echo "❌ Errore nel montaggio"
    exit 1
fi

# CONFIGURA FSTAB PER MONTAGGIO PERMANENTE
echo "📝 Configurazione permanente..."
CREDS_FILE="/etc/smb-creds-gh5dev"

# Crea file credenziali
cat > $CREDS_FILE << CREDS
username=$USERNAME
domain=$DOMAIN
password=$PASSWD
CREDS
chmod 600 $CREDS_FILE

# Aggiungi a fstab se non esiste
if ! grep -q "//$SERVER/$SHARE" /etc/fstab; then
    echo "//$SERVER/$SHARE $MOUNT_POINT cifs credentials=$CREDS_FILE,uid=$CURRENT_UID,gid=$CURRENT_GID,file_mode=0777,dir_mode=0777,rw,exec 0 0" >> /etc/fstab
    echo "✅ Aggiunto a /etc/fstab"
else
    echo "✅ Già in /etc/fstab"
fi
echo ""

# CARTELLA LOCALE
echo "📁 Verifica cartella locale..."
mkdir -p $CARTELLA_LOCALE
chmod 755 $CARTELLA_LOCALE
echo "✅ Cartella locale: $CARTELLA_LOCALE"
echo ""

# CONFERMA PRIMA DI SINCRONIZZARE
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   CONFERMA SINCRONIZZAZIONE                               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📤 I file di:"
echo "   $CARTELLA_LOCALE"
echo ""
echo "Verranno spostati in:"
echo "   $MOUNT_POINT"
echo ""
echo "⚠️  Attenzione:"
echo "   - I file verranno ELIMINATI dalla cartella locale dopo la copia"
echo "   - Se la rete cade, il programma riproverà automaticamente"
echo ""
echo "📌 File ESCLUSI (rimangono in locale):"
for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    echo "   - $pattern"
done
echo ""

read -p "Vuoi continuare? (s/n) [n]: " conferma
if [ "$conferma" != "s" ] && [ "$conferma" != "S" ]; then
    echo ""
    echo "❌ Sincronizzazione annullata"
    exit 0
fi

echo ""
echo "🔄 Avvio sincronizzazione..."
echo ""

if [ ! -f "$SYNC_SCRIPT" ]; then
    echo "❌ Script sync_folder.sh non trovato in $(pwd)"
    echo "   Posiziona sync_folder.sh nella stessa cartella di questo script"
    exit 1
fi

bash $SYNC_SCRIPT $CARTELLA_LOCALE $MOUNT_POINT
