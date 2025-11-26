# ==== LIBRERIE DA IMPORTARE ===================================
import libs.lb_log as lb_log
import libs.lb_config as lb_config
import time
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import libs.lb_system as lb_system
from modules.md_sync_folder.gloabls import pending_files
from modules.md_sync_folder.dto import SyncFolderDTO
from libs.lb_utils import createThread, startThread
# ==============================================================

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
	def on_created(self, event):
		lb_log.info(f"Watchdog: New file detected: {event.src_path}")
		pending_files.append(event.src_path)
		lb_log.info(f"Watchdog: Added to queue. Queue size: {len(pending_files)}")

class ModuleSyncFolder:
	def __init__(self):
		self.observer = None
		self.config = SyncFolderDTO(**lb_config.g_config["app_api"]["sync_folder"]["remote_folder"]) if lb_config.g_config["app_api"]["sync_folder"]["remote_folder"] else None
		self.local_dir = lb_config.g_config["app_api"]["sync_folder"]["local_dir"]
		self.mount_point = lb_config.g_config["app_api"]["sync_folder"]["mount_point"]
		# lb_log.warning(self.config)
		# lb_log.warning(self.local_dir)
		# lb_log.warning(self.mount_point)
		
	def create_remote_connection(self, config: SyncFolderDTO, local_dir: str, mount_point: str):
		lb_log.info(f"Creating remote connection: Protocol={config.protocol}, IP={config.ip}, Port={config.port}")

		# Clean up existing connection if protocol is samba
		if self.mount_point and self.mount_point != mount_point:
			lb_system.umount_remote(self.mount_point)

		mounted = False

		# Handle connection based on protocol
		if config.protocol == 'samba':
			lb_log.info(f"Mounting Samba share: //{config.ip}/{config.share_name}")
			mounted = lb_system.mount_remote(config.ip, config.domain, config.share_name, config.username, config.password, local_dir, mount_point)
		elif config.protocol == 'ftp':
			# Test FTP connection
			lb_log.info(f"Testing FTP connection to {config.ip}:{config.port}")
			connected, _, _ = lb_system.test_ftp_connection(config.ip, config.port, config.username, config.password)
			mounted = connected
		elif config.protocol == 'sftp':
			# Test SFTP connection
			lb_log.info(f"Testing SFTP connection to {config.ip}:{config.port}")
			connected, _, _ = lb_system.test_sftp_connection(config.ip, config.port, config.username, config.password)
			mounted = connected

		self.config = config
		self.local_dir = local_dir
		self.mount_point = mount_point if config.protocol == 'samba' else None

		# Scan local directory for existing files
		files = lb_system.scan_local_dir(local_dir)
		lb_log.info(f"Found {len(files)} existing files in {local_dir}")
		for file in files:
			pending_files.append(file)

		self.create_observer(local_dir)
		lb_log.info(f"Remote connection setup complete. Mounted: {mounted}")
		return mounted

	def delete_remote_connection(self):
		if self.mount_point and lb_system.is_mounted(self.mount_point):
			lb_system.umount_remote(self.mount_point)
		self.config = None
		self.local_dir = None
		self.mount_point = None
		if self.observer and self.observer.is_alive():
			self.observer.stop()
			self.observer.join()
			self.observer = None

	def test_connection(self):
		if not self.config:
			return False, None, 'no configuration'

		if self.config.protocol == 'samba':
			return lb_system.get_remote_connection_status(self.mount_point)
		elif self.config.protocol == 'ftp':
			return lb_system.test_ftp_connection(self.config.ip, self.config.port, self.config.username, self.config.password)
		elif self.config.protocol == 'sftp':
			return lb_system.test_sftp_connection(self.config.ip, self.config.port, self.config.username, self.config.password)

		return False, None, 'unknown protocol'

	def create_observer(self, local_dir):
		if self.observer and self.observer.is_alive():
			lb_log.info(f"Stopping existing observer for {local_dir}")
			self.observer.stop()
			self.observer.join()
		self.observer = Observer()
		self.observer.schedule(FileHandler(), local_dir, recursive=True)
		self.observer.start()
		lb_log.info(f"Watchdog observer started for directory: {local_dir}")
  
	def start(self):
		# lb_log.info("Starting sync folder module")
		
		# Lista delle estensioni da escludere (aggiungi quelle che ti servono)
		excluded_extensions = ['.db', '.db-journal']  # Modifica secondo necessità
		
		while lb_config.g_enabled:
			if pending_files and self.config:
				file_path = pending_files[0]
				lb_log.info(f"Processing file from queue: {file_path} (Protocol: {self.config.protocol})")

				# Ottieni l'estensione del file
				file_extension = os.path.splitext(file_path)[1].lower()

				# Controlla se l'estensione è nella lista delle escluse
				if file_extension in excluded_extensions:
					lb_log.info(f"Skipping file {file_path} with excluded extension {file_extension}")
					pending_files.popleft()
					continue

				copy_success = False

				# Handle copy based on protocol
				if self.config.protocol == 'samba':
					if lb_system.is_mounted(self.mount_point):
						copy_success = lb_system.copy_to_remote(file_path, self.local_dir, self.mount_point, self.config.sub_path)
					else:
						# Try to reconnect
						self.create_remote_connection(config=self.config, local_dir=self.local_dir, mount_point=self.mount_point)
						time.sleep(1)
						continue
				elif self.config.protocol == 'ftp':
					copy_success = lb_system.copy_to_ftp(file_path, self.local_dir, self.config.ip, self.config.port, self.config.username, self.config.password, self.config.sub_path)
				elif self.config.protocol == 'sftp':
					copy_success = lb_system.copy_to_sftp(file_path, self.local_dir, self.config.ip, self.config.port, self.config.username, self.config.password, self.config.sub_path)

				if copy_success:
					try:
						# Only remove files, not directories
						if not os.path.isdir(file_path):
							os.remove(file_path)
							lb_log.info(f"Successfully uploaded and removed file {file_path} from local directory")
						else:
							lb_log.info(f"Keeping directory {file_path} in local directory")
						pending_files.popleft()
						lb_log.info(f"Remaining files in queue: {len(pending_files)}")
					except Exception as e:
						lb_log.error(f"Failed to remove {file_path}: {e}")
						pending_files.popleft()
				else:
					lb_log.warning(f"Copy failed for {file_path}, retrying after delay")
					time.sleep(1)  # Retry after delay
			else:
				if self.config and self.config.protocol == 'samba' and self.mount_point and not lb_system.is_mounted(self.mount_point):
					self.create_remote_connection(config=self.config, local_dir=self.local_dir, mount_point=self.mount_point)
				time.sleep(1)  # Retry after delay