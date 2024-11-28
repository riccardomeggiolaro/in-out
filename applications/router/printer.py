from fastapi import APIRouter, HTTPException
from libs.lb_printer import HTMLPrinter
import libs.lb_database as lb_database
import libs.lb_config as lb_config
import libs.lb_log as lb_log

router = APIRouter()

# printer = HTMLPrinter(printer_name=lb_config.g_config["printer_name"])

printer = HTMLPrinter()

@router.get("/test")
async def printTest():
    try:
        html = """
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Test di stampa</title>
                </head>
                <body>
                    <h1>Test di stampa HTML</h1>
                    <p>Questo è un test di stampa.</p>
                </body>
            </html>
        """
        id, m1, m2 = printer.print_html(html)
        return {
            "id": id,
            "message_one": m1,
            "message_two": m2
        }
    except Exception as e:
        return HTTPException(status_code=400, detail=f"{e}")

@router.get("/print/{weighing_id}")
async def printWeighingId(weighing_id: int):
    try:
        weight = lb_database.get_data_by_id('weighing', weighing_id)
        html = f"""
            <h1>{weight["pid2"]}</h1>
        """
        id, m1, m2 = printer.print_html(html)
        return {
            "id": id,
            "message_one": m1,
            "message_two": m2
        }
    except Exception as e:
        return HTTPException(status_code=400, detail=f"{e}")

@router.get("/info")
async def getPrinter():
    return printer.get_detailed_status()

@router.get("/lists")
async def getLsitPrinters():
    return printer.get_list_printers()

@router.patch("/set/{printer_name}")
async def setPrinter(printer_name: str):
    try:
        status = printer.set_printer(printer_name=printer_name)
        lb_config.g_config["router_api"]["printer_name"] = printer_name
        lb_config.saveconfig()
        return status
    except Exception as e:
        return HTTPException(status_code=400, detail=f"{e}")

@router.get("/jobs")
async def getJobs():
    return printer.get_active_jobs()

@router.delete("/job/{job_id}")
async def deleteJob(job_id: int):
    try:
        printer.cancel_job(job_id)
        return {
            "message": "Job id deleted"
        }
    except Exception as e:
        return HTTPException(status_code=400, detail=f"{e}")

@router.delete("/jobs")
async def deleteJobs():
    printer.cancel_jobs()
    return {
        "message": "All job deleted"
    }