# Guida Rapida - Sincronizzatore Cartelle

## Avvio Veloce (5 minuti)

### 1️⃣ Installazione

```bash
# Clona o scarica i file
cd ~/sync-folder

# Esegui l'installazione
chmod +x install.sh
./install.sh
```

### 2️⃣ Uso Base

Il programma sincronizzerà automaticamente i file:

```bash
# Copia un file nella cartella locale
cp ~/mio_file.pdf ~/sync_local/

# Guarda il file essere copiato in rete e poi eliminato dalla cartella locale
cat /tmp/sync_monitor.log
```

---

## Esempi Pratici

### 📁 Scenario 1: Sincronizzare cartella locale con NAS

```bash
# 1. Monta il NAS
./mount-network.sh
# Segui le istruzioni per montare il NAS in /mnt/nas

# 2. Avvia il sincronizzatore
./sync_folder.sh ~/documenti /mnt/nas/backup
```

**Cosa succede:**
- I file aggiunti a `~/documenti` vengono copiati in `/mnt/nas/backup`
- Dopo la copia, vengono eliminati da `~/documenti`
- Se il NAS non è raggiungibile, il programma riprova automaticamente
- Una volta ripristinata la connessione, sincronizza i file in sospeso

---

### 📱 Scenario 2: Backup automatico da laptop

```bash
# 1. Crea cartelle
mkdir -p ~/backup_local /mnt/server/backup

# 2. Monta il server
sudo mount -t cifs //server/backup /mnt/server/backup -o username=user

# 3. Installa come servizio
sudo ./install_service.sh
# Quando richiesto:
#   Cartella locale: /home/utente/backup_local
#   Cartella rete: /mnt/server/backup

# 4. Il servizio si avvia automaticamente al riavvio
```

**Vantaggi:**
- Il backup avviene automaticamente
- Anche in caso di riavvio inaspettato, i file in sospeso vengono sincronizzati
- Usa `sudo systemctl status sync-folder` per verificare

---

### 🖥️ Scenario 3: Sincronizzazione da più PC

```bash
# PC 1 (ufficio)
./sync_folder.sh ~/ufficio /mnt/condivisione/backup_ufficio

# PC 2 (casa)
./sync_folder.sh ~/casa /mnt/condivisione/backup_casa

# PC 3 (laptop)
./sync_folder.sh ~/laptop /mnt/condivisione/backup_laptop

# I file da ogni PC vanno in cartelle separate sul NAS
```

---

### 🌐 Scenario 4: Sincronizzazione con condivisione Windows

```bash
# Monta la condivisione Windows
./mount-network.sh
# Seleziona: 1 (SMB/CIFS)
# Server: 192.168.1.10
# Condivisione: dati
# Username: nomeutente
# Password: password

# Sincronizza
./sync_folder.sh ~/dati /mnt/rete

# Opzionale: monta automaticamente al boot
# (Lo script te lo chiede durante il montaggio)
```

---

### ⚠️ Scenario 5: Rete instabile

Se la rete si disconnette spesso:

```bash
# Modifica i parametri nel script
# Aumenta INTERVALLO_CONTROLLO per ridurre i controlli
# Aumenta MAX_RETRY per più tentativi

# Oppure usa il config file
cp config.env.example config.env
# Modifica config.env
source config.env
./sync_folder.sh "$CARTELLA_LOCALE" "$CARTELLA_RETE"
```

---

## Comandi Utili

### 📊 Monitoraggio

```bash
# Visualizza log in tempo reale
tail -f /tmp/sync_monitor.log

# Visualizza solo gli errori
grep ERROR /tmp/sync_monitor.log

# Conta i file sincronizzati
wc -l /tmp/sync_state.db

# Ultimi 50 eventi
tail -50 /tmp/sync_monitor.log
```

### 🔧 Se installato come servizio

```bash
# Stato del servizio
sudo systemctl status sync-folder

# Log del servizio
sudo journalctl -u sync-folder -f

# Ultimi 100 log
sudo journalctl -u sync-folder -n 100

# Log degli ultimi 30 minuti
sudo journalctl -u sync-folder --since "30 min ago"

# Riavvia il servizio
sudo systemctl restart sync-folder
```

### 🗑️ Pulizia

