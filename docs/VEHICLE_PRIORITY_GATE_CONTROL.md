# Sistema di Controllo Sbarre con Priorita Veicoli

## Panoramica

Questo documento descrive il flusso operativo del sistema di gestione accessi e pesatura con **doppia sbarra** e **priorita veicoli**, integrato con un sistema esterno di identificazione targhe.

---

## 1. Architettura del Sistema

```
                    SISTEMA ESTERNO                          NOSTRO SOFTWARE (BARON IN-OUT)
                 (Riconoscimento Targhe)                    (Pesatura + Controllo Sbarre)

  ┌──────────────┐                          ┌──────────────────────────────────────────────┐
  │  Telecamera  │                          │                                              │
  │  Ingresso    │──► Identifica Targa ──►  │  Riceve Accesso con:                         │
  │              │                          │   - Targa                                    │
  └──────────────┘                          │   - Data/Ora                                 │
                                            │   - Slot                                     │
                                            │   - Priorita                                 │
                                            └──────────────┬───────────────────────────────┘
                                                           │
                                                           ▼
                                            ┌──────────────────────────────┐
                                            │  Logica Apertura Sbarre      │
                                            │  (basata su priorita)        │
                                            └──────────────────────────────┘
                                                     │           │
                                          ┌──────────┘           └──────────┐
                                          ▼                                 ▼
                                   ┌─────────────┐                  ┌─────────────┐
                                   │  SBARRA 1   │                  │  SBARRA 2   │
                                   │ (Priorita   │                  │ (Priorita   │
                                   │  ALTA)      │                  │  BASSA)     │
                                   └──────┬──────┘                  └──────┬──────┘
                                          │                                │
                                          ▼                                ▼
                                   ┌─────────────┐                  ┌─────────────┐
                                   │   PESA 1    │                  │   PESA 1    │
                                   │  (stessa    │                  │  (stessa    │
                                   │   pesa)     │                  │   pesa)     │
                                   └─────────────┘                  └─────────────┘
                                          │
                                          ▼
                                   ┌─────────────┐
                                   │   PESA 2    │
                                   │ (Pesatura   │
                                   │ Automatica) │
                                   └─────────────┘
```

---

## 2. Flusso Operativo Dettagliato

### Fase 1: Arrivo del Mezzo e Creazione Accesso

1. Il veicolo arriva all'ingresso del sito
2. Il **sistema esterno** (del cliente) identifica la targa tramite telecamera
3. Il sistema esterno crea un **accesso** nel nostro software tramite API, passando:
   - **Targa** del veicolo
   - **Data/Ora** dell'arrivo
   - **Slot** assegnato (fascia oraria o posizione)
   - **Priorita** (determina quale sbarra aprire)

#### API di Creazione Accesso (dal sistema esterno)

Il sistema esterno chiama il nostro endpoint per creare l'accesso con i dati della targa, slot e priorita. L'accesso viene creato con stato `WAITING`.

### Fase 2: Gestione Sbarre con Priorita

Tra le due sbarre, il nostro software implementa la seguente logica:

1. Il software **monitora costantemente** la Pesa 1 tramite il Callback Realtime
2. Quando la Pesa 1 e **vuota** (peso sotto la soglia minima `min_weight`):
   - Controlla la coda degli accessi in stato `WAITING`
   - Seleziona l'accesso con **priorita piu alta**
   - **Apre la sbarra corretta** in base alla priorita:
     - **Priorita ALTA** → Apre **Sbarra 1** (corsia preferenziale)
     - **Priorita BASSA** → Apre **Sbarra 2** (corsia normale)

#### Logica Decisionale Apertura Sbarra

```
QUANDO Pesa 1 e vuota (peso < min_weight):
  1. Cerca accessi in stato WAITING ordinati per priorita DESC
  2. SE esiste un accesso in attesa:
     a. SE priorita == ALTA:
        - Apri Sbarra 1 (rele sbarra 1)
        - Mostra targa sul pannello
        - Attiva sirena
     b. SE priorita == BASSA:
        - Apri Sbarra 2 (rele sbarra 2)
        - Mostra targa sul pannello
        - Attiva sirena
  3. QUANDO il veicolo sale sulla Pesa 1 (peso >= min_weight):
     - Chiudi la sbarra utilizzata
     - Aggiorna stato accesso a ENTERED
```

