import paramiko
import socket
import threading
import select
import time
from pydantic import BaseModel
import libs.lb_log as lb_log
import queue

class SshClientConnection(BaseModel):
    server: str
    user: str
    password: str
    ssh_port: int
    forwarding_port: int
    local_port: int

def handler(chan, local_port, should_reconnect, active_connections):
    sock = socket.socket()
    try:
        sock.connect(('localhost', local_port))
        sock.settimeout(30)  # Timeout sul socket locale
    except Exception as e:
        lb_log.error(f'Errore di connessione alla porta locale: {str(e)}')
        try:
            chan.close()
        except:
            pass
        return

    connection_id = id(chan)
    active_connections[connection_id] = (chan, sock)

    try:
        while not should_reconnect.is_set():
            try:
                r, w, x = select.select([sock, chan], [], [], 1.0)
                
                if sock in r:
                    data = sock.recv(4096)
                    if len(data) == 0:
                        break
                    chan.sendall(data)
                    
                if chan in r:
                    data = chan.recv(4096)
                    if len(data) == 0:
                        break
                    sock.sendall(data)
            except socket.timeout:
                continue
            except select.error:
                break
            except Exception as e:
                lb_log.error(f'Errore durante la trasmissione dati: {str(e)}')
                break
                
    finally:
        # Rimuovi la connessione dalla lista delle connessioni attive
        active_connections.pop(connection_id, None)
        try:
            sock.close()
        except:
            pass
        try:
            chan.close()
        except:
            pass

def reverse_forward_tunnel(server_port, local_port, transport, should_reconnect):
    active_connections = {}
    
    while not should_reconnect.is_set():
        try:
            chan = transport.accept(1000)
            if chan is None:
                # Verifica e pulisci le connessioni zombie
                for conn_id in list(active_connections.keys()):
                    chan, sock = active_connections[conn_id]
                    if not chan.is_active() or chan.closed:
                        try:
                            sock.close()
                        except:
                            pass
                        try:
                            chan.close()
                        except:
                            pass
                        active_connections.pop(conn_id, None)
                
                if not transport.is_active():
                    lb_log.info("Transport non più attivo, richiesta riconnessione...")
                    should_reconnect.set()
                    break
                continue

            chan.settimeout(30)
            
            # Avvia un nuovo thread handler
            thr = threading.Thread(
                target=handler,
                args=(chan, local_port, should_reconnect, active_connections),
                daemon=True
            )
            thr.start()
            
        except Exception as e:
            lb_log.error(f'Errore durante l\'accettazione della connessione: {str(e)}')
            if not transport.is_active():
                should_reconnect.set()
            break
    
    # Chiudi tutte le connessioni attive quando il tunnel viene chiuso
    for chan, sock in active_connections.values():
        try:
            sock.close()
        except:
            pass
        try:
            chan.close()
        except:
            pass
    active_connections.clear()

def monitor_connection(client: paramiko.SSHClient, should_reconnect):
    transport = client.get_transport()
    while not should_reconnect.is_set():
        try:
            if transport is None or not transport.is_active():
                lb_log.info('La connessione SSH è stata interrotta. Richiesta riconnessione...')
                should_reconnect.set()
                break
            transport.send_ignore()
        except Exception as e:
            lb_log.error(f'Errore nel monitoraggio della connessione: {str(e)}')
            should_reconnect.set()
            break
        time.sleep(1)

def ssh_tunnel(connection: SshClientConnection):
    retry_delay = 1
    max_retry_delay = 30
    
    while True:
        should_reconnect = threading.Event()
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            client.connect(
                connection.server,
                port=connection.ssh_port,
                username=connection.user,
                password=connection.password,
                allow_agent=False,
                look_for_keys=False,
                timeout=30,
                banner_timeout=30
            )
            
            lb_log.info('Connessione SSH stabilita.')
            retry_delay = 1
            
            transport = client.get_transport()
            transport.set_keepalive(10)
            transport.request_port_forward('', connection.forwarding_port)
            
            monitor_thread = threading.Thread(
                target=monitor_connection,
                args=(client, should_reconnect),
                daemon=True
            )
            monitor_thread.start()
            
            # Esegui il tunnel nel thread principale
            reverse_forward_tunnel(
                connection.forwarding_port,
                connection.local_port,
                transport,
                should_reconnect
            )
            
        except paramiko.SSHException as ssh_ex:
            lb_log.error(f'Errore di connessione SSH: {str(ssh_ex)}')
        except Exception as e:
            lb_log.error(f'Errore imprevisto: {str(e)}')
        finally:
            try:
                client.close()
            except:
                pass
            
            lb_log.info(f'Tunnel SSH chiuso. Riprovo a connettermi in {retry_delay} secondi...')
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_retry_delay)