```bash
# Cancella i log
rm /tmp/sync_monitor.log

# Cancella lo stato (attenzione: risincronizzerà tutto)
rm /tmp/sync_state.db

# Entrambi
rm /tmp/sync_monitor.log /tmp/sync_state.db
```

---

## Troubleshooting Comune

### ❌ "Cartella di rete non esiste"

```bash
# Controlla se è montata
mount | grep rete

# Se non è montata, montala
./mount-network.sh

# Verifica i permessi
ls -la /mnt/rete
```

### ❌ "Permesso negato"

```bash
# Controlla i permessi sulla cartella locale
ls -la ~/sync_local

# Dai permessi se necessario
chmod -R 755 ~/sync_local

# Se è il montaggio di rete, verifica le credenziali
# Ricollega con: sudo umount /mnt/rete && ./mount-network.sh
```

### ❌ "File non si sincronizzano"

```bash
# Verifica il log
tail -50 /tmp/sync_monitor.log

# Prova a sincronizzare manualmente
rsync -av ~/sync_local/file.txt /mnt/rete/

# Se rsync funziona manualmente, il problema potrebbe essere:
# - inotifywait non rileva i cambiamenti
# - Cartella locale non ha i permessi giusti
```

### ⏱️ "Il programma consuma molta CPU"

```bash
# Verifica cosa monitora
ls /tmp/sync_monitor.log

# Riduci la frequenza di controllo
# Modifica INTERVALLO_CONTROLLO da 5 a 30 secondi
# Riavvia il programma
```

---

## Configurazioni Avanzate

### Sincronizzazione con compressione

Modifica lo script `sync_folder.sh` e cambia la riga rsync:

```bash
# Originale
rsync -av --progress "$file" "$destinazione"

# Con compressione
rsync -avz --progress "$file" "$destinazione"
```

### Escludere certi file

```bash
# Modifica la riga rsync
rsync -av --exclude="*.tmp" --exclude=".*" "$file" "$destinazione"
```

### Sincronizzazione con checksum

```bash
# Usa checksum invece di timestamp
rsync -avc --checksum "$file" "$destinazione"
```

---

## Performance Tips

| Situazione | Soluzione |
|-----------|----------|
| Molti file piccoli | Aumenta `INTERVALLO_CONTROLLO` |
| Rete lenta | Usa compressione: aggiungi `z` a rsync |
| Rete instabile | Aumenta `MAX_RETRY` |
| Cartella molto grande | Escludi file non necessari |
| Disco lento | Usa SSD per la cartella locale |

---

## Disinstallazione

```bash
# Se installato come servizio
sudo systemctl stop sync-folder
sudo systemctl disable sync-folder
sudo rm /etc/systemd/system/sync-folder.service
sudo systemctl daemon-reload

# Rimuovi i file
rm ~/.local/bin/sync_folder.sh
rm ~/sync-folder/*

# Cancella i log
rm /tmp/sync_monitor.log /tmp/sync_state.db
```

---

## Domande Frequenti

**D: I file eliminati da una cartella vengono eliminati anche dalla rete?**  
R: No, questo script **solo copia** da locale a rete e **elimina dalla locale**. La cartella di rete rimane intatta.

**D: Posso sincronizzare da rete a locale?**  
R: No, il funzionamento è unidirezionale (locale → rete). Se serve bidirezionale, usa `rsync` o `syncthing`.

**D: Quanto spazio occupa il database?**  
R: Circa 1 byte per carattere del percorso del file. Per 10.000 file = ~1 MB.

**D: Posso sincronizzare più cartelle?**  
R: Sì, avvia più istanze del programma con cartelle diverse.

**D: Cosa succede se la rete cade durante una copia?**  
R: Il file rimane nella cartella locale e il programma riprova automaticamente.

---

## Supporto e Debug

### Modalità debug
```bash
bash -x ./sync_folder.sh /cartella/locale /cartella/rete 2>&1 | tee debug.log
```

### Verifica manuale della sincronizzazione
```bash
rsync -avv ~/sync_local/ /mnt/rete/ --dry-run  # Prova senza copiare
rsync -avv ~/sync_local/ /mnt/rete/            # Copia effettivamente
```

### Controlla l'attività di inotify
```bash
inotifywait -m ~/sync_local -r  # Monitora i cambiamenti
```

---

**Creato per:** Linux / Ubuntu / Debian / CentOS  
**Ultima modifica:** 2025
