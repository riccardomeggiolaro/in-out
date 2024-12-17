import { initAligningGuidelines } from './guide-lines.js';
import { initCenteringGuidelines } from './centering-guide-lines.js';

fabric.RectWithText = fabric.util.createClass(fabric.Rect, {
    type: 'rectWithText',
    text: null,

    initialize: function (rectOptions, textOptions, text) {
        // Call the rectangle constructor
        this.callSuper('initialize', rectOptions);

        // Listener per il ridimensionamento
        this.on('scaling', function() {
            // Larghezza minima basata sulla larghezza del testo
            const minWidth = this.text.width;
            
            // Altezza minima basata sull'altezza del testo
            const minHeight = this.text.height;

            // Calcola le dimensioni attuali
            const currentWidth = this.width * this.scaleX;
            const currentHeight = this.height * this.scaleY;

            // Gestisci la larghezza minima
            if (currentWidth < minWidth) {
                this.set({
                    scaleX: minWidth / this.width
                });
            }

            // Gestisci l'altezza minima
            if (currentHeight < minHeight) {
                this.set({
                    scaleY: minHeight / this.height
                });
            }
        });

        // Create the text
        this.text = new fabric.IText(text, {
            ...textOptions,
            selectable: false,
            evented: false,
            hasControls: false,
            hasBorders: false
        });

        // Improved centering function
        const centerText = () => {
            if (!this.canvas) return;

            // Calculate the center of the rectangle
            const center = this.getCenterPoint();

            // Update text position and properties
            this.text.set({
                left: center.x,
                top: center.y,
                originX: 'center',
                originY: 'center',
            });
        };

        // Event handlers to keep text synchronized
        const syncTextPosition = () => {
            centerText();
        };

        // Add event listeners
        this.on('moving', syncTextPosition);
        this.on('rotating', syncTextPosition);
        this.on('scaling', syncTextPosition);
        this.on('resizing', syncTextPosition);

        // Add and remove text from canvas
        this.on('added', () => {
            this.canvas.add(this.text);
            centerText();
        });

        // Handle text editing
        this.on('mousedown:before', () => {
            this._prevObjectStacking = this.canvas.preserveObjectStacking;
            this.canvas.preserveObjectStacking = true;
        });

        this.on('mousedblclick', () => {
            console.log(this.deletedText);
            if (this.deletedText) return;
            this.text.selectable = true;
            this.text.evented = true;
            this.canvas.setActiveObject(this.text);
            this.text.enterEditing();
            this.selectable = false;
        });

        this.on('deselected', () => {
            this.canvas.preserveObjectStacking = this._prevObjectStacking;
        });

        this.text.on('editing:exited', () => {
            this.text.selectable = false;
            this.text.evented = false;
            this.selectable = true;
        });

        // Aggiungi un listener per rilevare quando il testo viene eliminato
        this.text.on('deleted', () => {
            this.deletedText = true;
        });

        // Listener per l'editing del testo 
        this.text.on('changed', () => {
            const width = this.width * this.scaleX;
            const height = this.height * this.scaleY;
            if (this.text.width >= width) {
                this.set({
                    width: this.text.width / this.scaleX
                })
            }
            if (this.text.height >= height) {
                this.set({
                    height: this.text.height / this.scaleY
                })
            }
            // Quando finisce l'editing, ricalcola la larghezza 
            this.text.set({ 
                width: null, // Forza ricalcolo larghezza
                height: null // Forza ricalcolo altezza
            }); 
            this.text.initDimensions();
            // Ricalcola dimensioni 
            // Centra nuovamente il testo 
            const center = this.getCenterPoint(); 
            this.text.set({ left: center.x, top: center.y, originX: 'center', originY: 'center' }); 
        });

        this.text.on('editing:exited', () => {
            if (/^\s*$/.test(this.text.text)) {
                this.text.set({
                    text: ''
                });
            }
        });
    },

    // Metodo per clonare correttamente l'oggetto personalizzato
    clone: function(callback) {
        var clonedRect = new fabric.RectWithText(this.toObject(), this.text.toObject(), this.text.text);
        clonedRect.set({
            left: this.left + 10,  // Spostamento per evitare sovrapposizioni
            top: this.top + 10
        });
        callback(clonedRect);
    }
});

