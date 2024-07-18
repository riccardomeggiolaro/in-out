# ==============================================================
# 		GESTIONE LOGGER				=
# ==============================================================

# ==== LIBRERIE DA IMPORTARE ===================================
import os
import time
import inspect
import lib.lb_config as lb_config
from datetime import datetime
# ==============================================================

# ==== FUNZIONI RICHIAMABILI DA MODULI ESTERNI =================
# Funzione per stampare messaggi di debug con informazioni aggiuntive.
# Questa funzione accetta un messaggio come input e stampa il timestamp corrente, il modulo in cui è chiamata e il messaggio di debug.
def debug(msg):
    # defa_logfile = lb_config.g_defalogfile  # File di log di default
    now = datetime.now()  # Data e ora corrente
    module = os.path.splitext(os.path.basename(inspect.stack()[1].filename))[0].lower()  # Ottiene il nome del modulo corrente
    if len(module) > 10:
        module = module[:9] + "~"  # Tronca il nome del modulo se è più lungo di 10 caratteri
    else:
        module = module.ljust(10)  # Allunga il nome del modulo se è più corto di 10 caratteri
    module = module + "|"  # Aggiunge un separatore "|" al nome del modulo
    print("")  # Stampa una nuova riga

    # Stampa il messaggio di debug con il timestamp, il modulo e il messaggio stesso
    print("(debug)" + now.strftime("%Y/%m/%d %H:%M:%S"), module, msg, end="")

# Funzione per stampare messaggi informativi con informazioni aggiuntive.
# Questa funzione accetta un messaggio come input e stampa il timestamp corrente, il modulo in cui è chiamata e il messaggio informativo.
def info(msg):
    # defa_logfile = lb_config.g_defalogfile  # File di log di default
    now = datetime.now()  # Data e ora corrente
    module = os.path.splitext(os.path.basename(inspect.stack()[1].filename))[0].lower()  # Ottiene il nome del modulo corrente
    if type(msg) is not str:
        msg = str(msg)  # Converte il messaggio in una stringa se non lo è già

    if len(module) > 10:
        module = module[:9] + "~"  # Tronca il nome del modulo se è più lungo di 10 caratteri
    else:
        module = module.ljust(10)  # Allunga il nome del modulo se è più corto di 10 caratteri
    module = module + "|"  # Aggiunge un separatore "|" al nome del modulo
    newline()  # Aggiunge una nuova riga al file di log, se specificato

    if lb_config.g_defalogfile:  # Se è specificato un file di log
        with open(lb_config.g_defalogfile, 'a') as f:
            # Scrive nel file di log il timestamp, il modulo, e il messaggio informativo
            f.write(("I") + now.strftime(" %Y/%m/%d %H:%M:%S ") + module.ljust(10) + msg)

    # Stampa il messaggio informativo con il timestamp, il modulo e il messaggio stesso nella console
    print(f"{bcolors.OKGREEN}(info){bcolors.ENDC}", end="")
    print(now.strftime("%Y/%m/%d %H:%M:%S"), module, msg, end="")

# Funzione per stampare messaggi di avviso con informazioni aggiuntive.
# Questa funzione accetta un messaggio come input e stampa il timestamp corrente, il modulo in cui è chiamata e il messaggio di avviso.
def warning(msg):
    defa_logfile = lb_config.g_defalogfile  # File di log di default
    now = datetime.now()  # Data e ora corrente
    module = os.path.splitext(os.path.basename(inspect.stack()[1].filename))[0].lower()  # Ottiene il nome del modulo corrente
    if type(msg) is not str:
        msg = str(msg)  # Converte il messaggio in una stringa se non lo è già

    if len(module) > 10:
        module = module[:9] + "~"  # Tronca il nome del modulo se è più lungo di 10 caratteri
    else:
        module = module.ljust(10)  # Allunga il nome del modulo se è più corto di 10 caratteri
    module = module + "|"  # Aggiunge un separatore "|" al nome del modulo
    newline()  # Aggiunge una nuova riga al file di log, se specificato

    if defa_logfile:  # Se è specificato un file di log
        with open(defa_logfile, 'a') as f:
            # Scrive nel file di log il timestamp, il modulo, e il messaggio di avviso
            f.write(("W") + now.strftime(" %Y/%m/%d %H:%M:%S ") + module.ljust(10) + msg)

    # Stampa il messaggio di avviso con il timestamp, il modulo e il messaggio stesso nella console
    print(f"{bcolors.WARNING}(warn){bcolors.ENDC}", now.strftime("%Y/%m/%d %H:%M:%S"), module, msg, end="")

