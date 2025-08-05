# -*- coding: utf-8 -*-

# ==============================================================
# = Singleton Manager: Gestisce istanza singola applicazione  =
# ==============================================================

import os
import sys
import socket
import threading
import time
import libs.lb_log as lb_log

class SingletonManager:
    def __init__(self, app_name="BARON", port=65432):
        self.app_name = app_name
        self.port = port
        self.lock_file = f"/tmp/{app_name.lower()}.lock"  # Linux
        if os.name == 'nt':  # Windows
            self.lock_file = f"C:\\temp\\{app_name.lower()}.lock"
        
        self.server_socket = None
        self.server_thread = None
        self.is_running = False
        self.on_show_interface_callback = None
    
    def is_already_running(self):
        """Controlla se un'altra istanza è già in esecuzione"""
        if os.path.exists(self.lock_file):
            try:
                with open(self.lock_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Controlla se il processo esiste ancora
                if os.name == 'nt':  # Windows
                    import psutil
                    return psutil.pid_exists(pid)
                else:  # Linux/Unix
                    try:
                        os.kill(pid, 0)  # Non uccide, solo controlla
                        return True
                    except OSError:
                        return False
            except:
                return False
        return False
    
    def create_lock_file(self):
        """Crea il file di lock con il PID corrente"""
        try:
            os.makedirs(os.path.dirname(self.lock_file), exist_ok=True)
            with open(self.lock_file, 'w') as f:
                f.write(str(os.getpid()))
            return True
        except Exception as e:
            lb_log.error(f"Errore nella creazione lock file: {e}")
            return False
    
    def remove_lock_file(self):
        """Rimuove il file di lock"""
        try:
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
        except Exception as e:
            lb_log.error(f"Errore nella rimozione lock file: {e}")
    
    def send_show_interface_command(self):
        """Invia comando alla istanza esistente per mostrare l'interfaccia"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', self.port))
                s.sendall(b'SHOW_INTERFACE')
                response = s.recv(1024)
                return response.decode() == 'OK'
        except Exception as e:
            lb_log.error(f"Errore nell'invio comando: {e}")
            return False
    
    def start_command_server(self, callback=None):
        """Avvia il server per ricevere comandi da altre istanze"""
        self.on_show_interface_callback = callback
        self.server_thread = threading.Thread(target=self._run_command_server, daemon=True)
        self.server_thread.start()
    
    def _run_command_server(self):
        """Esegue il server dei comandi"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('localhost', self.port))
            self.server_socket.listen(1)
            self.is_running = True
            
            lb_log.info(f"Command server avviato sulla porta {self.port}")
            
            while self.is_running:
                try:
                    self.server_socket.settimeout(1)  # Timeout per permettere controllo is_running
                    conn, addr = self.server_socket.accept()
                    
                    with conn:
                        data = conn.recv(1024)
                        command = data.decode()
                        
                        if command == 'SHOW_INTERFACE':
                            lb_log.info("Ricevuto comando SHOW_INTERFACE")
                            if self.on_show_interface_callback:
                                self.on_show_interface_callback()
                            conn.sendall(b'OK')
                        else:
                            conn.sendall(b'UNKNOWN_COMMAND')
                            
                except socket.timeout:
                    continue  # Continua il loop per controllare is_running
                except Exception as e:
                    if self.is_running:  # Solo logga errori se il server dovrebbe essere attivo
                        lb_log.error(f"Errore nel command server: {e}")
                    
        except Exception as e:
            lb_log.error(f"Errore nell'avvio command server: {e}")
    
    def stop_command_server(self):
        """Ferma il server dei comandi"""
        self.is_running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=2)
    
    def cleanup(self):
        """Pulizia risorse"""
        self.stop_command_server()
        self.remove_lock_file()

# Istanza globale
singleton_manager = None

def init_singleton(app_name="BARON"):
    """Inizializza il singleton manager"""
    global singleton_manager
    singleton_manager = SingletonManager(app_name)
    return singleton_manager

def is_already_running():
    """Controlla se un'altra istanza è già in esecuzione"""
    global singleton_manager
    if singleton_manager:
        return singleton_manager.is_already_running()
    return False

def notify_existing_instance():
    """Notifica l'istanza esistente di mostrare l'interfaccia"""
    global singleton_manager
    if singleton_manager:
        return singleton_manager.send_show_interface_command()
    return False

def start_as_primary_instance(show_interface_callback=None):
    """Avvia come istanza principale"""
    global singleton_manager
    if singleton_manager:
        singleton_manager.create_lock_file()
        singleton_manager.start_command_server(show_interface_callback)
        return True
    return False

def cleanup_singleton():
    """Pulizia singleton"""
    global singleton_manager
    if singleton_manager:
        singleton_manager.cleanup()