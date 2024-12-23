import { initAligningGuidelines } from './reporter/guide-lines.js';
import { initCenteringGuidelines } from './reporter/centering-guide-lines.js';
import { paperSizes } from './reporter/paperSize.js';
import './reporter/rectWithText.js';
import './reporter/imageContainer.js';
import './reporter/textWithPadding.js';

let canvas;
let gridLayer;
let midlineLayer;
let marginLayer;
let copiedObject = null;
const formatSelect = document.getElementById('format-select');
const gridToggle = document.getElementById('grid-toggle');
const midlineToggle = document.getElementById('midline-toggle');
const marginToggle = document.getElementById('margin-toggle');

function initCanvas(format) {
    formatSelect.value = format;

    if (canvas) {
        canvas.dispose();
    }
    const size = paperSizes[format];

    // Applica il fattore di scala alle dimensioni
    const scaledWidth = size.width * size.scale;
    const scaledHeight = size.height * size.scale;

    canvas = new fabric.Canvas('canvas', {
        backgroundColor: 'white',
        selection: true,
        preserveObjectStacking: true,
        width: scaledWidth,
        height: scaledHeight
    });

    // Verifica se la griglia deve essere mostrata
    if (gridToggle && gridToggle.checked) {
        createGrid(scaledWidth, scaledHeight);
    }

    // Verifica se i midlines devono essere mostrati
    if (midlineToggle && midlineToggle.checked) {
        createMidlines(scaledWidth, scaledHeight);
    }

    if (marginToggle && marginToggle.checked) {
        createMargins(scaledWidth, scaledHeight, size.margins);
    }

    canvas.on('selection:created', showControls);
    canvas.on('selection:updated', showControls);
    canvas.on('selection:cleared', hideControls);
    initAligningGuidelines(canvas);
    initCenteringGuidelines(canvas);
}

