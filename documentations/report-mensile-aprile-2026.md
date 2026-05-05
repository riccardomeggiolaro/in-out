# REPORT MENSILE — APRILE 2026

**Progetto:** IN-OUT (Sistema di Pesatura e Gestione Accessi)
**Repository:** riccardomeggiolaro/in-out

---

## RIEPILOGO GENERALE

| | |
|---|---|
| Periodo | 1 – 30 aprile 2026 |
| Giorni lavorativi | 20 (il 6 aprile è Pasquetta; il 27 aprile ferie) |
| Pull Request completate | ~163 |

---

## DETTAGLIO PER GIORNO

---

### SETTIMANA 1 — 1–3 aprile

**Mercoledì 1 aprile** *(continuazione sprint totem)*
- Totem: reset completo dei dati selezionati tornando indietro dalla pagina targa
- Totem: skip anagrafiche disabilitate quando si naviga indietro
- Rimossa pagina selezione direzione; ripristino rilevamento automatico Entrata/Uscita
- Aggiunto pulsante Annulla sulla pagina targa per azzerare la selezione
- Campi non-prenotazione rimangono editabili sulla pesata di uscita
- Navigazione indietro dal riepilogo all'ultima anagrafica abilitata
- Fix: mostra tutti gli step abilitati in uscita, non solo quelli vuoti
- Fix controllo modalità prenotazione: applicato solo per le prenotazioni vere
- Gestione flag `from=summary` per navigazione bidirezionale
- Passaggio sempre allo step successivo abilitato (non solo quelli vuoti)
- **Internazionalizzazione (i18n)**: supporto completo Italiano/Inglese nel totem
- Pulsanti lingua con icone bandiera, dimensionati dinamicamente sull'altezza topbar
- Fix etichette pulsante pesata: Entrata/Uscita in IT, Weight 1/Weight 2 in EN
- Skip step prenotazione quando si naviga indietro dal riepilogo
- Applicazione palette colori ad alto contrasto per uso outdoor
- Passaggio a tema scuro per visibilità esterna
- Bordi 3D sugli item griglia; righe disabilitate riepilogo mantenute visibili
- Icone matita modifica riepilogo più grandi e bianche
- Bordi luminosi su item, sfondo giallo su item selezionato
- Pulsante pesata aggiornato in real-time in base al valore tara
- Aggiunto arrotondamento angoli all'immagine logo

**Giovedì 2 aprile**
- Aggiunto controllo accesso ai campi anagrafiche con default `typeSubject`
- Rimosso "operatore" dalle anagrafiche configurabili; applicato `typeSubject` di default in tutta l'applicazione (tutte le dashboard, totem, access, reservation, favourite, backend)

**Venerdì 3 aprile**
- Aggiunta UI hint RFID nella schermata input targa del totem
- Traduzione `rfid_read_card`; hint RFID nascosto se targa già presente
- Spaziatura dinamica tra item anagrafiche nel totem
- **Modulo RFID multi-istanza**: configurabile con selezione protocollo
- RFID associato per singola pesa, configurabile dall'interfaccia terminale
- RFID spostato dentro ciascuna pesa nella pagina configuration
- Salvataggio config RFID spostato dal modulo al router `config-weigher`
- Stop automatico RFID all'eliminazione della pesa
- Fix stile configurazione RFID: popup modifica separato, pulsanti corretti
- Impostazione callback `Callback_WeighingByIdentify` per lettura cardcode da RFID

---

### SETTIMANA 2 — 6–10 aprile

**Lunedì 6 aprile** — *Pasquetta (festività nazionale)*

**Martedì 7 aprile** *(nessuna attività registrata)*

