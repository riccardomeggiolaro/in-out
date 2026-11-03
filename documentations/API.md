# Documentazione API – In-Out

Sistema di gestione pesate e accessi. Tutte le richieste hanno base URL `http://<host>:<port>`.

---

## Autenticazione

La quasi totalità degli endpoint richiede un token JWT nell'header HTTP:

```
Authorization: Bearer <token>
```

Il token si ottiene tramite il login. Gli unici endpoint pubblici (senza token) sono:
- `POST /api/auth/login`
- `POST /api/command-weigher/weighing/auto`

---

## 1. Autenticazione

### Login
```
POST /api/auth/login
```
**Body:**
```json
{
  "username": "string",
  "password": "string"
}
```
**Risposta:**
```json
{
  "access_token": "string"
}
```

---

### Profilo utente corrente
```
GET /api/auth/me
```
Restituisce le informazioni dell'utente autenticato.

### Aggiorna profilo
```
PATCH /api/auth/me
```
**Body (tutti i campi opzionali):**
```json
{
  "password": "string",
  "description": "string"
}
```

---

## 2. Anagrafica

Le entità anagrafiche condividono la stessa struttura di endpoint. I prefissi disponibili sono:

| Prefisso | Entità |
|----------|--------|
| `/api/anagrafic/subject` | Soggetti (clienti/fornitori) |
| `/api/anagrafic/vehicle` | Veicoli |
| `/api/anagrafic/driver` | Autisti |
| `/api/anagrafic/vector` | Vettori |
| `/api/anagrafic/material` | Materiali |
| `/api/anagrafic/operator` | Operatori |

### Lista
```
GET /{prefisso}/list
```
**Query parameters:**
| Parametro | Tipo | Descrizione |
|-----------|------|-------------|
| `limit` | int | Numero massimo di risultati |
| `offset` | int | Offset per paginazione |
| `order_by` | string | Campo su cui ordinare |
| `order_direction` | string | `asc` o `desc` |

**Risposta:**
```json
{
  "data": [...],
  "total_rows": 100
}
```

### Crea
```
POST /{prefisso}
```
Richiede permessi di scrittura.

#### Soggetto (`/api/anagrafic/subject`)
```json
{
  "social_reason": "Ragione Sociale Srl",
  "telephone": "0123456789",
  "cfpiva": "12345678901"
}
```

#### Veicolo (`/api/anagrafic/vehicle`)
```json
{
  "plate": "AB123CD",
  "description": "Camion rosso",
  "tare": 5000
}
```
> `tare` è in kg e deve essere > 0.

#### Autista / Vettore / Operatore
```json
{
  "social_reason": "Nome Cognome",
  "telephone": "0123456789",
  "cfpiva": "XXXXXX"
}
```

#### Materiale
```json
{
  "description": "Ghiaia"
}
```

### Modifica
```
PATCH /{prefisso}/{id}
```
Richiede permessi di scrittura. Stessa struttura del body di creazione, tutti i campi opzionali.

### Elimina
```
DELETE /{prefisso}/{id}
```
Richiede permessi di scrittura.

### Elimina tutti
```
DELETE /{prefisso}
```
Richiede permessi di scrittura.

### Import massivo da file
```
POST /{prefisso}/upload-file
```
Accetta file CSV o Excel (multipart/form-data).

---

## 3. Prenotazioni / Accessi

Base: `/api/anagrafic/access`

### Lista accessi
```
GET /api/anagrafic/access/list
```
**Query parameters:**

