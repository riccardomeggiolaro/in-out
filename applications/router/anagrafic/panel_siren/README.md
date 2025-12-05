# Panel and Siren System - Adapter Architecture

## Panoramica

Sistema flessibile ad adapter per la gestione di pannelli e sirene con diversi protocolli di comunicazione. Ogni cliente può configurare il proprio dispositivo con il protocollo specifico necessario.

## Adapter Disponibili

### 1. **TCP Custom** (`tcp_custom`)
Protocollo binario custom per pannelli specifici (protocollo originale).

**Configurazione esempio:**
```json
{
  "enabled": true,
  "type": "tcp_custom",
  "connection": {
    "ip": "192.168.1.100",
    "port": 5000,
    "timeout": 5.0
  },
  "config": {
    "max_string_content": 100,
    "panel_id": 16,
    "duration": 90
  }
}
```

**Parametri config:**
- `max_string_content`: Lunghezza massima del buffer di messaggi
- `panel_id`: ID del pannello (default: 0x10 = 16)
- `duration`: Durata visualizzazione in decimi di secondo (default: 0x5A = 90)

### 2. **TCP Raw** (`tcp_raw`)
Invio di testo semplice via TCP (nessuna codifica speciale).

**Configurazione esempio:**
```json
{
  "enabled": true,
  "type": "tcp_raw",
  "connection": {
    "ip": "192.168.1.100",
    "port": 5000,
    "timeout": 5.0
  },
  "config": {
    "encoding": "utf-8",
    "line_ending": "\r\n",
    "wait_response": false,
    "response_bytes": 1024
  }
}
```

**Parametri config:**
- `encoding`: Codifica testo (default: "utf-8")
- `line_ending`: Fine linea (default: "\r\n")
- `wait_response`: Attendere risposta (default: false)
- `response_bytes`: Byte da leggere in risposta (default: 1024)

### 3. **HTTP Simple** (`http_simple`)
Richieste HTTP senza autenticazione.

**Configurazione esempio:**
```json
{
  "enabled": true,
  "type": "http_simple",
  "connection": {
    "ip": "192.168.1.100",
    "port": 80,
    "timeout": 5.0
  },
  "config": {
    "endpoint": "http://192.168.1.100/display",
    "method": "GET",
    "query_param": "text",
    "headers": {}
  }
}
```

**Parametri config:**
- `endpoint`: URL completo dell'endpoint (richiesto)
- `method`: Metodo HTTP (GET, POST, PUT, PATCH) (default: "GET")
- `query_param`: Nome parametro query per il messaggio (opzionale)
- `body_param`: Nome campo body per il messaggio (default: "message")
- `headers`: Header HTTP custom (default: {})

### 4. **HTTP Basic** (`http_basic`)
Richieste HTTP con autenticazione Basic (base64).

**Configurazione esempio:**
```json
{
  "enabled": true,
  "type": "http_basic",
  "connection": {
    "ip": "192.168.1.100",
    "port": 80,
    "timeout": 5.0
  },
  "config": {
    "endpoint": "http://192.168.1.100/api/display",
    "method": "POST",
    "username": "admin",
    "password": "secret123",
    "body_param": "message"
  }
}
```

**Parametri config:**
- `endpoint`: URL completo (richiesto)
- `method`: Metodo HTTP (default: "GET")
- `username`: Username per Basic Auth (richiesto)
- `password`: Password per Basic Auth (richiesto)
- `query_param`: Nome parametro query (opzionale)
- `body_param`: Nome campo body (default: "message")
- `headers`: Header custom (default: {})

### 5. **HTTP Digest** (`http_digest`)
Richieste HTTP con autenticazione Digest (più sicura di Basic).

**Configurazione esempio (protocollo originale sirena):**
```json
{
  "enabled": true,
  "type": "http_digest",
  "connection": {
    "ip": "100.100.100.101",
    "port": 80,
    "timeout": 5.0
  },
  "config": {
    "endpoint": "http://localhost",
    "method": "GET",
    "username": "marco",
    "password": "318101"
  }
}
```

**Parametri config:** Stessi di `http_basic`

### 6. **HTTP Bearer** (`http_bearer`)
Richieste HTTP con token Bearer (Authorization header).

**Configurazione esempio:**
```json
{
  "enabled": true,
  "type": "http_bearer",
  "connection": {
    "ip": "192.168.1.100",
    "port": 443,
    "timeout": 5.0
  },
  "config": {
    "endpoint": "https://api.example.com/siren",
    "method": "POST",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "headers": {}
  }
}
```

