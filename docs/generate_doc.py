from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE

doc = Document()

# --- Styles ---
style = doc.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(11)
style.paragraph_format.space_after = Pt(6)

for level in range(1, 4):
    h = doc.styles[f'Heading {level}']
    h.font.name = 'Calibri'
    h.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)

# --- Title ---
title = doc.add_heading('Sistema di Controllo Sbarre con Priorità Veicoli', level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
for run in title.runs:
    run.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)

doc.add_paragraph(
    'Sistema di gestione accessi e pesatura con doppia sbarra e priorità veicoli, '
    'integrato con un sistema esterno di identificazione targhe.'
)

# --- Fase 1 ---
doc.add_heading('1. Il Processo', level=1)
doc.add_heading('Fase 1: Arrivo del Mezzo', level=2)

items = [
    'Il veicolo arriva all\'ingresso del sito.',
    'Il sistema esterno (del cliente) identifica la targa tramite telecamera.',
    'Il sistema esterno chiama la nostra API per creare un accesso, passando:',
]
for item in items:
    doc.add_paragraph(item, style='List Number')

sub_items = ['Targa del veicolo', 'Data/Ora dell\'arrivo', 'Slot assegnato (fascia oraria o posizione)', 'Priorità (determina quale sbarra aprire)']
for s in sub_items:
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.left_indent = Cm(2.5)
    p.add_run(s)

p = doc.add_paragraph('L\'accesso può essere di due tipi:')
p.paragraph_format.space_before = Pt(6)

types = [
    ('Con pesatura', 'accesso normale, il veicolo verrà pesato sulla Pesa 2.'),
    ('Solo transito', 'senza pesatura, viene registrato solo il passaggio.'),
]
for bold_text, desc in types:
    p = doc.add_paragraph(style='List Bullet')
    run = p.add_run(bold_text + ': ')
    run.bold = True
    p.add_run(desc)

# --- Fase 2 ---
doc.add_heading('Fase 2: Apertura Sbarra in Base alla Priorità', level=2)

doc.add_paragraph(
    'Il software monitora continuamente la Pesa 1. '
    'Quando la pesa è vuota (peso sotto la soglia minima):'
)

steps = [
    'Cerca il prossimo accesso in coda (sia con pesatura che solo transito), ordinato per priorità decrescente. A parità di priorità viene servito il più vecchio.',
    'In base alla priorità del veicolo selezionato:\n'
    '    • Priorità ALTA → Apre Sbarra 1 (corsia preferenziale)\n'
    '    • Priorità BASSA → Apre Sbarra 2 (corsia normale)',
    'Mostra la targa sul pannello e attiva la sirena.',
    'Quando il veicolo sale sulla pesa (peso rilevato) → chiude la sbarra.',
]
for s in steps:
    doc.add_paragraph(s, style='List Number')

# --- Fase 3 ---
doc.add_heading('Fase 3: Pesatura Automatica sulla Pesa 2', level=2)

doc.add_paragraph('Per i veicoli con accesso con pesatura:')

steps = [
    'Il veicolo procede dalla Pesa 1 alla Pesa 2.',
    'Viene identificato automaticamente tramite telecamera (targa) o badge RFID.',
    'Il sistema esegue la pesata automatica: attende stabilità del peso, registra il peso, genera report.',
    'L\'accesso viene chiuso.',
]
for s in steps:
    doc.add_paragraph(s, style='List Number')

# --- Fase 4 ---
doc.add_heading('Fase 4: Transito Senza Pesata', level=2)

doc.add_paragraph('Per i veicoli registrati come solo transito:')

steps = [
    'Le sbarre si aprono normalmente in base alla priorità.',
    'Il veicolo transita sulla Pesa 1 ma la pesatura NON scatta.',
    'Viene registrato solo il passaggio (data/ora).',
    'Utile per veicoli di servizio o mezzi che non necessitano di pesatura.',
]
for s in steps:
    doc.add_paragraph(s, style='List Number')

# --- Schema del Processo ---
doc.add_heading('2. Schema del Processo', level=1)

