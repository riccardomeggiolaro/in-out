# ssh_client = None
# if lb_config.g_config["app_api"]["ssh_client"]:
# 	ssh_client = lb_config.g_config["app_api"]["ssh_client"]
# 	ssh_client["local_port"] = lb_config.g_config["app_api"]["port"]
# 	ssh_client = createThread(ssh_tunnel, (SshClientConnection(**ssh_client),))
# 	startThread(ssh_client)

# ==============================================================
# = Module......: md_dgt1					   =
# = Description.: Interfaccia di pesatura con più terminali =
# = Author......: Riccardo Meggiolaro				   =
# = Last rev....: 0.0002					   =
# ==============================================================

# ==== LIBRERIE DA IMPORTARE ===================================
import libs.lb_log as lb_log
import libs.lb_config as lb_config
from libs.lb_utils import createThread, startThread, closeThread
from modules.md_tunnel_connections.connections.ssh_reverse_tunneling import ssh_tunnel
from modules.md_tunnel_connections.dto import SshClientConnectionDTO
# ==============================================================

name_module = "md_ssh_reverse_tunneling"

def init():
	global tunnel_connections
	lb_log.info("init")
	tunnel_connections = TunnelConnections()
	lb_log.info("end")

def start():
	lb_log.info("start")
	while lb_config.g_config.g_enabled:
		time.sleep(1)
	lb_log.info("end")

class TunnelConnections:
	def __init__(self):
		
		self.thread_ssh_reverse_tunneling = None

		if lb_config.g_config["app_api"]["ssh_reverse_tunneling"]:
			ssh_client = lb_config.g_config["app_api"]["ssh_reverse_tunneling"]
			ssh_client["local_port"] = lb_config.g_config["app_api"]["port"]
			ssh_client = SshClientConnectionDTO(**ssh_client)
			self.thread_ssh_reverse_tunneling = createThread(ssh_tunnel, (ssh_client,))
			startThread(self.thread_ssh_reverse_tunneling)
   
	def getSshReverseTunneling(self):
		return lb_config.g_config["app_api"]["ssh_reverse_tunneling"]
   
	def setSshReverseTunneling(self, ssh_client: SshClientConnectionDTO):
		self.deleteSshReverseTunneling()
		self.thread_ssh_reverse_tunneling = createThread(ssh_tunnel, (ssh_client,))
		startThread(self.thread_ssh_reverse_tunneling)
		
	def deleteSshReverseTunneling(self):
		lb_config.g_config["app_api"]["ssh_client"] = None
		lb_config.saveconfig()
		if self.thread_ssh_reverse_tunneling:
			closeThread(self.thread_ssh_reverse_tunneling)
			self.thread_ssh_reverse_tunneling = None