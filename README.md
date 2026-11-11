# In-Out

## Installazione con Docker

Requisiti: host Linux **amd64** (i driver Epson/Custom sono solo x86_64).

```bash
sudo ./installer-docker.sh
```

L'installer installa Docker (se manca), copia il progetto in `/opt/in-out`,
crea `.env` e le cartelle persistenti, ferma eventuali servizi in conflitto
(`in-out.service` nativo, CUPS dell'host) e avvia il container.
Con `-y` non fa domande.

### Avvio manuale

```bash
cp .env.example .env      # modifica percorsi e password CUPS
docker compose up -d --build
```

### Cosa c'è nel container

- in-out (porta configurata in `config.json`, default 80)
- CUPS con driver Epson TM-T20II/TM-T88V e Custom VKP80/VKP80III,
  interfaccia web su `http://<host>:631` (utente/password da `.env`)
- `cifs-utils` per la sync-folder Samba

Il container usa `network_mode: host` (bilance, RFID e Moxa via TCP raggiungibili
come in un'installazione nativa) e `privileged: true` (porte seriali `/dev/tty*`
e mount CIFS).

### Dati persistenti

| Host (default)       | Container         | Contenuto                                  |
|----------------------|-------------------|--------------------------------------------|
| `/etc/in-out`        | `/etc/in-out`     | `config.json`, `service.log`               |
| `/var/opt/in-out`    | `/var/opt/in-out` | database, pdf, csv, immagini, backup       |
| `/etc/in-out/cups`   | `/etc/cups`       | stampanti configurate in CUPS              |

Al primo avvio, se `config.json` non esiste, viene copiato quello di default.
Il percorso della configurazione è definito dalla variabile `IN_OUT_CONFIG_DIR`
(senza la variabile il comportamento è quello nativo: `config.json` accanto a `main.py`).

### Comandi utili

```bash
docker compose logs -f          # log
docker compose restart          # riavvio
git pull && docker compose up -d --build   # aggiornamento
```

Il pulsante "Riavvia" dell'interfaccia in Docker riavvia il processo in-out
nel container (non serve systemd).

## Installazione con Docker su Windows

Requisiti: Windows 10 (22H2) / 11 a 64 bit con virtualizzazione abilitata nel BIOS.

1. Clona o copia il progetto, ad esempio in `C:\in-out`.
2. Apri **PowerShell come Amministratore** nella cartella del progetto ed esegui:
   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass
   .\installer-docker.ps1
   ```
   La prima volta lo script installa WSL2 e Docker Desktop e chiede di riavviare:
   dopo il riavvio apri Docker Desktop una volta (accetta i termini) e rilancia lo script.
3. Apri `http://localhost/` (in-out) e `http://localhost:631/` (CUPS, credenziali nel file `.env`).

Differenze rispetto a Linux:

- il container usa la rete *bridge* con le porte pubblicate (`docker-compose.windows.yml`);
  se cambi `app_api.port` in `config.json` aggiorna anche `IN_OUT_HTTP_PORT` nel `.env`
  e la porta interna in `docker-compose.windows.yml`;
- i dati stanno in `docker-data\` dentro la cartella del progetto;
- Docker Desktop parte solo dopo il login dell'utente: abilita
  *Settings → General → Start Docker Desktop when you sign in* e l'accesso automatico a Windows
  se il PC deve ripartire da solo;
- Docker Desktop è gratuito per aziende sotto i 250 dipendenti e 10 M$ di fatturato,
  altrimenti serve un abbonamento.

### Porte seriali su Windows

Docker Desktop non vede le porte `COMx`. Le opzioni sono:

- **Adattatori USB-seriale** con [usbipd-win](https://github.com/dorssel/usbipd-win)
  (lo script propone di installarlo). Da PowerShell come Amministratore:
  ```powershell
  usbipd list                                   # trova il BUSID dell'adattatore
  usbipd bind --busid 2-3                       # una sola volta
  usbipd attach --wsl --busid 2-3 --auto-attach # ad ogni avvio
  ```
  Nel container il dispositivo appare come `/dev/ttyUSB0` (o `/dev/ttyACM0`):
  usa questo nome nella configurazione della pesa/RFID al posto di `COM3`.
- **Porte COM integrate** (RS232 sulla scheda madre): non possono essere passate al container.
  Usa un convertitore seriale→TCP (es. Moxa NPort) e configura il dispositivo via TCP,
  oppure mantieni l'installazione nativa di in-out su quel PC.