const paperSizes = {
    A4: { 
        width: 595.28, 
        height: 841.89, 
        dpi: 300,
        margins: {
            top: 25,   // 25 points to px
            bottom: 25,  // 25 points to px
            left: 31.75,   // 31.75 points to px
            right: 31.75   // 31.75 points to px
        }
    },
    A5: { 
        width: 419.53, 
        height: 595.28, 
        dpi: 300,
        margins: {
            top: 25.4,    // 25.4 points to px
            bottom: 25.4,   // 25.4 points to px
            left: 31.75,   // 31.75 points to px
            right: 31.75   // 31.75 points to px
        }
    },
    A8: { 
        width: 209.76, 
        height: 297.64, 
        dpi: 300,
        margins: {
            top: 25.4,    // 25.4 points to px
            bottom: 25.4,   // 25.4 points to px
            left: 31.75,   // 31.75 points to px
            right: 31.75   // 31.75 points to px
        }
    }
};

let canvas;
let gridLayer;
let grid = 20;
let midlineLayer;
let marginLayer;
let currentTool = 'text';
const formatSelect = document.getElementById('format-select');
const canvasElement = document.getElementById('canvas');

function createMargins(width, height, margins) {
    const size = paperSizes[formatSelect.value];

    if (marginLayer) {
        canvas.remove(marginLayer);
    }

    console.log(width)

    marginLayer = new fabric.Group([], {
        width: width,
        height: height,
        selectable: false,
        evented: false
    });

    // Calcola i margini in pixel
    const topMargin = margins.top;
    const bottomMargin = height - margins.bottom;
    const leftMargin = margins.left;
    const rightMargin = width - margins.right;

    // Linea superiore dei margini
    const topLine = new fabric.Line([0, topMargin, width, topMargin], {
        stroke: '#0000FF',
        strokeWidth: 1,
        selectable: false,
        evented: false
    });

    // Linea inferiore dei margini
    const bottomLine = new fabric.Line([0, bottomMargin, width, bottomMargin], {
        stroke: '#0000FF',
        strokeWidth: 1,
        selectable: false,
        evented: false
    });

    // Linea sinistra dei margini
    const leftLine = new fabric.Line([leftMargin, 0, leftMargin, height], {
        stroke: '#0000FF',
        strokeWidth: 1,
        selectable: false,
        evented: false
    });

    // Linea destra dei margini
    const rightLine = new fabric.Line([rightMargin, 0, rightMargin, height], {
        stroke: '#0000FF',
        strokeWidth: 1,
        selectable: false,
        evented: false
    });

    // Aggiungi le linee di margine al gruppo
    marginLayer.addWithUpdate(topLine);
    marginLayer.addWithUpdate(bottomLine);
    marginLayer.addWithUpdate(leftLine);
    marginLayer.addWithUpdate(rightLine);

    // Aggiungi il gruppo di margini al canvas
    canvas.add(marginLayer);
    marginLayer.sendToBack(); // Metti il gruppo dei margini dietro agli altri oggetti

    // Restituisci le coordinate dei margini per eventuali usi futuri
    return {
        topMargin,
        bottomMargin,
        leftMargin,
        rightMargin
    };
}

export function toggleMargins() {
    const marginToggle = document.getElementById('margin-toggle');
    const size = paperSizes[formatSelect.value];

    if (marginToggle.checked) {
        createMargins(size.width, size.height, size.margins);
    } else if (marginToggle) {
        canvas.remove(marginLayer);
        marginToggle = null;
    }
}

function createMidlines(width, height) {
    if (midlineLayer) {
        canvas.remove(midlineLayer);
    }

    midlineLayer = new fabric.Group([], {
        width: width,
        height: height,
        selectable: false,
        evented: false
    });

    // Vertical midline at the center
    const verticalMidline = new fabric.Line([width/2, 0, width/2, height], {
        stroke: '#FF4500',
        strokeWidth: 1,
        selectable: false,
        evented: false
    });

    // Horizontal midline at the center
    const horizontalMidline = new fabric.Line([0, height/2, width, height/2], {
        stroke: '#FF4500',
        strokeWidth: 1,
        selectable: false,
        evented: false
    });

    midlineLayer.addWithUpdate(verticalMidline);
    midlineLayer.addWithUpdate(horizontalMidline);

    canvas.add(midlineLayer);
    midlineLayer.sendToBack();
}

export function toggleMidlines() {
    const midlineToggle = document.getElementById('midline-toggle');
    const size = paperSizes[formatSelect.value];

    if (midlineToggle.checked) {
        createMidlines(size.width, size.height);
    } else if (midlineLayer) {
        canvas.remove(midlineLayer);
        midlineLayer = null;
    }
}

