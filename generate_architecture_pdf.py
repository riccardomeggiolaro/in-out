#!/usr/bin/env python3
"""
Script per generare un PDF semplificato dell'architettura di BARON IN-OUT
destinato a un pubblico non tecnico.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Image, Flowable
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.graphics import renderPDF
import os

# ── Colori ──────────────────────────────────────────────
PRIMARY = HexColor("#2C3E50")       # Blu scuro
SECONDARY = HexColor("#3498DB")     # Blu chiaro
ACCENT = HexColor("#E74C3C")        # Rosso
SUCCESS = HexColor("#27AE60")       # Verde
WARNING = HexColor("#F39C12")       # Arancione
LIGHT_BG = HexColor("#ECF0F1")      # Grigio chiaro
LIGHT_BLUE = HexColor("#D6EAF8")    # Azzurro chiaro
LIGHT_GREEN = HexColor("#D5F5E3")   # Verde chiaro
LIGHT_ORANGE = HexColor("#FDEBD0")  # Arancione chiaro
LIGHT_RED = HexColor("#FADBD8")     # Rosso chiaro
LIGHT_PURPLE = HexColor("#E8DAEF")  # Viola chiaro
DARK_TEXT = HexColor("#2C3E50")
MEDIUM_TEXT = HexColor("#5D6D7E")

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "documentations", "architettura_semplificata.pdf")


# ── Stili ───────────────────────────────────────────────
def get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='CoverTitle',
        fontName='Helvetica-Bold',
        fontSize=32,
        leading=38,
        textColor=white,
        alignment=TA_CENTER,
        spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name='CoverSubtitle',
        fontName='Helvetica',
        fontSize=16,
        leading=22,
        textColor=HexColor("#D6EAF8"),
        alignment=TA_CENTER,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name='SectionTitle',
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=26,
        textColor=PRIMARY,
        spaceBefore=20,
        spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name='SubSectionTitle',
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=SECONDARY,
        spaceBefore=14,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name='BodyText2',
        fontName='Helvetica',
        fontSize=11,
        leading=16,
        textColor=DARK_TEXT,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name='BulletItem',
        fontName='Helvetica',
        fontSize=11,
        leading=16,
        textColor=DARK_TEXT,
        leftIndent=20,
        spaceAfter=4,
        bulletIndent=8,
        bulletFontName='Helvetica-Bold',
        bulletFontSize=11,
    ))
    styles.add(ParagraphStyle(
        name='BoxTitle',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=PRIMARY,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name='BoxBody',
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=MEDIUM_TEXT,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name='FooterText',
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=MEDIUM_TEXT,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name='NumberBig',
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=32,
        textColor=SECONDARY,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name='CaptionCenter',
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=MEDIUM_TEXT,
        alignment=TA_CENTER,
        spaceAfter=6,
    ))
    return styles


# ── Flowable personalizzati ─────────────────────────────
class ColoredBox(Flowable):
    """Riquadro colorato con titolo e contenuto."""

    def __init__(self, title, body, bg_color=LIGHT_BG, width=None, icon=None):
        super().__init__()
        self.title = title
        self.body = body
        self.bg_color = bg_color
        self._width = width or 16 * cm
        self.icon = icon or ""
        self.padding = 12

    def wrap(self, availWidth, availHeight):
        self._width = min(self._width, availWidth)
        # Calcola altezza approssimativa
        lines_title = 1
        lines_body = max(1, len(self.body) // 60 + 1)
        self._height = self.padding * 2 + lines_title * 18 + lines_body * 15 + 8
        return self._width, self._height

    def draw(self):
        canvas = self.canv
        p = self.padding
        # Sfondo arrotondato
        canvas.setFillColor(self.bg_color)
        canvas.setStrokeColor(self.bg_color)
        canvas.roundRect(0, 0, self._width, self._height, 8, fill=1, stroke=0)
        # Titolo
        canvas.setFillColor(PRIMARY)
        canvas.setFont("Helvetica-Bold", 12)
        title_text = f"{self.icon}  {self.title}" if self.icon else self.title
        canvas.drawString(p, self._height - p - 14, title_text)
        # Corpo
        canvas.setFillColor(MEDIUM_TEXT)
        canvas.setFont("Helvetica", 10)
        y = self._height - p - 34
        # Wrap testo manualmente
        words = self.body.split()
        line = ""
        max_chars = int((self._width - 2 * p) / 5.5)
        for word in words:
            if len(line) + len(word) + 1 <= max_chars:
                line = line + " " + word if line else word
            else:
                canvas.drawString(p, y, line)
                y -= 14
                line = word
                if y < p:
                    break
        if line and y >= p:
            canvas.drawString(p, y, line)


class HorizontalLine(Flowable):
    """Linea orizzontale decorativa."""

    def __init__(self, width=None, color=LIGHT_BG, thickness=2):
        super().__init__()
        self._width = width or 16 * cm
        self.color = color
        self.thickness = thickness

    def wrap(self, availWidth, availHeight):
        self._width = min(self._width, availWidth)
        return self._width, self.thickness + 6

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 3, self._width, 3)


# ── Diagrammi ───────────────────────────────────────────
def create_architecture_diagram():
    """Crea il diagramma architetturale principale."""
    d = Drawing(480, 380)

    # ── Titolo ──
    d.add(String(240, 365, "Come funziona BARON IN-OUT", fontName="Helvetica-Bold",
                 fontSize=14, fillColor=PRIMARY, textAnchor="middle"))

    # ── Livello Utenti (top) ──
    d.add(Rect(30, 290, 420, 55, fillColor=LIGHT_BLUE, strokeColor=SECONDARY, strokeWidth=1.5, rx=8, ry=8))
    d.add(String(240, 322, "UTENTI", fontName="Helvetica-Bold", fontSize=12, fillColor=PRIMARY, textAnchor="middle"))
    d.add(String(100, 300, "Browser Web", fontName="Helvetica", fontSize=9, fillColor=MEDIUM_TEXT, textAnchor="middle"))
    d.add(String(240, 300, "Tablet / Telefono", fontName="Helvetica", fontSize=9, fillColor=MEDIUM_TEXT, textAnchor="middle"))
    d.add(String(380, 300, "Postazione PC", fontName="Helvetica", fontSize=9, fillColor=MEDIUM_TEXT, textAnchor="middle"))

    # Freccia giù
    d.add(Line(240, 290, 240, 260, strokeColor=SECONDARY, strokeWidth=2))
    d.add(Polygon(points=[235, 262, 245, 262, 240, 254], fillColor=SECONDARY, strokeColor=SECONDARY))

    # ── Livello Applicazione ──
    d.add(Rect(30, 185, 420, 65, fillColor=LIGHT_GREEN, strokeColor=SUCCESS, strokeWidth=1.5, rx=8, ry=8))
    d.add(String(240, 230, "APPLICAZIONE BARON IN-OUT", fontName="Helvetica-Bold", fontSize=12,
                 fillColor=PRIMARY, textAnchor="middle"))
    d.add(String(120, 210, "Gestione Pesate", fontName="Helvetica", fontSize=9, fillColor=MEDIUM_TEXT, textAnchor="middle"))
    d.add(String(240, 210, "Anagrafiche", fontName="Helvetica", fontSize=9, fillColor=MEDIUM_TEXT, textAnchor="middle"))
    d.add(String(370, 210, "Documenti/Report", fontName="Helvetica", fontSize=9, fillColor=MEDIUM_TEXT, textAnchor="middle"))
    d.add(String(120, 195, "Sicurezza", fontName="Helvetica", fontSize=9, fillColor=MEDIUM_TEXT, textAnchor="middle"))
    d.add(String(240, 195, "Accessi", fontName="Helvetica", fontSize=9, fillColor=MEDIUM_TEXT, textAnchor="middle"))
    d.add(String(370, 195, "Stampa", fontName="Helvetica", fontSize=9, fillColor=MEDIUM_TEXT, textAnchor="middle"))

    # Freccia giù (sinistra - database)
    d.add(Line(150, 185, 150, 155, strokeColor=SUCCESS, strokeWidth=2))
    d.add(Polygon(points=[145, 157, 155, 157, 150, 149], fillColor=SUCCESS, strokeColor=SUCCESS))

    # Freccia giù (destra - hardware)
    d.add(Line(330, 185, 330, 155, strokeColor=SUCCESS, strokeWidth=2))
    d.add(Polygon(points=[325, 157, 335, 157, 330, 149], fillColor=SUCCESS, strokeColor=SUCCESS))

    # ── Database (in basso a sinistra) ──
    d.add(Rect(40, 90, 200, 55, fillColor=LIGHT_ORANGE, strokeColor=WARNING, strokeWidth=1.5, rx=8, ry=8))
    d.add(String(140, 125, "ARCHIVIO DATI", fontName="Helvetica-Bold", fontSize=11,
                 fillColor=PRIMARY, textAnchor="middle"))
    d.add(String(140, 108, "Pesate, Veicoli, Autisti,", fontName="Helvetica", fontSize=9,
                 fillColor=MEDIUM_TEXT, textAnchor="middle"))
    d.add(String(140, 95, "Materiali, Clienti, Utenti", fontName="Helvetica", fontSize=9,
                 fillColor=MEDIUM_TEXT, textAnchor="middle"))

    # ── Hardware (in basso a destra) ──
    d.add(Rect(260, 90, 200, 55, fillColor=LIGHT_RED, strokeColor=ACCENT, strokeWidth=1.5, rx=8, ry=8))
    d.add(String(360, 125, "DISPOSITIVI ESTERNI", fontName="Helvetica-Bold", fontSize=11,
                 fillColor=PRIMARY, textAnchor="middle"))
    d.add(String(360, 108, "Bilance, Stampanti,", fontName="Helvetica", fontSize=9,
                 fillColor=MEDIUM_TEXT, textAnchor="middle"))
    d.add(String(360, 95, "RFID, Pannelli, Sirene", fontName="Helvetica", fontSize=9,
                 fillColor=MEDIUM_TEXT, textAnchor="middle"))

    # ── Uscite in basso ──
    d.add(Rect(100, 20, 280, 50, fillColor=LIGHT_PURPLE, strokeColor=HexColor("#8E44AD"), strokeWidth=1.5, rx=8, ry=8))
    d.add(String(240, 50, "DOCUMENTI GENERATI", fontName="Helvetica-Bold", fontSize=11,
                 fillColor=PRIMARY, textAnchor="middle"))
    d.add(String(170, 32, "PDF", fontName="Helvetica-Bold", fontSize=10, fillColor=ACCENT, textAnchor="middle"))
    d.add(String(240, 32, "CSV / Excel", fontName="Helvetica-Bold", fontSize=10, fillColor=WARNING, textAnchor="middle"))
    d.add(String(320, 32, "Stampe", fontName="Helvetica-Bold", fontSize=10, fillColor=SUCCESS, textAnchor="middle"))

    # Frecce verso documenti
    d.add(Line(140, 90, 200, 70, strokeColor=HexColor("#8E44AD"), strokeWidth=1.5))
    d.add(Line(360, 90, 300, 70, strokeColor=HexColor("#8E44AD"), strokeWidth=1.5))

    return d


def create_weighing_flow_diagram():
    """Crea il diagramma del flusso di pesatura."""
    d = Drawing(480, 310)

    d.add(String(240, 295, "Il Processo di Pesatura", fontName="Helvetica-Bold",
                 fontSize=14, fillColor=PRIMARY, textAnchor="middle"))

    # Step boxes
    steps = [
        ("1", "Arrivo Veicolo", "Il veicolo arriva\nalla pesa", LIGHT_BLUE, SECONDARY),
        ("2", "Identificazione", "Badge, targa\no manuale", LIGHT_GREEN, SUCCESS),
        ("3", "Prima Pesata", "Peso lordo\nregistrato", LIGHT_ORANGE, WARNING),
        ("4", "Carico/Scarico", "Operazioni in\nmagazzino", LIGHT_PURPLE, HexColor("#8E44AD")),
        ("5", "Seconda Pesata", "Peso tara\nregistrato", LIGHT_ORANGE, WARNING),
        ("6", "Documento", "PDF generato\ne stampato", LIGHT_RED, ACCENT),
    ]

    box_w = 68
    box_h = 70
    start_x = 12
    gap = 10
    y_top = 195

    for i, (num, title, desc, bg, border) in enumerate(steps):
        x = start_x + i * (box_w + gap)
        # Riquadro
        d.add(Rect(x, y_top, box_w, box_h, fillColor=bg, strokeColor=border, strokeWidth=1.5, rx=6, ry=6))
        # Numero
        d.add(String(x + box_w / 2, y_top + box_h - 16, num, fontName="Helvetica-Bold",
                      fontSize=16, fillColor=border, textAnchor="middle"))
        # Titolo
        d.add(String(x + box_w / 2, y_top + box_h - 32, title, fontName="Helvetica-Bold",
                      fontSize=8, fillColor=PRIMARY, textAnchor="middle"))
        # Descrizione (due righe)
        lines = desc.split("\n")
        for j, line in enumerate(lines):
            d.add(String(x + box_w / 2, y_top + box_h - 46 - j * 11, line, fontName="Helvetica",
                          fontSize=7, fillColor=MEDIUM_TEXT, textAnchor="middle"))

        # Freccia tra i box
        if i < len(steps) - 1:
            ax = x + box_w + 1
            ay = y_top + box_h / 2
            d.add(Line(ax, ay, ax + gap - 2, ay, strokeColor=SECONDARY, strokeWidth=2))
            d.add(Polygon(points=[ax + gap - 4, ay + 3, ax + gap - 4, ay - 3, ax + gap, ay],
                          fillColor=SECONDARY, strokeColor=SECONDARY))

    # Risultato finale
    d.add(Rect(80, 100, 320, 55, fillColor=LIGHT_GREEN, strokeColor=SUCCESS, strokeWidth=2, rx=8, ry=8))
    d.add(String(240, 137, "RISULTATO FINALE", fontName="Helvetica-Bold",
                 fontSize=12, fillColor=PRIMARY, textAnchor="middle"))
    d.add(String(240, 118, "Peso Netto = Peso Lordo - Tara", fontName="Helvetica-Bold",
                 fontSize=11, fillColor=SUCCESS, textAnchor="middle"))
    d.add(String(240, 105, "Documento PDF con tutti i dati della pesata", fontName="Helvetica",
                 fontSize=9, fillColor=MEDIUM_TEXT, textAnchor="middle"))

    # Freccia verso risultato
    d.add(Line(240, 195, 240, 160, strokeColor=SUCCESS, strokeWidth=2))
    d.add(Polygon(points=[235, 162, 245, 162, 240, 155], fillColor=SUCCESS, strokeColor=SUCCESS))

    return d


def create_security_diagram():
    """Crea il diagramma della sicurezza."""
    d = Drawing(480, 200)

    d.add(String(240, 185, "Livelli di Accesso", fontName="Helvetica-Bold",
                 fontSize=14, fillColor=PRIMARY, textAnchor="middle"))

    levels = [
        ("Operatore", "Visualizza dati\nEsegue pesate", LIGHT_BLUE, SECONDARY, 140),
        ("Amministratore", "Gestisce anagrafiche\nGestisce utenti", LIGHT_ORANGE, WARNING, 140),
        ("Super Admin", "Configura sistema\nRiavvia software", LIGHT_RED, ACCENT, 140),
    ]

    total_w = sum(w for _, _, _, _, w in levels) + 20 * (len(levels) - 1)
    x = (480 - total_w) / 2
    y = 50

    for title, desc, bg, border, w in levels:
        d.add(Rect(x, y, w, 105, fillColor=bg, strokeColor=border, strokeWidth=1.5, rx=8, ry=8))
        d.add(String(x + w / 2, y + 85, title, fontName="Helvetica-Bold", fontSize=11,
                      fillColor=PRIMARY, textAnchor="middle"))
        lines = desc.split("\n")
        for j, line in enumerate(lines):
            d.add(String(x + w / 2, y + 60 - j * 14, line, fontName="Helvetica", fontSize=9,
                          fillColor=MEDIUM_TEXT, textAnchor="middle"))
        x += w + 20

    return d


# ── Costruzione del PDF ──────────────────────────────────
def build_pdf():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
    )

    styles = get_styles()
    story = []

    # ════════════════════════════════════════════════════════
    # COPERTINA
    # ════════════════════════════════════════════════════════
    # Spazio sopra per centrare
    story.append(Spacer(1, 4 * cm))

    # Riquadro copertina
    cover_data = [[""]]
    cover_table = Table(cover_data, colWidths=[16 * cm], rowHeights=[8 * cm])
    cover_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PRIMARY),
        ('ROUNDEDCORNERS', [12, 12, 12, 12]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    # Contenuto copertina come tabella interna
    cover_content = []
    cover_content.append(Paragraph("BARON IN-OUT", styles['CoverTitle']))
    cover_content.append(Spacer(1, 8))
    cover_content.append(Paragraph("Sistema di Pesatura Industriale", styles['CoverSubtitle']))
    cover_content.append(Spacer(1, 16))
    cover_content.append(Paragraph("Guida all'Architettura Semplificata", styles['CoverSubtitle']))
    cover_content.append(Spacer(1, 8))
    cover_content.append(Paragraph("Versione 3.0.1", styles['CoverSubtitle']))

    inner_table = Table([[cover_content]], colWidths=[14 * cm])
    inner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PRIMARY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
        ('TOPPADDING', (0, 0), (-1, -1), 30),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 30),
    ]))

    story.append(inner_table)
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(
        "Questo documento descrive in modo semplice come funziona il software BARON IN-OUT, "
        "senza entrare nei dettagli tecnici.",
        styles['CaptionCenter']
    ))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # INDICE
    # ════════════════════════════════════════════════════════
    story.append(Paragraph("Indice", styles['SectionTitle']))
    story.append(HorizontalLine())
    story.append(Spacer(1, 8))

    toc_items = [
        ("1.", "Cos'è BARON IN-OUT?"),
        ("2.", "Cosa fa il sistema"),
        ("3.", "Come funziona (schema generale)"),
        ("4.", "Il processo di pesatura passo per passo"),
        ("5.", "I dati che gestisce"),
        ("6.", "Sicurezza e accessi"),
        ("7.", "I dispositivi collegati"),
        ("8.", "Documenti e report"),
        ("9.", "Funzionalità aggiuntive"),
        ("10.", "Domande frequenti"),
    ]

    for num, title in toc_items:
        story.append(Paragraph(
            f'<b>{num}</b>  {title}',
            styles['BodyText2']
        ))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 1. COS'È BARON IN-OUT?
    # ════════════════════════════════════════════════════════
    story.append(Paragraph("1. Cos'è BARON IN-OUT?", styles['SectionTitle']))
    story.append(HorizontalLine())
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "BARON IN-OUT è un <b>software per la gestione delle pesature industriali</b>. "
        "Viene utilizzato in aziende che hanno bisogno di pesare veicoli in entrata e in uscita, "
        "come ad esempio impianti di riciclaggio, cave, aziende agricole, centri di raccolta e magazzini.",
        styles['BodyText2']
    ))
    story.append(Paragraph(
        "Il sistema si occupa di tutto il processo: dall'arrivo del veicolo alla pesa, "
        "fino alla generazione del documento finale con il peso netto calcolato.",
        styles['BodyText2']
    ))

    # Box riassuntivo
    story.append(Spacer(1, 10))
    summary_data = [
        [Paragraph("<b>In poche parole</b>", styles['BoxTitle'])],
        [Paragraph(
            "BARON IN-OUT sostituisce i registri cartacei delle pesature con un sistema "
            "digitale completo che registra i pesi, identifica i veicoli, genera documenti "
            "e tiene traccia di tutte le operazioni.",
            styles['BoxBody']
        )],
    ]
    summary_table = Table(summary_data, colWidths=[15 * cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BLUE),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (0, 0), 12),
        ('BOTTOMPADDING', (-1, -1), (-1, -1), 12),
    ]))
    story.append(summary_table)

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 2. COSA FA IL SISTEMA
    # ════════════════════════════════════════════════════════
    story.append(Paragraph("2. Cosa fa il sistema", styles['SectionTitle']))
    story.append(HorizontalLine())
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "BARON IN-OUT offre diverse funzionalità per gestire le operazioni quotidiane di pesatura:",
        styles['BodyText2']
    ))

    features = [
        ("Pesatura veicoli", "Registra il peso dei veicoli in entrata e in uscita, calcolando automaticamente il peso netto del materiale trasportato.", LIGHT_BLUE),
        ("Gestione anagrafiche", "Tiene un archivio completo di clienti, fornitori, veicoli, autisti, materiali e operatori.", LIGHT_GREEN),
        ("Generazione documenti", "Crea automaticamente documenti PDF e report delle pesature effettuate.", LIGHT_ORANGE),
        ("Sistema di accessi", "Gestisce gli ingressi dei veicoli con prenotazioni, identificazione tramite badge o inserimento manuale.", LIGHT_PURPLE),
        ("Stampa automatica", "Stampa i documenti di pesatura direttamente sulle stampanti collegate.", LIGHT_RED),
        ("Monitoraggio in tempo reale", "Mostra il peso in tempo reale dalla bilancia collegata.", LIGHT_BLUE),
    ]

    for title, desc, bg in features:
        box_data = [
            [Paragraph(f"<b>{title}</b>", styles['BoxTitle']),
             Paragraph(desc, styles['BoxBody'])],
        ]
        box_table = Table(box_data, colWidths=[4.5 * cm, 10.5 * cm])
        box_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg),
            ('ROUNDEDCORNERS', [6, 6, 6, 6]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(box_table)
        story.append(Spacer(1, 6))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 3. COME FUNZIONA
    # ════════════════════════════════════════════════════════
    story.append(Paragraph("3. Come funziona (schema generale)", styles['SectionTitle']))
    story.append(HorizontalLine())
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Il sistema è composto da diversi componenti che lavorano insieme. "
        "Ecco uno schema semplificato di come sono collegati:",
        styles['BodyText2']
    ))
    story.append(Spacer(1, 8))

    # Diagramma architettura
    arch_diagram = create_architecture_diagram()
    story.append(arch_diagram)

    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Gli <b>utenti</b> accedono al sistema tramite un browser web da qualsiasi dispositivo "
        "(computer, tablet o telefono). L'<b>applicazione</b> elabora le richieste, comunica con "
        "l'<b>archivio dati</b> per salvare e recuperare le informazioni, e si collega ai "
        "<b>dispositivi esterni</b> come bilance e stampanti.",
        styles['BodyText2']
    ))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 4. IL PROCESSO DI PESATURA
    # ════════════════════════════════════════════════════════
    story.append(Paragraph("4. Il processo di pesatura passo per passo", styles['SectionTitle']))
    story.append(HorizontalLine())
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Ecco come funziona una tipica operazione di pesatura dall'inizio alla fine:",
        styles['BodyText2']
    ))
    story.append(Spacer(1, 8))

    # Diagramma flusso
    flow_diagram = create_weighing_flow_diagram()
    story.append(flow_diagram)

    story.append(Spacer(1, 12))

    steps_detail = [
        ("<b>Passo 1 - Arrivo:</b> Il veicolo arriva alla pesa. L'operatore lo identifica tramite targa, badge RFID o inserimento manuale."),
        ("<b>Passo 2 - Identificazione:</b> Il sistema verifica i dati del veicolo, dell'autista e del materiale trasportato. Se c'era una prenotazione, i dati vengono caricati automaticamente."),
        ("<b>Passo 3 - Prima pesata:</b> Il veicolo sale sulla bilancia e il peso lordo viene registrato automaticamente nel sistema."),
        ("<b>Passo 4 - Operazioni:</b> Il veicolo si sposta per le operazioni di carico o scarico del materiale."),
        ("<b>Passo 5 - Seconda pesata:</b> Il veicolo torna sulla bilancia per la seconda pesata. Il sistema calcola il peso netto."),
        ("<b>Passo 6 - Documento:</b> Il sistema genera automaticamente un documento PDF con tutti i dettagli e, se configurato, lo stampa."),
    ]

    for step in steps_detail:
        story.append(Paragraph(step, styles['BulletItem']))
        story.append(Spacer(1, 2))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 5. I DATI CHE GESTISCE
    # ════════════════════════════════════════════════════════
    story.append(Paragraph("5. I dati che gestisce", styles['SectionTitle']))
    story.append(HorizontalLine())
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Il sistema mantiene un archivio organizzato di tutte le informazioni necessarie "
        "per le operazioni di pesatura:",
        styles['BodyText2']
    ))

    data_categories = [
        ["Categoria", "Cosa contiene", "Esempio"],
        ["Clienti/Fornitori", "Ragione sociale, telefono,\npartita IVA", "Rossi S.r.l."],
        ["Veicoli", "Targa, descrizione, tara", "AB123CD - Camion 3 assi"],
        ["Autisti", "Nome, telefono", "Mario Rossi"],
        ["Materiali", "Tipo di materiale", "Ghiaia, Sabbia, Ferro"],
        ["Operatori", "Personale alla pesa", "Operatore Turno 1"],
        ["Trasportatori", "Aziende di trasporto", "Trasporti Verdi S.r.l."],
        ["Pesate", "Data, peso, bilancia usata", "15/02/2026 - 18.500 kg"],
        ["Accessi", "Ingresso/uscita veicoli", "In attesa, Entrato, Chiuso"],
    ]

    col_widths = [3.5 * cm, 5.5 * cm, 5.5 * cm]
    data_table = Table(data_categories, colWidths=col_widths, repeatRows=1)
    data_table.setStyle(TableStyle([
        # Intestazione
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        # Righe
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), DARK_TEXT),
        # Alternanza colori
        ('BACKGROUND', (0, 1), (-1, 1), LIGHT_BLUE),
        ('BACKGROUND', (0, 2), (-1, 2), white),
        ('BACKGROUND', (0, 3), (-1, 3), LIGHT_BLUE),
        ('BACKGROUND', (0, 4), (-1, 4), white),
        ('BACKGROUND', (0, 5), (-1, 5), LIGHT_BLUE),
        ('BACKGROUND', (0, 6), (-1, 6), white),
        ('BACKGROUND', (0, 7), (-1, 7), LIGHT_BLUE),
        ('BACKGROUND', (0, 8), (-1, 8), white),
        # Bordi
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#BDC3C7")),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(data_table)

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 6. SICUREZZA E ACCESSI
    # ════════════════════════════════════════════════════════
    story.append(Paragraph("6. Sicurezza e accessi", styles['SectionTitle']))
    story.append(HorizontalLine())
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Il sistema protegge i dati con un sistema di autenticazione a più livelli. "
        "Ogni utente deve effettuare il login con nome utente e password.",
        styles['BodyText2']
    ))
    story.append(Spacer(1, 8))

    # Diagramma sicurezza
    security_diagram = create_security_diagram()
    story.append(security_diagram)

    story.append(Spacer(1, 12))

    security_features = [
        ("<b>Accesso protetto:</b> Ogni utente ha le proprie credenziali di accesso (nome utente e password)."),
        ("<b>Livelli di autorizzazione:</b> Tre livelli di accesso permettono di controllare chi può fare cosa."),
        ("<b>Protezione dei dati:</b> Le password sono cifrate e le sessioni hanno una scadenza automatica."),
        ("<b>Blocco record:</b> Quando un utente sta modificando un dato, gli altri utenti non possono modificarlo contemporaneamente, evitando conflitti."),
    ]

    for item in security_features:
        story.append(Paragraph(f"&bull;  {item}", styles['BulletItem']))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 7. I DISPOSITIVI COLLEGATI
    # ════════════════════════════════════════════════════════
    story.append(Paragraph("7. I dispositivi collegati", styles['SectionTitle']))
    story.append(HorizontalLine())
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "BARON IN-OUT si collega a diversi dispositivi esterni per automatizzare le operazioni:",
        styles['BodyText2']
    ))
    story.append(Spacer(1, 10))

    devices = [
        ("Bilance industriali",
         "Il cuore del sistema. Supporta diversi modelli di terminali di pesatura (DGT1, EGT-AF03) "
         "collegati tramite cavo seriale o rete. Il peso viene letto in tempo reale.",
         LIGHT_BLUE),
        ("Stampanti",
         "Stampanti termiche e di rete per la stampa automatica dei documenti di pesatura. "
         "Integrate tramite il sistema di stampa CUPS.",
         LIGHT_GREEN),
        ("Lettori RFID / Badge",
         "Per l'identificazione automatica dei veicoli tramite badge. "
         "Quando un badge viene letto, il sistema carica automaticamente i dati associati.",
         LIGHT_ORANGE),
        ("Pannelli e display",
         "Pannelli informativi che possono mostrare messaggi ai conducenti, "
         "come istruzioni o il peso corrente.",
         LIGHT_PURPLE),
        ("Sirene / allarmi",
         "Dispositivi di segnalazione per avvisare in caso di eventi particolari, "
         "come il superamento di soglie di peso.",
         LIGHT_RED),
    ]

    for title, desc, bg in devices:
        box_data = [
            [Paragraph(f"<b>{title}</b>", styles['BoxTitle'])],
            [Paragraph(desc, styles['BoxBody'])],
        ]
        box_table = Table(box_data, colWidths=[15 * cm])
        box_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg),
            ('ROUNDEDCORNERS', [6, 6, 6, 6]),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (0, 0), 10),
            ('BOTTOMPADDING', (-1, -1), (-1, -1), 10),
        ]))
        story.append(box_table)
        story.append(Spacer(1, 6))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 8. DOCUMENTI E REPORT
    # ════════════════════════════════════════════════════════
    story.append(Paragraph("8. Documenti e report", styles['SectionTitle']))
    story.append(HorizontalLine())
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Il sistema genera diversi tipi di documenti per le operazioni di pesatura:",
        styles['BodyText2']
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Tipi di documento", styles['SubSectionTitle']))

    doc_types = [
        ["Tipo", "Descrizione", "Formato"],
        ["Scontrino pesata", "Documento di pesata con tutti i dati\n(veicolo, peso, materiale, ecc.)", "PDF"],
        ["Report pesata ingresso", "Documento generato alla prima pesata", "PDF"],
        ["Report pesata uscita", "Documento finale con peso netto", "PDF"],
        ["Esportazione dati", "Elenco pesate per periodo selezionato", "CSV / Excel"],
    ]

    doc_table = Table(doc_types, colWidths=[4 * cm, 7.5 * cm, 3 * cm], repeatRows=1)
    doc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), DARK_TEXT),
        ('BACKGROUND', (0, 1), (-1, 1), LIGHT_BLUE),
        ('BACKGROUND', (0, 2), (-1, 2), white),
        ('BACKGROUND', (0, 3), (-1, 3), LIGHT_BLUE),
        ('BACKGROUND', (0, 4), (-1, 4), white),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#BDC3C7")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(doc_table)

    story.append(Spacer(1, 16))
    story.append(Paragraph("Formati supportati", styles['SubSectionTitle']))

    story.append(Paragraph(
        "I report possono essere generati in diversi formati di pagina per adattarsi "
        "alle esigenze di stampa:",
        styles['BodyText2']
    ))

    formats_data = [
        ["Formato", "Uso tipico"],
        ["A4", "Documenti standard"],
        ["A5", "Documenti ridotti"],
        ["A6 / A7 / A8", "Scontrini e ricevute piccole"],
        ["Scontrino 80mm", "Stampanti termiche a rotolo"],
    ]

    fmt_table = Table(formats_data, colWidths=[4 * cm, 10.5 * cm], repeatRows=1)
    fmt_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), DARK_TEXT),
        ('BACKGROUND', (0, 1), (-1, 1), LIGHT_BLUE),
        ('BACKGROUND', (0, 2), (-1, 2), white),
        ('BACKGROUND', (0, 3), (-1, 3), LIGHT_BLUE),
        ('BACKGROUND', (0, 4), (-1, 4), white),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#BDC3C7")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(fmt_table)

    story.append(Spacer(1, 16))

    # Box personalizzazione
    custom_data = [
        [Paragraph("<b>Personalizzazione dei report</b>", styles['BoxTitle'])],
        [Paragraph(
            "I documenti possono essere personalizzati tramite un editor visuale integrato. "
            "È possibile modificare il layout, aggiungere il logo aziendale, scegliere quali "
            "informazioni mostrare e impostare il formato di stampa preferito.",
            styles['BoxBody']
        )],
    ]
    custom_table = Table(custom_data, colWidths=[15 * cm])
    custom_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GREEN),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (0, 0), 12),
        ('BOTTOMPADDING', (-1, -1), (-1, -1), 12),
    ]))
    story.append(custom_table)

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 9. FUNZIONALITÀ AGGIUNTIVE
    # ════════════════════════════════════════════════════════
    story.append(Paragraph("9. Funzionalità aggiuntive", styles['SectionTitle']))
    story.append(HorizontalLine())
    story.append(Spacer(1, 8))

    extra_features = [
        ("Accesso remoto",
         "Il sistema può essere raggiunto da remoto tramite una connessione sicura (tunnel SSH), "
         "permettendo l'assistenza tecnica e il monitoraggio a distanza.",
         LIGHT_BLUE),
        ("Sincronizzazione file",
         "I documenti generati possono essere sincronizzati automaticamente con cartelle "
         "su altri computer o server, tramite diversi protocolli di rete.",
         LIGHT_GREEN),
        ("Modalità diagnostica",
         "Una modalità speciale per verificare il corretto funzionamento delle bilance, "
         "utile per la manutenzione e la taratura.",
         LIGHT_ORANGE),
        ("Fotografie delle pesate",
         "Il sistema può acquisire foto durante le operazioni di pesatura, "
         "che vengono allegate al documento finale.",
         LIGHT_PURPLE),
        ("Modalità automatica e semiautomatica",
         "Il sistema può operare in modalità completamente automatica (con badge e prenotazioni) "
         "o semiautomatica (con intervento dell'operatore).",
         LIGHT_RED),
        ("Aggiornamento in tempo reale",
         "Tutti gli utenti collegati vedono gli aggiornamenti istantaneamente, "
         "senza bisogno di ricaricare la pagina.",
         LIGHT_BLUE),
    ]

    for title, desc, bg in extra_features:
        box_data = [
            [Paragraph(f"<b>{title}</b>", styles['BoxTitle'])],
            [Paragraph(desc, styles['BoxBody'])],
        ]
        box_table = Table(box_data, colWidths=[15 * cm])
        box_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg),
            ('ROUNDEDCORNERS', [6, 6, 6, 6]),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (0, 0), 10),
            ('BOTTOMPADDING', (-1, -1), (-1, -1), 10),
        ]))
        story.append(box_table)
        story.append(Spacer(1, 6))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 10. DOMANDE FREQUENTI
    # ════════════════════════════════════════════════════════
    story.append(Paragraph("10. Domande frequenti", styles['SectionTitle']))
    story.append(HorizontalLine())
    story.append(Spacer(1, 8))

    faqs = [
        ("Da quali dispositivi posso accedere al sistema?",
         "Da qualsiasi dispositivo con un browser web: computer, tablet o smartphone. "
         "Non è necessario installare alcun programma aggiuntivo."),
        ("I dati sono al sicuro?",
         "Sì. Il sistema utilizza password cifrate, sessioni con scadenza automatica "
         "e un sistema di blocco per evitare modifiche simultanee ai dati."),
        ("Quante bilance posso collegare?",
         "Il sistema supporta più bilance contemporaneamente. Ogni bilancia può essere "
         "configurata indipendentemente con i propri parametri."),
        ("Posso personalizzare i documenti di stampa?",
         "Sì, tramite un editor visuale integrato è possibile personalizzare completamente "
         "il layout e il contenuto dei documenti di pesatura."),
        ("Il sistema funziona senza connessione internet?",
         "Sì, il sistema funziona in rete locale. La connessione internet è necessaria "
         "solo per l'accesso remoto e la sincronizzazione con server esterni."),
        ("Posso esportare i dati delle pesate?",
         "Sì, è possibile esportare i dati in formato CSV e Excel per analisi "
         "e archiviazione esterna."),
        ("Cosa succede se si spegne il computer?",
         "Tutti i dati sono salvati in modo permanente nell'archivio. Al riavvio del sistema, "
         "tutte le informazioni saranno disponibili esattamente come prima."),
    ]

    for question, answer in faqs:
        faq_data = [
            [Paragraph(f"<b>D: {question}</b>", styles['BoxTitle'])],
            [Paragraph(f"R: {answer}", styles['BoxBody'])],
        ]
        faq_table = Table(faq_data, colWidths=[15 * cm])
        faq_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), LIGHT_BLUE),
            ('BACKGROUND', (0, 1), (0, 1), HexColor("#F8F9FA")),
            ('ROUNDEDCORNERS', [6, 6, 6, 6]),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (0, 0), 10),
            ('BOTTOMPADDING', (-1, -1), (-1, -1), 10),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, HexColor("#BDC3C7")),
        ]))
        story.append(faq_table)
        story.append(Spacer(1, 8))

    # ── Footer finale ──
    story.append(Spacer(1, 20))
    story.append(HorizontalLine(color=PRIMARY, thickness=1))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "BARON IN-OUT v3.0.1 - Documento generato automaticamente",
        styles['FooterText']
    ))
    story.append(Paragraph(
        "Questo documento è destinato a fornire una panoramica semplificata del sistema. "
        "Per dettagli tecnici, consultare la documentazione tecnica completa.",
        styles['FooterText']
    ))

    # ── Genera il PDF ──
    doc.build(story)
    print(f"PDF generato con successo: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
