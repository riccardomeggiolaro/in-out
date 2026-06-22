import os
import libs.lb_log as lb_log
import platform
import subprocess
import serial
import serial.tools.list_ports
from pydantic import BaseModel, validator
from serial import SerialException
import socket
from typing import Optional, Union
import select
import time
import shutil
from collections import deque
try:
	import winreg
	import wmi
except ImportError:
	winreg = None
	wmi = None

class Connection(BaseModel):
	def try_connection(self):
		return False, ConnectionError('Try connection: No connection set')
	
	def flush(self):
		return False, ConnectionError('Flush: No connection set')

	def close(self):
		return False, ConnectionError('Close: No connection set')

	def write(self, cmd):
		return False

	def read(self):
		return None

	def is_open(self):
		return False

class SerialPortWithoutControls(Connection):
	baudrate: int = 19200
	serial_port_name: str
	timeout: float = 1

	connecting: bool = False

	conn: Optional[serial.Serial] = None

	class Config:
		arbitrary_types_allowed = True

	def is_open(self):
		status = False
		try:
			if isinstance(self.conn, serial.Serial) and self.conn.is_open:
				status = True
		except TypeError as e:
			pass
		return status

	def try_connection(self):
		status = False
		error_message = None
		self.connecting = True
		try:
			self.flush()
			self.conn = None
			self.conn = serial.Serial(port=self.serial_port_name, baudrate=self.baudrate, timeout=self.timeout)
			status = True
		except SerialException as e:
			error_message = e
			# lb_log.error(f"SerialException on try connection: {error_message}")
		except AttributeError as e:
			error_message = e
			# lb_log.error(f"AttributeError on try connection: {error_message}")
		except TypeError as e:
			error_message = e
			# lb_log.error(f"TypeError on try connection: {error_message}")
		finally:
			self.connecting = False
		return status, error_message

	def flush(self):
		status = False
		error_message = None
		try:
			if isinstance(self.conn, serial.Serial) and self.conn.is_open:
				# Salva il timeout originale
				original_timeout = self.conn.timeout
				
				# Imposta un timeout breve per non bloccare
				self.conn.timeout = 0.1
				
				# Svuota buffer di input
				if self.conn.in_waiting > 0:
					self.conn.reset_input_buffer()
				
				# Svuota buffer di output  
				if self.conn.out_waiting > 0:
					self.conn.reset_output_buffer()
				
				# Flush finale
				self.conn.flush()
				
				# Leggi e scarta eventuali dati residui
				while self.conn.in_waiting:
					discarded = self.conn.read(self.conn.in_waiting)
					lb_log.debug(f"Discarded {len(discarded)} bytes from buffer")
					time.sleep(0.01)  # Piccola pausa
					
				# Ripristina timeout originale
				self.conn.timeout = original_timeout
				
				status = True
		except SerialException as e:
			error_message = e
		except AttributeError as e:
			error_message = e
		except TypeError as e:
			pass
		return status, error_message

	def close(self):
		status = False
		error_message = None
		try:
			if isinstance(self.conn, serial.Serial) and self.conn.is_open:
				self.conn.flush()
				self.conn.close()
				self.conn = None
				status = True
		except SerialException as e:
			error_message = e
			# lb_log.error(f"SerialException on close: {error_message}")
		except AttributeError as e:
			error_message = e
			# lb_log.error(f"AttributeError on close: {error_message}")
		except TypeError as e:
			error_message = e
			# lb_log.error(f"TypeError on close: {error_message}")
		return status, error_message

	def write(self, cmd):
		status = False
		try:
			if isinstance(self.conn, serial.Serial) and self.conn.is_open:
				command = (cmd + chr(13)+chr(10)).encode()
				self.conn.write(command)
				status = True
		except AttributeError as e:
			pass
		except TypeError as e:
			pass
		except SerialException as e:
			pass
		return status

	def read(self):
		try:
			message = None
			if isinstance(self.conn, serial.Serial) and self.conn.is_open:
				message = self.conn.readline()  # Leggi i dati disponibili
		except AttributeError as e:
			pass
		except TypeError as e:
			pass
		return message

class SerialPort(SerialPortWithoutControls):
	@validator('baudrate', pre=True, always=True)
	def check_baudrate(cls, v):
		if v in [9600, 19200, 115200]:
			return v
		raise ValueError('Baudrate not valid')

	@validator('serial_port_name', pre=True, always=True)
	def check_serial_port_name(cls, v):
		exist, message = exist_serial_port(v)
		if exist is False:
			raise ValueError("Serial port is not exist")
		just_in_use, message = serial_port_is_just_in_use(v)
		if just_in_use:
			raise ValueError("Serial port is just occupated")
		enabled, message = enable_serial_port(v)
		# if not enabled:
		# 	raise ValueError(message)
		return v

	@validator('timeout', pre=False, always=True)
	def check_timeout(cls, v):
		if v > 0:
			return v
		raise ValueError("Timeout must to be bigger than 0")

