# REPORT MENSILE — MARZO 2026

**Progetto:** IN-OUT (Sistema di Pesatura e Gestione Accessi)
**Repository:** riccardomeggiolaro/in-out

---

## RIEPILOGO GENERALE

| | |
|---|---|
| Periodo | 1 – 31 marzo 2026 |
| Giorni lavorativi | 21 |
| Pull Request completate | ~395 |
| Riunioni | 24/03 e 26/03 (1 ora ciascuna) |

---

## DETTAGLIO PER GIORNO

---

### SETTIMANA 1 — 2–6 marzo

**Lunedì 2 marzo**
- Aggiunta null-safety nelle query DOM delle tabelle dinamiche
- Correzione fallback animazione riga quando `li:first-child p` non esiste

**Martedì 3 marzo**
- Miglioramento logica animazione delete su pagina accessi (uso dati WebSocket anziché DOM)
- Aggiunta logica fade-out riga per accessi con una sola pesata
- Allineamento animazione delete anche per cancellazioni pesate da prenotazione
- Aggiunta toggle mostra/nascondi totali nelle esportazioni lista
- Aggiunta stampa report separata per pesate alla tara
- Aggiunta config report/CSV alla tara nella pagina di setup (con link al designer)

**Mercoledì 4 marzo**
- Editor template report tara nelle pagine di configurazione
- Impostazioni report/CSV/stampante/copie per singolo tipo evento (entrata/uscita)
- Vista dettaglio pesata aggiornata con impostazioni per-evento a griglia
- Limitazione modifica accessi prenotati ai soli campi materiale
- Logica pulsante elimina: visibile solo se `is_latest_for_vehicle=true` e `is_last=true`
- Fix pulsante elimina per accessi non-prenotazione
- Fix dropdown suggerimenti tagliato dall'overflow del popup
- Nasconde pulsante elimina per anagrafiche con accessi associati
- Rimozione sezione recorder dalla pagina config; disabilitato `use_recordings`
- Rimozione pulsanti esportazione dalla pagina prenotazioni
- Spostamento checkbox modalità test sotto la selezione modalità operativa
- Aggiunta colonna badge nella lista pesate

**Giovedì 5 marzo**
- Supporto accessi multipli per badge; aggiunta proprietà `is_latest_for_badge`
- Blocco modifica badge su accessi chiusi (lato backend e frontend)
- Oscuramento campo badge nel popup modifica per prenotazioni chiuse
- Creazione documentazione di presentazione cliente del sistema BARON IN-OUT (versione completa e sintetica, con PDF)

**Venerdì 6 marzo**
- Miglioramento autocomplete: supporto filtro su lista parziale
- Aggiunta campo materiale all'entità Access
- Campo materiale nei popup aggiunta/modifica prenotazioni e colonna in tabella
- Riordino colonne: materiale prima di note, autista dopo note
- Popolamento materiale dashboard da `in_out` o fallback a materiale globale access
- Fix `RecursionError` in `filter_data`: rimosso `selectinload('*')` ricorsivo

---

### SETTIMANA 2 — 9–13 marzo

**Lunedì 9 marzo**
- Aggiunta opzione configurazione registrazioni per misurazioni peso
- Nuova pagina profilo utente con funzionalità cambio password
- Separazione modifica dati utente e cambio password in due popup distinti
- Pulsanti azione tabella utenti (modifica/password/elimina) visibili solo all'hover
- Fix selettori materiale nei dialog aggiornamento pesate
- Pulizia automatica a mezzanotte degli accessi in attesa non prenotati

**Martedì 10 marzo**
- Checkbox abilitazione pulizia mezzanotte in `configuration.html`
- Aggiornamento versione applicazione a **3.0.3**
- Correzione selezione materiale: reset quando si modifica manualmente la descrizione
- Fix estrazione materiale: controllo `netWeight` prima di accedere al campo
- Utilizzo ultimo `in_out` invece del primo per la descrizione del materiale

**Mercoledì 11 marzo**
- Sviluppo **Dashboard V2** con UI mobile migliorata e funzionalità real-time
- Dashboard V2: lista ultime 10 letture OCR targa (in sostituzione lista accessi)
- Dashboard V2: popup dettaglio lettura OCR con ora e esito
- Dashboard V2: tabella accessi sotto il display peso con supporto selezione
- Dashboard V2: layout peso/pulsanti full-width e riorganizzazione area bottoni

