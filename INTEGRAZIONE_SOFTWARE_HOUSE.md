# Guida all'integrazione per Software House

Questo documento descrive come i sistemi gestionali di terze parti possono integrarsi con il sistema di pesatura per raccogliere, importare e sincronizzare i dati di pesatura.

Sono disponibili tre approcci principali:

1. **API REST HTTP** — integrazione in tempo reale via chiamate HTTP
2. **File CSV** — raccolta dati tramite file generati automaticamente dopo ogni pesatura
3. **Cartella remota sincronizzata** — i file (PDF e CSV) vengono copiati automaticamente su una share di rete remota via Samba/CIFS, FTP o SFTP

---

## Autenticazione

Tutte le API (tranne quelle pubbliche indicate esplicitamente) richiedono un token JWT nell'header HTTP.

```
Authorization: Bearer <token>
```

Il token si ottiene tramite il login:

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "utente",
  "password": "password"
}
```

Risposta:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## 1. Integrazione via API REST HTTP

### 1.1 Recupero lista pesature (endpoint pubblico)

Endpoint disponibile senza autenticazione (o con permessi base), utile per scaricare periodicamente i dati:

```http
GET /api/in-out/list
```

Parametri query opzionali:

| Parametro             | Tipo      | Descrizione                                             |
|-----------------------|-----------|---------------------------------------------------------|
| `limit`               | int       | Numero massimo di record restituiti                     |
| `offset`              | int       | Offset per la paginazione                               |
| `fromDate`            | datetime  | Data di inizio (formato ISO 8601, es. `2024-01-01T00:00:00`) |
| `toDate`              | datetime  | Data di fine (include l'intera giornata fino alle 23:59:59) |
| `onlyInOutWithWeight2`| bool      | Se `true`, restituisce solo pesature complete (entrata + uscita) |
| qualsiasi campo       | string    | Filtra per qualunque attributo dell'entità (es. `plate`, `material_description`) |

Esempio:

```http
GET /api/in-out/list?limit=50&offset=0&fromDate=2024-01-01T00:00:00&toDate=2024-01-31T00:00:00&onlyInOutWithWeight2=true
```

Risposta:

```json
{
  "data": [
    {
      "id": 123,
      "typeSubject": "CUSTOMER",
      "subject": { "id": 1, "social_reason": "Azienda ABC", "telephone": "0123456789", "cfpiva": "IT12345678901" },
      "vector": { "id": 2, "social_reason": "Trasporti SRL", "telephone": null, "cfpiva": null },
      "driver": { "id": 3, "social_reason": "Mario Rossi", "telephone": null },
      "vehicle": { "id": 4, "plate": "AB123CD", "description": "Camion", "tare": 8000 },
      "material": { "id": 5, "description": "Rottame ferroso" },
      "note": null,
      "document_reference": "DDT-2024-001",
      "weight1": {
        "date": "2024-01-15T09:30:00",
        "pid": "0001",
        "weight": 28500
      },
      "weight2": {
        "date": "2024-01-15T11:15:00",
        "pid": "0002",
        "weight": 8000
      },
      "net_weight": 20500
    }
  ],
  "total_rows": 1,
  "buffer": ""
}
```

> I pesi sono espressi in **kg** come interi o float, a seconda della configurazione della pesa.

---

### 1.2 Dati in tempo reale via WebSocket

Per ricevere i dati della pesa in tempo reale (peso lordo, netto, tara, stato):

```
WS /api/weigher/command-weigher/realtime?instance_name=0&weigher_name=N1
```

Messaggio ricevuto (broadcast ad ogni variazione):

```json
{
  "gross_weight": "1250",
  "net_weight": "0",
  "tare": "0",
  "status": "ST",
  "potential_net_weight": null,
  "over_max_theshold": false
}
```

Valori del campo `status`:

| Valore | Significato         |
|--------|---------------------|
| `ST`   | Peso stabile        |
| `MO`   | Peso in movimento   |
| `OL`   | Sovraccarico        |
| `ER`   | Errore              |

Per mantenere la connessione attiva, il client deve inviare ping periodici:

```json
{ "type": "ping" }
```

Il server risponde con:

```json
{ "type": "pong" }
```

---

### 1.3 Impostare i dati prima di una pesatura

Prima di eseguire una pesatura, il gestionale può pre-compilare i dati anagrafici (veicolo, soggetto, materiale, ecc.):

```http
PATCH /api/weigher/data?instance_name=0&weigher_name=N1
Content-Type: application/json
Authorization: Bearer <token>