| Parametro | Tipo | Descrizione |
|-----------|------|-------------|
| `limit` | int | Numero massimo di risultati |
| `offset` | int | Offset per paginazione |
| `status` | string | `NOT_CLOSED` per filtrare solo quelli aperti |
| `fromDate` | datetime | Data di inizio (ISO 8601) |
| `toDate` | datetime | Data di fine (ISO 8601, l'ora viene portata a 23:59:59) |
| `excludeTestWeighing` | bool | Esclude le pesate di test |
| `permanent` | bool | Filtra solo accessi permanenti |
| `transits` | bool | Filtra solo transiti |
| `excludeManuallyAccess` | bool | Esclude gli accessi manuali |

**Risposta:**
```json
{
  "data": [...],
  "total_rows": 50,
  "buffer": []
}
```

### Crea accesso / prenotazione
```
POST /api/anagrafic/access
```
Richiede permessi di scrittura. La **targa è obbligatoria** (tramite `vehicle.plate` o `vehicle.id`).

**Body:**
```json
{
  "typeSubject": "CUSTOMER",
  "subject": {
    "id": 1,
    "social_reason": "Cliente Srl",
    "telephone": "0123456789",
    "cfpiva": "12345678901"
  },
  "vehicle": {
    "id": null,
    "plate": "AB123CD",
    "description": "Camion",
    "tare": 5000
  },
  "vector": {
    "id": null,
    "social_reason": "Vettore Srl"
  },
  "driver": {
    "id": null,
    "social_reason": "Mario Rossi"
  },
  "material": {
    "id": null,
    "description": "Ghiaia"
  },
  "number_in_out": null,
  "note": "Note libere",
  "document_reference": "DDT-001",
  "type": "RESERVATION",
  "permanent": false,
  "hidden": false,
  "mode": "STANDARD"
}
```

**Valori ammessi:**

| Campo | Valori |
|-------|--------|
| `typeSubject` | `CUSTOMER`, `SUPPLIER` |
| `type` | `RESERVATION`, `MANUALLY`, `TEST` |
| `mode` | `STANDARD`, `TRANSIT` |

> Per i campi anagrafici (subject, vehicle, ecc.) si può passare solo l'`id` di un record esistente, oppure i dati completi per creare un nuovo record al volo. Usare `id: null` o `id: -1` per non fare riferimento a un record esistente.

### Modifica accesso
```
PATCH /api/anagrafic/access/{id}
```
Richiede permessi di scrittura e che il record sia stato bloccato in precedenza (vedi sezione Lock).

**Query parameters opzionali:**
- `idInOut`: id di una pesata specifica da aggiornare.

**Body:** stessa struttura di `AddAccessDTO` con tutti i campi opzionali, in più:
```json
{
  "operator1": { "id": 1 },
  "operator2": { "id": 2 },
  "permanent": false,
  "close": false
}
```

### Chiudi accesso
```
GET /api/anagrafic/access/close/{id}
```
Richiede permessi di scrittura e che il record sia bloccato. Marca l'accesso come `CLOSED`. Fallisce se:
- L'accesso è già chiuso
- Non ha pesate associate
- L'ultima pesata è incompleta (manca il peso 2)

### Elimina accesso
```
DELETE /api/anagrafic/access/{id}
```
Richiede permessi di scrittura e che il record sia bloccato. Fallisce se l'accesso ha pesate associate.

### Elimina ultima pesata di un accesso
```
DELETE /api/anagrafic/access/last-weighing/{id}
```
Richiede permessi di scrittura e che il record sia bloccato.

**Query parameters:**
- `deleteAccessIfislastInOut` (bool, default `true`): se l'accesso non ha più pesate e non è di tipo `RESERVATION`, viene eliminato automaticamente.

### Chiama accesso (pannello/sirena)
```
GET /api/anagrafic/access/call/{id}
```
Invia la targa al pannello esterno e attiva la sirena. Il record deve essere bloccato con tipo `CALL`.

### Annulla chiamata
```
GET /api/anagrafic/access/cancel-call/{id}
```
Rimuove la targa dal pannello. Il record deve essere bloccato con tipo `CANCEL_CALL`.

---

## 4. Pesate (In-Out)

### Lista pesate complete (in-out)
```
GET /api/anagrafic/access/in-out/list
```
**Query parameters:**

| Parametro | Tipo | Descrizione |
|-----------|------|-------------|
| `limit` | int | Numero massimo di risultati |
| `offset` | int | Offset |
| `fromDate` | datetime | Data inizio |
| `toDate` | datetime | Data fine |
| `excludeTestWeighing` | bool | Esclude pesate di test |
| `onlyInOutWithWeight2` | bool | Solo pesate con peso 2 (complete) |
| `onlyInOutWithoutWeight2` | bool | Solo pesate senza peso 2 (incomplete) |

**Risposta:**
```json
{
  "data": [...],
  "total_rows": 200,
  "buffer": []
}
```

### Lista pesate singole (bilance)
```
GET /api/anagrafic/access/weighing/list
```
**Query parameters:**

| Parametro | Tipo | Descrizione |
|-----------|------|-------------|
| `weigher_name` | string | Nome della bilancia |
| `limit` | int | Numero massimo |
| `offset` | int | Offset |
| `fromDate` | datetime | Data inizio |
| `toDate` | datetime | Data fine |

### Scarica PDF di una pesata
```
GET /api/anagrafic/access/in-out/pdf/{id}
```
Restituisce il PDF della pesata come file scaricabile (`application/pdf`).

### Stampa ultima pesata
```
GET /api/anagrafic/access/in-out/print-last
```
**Query parameters:**
- `instance_name`: nome dell'istanza della pesa
- `weigher_name`: nome della bilancia

### Export XLSX
```
GET /api/anagrafic/access/export/xlsx
```
Scarica le pesate in formato Excel. Accetta gli stessi parametri di `/in-out/list` più:

| Parametro | Tipo | Descrizione |
|-----------|------|-------------|
| `filterDateAccess` | bool | Filtra per data dell'accesso anziché della pesata |
| `access.status` | string | `NOT_CLOSED` per filtrare aperti |
| `access.fromDate` | datetime | Alternativa a `fromDate` |
| `access.toDate` | datetime | Alternativa a `toDate` |

### Export PDF
```
GET /api/anagrafic/access/export/pdf
```
Stessa logica dell'export XLSX ma in formato PDF (orizzontale A4).

---

## 5. Terminale Pesate

Base: `/api/anagrafic/weighing-terminal`

### Lista
```
GET /api/anagrafic/weighing-terminal/list
```

### Export XLSX
```
GET /api/anagrafic/weighing-terminal/export/xlsx
```

### Export PDF
```
GET /api/anagrafic/weighing-terminal/export/pdf
```

### Elimina
```
DELETE /api/anagrafic/weighing-terminal/{id}
```
Richiede permessi di scrittura.

---

## 6. Comandi alla Pesa

Base: `/api/command-weigher`

Tutti gli endpoint (tranne `/weighing/auto`) richiedono autenticazione e i parametri di istanza/bilancia.

**Parametri comuni (query string):**
- `instance_name`: nome dell'istanza
- `weigher_name`: nome della bilancia

### Avvia modalità realtime
```
GET /api/command-weigher/realtime
```
Avvia la modalità di lettura continua del peso.

### Avvia diagnostica
```
GET /api/command-weigher/diagnostic
```

### Ferma tutti i comandi
```
GET /api/command-weigher/stop-all-command
```

### Esegui tara
```
GET /api/command-weigher/tare
```

### Tara preset
```
GET /api/command-weigher/tare/preset
```

### Zero
```
GET /api/command-weigher/zero
```
Azzera la pesa.

### Rele
```
GET /api/command-weigher/rele
```
Controlla il relè della pesa.

### Stampa generica
```
GET /api/command-weigher/print
```

### Peso 1 – Entrata
```
POST /api/command-weigher/in
```
Registra il primo peso (entrata). Il peso corrente sulla pesa deve essere stabile.

**Body:**
```json
{
  "typeSubject": "CUSTOMER",
  "subject": { "id": 1 },
  "vehicle": { "plate": "AB123CD" },
  "vector": {},
  "driver": {},
  "material": { "description": "Ghiaia" },
  "operator": { "id": 2 },
  "note": "Note",
  "document_reference": "DDT-001"
}
```

### Peso 2 – Uscita
```
POST /api/command-weigher/out
```
Stessa struttura di `/in`. Registra il secondo peso (uscita) completando la pesata.

### Pesata senza PID
```
POST /api/command-weigher/weighing-without-pid
```
Registra una pesata usando il peso attuale della bilancia senza generare un PID di stampa.

**Body:** stessa struttura di `/in`.

**Query parameters aggiuntivi:**
- `tare` (int): tara manuale da applicare (in kg)

### Pesata automatica tramite identificativo (pubblico)
```
POST /api/command-weigher/weighing/auto
```
Endpoint **senza autenticazione**. Permette l'esecuzione automatica di una pesata tramite un identificativo (es. badge/RFID).

**Body:**
```json
{
  "identify": "string",
  "rele": "nome_rele",
  "timeout": 3
}
```

| Campo | Note |
|-------|------|
| `identify` | Stringa identificativa (es. codice badge) |
| `rele` | Nome del relè da attivare (opzionale) |
| `timeout` | Secondi di attesa, max 5 (opzionale) |

---

## 7. Dati correnti della pesa

Base: `/api/data`

### Leggi dati correnti
```
GET /api/data
```
**Query parameters:** `instance_name`, `weigher_name`

Restituisce i dati attualmente caricati sulla pesa (soggetto, veicolo, materiale, ecc. selezionati).

### Aggiorna dati correnti
```
PATCH /api/data
```
**Query parameters:** `instance_name`, `weigher_name`

**Body:**
```json
{
  "data_in_execution": {
    "typeSubject": "CUSTOMER",
    "subject": { "id": 1 },
    "vehicle": { "plate": "AB123CD" },
    "vector": {},
    "driver": {},
    "material": { "description": "Ghiaia" },
    "operator": {},
    "note": null,
    "document_reference": null
  },
  "id_selected": {
    "id": 5
  }
}
```

> `data_in_execution` accetta **solo uno** dei campi anagrafici per volta.

### Cancella dati correnti
```
DELETE /api/data
```
**Query parameters:** `instance_name`, `weigher_name`

---

## 8. WebSocket – Aggiornamenti real-time

### Dati anagrafici
```
WS /api/anagrafic/{anagrafic}?token=<jwt>
```
Dove `{anagrafic}` può essere: `access`, `subject`, `vehicle`, `driver`, `vector`, `material`, `operator`.

Il token JWT va passato come query parameter `token`.

**Messaggi inviabili al server (lock/unlock record):**
```json
{
  "action": "lock",
  "anagrafic": "access",
  "idRecord": 42,
  "type": "UPDATE",
  "idRequest": 1
}
```

| Campo `action` | Descrizione |
|----------------|-------------|
| `lock` | Blocca il record per operazioni esclusive |
| `unlock` | Sblocca il record |

| Campo `type` | Descrizione |
|--------------|-------------|
| `UPDATE` | Blocco per modifica |
| `DELETE` | Blocco per eliminazione |
| `CALL` | Blocco per chiamata pannello |
| `CANCEL_CALL` | Blocco per annullamento chiamata |

**Messaggi ricevuti dal server:** notifiche di aggiunta, modifica o eliminazione di record.

### Dati bilancia in realtime
```
WS /api/command-weigher/realtime?token=<jwt>&instance_name=...&weigher_name=...
```
Stream continuo con peso lordo, netto, tara, stato bilancia.

### Diagnostica bilancia
```
WS /api/command-weigher/diagnostic?token=<jwt>&instance_name=...&weigher_name=...
```

---

## Note generali

- Le date vanno passate in formato ISO 8601 (es. `2025-01-15T00:00:00`).
- La paginazione usa `limit` e `offset`. Se non specificati, vengono restituiti tutti i record.
- Per modificare o eliminare un accesso è necessario prima bloccarlo via WebSocket con l'azione `lock` e il tipo appropriato (`UPDATE`, `DELETE`, ecc.). Il blocco viene rilasciato automaticamente al termine dell'operazione.
- Gli endpoint che restituiscono file (PDF, XLSX) usano `Content-Disposition: attachment` e avviano il download diretto.
