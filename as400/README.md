# Sincronizzazione AS400 → in-out

`as400.py` legge le prenotazioni aperte dall'AS400 (tabella `LIBDAT.CARARRP`)
e le scrive come **prenotazioni** (`access` di tipo `RESERVATION`) nel database
di in-out (`/var/opt/in-out/database.db`).

- È **autonomo**: non importa nulla dal progetto in-out. Usa solo Python,
  `pyodbc` e il modulo standard `sqlite3`.
- Sull'AS400 fa **solo letture** (`SELECT`), nessuna modifica.
- È **rilanciabile**: ogni esecuzione aggiorna le stesse prenotazioni, non crea
  doppioni.
- In produzione gira ogni **5 minuti** tramite un timer systemd.

---

## 1. Flusso dei dati

```
                      ┌──────────────────────────┐
                      │  AS400  LIBDAT.CARARRP   │
                      └────────────┬─────────────┘
                                   │ SELECT (solo prenotazioni aperte)
                                   ▼
                              as400.py
              ┌────────────────────┼─────────────────────────┐
              ▼                    ▼                          ▼
      test_as400.db        sample_as400.db        /var/opt/in-out/database.db
   (copia completa,      (copia ridotta,          (database di in-out:
    tutte le colonne)     12 colonne usate)        subject, vehicle,
                                                   card_registry, access)
```

| File | Cos'è | Chi lo usa |
|---|---|---|
| `database.db` | Database dell'app in-out. Qui finiscono le prenotazioni. | in-out |
| `test_as400.db` | Copia di controllo con **tutte** le colonne lette dall'AS400. | `--source local`, debug |
| `sample_as400.db` | Copia ridotta di `test_as400.db` con le sole 12 colonne usate. Ricreata a ogni esecuzione. | Solo consultazione |

I dati che vanno in `database.db` arrivano **direttamente dall'AS400**, non da
`test_as400.db`. Le due copie servono solo per controllo: se la loro scrittura
fallisce la sincronizzazione continua.

### Modalità di esecuzione

| Comando | Legge da | Scrive copie | Scrive su `database.db` |
|---|---|---|---|
| `python3 as400.py` | AS400 | sì | sì |
| `python3 as400.py --source local` | `test_as400.db` | no | sì |

`--source local` serve per prove senza AS400: usa i dati dell'ultima lettura,
che possono essere vecchi.

---

## 2. Quali righe vengono lette

Solo le prenotazioni aperte (stesso filtro del vecchio VBA):

```sql
SELECT * FROM LIBDAT.CARARRP
WHERE FEGUTS = '' AND FEADCE = '01' AND FEGVTS = ''
  AND FEONDT = 0 AND FEBZTM = 0
  AND FEJSUS IN ('C','S','H')
```

---

## 3. Corrispondenza dei campi

| Campo AS400 | Significato | Dove finisce in in-out |
|---|---|---|
| `FEMRA0` + `FEE8A0` | Anno + progressivo | Badge `AA-PPPPPPP` (es. `26-13766`) → `card_registry.code` e `.number`. È la **chiave** della prenotazione. |
| `FEHBTY` | Nome cliente/fornitore | `subject.social_reason` |
| `FEJSUS` | Carico / Scarico | `access.typeSubject`: `C` → `CUSTOMER` (Cliente), `S`/`H` → `SUPPLIER` (Fornitore) |
| `FEA335` | Targa motrice | `vehicle.plate` (in maiuscolo) |
| `FEHCTY` | Targa rimorchio | `vehicle.description` (solo alla creazione del veicolo) |
| `FERSTS` | Tipo automezzo | Tara standard, vedi §4 |
| `FER3CC` | Tara mezzo | Tara specifica, vedi §4 |
| `FERSCC` | Limite peso | `vehicle.max_threshold` |
| `FEG1TY` | Note merce | `access.note` |
| `FEFMCD` | Riferimento documento (es. codice nazione `ITA`, `BGR`) | `access.document_reference` |
| `FESIDT` + `FEB9TM` | Data e ora prenotazione | `access.date_created` (solo alla creazione) |
| `FER5TS` | Flag stampa peso | Letto ma **non usato** al momento |

---

## 4. Calcolo della tara

1. Se `FER3CC` è maggiore di 0 **e** diverso da 10000 e 15000 → la tara è
   `FER3CC` (es. 15500 kg).
2. Altrimenti la tara si ricava da `FERSTS`:

   | `FERSTS` | Mezzo | Tara |
   |---|---|---|
   | `A` | Autotreno | 15000 kg |
   | `B` | Bilico | 15000 kg |
   | `M` | Motrice | 10000 kg |
   | `C` / vuoto | Collettame | nessuna tara |

La regola vale anche con la targa vuota e con `FERSTS` = `C` o vuoto.

Esempi:

| `FERSTS` | `FER3CC` | Tara |
|---|---|---|
| `B` | 0 | 15000 |
| `B` | 15500 | 15500 |
| `B` | 10000 | 15000 (vince `FERSTS`) |
| `C` | 12000 | 12000 |
| `C` | 0 | nessuna |

La tara determina anche `access.number_in_out` (numero di operazioni di
ingresso/uscita previste per la prenotazione): **2** se c'è una tara, **1** se
non c'è. Viene impostato solo alla creazione della prenotazione.

---

## 5. Come vengono incrociati i dati

Per ogni riga lo script cerca prima se il dato esiste già in in-out e lo crea
solo se manca (lookup-or-create). Tutta l'esecuzione è **un'unica
transazione**: se qualcosa fallisce a metà non viene salvato niente.

### Soggetto (`subject`)
- Cercato per ragione sociale (`FEHBTY`), senza distinguere maiuscole/minuscole.
- Se non esiste viene creato. Se `FEHBTY` è vuoto la prenotazione resta senza
  soggetto.

