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
            hasBorders: false,
            isContained: true  // Add this flag to identify contained text
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
    },

    toObject: function(propertiesToInclude) {
        return fabric.util.object.extend(this.callSuper('toObject', propertiesToInclude), {
        text: this.text.toObject(),
        textContent: this.text.text
        });
    },

    _render: function(ctx) {
        this.callSuper('_render', ctx);
        if (this.text) {
        this.text.set({
            left: this.left + (this.width * this.scaleX) / 2,
            top: this.top + (this.height * this.scaleY) / 2,
            originX: 'center',
            originY: 'center'
        });
        this.text.setCoords();
        }
    }
});

// FromObject implementation
fabric.RectWithText.fromObject = function(object, callback) {
    const rectOptions = fabric.util.object.clone(object);
    delete rectOptions.text;
    delete rectOptions.textContent;
  
    const textOptions = object.text;
    const instance = new fabric.RectWithText(rectOptions, textOptions, object.textContent);
    
    if (callback) {
      callback(instance);
    }
    return instance;
};

fabric.ImageContainer = fabric.util.createClass(fabric.Rect, {
    type: 'imageContainer',
    text: null,
    image: null,
    
    initialize: function (rectOptions, textOptions, text, image) {
        this.callSuper('initialize', rectOptions);

        this.on('scaling', () => {
            // Calcola la larghezza e l'altezza effettiva del rettangolo
            const currentWidth = this.width * this.scaleX;  // Larghezza attuale del rettangolo
            const currentHeight = this.height * this.scaleY;  // Altezza attuale del rettangolo

            if (this.text) {
                if (this.text.width >= currentWidth) {
                    // Modifica la scala del testo in base alle dimensioni del rettangolo
                    this.text.set({
                        scaleX: currentWidth / this.text.width,  // Calcola il fattore di scala per la larghezza
                    });
            
                    // Applica le nuove dimensioni e la scala
                    this.canvas.renderAll();
                }
                if (this.text.height >= currentHeight) {
                    // Modifica la scala del testo in base alle dimensioni del rettangolo
                    this.text.set({
                        scaleY: currentHeight / this.text.height,  // Calcola il fattore di scala per l'altezza
                    });
            
                    // Applica le nuove dimensioni e la scala
                    this.canvas.renderAll();
                }
            }

            // Se l'immagine esiste, ridimensiona correttamente
            if (this.image) {
                // Modifica la scala dell'immagine in base alle dimensioni del rettangolo
                this.image.set({
                    scaleX: currentWidth / this.image.width,  // Calcola il fattore di scala per la larghezza
                    scaleY: currentHeight / this.image.height,  // Calcola il fattore di scala per l'altezza
                });
        
                // Applica le nuove dimensioni e la scala
                this.canvas.renderAll();
            }
        });                   
        
        // Create the text
        this.text = new fabric.IText(text, {
            ...textOptions,
            selectable: false,
            evented: false,
            hasControls: false,
            hasBorders: false,
            isContained: true
        });
        
        this.image = new fabric.Image(image, {
            ...textOptions,
            selectable: false,
            evented: false,
            hasControls: false,
            hasBorders: false,
            isContained: true
        })

        // Improved centering function
        const centerText = () => {
            if (!this.canvas) return;
            
            if (this.text) {
                const center = this.getCenterPoint();
                this.text.set({
                    left: center.x,
                    top: center.y,
                    originX: 'center',
                    originY: 'center',
                });
            }
            
            if (this.image) {
                const center = this.getCenterPoint();
                this.image.set({
                    left: center.x,
                    top: center.y,
                    originX: 'center',
                    originY: 'center',
                });
            }
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
            if (this.image) {
                this.canvas.add(this.image);
            }
            centerText();
        });
        
        // Double-click event for image loading
        this.on('mousedblclick', () => {
            this._onDoubleClick();
        });

        this.text.on('changed', () => {
            console.log(this.text.text);
            // Remove previous image if it exists
            if (this.image) {
                this.canvas.remove(this.image);
                this.canvas.renderAll();
            }
        });

        // Gestisci la selezione dell'intero contenitore
        if (this.image) {
            this.image.on('mousedown', (opt) => {
                // Deseleziona l'immagine e seleziona il contenitore
                opt.target.canvas.discardActiveObject();
                opt.target.canvas.setActiveObject(this);
                opt.target.canvas.renderAll();
            });
        }
    },
    
    _onDoubleClick: function() {
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = 'image/*';
        fileInput.onchange = (e) => {
            const file = e.target.files[0];
            const reader = new FileReader();
            const currentWidth = this.width * this.scaleX;  // Larghezza attuale del rettangolo
            const currentHeight = this.height * this.scaleY;  // Altezza attuale del rettangolo
            reader.onload = (event) => {
                fabric.Image.fromURL(event.target.result, (img) => {
                    if (this.text) {
                        this.text.text = '';
                    }

                    // Remove previous image if it exists
                    if (this.image) {
                        this.canvas.remove(this.image);
                    }
                    
                    // Imposta la scala dell'immagine in base alle dimensioni del rettangolo
                    img.set({
                        scaleX: currentWidth / img.width,  // Calcola il fattore di scala per la larghezza
                        scaleY: currentHeight / img.height,  // Calcola il fattore di scala per l'altezza
                    });
    
                    // Set image position to center of container
                    img.set({
                        left: this.left + currentWidth / 2,
                        top: this.top + currentHeight / 2,
                        originX: 'center',
                        originY: 'center',
                        selectable: false,
                        evented: false,
                        hasControls: false,
                        hasBorders: false,
                        isContained: true
                    });
                    
                    // Store the image as object property
                    this.image = img;

                    console.log(this.image.getSrc());
                    
                    // Add image to canvas
                    this.canvas.add(img);
    
                    // Aggiungi gestore di selezione per la nuova immagine
                    this.image.on('mousedown', (opt) => {
                        // Deseleziona l'immagine e seleziona il contenitore
                        opt.target.canvas.discardActiveObject();
                        opt.target.canvas.setActiveObject(this);
                        opt.target.canvas.renderAll();
                    });
                    
                    this.canvas.renderAll();
                });
            };
            reader.readAsDataURL(file);
        };
        fileInput.click();
    },

    clone: function(callback) {
        const self = this;
        // Get the original image source
        const imageSource = this.image ? this.image.getSrc() : null;
        
        // Create new container with same properties
        const clonedContainer = new fabric.ImageContainer(
            this.toObject(),
            this.text.toObject(),
            this.text.text,
            imageSource
        );
        
        // Make sure the image is loaded before calling callback
        if (imageSource) {
            fabric.Image.fromURL(imageSource, function(img) {
                clonedContainer.image = img;
                clonedContainer.image.set({
                    scaleX: self.image.scaleX,
                    scaleY: self.image.scaleY,
                    left: self.image.left,
                    top: self.image.top,
                    originX: 'center',
                    originY: 'center',
                    selectable: false,
                    evented: false,
                    hasControls: false,
                    hasBorders: false,
                    isContained: true
                });
                
                if (callback) callback(clonedContainer);
            });
        } else {
            if (callback) callback(clonedContainer);
        }
    },

    toObject: function(propertiesToInclude) {
        return fabric.util.object.extend(this.callSuper('toObject', propertiesToInclude), {
            text: this.text.toObject(),
            textContent: this.text.text,
            image: this.image ? {
                src: this.image.getSrc(),
                scaleX: this.image.scaleX,
                scaleY: this.image.scaleY
            } : null
        });
    },

    // FromObject implementation
    fromObject: function(object, callback) {
        const rectOptions = fabric.util.object.clone(object);
        delete rectOptions.text;
        delete rectOptions.textContent;
        delete rectOptions.image;

        const textOptions = object.text;
        const imageSource = object.image ? object.image.src : null;
        
        const instance = new fabric.ImageContainer(
            rectOptions, 
            textOptions, 
            object.textContent,
            imageSource
        );

        if (object.image) {
            fabric.Image.fromURL(imageSource, function(img) {
                instance.image = img;
                instance.image.set({
                    scaleX: object.image.scaleX,
                    scaleY: object.image.scaleY,
                    originX: 'center',
                    originY: 'center',
                    selectable: false,
                    evented: false,
                    hasControls: false,
                    hasBorders: false,
                    isContained: true
                });
                
                if (callback) callback(instance);
            });
        } else {
            if (callback) callback(instance);
        }
        
        return instance;
    }
});

