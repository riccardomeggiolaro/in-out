# ==============================================================
# = Module......: md_dgt1					   =
# = Description.: Interfaccia di pesatura con più terminali =
# = Author......: Riccardo Meggiolaro				   =
# = Last rev....: 0.0002					   =
# ==============================================================

# ==== LIBRERIE DA IMPORTARE ===================================
import libs.lb_log as lb_log
import libs.lb_config as lb_config
import time
import os
import time
import shutil
import subprocess
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
	lb_log.info("end")

def start():
	lb_log.info("start")
	lb_log.error("ihbdfiwfbwefiwyufwiuvy")
	module_sync_folder.start()
	lb_log.info("end")

def stop():
	pass

# Watchdog handler for file and directory creations
class FileHandler(FileSystemEventHandler):
	def on_created(event):
		pending_files.append(event.src_path)

class ModuleSyncFolder:
	def __init__(self):
		self.observer = None
		self.config = None
		self.local_dir = None
		self.mount_point = None
		self.create_remote_connection(config=SyncFolderDTO(**lb_config.g_config["app_api"]["sync_folder"]["remote_folder"]), local_dir=lb_config.g_config["app_api"]["sync_folder"]["local_dir"], mount_point=lb_config.g_config["app_api"]["sync_folder"]["mount_point"])
		self.start()
		
	def create_remote_connection(self, config: SyncFolderDTO, local_dir: str, mount_point: str):
		mounted = lb_system.mount_remote(config.ip, config.share_name, config.username, config.password, local_dir, mount_point)
		if mounted:
			self.config = config
			self.local_dir = local_dir
			self.mount_point = mount_point
			files = lb_system.scan_local_dir(local_dir)
			for file in files:
				pending_files.append(file)
			self.create_observer(local_dir)
		return mounted

	def create_observer(self, local_dir):
		if self.observer and self.observer.is_alive():
			self.observer.stop()
			self.observer.join()
		self.observer = Observer()
		self.observer.schedule(FileHandler(), local_dir, recursive=True)
		self.observer.start()
  
	def start(self):
		lb_log.error("ijjbefiuwefbwiefbu")
		while lb_config.g_enabled:
			if pending_files and self.mount_point:
				file_path = pending_files[0]
				if lb_system.is_mounted(self.mount_point) and lb_system.copy_to_remote(file_path, self.local_dir, self.mount_point, self.config.sub_path):
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
					lb_log.warning(f"Retrying {file_path} after delay")
					time.sleep(1)  # Retry after delay
			else:
				time.sleep(1)  # Idle wait