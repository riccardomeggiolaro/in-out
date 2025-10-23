# Sync Manager - Python File Synchronization Service

Un servizio Python avanzato per la sincronizzazione automatica di file tra cartelle locali e remote (rete/NAS/cloud), con API REST completa per la gestione e il monitoraggio.

## 🚀 Caratteristiche Principali

- **API REST completa** - Gestione via HTTP con FastAPI
- **Multi-sincronizzazione** - Gestisce multiple sincronizzazioni simultanee
- **Resilienza di rete** - Gestisce disconnessioni e riconnessioni automatiche
- **Monitoraggio real-time** - Rileva modifiche ai file istantaneamente
- **Dashboard Web** - Interfaccia web per monitoraggio e configurazione
- **Logging avanzato** - Sistema di log strutturato con rotazione
- **Persistenza stato** - Database SQLite per tracciare sincronizzazioni
- **Docker ready** - Container Docker per deployment facile
- **Metrics & Health** - Endpoint per monitoring e health check
- **WebSocket** - Eventi real-time per dashboard
- **Supporto cloud** - S3, Azure Blob, Google Cloud Storage

## 📋 Requisiti

- Python 3.8+
- pip

## 🔧 Installazione

### Locale

```bash
# Clona repository
git clone <repository>
cd sync-manager

# Crea virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oppure
venv\Scripts\activate  # Windows

# Installa dipendenze
pip install -r requirements.txt

# Avvia il servizio
python main.py
```

### Docker

```bash
# Build image
docker build -t sync-manager .

# Run container
docker run -d -p 8000:8000 -v /path/to/data:/data sync-manager
```

### Docker Compose

```bash
docker-compose up -d
```

## 🎯 Uso Rapido

### 1. Avvia il servizio

```bash
python main.py
```

Il servizio sarà disponibile su `http://localhost:8000`

### 2. Crea una sincronizzazione via API

```bash
curl -X POST http://localhost:8000/api/v1/syncs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Backup Documenti",
    "source_path": "/home/user/documenti",
    "destination_path": "/mnt/nas/backup",
    "delete_after_sync": true,
    "sync_interval": 5,
    "enabled": true
  }'
```

### 3. Monitora lo stato

```bash
# Lista sincronizzazioni
curl http://localhost:8000/api/v1/syncs

# Stato specifico
curl http://localhost:8000/api/v1/syncs/{sync_id}/status

# Metriche
curl http://localhost:8000/api/v1/metrics
```

## 📖 API Documentation

### Documentazione interattiva disponibile su:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Endpoint principali:

#### Sincronizzazioni
- `GET /api/v1/syncs` - Lista tutte le sincronizzazioni
- `POST /api/v1/syncs` - Crea nuova sincronizzazione
- `GET /api/v1/syncs/{id}` - Dettagli sincronizzazione
- `PUT /api/v1/syncs/{id}` - Aggiorna configurazione
- `DELETE /api/v1/syncs/{id}` - Elimina sincronizzazione
- `POST /api/v1/syncs/{id}/start` - Avvia sincronizzazione
- `POST /api/v1/syncs/{id}/stop` - Ferma sincronizzazione
- `POST /api/v1/syncs/{id}/force` - Forza sincronizzazione immediata

#### Monitoring
- `GET /api/v1/status` - Stato generale del servizio
- `GET /api/v1/metrics` - Metriche di performance
- `GET /api/v1/health` - Health check
- `GET /api/v1/logs` - Visualizza logs
- `WS /api/v1/ws` - WebSocket per eventi real-time

#### File Operations
- `GET /api/v1/syncs/{id}/files` - Lista file in coda
- `GET /api/v1/syncs/{id}/history` - Storico sincronizzazioni
- `POST /api/v1/syncs/{id}/retry` - Riprova file falliti

## 🔌 Configurazione

### File di configurazione (`config.yaml`)

```yaml
server:
  host: 0.0.0.0
  port: 8000
  workers: 4

database:
  url: sqlite:///data/sync_manager.db
  
logging:
  level: INFO
  file: /var/log/sync_manager.log
  max_size: 10MB
  backup_count: 5

sync:
  default_interval: 5
  max_retries: 3
  retry_delay: 10
  batch_size: 100
  
monitoring:
  enable_metrics: true
  enable_health: true
  
security:
  enable_auth: false
  api_key: your-secret-key
```

## 🎨 Dashboard Web

Accedi alla dashboard su `http://localhost:8000`

Funzionalità:
- Vista real-time delle sincronizzazioni
- Grafici statistiche
- Gestione sincronizzazioni
- Visualizzazione logs
- Configurazione

## 🐳 Docker Deployment

### docker-compose.yml

```yaml
version: '3.8'

services:
  sync-manager:
    image: sync-manager:latest
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data
      - ./config:/config
      - /mnt/nas:/mnt/nas
    environment:
      - CONFIG_FILE=/config/config.yaml
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

## 📊 Esempi di Utilizzo

### Python Client

```python
import requests

# Client API
class SyncManagerClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def create_sync(self, config):
        return requests.post(f"{self.base_url}/api/v1/syncs", json=config)
    
    def get_status(self, sync_id):
        return requests.get(f"{self.base_url}/api/v1/syncs/{sync_id}/status")

# Uso
client = SyncManagerClient()
response = client.create_sync({
    "name": "Backup Photos",
    "source_path": "/home/user/photos",
    "destination_path": "/mnt/nas/photos",
    "delete_after_sync": True
})
```

### Integrazione con systemd

```ini
[Unit]
Description=Sync Manager Service
After=network.target

[Service]
Type=simple
User=syncuser
WorkingDirectory=/opt/sync-manager
ExecStart=/usr/bin/python3 /opt/sync-manager/main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## 🔒 Sicurezza

- Supporto HTTPS con certificati SSL
- Autenticazione API Key opzionale
- Rate limiting configurabile
- Validazione path per prevenire directory traversal
- Logging di tutte le operazioni

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Con coverage
pytest --cov=sync_manager tests/
```

## 📈 Performance

- Gestisce migliaia di file simultaneamente
- Supporto per file di grandi dimensioni (streaming)
- Sincronizzazione parallela configurabile
- Cache intelligente per ottimizzare performance
- Compressione opzionale per trasferimenti di rete

## 🤝 Contributing

Contribuzioni benvenute! Vedi [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 Licenza

MIT License - vedi [LICENSE](LICENSE)

## 🆘 Support

- Issue tracker: GitHub Issues
- Documentation: [docs/](docs/)
- Email: support@example.com

## 🗺️ Roadmap

- [ ] Supporto per sincronizzazione bidirezionale
- [ ] Integrazione con servizi cloud (AWS S3, Azure, GCP)
- [ ] Plugin system per estensioni
- [ ] Mobile app per monitoring
- [ ] Crittografia end-to-end
- [ ] Deduplicazione file
