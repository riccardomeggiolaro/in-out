# Sistema di Controllo Sbarre con Priorità Veicoli

## Panoramica

Sistema di gestione accessi e pesatura con controllo automatico delle sbarre, integrato con un sistema esterno di identificazione targhe. La priorità determina l'ordine di servizio in coda quando più prenotazioni condividono la stessa data.

---

## 1. Il Processo

### Fase 1: Arrivo del Mezzo

1. Il veicolo arriva all'ingresso del sito.
2. Il **sistema esterno** (del cliente) identifica la targa tramite telecamera.
3. Il sistema esterno chiama la nostra API per creare un **accesso**, passando:
   - **Targa** del veicolo
   - **Data/ora** dell'arrivo
   - **Slot** assegnato (fascia oraria o posizione)
   - **Priorità** (usata per ordinare la coda in caso di stessa data)
4. L'accesso può essere di due tipi:
   - **Con pesatura** → accesso normale (tabella `access`)
   - **Solo transito** → senza pesatura (tabella `transit_access`)

### Fase 2: Gestione della Coda e Apertura della Sbarra

Il software monitora continuamente la Pesa 1. Quando la pesa è **vuota** (peso sotto `min_weight`):

1. Cerca il prossimo accesso da servire secondo questo criterio:
   - Passa prima la prenotazione con **data meno recente** (la più vecchia ha precedenza).
   - A parità di data, passa quella con **priorità più alta**.
2. Apre la sbarra corrispondente.
3. Mostra la targa sul **pannello** e attiva la **sirena**.
4. Quando il veicolo sale sulla pesa (peso ≥ `min_weight`), **chiude la sbarra**.

### Fase 3: Pesatura Automatica sulla Pesa 2

Per i veicoli con accesso **con pesatura**:

1. Il veicolo procede dalla Pesa 1 alla Pesa 2.
2. Viene identificato automaticamente tramite **telecamera** (targa) o **badge** RFID.
3. Il sistema esegue la pesatura automatica: attende la stabilità, registra il peso e genera il report.
4. L'accesso viene chiuso.

### Fase 4: Transito Senza Pesatura

Per i veicoli registrati come **solo transito** (`transit_access`):

1. La sbarra si apre normalmente seguendo l'ordine della coda.
2. Il veicolo transita sulla Pesa 1, ma la **pesatura non viene eseguita**.
3. Viene registrato solo il passaggio (data e ora).
4. Utile per veicoli di servizio o mezzi che non necessitano di pesatura.

---

## 2. Ordinamento della Coda

La coda viene ordinata con i seguenti criteri:

1. **Data di prenotazione ASC** — la prenotazione più vecchia passa prima.
2. **Priorità DESC** — a parità di data, passa prima quella con priorità più alta.

Esempio:

| Targa  | Data di prenotazione | Priorità | Ordine di servizio |
|--------|----------------------|----------|--------------------|
| AB123  | 10/03 ore 08:00      | 1        | **1°** (data più vecchia) |
| CD456  | 11/03 ore 09:00      | 3        | **2°** (stessa data di EF789, priorità più alta) |
| EF789  | 11/03 ore 09:00      | 1        | **3°** (stessa data di CD456, priorità più bassa) |
| GH012  | 12/03 ore 10:00      | 2        | **4°** (data più recente) |

---

## 3. Schema del Processo

```
Sistema Esterno          Nostro Software            Pesa 1           Sbarra           Pesa 2
     │                        │                       │                 │               │
     │  POST /access          │                       │                 │               │
     │  (targa, slot,         │                       │                 │               │
     │   priorità, tipo)      │                       │                 │               │
     │───────────────────────►│                       │                 │               │
     │                        │  Salva accesso        │                 │               │
     │                        │                       │                 │               │
     │                        │  [Monitoraggio Pesa]  │                 │               │
     │                        │◄──────────────────────│ Pesa vuota      │               │
     │                        │                       │                 │               │
     │                        │  Cerca prossimo       │                 │               │
     │                        │  (data ASC, poi       │                 │               │
     │                        │   priorità DESC)      │                 │               │
     │                        │                       │                 │               │
     │                        │  Apri sbarra ─────────────────────────►│               │
     │                        │                       │                 │ APERTA        │
     │                        │  Pannello + Sirena    │                 │               │
     │                        │                       │                 │               │
     │                  [Veicolo sale sulla pesa]      │                 │               │
     │                        │◄──────────────────────│ Peso rilevato   │               │
     │                        │                       │                 │               │
     │                        │  Chiudi sbarra ───────────────────────►│ CHIUSA        │
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

## 4. Cosa Serve Implementare

### 4.1 Tabella `transit_access`

Tabella separata per i soli transiti (senza pesatura). Contiene: targa, slot, priorità, data di ingresso/uscita, note e ID dal sistema esterno.

### 4.2 API per il Sistema Esterno

Endpoint che il sistema esterno utilizza per caricare gli accessi:

- `POST /api/open-to-customer/access` — Crea un accesso **con pesatura** (targa, slot, priorità).
- `POST /api/open-to-customer/transit-access` — Crea un accesso **solo transito** (targa, slot, priorità).

### 4.3 Automatismo di Apertura delle Sbarre

Nel `Callback_Realtime`, quando la pesa è vuota:

1. Cercare il prossimo accesso o transito in coda (data ASC, priorità DESC).
2. Aprire il relè della sbarra.
3. Quando il veicolo sale sulla pesa, chiudere la sbarra.
4. Se è un transito → registrare solo il passaggio, senza avviare la pesatura.
5. Se è un accesso normale → procedere con il flusso di pesatura esistente.

---

## 5. Esempi Pratici

**Veicolo con pesatura:** il sistema esterno invia targa, data e priorità → la pesa è vuota → si apre la sbarra → il veicolo transita sulla Pesa 1 → si chiude la sbarra → il veicolo va alla Pesa 2 → pesatura automatica → accesso chiuso.

**Veicolo solo transito:** il sistema esterno invia targa, data, priorità e tipo transito → la pesa è vuota → si apre la sbarra → il veicolo passa → si chiude la sbarra → si registra il passaggio → nessuna pesatura.

**Coda con stessa data:** due veicoli prenotati per la stessa data, uno con priorità 3 e uno con priorità 1 → passa prima quello con priorità 3. Se hanno date diverse, passa prima quello con data più vecchia, indipendentemente dalla priorità.