### Fase 3: Pesatura Automatica sulla Pesa 2

1. Il veicolo procede dalla Pesa 1 alla **Pesa 2**
2. Sulla Pesa 2, la pesatura avviene **automaticamente** quando il veicolo sale sulla pesa
3. L'identificazione avviene tramite:
   - **Telecamera** (riconoscimento targa)
   - **Badge** RFID
4. Il sistema esegue il callback `WeighingByIdentify` che:
   - Identifica l'accesso tramite targa o badge
   - Attende stabilita del peso
   - Esegue la pesata automatica
   - Salva il record nel database

### Fase 4: Transito Senza Pesata (Solo Accesso)

Alcuni veicoli devono poter **transitare senza effettuare la pesata**. Per questi casi:

1. Il veicolo viene registrato in una **tabella dedicata** (`transit_access`) separata dagli accessi normali
2. Quando il veicolo transita:
   - Le sbarre si aprono normalmente in base alla priorita
   - Il sistema **NON avvia** la procedura di pesatura automatica
   - Viene registrato solo il passaggio (data/ora ingresso e uscita)
3. Questo permette di gestire veicoli di servizio, mezzi autorizzati o trasporti che non necessitano di pesatura

---

## 3. Nuova Tabella: `transit_access` (Soli Accessi/Transiti)

Tabella separata per registrare i transiti che non richiedono pesatura.

### Struttura

| Campo              | Tipo        | Descrizione                                      |
|--------------------|-------------|--------------------------------------------------|
| `id`               | Integer PK  | Identificativo univoco                           |
| `plate`            | String      | Targa del veicolo                                |
| `slot`             | String      | Slot/fascia oraria assegnata                     |
| `priority`         | Integer     | Priorita (1=bassa, 2=media, 3=alta)             |
| `gate`             | Integer     | Sbarra utilizzata (1 o 2)                        |
| `status`           | Enum        | WAITING / TRANSITED / CANCELLED                  |
| `date_in`          | DateTime    | Data/ora di ingresso                             |
| `date_out`         | DateTime    | Data/ora di uscita (nullable)                    |
| `note`             | String      | Note opzionali                                   |
| `date_created`     | DateTime    | Data di creazione del record                     |
| `source_system_id` | String      | ID dal sistema esterno (per tracciabilita)        |

### Differenze rispetto alla tabella `access`

| Caratteristica        | `access` (Pesatura)         | `transit_access` (Solo Transito) |
|-----------------------|-----------------------------|----------------------------------|
| Pesatura              | Si, obbligatoria            | No, solo passaggio               |
| Tabella InOut         | Si, collegata               | No                               |
| Materiale             | Si, registrato              | No                               |
| Soggetto/Vettore      | Si, associati               | Opzionale                        |
| Report PDF            | Si, generato                | No                               |
| Priorita              | Da implementare             | Si, nativa                       |
| Slot                  | Da implementare             | Si, nativo                       |

---

## 4. API da Implementare

### 4.1 API per il Sistema Esterno (Caricamento Accessi)

#### `POST /api/open-to-customer/transit-access`

Endpoint aperto (senza autenticazione completa) per il sistema esterno.

**Request Body:**
```json
{
  "plate": "AB123CD",
  "slot": "08:00-09:00",
  "priority": 3,
  "note": "Mezzo di servizio",
  "source_system_id": "EXT-2024-001"
}
```

**Response:**
```json
{
  "id": 1,
  "plate": "AB123CD",
  "slot": "08:00-09:00",
  "priority": 3,
  "status": "WAITING",
  "gate": null,
  "date_created": "2024-01-15T08:00:00"
}
```

#### `POST /api/open-to-customer/access`

Per creare accessi con pesatura dal sistema esterno (come quelli attuali, ma con priorita e slot).

**Request Body:**
```json
{
  "plate": "AB123CD",
  "slot": "08:00-09:00",
  "priority": 2,
  "idSubject": 1,
  "idMaterial": 3,
  "number_in_out": 1
}
```

