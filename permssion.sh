# Installa authbind
sudo apt install authbind

# Permetti l'uso della porta 80 al tuo utente
sudo touch /etc/authbind/byport/80
sudo chown riccardo:riccardo /etc/authbind/byport/80
sudo chmod 755 /etc/authbind/byport/80