**Giovedì 12 marzo**
- Dashboard V2: molteplici iterazioni di raffinamento layout (barra peso, padding, margini)
- Dashboard V2: gruppo input con etichetta sopra il campo, larghezza adattiva
- Dashboard V2: troncamento testo JS con ricalcolo al resize
- Dashboard V2: vista mobile con tab per lista accessi, breakpoint 800px
- Dashboard V2: sostituzione pulsante diagnostica con pulsanti relay nella barra bilancia
- Dashboard V2: tooltip info sostituito con popup (dettagli terminale + diagnostica)

**Venerdì 13 marzo**
- Sviluppo **Totem Weighing Wizard**: interfaccia guidata con display peso real-time
- Aggiunta schermata selezione bilancia prima del wizard totem
- Integrazione script interceptor e auth nella pagina totem
- Redesign step targa: UI grafica targa realistica
- Nascondi suggerimenti alla selezione item e al blur dell'input
- Auto-selezione del suggerimento corrispondente al blur; chiamata API per `set data_in_execution`

---

### SETTIMANA 3 — 16–20 marzo

**Lunedì 16 marzo**
- Totem: fix suggerimenti dal passo precedente visibili tornando indietro
- Totem: step 2–5 come griglia selezione, solo targa come input manuale
- Totem: avanzamento automatico al passo successivo alla selezione
- Totem: refactoring del wizard in **pagine HTML separate** (rimozione progress bar)
- Aggiunta documentazione sistema di controllo sbarre con priorità veicoli

**Martedì 17 marzo**
- Aggiornamenti iterativi al documento di processo: slot 1/2, fasi semplificate, automatismo sbarre Pesa 1/Pesa 2
- Aggiunte sezioni: CSV/report PDF, QR code fallback, gestione transiti senza pesatura (Fase 5)
- Struttura e numerazione corretta del documento Word

**Mercoledì 18 marzo** *(nessuna attività registrata)*

**Giovedì 19 marzo**
- Aggiunta pulsanti "Avanti" condizionali nelle pagine totem
- Redesign pagina targa totem: targa vuota visibile, avanzamento automatico alla lettura
- Input targa manuale integrato graficamente dentro la targa
- Sostituzione pagina selezione tipo con pagine separate cliente/fornitore

**Venerdì 20 marzo**
- Rimozione filtro `excludeTestWeighing` dalla lista accessi
- Aggiornamento versione applicazione a **3.0.4**

---

### SETTIMANA 4 — 23–27 marzo

**Lunedì 23 marzo**
- Aggiunta modalità prenotazione nel riepilogo totem con gestione stato UI
- Fix ricerca prenotazione con inserimento manuale targa
- Ridimensionamento layout totem per monitor 12 pollici (~1024×768)
- Dimensioni touch-friendly (titoli, item, bottoni, riepilogo)
- Modalità inserimento manuale targa: attivazione con click sulla targa
- Paginazione con frecce per scorrere le anagrafiche; bottoni fissi in basso
- Layout a 3 zone fisse: peso, lista paginata, bottoni

**Martedì 24 marzo** *(+ 1 ora di riunione)*
- Refactoring paginazione e rimozione descrizioni UI statiche
- Fix calcolo paginazione al caricamento iniziale
- Auto-navigazione alla pagina contenente l'item selezionato
- Rimozione pulsanti Avanti/Indietro dalla lista; auto-skip pagine vuote
- Navigazione al riepilogo dopo la modifica di un singolo campo
- Merge tipo soggetto e soggetto in unica pagina con titolo dinamico
- **Refactoring totem in SPA** con connessione WebSocket persistente
- Schermata di successo pesata a pagina intera; poi ritorno alla targa
- Layout riepilogo 50/50 con divisore verticale; pulsante Annulla reset dati
- Peso real-time sostituito da logo; layout bottoni responsivo con `clamp()`

**Mercoledì 25 marzo**
- Stile titolo step: centrato, uppercase, font variabile
- Miglioramenti grafici targa: proporzioni, font dinamico, bande blu proporzionali
- Tastiera virtuale su touch per input targa
- Auto-skip pagine vuote in avanti e indietro
- Gestione errori pesata: schermata fullscreen, tap per tornare al riepilogo
- Font riepilogo adattivi alla viewport; font item e bottoni in `vh`
- Logo Baronpesi in alto; placeholder vuoti in griglia per mantenere layout

