# Sistema di Controllo Sbarre con Priorità Veicoli

## Panoramica

Sistema di gestione accessi e pesatura con controllo automatico delle sbarre, integrato con un sistema esterno di identificazione targhe. La priorità determina l'ordine di servizio in coda quando più prenotazioni condividono la stessa data.

---

## 1. Il Processo

### Fase 1: Arrivo del Mezzo

1. Il veicolo arriva all'ingresso del sito
2. Il **sistema esterno** (del cliente) identifica la targa tramite telecamera
3. Il sistema esterno chiama la nostra API per creare un **accesso**, passando:
   - **Targa** del veicolo
   - **Data/ora** dell'arrivo
   - **Slot** assegnato (fascia oraria o posizione)
   - **Priorità** (usata per ordinare la coda in caso di stessa data)
4. L'accesso può essere di due tipi:
   - **Con pesatura** → accesso normale (tabella `access`)
   - **Solo transito** → senza pesatura (tabella `transit_access`)

### Fase 2: Gestione Coda e Apertura Sbarra

Il software monitora continuamente la Pesa 1. Quando la pesa è **vuota** (peso sotto `min_weight`):

1. Cerca il prossimo accesso da servire con questo criterio:
   - Prima passa la prenotazione con **data meno recente** (la più vecchia ha precedenza)
   - A parità di data, passa quella con **priorità più alta**
2. Apre la sbarra corrispondente
3. Mostra la targa sul **pannello** e attiva la **sirena**
4. Quando il veicolo sale sulla pesa (peso >= `min_weight`) → **chiude la sbarra**

### Fase 3: Pesatura Automatica sulla Pesa 2

Per i veicoli con accesso **con pesatura**:

1. Il veicolo procede dalla Pesa 1 alla Pesa 2
2. Viene identificato automaticamente tramite **telecamera** (targa) o **badge** RFID
3. Il sistema esegue la pesatura automatica: attende stabilità, registra il peso, genera report
4. L'accesso viene chiuso

### Fase 4: Transito Senza Pesata

Per i veicoli registrati come **solo transito** (`transit_access`):

1. La sbarra si apre normalmente seguendo l'ordine di coda
2. Il veicolo transita sulla Pesa 1 ma la **pesatura NON scatta**
3. Viene registrato solo il passaggio (data/ora)
4. Utile per veicoli di servizio o mezzi che non necessitano di pesatura

---

## 2. Ordinamento della Coda

La coda viene ordinata così:

1. **Data prenotazione ASC** — la prenotazione più vecchia passa prima
2. **Priorità DESC** — a parità di data, passa prima quella con priorità più alta

Esempio:

| Targa  | Data Prenotazione | Priorità | Ordine di Servizio |
|--------|-------------------|----------|--------------------|
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
     │                        │◄──────────────────────│ pesa vuota      │               │
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
     │                        │◄──────────────────────│ peso rilevato   │               │
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

Tabella separata per i soli transiti (senza pesatura). Contiene: targa, slot, priorità, data ingresso/uscita, note, ID dal sistema esterno.

### 4.2 API per il Sistema Esterno

Endpoint per il sistema esterno per caricare gli accessi:

- `POST /api/open-to-customer/access` — Crea accesso **con pesatura** (con targa, slot, priorità)
- `POST /api/open-to-customer/transit-access` — Crea accesso **solo transito** (con targa, slot, priorità)

### 4.3 Automatismo Apertura Sbarre

Nel `Callback_Realtime`, quando la pesa è vuota:

1. Cercare il prossimo accesso/transito in coda (data ASC, priorità DESC)
2. Aprire il relè della sbarra
3. Quando il veicolo sale sulla pesa, chiudere la sbarra
4. Se è un transito → registrare solo il passaggio, non avviare pesatura
5. Se è un accesso normale → procedere con il flusso di pesatura esistente

---

## 5. Esempi Pratici

**Veicolo con pesatura:** Sistema esterno invia targa + data + priorità → pesa vuota → apre sbarra → veicolo transita su Pesa 1 → chiude sbarra → va a Pesa 2 → pesatura automatica → accesso chiuso.

**Veicolo solo transito:** Sistema esterno invia targa + data + priorità + tipo transito → pesa vuota → apre sbarra → veicolo passa → chiude sbarra → registra passaggio → nessuna pesatura.

**Coda con stessa data:** Due veicoli prenotati per la stessa data, uno con priorità 3 e uno con priorità 1 → passa prima quello con priorità 3. Se hanno date diverse, passa prima quello con data più vecchia indipendentemente dalla priorità.
