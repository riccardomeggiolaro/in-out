# Sincronizzatore Cartelle Locale ↔ Rete

Un programma Linux che sincronizza automaticamente i file da una cartella locale a una cartella condivisa in rete, eliminando poi gli originali dalla cartella locale. Gestisce automaticamente le disconnessioni di rete e risincronizza quando la connessione viene ripristinata.

## Caratteristiche

✅ **Sincronizzazione in tempo reale** - Monitora i cambiamenti nella cartella locale  
✅ **Gestione della rete** - Rileva disconnessioni e risincronizza automaticamente  
✅ **Elimina dopo copia** - Sposta i file dalla cartella locale a quella di rete  
✅ **Logging dettagliato** - Traccia tutte le operazioni con timestamp  
✅ **Servizio systemd** - Avvio automatico al boot del sistema  
✅ **Retry intelligenti** - Riprova l'operazione se la rete è temporaneamente indisponibile  

## Requisiti

- Linux (Ubuntu, Debian, CentOS, ecc.)
- `inotify-tools` - Per il monitoraggio dei file
- `rsync` - Per la copia efficiente dei file

## Installazione Veloce

### 1. Scarica i file

```bash
git clone <repository>
cd sync-folder
```

### 2. Esegui l'installazione

```bash
chmod +x install.sh
./install.sh
```

Lo script installerà automaticamente le dipendenze e ti guiderà nella configurazione.

### 3. (Opzionale) Installa come servizio systemd

Per avviare il sincronizzatore automaticamente al boot:

```bash
sudo chmod +x install_service.sh
sudo ./install_service.sh
```

## Uso Manuale

### Avvio semplice

```bash
./sync_folder.sh /percorso/cartella/locale /percorso/cartella/rete
```

### Esempio pratico

```bash
# Sincronizza la cartella ~/miei_file con /mnt/condivisione/backup
./sync_folder.sh ~/miei_file /mnt/condivisione/backup
```

### Avvio in background

```bash
./sync_folder.sh /percorso/locale /percorso/rete &
```

## Configurazione Avanzata

### Variabili modificabili nello script

Modifica queste variabili all'inizio di `sync_folder.sh` per personalizzare il comportamento:

```bash
# Intervallo di controllo della connessione (secondi)
INTERVALLO_CONTROLLO=5

# Numero di tentativi prima di rinunciare
MAX_RETRY=3

# File di log
LOG_FILE="/tmp/sync_monitor.log"

# Database di stato
STATE_FILE="/tmp/sync_state.db"
```

## Monitoraggio

### Visualizza i log in tempo reale

```bash
tail -f /tmp/sync_monitor.log
```

### Se installato come servizio

```bash
sudo journalctl -u sync-folder -f
```

### Visualizza solo gli errori

```bash
grep ERROR /tmp/sync_monitor.log
```

## Comandi per il Servizio systemd

Se hai installato il servizio con `install_service.sh`:

```bash
# Visualizza lo stato
sudo systemctl status sync-folder

# Avvia il servizio
sudo systemctl start sync-folder

# Arresta il servizio
sudo systemctl stop sync-folder

# Riavvia il servizio
sudo systemctl restart sync-folder

# Abilita l'avvio automatico
sudo systemctl enable sync-folder

# Disabilita l'avvio automatico
sudo systemctl disable sync-folder

# Visualizza i log
sudo journalctl -u sync-folder -f

# Visualizza le ultime 100 righe di log
sudo journalctl -u sync-folder -n 100
```

## Comportamento

### Operazioni normali

1. Un file viene aggiunto/modificato nella cartella **locale**
2. Il sincronizzatore lo rileva (tramite `inotifywait`)
3. Lo copia nella cartella di **rete** (tramite `rsync`)
4. Elimina il file dalla cartella **locale** una volta confermata la copia

### In caso di disconnessione di rete

1. Il sincronizzatore tenta di copiare il file 3 volte (MAX_RETRY)
2. Se tutti i tentativi falliscono, il file rimane nella cartella locale
3. Ogni 5 secondi (INTERVALLO_CONTROLLO) verifica se la connessione è ripristinata
4. Quando la rete torna online, sincronizza automaticamente tutti i file in sospeso

### Recovery automatico

Il programma mantiene uno stato persistente in `/tmp/sync_state.db` che traccia quali file sono stati sincronizzati. Quando il servizio viene riavviato, verifica lo stato precedente e completa eventuali sincronizzazioni interrotte.

