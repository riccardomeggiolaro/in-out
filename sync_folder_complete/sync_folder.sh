#!/bin/bash

##############################################################################
# Script di sincronizzazione cartella locale <-> cartella di rete
# Sincronizza i file dalla cartella locale a quella di rete, poi li elimina
# Gestisce disconnessioni di rete e ri-sincronizza al ripristino
##############################################################################

# ============ CONFIGURAZIONE ============
CARTELLA_LOCALE="${1:-.}"              # Cartella locale da sincronizzare
CARTELLA_RETE="${2:-/mnt/rete/sync}"   # Cartella di rete (mount point)
LOG_FILE="/tmp/sync_monitor.log"       # File di log
STATE_FILE="/tmp/sync_state.db"        # Database di stato
INTERVALLO_CONTROLLO=5                 # Secondi tra i controlli di connessione
MAX_RETRY=3                            # Numero massimo di tentativi

# ============ COLORI PER OUTPUT ============
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============ FUNZIONI ============

# Logging con timestamp
log() {
    local livello=$1
    shift
    local messaggio="$@"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$livello] $messaggio" >> "$LOG_FILE"
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $messaggio"
}

# Errore
errore() {
    echo -e "${RED}[ERRORE]${NC} $@" | tee -a "$LOG_FILE"
}

# Successo
successo() {
    echo -e "${GREEN}[OK]${NC} $@" | tee -a "$LOG_FILE"
}

# Avviso
avviso() {
    echo -e "${YELLOW}[AVVISO]${NC} $@" | tee -a "$LOG_FILE"
}

