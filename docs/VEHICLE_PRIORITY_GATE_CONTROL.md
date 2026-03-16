# Sistema di Controllo Sbarre con Priorita Veicoli

## Panoramica

Sistema di gestione accessi e pesatura con **doppia sbarra** e **priorita veicoli**, integrato con un sistema esterno di identificazione targhe.

---

## 1. Il Processo

### Fase 1: Arrivo del Mezzo

1. Il veicolo arriva all'ingresso del sito
2. Il **sistema esterno** (del cliente) identifica la targa tramite telecamera
3. Il sistema esterno chiama la nostra API per creare un **accesso**, passando:
   - **Targa** del veicolo
   - **Data/Ora** dell'arrivo
   - **Slot** assegnato (fascia oraria o posizione)
   - **Priorita** (determina quale sbarra aprire)
4. L'accesso puo essere di due tipi:
   - **Con pesatura** → accesso normale (tabella `access`)
   - **Solo transito** → senza pesatura (tabella `transit_access`)

### Fase 2: Apertura Sbarra in Base alla Priorita

Il software monitora continuamente la Pesa 1. Quando la pesa e **vuota** (peso sotto `min_weight`):

1. Cerca il prossimo accesso in coda (sia `access` che `transit_access`) ordinato per **priorita decrescente** (a parita, il piu vecchio prima)
2. In base alla priorita del veicolo selezionato:
   - **Priorita ALTA** → Apre **Sbarra 1** (corsia preferenziale)
   - **Priorita BASSA** → Apre **Sbarra 2** (corsia normale)
3. Mostra la targa sul **pannello** e attiva la **sirena**
4. Quando il veicolo sale sulla pesa (peso >= `min_weight`) → **chiude la sbarra**

### Fase 3: Pesatura Automatica sulla Pesa 2

Per i veicoli con accesso **con pesatura**:

1. Il veicolo procede dalla Pesa 1 alla Pesa 2
2. Viene identificato automaticamente tramite **telecamera** (targa) o **badge** RFID
3. Il sistema esegue la pesata automatica: attende stabilita, registra il peso, genera report
4. L'accesso viene chiuso

### Fase 4: Transito Senza Pesata

Per i veicoli registrati come **solo transito** (`transit_access`):

1. Le sbarre si aprono normalmente in base alla priorita
2. Il veicolo transita sulla Pesa 1 ma la **pesatura NON scatta**
3. Viene registrato solo il passaggio (data/ora)
4. Utile per veicoli di servizio o mezzi che non necessitano di pesatura

---

## 2. Schema del Processo

```
Sistema Esterno          Nostro Software            Pesa 1          Sbarra 1/2       Pesa 2
     │                        │                       │                 │               │
     │  POST /access          │                       │                 │               │
     │  (targa, slot,         │                       │                 │               │
     │   priorita, tipo)      │                       │                 │               │
     │───────────────────────►│                       │                 │               │
     │                        │  Salva accesso        │                 │               │
     │                        │                       │                 │               │
     │                        │  [Monitoraggio Pesa]  │                 │               │
     │                        │◄──────────────────────│ pesa vuota      │               │
     │                        │                       │                 │               │
     │                        │  Cerca prossimo       │                 │               │
     │                        │  per priorita         │                 │               │
     │                        │                       │                 │               │
     │                        │  Apri sbarra ─────────────────────────►│               │
     │                        │  (1 o 2 da priorita)  │                 │ APERTA        │
     │                        │                       │                 │               │
     │                        │  Pannello + Sirena    │                 │               │
     │                        │                       │                 │               │
     │                  [Veicolo sale sulla pesa]      │                 │               │
     │                        │◄──────────────────────│ peso rilevato   │               │
     │                        │                       │                 │               │
     │                        │  Chiudi sbarra ───────────────────────►│ CHIUSA        │
     │                        │                       │                 │               │
     │                        │                       │                 │               │
     │                        │  ┌─ SE solo transito: │                 │               │
     │                        │  │  Registra passaggio│                 │               │
     │                        │  │  FINE              │                 │               │
     │                        │  │                    │                 │               │
     │                        │  └─ SE con pesatura:  │                 │               │
     │                        │     Veicolo va a Pesa 2                │               │
     │                        │                       │                 │               │
     │                        │  Identificazione ─────────────────────────────────────►│
     │                        │  (telecamera/badge)   │                 │               │
     │                        │◄──────────────────────────────────────────────────────│
     │                        │  Pesatura automatica  │                 │               │
     │                        │  Accesso chiuso       │                 │               │
```

---

## 3. Cosa Serve Implementare

### 3.1 Tabella `transit_access`

Tabella separata per i soli transiti (senza pesatura). Contiene: targa, slot, priorita, sbarra usata, data ingresso/uscita, note, ID dal sistema esterno.

### 3.2 API per il Sistema Esterno

Endpoint per il sistema esterno per caricare gli accessi:

- `POST /api/open-to-customer/access` — Crea accesso **con pesatura** (con targa, slot, priorita)
- `POST /api/open-to-customer/transit-access` — Crea accesso **solo transito** (con targa, slot, priorita)

### 3.3 Automatismo Apertura Sbarre

Nel `Callback_Realtime`, quando la pesa e vuota:

1. Cercare il prossimo accesso/transito in coda per priorita
2. Aprire il rele della sbarra corretta (configurazione gate → rele nel `config.json`)
3. Quando il veicolo sale sulla pesa, chiudere la sbarra
4. Se e un transito → registrare solo il passaggio, non avviare pesatura
5. Se e un accesso normale → procedere con il flusso di pesatura esistente

### 3.4 Configurazione Sbarre

Nuova sezione `gate_control` nella configurazione del nodo pesa per mappare priorita → sbarra → rele:

```json
"gate_control": {
  "enabled": true,
  "gate_1": { "rele": "2", "min_priority": 2 },
  "gate_2": { "rele": "3", "min_priority": 1 }
}
```

---

## 4. Esempi Pratici

**Veicolo priorita alta con pesatura:** Sistema esterno invia targa + priorita 3 → pesa vuota → apre Sbarra 1 → veicolo pesa su Pesa 1 → chiude sbarra → va a Pesa 2 → pesatura automatica → accesso chiuso.

**Veicolo solo transito:** Sistema esterno invia targa + priorita 2 + tipo transito → pesa vuota → apre sbarra in base a priorita → veicolo passa → chiude sbarra → registra passaggio → nessuna pesatura.

**Coda mista:** Tre veicoli in coda con priorita 1, 3, 2 → viene servito prima quello con priorita 3 (Sbarra 1), poi 2 (Sbarra 1), poi 1 (Sbarra 2).
