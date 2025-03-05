function openPopup() {
    document.getElementById('popup').classList.add('active');
    document.getElementById('overlay').classList.add('active');
}

function closePopup() {
    document.getElementById('popup').classList.remove('active');
    document.getElementById('overlay').classList.remove('active');
    document.getElementById('input-description').value = '';
    document.getElementById('input-cell').value = '';
    document.getElementById('input-cfpiva').value = '';
    document.getElementById('save-btn').disabled = true;
}

function saveRagioneSociale() {
    const descrizione = document.getElementById('descrizione').value;
    const cell = document.getElementById('cell').value;
    const cfpiva = document.getElementById('cfpiva').value;
    
    if (descrizione && cell && cfpiva) {
        const table = document.querySelector('tbody');
        const newRow = `<tr><td>${descrizione}</td><td>${cell}</td><td>${cfpiva}</td></tr>`;
        table.innerHTML += newRow;
        closePopup();
    } else {
        alert("Tutti i campi sono obbligatori");
    }
}

function register() {
    // Seleziona il form tramite l'ID
    const form = document.getElementById("register");

    const name = form.querySelector("#input-description").value.trim();
    const cell = form.querySelector("#input-cell").value.trim();
    const cfpiva = form.querySelector("#input-cfpiva").value.trim();

    // Crea un oggetto con i valori degli input
    const formData = {
        name: name,
        cell: cell || null,
        cfpiva: cfpiva || null
    };

    fetch('/anagrafic/social_reason', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(res => res.json())
    .then(res => {
        closePopup();
        showSnackbar('green', 'white');
        updateTable();
    })
}

setTimeout(() => {
    urlPath = '/anagrafic/list/social_reason';
    updateTable();
}, 1000);