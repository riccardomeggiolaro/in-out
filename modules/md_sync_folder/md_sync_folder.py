import libs.lb_log as lb_log
import libs.lb_config as lb_config
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import libs.lb_system as lb_system
from modules.md_sync_folder.gloabls import pending_files
from modules.md_sync_folder.dto import SyncFolderDTO
from modules.md_sync_folder.protocol_handlers import create_protocol_handler, ProtocolHandler
from libs.lb_utils import createThread, startThread

name_module = "md_sync_folder"

def init():
	global module_sync_folder
	lb_log.info("init")
	module_sync_folder = ModuleSyncFolder()
	thread = createThread(module_sync_folder.start)
	startThread(thread=thread)
	lb_log.info("end")

def start():
	lb_log.info("start")
	lb_log.info("end")

def stop():
	pass

# Watchdog handler for file and directory creations
class FileHandler(FileSystemEventHandler):
	def __init__(self, local_dir, sub_paths=None):
		super().__init__()
		self.local_dir = local_dir
		self.sub_paths = sub_paths
		# Crea i path completi per il filtro
		if sub_paths:
			self.allowed_paths = [os.path.join(local_dir, sp) for sp in sub_paths]
		else:
			self.allowed_paths = None
	
	def _is_path_allowed(self, path):
		"""Controlla se il path è in uno dei sub_paths consentiti"""
		if self.allowed_paths is None:
			return True  # Se non ci sono filtri, accetta tutto
		
		# Verifica se il path inizia con uno dei path consentiti
		for allowed_path in self.allowed_paths:
			if path.startswith(allowed_path):
				return True
		return False
	
	def on_created(self, event):
		# Filtra solo i path consentiti
		if self._is_path_allowed(event.src_path):
			pending_files.append(event.src_path)
			lb_log.warning(event.src_path)

class ModuleSyncFolder:
	def __init__(self):
		self.observer = None
		self.config = SyncFolderDTO(**lb_config.g_config["app_api"]["sync_folder"]["remote_folder"]) if lb_config.g_config["app_api"]["sync_folder"]["remote_folder"] else None
		self.local_dir = lb_config.g_config["app_api"]["sync_folder"]["local_dir"]
		self.mount_point = lb_config.g_config["app_api"]["sync_folder"]["mount_point"]
		self.sub_paths = lb_config.g_config["app_api"]["sync_folder"]["sub_paths"]
		self.protocol_handler: ProtocolHandler = None
		
	def create_remote_connection(self, config: SyncFolderDTO, local_dir: str, mount_point: str):
		# Disconnect old protocol handler if exists
		if self.protocol_handler:
			try:
				self.protocol_handler.disconnect()
			except:
				pass

		# Create new protocol handler based on config
		try:
			self.protocol_handler = create_protocol_handler(config, local_dir, mount_point)
			connected = self.protocol_handler.connect()
		except Exception as e:
			lb_log.error(f"Failed to create protocol handler: {e}")
			return False

		self.config = config
		self.local_dir = local_dir
		self.mount_point = mount_point

		# Scan existing files and add to pending queue
		files = lb_system.scan_local_dir(local_dir, self.sub_paths)
		for file in files:
			pending_files.append(file)

		# Start file observer
		self.create_observer(local_dir)
		return connected

	def delete_remote_connection(self):
		# Disconnect protocol handler
		if self.protocol_handler:
			try:
				self.protocol_handler.disconnect()
			except Exception as e:
				lb_log.error(f"Error disconnecting protocol handler: {e}")
			self.protocol_handler = None

		self.config = None
		self.local_dir = None
		self.mount_point = None

		# Stop file observer
		if self.observer and self.observer.is_alive():
			self.observer.stop()
			self.observer.join()
			self.observer = None

	def test_connection(self):
		if self.protocol_handler:
			return self.protocol_handler.get_connection_status()
		return False, None, "no connection configured"

	def create_observer(self, local_dir):
		if self.observer and self.observer.is_alive():
			self.observer.stop()
			self.observer.join()
		self.observer = Observer()
		# Passa sub_paths al FileHandler per filtrare gli eventi
		self.observer.schedule(FileHandler(local_dir, self.sub_paths), local_dir, recursive=True)
		self.observer.start()
  
	def start(self):
		# Lista delle estensioni da escludere
		excluded_extensions = ['.db', '.db-journal']

		while lb_config.g_enabled:
			if pending_files and self.protocol_handler:
				file_path = pending_files[0]

				# Ottieni l'estensione del file
				file_extension = os.path.splitext(file_path)[1].lower()

				# Controlla se l'estensione è nella lista delle escluse
				if file_extension in excluded_extensions:
					pending_files.popleft()
					continue

				# Check if connection is active
				if self.protocol_handler.is_connected():
					# Calculate remote path based on protocol
					if hasattr(self.protocol_handler, 'get_remote_path'):
						remote_path = self.protocol_handler.get_remote_path(file_path, self.local_dir, self.config.sub_path)
					else:
						# Fallback for protocols without get_remote_path
						rel_path = os.path.relpath(file_path, self.local_dir)
						remote_path = os.path.join(self.config.sub_path, rel_path) if self.config.sub_path else rel_path

					# Copy file/directory to remote
					success = False
					if os.path.isdir(file_path):
						success = self.protocol_handler.copy_directory(file_path, remote_path)
					else:
						success = self.protocol_handler.copy_file(file_path, remote_path)

					if success:
						try:
							# Only remove files, not directories
							if not os.path.isdir(file_path):
								os.remove(file_path)
								lb_log.info(f"Removed file {file_path} from local directory")
							else:
								lb_log.info(f"Keeping directory {file_path} in local directory")
							pending_files.popleft()
						except Exception as e:
							lb_log.error(f"Failed to remove {file_path}: {e}")
					else:
						# Copy failed, wait before retry
						time.sleep(1)
				else:
					# Connection lost, try to reconnect
					if self.config:
						lb_log.warning("Connection lost, attempting to reconnect...")
						self.create_remote_connection(config=self.config, local_dir=self.local_dir, mount_point=self.mount_point)
					time.sleep(1)
			else:
				# No files or no connection configured
				if self.config and self.protocol_handler and not self.protocol_handler.is_connected():
					lb_log.warning("No active connection, attempting to connect...")
					self.create_remote_connection(config=self.config, local_dir=self.local_dir, mount_point=self.mount_point)
				time.sleep(1)