**Mercoledì 8 aprile**
- Sostituzione conferma targa con handler semi-automatico generico
- Skip messaggi WebSocket `command_in_executing` sulla pagina totem
- Fix modalità semi-automatica totem: nessun popup, nessuna pesata auto
- Fix totem che navigava alla pagina targa prima di mostrare il successo pesata
- Sfondo item anagrafica selezionati: da verde a bianco
- Rimossi elementi lettore tessera/RFID dalla pagina targa totem
- **Aggiunta pagina tessera (card)** prima della pagina targa nel totem
- Pagina tessera resa opzionale; label configurabile dall'UI; pulizia card view
- Fix crash `showView` quando la view non ha un `h2` (pagina card)
- Redirect alla pagina card quando si naviga indietro dal riepilogo con card abilitata
- Iterazioni tema chiaro/scuro per item anagrafiche
- Sfondo giallo per item selezionati; topbar e pulsanti grigi
- Fix sovrapposizione topbar con h2; altezza uniforme topbar e step-buttons
- Pulsanti bianchi con testo scuro; fix padding step-buttons
- Logo spostato al centro dei step-buttons tra Indietro e Avanti
- Logo mostrato nella pagina card (centrato nei step-buttons senza altri pulsanti)
- H2 titolo spostato dentro il topbar; aumento dimensione logo

