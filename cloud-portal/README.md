# BARON IN-OUT Cloud Portal

Portale online multi-sito che riceve le pesate dagli impianti BARON IN-OUT (via API) e le rende
consultabili da browser, con login e filtri.

## Componenti

- `app/` — backend FastAPI + SQLAlchemy (Postgres in produzione, SQLite in sviluppo)
- Frontend server-rendered (Jinja2 + JS vanilla), niente build step

## Avvio rapido (sviluppo, SQLite)

```bash
cd cloud-portal
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY=dev-secret
export BOOTSTRAP_ADMIN_PASSWORD=admin123
uvicorn app.main:app --reload
```

Al primo avvio viene creato automaticamente un utente super-admin (`admin` / la password indicata in
`BOOTSTRAP_ADMIN_PASSWORD`). Apri `http://localhost:8000/login`.

## Avvio in produzione (Docker + Postgres)

```bash
cd cloud-portal
cp .env.example .env   # valorizza SECRET_KEY e le password
docker compose up -d --build
```

Il portale sarà disponibile su `http://<server>:8000` (mettere dietro un reverse proxy con TLS, es.
nginx/Caddy, per esporlo su internet).

## Concetti

- **Sito (Site)**: un impianto di pesatura (un'installazione BARON IN-OUT). Ogni sito ha un nome, un
  codice univoco e una **API key** usata dall'impianto per inviare le pesate.
- **Utente portale (PortalUser)**: un login web. Un utente super-admin vede tutti i siti e gestisce
  siti/utenti; un utente normale è associato a un sito e vede solo le pesate di quel sito.
- **Pesata (Weighing)**: record ricevuto da un sito, identificato da `(site_id, external_id)` — dove
  `external_id` è l'id del record `InOut` sull'impianto locale. L'invio è idempotente: rispedire lo
  stesso `external_id` aggiorna il record invece di duplicarlo.

## Gestione siti

1. Accedi come super-admin su `/sites`.
2. Crea un nuovo sito (nome + codice). L'**API key viene mostrata una sola volta**: copiala e
   configurala sull'impianto locale (vedi `modules/md_cloud_portal` nel progetto principale).
3. Se necessario, crea utenti scoperti sul singolo sito così i clienti/operatori di quell'impianto
   possano accedere al portale vedendo solo le proprie pesate.

## API di ingestione

L'impianto locale invia le pesate con:

```
POST /api/ingest/weighings
X-API-Key: <api key del sito>
Content-Type: application/json

{
  "weighings": [
    {
      "external_id": 123,
      "status": "CLOSED",
      "type": "MANUALLY",
      "type_subject": "CUSTOMER",
      "plate": "AB123CD",
      "subject_name": "Rossi Srl",
      "material": "Ferro",
      "weight1": 15000,
      "weight1_date": "2026-07-01T08:00:00",
      "weight2": 25000,
      "weight2_date": "2026-07-01T08:30:00",
      "net_weight": 10000,
      "date_created": "2026-07-01T07:55:00"
    }
  ]
}
```

Risposta:

```json
{ "received": 1, "created": 1, "updated": 0 }
```

## API di consultazione

```
GET /api/weighings?plate=AB123CD&from_date=2026-07-01&limit=50&offset=0
Authorization: Bearer <token JWT ottenuto da /api/auth/login>
```

## Note di sicurezza

- Le API key dei siti sono salvate come hash SHA-256 (non recuperabili, solo verificabili) e mostrate
  in chiaro solo al momento della creazione/rigenerazione.
- Le password degli utenti portale sono salvate con bcrypt (salt casuale per utente).
- Mettere sempre il portale dietro HTTPS in produzione: le API key e i JWT viaggiano in header HTTP.
