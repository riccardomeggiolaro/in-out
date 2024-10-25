import paramiko
import socket
import threading
import select
from pydantic import BaseModel
import libs.lb_log as lb_log

class SshClientConnection(BaseModel):
    server: str
    user: str
    password: str
    ssh_port: int
    forwarding_port: int
    local_port: int    

def reverse_forward_tunnel(server_port, local_port, transport):
    while True:
        try:
            chan = transport.accept(1000)
            if chan is None:
                continue
            thr = threading.Thread(target=handler, args=(chan, local_port), daemon=True)
            thr.start()
        except Exception as e:
            lb_log.info(f'Errore: {str(e)}')

def handler(chan, local_port):
    sock = socket.socket()
    try:
        sock.connect(('localhost', local_port))
    except Exception as e:
        lb_log.info(f'Errore di connessione alla porta locale: {str(e)}')
        chan.close()
        return

    while True:
        r, w, x = select.select([sock, chan], [], [])
        if sock in r:
            data = sock.recv(1024)
            if len(data) == 0:
                break
            chan.send(data)
        if chan in r:
            data = chan.recv(1024)
            if len(data) == 0:
                break
            sock.send(data)
    chan.close()
    sock.close()

def ssh_tunnel(connection: SshClientConnection):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    while True:
        try:
            client.connect(
                connection.server,
                port=connection.ssh_port,
                username=connection.user,
                password=connection.password,
                allow_agent=False,
                look_for_keys=False
            )
            lb_log.info('Connessione SSH stabilita.')

            transport = client.get_transport()
            transport.request_port_forward('', connection.forwarding_port)
            reverse_forward_tunnel(connection.forwarding_port, connection.local_port, transport)

        except Exception as e:
            lb_log.info(f'Errore di connessione al server SSH: {str(e)}')
            time.sleep(5)  # Aspetta 5 secondi prima di riprovare
        finally:
            client.close()
            lb_log.info('Tunnel SSH chiuso. Riprovo a connettermi...')