fabric.RectWithText = fabric.util.createClass(fabric.Rect, {
    type: 'rectWithText',
    text: null,

    initialize: function (rectOptions, textOptions, text) {
        // Call the rectangle constructor
        this.callSuper('initialize', rectOptions);

        // Create the text
        this.text = new fabric.Textbox(text, {
            ...textOptions,
            selectable: false,
            evented: false
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
                angle: this.angle
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

        this.on('removed', () => {
            this.canvas.remove(this.text);
        });

        // Handle text editing
        this.on('mousedown:before', () => {
            this._prevObjectStacking = this.canvas.preserveObjectStacking;
            this.canvas.preserveObjectStacking = true;
        });

        this.on('mousedblclick', () => {
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
    }
});