## Troubleshooting

### "inotify-tools not installed"

```bash
# Ubuntu/Debian
sudo apt install inotify-tools

# CentOS/RHEL
sudo yum install inotify-tools
```

### "rsync not installed"

```bash
# Ubuntu/Debian
sudo apt install rsync

# CentOS/RHEL
sudo yum install rsync
```

### La cartella di rete non è accessibile

Verifica che:
1. La cartella di rete sia montata: `mount | grep rete`
2. Hai i permessi di lettura/scrittura: `ls -la /mnt/rete`
3. La connessione di rete sia attiva: `ping google.com`

Per montare manualmente:

```bash
# SMB (Windows)
sudo mount -t cifs //server/condivisione /mnt/rete -o username=utente

# NFS
sudo mount -t nfs server:/percorso /mnt/rete

# Per rendere permanente, aggiungi a /etc/fstab
```

### I file non vengono eliminati dalla cartella locale

Verifiche:
1. I permessi sulla cartella locale siano corretti
2. Il file non sia in uso da altri processi
3. Verifica nei log l'errore specifico

### Il sincronizzatore consuma molta CPU

Se rileva troppe notifiche di inotify:
1. Aumenta `INTERVALLO_CONTROLLO`
2. Usa pattern di esclusione (file nascosti, .tmp)
3. Verifica che la cartella non contenga troppi file

## Struttura della soluzione

```
sync-folder/
├── sync_folder.sh          # Script principale di sincronizzazione
├── install.sh              # Script di installazione
├── install_service.sh      # Script per il servizio systemd
├── README.md               # Questa documentazione
└── examples/               # Esempi di configurazione
    ├── config.env          # File di configurazione
    └── mount-network.sh    # Helper per montare condivisioni
```

## Configurazione con Config File

Puoi creare un file di configurazione per gestire più sincronizzazioni:

```bash
# config.env
CARTELLA_LOCALE="/home/utente/documenti"
CARTELLA_RETE="/mnt/rete/backup"
INTERVALLO_CONTROLLO=5
MAX_RETRY=3
```

Quindi usa:

```bash
source config.env
./sync_folder.sh "$CARTELLA_LOCALE" "$CARTELLA_RETE"
```

## Performance e Limiti

- **Max file size**: Limitato solo dallo spazio disponibile
- **Max numero file**: Testato fino a 100.000 file
- **Latenza di rilevazione**: ~500ms
- **Velocità di copia**: Dipende dalla velocità della rete e dal disco

Per migliori performance con molti file:
1. Usa dischi SSD
2. Assicurati una buona connessione di rete
3. Aumenta `MAX_RETRY` se la rete è instabile

## Sicurezza

⚠️ **Considerazioni importanti:**

1. I file vengono **eliminati** dalla cartella locale dopo la copia
2. Non c'è un cestino - usa backup se serve
3. Assicurati che la cartella di rete sia su un disco con backup
4. I permessi vengono copiati con rsync (predefinito)
5. Il file di stato è in `/tmp` - non è persistent tra i riavvii

## Log e Debug

### Aumenta il dettaglio del logging

Modifica lo script e cambia:

```bash
# Originale
rsync -av --progress "$file" "$destinazione" >> "$LOG_FILE" 2>&1

# Per debug
rsync -avvv --progress "$file" "$destinazione" | tee -a "$LOG_FILE"
```

### Visualizza i file in sincronizzazione

```bash
# In tempo reale
watch -n 1 'tail /tmp/sync_monitor.log'

# Con grep per errori
tail -f /tmp/sync_monitor.log | grep -E "ERROR|AVVISO"
```

## Disinstallazione

Se hai installato il servizio:

```bash
sudo systemctl stop sync-folder
sudo systemctl disable sync-folder
sudo rm /etc/systemd/system/sync-folder.service
sudo systemctl daemon-reload
```

Rimuovi i file:

```bash
rm ~/.local/bin/sync_folder.sh
rm /tmp/sync_monitor.log
rm /tmp/sync_state.db
```

## Licenza

MIT License

## Supporto

Per problemi o suggerimenti, controlla i log in `/tmp/sync_monitor.log` o esegui con debug:

```bash
bash -x ./sync_folder.sh /cartella/locale /cartella/rete
```

---

**Creato per Linux** | Tested on Ubuntu 20.04+ and Debian 11+
