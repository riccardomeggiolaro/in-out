# Architettura Software BARON IN-OUT - Sistema di Pesatura

## 1. Schema Generale dell'Architettura

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    BARON IN-OUT                                      │
│                              Sistema di Pesatura Industriale                         │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                  FRONTEND (UI)                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐              │
│  │   Web Browser    │    │  Desktop GUI     │    │   Mobile App     │              │
│  │   (Jinja2/HTML)  │    │   (Tkinter)      │    │   (REST Client)  │              │
│  └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘              │
│           │                       │                       │                         │
│           └───────────────────────┼───────────────────────┘                         │
│                                   │                                                  │
│                          HTTP/REST + WebSocket                                       │
└───────────────────────────────────┼──────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                               BACKEND (FastAPI)                                      │
│                                   Porta: 80                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────────────┐     │
│  │                            MIDDLEWARE LAYER                                 │     │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │     │
│  │  │    CORS     │  │    Auth     │  │   Admin     │  │  Writable   │       │     │
│  │  │ Middleware  │  │ Middleware  │  │   Check     │  │    User     │       │     │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │     │
│  └────────────────────────────────────────────────────────────────────────────┘     │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────┐     │
│  │                              API ROUTERS                                    │     │
│  │                                                                             │     │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │     │
│  │  │   /auth     │  │ /anagrafic  │  │  /weigher   │  │  /printer   │       │     │
│  │  │  Login/JWT  │  │ CRUD Data   │  │  Comandi    │  │   Stampa    │       │     │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │     │
│  │                                                                             │     │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │     │
│  │  │  /generic   │  │   /in-out   │  │ /sync-folder│  │  /tunnel    │       │     │
│  │  │  Report/PDF │  │  API Pubbl. │  │  Sincroniz. │  │  SSH Remoto │       │     │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │     │
│  └────────────────────────────────────────────────────────────────────────────┘     │
└───────────────────────────────────┬──────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              MODULES (Logica Core)                                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │ md_weigher  │  │ md_database │  │  md_rfid    │  │ md_desktop  │                │
│  │   Bilance   │  │     ORM     │  │   Lettore   │  │  Interface  │                │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────────────┘                │
│         │                │                │                                          │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐  ┌─────────────┐                │
│  │ md_sync_    │  │  md_tunnel  │  │   Panel/    │  │   Siren     │                │
│  │   folder    │  │ connections │  │  Display    │  │  Control    │                │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘                │
└───────────────────────────────────┬──────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           LIBRARIES (Funzioni Condivise)                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │  lb_config  │  │   lb_log    │  │  lb_system  │  │ lb_printer  │                │
│  │   Config    │  │   Logging   │  │ Serial/TCP  │  │    CUPS     │                │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘                │
│                                                                                      │
│  ┌─────────────┐  ┌─────────────┐                                                   │
│  │  lb_camera  │  │  lb_utils   │                                                   │
│  │  Fotocamera │  │  Utilities  │                                                   │
│  └─────────────┘  └─────────────┘                                                   │
└───────────────────────────────────┬──────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼──────────────────────────────────────────────────┐
│                                   ▼                                                  │
│                        LAYER DI PERSISTENZA                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐                     ┌─────────────────────┐                │
│  │      SQLite DB      │                     │    File System      │                │
│  │  /var/opt/in-out/   │                     │  /var/opt/in-out/   │                │
│  │    database.db      │                     │  ├── pdf/           │                │
│  └─────────────────────┘                     │  ├── csv/           │                │
│                                              │  ├── images/        │                │
│                                              │  └── config.json    │                │
│                                              └─────────────────────┘                │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            HARDWARE ESTERNO                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │   Bilance   │  │   Lettore   │  │   Display   │  │   Sirena    │                │
│  │  EGT/DGT1   │  │    RFID     │  │   Pannello  │  │   Allarme   │                │
│  │  TCP/Serial │  │   Serial    │  │  TCP/HTTP   │  │  TCP/HTTP   │                │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘                │
│                                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                                  │
│  │  Stampante  │  │  Fotocamera │  │    Relay    │                                  │
│  │    CUPS     │  │   USB/IP    │  │  Controllo  │                                  │
│  └─────────────┘  └─────────────┘  └─────────────┘                                  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Struttura del Database

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              DATABASE SCHEMA (SQLite)                                │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│      User       │     │    Subject      │     │     Vector      │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │     │ id (PK)         │     │ id (PK)         │
│ username        │     │ social_reason   │     │ social_reason   │
│ password (hash) │     │ telephone       │     │ telephone       │
│ level           │     │ cfpiva          │     │ cfpiva          │
│ description     │     │ date_created    │     │ date_created    │
│ date_created    │     └─────────────────┘     └─────────────────┘
└─────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Driver      │     │    Vehicle      │     │    Material     │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │     │ id (PK)         │     │ id (PK)         │
│ social_reason   │     │ plate (Unique)  │     │ description     │
│ telephone       │     │ description     │     │ date_created    │
│ date_created    │     │ tare            │     └─────────────────┘
└─────────────────┘     │ date_created    │
                        └─────────────────┘     ┌─────────────────┐
                                                │    Operator     │
                                                ├─────────────────┤
                                                │ id (PK)         │
                                                │ description     │
                                                │ date_created    │
                                                └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          TABELLE PRINCIPALI DI PESATURA                              │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    ACCESS                                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ id (PK) │ typeSubject │ number_in_out │ status      │ type        │ badge         │
