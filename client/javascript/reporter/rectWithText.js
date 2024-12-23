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
            scaleToWidth: false,
            isContained: true  // Add this flag to identify contained text
        });

        // Improved centering function with border consideration
        const centerText = () => {
            if (!this.canvas) return;

            // Calculate the center of the rectangle, accounting for stroke width
            const center = this.getCenterPoint();
            
            // Update text position and properties
            this.text.set({
                left: center.x,
                top: center.y,
                originX: 'center',
                originY: 'center'
            });
        };

        // Event handlers to keep text synchronized
        const syncTextPosition = () => {
            centerText();
            this.canvas.renderAll();
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
            this.canvas.renderAll();
        });

        this.on('removed', () => {
            if (this.text && this.canvas) {
                this.canvas.remove(this.text);
            }
        });

        // Handle text editing
        this.on('mousedown:before', () => {
            this._prevObjectStacking = this.canvas.preserveObjectStacking;
            this.canvas.preserveObjectStacking = true;
        });

        this.on('mousedblclick', () => {
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
            // Ricalcola dimensioni 
            // Centra nuovamente il testo 
            const center = this.getCenterPoint(); 
            this.text.set({ left: center.x, top: center.y, originX: 'center', originY: 'center' });
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
        if (this.text && this.canvas) {
            const center = this.getCenterPoint();
            this.text.set({
                left: center.x,
                top: center.y,
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