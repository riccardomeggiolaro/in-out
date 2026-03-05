# BARON IN-OUT - Testo Presentazione Cliente

---

## 1. Introduzione al Sistema

Buongiorno e grazie per il vostro tempo. Oggi vi presentiamo **BARON IN-OUT**, il nostro sistema di pesatura industriale progettato per gestire in modo completo e automatizzato le operazioni di ingresso e uscita dei veicoli dal vostro impianto.

Il sistema nasce per rispondere alle esigenze di realta come centri logistici, impianti di gestione rifiuti e stabilimenti industriali, dove e fondamentale tracciare con precisione i materiali in entrata e in uscita tramite la pesatura dei veicoli.

BARON IN-OUT e una soluzione completa: un software che integra interfaccia web, gestione dati e collegamento diretto con l'hardware di pesatura, il tutto accessibile da un normale browser.

---

## 2. Flusso Operativo Principale

Vediamo ora come funziona concretamente il sistema, seguendo il percorso di un veicolo dall'ingresso all'uscita.

**Identificazione del veicolo.** Quando un mezzo arriva all'impianto, l'operatore puo identificarlo in tre modi: tramite la scansione di un badge RFID, inserendo manualmente la targa, oppure selezionando il veicolo da una lista gia presente nel sistema. Questo garantisce flessibilita in base alla dotazione del vostro impianto.

**Pesatura in ingresso.** Il veicolo sale sulla bilancia e il sistema registra automaticamente il primo peso. Questo valore viene salvato come "Weight1" e associato all'accesso appena creato.

**Inserimento dati.** A questo punto l'operatore puo completare le informazioni: l'autista, il soggetto (cliente o fornitore), il materiale trasportato e un eventuale riferimento documento. Se avete telecamere collegate, il sistema puo anche scattare una foto del veicolo.

**Pesatura in uscita.** Quando il veicolo ha completato le operazioni e torna sulla bilancia, il sistema registra il secondo peso come "Weight2".

**Calcolo automatico del peso netto.** Il sistema calcola automaticamente la differenza tra i due pesi, ottenendo il peso netto del materiale caricato o scaricato. Nessun calcolo manuale, nessun errore.

**Gestione dello stato.** Ogni accesso segue un flusso chiaro: parte dallo stato "In attesa", passa a "Entrato" quando il veicolo e dentro l'impianto, e si chiude automaticamente con "Chiuso" al completamento della pesatura in uscita. Questo vi permette di avere sempre sotto controllo la situazione in tempo reale.

---

## 3. Interfaccia Web

Passiamo ora all'interfaccia che i vostri operatori utilizzeranno quotidianamente.

Abbiamo progettato una dashboard web accessibile da qualsiasi browser, senza bisogno di installare software aggiuntivo sulle postazioni di lavoro. La schermata principale mostra il peso in tempo reale dalla bilancia, aggiornato istantaneamente grazie alla tecnologia WebSocket.

Da qui l'operatore vede la lista degli accessi attivi e quelli completati, puo inserire o modificare i dati di pesatura, e navigare tra le varie sezioni del sistema in modo intuitivo. L'interfaccia e stata pensata per essere semplice e veloce, perche sappiamo che in un impianto il tempo e prezioso e gli operatori devono poter lavorare senza complicazioni.

---

## 4. Gestione Anagrafiche

Il sistema include una gestione completa delle anagrafiche, tutte modificabili direttamente dall'interfaccia.

Potete gestire l'archivio dei **veicoli** con targa e tara associata, l'elenco degli **autisti**, i **soggetti** ovvero i vostri clienti e fornitori, i **vettori** per le tipologie di trasporto, il catalogo dei **materiali** che trattate, e gli **operatori** che utilizzano il sistema.

Ogni anagrafica supporta le operazioni complete di creazione, modifica, ricerca e cancellazione. Una volta inseriti i dati, le pesature successive saranno molto piu rapide perche il sistema propone automaticamente le informazioni gia registrate.

---

## 5. Integrazione Hardware

Uno dei punti di forza di BARON IN-OUT e la sua capacita di integrarsi con diversi dispositivi hardware.

**Terminali di pesatura.** Il sistema supporta i principali terminali in commercio, come gli EGT-AF03 e i DGT1, e puo gestire piu bilance contemporaneamente. La comunicazione avviene via TCP o seriale, quindi compatibile con le configurazioni piu comuni.

**Lettore RFID.** Per velocizzare l'identificazione dei veicoli, potete collegare un lettore RFID seriale. I badge vengono associati ai veicoli in anagrafica e la lettura e istantanea.

**Pannelli display.** E possibile collegare display esterni, ad esempio sopra la bilancia, per mostrare messaggi all'autista come il peso corrente o istruzioni operative.

**Controllo relay.** Il sistema puo comandare relay per l'apertura automatica dei cancelli o l'attivazione di allarmi, anche in base a soglie di peso configurabili.

