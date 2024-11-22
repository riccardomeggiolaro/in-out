from html_printer import HTMLPrinter

if __name__ == "__main__":
    printer_name = "HP-OfficeJet-Pro-8720"

    printer = HTMLPrinter(printer_name)

    html = f"""
    <html>
        <body>
            <h1>Benvenuto</h1>
            <p>Questo è un test di stampa. {printer_name}</p>
        </body>
    </html>
    """

    j = printer.print_html(html)
    print(j)