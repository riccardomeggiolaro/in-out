# ==============================================================
# 		GESTIONE SISTEMA				=
# ==============================================================

# ==== LIBRERIE DA IMPORTARE ===================================
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
try:
	import winreg
	import wmi
except ImportError:
	winreg = None
	wmi = None
# ==============================================================

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
		return status, error_message

	def flush(self):
		status = False
		error_message = None
		try:
			if isinstance(self.conn, serial.Serial) and self.conn.is_open:
				self.conn.flush()
				status = True
		except SerialException as e:
			error_message = e
			# lb_log.error(f"SerialException on flush: {error_message}")
		except AttributeError as e:
			error_message = e
			# lb_log.error(f"AttributeError on flush: {error_message}")
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
			lb_log.warning(f"Timeout: {v}")
			return v
		raise ValueError("Timeout must to be bigger than 0")

class TcpWithoutControls(Connection):
	ip: str
	port: int
	timeout: float

	conn: Optional[socket.socket] = None

	class Config:
		arbitrary_types_allowed = True

	def is_open(self):
		try:
			status = None
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
				sock.setblocking(False)
				sock.settimeout(self.timeout)
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
		try:
			self.conn = None
			self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.conn.setblocking(False)
			self.conn.settimeout(self.timeout)
			self.conn.connect((self.ip, self.port))
		except Exception as e:
			status = False
			error_message = e
		return status, error_message

	def flush(self):
		status = True
		error_message = None
		try:
			buffer = b""			
			# Ricevi i dati finché ce ne sono
			while True:
				try:
					data = self.conn.recv(5000)  # Ricevi fino a 1024 byte alla volta
					if not data:
						break  # Se non ci sono più dati nel buffer, esci dal ciclo
					# Accumula i dati ricevuti nel buffer
					buffer += data
				except BlockingIOError:
					break
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
			self.conn.close()
			status = True
			status = False
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
		return status
		
	def read(self):
		message = None
		try:
			readable, _, _ = select.select([self.conn], [], [], self.timeout)
			if readable:
				message = self.conn.recv(1024)
		except socket.timeout as e:
			pass
		except AttributeError as e:
			pass
		return message

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

# ==== FUNZIONE RICHIAMBILI FUORI DALLA LIBRERIA ===============
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
	if is_linux():
		result, message = serial_port_is_just_in_use_linux(port_name)
	elif is_windows():
		result, message = serial_port_is_just_in_use_windows(port_name)
	return result, message

def exist_serial_port(port_name):
	result = False
	message = None
	if is_linux():
		result, message = exist_serial_port_linux(port_name)
	elif is_windows():
		result, message = exist_serial_port_windows(port_name)
	return result, message
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
		lb_log.info(f"Serial port {port_name} enabled successfully")
		return True, f"Serial port {port_name} enabled successfully"

	except Exception as e:
		lb_log.error(f"Unexpected error enabling port {port_name}: {e}")
		return False, f"Unexpected error enabling port: {str(e)}"


def is_port_in_use(port):
    if os.name == 'nt':  # Windows
        try:
            port_handle = open(port, 'w')
            port_handle.close()
            return False  # non in uso
        except PermissionError:  # se non possiamo accedere in scrittura, è in uso
            return True
    else:  # Linux
        try:
            # Usa lsof per vedere se qualche processo sta usando la porta
            cmd = ['lsof', port]
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            return True  # se lsof trova qualcosa, la porta è in uso
        except subprocess.CalledProcessError:  # se lsof non trova nulla
            return False
        except FileNotFoundError:  # se lsof non è installato
            try:
                # Fallback: prova ad accedere al device in scrittura
                port_handle = open(port, 'w')
                port_handle.close()
                return False
            except PermissionError:
                return True

def list_serial_port_linux():
	try:
		ports = serial.tools.list_ports.comports()
		serial_ports = []
        # Itera su ogni porta trovata
		for port_info in sorted(ports):	
			port_data = {
                "port": port_info.device,
                "using": is_port_in_use(port_info.device)
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
                "using": is_port_in_use(port_info.device)
            }
			serial_ports.append(port_data)
		return True, serial_ports
	except Exception as e:
		return False, e

def serial_port_is_just_in_use_linux(port_name):
	"""
	Checks if the specified serial port is in use using `fuser`.

	Args:
		port_name: The serial port to check (e.g., "/dev/ttyS0").

	Returns:
		(bool, str): Tuple where the first value is True if the port is in use,
					 and the second value is the appropriate message.
	"""
	try:
		# Execute fuser with options to check serial port usage
		subprocess.run(["fuser", "-s", port_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
		# If fuser does not raise an error, the port is in use
		message = f"Port {port_name} is in use"
		return True, message
	except subprocess.CalledProcessError:
		# If fuser raises an exception, the port is not in use
		message = f"Port {port_name} is not in use"
		return False, message
	except FileNotFoundError:
		# Handle case where `fuser` is not available
		message = "'fuser' command not found. Please install it to check port usage."
		return False, message

def serial_port_is_just_in_use_windows(port_name):
    """
    Funzione per verificare se una porta seriale è in uso utilizzando pyserial.
    Tenta di aprire la porta in modalità esclusiva e gestisce eventuali errori.
    """
    try:
        # Proviamo ad aprire la porta in modalità esclusiva per vedere se è in uso
        with serial.Serial(port_name, timeout=1) as ser:
            return False, f"Port {port_name} is available for use."  # Se non ci sono errori, la porta è disponibile
    except serial.SerialException as e:
        # Se la porta è in uso, solitamente si ottiene un errore di tipo SerialException
        if 'could not open port' in str(e):
            return True, f"Port {port_name} is currently in use or could not be opened: {e}"  # La porta è in uso
        else:
            return False, f"Error opening port {port_name}: {e}"  # Un altro tipo di errore, la porta potrebbe non essere disponibile
    except Exception as e:
        return False, f"Unexpected error while checking port {port_name}: {str(e)}"  # Gestiamo eventuali errori imprevisti

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