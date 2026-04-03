import copy
import inspect
import libs.lb_log as lb_log
import libs.lb_config as lb_config
import time
import serial
import binascii
from typing import Callable

class ApromixRfidSerial:
	NAME = "apromix"

	def __init__(self):
		self.serial = None
		self.status = 301  # 301 = disconnected, 305 = connected
		self.last_cardcode = ""
		self.callback_cardcode = None
		self.config = {
			"connection": {
				"serial_port_name": None,
				"baudrate": None,
				"timeout": None
			},
			"setup": {}
		}

	def initialize(self, connection, setup) -> bool:
		lb_log.info("initialize apromix_rfid_serial")
		try:
			if isinstance(self.serial, serial.Serial) and self.serial.is_open:
				self.serial.close()
			self.serial = None
			self.serial = serial.Serial(
				connection.serial_port_name,
				baudrate=connection.baudrate,
				timeout=connection.timeout
			)
			if self._wait_for_serial_ready():
				self.config = {
					"connection": {
						"serial_port_name": connection.serial_port_name,
						"baudrate": connection.baudrate,
						"timeout": connection.timeout
					},
					"setup": setup.dict() if hasattr(setup, "dict") else {}
				}
				self.status = 305
				lb_log.info("apromix_rfid_serial initialized successfully")
			else:
				lb_log.error("Serial port not ready after initialization.")
				self.status = 301
		except serial.SerialException as e:
			lb_log.error(f"SerialException: {e}")
			self.status = 301
		except Exception as e:
			lb_log.error(f"Exception: {e}")
			self.status = 301
		return self.status == 305

	def set_action(self, cb_cardcode: Callable[[str], any] = None):
		try:
			if callable(cb_cardcode) and len(inspect.signature(cb_cardcode).parameters) == 1:
				self.callback_cardcode = cb_cardcode
		except Exception as e:
			lb_log.error(e)

	def get_config(self) -> dict:
		data = copy.copy(self.config)
		data["status"] = self.status
		return data

	def is_initialized(self) -> bool:
		return self.status == 305

	def delete_config(self) -> bool:
		try:
			self.status = 301
			time.sleep(0.1)
			if isinstance(self.serial, serial.Serial) and self.serial.is_open:
				self.serial.flush()
				self.serial.close()
			self.serial = None
			self.config = {
				"connection": {
					"serial_port_name": None,
					"baudrate": None,
					"timeout": None
				},
				"setup": {}
			}
			return True
		except Exception:
			return False

	def start(self, enabled_fn):
		lb_log.info("start apromix_rfid_serial")
		while enabled_fn() and lb_config.g_enabled:
			if self.status == 305:
				try:
					data = self.serial.readline().strip()
					if data:
						hex_string = binascii.hexlify(data).decode("UTF-8")
						length = len(hex_string)
						# Card present: 14 hex chars = 7 bytes, validate BCC checksum
						if length == 14:
							byte_sequence = bytes.fromhex(hex_string[0:-2])
							checksum = hex_string[-2:]
							bcc = (-sum(byte_sequence)) % 256
							bcc_hex = format(bcc, "02X")
							cardcode = hex_string[2:-2]
							if bcc_hex.lower() == checksum.lower():
								if cardcode != self.last_cardcode:
									self.last_cardcode = cardcode
									lb_log.info(f"Card read: {cardcode}")
									if callable(self.callback_cardcode):
										self.callback_cardcode(cardcode)
							else:
								lb_log.error(f"Incorrect checksum for card {cardcode}")
						# Card removed: 18 hex chars ending in ff01
						elif length == 18:
							if hex_string[-4:] == "ff01":
								self.last_cardcode = ""
						# Card removed: 4 hex chars ff01
						elif length == 4:
							if hex_string == "ff01":
								self.last_cardcode = ""
				except Exception as e:
					lb_log.error(f"Error reading serial: {e}")
			time.sleep(0.1)
		if isinstance(self.serial, serial.Serial) and self.serial.is_open:
			self.serial.close()
		lb_log.info("end apromix_rfid_serial")

	def _wait_for_serial_ready(self, max_attempts=5, delay_seconds=1) -> bool:
		for _ in range(max_attempts):
			if isinstance(self.serial, serial.Serial) and self.serial.is_open:
				return True
			time.sleep(delay_seconds)
		return False