function createGrid(width, height, gridSize = 20) {
    if (gridLayer) {
        canvas.remove(gridLayer);
    }

    gridLayer = new fabric.Group([], {
        width: width,
        height: height,
        selectable: false,
        evented: false
    });

    for (let x = 0; x <= width; x += gridSize) {
        const vLine = new fabric.Line([x, 0, x, height], {
            stroke: '#e0e0e0',
            strokeWidth: x % 50 === 0 ? 1 : 0.5,
            selectable: false,
            evented: false
        });
        gridLayer.addWithUpdate(vLine);
    }

    for (let y = 0; y <= height; y += gridSize) {
        const hLine = new fabric.Line([0, y, width, y], {
            stroke: '#e0e0e0',
            strokeWidth: y % 50 === 0 ? 1 : 0.5,
            selectable: false,
            evented: false
        });
        gridLayer.addWithUpdate(hLine);
    }

    canvas.add(gridLayer);
    gridLayer.sendToBack();
}

export function toggleGrid() {
    const gridToggle = document.getElementById('grid-toggle');
    if (gridToggle.checked) {
        const size = paperSizes[formatSelect.value];
        createGrid(size.width, size.height);
    } else if (gridLayer) {
        canvas.remove(gridLayer);
        gridLayer = null;
    }
}

function initCanvas(format) {
    if (canvas) {
        canvas.dispose();
    }

    const size = paperSizes[format];
    
    canvas = new fabric.Canvas('canvas', {
        backgroundColor: 'white',
        selection: true,
        preserveObjectStacking: true,
        width: size.width,
        height: size.height
    });

    // Verifica se la griglia deve essere mostrata
    const gridToggle = document.getElementById('grid-toggle');
    if (gridToggle && gridToggle.checked) {
        createGrid(size.width, size.height);
    }

    // Verifica se i midlines devono essere mostrati
    const midlineToggle = document.getElementById('midline-toggle');
    if (midlineToggle && midlineToggle.checked) {
        createMidlines(size.width, size.height);
    }

    const marginToggle = document.getElementById('margin-toggle');
    if (marginToggle && marginToggle.checked) {
        createMargins(size.width, size.height, size.margins);
    }

    canvas.on('selection:created', showControls);
    canvas.on('selection:updated', showControls);
    canvas.on('selection:cleared', hideControls);
    initAligningGuidelines(canvas);
    initCenteringGuidelines(canvas);
}

function colorNameToHex(color) {
    // Crea un elemento temporaneo per utilizzare la conversione del colore del browser
    const tempElement = document.createElement('div');
    tempElement.style.color = color;
    document.body.appendChild(tempElement);
    
    // Ottiene il colore computato in formato RGB
    const computedColor = window.getComputedStyle(tempElement).color;
    
    // Rimuove l'elemento temporaneo
    document.body.removeChild(tempElement);
    
    // Converte il colore RGB in hex
    const rgbMatch = computedColor.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
    if (rgbMatch) {
        const [, r, g, b] = rgbMatch;
        // Converte i valori decimali in esadecimale e aggiunge zeri iniziali se necessario
        return "#" + 
            parseInt(r).toString(16).padStart(2, '0') +
            parseInt(g).toString(16).padStart(2, '0') +
            parseInt(b).toString(16).padStart(2, '0');
    }
    
    // Se la conversione fallisce, restituisce un colore predefinito
    return '#000000';
}

function showControls(e) {
    console.log("show");

    const activeObj = canvas.getActiveObject();
    const textControls = document.getElementById('text-controls');
    const rectWithTextControls = document.getElementById('rectangle-controls');
    const lineControls = document.getElementById('line-controls');

    // Nascondi tutti i controlli di default
    textControls.style.display = 'none';
    rectWithTextControls.style.display = 'none';
    lineControls.style.display = 'none';    

    console.log(activeObj.type);

    // Controlla che activeObj esista prima di accedere al suo tipo
    if (activeObj && activeObj.type === 'i-text') {
        textControls.style.display = 'flex';
        
        document.getElementById('font-size-text').value = activeObj.fontSize;
        // document.getElementById('align-text').value = activeObj.textAlign;
        document.getElementById('font-family-text').value = activeObj.fontFamily;
        try {
            document.getElementById('database-data-text').value = activeObj.text;
        } catch {}
    } else if (activeObj && activeObj.type === 'rectWithText') {
        rectWithTextControls.style.display = 'flex';
        
        // Converti i colori in formato hex
        const fillColor = activeObj.fill ? colorNameToHex(activeObj.fill) : '#ffffff';
        const strokeColor = activeObj.stroke ? colorNameToHex(activeObj.stroke) : '#000000';
        
        document.getElementById('fill-color-rect').value = fillColor;
        document.getElementById('stroke-color-rect').value = strokeColor;
        document.getElementById('stroke-width-rect').value = activeObj.strokeWidth || 1;
    } else if (activeObj && activeObj.type === 'line') {
        lineControls.style.display = 'flex';
        
        // Converti i colori in formato hex
        const strokeColor = activeObj.stroke ? colorNameToHex(activeObj.stroke) : '#000000';
        
        document.getElementById('color-line').value = strokeColor;
        document.getElementById('stroke-width-line').value = activeObj.strokeWidth || 1;
    }
}

