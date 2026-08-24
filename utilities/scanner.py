#!/usr/bin/env python3
"""
Scansiona la propria subnet locale (rilevata automaticamente da IP + netmask)
e per ogni host prova GET http://IP/whoami sulla porta 80.
Se la risposta JSON contiene {"program_name": "in-out"}, l'IP viene
stampato live e aggiunto alla lista finale.

Dipendenze:
    pip install requests netifaces
"""

import socket
import ipaddress
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

import netifaces


TIMEOUT = 0.5          # secondi per richiesta
MAX_WORKERS = 100       # thread paralleli
TARGET_KEY = "program_name"
TARGET_VALUE = "in-out"


def get_own_network() -> ipaddress.IPv4Network:
    """
    Trova l'IP locale (quello usato per uscire su internet) e la relativa
    netmask leggendola dall'interfaccia corrispondente, poi calcola la rete.
    """
    # 1. IP locale "principale" (non richiede connessione reale)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    finally:
        s.close()

    # 2. Trova l'interfaccia che ha questo IP e prendine la netmask
    for iface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(iface).get(netifaces.AF_INET, [])
        for addr in addrs:
            if addr.get("addr") == local_ip:
                netmask = addr.get("netmask")
                network = ipaddress.IPv4Network(
                    f"{local_ip}/{netmask}", strict=False
                )
                return network

    raise RuntimeError("Impossibile determinare la subnet locale")


def check_host(ip: str):
    url = f"http://{ip}/whoami"
    try:
        r = requests.get(url, timeout=TIMEOUT)
        data = r.json()
        if data.get(TARGET_KEY) == TARGET_VALUE:
            return ip
    except Exception:
        pass
    return None


def main():
    network = get_own_network()
    print(f"Subnet rilevata: {network}")
    print(f"Host da scansionare: {network.num_addresses - 2}\n")

    hosts = [str(h) for h in network.hosts()]
    found = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_host, ip): ip for ip in hosts}
        for future in as_completed(futures):
            result = future.result()
            if result:
                found.append(result)
                print(f"[MATCH] {result} -> program_name: {TARGET_VALUE}")

    print("\n--- Risultato finale ---")
    if found:
        for ip in found:
            print(ip)
    else:
        print("Nessun host trovato.")


if __name__ == "__main__":
    main()