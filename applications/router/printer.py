from fastapi import APIRouter, HTTPException
from libs.lb_printer import HTMLPrinter
import libs.lb_database as lb_database
import libs.lb_config as lb_config

class PrinterRouter:
    def __init__(self):
        self.router = APIRouter()
        self.printer = HTMLPrinter()

        self.router.add_api_route('/test', self.printTest)
        self.router.add_api_route('/print/{weighing_id}', self.printWeighingId)
        self.router.add_api_route('/info', self.getPrinter)
        self.router.add_api_route('/list/printer', self.getListPrinters)
        self.router.add_api_route('/set/{printer_name}', self.setPrinter)
        self.router.add_api_route('/list/job', self.getJobs)
        self.router.add_api_route('/job/{job_id}', self.deleteJob)
        self.router.add_api_route('/jobs', self.deleteJobs)

    async def printTest(self):
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
            id, m1, m2 = self.printer.print_html(html)
            return {
                "id": id,
                "message_one": m1,
                "message_two": m2
            }
        except Exception as e:
            return HTTPException(status_code=400, detail=f"{e}")

    async def printWeighingId(self, weighing_id: int):
        try:
            weight = lb_database.get_data_by_id('weighing', weighing_id)
            html = f"""
                <h1>{weight["pid2"]}</h1>
            """
            id, m1, m2 = self.printer.print_html(html)
            return {
                "id": id,
                "message_one": m1,
                "message_two": m2
            }
        except Exception as e:
            return HTTPException(status_code=400, detail=f"{e}")

    async def getPrinter(self):
        return self.get_detailed_status()

    async def getListPrinters(self):
        return self.printer.get_list_printers()

    async def setPrinter(self, printer_name: str):
        try:
            status = self.printer.set_printer(printer_name=printer_name)
            lb_config.g_config["router_api"]["printer_name"] = printer_name
            lb_config.saveconfig()
            return status
        except Exception as e:
            return HTTPException(status_code=400, detail=f"{e}")

    async def getJobs(self):
        return self.printer.get_active_jobs()

    async def deleteJob(self, job_id: int):
        try:
            self.printer.cancel_job(job_id)
            return {
                "message": "Job id deleted"
            }
        except Exception as e:
            return HTTPException(status_code=400, detail=f"{e}")

    async def deleteJobs(self):
        self.printer.cancel_jobs()
        return {
            "message": "All job deleted"
        }