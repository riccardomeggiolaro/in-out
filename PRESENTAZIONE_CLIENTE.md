# BARON IN-OUT - Checklist Presentazione Cliente

## 1. Introduzione al Sistema
- [ ] Panoramica generale: sistema di pesatura industriale per la gestione ingresso/uscita veicoli
- [ ] Casi d'uso: centri logistici, impianti di gestione rifiuti, stabilimenti industriali
- [ ] Architettura del sistema (backend FastAPI, frontend web, integrazione hardware)

---

## 2. Flusso Operativo Principale
- [ ] **Identificazione veicolo**: scansione badge RFID, inserimento manuale targa, selezione da lista
- [ ] **Pesatura in ingresso** (Weight1): registrazione peso alla bilancia
- [ ] **Gestione dati**: autista, soggetto, materiale, documenti associati
- [ ] **Pesatura in uscita** (Weight2): registrazione peso alla bilancia
- [ ] **Calcolo peso netto**: differenza automatica tra peso lordo e tara
- [ ] **Stato accesso**: dimostrazione del flusso WAITING -> ENTERED -> CLOSED

---

## 3. Interfaccia Web
- [ ] Dashboard principale con monitoraggio peso in tempo reale
- [ ] Lista accessi attivi e completati
- [ ] Inserimento e modifica dati pesatura
- [ ] Navigazione intuitiva tra le sezioni
- [ ] Aggiornamenti in tempo reale via WebSocket

---

## 4. Gestione Anagrafiche (CRUD completo)
- [ ] **Veicoli**: targa, tara, dati associati
- [ ] **Autisti**: anagrafica conducenti
- [ ] **Soggetti**: clienti e fornitori
- [ ] **Vettori**: tipologie di trasporto
- [ ] **Materiali**: catalogo materiali gestiti
- [ ] **Operatori**: utenti del sistema

---

## 5. Integrazione Hardware
- [ ] **Terminali di pesatura**: supporto multi-bilancia (EGT-AF03, DGT1)
- [ ] **Lettore RFID**: identificazione badge via seriale
- [ ] **Pannelli display**: messaggistica su display esterni (TCP/HTTP)
- [ ] **Controllo relay**: apertura cancelli e allarmi basati su soglie di peso
- [ ] **Telecamere**: acquisizione foto (USB/IP) collegate alla pesatura
- [ ] **Stampante**: stampa ticket e report via CUPS

---

## 6. Reportistica e Esportazione Dati
- [ ] **Report PDF**: generici, ingresso, uscita, tara con template personalizzabili
- [ ] **Esportazione CSV**: export massivo con totali riepilogo
- [ ] **Report Designer**: personalizzazione del formato di output
- [ ] **Dati in tempo reale**: streaming dati JSON

---

## 7. Sicurezza e Gestione Utenti
- [ ] **Autenticazione JWT** con password crittografate (BCrypt)
- [ ] **5 livelli di accesso**: sola lettura, scrittura, admin, super-admin
- [ ] **Sistema di lock record**: prevenzione modifiche concorrenti
- [ ] Gestione permessi granulare per ruolo

---

## 8. Funzionalita Avanzate
- [ ] **Tunneling SSH inverso**: accesso remoto al sistema
- [ ] **Sincronizzazione file**: monitoraggio cartelle per PDF/CSV/immagini
- [ ] **Supporto multi-lingua**: localizzazione messaggi
- [ ] **Modalita test**: per sviluppo e validazione
- [ ] **Prenotazioni**: gestione accessi programmati
- [ ] **Tara preimpostata**: configurazione tare predefinite per veicoli

---

## 9. Configurazione e Personalizzazione
- [ ] File di configurazione centralizzato (config.json)
- [ ] Configurazione individuale per ogni bilancia
- [ ] Parametri di connessione hardware personalizzabili
- [ ] Template report configurabili
- [ ] Toggle funzionalita (anagrafiche, badge, preset, prenotazioni, registrazioni)

---

## 10. Aspetti Tecnici da Evidenziare
- [ ] Architettura modulare e manutenibile
- [ ] Comunicazione asincrona (FastAPI + WebSocket)
- [ ] Database SQLite (leggero, senza server aggiuntivo)
- [ ] Installazione su Linux (Debian/Ubuntu) e Windows
- [ ] Aggiornamenti e manutenzione remota via SSH

---

## 11. Proposte e Sviluppi Futuri (da discutere col cliente)
- [ ] Eventuali integrazioni con ERP o gestionali esistenti
- [ ] Dashboard avanzata con grafici e statistiche
- [ ] App mobile dedicata
- [ ] Notifiche automatiche (email/SMS) per eventi specifici
- [ ] Backup automatico e disaster recovery
- [ ] Integrazione con sistemi di videosorveglianza esistenti

---

## Note per la Presentazione
- Preparare un ambiente demo con dati di esempio
- Avere pronto il collegamento a una bilancia (o simulatore in modalita test)
- Mostrare il flusso completo: ingresso veicolo -> pesatura -> uscita -> report
- Evidenziare la semplicita d'uso dell'interfaccia
- Sottolineare la flessibilita di configurazione e personalizzazione