class TcpWithoutControls(Connection):
	ip: str
	port: int
	timeout: float

	connecting: bool = False

	conn: Optional[socket.socket] = None

	class Config:
		arbitrary_types_allowed = True

	def is_open(self):
		try:
			status = None
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
				sock.setblocking(False)
				sock.settimeout(0.1)
				result = sock.connect_ex((self.ip, self.port))
				if result == 0:
					status = True
				else:
					status = False
			return status
		except socket.timeout:
			return False
		except Exception as e:
			return False

	def try_connection(self):
		status = True
		error_message = None
		self.connecting = True
		try:
			self.conn = None
			self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.conn.setblocking(False)
			self.conn.settimeout(self.timeout)
			self.conn.connect((self.ip, self.port))
		except Exception as e:
			status = False
			error_message = e
		finally:
			self.connecting = False
		return status, error_message

	def flush(self):
		status = True
		error_message = None
		try:
			if self.conn is None:
				return False, "No connection"
				
			# Imposta socket non bloccante temporaneamente
			self.conn.setblocking(False)
			
			buffer = b""
			total_discarded = 0
			
			# Ricevi e scarta tutti i dati nel buffer
			while True:
				try:
					data = self.conn.recv(4096)
					if not data:
						break
					total_discarded += len(data)
				except BlockingIOError:
					# Non ci sono più dati da leggere
					break
				except socket.timeout:
					break
					
			if total_discarded > 0:
				lb_log.debug(f"Flushed {total_discarded} bytes from TCP buffer")
				
			# Ripristina modalità bloccante con timeout
			self.conn.setblocking(True)
			self.conn.settimeout(self.timeout)
			
		except Exception as e:
			status = False
			error_message = e
		return status, error_message

	def close(self):
		status = False
		error_message = None
		try:
			# Shutdown the socket to indicate no more data will be sent or received
			self.conn.shutdown(socket.SHUT_RDWR)
			# Close the socket to free up the resources
			self.flush()
			self.conn.close()
			self.conn = None
			status = True
		except Exception as e:
			status = False
			error_message = e
		return status, error_message

	def write(self, cmd):
		status = False
		try:
			command = (cmd + chr(13)+chr(10)).encode()
			self.conn.sendall(command[:1024])
			status = True
		except socket.error as e:
			pass
		except Exception as e:
			pass
		return status
		
	def read(self):
		message = b""  # Initialize empty bytes object
		try:
			readable, _, _ = select.select([self.conn], [], [], self.timeout)
			if readable:
				while True:
					try:
						chunk = self.conn.recv(4096)
						if not chunk:  # Connection closed by peer
							break
						message += chunk

						# Check if message ends with CRLF
						if message.endswith(b'\r\n'):
							break
						
						# Check if we have more data to read
						readable, _, _ = select.select([self.conn], [], [], 0.1)
						if not readable:
							break
							
					except socket.error as e:
						break
		except socket.timeout:
			pass
		except AttributeError:
			pass
		except Exception as e:
			print(f"Error reading from socket: {e}")
			
		return message if message else None

class Tcp(TcpWithoutControls):
	@validator('port', pre=True, always=True)
	def check_positive(cls, v):
		if v is not None and v < 1:
			raise ValueError('Value must be greater than or equal to 1')
		return v
	
	@validator('ip', pre=True, always=True)
	def check_format(cls, v):
		parts = v.split(".")
		if len(parts) == 4:
			for p in parts:
				if not p.isdigit():
					raise ValueError('Ip must contains only number and')
			return v
		else:
			raise ValueError('Ip no valid')

	@validator('timeout', pre=False, always=True)
	def check_timeout(cls, v):
		if v > 0:
			return v
		raise("Timeout must to be bigger than 0")

class ConfigConnection():
	connection: Union[SerialPort, Tcp, Connection] = Connection(**{})
	
	def getConnection(self):
		conn = self.connection.copy().dict()
		conn["connected"] = self.connection.is_open()
		if "conn" in conn:
			del conn["conn"]
		return conn

	def setConnection(self, connection: Union[SerialPort, Tcp]):
		self.deleteConnection()
		self.connection = connection
		self.connection.try_connection()
		conn = self.getConnection()
		return conn

	def deleteConnection(self):
		self.connection.close()
		self.connection = Connection(**{})
		return self.getConnection()