│         │ (CLIENTE/   │               │ (WAITING/   │ (RESERV./   │               │
│         │  FORNITORE) │               │  ENTERED/   │  MANUALLY/  │               │
│         │             │               │  CLOSED)    │  TEST)      │               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ selected │ hidden │ document_reference │ note │ date_created                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ FK: idSubject → Subject │ FK: idVector → Vector │ FK: idDriver → Driver             │
│ FK: idVehicle → Vehicle │                                                           │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                     INOUT                                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ id (PK) │ net_weight │ FK: idAccess → Access │ FK: idMaterial → Material            │
│         │            │ FK: idWeight1 → Weighing │ FK: idWeight2 → Weighing          │
└─────────────────────────────────────────────────────────────────────────────────────┘
                          │                 │
                          ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                   WEIGHING                                           │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ id (PK) │ date │ weigher │ weigher_serial_number │ pid │ tare │ weight │ log       │
│         │      │         │                       │     │      │        │           │
│ is_preset_tare │ is_preset_weight │ FK: idUser → User │ FK: idOperator → Operator  │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              WEIGHING_PICTURE                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ id (PK) │ path_name │ FK: idWeighing → Weighing                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                               LOCK_RECORD                                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ id (PK) │ table_name │ idRecord │ type │ websocket_identifier │ user_id │ weigher  │
│         │            │          │ (SELECT/UPDATE/DELETE/CALL/CANCEL_CALL)           │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Flusso di Autenticazione

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           FLUSSO DI AUTENTICAZIONE JWT                               │
└─────────────────────────────────────────────────────────────────────────────────────┘

    ┌──────────┐                    ┌──────────┐                    ┌──────────┐
    │  Client  │                    │  FastAPI │                    │ Database │
    │  (Web/   │                    │  Backend │                    │  SQLite  │
    │  Mobile) │                    │          │                    │          │
    └────┬─────┘                    └────┬─────┘                    └────┬─────┘
         │                               │                               │
         │  1. POST /api/auth/login      │                               │
         │   {username, password}        │                               │
         │ ─────────────────────────────>│                               │
         │                               │                               │
         │                               │  2. Query User                │
         │                               │ ─────────────────────────────>│
         │                               │                               │
         │                               │  3. Return User Data          │
         │                               │<─────────────────────────────│
         │                               │                               │
         │                               │  4. Verifica Password         │
         │                               │     (bcrypt.verify)           │
         │                               │                               │
         │                               │  5. Genera JWT Token          │
         │                               │     {user_id, username,       │
         │                               │      level, exp}              │
         │                               │                               │
         │  6. Return JWT Token          │                               │
         │<─────────────────────────────│                               │
         │                               │                               │
         │  7. Richiesta con Token       │                               │
         │   Authorization: Bearer xxx   │                               │
         │ ─────────────────────────────>│                               │
         │                               │                               │
         │                               │  8. AuthMiddleware            │
         │                               │     Valida Token              │
         │                               │                               │
         │                               │  9. Role Check                │
         │                               │     @is_admin                 │
         │                               │     @is_writable_user         │
         │                               │                               │
         │  10. Response                 │                               │
         │<─────────────────────────────│                               │
         │                               │                               │

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              LIVELLI DI AUTORIZZAZIONE                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   Level 0-1:  Read Only User     → Solo lettura dati                                │
│   Level 2:    Writable User      → Lettura + Scrittura                              │
│   Level 3:    Admin              → Gestione utenti + Configurazione                  │
│   Level 4+:   Super Admin        → Tutte le operazioni + Eliminazione utenti        │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Workflow Principale di Pesatura

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        WORKFLOW COMPLETO DI PESATURA                                 │
└─────────────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────┐
  │   ARRIVO    │
  │   VEICOLO   │
  └──────┬──────┘
         │
         ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │ 1. IDENTIFICAZIONE                                              │
  │    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐ │
  │    │ Scansione     │ OR │  Inserimento  │ OR │  Selezione    │ │
  │    │ Badge RFID    │    │  Targa Manual │    │  da Lista     │ │
  │    └───────────────┘    └───────────────┘    └───────────────┘ │
  └──────────────────────────────┬──────────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │ 2. CREAZIONE ACCESSO                                            │
  │    ┌─────────────────────────────────────────────────────────┐ │
  │    │  Access Record                                          │ │
  │    │  • status: WAITING                                      │ │
  │    │  • type: MANUALLY / RESERVATION / TEST                  │ │
  │    │  • typeSubject: CLIENTE / FORNITORE                     │ │
  │    │  • Links: Vehicle, Driver, Subject, Vector              │ │
  │    └─────────────────────────────────────────────────────────┘ │
  └──────────────────────────────┬──────────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │ 3. VISUALIZZAZIONE PANNELLO                                     │
  │    ┌─────────────────────────────────────────────────────────┐ │
  │    │  "TARGA: AB123CD - POSIZIONE: 3"                        │ │
  │    │  Messaggio inviato via TCP/HTTP al display              │ │
  │    └─────────────────────────────────────────────────────────┘ │
  └──────────────────────────────┬──────────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │ 4. PRIMA PESATURA (INGRESSO)                                    │
  │    ┌─────────────────────────────────────────────────────────┐ │
  │    │  Veicolo sulla bilancia                                 │ │
  │    │  ↓                                                      │ │
  │    │  Bilancia → Peso Stabile → Callback cb_weighing         │ │
  │    │  ↓                                                      │ │
  │    │  Weighing Record (Weight1)                              │ │
  │    │  • weight: 15000 kg                                     │ │
  │    │  • tare: 0                                              │ │
  │    │  • date: timestamp                                      │ │
  │    │  ↓                                                      │ │
  │    │  InOut Record creato                                    │ │
  │    │  • idWeight1 = Weighing.id                              │ │
  │    │  ↓                                                      │ │
  │    │  Access.status → ENTERED                                │ │
  │    └─────────────────────────────────────────────────────────┘ │
  └──────────────────────────────┬──────────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │ 5. OPERAZIONI INTERMEDIE                                        │
  │    ┌─────────────────────────────────────────────────────────┐ │
  │    │  • Carico/Scarico materiale                             │ │
  │    │  • Selezione materiale                                  │ │
  │    │  • Foto (opzionale)                                     │ │
  │    │  • Note/Documento riferimento                           │ │
  │    └─────────────────────────────────────────────────────────┘ │
  └──────────────────────────────┬──────────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │ 6. SECONDA PESATURA (USCITA)                                    │
  │    ┌─────────────────────────────────────────────────────────┐ │
  │    │  Veicolo sulla bilancia                                 │ │
  │    │  ↓                                                      │ │
  │    │  Bilancia → Peso Stabile → Callback cb_weighing         │ │
  │    │  ↓                                                      │ │
  │    │  Weighing Record (Weight2)                              │ │
  │    │  • weight: 25000 kg                                     │ │
  │    │  ↓                                                      │ │
  │    │  InOut Record aggiornato                                │ │
  │    │  • idWeight2 = Weighing.id                              │ │
  │    │  • net_weight = |Weight2 - Weight1| = 10000 kg          │ │
  │    │  ↓                                                      │ │
  │    │  Access.status → CLOSED                                 │ │
  │    └─────────────────────────────────────────────────────────┘ │
  └──────────────────────────────┬──────────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │ 7. GENERAZIONE REPORT                                           │
  │    ┌─────────────────────────────────────────────────────────┐ │
  │    │  • PDF generato con WeasyPrint                          │ │
  │    │  • Salvato in /var/opt/in-out/pdf/                      │ │
  │    │  • Stampato via CUPS (se configurato)                   │ │
  │    │  • Sincronizzato in remoto (se attivo)                  │ │
  │    └─────────────────────────────────────────────────────────┘ │
  └──────────────────────────────┬──────────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────┐
  │   USCITA    │
  │   VEICOLO   │
  └─────────────┘
