#!/bin/bash

##############################################################################
# Script helper per montare condivisioni di rete (SMB, NFS)
##############################################################################

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Utility Montaggio Condivisioni di Rete                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Menu di scelta
echo "Tipo di condivisione:"
echo "1) SMB/CIFS (Windows/Samba)"
echo "2) NFS (Network File System)"
echo ""
read -p "Seleziona (1-2): " tipo_condivisione

mount_point=""
read -p "Punto di montaggio (es. /mnt/rete): " mount_point
mount_point="${mount_point:-/mnt/rete}"

if [ "$tipo_condivisione" = "1" ]; then
    # SMB/CIFS
    read -p "Indirizzo server (es. 192.168.1.100 o server.local): " server
    read -p "Percorso condivisione (es. condivisione): " condivisione
    read -p "Nome utente: " username
    read -s -p "Password: " password
    echo ""
    
    read -p "Montaggio permanente in /etc/fstab? (y/n) [n]: " permanente
    
    # Crea il punto di montaggio
    sudo mkdir -p "$mount_point"
    
    # Crea un file di credenziali
    CREDS_FILE="$HOME/.smbcredentials"
    cat > "$CREDS_FILE" << EOF
username=$username
password=$password
EOF
    chmod 600 "$CREDS_FILE"
    
    # Monta la condivisione
    echo "Montaggio della condivisione SMB..."
    sudo mount -t cifs //"$server"/"$condivisione" "$mount_point" \
        -o credentials="$CREDS_FILE",uid=$(id -u),gid=$(id -g)
    
    if [ "$permanente" = "y" ] || [ "$permanente" = "Y" ]; then
        echo "Aggiunta al file fstab..."
        echo "//$server/$condivisione $mount_point cifs credentials=$CREDS_FILE,uid=$(id -u),gid=$(id -g) 0 0" | sudo tee -a /etc/fstab
        echo "✅ Montaggio permanente configurato"
    fi
    
elif [ "$tipo_condivisione" = "2" ]; then
    # NFS
    read -p "Server NFS (es. 192.168.1.100 o nfs.local): " server
    read -p "Percorso esportato (es. /export/home): " percorso
    
    read -p "Montaggio permanente in /etc/fstab? (y/n) [n]: " permanente
    
    # Installa client NFS se necessario
    if ! command -v mount.nfs &> /dev/null; then
        echo "Installazione client NFS..."
        if command -v apt &> /dev/null; then
            sudo apt install -y nfs-common
        elif command -v yum &> /dev/null; then
            sudo yum install -y nfs-utils
        fi
    fi
    
    # Crea il punto di montaggio
    sudo mkdir -p "$mount_point"
    
    # Monta la condivisione
    echo "Montaggio della condivisione NFS..."
    sudo mount -t nfs "$server:$percorso" "$mount_point"
    
    if [ "$permanente" = "y" ] || [ "$permanente" = "Y" ]; then
        echo "Aggiunta al file fstab..."
        echo "$server:$percorso $mount_point nfs defaults 0 0" | sudo tee -a /etc/fstab
        echo "✅ Montaggio permanente configurato"
    fi
else
    echo "❌ Opzione non valida"
    exit 1
fi

echo ""
echo "✅ Condivisione montata: $mount_point"
echo ""
echo "Verifica il montaggio:"
echo "  ls -la $mount_point"
echo "  mount | grep $mount_point"
echo ""
echo "Per smontare:"
echo "  sudo umount $mount_point"
echo ""

if [ "$permanente" = "y" ] || [ "$permanente" = "Y" ]; then
    echo "⚠️  Ricorda: il montaggio verrà eseguito automaticamente al boot"
    echo "   Se necessario, puoi modificare /etc/fstab o eseguire: sudo umount $mount_point"
fi