**Giovedì 26 marzo** *(+ 1 ora di riunione)*
- Pulsante pesata mostra "Entrata"/"Uscita" in base allo stato corrente
- Auto-navigazione alla pagina corretta al refresh (in base ai dati esistenti)
- Aggiunta parametro `auto_select` all'endpoint PATCH `/api/data` per matching automatico totem
- `auto_select`: selezione access esistente invece di restituire errore
- Modifica materiale abilitata sulle prenotazioni in dashboard
- Aggiornamento materiale su `in_out` in DB quando peso1 esiste su prenotazione
- Gestione priorità materiale: `data_in_execution` > `in_out` > `access`
- Fix `NoneType` quando la relazione materiale è nulla

**Venerdì 27 marzo**
- Fix re-abilitazione input al refresh con prenotazione selezionata
- Aggiornamento materiale dal DB dopo `update_access` per evitare dati stantii
- Deseleziona access corrente prima di impostare nuova targa dal totem
- Totem torna alla targa quando l'access viene deselezionato; va al riepilogo quando selezionato esternamente
- Modifica materiale su prenotazioni: solo se campo vuoto, in memoria fino alla pesata
- Broadcast aggiornamento access alla dashboard dopo modifica da totem
- Aggiunta sezione **TOTEM settings**: anagrafiche configurabili (soggetto, vettore, autista, materiale)
- Totem rispetta la configurazione `totem_anagrafiche` per le pagine visibili

---

### SETTIMANA 5 — 30–31 marzo

**Lunedì 30 marzo**
- Estensione livello `in_out`: aggiunta colonne per tutti i campi (soggetto, vettore, autista, ecc.)
- Migrazione esplicita colonne `in_out` con backfill dai dati `access`
- Dashboard: ogni campo editabile in base ai flag `reservation_has_*`
- Fix salvataggio cambiamenti campi prenotazione in memoria e `in_out`
- Salvataggio tutti i campi `data_in_execution` su `in_out` al momento della pesata
- Fix: prima pesata `in_out` salva correttamente tutti i campi

**Martedì 31 marzo**
- Refactoring aggiornamento entità InOut con supporto creazione dinamica soggetto/vettore/autista
- Aggiunta tracciamento stato campi note e riferimento documento
- Fix visualizzazione soggetto/vettore nella lista accessi dopo assegnazione su prenotazione
- Applicazione regola lock su targa: disabilitata solo se dato preesistente
- Fallback a dati access quando campo `in_out` è vuoto, con lock automatico
- Applicazione flag-based field locking anche a `_dashboard.js` e `_dashboard-v2.js`
- Visualizzazione soggetto/materiale in lista accessi con priorità `in_out` su prenotazione
- Aggiunta ordinamento dinamico agli endpoint anagrafiche; ordinamento alfabetico nei suggerimenti popup
- Totem: **aggiunta step selezione direzione (Entrata/Uscita)** come primo step, prima della targa
- Redirect alla pagina direzione in caso di mismatch direzione/targa
- Totem riepilogo: restyling come tabella singola con bordo, righe proporzionali, colonne 50/50

---

## SINTESI TEMATICA

| Area | Attività principali |
|---|---|
| **Dashboard V2** | Nuova interfaccia operatore mobile-first con OCR, relay, diagnostica |
| **Totem SPA** | Sviluppo completo da zero del wizard totem (multipage → SPA WebSocket) |
| **Prenotazioni / In-Out** | Gestione dati per-pesata, priorità campi, lock/unlock automatico |
| **Materiali** | Tracciamento materiale a livello `in_out`, modifica da totem e dashboard |
| **Badge / RFID** | Accessi multipli per badge, blocco modifica su accessi chiusi |
| **Report / Export** | Report tara separato, impostazioni per-evento, toggle totali |
| **Configurazione** | Pulizia mezzanotte, anagrafiche totem configurabili, totem_enabled |
| **Documentazione** | Presentazione cliente BARON IN-OUT, documento processo sbarre/priorità |
| **Versioni rilasciate** | 3.0.3 (10/03), 3.0.4 (20/03) |
| **Riunioni** | 24/03 ore 1h — 26/03 ore 1h |