```

---

## 5. Comunicazione Hardware

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         SCHEMA COMUNICAZIONE HARDWARE                                │
└─────────────────────────────────────────────────────────────────────────────────────┘

                              ┌───────────────────┐
                              │    MAIN THREAD    │
                              │    (mainprg)      │
                              │    Loop 0.5s      │
                              └─────────┬─────────┘
                                        │
         ┌──────────────────────────────┼──────────────────────────────┐
         │                              │                              │
         ▼                              ▼                              ▼
┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐
│  WEIGHER THREAD │          │   RFID THREAD   │          │  SYNC THREAD    │
│                 │          │                 │          │                 │
│ Protocolli:     │          │ Protocollo:     │          │ Protocolli:     │
│ • DGT1          │          │ • Serial ASCII  │          │ • SFTP          │
│ • EGT-AF03      │          │   9600 baud     │          │ • SMB/CIFS      │
│                 │          │                 │          │                 │
│ Connessione:    │          │ Connessione:    │          │ Watchdog:       │
│ • TCP (23)      │          │ • /dev/ttyACM0  │          │ • File monitor  │
│ • Serial RS485  │          │                 │          │                 │
└────────┬────────┘          └────────┬────────┘          └────────┬────────┘
         │                            │                            │
         │ Callbacks:                 │ Callback:                  │
         │ • cb_realtime              │ • cb_code_identify         │
         │ • cb_weighing              │                            │
         │ • cb_diagnostic            │                            │
         │ • cb_rele                  │                            │
         │                            │                            │
         ▼                            ▼                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              FASTAPI / WEBSOCKET                                     │
│                                                                                      │
│  WebSocket Channels:                                                                 │
│  • /api/command-weigher/realtime  → Peso in tempo reale                             │
│  • /api/anagrafic/*/ws            → Aggiornamenti dati anagrafici                   │
│  • Lock notifications             → Notifiche blocco record                          │
└─────────────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           PROTOCOLLI BILANCE                                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  EGT-AF03 (DIN 43859):                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  REXT     → Richiesta peso tempo reale                                      │   │
│  │  PID      → Lettura ID prodotto                                             │   │
│  │  TARE     → Tara bilancia                                                   │   │
│  │  ZERO     → Azzeramento                                                     │   │
│  │  MVOL/RAZF→ Diagnostica                                                     │   │
│  │  OUTP X   → Controllo relay (X = 0-7)                                       │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  Response Format:                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  Status | Weight | Unit | Tare | Net | Flags                                │   │
│  │  ST     | 15000  | kg   | 0    | 0   | OK                                   │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          ADATTATORI PANNELLO/SIRENA                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐    │
│  │  TCP RAW    │      │ TCP CUSTOM  │      │    HTTP     │      │  DISABLED   │    │
│  │  Binary     │      │   ASCII     │      │   REST API  │      │   Nessuna   │    │
│  │  Protocol   │      │  Protocol   │      │   JSON      │      │  Comunic.   │    │
│  └─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘    │
│                                                                                      │
│  Funzionalità Pannello:                                                             │
│  • Messaggi scrolling                                                               │
│  • Buffer messaggi                                                                   │
│  • Limite parole configurabile                                                      │
│                                                                                      │
│  Funzionalità Sirena:                                                               │
│  • Attivazione allarme                                                              │
│  • Controllo durata                                                                  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. API Endpoints

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              MAPPA API ENDPOINTS                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  /api/auth                          [Autenticazione]                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  POST   /login          🔓 PUBLIC   → Login, ritorna JWT                            │
│  POST   /register       🔒 ADMIN    → Registra nuovo utente                         │
│  GET    /me             🔒 AUTH     → Dati utente corrente                          │
│  GET    /users          🔒 ADMIN    → Lista tutti utenti                            │
│  GET    /user/{id}      🔒 ADMIN    → Dettaglio utente                              │
│  PUT    /user/{id}      🔒 ADMIN    → Modifica utente                               │
│  DELETE /user/{id}      🔒 S.ADMIN  → Elimina utente                                │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  /api/anagrafic                     [Gestione Anagrafiche]                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  CRUD per ogni entità: subject, vector, driver, vehicle, material, operator         │
│                                                                                      │
│  GET    /{entity}           🔒 AUTH     → Lista con paginazione e filtri            │
│  GET    /{entity}/{id}      🔒 AUTH     → Dettaglio record                          │
│  POST   /{entity}           🔒 WRITE    → Crea record                               │
│  PUT    /{entity}/{id}      🔒 WRITE    → Modifica record                           │
│  DELETE /{entity}/{id}      🔒 ADMIN    → Elimina record                            │
│                                                                                      │
│  WebSocket:                                                                          │
│  WS     /{entity}/ws        🔒 AUTH     → Real-time updates                         │
│                                                                                      │
│  Lock System:                                                                        │
│  POST   /{entity}/lock      🔒 WRITE    → Blocca record per modifica                │
│  POST   /{entity}/unlock    🔒 WRITE    → Sblocca record                            │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  /api/anagrafic/access              [Gestione Accessi]                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  GET    /                   🔒 AUTH     → Lista accessi (con filtri status/date)    │
│  GET    /{id}               🔒 AUTH     → Dettaglio accesso con InOut               │
│  POST   /                   🔒 WRITE    → Crea nuovo accesso                        │
│  PUT    /{id}               🔒 WRITE    → Modifica accesso                          │
│  DELETE /{id}               🔒 ADMIN    → Elimina accesso                           │
│  POST   /{id}/select        🔒 WRITE    → Seleziona per pesatura                    │
│  POST   /{id}/hide          🔒 WRITE    → Nascondi dalla lista                      │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  /api/config-weigher                 [Configurazione Bilance]                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  GET    /configuration       🔒 AUTH     → Configurazione completa                  │
│  PATCH  /configuration/mode  🔒 S.ADMIN  → Imposta modalità operativa               │
│  PATCH  /configuration/...   🔒 S.ADMIN  → Imposta flag (reservation/badge/ecc.)    │
│  PATCH  /configuration/path-*🔒 S.ADMIN  → Imposta percorsi (pdf/csv/img)           │
│  GET    /terminals           🔒 AUTH     → Lista tipi terminale disponibili          │
│  GET    /all/instance        🔒 AUTH     → Lista tutte le istanze bilance            │
│  GET    /instance/node       🔒 AUTH     → Dettaglio nodo bilancia                   │
│  POST   /instance/node       🔒 S.ADMIN  → Aggiungi nodo bilancia                   │
│  PATCH  /instance/node       🔒 S.ADMIN  → Modifica nodo bilancia                   │
│  DELETE /instance/node       🔒 S.ADMIN  → Elimina nodo bilancia                    │
│  POST   /instance/connection 🔒 AUTH     → Aggiungi connessione istanza              │
│  PATCH  /instance/connection 🔒 AUTH     → Modifica connessione istanza              │
│  DELETE /instance/connection 🔒 AUTH     → Elimina connessione istanza               │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  /api/command-weigher               [Controllo Bilance]                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  WS     /realtime           🔒 AUTH     → Stream peso tempo reale                   │
│  POST   /diagnostic         🔒 AUTH     → Avvia diagnostica                         │
│  POST   /weighing/in        🔒 WRITE    → Pesatura ingresso                         │
│  POST   /weighing/out       🔒 WRITE    → Pesatura uscita                           │
│  POST   /weighing/auto      🔓 PUBLIC   → Pesatura automatica (badge)              │
│  POST   /tare               🔒 WRITE    → Tara bilancia                             │
│  POST   /zero               🔒 WRITE    → Azzera bilancia                           │
│  POST   /rele               🔒 WRITE    → Controlla relay                           │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  /api/data                          [Dati Bilance]                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  GET    /realtime           🔒 AUTH     → Peso attuale                              │
│  GET    /config             🔒 AUTH     → Configurazione bilancia                   │
│  GET    /terminal           🔒 AUTH     → Dati terminale                            │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  /api/in-out                        [API Pubblica Export]                           │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  GET    /list               🔓 PUBLIC   → Lista pesature con filtri data           │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  /api/printer                       [Gestione Stampa]                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  GET    /list               🔒 AUTH     → Lista stampanti disponibili               │
│  POST   /test/{name}        🔒 AUTH     → Test stampa                               │
│  GET    /connection         🔒 AUTH     → Stato connessione CUPS                    │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  /api/generic                       [Utilità Generali]                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  POST   /report/xlsx        🔒 AUTH     → Genera report Excel                       │
│  POST   /report/pdf         🔒 AUTH     → Genera report PDF                         │
│  GET    /config             🔒 ADMIN    → Configurazione sistema                    │
│  PUT    /config             🔒 ADMIN    → Modifica configurazione                   │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  /api/sync-folder                   [Sincronizzazione]                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  GET    /config             🔒 ADMIN    → Config sincronizzazione                   │
│  PUT    /config             🔒 ADMIN    → Modifica config sync                      │
│  GET    /status             🔒 AUTH     → Stato sincronizzazione                    │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  /api/tunnel_connections            [Tunnel SSH]                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  GET    /config             🔒 ADMIN    → Config tunnel SSH                         │
│  PUT    /config             🔒 ADMIN    → Modifica config tunnel                    │
│  GET    /status             🔒 AUTH     → Stato connessione tunnel                  │
└─────────────────────────────────────────────────────────────────────────────────────┘

Legenda:  🔓 PUBLIC = Nessuna autenticazione richiesta
          🔒 AUTH   = Token JWT richiesto
          🔒 WRITE  = Token JWT + Livello scrittura
          🔒 ADMIN  = Token JWT + Livello admin
          🔒 S.ADMIN= Token JWT + Livello super admin
```