function createMargins(width, height, margins) {
    if (marginLayer) {
        canvas.remove(marginLayer);
    }

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

function toggleMargins() {
    const marginToggle = document.getElementById('margin-toggle');
    const size = paperSizes[formatSelect.value];

    // Applica il fattore di scala alle dimensioni
    const scaledWidth = size.width * size.scale;
    const scaledHeight = size.height * size.scale;

    if (marginToggle.checked) {
        createMargins(scaledWidth, scaledHeight, size.margins);
    } else {
        canvas.remove(marginLayer);
        marginLayer = null;
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

function toggleMidlines() {
    const midlineToggle = document.getElementById('midline-toggle');
    const size = paperSizes[formatSelect.value];

    // Applica il fattore di scala alle dimensioni
    const scaledWidth = size.width * size.scale;
    const scaledHeight = size.height * size.scale;

    if (midlineToggle.checked) {
        createMidlines(scaledWidth, scaledHeight);
    } else {
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

function toggleGrid() {
    const gridToggle = document.getElementById('grid-toggle');

    const size = paperSizes[formatSelect.value];

    // Applica il fattore di scala alle dimensioni
    const scaledWidth = size.width * size.scale;
    const scaledHeight = size.height * size.scale;

    if (gridToggle.checked) {
        createGrid(scaledWidth, scaledHeight);
    } else {
        canvas.remove(gridLayer);
        gridLayer = null;
    }
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
    const activeObj = canvas.getActiveObject();
    const textControls = document.getElementById('text-controls');
    const rectWithTextControls = document.getElementById('rectangle-controls');
    const lineControls = document.getElementById('line-controls');
    const imageControls = document.getElementById('image-controls');

    // Nascondi tutti i controlli di default
    textControls.style.display = 'none';
    rectWithTextControls.style.display = 'none';
    lineControls.style.display = 'none';    
    imageControls.style.display = 'none';

    // Controlla che activeObj esista prima di accedere al suo tipo
    if (activeObj && activeObj.type === 'i-text') {
        textControls.style.display = 'flex';
        
        document.getElementById('font-size-text').value = activeObj.fontSize;
        // document.getElementById('align-text').value = activeObj.textAlign;
        document.getElementById('font-family-text').value = activeObj.fontFamily;
        try {
            document.getElementById('database-data-text').value = activeObj.text;
        } catch {}
    } else if (activeObj && activeObj.type === 'rectWithText' || activeObj.type === 'imageContainer') {
        rectWithTextControls.style.display = 'flex';
        
        if (activeObj.type === 'imageContainer') {
            imageControls.style.display = 'flex';
            document.getElementById('cam').value = activeObj.text.text;
        }

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
    } else if (activeObj && activeObj.type === 'rect') {
        imageControls.style.display = 'flex';
    }
}

function hideControls() {
    document.getElementById('text-controls').style.display = 'none';
    document.getElementById('rectangle-controls').style.display = 'none';
    document.getElementById('line-controls').style.display = 'none';
    document.getElementById('image-controls').style.display = 'none';
}

function setTool(tool) {
    document.querySelectorAll('#tool-buttons button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    event.target.classList.add('active');
}

function addText() {
    const text = new fabric.IText('Testo', {
        left: 50,
        top: 50,
        fontSize: 30,
        fill: 'black',
        transparentCorners: false,
        hasControls: true,     // Mostra i controlli di ridimensionamento
    });

    canvas.add(text);
    canvas.setActiveObject(text);

    // // Attiva immediatamente la modalità di editing
    // text.enterEditing();
    
    // // Sposta il cursore alla fine del testo
    // text.setSelectionStart(text.text.length);
    // text.setSelectionEnd(text.text.length);
}

function addLine() {
    const line = new fabric.Line([0, 200, 200, 200], {
        stroke: 'black',
        selectable: true,
        evented: true,
        hasControls: true,
        strokeWidth: 2,
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

function addRectangleText() {
    const rectText = new fabric.RectWithText(
        {
            left: 10,
            top: 10,
            width: 200,
            height: 75,
            fill: '#FFFFFF',
            stroke: 'black',
            strokeWidth: 1,
            noScaleCache: false,
            strokeUniform: true
        },
        {
            fill: 'black',
            fontSize: 30,
            selectable: true,
            textAlign: 'center'
        }, 
        '');
    canvas.add(rectText);
    canvas.setActiveObject(rectText);
}

function addImage() {
    const imageContainer = new fabric.ImageContainer({
            width: 200,
            height: 200,
            fill: '#DEDDDA', // Light gray semi-transparent background
            stroke: 'black',
            strokeWidth: 1,
            selectable: true,
            noScaleCache: false,
            strokeUniform: true
        },
        {
            fontSize: 12,
            fill: 'black'
        },
        'Doppio click per aggiungere un\'immagine',
        null
    );
    // Add to canvas
    canvas.add(imageContainer);
    canvas.setActiveObject(imageContainer);
}

function deleteSelected() {
    const activeObjects = canvas.getActiveObjects();  // Ottieni tutti gli oggetti selezionati

    if (activeObjects.length > 0) {
        // Itera su ogni oggetto selezionato
        activeObjects.forEach(activeObject => {
            // Trova il contenitore RectWithText se esiste
            const parentRectWithText = canvas.getObjects().find(obj => 
                obj.type === 'rectWithText' && 
                (obj === activeObject || obj.text === activeObject)
            );
            
            const parentImageContainer = canvas.getObjects().find(obj => 
                obj.type === 'imageContainer' && 
                (obj === activeObject || obj.text === activeObject)
            );

            // Se è un oggetto RectWithText, rimuovi l'intero contenitore
            if (parentRectWithText) {
                canvas.remove(parentRectWithText);
                canvas.remove(parentRectWithText.text);
            } else if (parentImageContainer) {
                canvas.remove(parentImageContainer);
                canvas.remove(parentImageContainer.text);
                canvas.remove(parentImageContainer.image);
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

function updateText() {
    const activeObject = canvas.getActiveObject();
    if (activeObject && activeObject.type === 'i-text') {
        const databaseDataText = document.getElementById('database-data-text').value;
        let data = {
            fontSize: parseInt(document.getElementById('font-size-text').value),
            fontFamily: document.getElementById('font-family-text').value,
            text: databaseDataText || activeObject.text
        };
        activeObject.set(data);
        // Trova il contenitore RectWithText se esiste
        const parentRectWithText = canvas.getObjects().find(obj => 
            obj.type === 'rectWithText' && 
            (obj === activeObject || obj.text === activeObject)
        );
        if (parentRectWithText) {
            // Emetti manualmente l'evento 'changed' per il testo
            activeObject.fire('changed');
        }
        canvas.discardActiveObject();

        // Riseleziona immediatamente l'oggetto
        canvas.setActiveObject(activeObject);
        canvas.requestRenderAll();
    }
}

function updateRect() {
    const activeObj = canvas.getActiveObject();
    if (activeObj && activeObj.type === 'rectWithText' || activeObj.type === 'imageContainer') {
        activeObj.set({
            fill: document.getElementById('fill-color-rect').value,
            stroke: document.getElementById('stroke-color-rect').value,
            strokeWidth: parseInt(document.getElementById('stroke-width-rect').value)
        });
        canvas.requestRenderAll();
    }
}

function updateLine() {
    const activeObj = canvas.getActiveObject();
    if (activeObj && activeObj.type === 'line') {
        activeObj.set({
            stroke: document.getElementById('color-line').value,
            strokeWidth: parseInt(document.getElementById('stroke-width-line').value)
        });
        canvas.requestRenderAll();
    }
}

function updateImage() {
    const activeObj = canvas.getActiveObject();
    if (activeObj && activeObj.type === 'imageContainer') {
        activeObj.text.set({
            text: document.getElementById('cam').value
        });
        canvas.requestRenderAll();
        // Emetti manualmente l'evento 'changed' per il testo
        activeObj.text.fire('changed');
    }
}

// Modified Import function that handles custom objects
function importCanvas() {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.json';
    
    fileInput.onchange = function(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = function(event) {
            try {
                const jsonData = JSON.parse(event.target.result);
                
                initCanvas(jsonData.formatPaper);

                const reviver = function(obj, instance) {
                    if (instance) {
                        if (instance.type === 'rectWithText' && instance.text) {
                            instance.text.canvas = canvas;
                            instance.text.isContained = true;  // Ensure flag is set on import
                            canvas.add(instance.text);
                        } else if (instance.type === 'imageContainer' && instance.text) {
                            instance.text.canvas = canvas;
                            instance.text.isContained = true;  // Ensure flag is set on import
                            canvas.add(instance.text);
                        }
                    }
                };

                canvas.loadFromJSON(jsonData.canvasData, function() {
                    if (gridLayer) {
                        canvas.add(gridLayer);
                        gridLayer.sendToBack();
                    }
                    if (marginLayer) {
                        canvas.add(marginLayer);
                        marginLayer.sendToBack();
                    }
                    if (midlineLayer) {
                        canvas.add(midlineLayer);
                        midlineLayer.sendToBack();
                    }

                    canvas.renderAll();
                }, reviver);
            
            } catch (error) {
                console.error('Error importing canvas:', error);
                alert('Error importing canvas. Please check if the file is valid.');
            }
        };
    
        reader.readAsText(file);
    };
  
    fileInput.click();
}

// Modified Export function that filters out contained text objects
function exportCanvas() {
    if (midlineLayer) {
        canvas.remove(midlineLayer);
    }
    if (gridLayer) {
        canvas.remove(gridLayer);
    }
    if (marginLayer) {
        canvas.remove(marginLayer);
    }

    try {
        // Create a custom toJSON function that filters out contained text
        const customToJSON = (function(originalFn) {
            return function(propertiesToInclude) {
                const objects = this.getObjects();
                // Temporarily remove contained text objects
                const containedTexts = objects.filter(obj => obj.isContained);
                containedTexts.forEach(text => this.remove(text));
                // Get JSON without contained text objects
                const json = originalFn.call(this, propertiesToInclude);
                // Restore contained text objects
                containedTexts.forEach(text => this.add(text));
                return json;
            };
        })(canvas.toJSON);

        // Temporarily replace toJSON method
        const originalToJSON = canvas.toJSON;
        canvas.toJSON = customToJSON;

        // Create configuration object including canvas dimensions
        const configuration = {
            formatPaper: formatSelect.value,
            canvasData: canvas.toJSON([
                'selectable',
                'hasControls',
                'hasBorders',
                'id',
                'name',
                'editable',
                'customType',
                'type',
                'isContained'
            ])
        };

        // Restore original toJSON method
        canvas.toJSON = originalToJSON;

        // Create and trigger download
        const blob = new Blob([JSON.stringify(configuration)], { type: 'application/json' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'canvas_export.json';
        link.click();
        URL.revokeObjectURL(link.href);

    } catch (error) {
        console.error('Error exporting canvas:', error);
    } finally {
        // Restore layers
        if (midlineLayer) {
            canvas.add(midlineLayer);
            midlineLayer.sendToBack();
        }
        if (gridLayer) {
            canvas.add(gridLayer);
            gridLayer.sendToBack();
        }
        if (marginLayer) {
            canvas.add(marginLayer);
            marginLayer.sendToBack();
        }
    }
}

// Optional: Save canvas state to localStorage
function saveCanvasState() {
    try {
        const json = canvas.toJSON([
            'selectable', 
            'hasControls', 
            'hasBorders', 
            'id', 
            'name', 
            'editable', 
            'customType',
            'type'
        ]);
        localStorage.setItem('canvasState', JSON.stringify(json));
    } catch (error) {
        console.error('Error saving canvas state:', error);
    }
}

// Optional: Load canvas state from localStorage
function loadCanvasState() {
    try {
        const savedState = localStorage.getItem('canvasState');
        if (savedState) {
            canvas.loadFromJSON(JSON.parse(savedState), function() {
                canvas.renderAll();
            });
        }
    } catch (error) {
        console.error('Error loading canvas state:', error);
    }
}

formatSelect.addEventListener('change', (e) => {
    initCanvas(e.target.value);
});

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
        case 'Immagine':
            addImage();
            break;
        default:
            break;
    }
});

// Aggiungi un event listener per la tastiera (per intercettare Ctrl+C e Ctrl+V)
document.addEventListener('keydown', function(event) {
    // Verifica se Ctrl (o Cmd) è premuto insieme alla lettera 'C' (per copia)
    if (event.ctrlKey && event.key === 'c') {
        let activeObject = canvas.getActiveObject();
        if (activeObject) {
            copiedObject = activeObject; // Clona l'oggetto selezionato
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
            });
        }
    }  
});

initCanvas(formatSelect.value);

// If you want to make these globally accessible for HTML inline events
window.setTool = setTool;
window.deleteSelected = deleteSelected;
window.exportCanvas = exportCanvas;
window.importCanvas = importCanvas;
window.toggleGrid = toggleGrid;
window.toggleMidlines = toggleMidlines;
window.toggleMargins = toggleMargins;
window.updateText = updateText;
window.updateRect = updateRect;
window.updateLine = updateLine;
window.updateImage = updateImage;