document.querySelectorAll('input[type="number"]').forEach(input => {
    input.addEventListener('input', (event) => {
        let value = event.target.value;
        console.log(value);  // Aggiungi questa riga per fare il debug

        event.target.value = 500000000
    });
});