# ==== FUNZIONI RICHIAMBILI FUORI DALLA LIBRERIA ===============
def enable_serial_port(port_name):
	result = False
	message = None
	if is_linux():
		result, message = enable_serial_port_linux(port_name)
	elif is_windows():
		result, message = enable_serial_port_windows(port_name)
	return result, message

def list_serial_port():
	result = False
	message = None
	if is_linux():
		result, message = list_serial_port_linux()
	elif is_windows():
		result, message = list_serial_port_windows()
	return result, message

def serial_port_is_just_in_use(port_name):
	result = False
	message = None
	result, message = is_serial_port_in_use(port_name)
	return result, message

def exist_serial_port(port_name):
	result = False
	message = None
	if is_linux():
		result, message = exist_serial_port_linux(port_name)
	elif is_windows():
		result, message = exist_serial_port_windows(port_name)
	return result, message

import threading

def makedirs_with_timeout(path, timeout=5, exist_ok=True):
    """
    Crea directory con timeout per evitare blocchi su mount remoti.
    
    Args:
        path: Percorso della directory da creare
        timeout: Timeout in secondi (default: 5)
        exist_ok: Se True, non genera errore se la directory esiste
    
    Returns:
        bool: True se successo, False se timeout o errore
    """
    success = False
    error = None
    
    def _makedirs():
        try:
            os.makedirs(path, exist_ok=exist_ok)
            success = True
        except Exception as e:
            error = e
    
    thread = threading.Thread(target=_makedirs)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout)
    
    if thread.is_alive():
        error = f"Timeout durante creazione directory: {path}"
    
    if error:
        error = f"Errore creazione directory: {error}"
    
    return success, error

# Function to scan local directory and add existing files/directories to queue
def scan_local_dir(local_dir, sub_paths=None):
	"""
	Scan local directory and add existing files/directories to queue
	
	Args:
		local_dir: Base directory to scan
		sub_paths: Optional list of sub-paths to scan. If None, scans entire local_dir.
				   Example: ['reports', 'data/output'] will scan only those subdirectories
	"""
	pending_files = deque()
	
	# Se non sono specificati sub_paths, scansiona tutto local_dir
	if sub_paths is None:
		paths_to_scan = [local_dir]
	else:
		# Crea i path completi combinando local_dir con i sub_paths
		paths_to_scan = [os.path.join(local_dir, sub_path) for sub_path in sub_paths]
	
	for path in paths_to_scan:
		# Verifica che il path esista
		if not os.path.exists(path):
			continue
			
		for root, dirs, files in os.walk(path):
			for dir_name in dirs:
				dir_path = os.path.join(root, dir_name)
				pending_files.append(dir_path)
			for file_name in files:
				file_path = os.path.join(root, file_name)
				pending_files.append(file_path)
	
	return pending_files

# Function to mount the remote share
def mount_remote(ip, domain, share_name, username, password, local_dir, mount_point):
	umount_remote(mount_point)
	if is_linux():
		# Build params only if credentials are provided
		params_list = []
		if username:
			params_list.append(f'username={username}')
		if password:
			params_list.append(f'password={password}')
		if domain:
			params_list.append(f'domain={domain}')

		# If no credentials, use guest access
		if not params_list:
			params_list.append('guest')

		params = ','.join(params_list)
		cmd = [
			'mount', '-t', 'cifs', f'//{ip}/{share_name}', mount_point,
			'-o', params
		]
		try:
			os.chmod(local_dir, 0o777)  # Ensure directory is writable (adjust as needed)
		except Exception as e:
			pass
	elif is_windows():
		if username and password:
			cmd = [
				'net', 'use', mount_point, f'\\\\{ip}\\{share_name}',
				f'/user:{username}', password
			]
		else:
			# Mount without credentials for public shares
			cmd = [
				'net', 'use', mount_point, f'\\\\{ip}\\{share_name}'
			]
	try:
		subprocess.check_call(cmd)
		# Verify mount is not empty
		if not os.listdir(mount_point):
			return False
		return True
	except subprocess.CalledProcessError as e:
		lb_log.error(e)
		return False
	except OSError as e:
		lb_log.error(e)
		return False

def is_mounted(mount_point):
	if is_linux():
		return os.path.ismount(mount_point)
	elif is_windows():
		try:
			output = subprocess.check_output(['net', 'use'], text=True)
			return mount_point in output
		except subprocess.CalledProcessError:
			return False
	return False