### 4.2 API di Gestione Transit Access

| Metodo   | Endpoint                                | Descrizione                          |
|----------|-----------------------------------------|--------------------------------------|
| `GET`    | `/api/anagrafic/transit-access/list`    | Lista transiti con filtri            |
| `POST`   | `/api/anagrafic/transit-access`         | Crea nuovo transito                  |
| `PATCH`  | `/api/anagrafic/transit-access/{id}`    | Aggiorna transito                    |
| `DELETE` | `/api/anagrafic/transit-access/{id}`    | Elimina transito                     |
| `GET`    | `/api/anagrafic/transit-access/close/{id}` | Chiudi transito (segna uscita)    |

---

## 5. Automatismo Apertura Sbarre

### Configurazione nel `config.json`

Nuova sezione nella configurazione del weigher per mappare le sbarre ai rele:

```json
{
  "app_api": {
    "weighers": {
      "0": {
        "nodes": {
          "P1": {
            "gate_control": {
              "enabled": true,
              "gate_1": {
                "rele": "2",
                "description": "Sbarra 1 - Priorita Alta",
                "min_priority": 2
              },
              "gate_2": {
                "rele": "3",
                "description": "Sbarra 2 - Priorita Bassa",
                "min_priority": 1
              },
              "auto_open_delay_seconds": 2,
              "auto_close_on_weight": true
            }
          }
        }
      }
    }
  }
}
```

### Flusso dell'Automatismo

```
┌─────────────────────────────────────────────────────┐
│           CALLBACK REALTIME (ciclo continuo)         │
│                                                      │
│  1. Leggi peso dalla Pesa 1                          │
│  2. SE peso < min_weight (pesa vuota):               │
│     a. Cerca prossimo accesso/transito WAITING       │
│        ordinato per priorita DESC, data ASC          │
│     b. SE trovato:                                   │
│        - Determina sbarra da aprire                  │
│        - Apri rele corrispondente                    │
│        - Mostra targa su pannello                    │
│        - Attiva sirena                               │
│  3. SE peso >= min_weight (veicolo sulla pesa):      │
│     a. Chiudi rele sbarra                            │
│     b. SE e un transit_access:                       │
│        - NON avviare pesatura                        │
│        - Aggiorna stato a TRANSITED                  │
│        - Registra date_in                            │
│     c. SE e un access normale:                       │
│        - Procedi con pesatura automatica             │
│        - Aggiorna stato a ENTERED                    │
└─────────────────────────────────────────────────────┘
```

---

## 6. Integrazione con il Sistema Esistente

### Modifiche al Callback Realtime

Il `Callback_Realtime` in `callback_weigher.py` deve essere esteso per:

1. **Monitorare la pesa vuota**: Quando il peso scende sotto `min_weight`, cercare il prossimo accesso/transito in coda
2. **Aprire la sbarra corretta**: Utilizzando i rele configurati per gate_1 o gate_2
3. **Distinguere transiti da pesature**: Quando il veicolo sale sulla pesa, verificare se e un `transit_access` (solo passaggio) o un `access` (pesatura completa)

### Modifiche al Callback Weighing

Il `Callback_Weighing` in `callback_weigher.py` deve:

1. Verificare se l'accesso corrente e un transito prima di avviare la pesatura
2. Se e un transito, saltare la pesatura e aggiornare solo lo stato

### Nuovi Componenti

- **Modello `TransitAccess`** in `md_database.py`
- **Router `transit_access.py`** in `applications/router/anagrafic/`
- **Funzioni DB** per CRUD transit access in `modules/md_database/functions/`
- **Endpoint open-to-customer** per ricezione dati dal sistema esterno

---

## 7. Diagramma di Sequenza Completo

