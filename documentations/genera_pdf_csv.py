"""
Rigenera documentations_csv.pdf a partire da documentations_csv.html.

Uso:
    python3 documentations/genera_pdf_csv.py

Richiede Playwright con Chromium (pip install playwright && playwright install chromium).
"""

from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
SRC = HERE / "documentations_csv.html"
OUT = HERE / "documentations_csv.pdf"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(SRC.as_uri())
        page.pdf(path=str(OUT), format="A4", print_background=True, prefer_css_page_size=True)
        browser.close()
    print(f"PDF generato: {OUT}")


if __name__ == "__main__":
    main()
