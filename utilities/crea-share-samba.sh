#!/bin/bash
# Crea una cartella condivisa Samba (es. su una VM Debian/Ubuntu in cloud)
# per le prove di sincronizzazione di in-out.
#
# Uso (sulla VM):
#   curl -fsSL <url di questo file> | sudo bash -s UTENTE PASSWORD
#   oppure:  sudo bash crea-share-samba.sh UTENTE PASSWORD
#
# Variabili opzionali: SHARE_NAME (default inout), SHARE_DIR (default /srv/inout),
#                      INSTALL_TAILSCALE (si/no, default si)
set -e

SMB_USER="${1:-}"
SMB_PASSWORD="${2:-}"
SHARE_NAME="${SHARE_NAME:-inout}"
SHARE_DIR="${SHARE_DIR:-/srv/inout}"
INSTALL_TAILSCALE="${INSTALL_TAILSCALE:-si}"

if [ -z "$SMB_USER" ] || [ -z "$SMB_PASSWORD" ]; then
    echo "Uso: sudo bash $0 UTENTE PASSWORD"
    exit 1
fi
if [ "$(id -u)" -ne 0 ]; then
    echo "Esegui lo script con sudo"
    exit 1
fi

echo "==> Installo Samba"
apt-get update -y </dev/null
DEBIAN_FRONTEND=noninteractive apt-get install -y samba smbclient </dev/null

echo "==> Creo l'utente di sistema '$SMB_USER'"
if ! id "$SMB_USER" >/dev/null 2>&1; then
    useradd -M -s /usr/sbin/nologin "$SMB_USER"
fi

echo "==> Imposto la password Samba per '$SMB_USER'"
(echo "$SMB_PASSWORD"; echo "$SMB_PASSWORD") | smbpasswd -s -a "$SMB_USER"

echo "==> Creo la cartella $SHARE_DIR/csv/in"
mkdir -p "$SHARE_DIR/csv/in"
chown -R "$SMB_USER:$SMB_USER" "$SHARE_DIR"
chmod -R 775 "$SHARE_DIR"

echo "==> Configuro la condivisione [$SHARE_NAME]"
# Rimuove una eventuale condivisione con lo stesso nome e la riscrive
sed -i "/^\[$SHARE_NAME\]/,/^\[/{/^\[$SHARE_NAME\]/d;/^\[/!d}" /etc/samba/smb.conf
cat >> /etc/samba/smb.conf <<EOF

[$SHARE_NAME]
   path = $SHARE_DIR
   read only = no
   browseable = yes
   valid users = $SMB_USER
   force user = $SMB_USER
   create mask = 0664
   directory mask = 0775
   smb encrypt = required
EOF

testparm -s >/dev/null
systemctl enable smbd >/dev/null 2>&1 || true
systemctl restart smbd

echo "==> Verifico l'accesso"
smbclient "//localhost/$SHARE_NAME" -U "$SMB_USER%$SMB_PASSWORD" -c ls

if [ "$INSTALL_TAILSCALE" = "si" ]; then
    echo "==> Installo Tailscale"
    if ! command -v tailscale >/dev/null 2>&1; then
        curl -fsSL https://tailscale.com/install.sh | sh
    fi
    echo ">>> Apri il link che compare qui sotto per autorizzare la macchina <<<"
    tailscale up
    # Consente il traffico dalla VPN se il firewall iptables blocca il resto
    if command -v iptables >/dev/null 2>&1; then
        iptables -C INPUT -i tailscale0 -j ACCEPT 2>/dev/null || iptables -I INPUT -i tailscale0 -j ACCEPT
        if command -v netfilter-persistent >/dev/null 2>&1; then netfilter-persistent save || true; fi
    fi
    IP=$(tailscale ip -4 | head -n1)
else
    IP=$(hostname -I | awk '{print $1}')
fi

echo
echo "================ FATTO ================"
echo " Dati da inserire in in-out:"
echo "   protocol   : samba"
echo "   ip         : $IP"
echo "   share_name : $SHARE_NAME"
echo "   sub_path   : (vuoto)"
echo "   username   : $SMB_USER"
echo "   password   : (quella passata allo script)"
echo " Cartella per i file del cliente: $SHARE_DIR/csv/in"
echo "======================================="
