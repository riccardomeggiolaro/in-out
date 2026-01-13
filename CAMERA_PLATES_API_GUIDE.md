# Sistema Storico Targhe Telecamere - Guida API

## Descrizione
Sistema per salvare e visualizzare le ultime 5 targhe rilevate da ciascuna telecamera nella dashboard.

## Endpoints API

### 1. Aggiungere una targa rilevata
**POST** `/api/anagrafic/camera-plate-history/add`

**Body (JSON):**
```json
{
  "camera_id": "CAM_01",
  "plate": "AB123CD"
}
```

**Risposta:**
```json
{
  "success": true,
  "message": "Plate added successfully",
  "camera_id": "CAM_01",
  "plate": "AB123CD",
  "plates": [
    {
      "id": 1,
      "camera_id": "CAM_01",
      "plate": "AB123CD",
      "timestamp": "2026-01-13 10:30:45"
    }
  ]
}
```

**Note:**
- Le targhe più corte di 5 caratteri vengono automaticamente scartate
- Il sistema mantiene automaticamente solo le ultime 5 targhe per telecamera
- Le targhe più vecchie vengono eliminate automaticamente

---

### 2. Recuperare targhe di tutte le telecamere
**GET** `/api/anagrafic/camera-plate-history/list`

**Risposta:**
```json
{
  "success": true,
  "data": {
    "CAM_01": [
      {
        "id": 5,
        "plate": "AB123CD",
        "timestamp": "2026-01-13 10:30:45"
      },
      {
        "id": 4,
        "plate": "EF456GH",
        "timestamp": "2026-01-13 10:25:30"
      }
    ],
    "CAM_02": [
      {
        "id": 3,
        "plate": "IJ789KL",
        "timestamp": "2026-01-13 10:20:15"
      }
    ]
  }
}
```

---

### 3. Recuperare targhe di una specifica telecamera
**GET** `/api/anagrafic/camera-plate-history/list/{camera_id}`

**Esempio:** `/api/anagrafic/camera-plate-history/list/CAM_01`

**Risposta:**
```json
{
  "success": true,
  "camera_id": "CAM_01",
  "plates": [
    {
      "id": 5,
      "plate": "AB123CD",
      "timestamp": "2026-01-13 10:30:45"
    }
  ]
}
```

---

## Test Manuale con cURL

### Aggiungere targhe di test:

```bash
# Aggiungi targhe per CAM_01
curl -X POST http://localhost:8000/api/anagrafic/camera-plate-history/add \
  -H "Content-Type: application/json" \
  -d '{"camera_id": "CAM_01", "plate": "AB123CD"}'

curl -X POST http://localhost:8000/api/anagrafic/camera-plate-history/add \
  -H "Content-Type: application/json" \
  -d '{"camera_id": "CAM_01", "plate": "EF456GH"}'

# Aggiungi targhe per CAM_02
curl -X POST http://localhost:8000/api/anagrafic/camera-plate-history/add \
  -H "Content-Type: application/json" \
  -d '{"camera_id": "CAM_02", "plate": "IJ789KL"}'
```

### Recuperare tutte le targhe:

```bash
curl http://localhost:8000/api/anagrafic/camera-plate-history/list
```

### Recuperare targhe di una telecamera specifica:

```bash
curl http://localhost:8000/api/anagrafic/camera-plate-history/list/CAM_01
```

---

## Visualizzazione nella Dashboard

Le targhe vengono visualizzate automaticamente nella dashboard appena sotto i pulsanti "⚡" e "🖨️ Ristampa".

### Caratteristiche UI:
- **Organizzazione per telecamera**: ogni telecamera ha la sua sezione
- **Evidenziazione**: la targa più recente è evidenziata in verde
- **Click per selezionare**: cliccando su una targa, viene automaticamente selezionata come veicolo
- **Aggiornamenti in tempo reale**: tramite WebSocket
- **Timestamp**: ogni targa mostra l'ora di rilevamento
- **Auto-hide**: il container è nascosto se non ci sono targhe

---

## Integrazione con Sistema di Rilevamento Targhe

Per integrare un sistema esterno di rilevamento targhe (OCR, ANPR, ecc.), configurare il sistema per inviare una richiesta POST all'endpoint `/api/anagrafic/camera-plate-history/add` ogni volta che viene rilevata una nuova targa.

### Esempio in Python:

```python
import requests

def send_detected_plate(camera_id, plate):
    url = "http://localhost:8000/api/anagrafic/camera-plate-history/add"
    data = {
        "camera_id": camera_id,
        "plate": plate
    }
    response = requests.post(url, json=data)
    return response.json()

# Utilizzo
result = send_detected_plate("CAM_01", "AB123CD")
print(result)
```

---

## Database

### Tabella: `camera_plate_history`

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| id | Integer | Primary key |
| camera_id | String | Identificatore telecamera |
| plate | String | Targa rilevata (uppercase, case-insensitive) |
| timestamp | DateTime | Momento del rilevamento |
| date_created | DateTime | Data creazione record |

### Indici:
- `camera_id` (per query veloci per telecamera)
- `plate` (per ricerche per targa)
- `timestamp` (per ordinamento temporale)

---

## WebSocket

Le modifiche alle targhe vengono trasmesse in tempo reale tramite WebSocket:

**URL:** `ws://localhost:8000/api/anagrafic/camera_plate_history?token={auth_token}`

**Messaggio broadcast quando viene aggiunta una targa:**
```json
{
  "action": "add",
  "camera_id": "CAM_01",
  "plates": [...]
}
```

---

## Caratteristiche Implementate

✅ Salvataggio automatico ultime 5 targhe per telecamera
✅ Eliminazione automatica targhe più vecchie
✅ Filtro targhe troppo corte (< 5 caratteri)
✅ API REST completa (add, list, list by camera)
✅ Visualizzazione nella dashboard
✅ Selezione targa con click
✅ Aggiornamenti WebSocket in tempo reale
✅ Design responsive
✅ Timestamp su ogni targa
✅ Evidenziazione targa più recente

---

## Prossimi Passi (Opzionale)

- Configurazione numero massimo targhe per telecamera (attualmente fisso a 5)
- Storico completo targhe con paginazione
- Export CSV/PDF targhe rilevate
- Statistiche rilevamenti per telecamera
- Filtri per data/ora
- Notifiche per targhe specifiche
