from fastapi import APIRouter, HTTPException, Request
from libs.lb_printer import printer
import libs.lb_database as lb_database
import libs.lb_config as lb_config

class PrinterRouter:
    def __init__(self):
        self.router = APIRouter()

        self.router.add_api_route('/test', self.printTest)
        self.router.add_api_route('/print/{weighing_id}', self.printWeighingId)
        self.router.add_api_route('/info', self.getPrinter)
        self.router.add_api_route('/list/printer', self.getListPrinters)
        self.router.add_api_route('/list/job', self.getJobs)
        self.router.add_api_route('/job/{job_id}', self.deleteJob)
        self.router.add_api_route('/jobs', self.deleteJobs)

    async def printTest(self, request: Request):
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
            id, m1, m2 = printer.print_html(html, request.state.user.printer_name)
            return {
                "id": id,
                "message_one": m1,
                "message_two": m2
            }
        except Exception as e:
            return HTTPException(status_code=400, detail=f"{e}")

    async def printWeighingId(self, request: Request, weighing_id: int):
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

    async def getPrinter(self, request: Request):
        return printer.get_detailed_status(request.state.user.printer_name)

    async def getListPrinters(self):
        return printer.get_list_printers()

    async def getJobs(self, request: Request):
        return printer.get_active_jobs(request.state.user.printer_name)

    async def deleteJob(self, request: Request, job_id: int):
        try:
            printer.cancel_job(request.state.user.printer_name, job_id)
            return {
                "message": f"Job with id {job_id} was deleted successfully from printer {request.state.user.printer_name}"
            }
        except Exception as e:
            return HTTPException(status_code=400, detail=f"{e}")

    async def deleteJobs(self, request: Request):
        deleted = printer.cancel_all_jobs(request.state.user.printer_name)
        return {
            "message": f"Deleted {deleted} jobs successfully from printer {request.state.user.printer_name}"
        }