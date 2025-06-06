from fastapi import APIRouter
from libs.lb_printer import printer

class PrinterRouter:
    def __init__(self):
        self.router = APIRouter()

        self.router.add_api_route('/connection', self.checkSubsystemConnection)
        self.router.add_api_route('/test/{printer_name}', self.printTest)
        self.router.add_api_route('/list', self.getListPrinters)

    async def checkSubsystemConnection(self):
        return {
            "connection": printer.check_subsystem_connection()
        }

    async def printTest(self, printer_name: str):
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
        id, m1, m2 = printer.print_html(html, printer_name)
        return {
            "id": id,
            "message_one": m1,
            "message_two": m2
        }

    async def getListPrinters(self):
        return printer.get_list_printers()