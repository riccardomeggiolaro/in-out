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