### Veicolo (`vehicle`)
- **Con targa**: cercato per targa. Se esiste viene riusato; se non esiste
  viene creato con targa, rimorchio (descrizione), tara e limite peso.
- **Senza targa ma con tara**: cercato un veicolo senza targa con **la stessa
  tara**; se non c'è ne viene creato uno nuovo. Quindi ogni tara diversa
  (10000, 15000, 15500, …) ha il suo veicolo "senza targa".
- **Senza targa e senza tara**: la prenotazione resta senza veicolo.
- Su un veicolo già esistente tara e limite peso vengono scritti **solo se
  erano vuoti**: un valore già presente in in-out non viene sovrascritto.

### Badge (`card_registry`)
- Il badge è `anno-progressivo` (es. `26-13766`), cercato per codice o numero.
- Se non esiste viene creato con `code` = `number` = badge.

### Prenotazione (`access`)
La prenotazione è collegata al badge: badge uguale = stessa prenotazione.

| Situazione in in-out | Cosa fa lo script | Conteggio nel log |
|---|---|---|
| Nessun accesso con quel badge | Crea l'accesso: `RESERVATION`, stato `WAITING`, modalità `STANDARD` | inseriti |
| Accesso in stato `WAITING` o `OPEN` | Aggiorna tipo soggetto, soggetto, veicolo, note, riferimento documento | aggiornati |
| Accesso in stato `ENTERED` o `CLOSED` | **Non lo tocca**, per non alterare una pesata in corso o completata | saltati |
| Riga AS400 senza anno o progressivo | Ignorata | saltati |

Le prenotazioni chiuse o cancellate sull'AS400 non vengono rimosse da in-out:
semplicemente non vengono più aggiornate.

> Lo script scrive direttamente nel database: se l'interfaccia di in-out è già
> aperta, le nuove prenotazioni compaiono dopo un aggiornamento della pagina.

---

## 6. Installazione (Debian 13)

Requisito: driver **IBM i Access ODBC Driver** già installato (IBM i Access
Client Solutions). L'installer controlla che ci sia ma non lo installa.

```bash
odbcinst -q -d
```

Deve comparire `[IBM i Access ODBC Driver]`.

Poi, dalla cartella `as400` (ovunque si trovi):

```bash
sudo ./install-debian13.sh
```

L'installer:
1. installa `python3-venv` e `unixodbc` se mancano;
2. crea `.venv` nella cartella e ci installa `pyodbc`;
3. controlla il driver ODBC IBM e la presenza di `database.db`;
4. se manca, chiede le credenziali e crea `.env` (permessi 600, solo root);
5. crea `as400-sync.service` e `as400-sync.timer` (ogni 5 minuti) e lancia
   una prima sincronizzazione di prova.

Il servizio usa la cartella in cui si trova l'installer. **Se sposti la
cartella, rilancia l'installer.** Per rimuovere servizio e timer:

```bash
sudo ./install-debian13.sh --uninstall
```

### File `.env`

Letto automaticamente da `as400.py` (cartella dello script). Le variabili già
presenti nell'ambiente hanno la precedenza.

```
AS400_SYSTEM=10.0.0.1
AS400_UID=UTENTE
AS400_PWD='password'
AS400_DRIVER='IBM i Access ODBC Driver'
MAIN_DB_PATH=/var/opt/in-out/database.db
```

| Variabile | Obbligatoria | Default |
|---|---|---|
| `AS400_SYSTEM` | sì | — |
| `AS400_UID` | sì | — |
| `AS400_PWD` | sì | — |
| `AS400_DRIVER` | no | `IBM i Access ODBC Driver` |
| `MAIN_DB_PATH` | no | `/var/opt/in-out/database.db` |
| `TEST_DB_PATH` | no | `<cartella script>/test_as400.db` |
| `SAMPLE_DB_PATH` | no | `<cartella script>/sample_as400.db` |
| `AS400_ENV_FILE` | no | `<cartella script>/.env` |

Il `.env` contiene la password: non va messo su git (è già in `.gitignore`).

---

## 7. Gestione

Prossime esecuzioni:

```bash
systemctl list-timers as400-sync.timer
```

Log in tempo reale:

```bash
journalctl -u as400-sync.service -f
```

Lanciare subito una sincronizzazione:

```bash
sudo systemctl start as400-sync.service
```

Sospendere / riprendere:

```bash
sudo systemctl stop as400-sync.timer
```

```bash
sudo systemctl start as400-sync.timer
```

Un'esecuzione riuscita scrive nel log:

```
INFO Lette 30 prenotazioni da AS400
INFO Sincronizzazione completata: 0 inseriti, 29 aggiornati, 1 saltati
```

### Problemi frequenti

| Messaggio | Causa | Soluzione |
|---|---|---|
| `pyodbc non installato` | Lanciato fuori dal venv | Usa `.venv/bin/python3 as400.py` o rilancia l'installer |
| `Variabili d'ambiente AS400_SYSTEM, AS400_UID, AS400_PWD richieste` | `.env` mancante o incompleto | Controlla `.env` nella cartella dello script |
| `Connessione AS400 fallita` | Rete, credenziali o driver | Verifica IP, utente/password e `odbcinst -q -d` |
| `Database principale non trovato` | `MAIN_DB_PATH` errato o in-out non installato | Correggi `MAIN_DB_PATH` nel `.env` |
| `database is locked` | in-out occupato a lungo | Si risolve da solo al giro successivo (5 minuti) |
| N `saltati` nel log | Prenotazioni già `ENTERED`/`CLOSED` in in-out | Normale, nessuna azione |