def umount_remote(mount_point):
	if is_linux():
		if os.path.ismount(mount_point):
			try:
				subprocess.check_call(['umount', mount_point])
				return True
			except subprocess.CalledProcessError as e:
				lb_log.error(e)
				return False
		else:
			return True
	elif is_windows():
		try:
			subprocess.check_call(['net', 'use', mount_point])
			subprocess.check_call(['net', 'use', mount_point, '/delete'])
			return True
		except subprocess.CalledProcessError as e:
			lb_log.error(e)
			return False
	return False

def get_remote_connection_status(mount_point):
	"""
	Verifica lo stato della connessione alla cartella remota.

	Args:
		mount_point: Il punto di mount (Linux) o lettera di unità (Windows)

	Returns:
		dict: Dizionario con informazioni sulla connessione
				{
					'connected': bool,
					'mount_point': str,
					'remote_path': str o None,
					'status': str
				}
	"""
	connected = False
	remote_path = None,
	status = 'disconnected'
	
	if is_linux():
		# Verifica se il mount point è montato
		if os.path.ismount(mount_point):
			connected = True
			status = 'connected'
			
			# Ottieni informazioni dettagliate dal file /proc/mounts
			try:
				with open('/proc/mounts', 'r') as f:
					for line in f:
						parts = line.split()
						if len(parts) >= 2 and parts[1] == mount_point:
							remote_path = parts[0]
							break
			except Exception as e:
				lb_log.error(f"Errore lettura /proc/mounts: {e}")
		else:
			status = 'not mounted'
			
	elif is_windows():
		try:
			# Esegui comando 'net use' per vedere le connessioni attive
			output = subprocess.check_output(['net', 'use'], text=True)
			
			for line in output.split('\n'):
				if mount_point in line:
					connected = True
					status = 'connected'
					
					# Estrai il percorso remoto dalla riga
					parts = line.split()
					for part in parts:
						if part.startswith('\\\\'):
							remote_path = part
							break
					break
			else:
				status = 'not connected'
				
		except subprocess.CalledProcessError as e:
			lb_log.error(f"Errore esecuzione 'net use': {e}")
			status = 'error checking status'

	return connected, remote_path, status

# Function to copy a file or directory to remote
def copy_to_remote(file_path, local_dir, mount_point, sub_path):
	# Calculate relative path from local_dir
	rel_path = os.path.relpath(file_path, local_dir)
	# Normalize paths for comparison
	norm_sub_path = os.path.normpath(sub_path).replace('\\', '/')
	norm_rel_path = os.path.normpath(rel_path).replace('\\', '/')
	# Remove sub_path from rel_path if it exists to avoid duplication
	if norm_sub_path and norm_rel_path.startswith(norm_sub_path + '/'):
		rel_path = rel_path[len(sub_path) + 1:]
	elif norm_sub_path and norm_rel_path == norm_sub_path:
		if os.path.isdir(file_path):
			# Copy contents of the folder to the remote sub_path
			for child in os.listdir(file_path):
				child_path = os.path.join(file_path, child)
				remote_child_path = os.path.join(mount_point, sub_path, child)
				remote_child_dir = os.path.dirname(remote_child_path)
				os.makedirs(remote_child_dir, exist_ok=True)
				if os.path.isdir(child_path):
					shutil.copytree(child_path, remote_child_path, dirs_exist_ok=True)
				else:
					shutil.copy(child_path, remote_child_path)
			return True
		else:
			rel_path = os.path.basename(file_path)
	# Construct remote path
	remote_path = os.path.join(mount_point, sub_path, rel_path) if rel_path else os.path.join(mount_point, sub_path, os.path.basename(file_path))
	remote_path = os.path.normpath(remote_path)  # Normalize path to handle separators
	remote_dir = os.path.dirname(remote_path)
	# os.makedirs(remote_dir, exist_ok=True)
	makedirs_with_timeout(remote_dir, timeout=5, exist_ok=True)
	try:
		if os.path.isdir(file_path):
			shutil.copytree(file_path, remote_path, dirs_exist_ok=True)
		else:
			shutil.copy(file_path, remote_path)
		return True
	except IOError as e:
		return False
# ==============================================================

# ==== FUNZIONI RICHIAMABILI DENTRO LA LIBRERIA ================
# Funzione per salvare le configurazioni in un file JSON specificato.
# Questa funzione scrive le configurazioni memorizzate nelle variabili globali g_config
# in un file JSON e aggiorna il timestamp dell'ultima modifica del file di configurazione.
def is_linux():
	"""
	Funzione per controllare se il sistema operativo è Linux.

	Restituisce:
		True se il sistema operativo è Linux, False altrimenti.
	"""
	return platform.system().lower() == "linux"