**Parametri config:**
- `endpoint`: URL completo (richiesto)
- `method`: Metodo HTTP (default: "GET")
- `token`: Bearer token (richiesto)
- Altri parametri come HTTP simple

### 7. **Disabled** (`disabled`)
Dispositivo disabilitato (nessuna operazione).

**Configurazione esempio:**
```json
{
  "enabled": false,
  "type": "disabled",
  "connection": {
    "ip": "0.0.0.0",
    "port": 0,
    "timeout": 5.0
  },
  "config": {}
}
```

## Configurazione in config.json

### Pannello (Panel)

```json
{
  "app_api": {
    "panel": {
      "enabled": true,
      "type": "tcp_custom",
      "connection": {
        "ip": "192.168.1.100",
        "port": 5000,
        "timeout": 5.0
      },
      "config": {
        "max_string_content": 100,
        "panel_id": 16,
        "duration": 90
      }
    }
  }
}
```

### Sirena (Siren)

```json
{
  "app_api": {
    "siren": {
      "enabled": true,
      "type": "http_digest",
      "connection": {
        "ip": "100.100.100.101",
        "port": 80,
        "timeout": 5.0
      },
      "config": {
        "endpoint": "http://localhost",
        "method": "GET",
        "username": "marco",
        "password": "318101"
      }
    }
  }
}
```

## API Endpoints

### Panel

- `GET /api/anagrafic/message/panel?text={text}` - Aggiungi messaggio al pannello
- `DELETE /api/anagrafic/cancel-message/panel?text={text}` - Rimuovi messaggio dal pannello
- `GET /api/anagrafic/configuration/panel` - Ottieni configurazione pannello
- `PATCH /api/anagrafic/configuration/panel` - Aggiorna configurazione pannello
- `DELETE /api/anagrafic/configuration/panel` - Disabilita pannello

### Siren

- `GET /api/anagrafic/call/siren` - Attiva sirena
- `GET /api/anagrafic/configuration/siren` - Ottieni configurazione sirena
- `PATCH /api/anagrafic/configuration/siren` - Aggiorna configurazione sirena
- `DELETE /api/anagrafic/configuration/siren` - Disabilita sirena

## Come Aggiungere un Nuovo Adapter

1. Creare una nuova classe che eredita da `BaseAdapter`
2. Implementare i metodi astratti:
   - `send_message(message: Optional[str]) -> None`
   - `adapter_type` property
3. (Opzionale) Override del metodo `validate_config()` per validazione custom
4. Aggiungere il nuovo tipo in `AdapterType` enum (base.py)
5. Registrare la classe in `AdapterFactory._ADAPTER_MAP` (factory.py)
6. Aggiungere l'import in `__init__.py`

**Esempio:**

```python
from .base import BaseAdapter, AdapterType

class MyCustomAdapter(BaseAdapter):
    @property
    def adapter_type(self) -> AdapterType:
        return AdapterType.MY_CUSTOM

    def validate_config(self) -> bool:
        super().validate_config()
        # Validazione custom
        if not self.config.get("custom_param"):
            raise ValueError("custom_param is required")
        return True

    async def send_message(self, message: Optional[str] = None) -> None:
        # Implementazione custom
        pass
```

## Vantaggi del Sistema

✅ **Flessibilità**: Ogni cliente può configurare il proprio protocollo
✅ **Opzionalità**: Pannello e sirena completamente opzionali
✅ **Estensibilità**: Facile aggiungere nuovi protocolli
✅ **Retrocompatibilità**: Supporto configurazioni legacy
✅ **Validazione**: Validazione automatica della configurazione
✅ **Type Safety**: Tipizzazione completa con Pydantic

## Migrazione da Vecchia Configurazione

### Pannello (vecchio formato)
```json
{
  "panel": {
    "ip": "192.168.1.100",
    "port": 5000,
    "timeout": 5.0,
    "max_string_content": 100
  }
}
```

### Pannello (nuovo formato)
```json
{
  "panel": {
    "enabled": true,
    "type": "tcp_custom",
    "connection": {
      "ip": "192.168.1.100",
      "port": 5000,
      "timeout": 5.0
    },
    "config": {
      "max_string_content": 100
    }
  }
}
```

La vecchia configurazione continua a funzionare ma è deprecata.