---

## 7. Struttura Directory del Progetto

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         STRUTTURA DIRECTORY PROGETTO                                 │
└─────────────────────────────────────────────────────────────────────────────────────┘

/home/user/in-out/
│
├── main.py                          # Entry point applicazione
├── start.sh                         # Script di avvio
├── config.json                      # Configurazione principale
├── requirements.txt                 # Dipendenze Python
│
├── applications/                    # Applicazione FastAPI
│   ├── app_api.py                  # Inizializzazione FastAPI
│   │
│   ├── middleware/                  # Middleware di sicurezza
│   │   ├── auth.py                 # Validazione JWT
│   │   ├── admin.py                # Controllo ruolo admin
│   │   ├── super_admin.py          # Controllo super admin
│   │   ├── writable_user.py        # Controllo permessi scrittura
│   │   └── public_endpoints.py     # Lista endpoint pubblici
│   │
│   ├── router/                      # API Routers
│   │   ├── anagrafic/              # CRUD dati anagrafici
│   │   │   ├── subject.py          # Clienti/Fornitori
│   │   │   ├── vector.py           # Trasportatori
│   │   │   ├── driver.py           # Autisti
│   │   │   ├── vehicle.py          # Veicoli
│   │   │   ├── material.py         # Materiali
│   │   │   ├── operator.py         # Operatori
│   │   │   └── access.py           # Accessi/Pesature
│   │   │
│   │   ├── weigher/                # Controllo bilance
│   │   │   ├── command.py          # Comandi bilancia
│   │   │   └── data.py             # Dati tempo reale
│   │   │
│   │   ├── auth.py                 # Autenticazione
│   │   ├── printer.py              # Gestione stampa
│   │   ├── generic.py              # Report e utilità
│   │   ├── open_to_customer.py     # API pubblica
│   │   ├── sync_folder.py          # Sincronizzazione
│   │   └── tunnel_connections.py   # Tunnel SSH
│   │
│   ├── utils/                       # Helper functions
│   │
│   └── static/                      # Asset statici
│       └── ui/default/             # Template HTML/CSS/JS
│
├── modules/                         # Moduli core business logic
│   ├── md_weigher/                 # Interfaccia bilance
│   │   ├── __init__.py
│   │   ├── terminals/              # Protocolli bilance (dgt1, egt-af03)
│   │   ├── types.py                # Tipi dati (Realtime, Weight, ecc.)
│   │   └── globals.py              # Registry terminali (terminalsClasses)
│   │
│   ├── md_database/                # Database ORM
│   │   ├── __init__.py
│   │   ├── models.py               # Modelli SQLAlchemy
│   │   └── connection.py           # Connessione DB
│   │
│   ├── md_rfid/                    # Lettore RFID
│   │   └── __init__.py
│   │
│   ├── md_sync_folder/             # Sincronizzazione remota
│   │   └── __init__.py
│   │
│   ├── md_tunnel_connections/      # Tunnel SSH
│   │   └── __init__.py
│   │
│   └── md_desktop_interface/       # GUI Desktop (Tkinter)
│       └── __init__.py
│
├── libs/                            # Librerie condivise
│   ├── lb_config.py                # Gestione configurazione
│   ├── lb_log.py                   # Sistema di logging
│   ├── lb_system.py                # Connessioni Serial/TCP
│   ├── lb_printer.py               # Stampa CUPS
│   ├── lb_capture_camera.py        # Cattura fotocamera
│   └── lb_utils.py                 # Utility generiche
│
├── tmt-cups/                        # Backend stampante CUPS
│
└── /var/opt/in-out/                 # Directory dati runtime
    ├── database.db                  # Database SQLite
    ├── pdf/                         # Report PDF generati
    ├── csv/                         # Export CSV
    └── images/                      # Foto catturate
