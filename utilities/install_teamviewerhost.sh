#!/bin/bash

# Rimuovi eventuali installazioni precedenti
sudo apt remove teamviewer teamviewer-host -y
sudo apt autoremove -y
sudo rm -rf /opt/teamviewer
sudo rm -rf /var/log/teamviewer*

# Scarica e installa TeamViewer Host
wget https://download.teamviewer.com/download/linux/teamviewer-host_amd64.deb -P ~/Downloads/
sudo dpkg -i ~/Downloads/teamviewer-host_amd64.deb
sudo apt-get install -f -y

# Avvia e abilita il daemon
sudo systemctl enable teamviewerd
sudo teamviewer --daemon restart
sleep 20

# Imposta la password
sudo teamviewer passwd tvh318101

# Mostra ID
sudo teamviewer info | grep "TeamViewer ID"