{
  "data_in_execution": {
    "typeSubject": "CUSTOMER",
    "subject": { "id": 1 },
    "vehicle": { "plate": "AB123CD" },
    "material": { "id": 5 },
    "document_reference": "DDT-2024-001",
    "note": "Nota operativa"
  },
  "id_selected": { "id": null }
}
```

Parametri query aggiuntivi:

| Parametro                | Tipo | Default | Descrizione                                                           |
|--------------------------|------|---------|-----------------------------------------------------------------------|
| `auto_select`            | bool | `false` | Cerca automaticamente l'anagrafica per nome/targa se non ha l'ID     |
| `keep_selected`          | bool | `false` | Mantiene l'accesso già selezionato e aggiorna solo i dati             |
| `set_preset_tare_if_exists` | bool | `true` | Imposta automaticamente la tara preset del veicolo sulla pesa      |

Esempio con `auto_select=true` (ricerca veicolo per targa):

```http
PATCH /api/weigher/data?instance_name=0&weigher_name=N1&auto_select=true
Content-Type: application/json

{
  "data_in_execution": {
    "vehicle": { "plate": "AB123CD" },
    "material": { "description": "Rottame ferroso" }
  },
  "id_selected": { "id": null }
}
```

---

### 1.4 Avviare una pesatura

**Pesatura entrata (Weight 1):**

```http
POST /api/weigher/command-weigher/in?instance_name=0&weigher_name=N1
Authorization: Bearer <token>
```

**Pesatura uscita (Weight 2):**

```http
POST /api/weigher/command-weigher/out?instance_name=0&weigher_name=N1
Authorization: Bearer <token>
```

**Pesatura automatica tramite codice identificativo (badge, RFID, targa):**

```http
POST /api/weigher/command-weigher/weighing/auto?instance_name=0&weigher_name=N1
Content-Type: application/json
Authorization: Bearer <token>

{
  "identify": "AB123CD",
  "rele": null,
  "timeout": null
}
```

**Pesatura singola senza PID (peso manuale con tara preset):**

```http
POST /api/weigher/command-weigher/weighing-without-pid?instance_name=0&weigher_name=N1&tare=8000
Content-Type: application/json
Authorization: Bearer <token>

{
  "typeSubject": "CUSTOMER",
  "subject": { "id": 1 },
  "material": { "id": 5 }
}
```

---

### 1.5 Altri comandi pesa

| Endpoint                                                                | Metodo | Descrizione               |
|-------------------------------------------------------------------------|--------|---------------------------|
| `/api/weigher/command-weigher/tare?instance_name=0&weigher_name=N1`    | GET    | Esegue tara               |
| `/api/weigher/command-weigher/tare/preset?instance_name=0&weigher_name=N1&tare=8000` | GET | Imposta tara preset |
| `/api/weigher/command-weigher/zero?instance_name=0&weigher_name=N1`   | GET    | Azzera il peso            |
| `/api/weigher/command-weigher/stop-all-command?instance_name=0&weigher_name=N1` | GET | Ferma tutti i comandi |
| `/api/weigher/command-weigher/realtime?instance_name=0&weigher_name=N1` | GET   | Avvia modalità realtime   |

---

### 1.6 Parametri `instance_name` e `weigher_name`

Ogni pesa fisica è identificata da una coppia:

- `instance_name`: identificatore numerico dell'istanza di connessione (es. `"0"`)
- `weigher_name`: nome del nodo bilancia all'interno dell'istanza (es. `"N1"`)

Per ottenere le istanze configurate:

```http
GET /api/weigher/config-weigher/all/instance
Authorization: Bearer <token>
```

---

## 2. Esportazione dati tramite file CSV

Dopo ogni pesatura completata il sistema può generare automaticamente un file CSV nella directory configurata.

### 2.1 Configurazione del percorso CSV

```http
PATCH /api/weigher/config-weigher/configuration/path-csv
Content-Type: application/json
Authorization: Bearer <token>