function hideControls() {
    console.log("hide")

    document.getElementById('text-controls').style.display = 'none';
    document.getElementById('rectangle-controls').style.display = 'none';
    document.getElementById('line-controls').style.display = 'none';
}

export function setTool(tool) {
    document.querySelectorAll('#tool-buttons button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    event.target.classList.add('active');
    
    currentTool = tool;
    console.log("set")
}

initCanvas('A4');

formatSelect.addEventListener('change', (e) => {
    initCanvas(e.target.value);
});

function addText() {
    const text = new fabric.IText('Testo', {
        left: 50,
        top: 50,
        fontSize: 30,
        fill: 'black',
        cornerSize: 12,
        transparentCorners: false,
        hasControls: true,     // Mostra i controlli di ridimensionamento
    });
    canvas.add(text);
    canvas.setActiveObject(text);
}

function addLine() {
    const line = new fabric.Line([0, 200, 200, 200], {
        stroke: 'black',
        selectable: true,
        evented: true,
        hasControls: true,
        strokeWidth: 1,
        noScaleCache: false,
        strokeUniform: true
    });
    canvas.add(line);
    canvas.setActiveObject(line);
    // Personalizza i controlli per avere solo quello per la larghezza
    line.setControlsVisibility({
        tl: false, // Non mostrare il controllo in alto a sinistra
        tr: false, // Non mostrare il controllo in alto a destra
        bl: false, // Non mostrare il controllo in basso a sinistra
        br: false, // Non mostrare il controllo in basso a destra
        mt: false, // Non mostrare il controllo al centro in alto
        mb: false, // Non mostrare il controllo al centro in basso
        ml: true, // Non mostrare il controllo a sinistra
        mr: true,  // Mostra solo il controllo a destra per la larghezza
    });
    // Imposta il controllo di ridimensionamento orizzontale per la larghezza
    line.set({ lockScalingY: true }); // Blocca la scalabilità verticale
}

const rectOptions = {
    left: 10,
    top: 10,
    width: 200,
    height: 75,
    fill: '#ffffff',
    stroke: 'black',
    strokeWidth: 1,
    noScaleCache: false,
    strokeUniform: true
}

const textOptions = {
    fill: 'black',
    fontSize: 30,
    selectable: true,
    textAlign: 'center'
}

function addRectangleText() {
    const rectText = new fabric.RectWithText(rectOptions, textOptions, '');
    canvas.add(rectText);
    canvas.setActiveObject(rectText);
}

export function deleteSelected() {
    const activeObjects = canvas.getActiveObjects();  // Ottieni tutti gli oggetti selezionati

    if (activeObjects.length > 0) {
        // Itera su ogni oggetto selezionato
        activeObjects.forEach(activeObject => {
            // Trova il contenitore RectWithText se esiste
            const parentRectWithText = canvas.getObjects().find(obj => 
                obj.type === 'rectWithText' && 
                (obj === activeObject || obj.text === activeObject)
            );
            
            // Se è un oggetto RectWithText, rimuovi l'intero contenitore
            if (parentRectWithText) {
                canvas.remove(parentRectWithText);
                canvas.remove(parentRectWithText.text);
            } else {
                // Altrimenti procedi con la rimozione normale
                canvas.remove(activeObject);
            }
        });

        // Deselect all objects after removal
        canvas.discardActiveObject();
        canvas.renderAll();  // Rende il canvas di nuovo aggiornato dopo le modifiche
    }
}

export function updateText() {
    const activeObject = canvas.getActiveObject();
    if (activeObject && activeObject.type === 'i-text') {
        activeObject.set({
            fontSize: parseInt(document.getElementById('font-size-text').value),
            fontFamily: document.getElementById('font-family-text').value,
            // textAlign: document.getElementById('align-text').value
            text: document.getElementById('database-data-text').value
        });
        canvas.requestRenderAll(); // Metodo più affidabile per aggiornare il canvas
        // Trova il contenitore RectWithText se esiste
        const parentRectWithText = canvas.getObjects().find(obj => 
            obj.type === 'rectWithText' && 
            (obj === activeObject || obj.text === activeObject)
        );
        if (parentRectWithText) {
            // Emetti manualmente l'evento 'changed' per il testo
            activeObject.fire('changed');
        }
    }
}

export function updateRectWithText() {
    const activeObj = canvas.getActiveObject();
    if (activeObj && activeObj.type === 'rectWithText') {
        activeObj.set({
            fill: document.getElementById('fill-color-rect').value,
            stroke: document.getElementById('stroke-color-rect').value,
            strokeWidth: parseInt(document.getElementById('stroke-width-rect').value)
        });
        canvas.requestRenderAll();
    }
}

export function updateLine() {
    const activeObj = canvas.getActiveObject();
    if (activeObj && activeObj.type === 'line') {
        activeObj.set({
            stroke: document.getElementById('color-line').value,
            strokeWidth: parseInt(document.getElementById('stroke-width-line').value)
        });
        canvas.requestRenderAll();
    }
}

export function exportToPDF() {
    const format = formatSelect.value;
    const size = paperSizes[format];

    if (midlineLayer) {
        canvas.remove(midlineLayer);
    }

    // Rimuovi la griglia temporaneamente
    if (gridLayer) {
        canvas.remove(gridLayer);
    }

    if (marginLayer) {
        canvas.remove(marginLayer);
    }

    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF({
        unit: 'px',
        format: [size.width, size.height],
        orientation: size.width > size.height ? 'l' : 'p'
    });

    // Esporta con alta qualità
    const imgData = canvas.toDataURL({ 
        format: 'png', 
        quality: 1, 
    });

    pdf.addImage(imgData, 'PNG', 0, 0, size.width, size.height, '', 'FAST');
    
    // Ripristina la griglia
    if (midlineLayer) {
        canvas.add(midlineLayer);
        midlineLayer.sendToBack();
    }

    // Ripristina la griglia
    if (gridLayer) {
        canvas.add(gridLayer);
        gridLayer.sendToBack();
    }

    // Ripristina i margini
    if (marginLayer) {
        canvas.add(marginLayer);
        marginLayer.sendToBack();
    }

    pdf.save(`receipt_${format}.pdf`);
}

document.getElementById('tool-buttons').addEventListener('click', (e) => {
    switch(e.target.innerText) {
        case 'Testo':
            addText();
            break;
        case 'Rettangolo':
            addRectangleText();
            break;
        case 'Linea':
            addLine();
            break;
        default:
            break;
    }
});

// If you want to make these globally accessible for HTML inline events
window.setTool = setTool;
window.deleteSelected = deleteSelected;
window.exportToPDF = exportToPDF;
window.toggleGrid = toggleGrid;
window.toggleMidlines = toggleMidlines;
window.toggleMargins = toggleMargins;
window.updateText = updateText;
window.updateRectWithText = updateRectWithText;
window.updateLine = updateLine;

// Dichiarazione della variabile per memorizzare l'oggetto copiato
var copiedObject = null; // Dichiarata all'esterno per renderla globale

// Aggiungi un event listener per la tastiera (per intercettare Ctrl+C e Ctrl+V)
document.addEventListener('keydown', function(event) {
  // Verifica se Ctrl (o Cmd) è premuto insieme alla lettera 'C' (per copia)
  if (event.ctrlKey && event.key === 'c') {
    var activeObject = canvas.getActiveObject();
    if (activeObject) {
      copiedObject = activeObject; // Clona l'oggetto selezionato
      console.log("Oggetto copiato!");
      console.log(copiedObject);
    }
  }

// Verifica se Ctrl (o Cmd) è premuto insieme alla lettera 'V' (per incolla)
if (event.ctrlKey && event.key === 'v') {
    if (copiedObject) {
      // Usa il metodo clone() di Fabric.js per clonare l'oggetto
      copiedObject.clone(function(cloned) {
        // Posiziona l'oggetto copiato vicino all'oggetto originale
        cloned.set({
          left: copiedObject.left + 10,
          top: copiedObject.top + 10
        });
  
        // Aggiungi l'oggetto clonata alla tela
        canvas.add(cloned);
        canvas.setActiveObject(cloned);
        canvas.renderAll();
        console.log("Oggetto incollato!");
      });
    }
  }  
});