from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import os
from typing import Optional
from fastapi.templating import Jinja2Templates
import libs.lb_system as lb_system

router = APIRouter()

base_dir_templates = os.getcwd() + "/client"
templates = Jinja2Templates(directory=f"{base_dir_templates}")

@router.get("/{filename:path}", response_class=HTMLResponse)
async def Static(request: Request, filename: Optional[str] = None):
    if filename is None or filename == "":
        return templates.TemplateResponse("index.html", {"request": request})
    elif filename in ["index", "index.html"]:
        return RedirectResponse(url="/")
    file_exist = os.path.isfile(f"{base_dir_templates}/{filename}")
    if file_exist:
        return templates.TemplateResponse(filename, {"request": request})
    else:
        filename_html = f'{filename}.html'
        file_exist = os.path.isfile(f"{base_dir_templates}/{filename_html}")
        if file_exist:
            return templates.TemplateResponse(filename_html, {"request": request})
    return RedirectResponse(url="/")

@router.get("/list_serial_ports")
async def ListSerialPorts():
    status, data = lb_system.list_serial_port()
    if status is True:
        return {
            "list_serial_ports": data
        }
    return data