import requests
from requests.auth import HTTPDigestAuth
import socket

def send_message(ip, port, username, password, timeout, endpoint):
    try:
        # Verificare preventivamente la raggiungibilità dell'host
        socket.create_connection((ip, port), timeout=timeout)
        
        # Impostare un timeout per la richiesta
        response = requests.get(
            endpoint, 
            auth=HTTPDigestAuth(username, password),
            timeout=timeout
        )

        # Sollevare un'eccezione in caso di errore
        response.raise_for_status()
    except ConnectionRefusedError:
        raise ConnectionRefusedError(f"Connection refused by {ip}:{port}")
    except socket.timeout:
        raise ConnectionError(f"Host {ip}:{port} non raggiungibile (timeout)")
    except socket.error as e:
        raise ConnectionError(f"Errore di rete con {ip}:{port}: {e}")
    except Exception as e:
        raise ConnectionError(f"Errore di rete con {ip}:{port}: {e}")