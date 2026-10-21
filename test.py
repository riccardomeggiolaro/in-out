"""
Consumer lato server (esempio): riceve le pesate dai gateway via MQTT,
le salva in modo idempotente e conferma con un ack applicativo.

Qui SQLite fa da segnaposto: in produzione usa Postgres con
INSERT ... ON CONFLICT (uuid) DO NOTHING.

Dipendenze: pip install paho-mqtt   (>= 2.0)
"""
import json
import os
import sqlite3

import paho.mqtt.client as mqtt

BROKER_HOST = os.getenv("BROKER_HOST", "localhost")
BROKER_PORT = int(os.getenv("BROKER_PORT", "1883"))
DB_PATH = os.getenv("DB_PATH", "server.db")

db = sqlite3.connect(DB_PATH, check_same_thread=False)
db.execute(
    """CREATE TABLE IF NOT EXISTS weighings (
           uuid      TEXT PRIMARY KEY,   -- garantisce l'idempotenza
           device_id TEXT NOT NULL,
           seq       INTEGER NOT NULL,
           ts        REAL NOT NULL,
           data      TEXT NOT NULL
       )"""
)
db.commit()


def on_connect(client, userdata, flags, reason_code, properties):
    print("consumer connesso:", reason_code)
    # Shared subscription ($share): se avvii piu' consumer il carico si divide.
    # Richiede un broker che la supporti (EMQX, HiveMQ, Mosquitto >= 2.0 con MQTT5).
    # Con un solo consumer puoi usare semplicemente "devices/+/weighings".
    client.subscribe("devices/+/weighings", qos=1)


def on_message(client, userdata, msg):
    # topic: devices/<device_id>/weighings
    parts = msg.topic.split("/")
    if len(parts) != 3:
        return
    device_id = parts[1]

    try:
        rec = json.loads(msg.payload)
        rec_uuid, seq, ts, data = rec["uuid"], rec["seq"], rec["ts"], rec["data"]
    except (json.JSONDecodeError, KeyError):
        print("messaggio malformato da", device_id)
        return  # in produzione: salvalo in una dead-letter table

    # 1) salva in modo idempotente
    db.execute(
        "INSERT OR IGNORE INTO weighings (uuid, device_id, seq, ts, data) VALUES (?,?,?,?,?)",
        (rec_uuid, device_id, seq, ts, json.dumps(data)),
    )
    db.commit()

    # 2) SOLO dopo il commit conferma al gateway (anche per i duplicati)
    client.publish(
        f"devices/{device_id}/acks", json.dumps({"acked": [rec_uuid]}), qos=1
    )


def publish_config(client, device_id: str, version: int, params: dict):
    """Esempio di invio configurazione: retained, cosi' il gateway la riceve
    anche se era offline quando l'hai pubblicata."""
    client.publish(
        f"devices/{device_id}/config",
        json.dumps({"version": version, "params": params}),
        qos=1,
        retain=True,
    )


def notify_master_data(client, device_id: str, rev: int):
    """Notifica leggera: il gateway scarica poi via HTTPS."""
    client.publish(
        f"devices/{device_id}/masterdata/notify", json.dumps({"rev": rev}), qos=1
    )


if __name__ == "__main__":
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="server-consumer-1",
        clean_session=False,
    )
    client.username_pw_set(os.getenv("MQTT_USER", "server"), os.getenv("MQTT_PASS", ""))
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=30)
    client.loop_forever()