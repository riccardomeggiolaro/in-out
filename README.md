# In-Out

## Immagine Docker

L'immagine viene costruita dalla GitHub Action `.github/workflows/docker-image.yml`
e pubblicata **privata** su `ghcr.io/riccardomeggiolaro/in-out`:

- ogni push su `main` aggiorna il tag `latest`;
- un tag `vX.Y.Z` (es. `git tag v3.0.5 && git push origin v3.0.5`) pubblica la versione `X.Y.Z`
  e crea una release GitHub con **`in-out-docker.zip`**, il pacchetto di installazione
  (compose, installer, `.env.example`) senza codice sorgente.

Per scaricare l'immagine serve un login a `ghcr.io` con un token GitHub *classic*
con il solo permesso **`read:packages`** (GitHub → Settings → Developer settings →
Personal access tokens). Gli installer lo chiedono la prima volta; Docker lo ricorda.

Aggiornamento di un'installazione: `docker compose pull && docker compose up -d`
(per una versione precisa imposta `IN_OUT_TAG` nel file `.env`).

## Installazione con Docker su Linux

Requisiti: host Linux **amd64** (i driver Epson/Custom sono solo x86_64).

```bash
unzip in-out-docker.zip && cd in-out-docker
sudo ./installer-docker.sh
```

L'installer installa Docker (se manca), copia i file in `/opt/in-out`,
crea `.env` e le cartelle persistenti, ferma eventuali servizi in conflitto
(`in-out.service` nativo, CUPS dell'host), scarica l'immagine e avvia il container.
Con `-y` non fa domande; con `--build` costruisce l'immagine dal codice sorgente
invece di scaricarla.

### Avvio manuale

```bash
cp .env.example .env      # modifica percorsi e password CUPS
docker login ghcr.io      # utente GitHub + token read:packages
docker compose pull && docker compose up -d
```

Dal codice sorgente, senza registry: `docker compose up -d --build`.

### Cosa c'è nel container

- in-out (porta configurata in `config.json`, default 80)
- CUPS con driver Epson TM-T20II/TM-T88V e Custom VKP80/VKP80III,
  interfaccia web su `http://<host>:631` (utente/password da `.env`)
- `cifs-utils` per la sync-folder Samba

Su Linux il container ha accesso completo all'host: `network_mode: host` (bilance,
RFID e Moxa via TCP raggiungibili come in un'installazione nativa), `privileged: true`
e tutto `/dev` montato (porte seriali e dispositivi USB, anche collegati a caldo,
mount CIFS).

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
docker compose pull && docker compose up -d   # aggiornamento
```

Il pulsante "Riavvia" dell'interfaccia in Docker riavvia il processo in-out
nel container (non serve systemd).

## Installazione con Docker su Windows

Requisiti: Windows 10 (22H2) / 11 a 64 bit con virtualizzazione abilitata nel BIOS.

1. Scarica `in-out-docker.zip` dalla release GitHub ed estrailo, ad esempio in `C:\in-out`.
2. Apri **PowerShell come Amministratore** in quella cartella ed esegui:
   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass
   .\installer-docker.ps1
   ```
   La prima volta lo script installa WSL2 e Docker Desktop e chiede di riavviare:
   dopo il riavvio apri Docker Desktop una volta (accetta i termini) e rilancia lo script.
   Al primo download chiede utente GitHub e token `read:packages`.
   Con `-Build` (dal codice sorgente completo) costruisce l'immagine invece di scaricarla.
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

- **Dispositivi USB** (adattatori USB-seriale, lettori, ...): l'installer installa
  [usbipd-win](https://github.com/dorssel/usbipd-win) e chiede la modalità:
  - **Tutti** (consigliata): ogni dispositivo USB collegato viene passato al container,
    **tranne** quelli che Windows usa come tastiera, mouse, touch/HID, rete o Bluetooth
    (un dispositivo passato al container sparisce da Windows). Si possono escludere altri VID:PID;
  - **Solo specifici**: solo i VID:PID indicati.

  Viene creata l'operazione pianificata **"In-Out USB"** che a ogni accesso aspetta
  Docker Desktop e ogni 15 secondi passa al container i dispositivi nuovi o ricollegati
  (`docker\windows-usb-attach.ps1`, log in `docker-data\usb-attach.log`).
  Nel container le seriali appaiono come `/dev/ttyUSB0`, `/dev/ttyACM0`, ...:
  usa questi nomi nella configurazione di pese/RFID al posto di `COM3`. Per verificarlo:
  ```powershell
  docker exec in-out ls /dev/ttyUSB* /dev/ttyACM*
  ```
  Per riprendere un dispositivo in Windows: `usbipd detach --busid <BUSID>` e aggiungilo alle esclusioni.

  Nel kernel di WSL2 i driver USB-seriale (FTDI, CH341, CP210x, PL2303) sono moduli **non caricati
  di default**: lo script li carica a ogni avvio di Docker Desktop. A mano:
  ```powershell
  usbipd bind --busid <BUSID>                     # una volta, da amministratore
  usbipd attach --wsl --busid <BUSID>
  docker run --rm --privileged --pid=host alpine nsenter -t 1 -m -u -n -i modprobe -a ftdi_sio ch341 cp210x pl2303 cdc_acm
  docker exec in-out ls /dev/ttyUSB*
  ```
- **Porte COM integrate** (RS232 sulla scheda madre): non possono essere passate al container.
  Usa un convertitore seriale→TCP (es. Moxa NPort) e configura il dispositivo via TCP,
  oppure mantieni l'installazione nativa di in-out su quel PC.
