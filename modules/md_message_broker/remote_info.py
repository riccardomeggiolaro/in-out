"""
Stato della macchina per il pannello del broker
===============================================

Il pannello chiede `{"t":"info","id"}` sul tunnel (vedi `remote_tunnel.py`) e l'in-out
risponde `{"t":"info","id","ok":true,"data":{...}}` con versione, sistema operativo,
uptime, CPU, memoria, disco, da quanto gira il servizio e stato del terminale SSH.
Solo letture: nessun comando viene eseguito.
"""

import os
import platform
import shutil
import socket
import sys
import time

import libs.lb_config as lb_config
from modules.md_message_broker import remote_ssh

try:
	import psutil
except ImportError:  # pragma: no cover
	psutil = None


def _disk(path: str) -> dict:
	try:
		usage = shutil.disk_usage(path)
	except OSError:
		return {}
	return {
		"path": path,
		"total": usage.total,
		"used": usage.used,
		"free": usage.free,
		"percent": round(usage.used * 100 / usage.total, 1) if usage.total else None,
	}


def _install_dir() -> str:
	if getattr(sys, "frozen", False):
		return os.path.dirname(sys.executable)
	return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def collect() -> dict:
	now = time.time()
	data = {
		"version": getattr(lb_config, "g_vers", None),
		"hostname": socket.gethostname(),
		"os": platform.platform(terse=True),
		"python": platform.python_version(),
		"time": now,
		"disk": _disk(_install_dir()),
		"ssh": remote_ssh.status(),
	}
	if psutil is not None:
		try:
			mem = psutil.virtual_memory()
			data["memory"] = {"total": mem.total, "used": mem.total - mem.available, "percent": mem.percent}
			data["cpu_percent"] = psutil.cpu_percent(interval=0.3)
			data["cpu_count"] = psutil.cpu_count()
			data["uptime"] = int(now - psutil.boot_time())
			data["service_uptime"] = int(now - psutil.Process().create_time())
		except Exception:
			pass
	return data