```
Sistema Esterno          Nostro Software            Pesa 1          Sbarra 1/2       Pesa 2
     │                        │                       │                 │               │
     │  POST /access          │                       │                 │               │
     │  (targa, slot,         │                       │                 │               │
     │   priorita)            │                       │                 │               │
     │───────────────────────►│                       │                 │               │
     │                        │  Salva accesso        │                 │               │
     │                        │  stato=WAITING        │                 │               │
     │                        │                       │                 │               │
     │                        │  [Realtime Loop]      │                 │               │
     │                        │◄──────────────────────│ peso < min      │               │
     │                        │                       │                 │               │
     │                        │  Cerca WAITING        │                 │               │
     │                        │  con priorita max     │                 │               │
     │                        │                       │                 │               │
     │                        │  Apri sbarra ─────────────────────────►│               │
     │                        │  (in base a priorita) │                 │ APERTA        │
     │                        │                       │                 │               │
     │                        │  Mostra targa pannello│                 │               │
     │                        │  Attiva sirena        │                 │               │
     │                        │                       │                 │               │
     │                  [Veicolo sale sulla pesa]      │                 │               │
     │                        │◄──────────────────────│ peso >= min     │               │
     │                        │                       │                 │               │
     │                        │  Chiudi sbarra ───────────────────────►│               │
     │                        │                       │                 │ CHIUSA        │
     │                        │                       │                 │               │
     │                        │  SE transit_access:   │                 │               │
     │                        │    stato=TRANSITED    │                 │               │
     │                        │    FINE               │                 │               │
     │                        │                       │                 │               │
     │                        │  SE access normale:   │                 │               │
     │                        │    stato=ENTERED      │                 │               │
     │                        │                       │                 │               │
     │                        │  [Veicolo va a Pesa 2]│                 │               │
     │                        │                       │                 │               │
     │                        │  Identificazione ─────────────────────────────────────►│
     │                        │  (telecamera/badge)   │                 │               │
     │                        │                       │                 │               │
     │                        │◄──────────────────────────────────────────────────────│
     │                        │  Pesatura automatica  │                 │               │
     │                        │  stato=CLOSED         │                 │               │
     │                        │                       │                 │               │
```

---

## 8. Casi d'Uso

### Caso 1: Veicolo con Priorita Alta per Pesatura
1. Sistema esterno invia: `{plate: "AB123", priority: 3, type: "access"}`
2. Software crea accesso con stato WAITING
3. Pesa 1 vuota → apre Sbarra 1 (priorita alta)
4. Veicolo sale su Pesa 1 → chiude Sbarra 1, stato ENTERED
5. Veicolo va a Pesa 2 → pesatura automatica → stato CLOSED

### Caso 2: Veicolo con Priorita Bassa per Pesatura
1. Sistema esterno invia: `{plate: "CD456", priority: 1, type: "access"}`
2. Software crea accesso con stato WAITING
3. Pesa 1 vuota → apre Sbarra 2 (priorita bassa)
4. Resto del flusso identico al Caso 1

### Caso 3: Veicolo Solo Transito (Senza Pesata)
1. Sistema esterno invia: `{plate: "EF789", priority: 2, type: "transit"}`
2. Software crea record in `transit_access` con stato WAITING
3. Pesa 1 vuota → apre sbarra in base a priorita
4. Veicolo transita → stato TRANSITED, registra date_in
5. **Nessuna pesatura viene avviata**
6. Veicolo esce → registra date_out

### Caso 4: Coda con Priorita Miste
1. Coda: `[{plate: "A", priority: 1}, {plate: "B", priority: 3}, {plate: "C", priority: 2}]`
2. Pesa vuota → viene servito prima "B" (priorita 3) → Sbarra 1
3. Pesa vuota di nuovo → viene servito "C" (priorita 2) → Sbarra 1
4. Pesa vuota di nuovo → viene servito "A" (priorita 1) → Sbarra 2

---

## 9. Note Tecniche

- I **rele** delle sbarre sono gestiti tramite il modulo `md_weigher` con i comandi `OPENRELE` / `CLOSERELE`
- Il **pannello** mostra la targa del veicolo chiamato tramite gli adapter configurati (TCP, HTTP, ecc.)
- La **sirena** viene attivata per segnalare l'apertura della sbarra
- Il sistema supporta le modalita `AUTOMATIC`, `SEMIAUTOMATIC` e `MANUALLY` gia esistenti
- La priorita e gestita come Integer: valori piu alti = priorita maggiore
- In caso di parita di priorita, viene servito l'accesso piu vecchio (FIFO per `date_created ASC`)
