#!/usr/bin/env python3
"""Genera il PDF della presentazione cliente sintetica."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

OUTPUT = "/home/user/in-out/PRESENTAZIONE_CLIENTE_SINTETICA.pdf"

BLUE = HexColor("#1a3c6e")
GRAY = HexColor("#444444")
LIGHT_BLUE = HexColor("#2b5ea7")
LINE_COLOR = HexColor("#cccccc")

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "CustomTitle",
    parent=styles["Title"],
    fontSize=22,
    textColor=BLUE,
    spaceAfter=4,
    alignment=1,
)

subtitle_style = ParagraphStyle(
    "Subtitle",
    parent=styles["Normal"],
    fontSize=11,
    textColor=GRAY,
    alignment=1,
    spaceAfter=20,
)

heading_style = ParagraphStyle(
    "CustomHeading",
    parent=styles["Heading2"],
    fontSize=14,
    textColor=BLUE,
    spaceBefore=16,
    spaceAfter=6,
    borderPadding=(0, 0, 2, 0),
)

body_style = ParagraphStyle(
    "CustomBody",
    parent=styles["Normal"],
    fontSize=10,
    textColor=GRAY,
    leading=15,
    spaceAfter=4,
)

bullet_style = ParagraphStyle(
    "CustomBullet",
    parent=body_style,
    leftIndent=16,
    bulletIndent=6,
    spaceAfter=3,
)

sections = [
    ("1. Cos'e BARON IN-OUT", [
        "Vi presentiamo <b>BARON IN-OUT</b>, il nostro sistema di pesatura industriale per gestire "
        "in automatico ingressi e uscite dei veicoli dal vostro impianto. Pensato per centri logistici, "
        "impianti rifiuti e stabilimenti industriali. Un unico software che collega interfaccia web, "
        "dati e bilance, accessibile da qualsiasi browser."
    ]),
    ("2. Come Funziona", [
        "Il flusso e semplice: il veicolo arriva, viene identificato tramite <b>badge RFID, targa "
        "manuale o lista</b>, sale sulla bilancia e il sistema registra il <b>peso in ingresso</b>. "
        "L'operatore completa i dati: autista, soggetto, materiale, documenti.",
        "Quando il veicolo esce, si registra il <b>peso in uscita</b> e il sistema calcola il "
        "<b>peso netto in automatico</b>.",
        "Ogni accesso segue tre stati chiari: <b>In attesa, Entrato, Chiuso</b>. Sempre tutto sotto controllo."
    ]),
    ("3. Interfaccia", [
        "Dashboard web con <b>peso in tempo reale</b>, lista accessi, inserimento dati. "
        "Tutto immediato, senza installare nulla. Pensata per essere usata velocemente "
        "anche da operatori non tecnici."
    ]),
    ("4. Anagrafiche", [
        "Gestione completa di <b>veicoli, autisti, soggetti, vettori, materiali e operatori</b>. "
        "Una volta inseriti, il sistema li propone automaticamente nelle pesature successive, "
        "velocizzando il lavoro."
    ]),
    ("5. Hardware", [
        "Il sistema si collega a:",
        "\u2022  <b>Bilance</b> (EGT-AF03, DGT1, multi-bilancia)",
        "\u2022  <b>Lettori RFID</b> per identificazione veicoli",
        "\u2022  <b>Display esterni</b> per messaggi all'autista",
        "\u2022  <b>Relay</b> per apertura cancelli e allarmi",
        "\u2022  <b>Telecamere</b> USB/IP per foto del veicolo",
        "\u2022  <b>Stampanti</b> per ticket e report",
    ]),
    ("6. Report", [
        "<b>PDF personalizzabili</b> con Report Designer integrato, <b>export CSV</b> con totali "
        "automatici, e <b>dati JSON in tempo reale</b> per integrazioni con altri software."
    ]),
    ("7. Sicurezza", [
        "Autenticazione <b>JWT con password crittografate</b>, <b>5 livelli di accesso</b> "
        "(da sola lettura a super-admin), e <b>lock dei record</b> per evitare modifiche "
        "simultanee sullo stesso dato."
    ]),
    ("8. Extra", [
        "\u2022  <b>Accesso remoto</b> sicuro via SSH per assistenza e manutenzione",
        "\u2022  <b>Sincronizzazione automatica</b> dei file generati",
        "\u2022  <b>Prenotazioni</b> per programmare gli accessi",
        "\u2022  <b>Tare preimpostate</b> per i veicoli abituali",
        "\u2022  <b>Modalita test</b> per formazione senza hardware",
    ]),
    ("9. Configurazione", [
        "Tutto configurabile: bilance, hardware, report, funzionalita attive. "
        "Un file centralizzato, adattabile alle esigenze specifiche del vostro impianto."
    ]),
    ("10. Tecnica in Breve", [
        "Architettura modulare con <b>FastAPI + WebSocket</b>, database <b>SQLite</b> "
        "(niente server aggiuntivi), gira su <b>Linux e Windows</b>, manutenzione <b>da remoto</b>."
    ]),
    ("11. Sviluppi Futuri", [
        "Da valutare insieme:",
        "\u2022  Integrazione ERP",
        "\u2022  Dashboard con grafici e statistiche",
        "\u2022  App mobile",
        "\u2022  Notifiche email/SMS",
        "\u2022  Backup automatico",
        "\u2022  Integrazione videosorveglianza",
    ]),
]

def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
    )

    story = []

    # Title
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("BARON IN-OUT", title_style))
    story.append(Paragraph("Presentazione Cliente - Versione Sintetica", subtitle_style))
    story.append(HRFlowable(width="80%", thickness=1, color=LINE_COLOR, spaceAfter=20))

    for heading, paragraphs in sections:
        story.append(Paragraph(heading, heading_style))
        for p in paragraphs:
            if p.startswith("\u2022"):
                story.append(Paragraph(p, bullet_style))
            else:
                story.append(Paragraph(p, body_style))
        story.append(Spacer(1, 4))

    # Chiusura
    story.append(HRFlowable(width="80%", thickness=1, color=LINE_COLOR, spaceBefore=16, spaceAfter=12))
    story.append(Paragraph(
        "<b>BARON IN-OUT</b>: completo, flessibile, pronto per il vostro impianto.<br/>"
        "Siamo a disposizione per domande. Grazie.",
        ParagraphStyle("Closing", parent=body_style, alignment=1, textColor=BLUE, fontSize=11)
    ))

    doc.build(story)
    print(f"PDF generato: {OUTPUT}")

if __name__ == "__main__":
    build_pdf()
