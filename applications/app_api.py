import libs.lb_log as lb_log
import libs.lb_config as lb_config
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn
import psutil
from applications.router.generic import GenericRouter
from applications.router.anagrafic import AnagraficRouter
from applications.router.weigher.router import WeigherRouter
from applications.router.data_in_execution import DataInExecutionRouter
from applications.router.historic_data import HistoricDataRouter
from applications.router.auth import AuthRouter
from applications.router.printer import PrinterRouter
from typing import Optional
from pathlib import Path
import os
from fastapi.templating import Jinja2Templates
from applications.middleware.auth import AuthMiddleware
# ==============================================================

name_app = "app_api"

# ==============================================================

# ==== MAINPRGLOOP =============================================
# funzione che si connette a redis, setta i moduli e imposta le callback da richiamare dentro i moduli
def mainprg():
	global app
	global thread_ssh_tunnel
	global base_dir_templates
	global templates
 
	@app.get('/{filename:path}', response_class=HTMLResponse)
	async def Static(request: Request, filename: Optional[str] = None):
		"""Gestisce le richieste di file statici (HTML, CSS, JS)."""
		if filename is None or filename == "":
			return templates.TemplateResponse("index.html", {"request": request})

		# Redirect alla home se il file richiesto è "index" o "index.html"
		elif filename in ["index", "index.html"]:
			return RedirectResponse(url="/")
		
		# Verifica se il file esiste nella directory templates
		file_path = base_dir_templates / filename
		if file_path.is_file():
			return templates.TemplateResponse(filename, {"request": request})

		# Prova ad aggiungere l'estensione ".html" se non è stato fornito
		filename_html = f"{filename}.html"
		file_path_html = base_dir_templates / filename_html
		if file_path_html.is_file():
			return templates.TemplateResponse(filename_html, {"request": request})

		# Se il file non esiste, fai un redirect alla home
		return RedirectResponse(url="/")

	uvicorn.run(app, host="0.0.0.0", port=lb_config.g_config["app_api"]["port"], log_level="info", reload=False)
# ==============================================================


# ==== START ===================================================
# funzione che fa partire la applicazione
def start():
	lb_log.info("start")
	mainprg()  # 	a il loop a mainprg
	lb_log.info("end")
# ==============================================================

def stop():
	global ssh_client
	
	try:
		port = lb_config.g_config["app_api"]["port"]
		connection = [conn for conn in psutil.net_connections() if conn.laddr.port == port] 
		lb_log.info(f"Chiudendo il processo che utilizza la porta {port}...")
		p = psutil.Process(connection[-1].pid)
		p.kill()
		p.wait(timeout=5)  # Attendere al massimo 5 secondi per la chiusura
		lb_log.info(f"Processo sulla porta {port} chiuso con successo.")
	except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired) as e:	
		lb_log.info(f"Impossibile chiudere il processo sulla porta {port}. {e}")

	# closeThread(ssh_client)

# ==== INIT ====================================================
# funzione che dichiara tutte le globali
def init():	
	lb_log.info("init")
	global app
	global rfid
	global modules
	global ssh_client
	global base_dir_templates
	global templates

	# Usa Path per una gestione più sicura dei percorsi
	base_dir_templates = Path(os.getcwd()) / "client"
	templates = Jinja2Templates(directory=str(base_dir_templates))

	app = FastAPI()

	app.add_middleware(
		CORSMiddleware, 
		allow_origins=["*"],
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	# Aggiungi il middleware al tuo FastAPI
	app.add_middleware(AuthMiddleware)

	generic_router = GenericRouter()
	anagrafic_router = AnagraficRouter()
	weigher_router = WeigherRouter()
	data_in_execution_router = DataInExecutionRouter()
	historic_data_router = HistoricDataRouter()
	auth_router = AuthRouter()
	printer_router = PrinterRouter()

	app.include_router(weigher_router.router)

	app.include_router(anagrafic_router.router, prefix="/anagrafic", tags=["anagrafic"])

	app.include_router(data_in_execution_router.router, prefix="/data_in_execution", tags=["data in execution"])

	app.include_router(printer_router, prefix="/printer", tags=["printer"])

	app.include_router(historic_data_router.router, prefix="/historic_data", tags=["historic data"])

	app.include_router(generic_router.router, prefix="/generic", tags=["generic"])

	app.include_router(auth_router.router, prefix="/auth", tags=["auth"])

	# ssh_client = None
	# if lb_config.g_config["app_api"]["ssh_client"]:
	# 	ssh_client = lb_config.g_config["app_api"]["ssh_client"]
	# 	ssh_client["local_port"] = lb_config.g_config["app_api"]["port"]
	# 	ssh_client = createThread(ssh_tunnel, (SshClientConnection(**ssh_client),))
	# 	startThread(ssh_client)