```

---

## 8. Configurazione Sistema (config.json)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         STRUTTURA CONFIGURAZIONE                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘

config.json
│
├── ver: "3.0.1"                              # Versione software
├── secret_key: "..."                         # Chiave crittografia JWT
│
└── app_api:                                  # Configurazione applicazione
    │
    ├── mode: "AUTOMATIC"                     # Modalità operativa
    ├── port: 80                              # Porta HTTP
    │
    ├── Paths:
    │   ├── path_database: "/var/opt/in-out/database.db"
    │   ├── path_ui: "static/ui/default"
    │   ├── path_img: "/var/opt/in-out/images"
    │   ├── path_pdf: "/var/opt/in-out/pdf"
    │   └── path_csv: "/var/opt/in-out/csv"
    │
    ├── panel:                                # Configurazione pannello
    │   ├── enabled: true/false
    │   ├── type: "tcp_raw" | "tcp_custom" | "http" | "disabled"
    │   └── connection: {ip, port}
    │
    ├── siren:                                # Configurazione sirena
    │   ├── enabled: true/false
    │   └── type: "tcp" | "http" | "disabled"
    │
    ├── weighers:                             # Configurazione bilance
    │   └── "0":                              # ID bilancia
    │       ├── connection: {ip, port} | {serial_port, baudrate}
    │       └── nodes:
    │           └── "3590-EGT":               # Nome nodo
    │               ├── terminal: "egt-af03" | "dgt1"  # Dinamico via GET /terminals
    │               ├── max_weight: 60000
    │               ├── min_weight: 400
    │               └── events: {...}         # Callback configurabili
    │
    ├── rfid:                                 # Configurazione lettore RFID
    │   ├── connection: {serial_port_name, baudrate}
    │   └── module: "rfidserialrfid"
    │
    ├── sync_folder:                          # Sincronizzazione remota
    │   ├── enabled: true/false
    │   ├── protocol: "sftp" | "smb"
    │   ├── local_dir: "/var/opt/in-out"
    │   ├── sub_paths: ["pdf", "csv", "images"]
    │   └── remote: {host, user, password, path}
    │
    ├── ssh_reverse_tunneling:                # Accesso remoto
    │   ├── enabled: true/false
    │   ├── server: "on.baron.it"
    │   ├── ssh_port: 10022
    │   └── local_port: 80
    │
    └── use_anagrafic:                        # Feature flags
        ├── subject: true
        ├── vector: true
        ├── driver: true
        ├── material: true
        ├── operator: false
        ├── weighing_pictures: true
        ├── document_reference: true
        └── note: true
```