schema = (
    'Sistema Esterno          Nostro Software            Pesa 1          Sbarra 1/2       Pesa 2\n'
    '     │                        │                       │                 │               │\n'
    '     │  POST /access          │                       │                 │               │\n'
    '     │  (targa, slot,         │                       │                 │               │\n'
    '     │   priorità, tipo)      │                       │                 │               │\n'
    '     │───────────────────────►│                       │                 │               │\n'
    '     │                        │  Salva accesso        │                 │               │\n'
    '     │                        │                       │                 │               │\n'
    '     │                        │  [Monitoraggio Pesa]  │                 │               │\n'
    '     │                        │◄──────────────────────│ pesa vuota      │               │\n'
    '     │                        │                       │                 │               │\n'
    '     │                        │  Cerca prossimo       │                 │               │\n'
    '     │                        │  per priorità         │                 │               │\n'
    '     │                        │                       │                 │               │\n'
    '     │                        │  Apri sbarra ─────────────────────────►│               │\n'
    '     │                        │  (1 o 2 da priorità)  │                 │ APERTA        │\n'
    '     │                        │                       │                 │               │\n'
    '     │                        │  Pannello + Sirena    │                 │               │\n'
    '     │                        │                       │                 │               │\n'
    '     │                  [Veicolo sale sulla pesa]      │                 │               │\n'
    '     │                        │◄──────────────────────│ peso rilevato   │               │\n'
    '     │                        │                       │                 │               │\n'
    '     │                        │  Chiudi sbarra ───────────────────────►│ CHIUSA        │\n'
    '     │                        │                       │                 │               │\n'
    '     │                        │  ┌─ SE solo transito: │                 │               │\n'
    '     │                        │  │  Registra passaggio│                 │               │\n'
    '     │                        │  │  FINE              │                 │               │\n'
    '     │                        │  │                    │                 │               │\n'
    '     │                        │  └─ SE con pesatura:  │                 │               │\n'
    '     │                        │     Veicolo va a Pesa 2                │               │\n'
    '     │                        │                       │                 │               │\n'
    '     │                        │  Identificazione ─────────────────────────────────────►│\n'
    '     │                        │  (telecamera/badge)   │                 │               │\n'
    '     │                        │◄──────────────────────────────────────────────────────│\n'
    '     │                        │  Pesatura automatica  │                 │               │\n'
    '     │                        │  Accesso chiuso       │                 │               │\n'
)

p = doc.add_paragraph()
run = p.add_run(schema)
run.font.name = 'Consolas'
run.font.size = Pt(8)

# --- Cosa Serve ---
doc.add_heading('3. Cosa Serve Implementare', level=1)

doc.add_heading('Tabella transit_access', level=2)
doc.add_paragraph(
    'Tabella separata per i soli transiti (senza pesatura). '
    'Contiene: targa, slot, priorità, sbarra usata, data ingresso/uscita, note, ID dal sistema esterno.'
)

doc.add_heading('API per il Sistema Esterno', level=2)
doc.add_paragraph('Endpoint per il sistema esterno per caricare gli accessi:')
apis = [
    ('POST /api/open-to-customer/access', 'Crea accesso con pesatura (con targa, slot, priorità)'),
    ('POST /api/open-to-customer/transit-access', 'Crea accesso solo transito (con targa, slot, priorità)'),
]
for endpoint, desc in apis:
    p = doc.add_paragraph(style='List Bullet')
    run = p.add_run(endpoint)
    run.bold = True
    run.font.name = 'Consolas'
    run.font.size = Pt(10)
    p.add_run(f' — {desc}')

doc.add_heading('Automatismo Apertura Sbarre', level=2)
steps = [
    'Nel Callback Realtime, quando la pesa è vuota: cercare il prossimo accesso/transito in coda per priorità.',
    'Aprire il relè della sbarra corretta (configurazione gate → relè).',
    'Quando il veicolo sale sulla pesa, chiudere la sbarra.',
    'Se è un transito → registrare solo il passaggio, non avviare pesatura.',
    'Se è un accesso normale → procedere con il flusso di pesatura esistente.',
]
for s in steps:
    doc.add_paragraph(s, style='List Number')

# --- Esempi ---
doc.add_heading('4. Esempi Pratici', level=1)

doc.add_heading('Veicolo priorità alta con pesatura', level=2)
doc.add_paragraph(
    'Sistema esterno invia targa + priorità 3 → pesa vuota → apre Sbarra 1 → '
    'veicolo pesa su Pesa 1 → chiude sbarra → va a Pesa 2 → pesatura automatica → accesso chiuso.'
)

doc.add_heading('Veicolo solo transito', level=2)
doc.add_paragraph(
    'Sistema esterno invia targa + priorità 2 + tipo transito → pesa vuota → '
    'apre sbarra in base a priorità → veicolo passa → chiude sbarra → '
    'registra passaggio → nessuna pesatura.'
)

doc.add_heading('Coda mista', level=2)
doc.add_paragraph(
    'Tre veicoli in coda con priorità 1, 3, 2 → viene servito prima quello con priorità 3 (Sbarra 1), '
    'poi 2 (Sbarra 1), poi 1 (Sbarra 2).'
)

# --- Save ---
doc.save('/home/user/in-out/docs/VEHICLE_PRIORITY_GATE_CONTROL.docx')
print("Done")
