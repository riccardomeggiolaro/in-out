import socket

ip = "10.0.5.98"

try:
    hostname = socket.getaddrinfo(ip, None)[0][4][0]
    print(f"IP:       {ip}")
    print(f"Hostname: {hostname}")
except socket.herror:
    print(f"Nessun hostname trovato per {ip}")