---

## 9. Diagramma Relazioni Entità

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              ENTITY RELATIONSHIP DIAGRAM                             │
└─────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌───────────┐
                                    │   USER    │
                                    │───────────│
                                    │ id        │
                                    │ username  │
                                    │ password  │
                                    │ level     │
                                    └─────┬─────┘
                                          │
                                          │ 1
                                          │
                                          │ registra
                                          │
                                          ▼ *
┌───────────┐    1          *    ┌───────────────┐    *          1    ┌───────────┐
│  SUBJECT  │◄───────────────────│    ACCESS     │───────────────────►│  VECTOR   │
│───────────│                    │───────────────│                    │───────────│
│ id        │                    │ id            │                    │ id        │
│ social_   │                    │ number_in_out │                    │ social_   │
│ reason    │                    │ status        │                    │ reason    │
│ telephone │                    │ type          │                    │ telephone │
│ cfpiva    │                    │ typeSubject   │                    │ cfpiva    │
└───────────┘                    │ badge         │                    └───────────┘
                                 │ selected      │
                                 │ hidden        │
┌───────────┐    1          *    │ date_created  │    *          1    ┌───────────┐
│  DRIVER   │◄───────────────────│               │───────────────────►│  VEHICLE  │
│───────────│                    └───────┬───────┘                    │───────────│
│ id        │                            │                            │ id        │
│ social_   │                            │ 1                          │ plate     │
│ reason    │                            │                            │ tare      │
│ telephone │                            │                            │ descrip.  │
└───────────┘                            │ ha                         └───────────┘
                                         │
                                         ▼ *
                                 ┌───────────────┐
                                 │     INOUT     │
                                 │───────────────│
                                 │ id            │
                                 │ net_weight    │◄────────────┐
                                 │ idAccess (FK) │             │
                                 │ idMaterial(FK)│───────────┐ │
                                 │ idWeight1(FK) │─────────┐ │ │
                                 │ idWeight2(FK) │───────┐ │ │ │
                                 └───────────────┘       │ │ │ │
                                                         │ │ │ │
                    ┌────────────────────────────────────┘ │ │ │
                    │   ┌──────────────────────────────────┘ │ │
                    │   │                                    │ │
                    ▼   ▼                                    │ │
            ┌───────────────┐                                │ │
            │   WEIGHING    │                                │ │
            │───────────────│                                │ │
            │ id            │                                │ │
            │ date          │                                │ │
            │ weight        │    ┌───────────────┐           │ │
            │ tare          │    │   OPERATOR    │           │ │
            │ log           │◄───│───────────────│           │ │
            │ idUser (FK)   │    │ id            │           │ │
            │ idOperator(FK)│    │ description   │           │ │
            └───────┬───────┘    └───────────────┘           │ │
                    │                                        │ │
                    │ 1                     ┌────────────────┘ │
                    │                       │                  │
                    │ ha                    ▼                  │
                    │            ┌───────────────┐             │
                    ▼ *          │   MATERIAL    │             │
          ┌─────────────────┐    │───────────────│             │
          │WEIGHING_PICTURE │    │ id            │◄────────────┘
          │─────────────────│    │ description   │
          │ id              │    └───────────────┘
          │ path_name       │
          │ idWeighing (FK) │
          └─────────────────┘