// Assign fromObject to the class
fabric.ImageContainer.fromObject = function(object, callback) {
    return fabric.ImageContainer.prototype.fromObject(object, callback);
};

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

function toggleMargins() {
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

function toggleMidlines() {
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

function toggleGrid() {
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
    const imageControls = document.getElementById('image-controls');

    console.log(activeObj);

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
    console.log("hide")

    document.getElementById('text-controls').style.display = 'none';
    document.getElementById('rectangle-controls').style.display = 'none';
    document.getElementById('line-controls').style.display = 'none';
}

function setTool(tool) {
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

function addImage() {
    const imageContainer = new fabric.ImageContainer({
            width: 200,
            height: 200,
            fill: '#C0BFBC', // Light gray semi-transparent background
            stroke: 'black',
            strokeWidth: 2,
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
        
        canvas.clear();

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

        canvas.loadFromJSON(jsonData, function() {
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

    // Export the canvas
    const json = canvas.toJSON([
      'selectable', 
      'hasControls', 
      'hasBorders', 
      'id', 
      'name', 
      'editable', 
      'customType',
      'type',
      'isContained'  // Include this property in the export
    ]);

    // Restore original toJSON method
    canvas.toJSON = originalToJSON;

    // Create and trigger download
    const blob = new Blob([JSON.stringify(json)], { type: 'application/json' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'canvas_export.json';
    link.click();
    URL.revokeObjectURL(link.href);
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