{
  "path": "/var/exports/pesatura/csv"
}
```

Il percorso deve essere un path assoluto, accessibile in lettura/scrittura dal server.

### 2.2 Abilitare la generazione CSV per tipo di evento

La generazione CSV è configurabile separatamente per: entrata (`in`), uscita (`out`), tara (`tare`), generica (`generic`).

La configurazione si trova in `app_api.weighers.<instance_name>.nodes.<weigher_name>.events.weighing.csv`:

```json
{
  "csv": {
    "in": false,
    "out": true,
    "tare": false,
    "generic": false
  }
}
```

### 2.3 Formato del file CSV

Il file viene nominato nel formato: `<weigher_name>_<pid_entrata>_<pid_uscita>.csv`

Esempio: `N1_0001_0002.csv`

Il file contiene **una sola riga** per pesatura, con campi separati da **punto e virgola (`;`)** e senza intestazione.

Ordine e significato delle colonne:

| N. | Campo                    | Esempio              |
|----|--------------------------|----------------------|
| 1  | Tipo soggetto            | `CUSTOMER`           |
| 2  | ID soggetto              | `1`                  |
| 3  | Ragione sociale soggetto | `Azienda ABC`        |
| 4  | Telefono soggetto        | `0123456789`         |
| 5  | CF/P.IVA soggetto        | `IT12345678901`      |
| 6  | ID vettore               | `2`                  |
| 7  | Ragione sociale vettore  | `Trasporti SRL`      |
| 8  | Telefono vettore         | ` `                  |
| 9  | CF/P.IVA vettore         | ` `                  |
| 10 | ID autista               | `3`                  |
| 11 | Ragione sociale autista  | `Mario Rossi`        |
| 12 | Telefono autista         | ` `                  |
| 13 | ID veicolo               | `4`                  |
| 14 | Targa veicolo            | `AB123CD`            |
| 15 | Descrizione veicolo      | `Camion`             |
| 16 | ID materiale             | `5`                  |
| 17 | Descrizione materiale    | `Rottame ferroso`    |
| 18 | Note                     | ` `                  |
| 19 | Riferimento documento    | `DDT-2024-001`       |
| 20 | Data/ora peso 1          | `15/01/2024 09:30`   |
| 21 | PID peso 1               | `0001`               |
| 22 | Peso 1 (kg)              | `28500`              |
| 23 | Data/ora peso 2          | `15/01/2024 11:15`   |
| 24 | PID peso 2               | `0002`               |
| 25 | Peso 2 (kg)              | `8000`               |
| 26 | Peso netto (kg)          | `20500`              |

Esempio di riga completa:

```
CUSTOMER;1;Azienda ABC;0123456789;IT12345678901;2;Trasporti SRL;;;3;Mario Rossi;;4;AB123CD;Camion;5;Rottame ferroso;;DDT-2024-001;15/01/2024 09:30;0001;28500;15/01/2024 11:15;0002;8000;20500
```

> I campi vuoti compaiono come stringa vuota tra due separatori `;;`.

### 2.4 Monitoraggio della directory

Il gestionale può monitorare la directory configurata e leggere i nuovi file CSV non appena vengono creati. Il sistema di pesatura li genera immediatamente dopo il completamento della pesatura.

---

## 3. Sincronizzazione con cartella remota

Il sistema può copiare automaticamente i file prodotti (PDF e CSV) su una cartella di rete remota non appena vengono creati in locale. Supporta tre protocolli.

### 3.1 Protocolli supportati

| Protocollo  | Porta default | Note                                          |
|-------------|---------------|-----------------------------------------------|
| `samba`     | 445           | Samba/CIFS — condivisione di rete Windows/Linux |
| `ftp`       | 21            | FTP con supporto TLS (FTPS) come fallback     |
| `sftp`      | 22            | SFTP tramite SSH (usa libreria Paramiko)       |

### 3.2 Configurazione della cartella remota

```http
POST /api/sync-folder
Content-Type: application/json
Authorization: Bearer <token>

