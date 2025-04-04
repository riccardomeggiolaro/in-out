import requests
from requests.auth import HTTPDigestAuth
import socket

# Device details
SHELLY_IP = "100.100.100.101"  # Replace with actual IP address
ENDPOINT = f"http://{SHELLY_IP}/rpc/Switch.Set?id=0&on=true"

# Credentials
USERNAME = "admin"  # Replace with actual username
PASSWORD = "16888"  # Replace with actual password

def send_siren_command(endpoint, username, password, timeout=5):
    try:
        # Verificare preventivamente la raggiungibilità dell'host
        socket.create_connection((SHELLY_IP, 80), timeout=timeout)
        
        # Impostare un timeout per la richiesta
        response = requests.get(
            ENDPOINT, 
            auth=HTTPDigestAuth(USERNAME, PASSWORD),
            timeout=timeout
        )

        # Sollevare un'eccezione in caso di errore
        response.raise_for_status()

    except socket.timeout:
        raise ConnectionError(f"Host {SHELLY_IP} non raggiungibile (timeout)")
    except socket.error as e:
        raise ConnectionError(f"Errore di rete con {SHELLY_IP}: {e}")
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Errore durante la richiesta a {SHELLY_IP}: {e}")
    except Exception as e:
        raise e

def activate_siren():
    # Questo metodo mantiene la compatibilità con le chiamate esistenti
    send_siren_command()