# Controlla se una rete è raggiungibile
check_connessione() {
    # Prova a fare ping al gateway
    if ping -c 1 -W 2 8.8.8.8 &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Controlla se la cartella di rete è montata e accessibile
check_cartella_rete() {
    if [ -d "$CARTELLA_RETE" ] && touch "$CARTELLA_RETE/.test_write" 2>/dev/null; then
        rm -f "$CARTELLA_RETE/.test_write"
        return 0
    else
        return 1
    fi
}

# Sincronizza un file singolo
sincronizza_file() {
    local file="$1"
    local percorso_relativo="${file#$CARTELLA_LOCALE/}"
    local destinazione="$CARTELLA_RETE/$percorso_relativo"
    local dir_destinazione=$(dirname "$destinazione")
    
    log "INFO" "Sincronizzando: $file"
    
    # Crea la cartella di destinazione se non esiste
    if ! mkdir -p "$dir_destinazione" 2>/dev/null; then
        errore "Impossibile creare cartella: $dir_destinazione"
        return 1
    fi
    
    # Copia il file con rsync
    if rsync -av --progress "$file" "$destinazione" >> "$LOG_FILE" 2>&1; then
        log "INFO" "File sincronizzato con successo: $file"
        # Salva nel database di stato
        echo "$file" >> "$STATE_FILE"
        return 0
    else
        errore "Errore nella sincronizzazione di: $file"
        return 1
    fi
}

# Sincronizza file locale a rete e lo elimina
sposta_in_rete() {
    local file="$1"
    
    # Controlla se il file esiste ancora (potrebbe essere già stato eliminato)
    if [ ! -f "$file" ]; then
        log "INFO" "File già eliminato: $file"
        return 0
    fi
    
    # Salta i file .db (non vengono sincronizzati)
    if [[ "$file" == *.db ]]; then
        log "INFO" "File .db ignorato: $file"
        return 0
    fi
    
    # Tenta la sincronizzazione
    local tentativi=0
    while [ $tentativi -lt $MAX_RETRY ]; do
        if check_cartella_rete; then
            if sincronizza_file "$file"; then
                # Elimina il file locale dopo la sincronizzazione
                if rm -f "$file"; then
                    successo "File spostato in rete: $file"
                    return 0
                else
                    errore "Impossibile eliminare il file locale: $file"
                    return 1
                fi
            fi
        else
            avviso "Cartella di rete non accessibile, tentativo $((tentativi+1))/$MAX_RETRY"
            sleep 2
        fi
        tentativi=$((tentativi+1))
    done
    
    avviso "Impossibile sincronizzare $file dopo $MAX_RETRY tentativi. Riproverò al prossimo controllo."
    return 1
}

# Sincronizza tutti i file pendenti quando si riconnette
sincronizza_pendenti() {
    log "INFO" "Sincronizzando file pendenti..."
    
    find "$CARTELLA_LOCALE" -type f | while read file; do
        if ! grep -q "^$file$" "$STATE_FILE" 2>/dev/null; then
            sposta_in_rete "$file"
        fi
    done
    
    successo "Sincronizzazione file pendenti completata"
}

# Monitora la connessione di rete in background
monitora_connessione() {
    local stato_precedente=0
    
    while true; do
        if check_connessione; then
            if [ $stato_precedente -eq 0 ]; then
                # Passaggio da offline a online
                successo "Connessione di rete ripristinata!"
                if check_cartella_rete; then
                    sincronizza_pendenti
                fi
            fi
            stato_precedente=1
        else
            if [ $stato_precedente -eq 1 ]; then
                # Passaggio da online a offline
                avviso "Connessione di rete persa!"
            fi
            stato_precedente=0
        fi
        
        sleep $INTERVALLO_CONTROLLO
    done
}

# Valida le cartelle di input
valida_cartelle() {
    if [ ! -d "$CARTELLA_LOCALE" ]; then
        errore "Cartella locale non esiste: $CARTELLA_LOCALE"
        exit 1
    fi
    
    if [ ! -d "$CARTELLA_RETE" ]; then
        errore "Cartella di rete non esiste o non è montata: $CARTELLA_RETE"
        exit 1
    fi
    
    # Converti a percorsi assoluti
    CARTELLA_LOCALE=$(cd "$CARTELLA_LOCALE" && pwd)
    CARTELLA_RETE=$(cd "$CARTELLA_RETE" && pwd)
}

# Inizializza il database di stato
inizializza_stato() {
    if [ ! -f "$STATE_FILE" ]; then
        touch "$STATE_FILE"
    fi
}

# ============ MAIN ============

main() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   Sincronizzatore Cartelle Locale <-> Rete               ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Controlla i prerequisiti
    if ! command -v inotifywait &> /dev/null; then
        errore "inotify-tools non installato. Installa con: sudo apt install inotify-tools"
        exit 1
    fi
    
    if ! command -v rsync &> /dev/null; then
        errore "rsync non installato. Installa con: sudo apt install rsync"
        exit 1
    fi
    
    # Valida le cartelle
    valida_cartelle
    inizializza_stato
    
    log "INFO" "==================== INIZIO SINCRONIZZAZIONE ===================="
    log "INFO" "Cartella locale: $CARTELLA_LOCALE"
    log "INFO" "Cartella rete: $CARTELLA_RETE"
    log "INFO" "Log: $LOG_FILE"
    log "INFO" "=============================================================="
    
    successo "Cartelle validate correttamente"
    echo "Locale: $CARTELLA_LOCALE"
    echo "Rete:   $CARTELLA_RETE"
    echo ""
    
    # Avvia il monitoraggio della connessione in background
    monitora_connessione &
    MONITOR_PID=$!
    log "INFO" "Monitoraggio connessione avviato (PID: $MONITOR_PID)"
    
    # Monitora i cambiamenti nella cartella locale
    log "INFO" "In ascolto di cambiamenti nella cartella locale..."
    successo "Sistema pronto. In ascolto di nuovi file..."
    echo ""
    
    inotifywait -m -e create -e moved_to "$CARTELLA_LOCALE" -r |
    while read cartella evento file; do
        # Ignora i file nascosti
        if [[ "$file" == .* ]]; then
            continue
        fi
        
        file_path="$cartella$file"
        
        # Attendi un momento per assicurarti che il file sia completamente scritto
        sleep 0.5
        
        # Se è una cartella, ignora
        if [ -d "$file_path" ]; then
            log "INFO" "Cartella rilevata, ignorata: $file_path"
            continue
        fi
        
        log "INFO" "File rilevato: $file_path"
        sposta_in_rete "$file_path"
    done
}

# Gestione dei segnali di chiusura
trap 'errore "Script interrotto"; exit 0' SIGINT SIGTERM

# Avvia il programma principale
main