**Giovedì 9 aprile**
- **Redesign completo UI totem**: gerarchia visiva migliorata e layout ottimizzato
- Redesign card view: display peso e stato in tempo reale
- Item riepilogo più grandi; layout suddiviso al punto medio verticale
- Display peso real-time aggiunto alla vista riepilogo
- Peso inserito come riga dentro la lista riepilogo; sizing font unità/stato
- Pulsante pesata: sempre icona stampante SVG + "Conferma"/"Confirm"
- Fix restringimento targa all'apertura tastiera: toggle `step-content`
- Bordo targa allineato al colore item anagrafiche (#CCCCCC)
- Fix data flash: blocco `onDataUpdate` durante la pesata
- **Modalità AUTOMATIC**: skip di tutti gli step anagrafiche, accesso diretto a card/targa/riepilogo
- Fix rilevamento modalità AUTOMATIC: lettura `weigherMode` da config invece da access
- Modalità AUTOMATIC: rimane sulla card view senza navigare
- Blocco display peso durante il completamento pesata (evita flash)
- SEMIAUTOMATIC/MANUALLY passano per tutti gli step abilitati; solo AUTOMATIC li salta

**Venerdì 10 aprile**
- Fix redirect al refresh del riepilogo; aggiunta notifiche toast per `cam_message`
- `cam_message` mostrato come popup errore; fix overlay: rimane sulla pagina corrente al dismiss
- Aggiunto flag `cam_is_error` ai broadcast `cam_message`; popup mostrato solo su errori
- **Sistema Card Registry**: gestione anagrafica badge con interfaccia dedicata
- Sostituzione `Access.badge` con FK `idCardRegistry` verso tabella `card_registry`
- Suggerimenti card registry, auto-selezione al blur su corrispondenza esatta
- Fix visibilità suggerimenti e idempotenza `update_access`
- Fix `itemName` card_registry per allineamento al manager anagrafiche
- Aggiunta relazione back `accesses` al modello `CardRegistry`
- Accesso in scrittura alla card registry limitato a **super_admin (livello 4)**

---

### SETTIMANA 3 — 13–17 aprile

**Lunedì 13 aprile**
- Fix layout vista riepilogo: contenuto correttamente centrato e a piena altezza
- Fix toast di errore sulla conferma targa e navigazione post-conferma
- Fix skip step anagrafica: non saltare step già compilati durante la navigazione
- Fix toast spurio sull'inserimento targa (race condition DOM)
- Modalità AUTOMATIC: naviga attraverso gli step non compilati dopo inserimento targa manuale
- Modalità AUTOMATIC: rimane sulla pagina targa quando l'access è auto-selezionato
- Guard `updateSummary` contro DOM null quando non si è sulla pagina riepilogo
- Semplificazione etichette UI lettore tessera RFID
- Forma infinitiva per istruzione tessera in italiano ("Avvicinare la tessera")

**Martedì 14 aprile**
- Refactoring pagina transiti: rimossi prenotazioni permanenti e gestione materiale (in revisione)

**Mercoledì 15 aprile**
- Rimossi API call non necessari al cancel/reset dei dati totem
- Modalità AUTOMATIC: skip notifica "pesata eseguita" quando PID è "NO"
- Applicazione controllo PID a tutte le modalità (non solo AUTOMATIC)
- Modalità MANUALLY e SEMIAUTOMATIC: popup errore quando PID è "NO"

**Giovedì 16 aprile**
- Modalità SEMIAUTOMATIC: skip campi selezione, navigazione diretta al riepilogo
- Modalità AUTOMATIC: navigazione al riepilogo dopo lettura card/targa
- Modalità AUTOMATIC: pulsante pesata disabilitato nel riepilogo
- Modalità AUTOMATIC: tutti i campi riepilogo disabilitati (icone matita nascoste)
- Fix triple-tap toggle fullscreen su dispositivi touch (listener su `touchend`)
- **Toggle abilitazione totem**: checkbox in config + endpoint backend `SetTotemEnabled`
- Totem disabilitato a livello server: redirect a `/not-found` su tutte le route totem
- Prevenzione context menu browser al long-press nella pagina totem
- Script da terminale per elencare accessi nascosti (`list_hidden_accesses.py`)
- Script da terminale per eliminare accessi con `hidden=True` con opzioni `--status`, `--force`

**Venerdì 17 aprile**
- Nasconde campo targa veicolo (frontend e backend) quando esistono pesate per la prenotazione
- Copia `idCardRegistry` sui record `in_out` al momento della pesata
- Migrazione dati: backfill `in_out.idCardRegistry` da `access` per tutti i record storici
- Totem: mostra targa per 3 secondi prima della navigazione automatica; font riepilogo più grandi
- Fix ritardo visualizzazione targa nel totem multi-pagina (`totem-plate.html`)
- Fix ritardo targa in modalità semi-automatica/automatica
- Nasconde pulsanti durante la finestra di visualizzazione targa
- **Gestione fullscreen robusta**: intercettazione F11 con JS Fullscreen API
- Auto rientro in fullscreen se uscita accidentale (es. pulsante X browser)
- Blocco `touchmove` in fullscreen per prevenire la toolbar di uscita Chrome

---

### SETTIMANA 4 — 20–24 aprile

**Lunedì 20 aprile**
- Fix script di build per cifratura PyArmor: fix typo `STATIC_DIR`, aggiunta `clean_dist()`, esclusioni directory (`.venv`, `dist`, `__pycache__`, ecc.), fix `DIST_DIR`

**Martedì 21 aprile**
- Aggiunto script utility `delete_table_data.py` per svuotare una o più tabelle del database; supporta `--tables`, `--all`, `--force`, `--list`

**Mercoledì 22 aprile** — *Trasferta: montaggio e messa in opera del totem presso il cliente*

**Giovedì 23 aprile** — *Trasferta mezza giornata: sopralluogo presso Alluminio di Qualità per risoluzione problemi di rete*

**Venerdì 24 aprile** *(nessuna attività di sviluppo registrata)*

**Lunedì 27 aprile** — *Ferie*

**Martedì 28 – Giovedì 30 aprile** *(nessuna attività di sviluppo registrata)*

---

## SINTESI TEMATICA

| Area | Attività principali |
|---|---|
| **Totem — Navigazione** | Gestione completa back/forward, skip step, reset dati, flag from=summary |
| **Totem — Modalità operative** | Comportamento differenziato AUTOMATIC / SEMIAUTOMATIC / MANUALLY |
| **Totem — UI/UX** | Tema scuro outdoor, i18n IT/EN, pagina tessera, logo, layout peso in riepilogo |
| **Totem — Fullscreen** | F11 intercept, auto re-enter, prevenzione toolbar Chrome su touch |
| **RFID** | Modulo multi-istanza per pesa, callback `WeighingByIdentify`, config da UI |
| **Card Registry** | Nuovo sistema gestione badge con FK su accessi, scrittura riservata a super_admin |
| **Modalità AUTOMATIC** | Navigazione diretta a riepilogo, disable pulsanti/campi, gestione PID |
| **Cam message** | Flag `cam_is_error`, popup errore differenziato da messaggi informativi |
| **Database / Manutenzione** | Script terminale per lista/delete accessi nascosti, script svuotamento tabelle |
| **Build / Deploy** | Fix script PyArmor per produzione |

---

*Report generato dal repository `riccardomeggiolaro/in-out` — branch `main`*
