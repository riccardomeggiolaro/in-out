import json
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

def replace_placeholder(text, replacements):
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)
    return text

def create_pdf(canvas_data, replacements, output_file='output.pdf'):
    data = json.loads(canvas_data)
    objects = data["canvasData"]["objects"]

    c = canvas.Canvas(output_file, pagesize=A4)
    width, height = A4

    c.setFillColorRGB(0, 0, 0)

    for obj in objects:
        if obj["type"] == "rectWithText":
            c.setStrokeColorRGB(0, 0, 0)
            c.setLineWidth(obj["strokeWidth"])
            rect_y = height - obj["top"] - obj["height"]
            c.rect(obj["left"], rect_y, obj["width"], obj["height"])

            if obj["text"]["type"] == "i-text":
                text = replace_placeholder(obj["text"]["text"], replacements)
                font_size = obj["text"]["fontSize"]
                line_height = obj["text"]["lineHeight"]

                c.setFont("Times-Roman", font_size)
                text_width = c.stringWidth(text, "Times-Roman", font_size)

                # Stima iniziale dell'altezza del testo (può richiedere aggiustamenti)
                text_height = font_size * line_height

                text_left = obj["left"] + (obj["width"] - text_width) / 2

                # Centramento verticale con aggiustamento fine (da fare manualmente)
                text_top = rect_y + (obj["height"] - text_height) / 2

                # Aggiustamento fine (valori tipici: -1, -0.5, 0, +0.5, +1)
                offset = 0  # <--- *REGOLA QUESTO VALORE* dopo aver visto il PDF
                text_top += offset

                c.drawString(text_left, text_top, text)

    c.save()


# Dati JSON (inserisci qui il tuo JSON completo)
canvas_data = '''
{"formatPaper":"A4","canvasData":{"version":"5.3.0","objects":[{"type":"i-text","version":"5.3.0","originX":"left","originY":"top","left":264.86,"top":403.49,"width":64.56,"height":33.9,"fill":"black","stroke":null,"strokeWidth":1,"strokeDashArray":null,"strokeLineCap":"butt","strokeDashOffset":0,"strokeLineJoin":"miter","strokeUniform":false,"strokeMiterLimit":4,"scaleX":1,"scaleY":1,"angle":0,"flipX":false,"flipY":false,"opacity":1,"shadow":null,"visible":true,"backgroundColor":"","fillRule":"nonzero","paintFirst":"fill","globalCompositeOperation":"source-over","skewX":0,"skewY":0,"fontFamily":"Times New Roman","fontWeight":"normal","fontSize":30,"text":"Testo","underline":false,"overline":false,"linethrough":false,"textAlign":"left","fontStyle":"normal","lineHeight":1.16,"textBackgroundColor":"","charSpacing":0,"styles":[],"direction":"ltr","path":null,"pathStartOffset":0,"pathSide":"left","pathAlign":"baseline","selectable":true,"hasControls":true,"hasBorders":true,"editable":true}],"background":"white"}}
'''


# Definisci le sostituzioni per i segnaposto
replacements = {
    '[weight2]': '10 kg',  # Sostituisci [weight2] con "10 kg"
    '[supplier]': 'Supplier XYZ'  # Sostituisci [supplier] con "Supplier XYZ"
}

# Crea il PDF con i dati e le sostituzioni
create_pdf(canvas_data, replacements)