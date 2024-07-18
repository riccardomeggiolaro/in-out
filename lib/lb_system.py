# ==============================================================
# 		GESTIONE SISTEMA				=
# ==============================================================

# ==== LIBRERIE DA IMPORTARE ===================================
import os
import lib.lb_log as lb_log
import platform
import subprocess
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
		return False, ConnectionError('Write: No connection set')

	def read(self):
		return False, None, ConnectionError('Read: No connection set')

	def decode_read(self, read):
		return False, None, ConnectionError('Decode read: No connection set')

	def is_open(self):
		return False, None, ConnectionError('Is open: No connection set')

class SerialPort(Connection):
	baudrate: int = 19200
	serial_port_name: str
	timeout: int = 1

	conn: Optional[socket.socket] = None

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
		status = True
		error_message = None
		try:
			if isinstance(self.conn, serial.Serial) and self.conn.is_open:
				self.conn.flush()
				self.conn.close()
			return serial.Serial(port=self.serial_port_name, baudrate=self.baudrate, timeout=self.timeout)
		except SerialException as e:
			status = False
			error_message = e
			# lb_log.error(f"SerialException on try connection: {error_message}")
		except AttributeError as e:
			status = False
			error_message = e
			# lb_log.error(f"AttributeError on try connection: {error_message}")
		except TypeError as e:
			status = False
			error_message = e
			# lb_log.error(f"TypeError on try connection: {error_message}")
		return status, error_message

	def flush(self):
		status = True
		error_message = None
		try:
			if isinstance(self.conn, serial.Serial) and self.conn.is_open:
				self.conn.flush()
		except SerialException as e:
			status = False
			error_message = e
			# lb_log.error(f"SerialException on flush: {error_message}")
		except AttributeError as e:
			status = False
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
			status = False
			error_message = e
			# lb_log.error(f"SerialException on close: {error_message}")
		except AttributeError as e:
			status = False
			error_message = e
			# lb_log.error(f"AttributeError on close: {error_message}")
		except TypeError as e:
			status = False
			error_message = e
			# lb_log.error(f"TypeError on close: {error_message}")
		return status, error_message

	def write(self, cmd):
		status = True
		error_message = None
		try:
			status = False
			if isinstance(self.conn, serial.Serial) and self.conn.is_open:
				command = (cmd + chr(13)+chr(10)).encode()
				self.conn.write(command)
			else:
				raise SerialException()
		except SerialException as e:
			status = False
			error_message = e
			# lb_log.error(f"SerialException on write: {error_message}")
		except AttributeError as e:
			status = False
			error_message = e
			# lb_log.error(f"AttributeError on write: {error_message}")
		except TypeError as e:
			status = False
			error_message = e
			# lb_log.error(f"TypeError on write: {error_message}")
		return status, error_message

	def read(self):
		status = True
		message = None
		error_message = None
		try:
			if isinstance(self.conn, serial.Serial) and self.conn.is_open:
				message = self.conn.readline()
			else:
				raise SerialException()
		except SerialException as e:
			status = False
			error_message = e
			# lb_log.error(f"SerialException on read: {error_message}")
		except AttributeError as e:
			status = False
			error_message = e
			# lb_log.error(f"AttributeError on read: {error_message}")
		except TypeError as e:
			status = False
			error_message = e
			# lb_log.error(f"TypeError on read: {error_message}")
		return status, message, error_message

	def decode_read(self, read):
		status = True
		message = None
		error_message = None
		try:
			message = read.decode('utf-8', errors='ignore').replace("\r\n", "").strip()
		except AttributeError as e:
			status = False
			error_message = e
			# lb_log.info(read)
			# lb_log.error(f"AttributeError on decode read: {error_message}")
		return status, message, error_message

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
			if isinstance(self.conn, socket.socket):
				# Use select to check if the socket is ready for reading
				readable, _, _ = select.select([self.conn], [], [], 0)
				if readable:
					# If the socket is ready for reading, attempt to read with MSG_PEEK
					data = self.conn.recv(1, socket.MSG_PEEK)
					if data == b'':
						return False
			return True
		except (socket.error, OSError):
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
		except socket.error as e:
			status = False
			error_message = f"Errore nella riconnessione {e}"
			lb_log.info(f"{error_message}")
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
			lb_log.info(e)
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
		status = True
		error_message = None
		try:
			status = False
			command = (cmd + chr(13)+chr(10)).encode()
			self.conn.sendall(command[:1024])
		except socket.error as e:
			status = False
			error_message = e
			lb_log.error(f"Socket error on write: {error_message}")
		return status, error_message
	
	def read(self):
		status = False
		message = None
		error_message = None
		try:
			message = self.conn.recv(1024)
			status = True
		except BlockingIOError as e:
			status = False
			error_message = e
			lb_log.info(f"Error on read: {e}")
		except socket.error as e:
			status = False
			error_message = e
			lb_log.info(f"Error on read: {e}")
			# lb_log.error(f"Socket error on write: {error_message}")
		return status, message, error_message

	def decode_read(self, read):
		status = True
		message = None
		error_message = None
		try:
			message = read.decode('utf-8', errors='ignore').replace("\r\n", "").strip()
		except AttributeError as e:
			status = False
			error_message = e
			# lb_log.info(read)
			# lb_log.error(f"AttributeError on decode read: {error_message}")
		return status, message, error_message

class ConfigConnection():
	connection: Union[SerialPort, Tcp, Connection] = Connection(**{})
	
	def getConnection(self):
		conn = self.connection.copy().dict()
		if "conn" in conn:
			del conn["conn"]
		return conn

	def setConnection(self, connection: Union[SerialPort, Tcp]):
		connected, message = False, None
		self.deleteConnection()
		self.connection = connection
		connected, message = self.connection.try_connection()
		conn = self.getConnection()
		return connected, conn, message

	def deleteConnection(self):
		status, message = self.connection.close()
		self.connection = Connection(**{})
		return status

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
            lb_log.info(message)
            return False, message

        # Modifica i permessi del file
        os.chmod(port_name, 0o666)

        # Controlla se i permessi sono stati modificati correttamente
        if not os.path.exists(port_name) or not os.access(port_name, os.W_OK):
            message = "Errore: Impossibile modificare i permessi del file."
            lb_log.info(message)
            return False, message

        message = "Porta seriale " + port_name + " abilitata correttamente."
        lb_log.info(message)
        return True, message
    except Exception as e:
        lb_log.error(e)
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
            lb_log.info(message)
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
        lb_log.info(message)
        return True, message
    except Exception as e:
        lb_log.error(e)
        return False, e

def list_serial_port_linux():
    try:
        ports = serial.tools.list_ports.comports()
        serial_ports = []
        for port, desc, hwid in sorted(ports):
            serial_ports.append(port)
        return True, serial_ports
    except Exception as e:
        lb_log.error(e)
        return False, e

def list_serial_port_windows():
    try:
        ports = serial.tools.list_ports.comports()
        serial_ports = []
        for port, desc, hwid in sorted(ports):
            serial_ports.append(port)
        return True, serial_ports
    except Exception as e:
        lb_log.error(e)
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
        lb_log.error(e)
        return False, e

def exist_serial_port_linux(port_name):
    try:
        # Controlla se il file esiste
        if not os.path.exists(port_name):
            message = "Errore: La porta seriale " + port_name + " non esiste."
            lb_log.info(message)
            return False, message
        return True, None
    except Exception as e:
        lb_log.error(e)
        return False, e

def exist_serial_port_windows(port_name):
    try:
        return True, None
    except Exception as e:
        lb_log.error(e)
        return False, e
# ==============================================================