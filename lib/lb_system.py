# ==============================================================
# 		GESTIONE SISTEMA				=
# ==============================================================

# ==== LIBRERIE DA IMPORTARE ===================================
import os
import lib.lb_log as lb_log
import platform
import subprocess
import serial
import serial.tools.list_ports
from pydantic import BaseModel, validator
from serial import SerialException
import socket
from typing import Optional, Union
import select
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

class SerialPort(Connection):
	baudrate: int = 19200
	serial_port_name: str
	timeout: int = 1

	conn: Optional[serial.Serial] = None

	class Config:
		arbitrary_types_allowed = True

	@validator('baudrate', 'timeout', pre=True, always=True)
	def check_positive(cls, v):
		if v is not None and v < 1:
			raise ValueError('Value must be greater than or equal to 1')
		return v

	@validator('serial_port_name', pre=True, always=True)
	def check_format(cls, v):
		if v is not None:
			result, message = exist_serial_port(v)
			if result is False:
				raise ValueError(message)
			result, message = enable_serial_port(v)
			if result is False:
				raise ValueError(message)
			result, message = serial_port_not_just_in_use(v)
			if result is False:
				raise ValueError(message)
		return v

	def try_connection(self):
		status = False
		error_message = None
		try:
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
		return status

	def read(self):
		message = None
		try:
			if isinstance(self.conn, serial.Serial) and self.conn.is_open:
				message = self.conn.readline()
		except TimeoutError as e:
			pass
		except SerialException as e:
			pass
		except AttributeError as e:
			pass
		return message

class Tcp(Connection):
	ip: str
	port: int
	timeout: float
 
	conn: Optional[socket.socket] = None

	class Config:
		arbitrary_types_allowed = True

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
		return self.getConnection()

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

def serial_port_not_just_in_use(port_name):
	result = False
	message = None
	if is_linux():
		result, message = serial_port_not_just_in_use_linux(port_name)
	elif is_windows():
		result, message = serial_port_not_just_in_use_windows(port_name)
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
		import winreg

		"""
		Funzione per abilitare la porta seriale specificata in lettura e scrittura su Windows.

		Args:
			port_name: Nome della porta seriale (es. "COM1").
		"""

		# Controlla se la porta seriale è valida
		if not port_name.startswith("COM"):
			message = f"Errore: Porta seriale non valida: {port_name}"
			return False, message

		# Aprire la chiave del Registro di sistema
		key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
							"SYSTEM\\CurrentControlSet\\Services\\Serial\\Parameters",
							0, winreg.KEY_WRITE)

		# Impostare il valore DWORD "PortName"
		winreg.SetValueEx(key, "PortName", 0, winreg.REG_SZ, port_name)

		# Impostare il valore DWORD "BaudRate" (opzionale)
		winreg.SetValueEx(key, "BaudRate", 0, winreg.REG_DWORD, 9600)

		# Impostare il valore DWORD "Parity" (opzionale)
		winreg.SetValueEx(key, "Parity", 0, winreg.REG_DWORD, 0)

		# Impostare il valore DWORD "DataBits" (opzionale)
		winreg.SetValueEx(key, "DataBits", 0, winreg.REG_DWORD, 8)

		# Impostare il valore DWORD "StopBits" (opzionale)
		winreg.SetValueEx(key, "StopBits", 0, winreg.REG_DWORD, 1)

		# Chiudere la chiave del Registro di sistema
		winreg.CloseKey(key)

		# Riavviare il servizio "Serial"
		os.system("net stop Serial")
		os.system("net start Serial")

		message = f"Porta seriale {port_name} abilitata correttamente."
		return True, message
	except Exception as e:
		return False, e

def list_serial_port_linux():
	try:
		ports = serial.tools.list_ports.comports()
		serial_ports = []
		for port, desc, hwid in sorted(ports):
			serial_ports.append(port)
		return True, serial_ports
	except Exception as e:
		return False, e

def list_serial_port_windows():
	try:
		ports = serial.tools.list_ports.comports()
		serial_ports = []
		for port, desc, hwid in sorted(ports):
			serial_ports.append(port)
		return True, serial_ports
	except Exception as e:
		return False, e

def serial_port_not_just_in_use_linux(port_name):
	"""
	Checks if the specified serial port is in use using `fuser`.

	Args:
		port: The serial port to check (e.g., "/dev/ttyS0").

	Returns:
		True if the port is in use, False otherwise.
	"""
	try:
		# Execute fuser with options to check serial port usage
		subprocess.run(["fuser", "-s", port_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
		# Non-zero return code from fuser indicates port usage
		message = f"Port {port_name} is just in use"
		return False, message
	except subprocess.CalledProcessError:
		# Handle potential errors (e.g., fuser not found)
		return True, None

def serial_port_not_just_in_use_windows(port_name):
	try:
		return True, None
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
		return True, None
	except Exception as e:
		return False, e
# ==============================================================