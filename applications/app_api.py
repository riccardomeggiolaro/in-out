import libs.lb_log as lb_log
import libs.lb_config as lb_config
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import psutil
from applications.router.generic import GenericRouter
from applications.router.weigher.router import WeigherRouter
from applications.router.anagrafic.router import AnagraficRouter
from applications.router.auth import AuthRouter
from applications.router.printer import PrinterRouter
from applications.router.tunnel_connections import TunnelConnectionsRouter
from applications.router.open_to_customer import OpenToCustomerRouter
from applications.router.sync_folder import SyncFolderRouter
from pathlib import Path
import os
from fastapi.templating import Jinja2Templates
from applications.middleware.auth import AuthMiddleware
from applications.middleware.no_cache import NoCacheMiddleware
import applications.utils.utils as utils
from libs.lb_utils import base_path
# ==============================================================

name_app = "app_api"

# ==============================================================

# ==== MAINPRGLOOP =============================================
# funzione che si connette a redis, setta i moduli e imposta le callback da richiamare dentro i moduli
def mainprg():
	global app
 
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
	# global ssh_client
	
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

	app = FastAPI()
	utils.base_path_applications = Path(__file__).parent
	path_ui = utils.base_path_applications / lb_config.g_config["app_api"]["path_ui"]
	path_content = utils.base_path_applications / lb_config.g_config["app_api"]["path_content"]
	path_images = lb_config.g_config["app_api"]["path_img"]
	if not path_images.startswith("/"):
		path_images = f"{base_path}/{path_images}"
	templates = Jinja2Templates(directory=str(path_ui))

	app.add_middleware(
		CORSMiddleware, 
		allow_origins=[""],
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	# Aggiungi il middleware al tuo FastAPI
	app.add_middleware(AuthMiddleware)

	# Middleware per disabilitare la cache del browser su HTML, CSS e JS
	app.add_middleware(NoCacheMiddleware)

	generic_router = GenericRouter()
	weigher_router = WeigherRouter()
	anagrafic_router = AnagraficRouter()
	auth_router = AuthRouter()
	printer_router = PrinterRouter()
	tunnel_connections_router = TunnelConnectionsRouter()
	open_to_customer = OpenToCustomerRouter()
	sync_folder_router = SyncFolderRouter()

	app.include_router(weigher_router.router, prefix="/api")

	app.include_router(anagrafic_router.router, prefix="/api")

	app.include_router(printer_router.router, prefix="/api/printer", tags=["printer"])

	app.include_router(generic_router.router, prefix="/api/generic", tags=["generic"])

	app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])

	app.include_router(tunnel_connections_router.router, prefix="/api/tunnel_connections", tags=["tunnel connections"])

	app.include_router(open_to_customer.router, prefix="/api", tags=["open to customer"])

	app.include_router(sync_folder_router.router, prefix="/api/sync-folder", tags=["sync folder"])

	app.mount("/static/content", StaticFiles(directory=path_content), name="content")

	app.mount("/static", StaticFiles(directory=path_ui), name="static")
 
	app.mount("/images", StaticFiles(directory=path_images), name="images")
 
	@app.get("/access", response_class=HTMLResponse)
	async def Access(request: Request):
		use_reservation = lb_config.g_config["app_api"]["use_reservation"]
		file_name = "access.html"
		if use_reservation:
			file_name = "reservation.html"
		return templates.TemplateResponse(file_name, {"request": request})
 
	@app.get('/report-designer/entrata', response_class=HTMLResponse)
	async def report_designer(request: Request):
		"""Endpoint dedicato per il report designer."""
		try:
			nome_variabile = ""
			type = "ENTRATA"
			type_default_report = "IN"
			file_path = path_ui / "report-designer.html"
			
			if not file_path.is_file():
				return HTMLResponse(content="File report-designer.html non trovato", status_code=404)
			
			# Leggi il file HTML
			with open(file_path, 'r', encoding='utf-8') as f:
				html_content = f.read()
			
			# Sostituisci le variabili
			html_content = html_content.replace('{{ nome_variabile }}', nome_variabile)
			html_content = html_content.replace('{{ type }}', type)
			html_content = html_content.replace('{{ type_default_report }}', type_default_report)
			html_content = html_content.replace('{{ default_report_template }}', '/static/content/report/weight_in.json')
			html_content = html_content.replace('{{ report }}', 'report_in')
			
			# Puoi aggiungere altre sostituzioni se servono
			# html_content = html_content.replace('{{ altra_variabile }}', altro_valore)
			
			return HTMLResponse(content=html_content)
			
		except Exception as e:
			print(f"Errore nel caricamento report-designer: {e}")
			return HTMLResponse(content=f"Errore: {str(e)}", status_code=500)

	@app.get('/report-designer/uscita', response_class=HTMLResponse)
	async def report_designer(request: Request):
		"""Endpoint dedicato per il report designer."""
		try:
			nome_variabile = ""
			type = "USCITA"
			type_defualt_report = "OUT"
			file_path = path_ui / "report-designer.html"
			
			if not file_path.is_file():
				return HTMLResponse(content="File report-designer.html non trovato", status_code=404)
			
			# Leggi il file HTML
			with open(file_path, 'r', encoding='utf-8') as f:
				html_content = f.read()
			
			# Sostituisci le variabili
			html_content = html_content.replace('{{ nome_variabile }}', nome_variabile)
			html_content = html_content.replace('{{ type }}', type)
			html_content = html_content.replace('{{ type_default_report }}', type_defualt_report)
			html_content = html_content.replace('{{ default_report_template }}', '/static/content/report/weight_out.json')
			html_content = html_content.replace('{{ report }}', 'report_out')
			
			# Puoi aggiungere altre sostituzioni se servono
			# html_content = html_content.replace('{{ altra_variabile }}', altro_valore)
			
			return HTMLResponse(content=html_content)
			
		except Exception as e:
			print(f"Errore nel caricamento report-designer: {e}")
			return HTMLResponse(content=f"Errore: {str(e)}", status_code=500)

	@app.get('/report-designer/stampa', response_class=HTMLResponse)
	async def report_designer_stampa(request: Request):
		"""Endpoint dedicato per il report designer della pesatura generica (stampa)."""
		try:
			nome_variabile = ""
			type = "STAMPA"
			type_default_report = "PRINT"
			file_path = path_ui / "report-designer.html"

			if not file_path.is_file():
				return HTMLResponse(content="File report-designer.html non trovato", status_code=404)

			with open(file_path, 'r', encoding='utf-8') as f:
				html_content = f.read()

			html_content = html_content.replace('{{ nome_variabile }}', nome_variabile)
			html_content = html_content.replace('{{ type }}', type)
			html_content = html_content.replace('{{ type_default_report }}', type_default_report)
			html_content = html_content.replace('{{ default_report_template }}', '/static/content/report/weight_print.json')
			html_content = html_content.replace('{{ report }}', 'report_print')

			return HTMLResponse(content=html_content)

		except Exception as e:
			print(f"Errore nel caricamento report-designer: {e}")
			return HTMLResponse(content=f"Errore: {str(e)}", status_code=500)

	@app.get('/{filename:path}', response_class=HTMLResponse)
	async def Static(request: Request, filename: str):
		"""Gestisce le richieste di file statici (HTML, CSS, JS)."""
		if filename is None or filename == "":
			return RedirectResponse(url="/dashboard")

		# Verifica se il file esiste nella directory templates
		file_path = path_ui / filename
		if file_path.is_file():
			return templates.TemplateResponse(filename, {"request": request})

		# Prova ad aggiungere l'estensione ".html" se non è stato fornito
		filename_html = f"{filename}.html"
		file_path_html = path_ui / filename_html
		if file_path_html.is_file():
			return templates.TemplateResponse(filename_html, {"request": request})

		# Se il file non esiste, fai un redirect alla home
		return RedirectResponse(url="/not-found")