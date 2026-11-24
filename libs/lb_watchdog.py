# Watchdog diagnostico per il thread della pesa.
#
# Ogni chiamata a Callback_Realtime registra un "battito" con beat(). Se per una pesa
# non arrivano battiti per STALL_SECONDS (mentre ci sono client collegati), scrive in
# thread_dump.log lo stack di tutti i thread, così si vede in quale riga il thread
# della pesa è rimasto fermo.
#
# In più, su Linux, `kill -USR1 <pid>` scrive in qualsiasi momento lo stack di tutti i
# thread nello stesso file (tramite faulthandler, funziona anche se un thread è bloccato
# dentro codice C).

import faulthandler
import os
import signal
import sys
import threading
import time
import traceback
from datetime import datetime

import libs.lb_config as lb_config
import libs.lb_log as lb_log

STALL_SECONDS = 60
CHECK_INTERVAL = 10

_heartbeats = {}
_lock = threading.Lock()
_started = False
_signal_file = None


def _dump_path():
	try:
		return os.path.join(os.path.dirname(lb_config.g_defalogfile), "thread_dump.log")
	except Exception:
		return "thread_dump.log"


def _log_error(msg):
	try:
		lb_log.error(msg)
	except Exception:
		print(msg, flush=True)


def beat(key):
	_heartbeats[key] = time.time()


def dump_threads(reason):
	path = _dump_path()
	try:
		frames = sys._current_frames()
		with open(path, "a", encoding="utf-8") as f:
			f.write(f"\n===== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {reason} =====\n")
			for thread in threading.enumerate():
				frame = frames.get(thread.ident)
				f.write(f"\n--- Thread '{thread.name}' (id {thread.ident}, daemon={thread.daemon}) ---\n")
				if frame is not None:
					f.write("".join(traceback.format_stack(frame)))
		_log_error(f"Watchdog: {reason}. Stack dei thread salvato in {path}")
	except Exception as e:
		_log_error(f"Watchdog: impossibile salvare lo stack dei thread: {e}")


def _run(should_alert):
	alerted = set()
	while True:
		time.sleep(CHECK_INTERVAL)
		try:
			_check(should_alert, alerted)
		except Exception as e:
			_log_error(f"Watchdog: errore nel controllo: {e}")


def _check(should_alert, alerted):
	now = time.time()
	for key, last in list(_heartbeats.items()):
		stalled = now - last
		if stalled > STALL_SECONDS:
			if key in alerted:
				continue
			try:
				if should_alert is not None and not should_alert(key):
					continue
			except Exception:
				pass
			alerted.add(key)
			dump_threads(f"nessun peso in tempo reale dalla pesa {key} da {int(stalled)} secondi")
		else:
			alerted.discard(key)


def start(should_alert=None):
	global _started, _signal_file
	with _lock:
		if _started:
			return
		_started = True
	if hasattr(signal, "SIGUSR1"):
		try:
			_signal_file = open(_dump_path(), "a", encoding="utf-8")
			faulthandler.register(signal.SIGUSR1, file=_signal_file, all_threads=True)
		except Exception as e:
			_log_error(f"Watchdog: SIGUSR1 non registrato: {e}")
	threading.Thread(target=_run, args=(should_alert,), daemon=True, name="weigher-watchdog").start()
