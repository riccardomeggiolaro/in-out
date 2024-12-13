from fastapi import APIRouter, HTTPException, Request
from libs.lb_printer import printer
import libs.lb_database as lb_database
import libs.lb_config as lb_config

class PrinterRouter:
    def __init__(self):
        self.router = APIRouter()

        self.router.add_api_route('/connection', self.checkSubsystemConnection)
        self.router.add_api_route('/test', self.printTest)
        self.router.add_api_route('/print/{weighing_id}', self.printWeighingId)
        self.router.add_api_route('/info', self.getPrinter)
        self.router.add_api_route('/list', self.getListPrinters)

    async def checkSubsystemConnection(self):
        return {
            "connection": printer.check_subsystem_connection()
        }

    async def printTest(self, request: Request):
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

    async def printWeighingId(self, request: Request, weighing_id: int):
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

    async def getPrinter(self, request: Request):
        return printer.get_detailed_status(request.state.user.printer_name)

    async def getListPrinters(self):
        return printer.get_list_printers()