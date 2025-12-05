# 🧪 Panel Test Server - Guida Rapida

Server di test per simulare e testare il pannello con protocollo binario TCP custom.

## 📋 Indice

1. [Avvio del Server di Test](#avvio-del-server-di-test)
2. [Test con Client Python](#test-con-client-python)
3. [Test dall'Applicazione Web](#test-dallapplicazione-web)
4. [Test con API REST](#test-con-api-rest)
5. [Configurazione Pannello Reale](#configurazione-pannello-reale)

---

## 🚀 Avvio del Server di Test

### Metodo 1: Porta predefinita (5200)

```bash
python3 panel_test_server.py
```

**Output:**
```
================================================================================
🚀 Panel Test Server AVVIATO
================================================================================
📍 Host: 0.0.0.0
🔌 Porta: 5200
🌐 Indirizzo: 0.0.0.0:5200
================================================================================

⏳ In attesa di connessioni...
💡 Configura il pannello con IP: 0.0.0.0 e Porta: 5200
💡 Premi Ctrl+C per terminare
```

### Metodo 2: Porta personalizzata

```bash
python3 panel_test_server.py --host 127.0.0.1 --port 9999
```

### Metodo 3: Background (con log)

```bash
nohup python3 panel_test_server.py > panel_test.log 2>&1 &
```

Per vedere i log in tempo reale:
```bash
tail -f panel_test.log
```

Per fermare:
```bash
pkill -f panel_test_server.py
```

---

## 🧪 Test con Client Python

### Test Base

```bash
python3 panel_test_client.py --message "ABC"
```

**Output:**
```
================================================================================
📤 INVIO MESSAGGIO AL PANNELLO
================================================================================
🌐 Host: 127.0.0.1
🔌 Porta: 5200
💬 Messaggio: 'ABC'
🆔 Panel ID: 16 (0x10)
⏱️  Duration: 90 decimi = 9.0 secondi
────────────────────────────────────────────────────────────────────────────────
📦 Pacchetto generato: 44 byte
📊 Dati (hex): ffffffff2600000068321007b00000002000000000031200410012004200120043000000b70a
────────────────────────────────────────────────────────────────────────────────
🔌 Connessione a 127.0.0.1:5200...
✅ Connesso!
📤 Invio pacchetto...
✅ Pacchetto inviato con successo!
🔌 Connessione chiusa
================================================================================
✅ MESSAGGIO INVIATO CON SUCCESSO
================================================================================
```

### Test con Parametri Personalizzati

```bash
# Messaggio lungo (5 secondi)
python3 panel_test_client.py --message "HELLO" --duration 50

# Panel ID diverso
python3 panel_test_client.py --message "TEST" --panel-id 17

# Host remoto
python3 panel_test_client.py --host 100.100.100.100 --port 5200 --message "OK"

# Tutti i parametri
python3 panel_test_client.py \
    --host 127.0.0.1 \
    --port 5200 \
    --message "ABC123" \
    --panel-id 16 \
    --duration 90 \
    --timeout 10.0
```

### Output del Server

Quando riceve un messaggio, il server mostra:

```
================================================================================
[2025-12-05 10:30:45.123] 🔌 Nuova connessione da 127.0.0.1:54321
================================================================================

📦 Ricevuti 44 byte
📊 Dati raw (hex): ffffffff2600000068321007b00000002000000000031200410012004200120043000000b70a

────────────────────────────────────────────────────────────────────────────────
📋 DECODIFICA PACCHETTO:
────────────────────────────────────────────────────────────────────────────────
✅ Pacchetto valido
🆔 Panel ID: 16 (0x10)
⏱️  Duration: 90 decimi = 9.0 secondi
💬 Messaggio: 'ABC'
📏 Lunghezza messaggio: 3 caratteri
🔢 Checksum: ✅ OK
   - Calcolato: 0x0AB7
   - Ricevuto:  0x0AB7

┌────────────────────────────────────────────┐
│ 📺 DISPLAY PANNELLO:
│
│                   ABC
│
│ (visualizzato per 9.0s)
└────────────────────────────────────────────┘

📈 Messaggi ricevuti: 1
────────────────────────────────────────────────────────────────────────────────
🔌 Chiusura connessione da 127.0.0.1:54321
================================================================================
```

---

## 🌐 Test dall'Applicazione Web

### 1. Avvia il server di test

```bash
python3 panel_test_server.py
```

### 2. Configura il pannello nell'applicazione

Vai su: **http://localhost/panel-siren**

**Configurazione:**
- ✅ Abilita Pannello
- Tipo: `TCP Custom (Protocollo Binario)`
- IP: `127.0.0.1` (o `localhost`)
- Porta: `5200`
- Timeout: `5.0`
- Lunghezza Max Buffer: `3`
- Panel ID: `16`
- Durata: `90`

💾 **Salva Configurazione**

### 3. Testa dall'interfaccia web

Nella sezione **Test Pannello**:
- Testo test: `ABC`
- 🧪 **Invia Test**

Dovresti vedere il messaggio nel terminale del server!

---

## 🔗 Test con API REST

### Test diretto con curl

```bash
# Invia messaggio "TEST" al pannello
curl "http://localhost/api/anagrafic/message/panel?text=TEST"
```

**Response:**
```json
{
  "buffer": "TEST",
  "success": true
}
```

### Cancella messaggio

```bash
curl -X DELETE "http://localhost/api/anagrafic/cancel-message/panel?text=TEST"
```

### Con autenticazione

Se hai autenticazione JWT:

```bash
# Login
TOKEN=$(curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  | jq -r '.access_token')

# Invia messaggio con token
curl "http://localhost/api/anagrafic/message/panel?text=ABC" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🎯 Configurazione Pannello Reale

Quando hai il pannello fisico, modifica la configurazione:

### Nel frontend `/panel-siren`:

```
IP:      100.100.100.100  ← IP del pannello reale
Porta:   5200
Timeout: 5.0
```

### O in `config.json`:

```json
{
  "app_api": {
    "panel": {
      "enabled": true,
      "type": "tcp_custom",
      "connection": {
        "ip": "100.100.100.100",
        "port": 5200,
        "timeout": 5.0
      },
      "config": {
        "max_string_content": 3,
        "panel_id": 16,
        "duration": 90
      }
    }
  }
}
```

---

## 🐛 Troubleshooting

### Errore: "Connection refused"

**Causa:** Il server non è in esecuzione o la porta è diversa

**Soluzione:**
```bash
# Verifica che il server sia attivo
ps aux | grep panel_test_server

# Verifica la porta
netstat -tuln | grep 5200
```

### Errore: "Address already in use"

**Causa:** La porta 5200 è già in uso

**Soluzione:**
```bash
# Trova il processo che usa la porta
lsof -i :5200

# Uccidi il processo (sostituisci PID)
kill -9 <PID>

# Oppure usa una porta diversa
python3 panel_test_server.py --port 9999
```

### Errore: "Timeout"

**Causa:** Il server non risponde entro il timeout

**Soluzione:**
```bash
# Aumenta il timeout
python3 panel_test_client.py --timeout 10.0

# Verifica connettività
ping 127.0.0.1
telnet 127.0.0.1 5200
```

### Pacchetto non valido

**Causa:** Checksum errato o formato pacchetto sbagliato

**Soluzione:**
- Verifica i parametri (panel_id, duration)
- Controlla l'output hex del pacchetto
- Confronta con il protocollo atteso

---

## 📊 Esempi Pratici

### Scenario 1: Test Rapido Locale

```bash
# Terminal 1: Avvia server
python3 panel_test_server.py

# Terminal 2: Invia test
python3 panel_test_client.py --message "OK"
```

### Scenario 2: Test Remoto

```bash
# Server su macchina A (IP: 192.168.1.10)
python3 panel_test_server.py --host 0.0.0.0 --port 5200

# Client su macchina B
python3 panel_test_client.py --host 192.168.1.10 --message "REMOTE"
```

### Scenario 3: Simulazione Buffer

```bash
# Invia 3 messaggi in sequenza
python3 panel_test_client.py --message "AAA"
sleep 1
python3 panel_test_client.py --message "BBB"
sleep 1
python3 panel_test_client.py --message "CCC"

# Il server mostrerà tutti e 3 i messaggi
```

### Scenario 4: Test Stress

```bash
# Invia 10 messaggi rapidamente
for i in {1..10}; do
    python3 panel_test_client.py --message "MSG$i"
done
```

---

## 📝 Note

- Il server decodifica automaticamente il protocollo binario
- Mostra checksum, panel ID, duration e messaggio
- Conta i messaggi ricevuti
- Compatibile al 100% con il protocollo del pannello reale
- Utile per debug e sviluppo senza hardware fisico

---

## ✅ Checklist Test Completo

- [ ] Server di test avviato su porta 5200
- [ ] Client Python invia messaggio "TEST" con successo
- [ ] Server decodifica correttamente il messaggio
- [ ] Checksum valido
- [ ] Configurazione web salvata correttamente
- [ ] Test dall'interfaccia web funziona
- [ ] API REST `/api/anagrafic/message/panel` funziona
- [ ] Pronto per connettere pannello reale!

---

**Creato da:** Claude AI
**Data:** 2025-12-05
**Versione:** 1.0