```

---

## 10. Ciclo di Vita Thread

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           CICLO DI VITA APPLICAZIONE                                 │
└─────────────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │    start.sh     │
                              │    Avvio App    │
                              └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │    main.py      │
                              │   Entry Point   │
                              └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │  Load Config    │
                              │  config.json    │
                              └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │  Init Logger    │
                              │   lb_log.py     │
                              └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │  Init Database  │
                              │  md_database    │
                              └────────┬────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
              ▼                        ▼                        ▼
    ┌─────────────────┐     ┌─────────────────┐      ┌─────────────────┐
    │  Start Weigher  │     │  Start FastAPI  │      │  Start RFID     │
    │     Thread      │     │     Thread      │      │     Thread      │
    │   md_weigher    │     │    Uvicorn      │      │    md_rfid      │
    └────────┬────────┘     └────────┬────────┘      └────────┬────────┘
             │                       │                        │
             │                       │                        │
              ┌─────────────────────┼───────────────────────┐
              │                     │                       │
              ▼                     ▼                       ▼
    ┌─────────────────┐   ┌─────────────────┐    ┌─────────────────┐
    │  Start Sync     │   │ Start Desktop   │    │  Start Tunnel   │
    │  Folder Thread  │   │ Interface Thread│    │     Thread      │
    │ md_sync_folder  │   │ md_desktop_int. │    │ md_tunnel_conn. │
    └─────────────────┘   └─────────────────┘    └─────────────────┘
              │                     │                       │
              └─────────────────────┼───────────────────────┘
                                    │
                                    ▼
                          ┌─────────────────┐
                          │   Main Loop     │
                          │   mainprg()     │
                          │   Sleep 0.5s    │
                          │                 │
                          │ • Check config  │
                          │ • Monitor health│
                          │ • Handle signals│
                          └─────────────────┘
                                    │
                                    │ SIGTERM/SIGINT
                                    ▼
                          ┌─────────────────┐
                          │   Shutdown      │
                          │                 │
                          │ • Stop threads  │
                          │ • Close DB      │
                          │ • Cleanup       │
                          └─────────────────┘
```

---

## Legenda

| Simbolo | Significato |
|---------|-------------|
| → | Direzione del flusso dati |
| ◄─► | Relazione bidirezionale |
| FK | Foreign Key (Chiave Esterna) |
| PK | Primary Key (Chiave Primaria) |
| 1 / * | Cardinalità (uno-a-molti) |
| 🔓 | Endpoint pubblico |
| 🔒 | Endpoint protetto |

---

*Documento generato automaticamente - BARON IN-OUT v3.0.1*