def is_windows():
	"""
	Funzione per controllare se il sistema operativo è Windows.

	Restituisce:
		True se il sistema operativo è Windows, False altrimenti.
	"""
	return platform.system().lower() == "windows"

def enable_serial_port_linux(port_name):
	"""
	Funzione per abilitare la porta seriale in lettura e scrittura per tutti gli utenti.
	"""

	try:
		# Controlla se il file esiste
		if not os.path.exists(port_name):
			message = "Errore: La porta seriale " + port_name + " non esiste."
			return False, message

		# Modifica i permessi del file
		os.chmod(port_name, 0o666)

		# Controlla se i permessi sono stati modificati correttamente
		if not os.path.exists(port_name) or not os.access(port_name, os.W_OK):
			message = "Errore: Impossibile modificare i permessi del file."
			return False, message

		message = "Porta seriale " + port_name + " abilitata correttamente."
		return True, message
	except Exception as e:
		return False, e

def enable_serial_port_windows(port_name):
	try:
		# Validate port name
		if not isinstance(port_name, str):
			return False, f"Invalid port name type: {type(port_name)}"
		
		# Validate port name format
		if not port_name.startswith("COM") or not port_name[3:].isdigit():
			return False, f"Invalid serial port format: {port_name}"

		# Use subprocess to modify port permissions
		try:
			# Use icacls to grant full access to everyone
			result = subprocess.run(
				["icacls", port_name, "/grant", "Everyone:(OI)(CI)F"], 
				capture_output=True, 
				text=True, 
				check=True
			)
		except subprocess.CalledProcessError as perm_error:
			lb_log.error(perm_error)
			lb_log.error(f"Permission modification failed: {perm_error}")
			return False, f"Failed to modify port permissions: {perm_error.stderr}"
		except FileNotFoundError as e:
			lb_log.error(e)
			lb_log.error("icacls command not found")
			return False, "System utility icacls not found"

		# Log successful permission modification
		return True, f"Serial port {port_name} enabled successfully"

	except Exception as e:
		lb_log.error(f"Unexpected error enabling port {port_name}: {e}")
		return False, f"Unexpected error enabling port: {str(e)}"


def is_serial_port_in_use(serial_port_name):
	"""
	Controlla se la porta seriale è in uso provando ad aprirla in scrittura.
	"""
	try:
		port_handle = open(serial_port_name, 'w')
		port_handle.close()
		message = f"Port {serial_port_name} is not in use"
		return False, message
	except PermissionError:
		message = f"Port {serial_port_name} is in use"
		return True, message
	except Exception as e:
		message = f"Error checking port {serial_port_name}: {e}"
		return False, message

def list_serial_port_linux():
	try:
		ports = serial.tools.list_ports.comports()
		serial_ports = []
		# Itera su ogni porta trovata
		for port_info in sorted(ports):	
			port_data = {
				"port": port_info.device,
				"using": is_serial_port_in_use(port_info.device)
			}
			serial_ports.append(port_data)
		return True, serial_ports
	except Exception as e:
		return False, e

def list_serial_port_windows():
	try:
		ports = serial.tools.list_ports.comports()
		serial_ports = []
		# Itera su ogni porta trovata
		for port_info in sorted(ports):
			port_data = {
				"port": port_info.device,
				"using": is_serial_port_in_use(port_info.device)
			}
			serial_ports.append(port_data)
		return True, serial_ports
	except Exception as e:
		return False, e

def exist_serial_port_linux(port_name):
	try:
		# Controlla se il file esiste
		if not os.path.exists(port_name):
			message = "Errore: La porta seriale " + port_name + " non esiste."
			return False, message
		return True, None
	except Exception as e:
		return False, e

def exist_serial_port_windows(port_name):
	try:
		# Percorso del registro che contiene le informazioni sulle porte COM
		registry_path = r"HARDWARE\DEVICEMAP\SERIALCOMM"
		
		# Accede alla chiave del registro delle porte seriali
		reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path)

		# Ottieni il numero di voci presenti nella chiave del registro
		num_entries = winreg.QueryInfoKey(reg_key)[1]
		
		# Controlla se la porta cercata è presente nel registro
		for i in range(num_entries):
			entry_name, entry_value, _ = winreg.EnumValue(reg_key, i)
			if entry_value == port_name:  # Verifica se il valore corrisponde al nome della porta
				return True, None  # La porta esiste

		# Se la porta non è trovata nel registro, restituisce False
		return False, f"Port {port_name} does not exist."
	
	except Exception as e:
		return False, f"Error checking serial port {port_name}: {str(e)}"
# ==============================================================