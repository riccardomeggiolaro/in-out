import paramiko
import socket
import threading
import select

def reverse_forward_tunnel(server_port, local_port, transport):
    while True:
        try:
            chan = transport.accept(1000)
            if chan is None:
                continue
            thr = threading.Thread(target=handler, args=(chan, local_port), daemon=True)
            thr.start()
        except Exception as e:
            print(f'Errore: {str(e)}')

def handler(chan, local_port):
    sock = socket.socket()
    try:
        sock.connect(('localhost', local_port))
    except Exception as e:
        print(f'Errore di connessione alla porta locale: {str(e)}')
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

def ssh_tunnel():
    server = 'on.baron.it'
    server_port = 80
    remote_port = 3322
    local_port = 8000
    user = 'root'
    password = '318101'  # Password inserita direttamente nello script

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(server, port=remote_port, username=user, password=password, allow_agent=False, look_for_keys=False)
    except Exception as e:
        print(f'Errore di connessione al server SSH: {str(e)}')
        return

    try:
        transport = client.get_transport()
        transport.request_port_forward('', server_port)
        reverse_forward_tunnel(server_port, local_port, transport)
    except KeyboardInterrupt:
        print('Interruzione da tastiera. Chiusura del tunnel.')
    finally:
        client.close()

if __name__ == '__main__':
    ssh_tunnel()