**Telecamere.** Supportiamo telecamere USB e IP per acquisire foto del veicolo durante la pesatura, utili per la documentazione e la tracciabilita.

**Stampante.** Tramite il sistema di stampa CUPS, potete stampare ticket e report direttamente dalla postazione di pesatura.

---

## 6. Reportistica e Esportazione Dati

La reportistica e un aspetto fondamentale per chi deve rendicontare e analizzare i dati.

BARON IN-OUT genera **report in formato PDF** con template completamente personalizzabili. Potete avere report generici, specifici per ingressi o uscite, e report di tara. Il layout e adattabile alle vostre esigenze tramite il **Report Designer** integrato.

Per chi lavora con fogli di calcolo o deve alimentare altri sistemi, e disponibile l'**esportazione in CSV** con totali di riepilogo calcolati automaticamente.

Inoltre, i dati sono disponibili anche in **tempo reale in formato JSON**, utile per eventuali integrazioni con altri software gestionali.

---

## 7. Sicurezza e Gestione Utenti

La sicurezza dei dati e la gestione degli accessi sono integrate nel sistema.

L'autenticazione utilizza **token JWT** con password crittografate tramite BCrypt, uno standard di sicurezza riconosciuto. Abbiamo previsto **cinque livelli di accesso**: sola lettura per chi deve solo consultare, scrittura per gli operatori, e poi livelli amministratore e super-amministratore per la gestione del sistema.

Un aspetto importante e il **sistema di lock dei record**: quando un operatore sta modificando una pesatura, il sistema impedisce ad altri di modificare lo stesso dato contemporaneamente, evitando conflitti e perdite di informazioni.

---

## 8. Funzionalita Avanzate

Oltre alle funzioni base, il sistema offre diverse funzionalita avanzate.

Il **tunneling SSH inverso** permette di accedere al sistema da remoto in modo sicuro, utile per assistenza tecnica e manutenzione senza dover essere fisicamente in loco.

La **sincronizzazione file** monitora automaticamente le cartelle di output e puo sincronizzare PDF, CSV e immagini verso destinazioni configurate.

Il sistema supporta il **multi-lingua** per adattarsi a contesti internazionali, e include una **modalita test** che permette di simulare le operazioni senza hardware collegato, ideale per formazione e verifiche.

Potete inoltre gestire **prenotazioni** per programmare gli accessi in anticipo, e configurare **tare preimpostate** per i veicoli abituali, velocizzando ulteriormente le operazioni quotidiane.

---

## 9. Configurazione e Personalizzazione

Il sistema e altamente configurabile per adattarsi alla vostra realta specifica.

Tutto passa da un **file di configurazione centralizzato** che permette di impostare i parametri per ogni bilancia collegata, i dettagli di connessione per tutti i dispositivi hardware, i template per i report e le funzionalita da attivare o disattivare.

Ad esempio, potete decidere se utilizzare o meno le anagrafiche, i badge RFID, le prenotazioni o le tare preimpostate. Ogni impianto ha le sue esigenze e il sistema si adatta di conseguenza.

---

## 10. Aspetti Tecnici

Per chi e interessato agli aspetti tecnici, il sistema si basa su un'architettura **modulare** che facilita la manutenzione e l'evoluzione nel tempo.

Il backend utilizza **FastAPI**, un framework Python ad alte prestazioni con supporto asincrono, e comunica con l'interfaccia tramite **WebSocket** per gli aggiornamenti in tempo reale.

Il database e **SQLite**, leggero e senza necessita di un server database separato: tutto gira su un singolo dispositivo, che puo essere un PC industriale o anche un mini-PC.

L'installazione e supportata su **Linux** (Debian e Ubuntu) e **Windows**, e la manutenzione puo avvenire interamente **da remoto** tramite connessione SSH.

---

## 11. Proposte e Sviluppi Futuri

Per concludere, vorremmo discutere con voi alcune possibilita di sviluppo futuro.

Possiamo valutare l'**integrazione con il vostro ERP o gestionale** esistente, in modo che i dati di pesatura confluiscano automaticamente nei vostri sistemi contabili e di magazzino.

Stiamo lavorando su una **dashboard avanzata con grafici e statistiche** per avere una visione d'insieme immediata sull'andamento dell'impianto.

E possibile sviluppare un'**app mobile dedicata** per consultare i dati anche in mobilita, implementare **notifiche automatiche via email o SMS** per eventi specifici come il superamento di soglie di peso, e predisporre un sistema di **backup automatico** per la massima sicurezza dei dati.

Se avete gia un sistema di **videosorveglianza**, possiamo valutare l'integrazione per collegare le registrazioni alle singole pesature.

---

## Chiusura

Questo e il quadro completo di cio che BARON IN-OUT puo offrire al vostro impianto. Come avete visto, si tratta di un sistema completo, flessibile e pensato per le esigenze reali di chi lavora con la pesatura industriale ogni giorno.

Siamo a disposizione per qualsiasi domanda e per approfondire gli aspetti che vi interessano di piu. Grazie per l'attenzione.
