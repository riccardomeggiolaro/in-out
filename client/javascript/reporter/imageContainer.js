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

            const center = this.getCenterPoint();
            
            if (this.text) {
                if (this.text.width >= currentWidth) {
                    // Modifica la scala del testo in base alle dimensioni del rettangolo
                    this.text.set({
                        scaleX: currentWidth / this.text.width,  // Calcola il fattore di scala per la larghezza
                        left: center.x,
                        top: center.y
                    });
            
                    // Applica le nuove dimensioni e la scala
                    this.canvas.renderAll();
                }
                if (this.text.height >= currentHeight) {
                    // Modifica la scala del testo in base alle dimensioni del rettangolo
                    this.text.set({
                        scaleY: currentHeight / this.text.height,  // Calcola il fattore di scala per l'altezza
                        left: center.x,
                        top: center.y
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
                    left: center.x,
                    top: center.y
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
            scaleToWidth: false,
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

            const center = this.getCenterPoint();

            if (this.text) {
                this.text.set({
                    left: center.x,
                    top: center.y,
                    originX: 'center',
                    originY: 'center',
                });
            }
            
            if (this.image) {
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
        this.on('scaling', syncTextPosition);
        this.on('changed', syncTextPosition);
        
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

                    const center = this.getCenterPoint();

                    // Imposta la scala dell'immagine in base alle dimensioni del rettangolo
                    img.set({
                        scaleX: currentWidth / img.width,  // Calcola il fattore di scala per la larghezza
                        scaleY: currentHeight / img.height,  // Calcola il fattore di scala per l'altezza
                    });
    
                    // Set image position to center of container
                    img.set({
                        left: center.x,
                        top: center.y,
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

    _render: function(ctx) {
        this.callSuper('_render', ctx);
        const center = this.getCenterPoint();
        if (this.text && this.canvas) {
            this.text.set({
                left: center.x,
                top: center.y,
                originX: 'center',
                originY: 'center'
            });
            this.text.setCoords();
        }
        if (this.image && this.canvas) {
            this.image.set({
                left: center.x,
                top: center.y,
                originX: 'center',
                originY: 'center'
            });
            this.image.setCoords();
        }
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