{
  "ip": "192.168.1.100",
  "domain": "WORKGROUP",
  "share_name": "pesature",
  "sub_path": "2024/csv",
  "username": "utente",
  "password": "password",
  "protocol": "samba",
  "port": 445
}
```

Campi del body:

| Campo        | Tipo   | Obbligatorio | Descrizione                                         |
|--------------|--------|-------------|------------------------------------------------------|
| `ip`         | string | Sì          | Indirizzo IP del server remoto                       |
| `domain`     | string | No          | Dominio Windows (solo Samba, es. `WORKGROUP`)        |
| `share_name` | string | Sì          | Nome della share (es. `pesature`, `dati`)            |
| `sub_path`   | string | No          | Sottocartella all'interno della share                |
| `username`   | string | Sì          | Utente con accesso alla share                        |
| `password`   | string | Sì          | Password dell'utente                                 |
| `protocol`   | string | Sì          | `samba`, `ftp` o `sftp`                              |
| `port`       | int    | No          | Porta custom (default automatico per protocollo)     |

### 3.3 Test della connessione

```http
GET /api/sync-folder/test
Authorization: Bearer <token>
```

Risposta:

```json
{
  "mounted": true,
  "remote_path": "//192.168.1.100/pesature",
  "status": "connected"
}
```

### 3.4 Lettura configurazione attiva

```http
GET /api/sync-folder
Authorization: Bearer <token>
```

### 3.5 Rimozione configurazione

```http
DELETE /api/sync-folder
Authorization: Bearer <token>
```

### 3.6 Comportamento della sincronizzazione

- All'avvio del sistema, se è configurata una cartella remota, viene creata automaticamente la connessione.
- I file presenti nella directory locale vengono accodati e copiati uno per uno sul server remoto.
- I file `.db` e `.db-journal` sono esclusi dalla sincronizzazione.
- Dopo la copia il file locale viene eliminato (solo i file, non le cartelle).
- Se la connessione si interrompe, il sistema tenta automaticamente il riconnessione prima di riprovare la copia.
- I file non ancora copiati rimangono in coda e vengono inviati non appena la connessione è ripristinata.

---

## 4. Configurazione del percorso PDF

Oltre al CSV, è possibile configurare una directory locale dove salvare le copie PDF dei bollettini di pesatura:

```http
PATCH /api/weigher/config-weigher/configuration/path-pdf
Content-Type: application/json
Authorization: Bearer <token>

{
  "path": "/var/exports/pesatura/pdf"
}
```

I PDF vengono nominati con lo stesso schema dei CSV: `<weigher_name>_<pid_entrata>_<pid_uscita>.pdf`

---

## 5. Workflow tipico di integrazione

```
Gestionale                          Sistema di pesatura
    |                                       |
    |-- PATCH /data (dati veicolo) -------> |  Pre-compila dati
    |                                       |
    |<-- WS realtime (peso in movimento) -- |  Monitoraggio in real-time
    |<-- WS realtime (peso stabile ST) ---- |
    |                                       |
    |-- POST /command-weigher/in ---------> |  Avvia acquisizione peso 1
    |<-- WS: { weight_executed: { pid } } - |  Conferma acquisizione
    |                                       |
    |   [veicolo esce e rientra]            |
    |                                       |
    |-- POST /command-weigher/out --------> |  Avvia acquisizione peso 2
    |<-- WS: { weight_executed: { pid } } - |  Conferma + genera CSV/PDF
    |                                       |
    |-- GET /in-out/list (ultima pesatura)  |  Recupero dati definitivi
    |<-- { net_weight: 20500, ... } ------> |
    |                                       |
    |   [oppure legge il CSV dalla dir]     |
    |   [oppure riceve file via Samba/FTP]  |
```

---

## 6. Note tecniche

- Il server espone le API su `http://<host>:<porta>/api/`
- La porta di default è configurabile; verificare con l'installatore del sistema.
- I pesi sono in **chilogrammi** (interi o decimali).
- Le date nei CSV usano il formato `dd/MM/yyyy HH:mm`; nelle risposte JSON usano ISO 8601.
- Il campo `pid` è il numero progressivo assegnato dalla pesa ad ogni pesata; può essere `null` per pesature senza PID (es. pesature manuali).
- Il campo `typeSubject` può essere `CUSTOMER` (cliente) o `SUPPLIER` (fornitore).
- Il campo `net_weight` è `null` nelle pesature incomplete (solo entrata).
