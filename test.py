import psutil

def close_connections_to(ip, port):
    for conn in psutil.net_connections(kind='inet'):
        if conn.raddr and conn.raddr.ip == ip and conn.raddr.port == port:
            print(f"Found connection to {ip}:{port} - status: {conn.status}")
            if conn.status != 'ESTABLISHED':  # Esclude server listener
                try:
                    pid = conn.pid
                    print(conn)
                    if pid:
                        proc = psutil.Process(pid)
                        print(f"Terminating process with PID {pid} holding connection")
                        proc.terminate()
                except Exception as e:
                    print(f"Error terminating process: {e}")

# Esempio: chiudi connessioni verso 10.0.5.177:4001
close_connections_to("10.0.5.177", 4001)