# Funzione per stampare messaggi di errore con informazioni aggiuntive.
# Questa funzione accetta un messaggio come input e stampa il timestamp corrente, il modulo in cui è chiamata e il messaggio di errore.
def error(msg):
    # defa_logfile = lb_config.g_defalogfile  # File di log di default
    now = datetime.now()  # Data e ora corrente
    module = os.path.splitext(os.path.basename(inspect.stack()[1].filename))[0].lower()  # Ottiene il nome del modulo corrente
    if type(msg) is not str:
        msg = str(msg)  # Converte il messaggio in una stringa se non lo è già

    if len(module) > 10:
        module = module[:9] + "~"  # Tronca il nome del modulo se è più lungo di 10 caratteri
    else:
        module = module.ljust(10)  # Allunga il nome del modulo se è più corto di 10 caratteri
    module = module + "|"  # Aggiunge un separatore "|" al nome del modulo
    newline()  # Aggiunge una nuova riga al file di log, se specificato

    if lb_config.g_defalogfile:  # Se è specificato un file di log
        with open(lb_config.g_defalogfile, 'a') as f:
            # Scrive nel file di log il timestamp, il modulo, e il messaggio di errore
            f.write(("E") + now.strftime(" %Y/%m/%d %H:%M:%S ") + module.ljust(10) + msg)

    # Stampa il messaggio di errore con il timestamp, il modulo e il messaggio stesso nella console
    print(f"{bcolors.FAIL}(err!){bcolors.ENDC}", now.strftime("%Y/%m/%d %H:%M:%S"), module, msg, end="")

# Funzione per stampare un messaggio in linea con un eventuale attributo di formattazione.
# Questa funzione accetta un messaggio e un attributo di formattazione opzionale come input e lo stampa.
def inline(msg, att=""):
    if type(msg) is not str:
        msg = str(msg)  # Converte il messaggio in una stringa se non lo è già

    if att:  # Se è specificato un attributo di formattazione
        print(att, end="")  # Stampa l'attributo di formattazione

    if lb_config.g_defalogfile:  # Se è specificato un file di log
        with open(lb_config.g_defalogfile, 'a') as f:
            f.write(msg)  # Scrive il messaggio nel file di log

    print(msg, end="")  # Stampa il messaggio

    if att:  # Se è specificato un attributo di formattazione
        print(f"{bcolors.ENDC}", end="")  # Termina l'attributo di formattazione
# ==============================================================

# ==== FUNZIONI RICHIAMABILI DENTRO LA LIBRERIA ==================
# Definizione della classe bcolors che contiene costanti per formattare il testo con colori ANSI nella console.
class bcolors:
    HEADER = '\033[95m'   # Colore viola per l'intestazione
    OKBLUE = '\033[94m'   # Colore blu per le informazioni
    OKCYAN = '\033[96m'   # Colore ciano per informazioni speciali
    OKGREEN = '\033[92m'  # Colore verde per segnalare successo
    WARNING = '\033[93m'  # Colore giallo per avvisi
    FAIL = '\033[91m'     # Colore rosso per segnalare errori
    ENDC = '\033[0m'      # Sequenza per terminare il colore
    BOLD = '\033[1m'      # Imposta il testo in grassetto
    UNDERLINE = '\033[4m' # Sottolinea il testo

# Funzione per aggiungere una nuova riga a un file di log specificato da defa_logfile.
def newline():
    defa_logfile = lb_config.g_defalogfile  # Il file di log di default
    if defa_logfile:  # Se il file di log è specificato
        with open(defa_logfile, 'a') as f:  # Apre il file in modalità di append
            f.write(chr(13) + chr(10))  # Aggiunge una nuova riga nel file di log
    print("")  # Stampa una nuova riga nella console
# ==============================================================

# ==== MAINPRGLOOP ===============================================
# Funzione principale del programma per la gestione del log.
# Controlla periodicamente la dimensione del file di log e lo elimina se supera una dimensione massima specificata.
# Si interrompe quando il flag g_enabled di lb_config diventa False.
def mainprg():
    try:
        secwait = 5  # Intervallo di attesa in secondi
        # Continua il loop finché il flag g_enabled di lb_config è True
        while lb_config.g_enabled:
            # Gestisce il log
            if os.path.exists(lb_config.g_defalogfile):  # Controlla se il file di log esiste
                # Ottiene la dimensione del file di log in megabyte
                file_size = os.path.getsize(lb_config.g_defalogfile) / 1048576
                # Verifica se la dimensione del file di log supera la dimensione massima consentita
                if file_size >= lb_config.g_config["log"]["max-size-mb"]:
                    os.remove(lb_config.g_defalogfile)  # Rimuove il file di log
            time.sleep(secwait)  # Attende per un periodo di tempo specificato prima di ripetere il ciclo
    except Exception as e:
        info(e)
# ==============================================================

# ==== START ===================================================
# funzione che fa partire la libreria
def start():
	info("start")
	mainprg()
	info("end")
# ==============================================================

def stop():
    pass

# ==== INIT ====================================================
# funzione che inizializza delle globali
def init():
	info("log initialize")
# ==============================================================