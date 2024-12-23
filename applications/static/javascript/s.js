    // Add double-click event for image upload
    imageContainer.on('mousedblclick', function() {
        // Create a hidden file input
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = 'image/*';

        // Handle file selection
        fileInput.onchange = function(e) {
            const file = e.target.files[0];
            const reader = new FileReader();

            reader.onload = function(event) {
                fabric.Image.fromURL(event.target.result, function(img) {
                    // Salva la posizione corrente del gruppo
                    const currentLeft = imageContainer.left;
                    const currentTop = imageContainer.top;

                    // Scale the image to fit the container
                    img.scaleToWidth(imageContainer.width);
                    img.scaleToHeight(imageContainer.height);

                    // Imposta la posizione dell'immagine al centro del gruppo
                    img.set({
                        left: imageContainer.width / 2,
                        top: imageContainer.height / 2,
                        originX: 'center',
                        originY: 'center'
                    });

                    // Rimuovi tutti gli elementi esistenti nel gruppo
                    while (imageContainer.getObjects().length > 0) {
                        imageContainer.remove(imageContainer.getObjects()[0]);
                    }

                    // Aggiungi la nuova immagine al gruppo
                    imageContainer.addWithUpdate(img);

                    // Ripristina la posizione originale del gruppo
                    imageContainer.set({
                        left: currentLeft,
                        top: currentTop
                    });

                    canvas.renderAll();
                });
            };

            reader.readAsDataURL(file);
        };

        // Trigger file selection
        fileInput.click();
    });