let currentPage = 1;
let rowsPerPage = 10;
let totalRows = 0; // Aggiungi questa variabile per tenere traccia del numero totale di righe
let itemName = null;
let listUrlPath = null;
let addUrlPath = null;
let setUrlPath = null;
let deleteUrlPath = null;
let currentId = null;
const columns = {};

document.querySelectorAll('thead th').forEach((th, index) => {
    const columnName = th.attributes["name"];
    if (columnName && columnName.value) {
        columns[columnName.value] = index;
    }
});

function updateTable() {
    const offset = (currentPage - 1) * rowsPerPage; // Calcola l'offset in base alla pagina
    fetch(`${listUrlPath}?limit=${rowsPerPage}&offset=${offset}`)
    .then(res => res.json())
    .then(res => {
        totalRows = res.total_rows; // Aggiorna il numero totale di righe dalla risposta
        populateTable(res.data); // Popola la tabella con i dati
        updatePageSelect(); // Aggiorna la selezione della pagina
        // Mostra il numero totale di righe
        document.getElementById("total-rows").textContent = `Totale righe: ${totalRows}`;
    });
}

function updatePageSelect() {
    const totalPages = Math.ceil(totalRows / rowsPerPage); // Calcola il numero totale di pagine
    const pageSelect = document.getElementById("page-select");
    const previousPage = document.getElementById("previous-page");
    const nextPage = document.getElementById("next-page");
    pageSelect.innerHTML = "";
    for (let i = 1; i <= totalPages; i++) {
        let option = document.createElement("option");
        option.value = i;
        option.textContent = `Pagina ${i}`;
        if (i === currentPage) option.selected = true;
        pageSelect.appendChild(option);
    }
    if (totalPages === 0) {
        previousPage.disabled = true;
        nextPage.disabled = true;
    } else {
        if (pageSelect.value == totalPages) nextPage.disabled = true;
        else nextPage.disabled = false;
        if (pageSelect.value == 1) previousPage.disabled = true;
        else previousPage.disabled = false;
        if (currentPage > totalPages) {
            pageSelect.value = null;
        }
    }
}

function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        updateTable();
    }
}

function nextPage() {
    const totalPages = Math.ceil(totalRows / rowsPerPage); // Usa `totalRows` per calcolare il numero di pagine
    if (currentPage < totalPages) {
        currentPage++;
        updateTable();
    }
}

function goToPage() {
    currentPage = parseInt(document.getElementById("page-select").value);
    updateTable();
}

function changeRowsPerPage() {
    rowsPerPage = parseInt(document.getElementById("rows-per-page").value);
    currentPage = 1; // Quando cambia il numero di righe per pagina, torna alla prima pagina
    updateTable();
}

function populateTable(data) {
    const table = document.querySelector("tbody");
    table.innerHTML = ""; // Pulisce la tabella esistente

    data.forEach(item => {
        const row = document.createElement("tr");
        Object.entries(columns).forEach(_ => row.insertCell());

        Object.entries(item).forEach(([key, value]) => {
            // Salta l'id
            if (key in columns) {
                row.cells[columns[key]].textContent = value;
            }
        });

        // Crea la cella per i pulsanti di azione
        const actionsCell = document.createElement("td");
        actionsCell.style.textAlign = "right"; // Allinea i pulsanti a destra

        // Pulsante Modifica
        const editButton = document.createElement("button");
        editButton.style.visibility = 'hidden';
        editButton.textContent = "✏️";
        editButton.onclick = () => editRow(item);

        // Pulsante Elimina
        const deleteButton = document.createElement("button");
        deleteButton.style.visibility = 'hidden';
        deleteButton.textContent = "🗑️";
        deleteButton.onclick = () => deleteRow(item);

        actionsCell.appendChild(editButton);
        actionsCell.appendChild(deleteButton);
        row.appendChild(actionsCell);

        // Mostra i pulsanti solo all'hover della riga
        row.addEventListener("mouseenter", () => {
            row.style.backgroundColor = 'whitesmoke';
            editButton.style.visibility = 'inherit';
            deleteButton.style.visibility = 'inherit';
        });
        row.addEventListener("mouseleave", () => {
            row.style.backgroundColor = 'white';
            editButton.style.visibility = 'hidden';
            deleteButton.style.visibility = 'hidden';
        });

        table.appendChild(row);
    });
}

function getFormData(form) {
    const formData = {};
    const elements = form.elements;

    for (let element of elements) {
        if (element.id) {
            if (element.type === 'checkbox') {
                formData[element.id] = element.checked;
            } else if (element.type === 'radio') {
                if (element.checked) {
                    formData[element.id] = element.value;
                }
            } else {
                formData[element.id] = element.value;
            }
        }
    }
    
    return formData;
}

function removeNullValues(obj) {
    return Object.entries(obj).reduce((acc, [key, value]) => {
        if (value !== null) {
            acc[key] = value;
        }
        return acc;
    }, {});
}

const addPopup = document.getElementById('add-popup');
addPopup.querySelector('#save-btn').addEventListener('click', () => {
    const data = getFormData(addPopup.querySelector('form'));
    const nonNullableData = removeNullValues(data);
    fetch(`${addUrlPath}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(nonNullableData)
    })
    .then(res => res.json())
    .then(_ => {
        closePopups(['add-popup']);
        showSnackbar(`${itemName} creata`, 'green', 'white');
        updateTable();
    })
});

function addRow() {
    document.getElementById('overlay').classList.add('active');
    addPopup.classList.add('active');
}

const editPopup = document.getElementById('edit-popup');
editPopup.querySelector('#save-btn').addEventListener('click', () => {
    const data = getFormData(editPopup.querySelector('form'));
    fetch(`${setUrlPath}/${currentId}`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(res => {
        return {
            "data": res.json(),
            "status": res.status
        }
    })
    .then(res => {
        closePopups(['edit-popup']);
        if (res.status === 404) showSnackbar(`La ${itemName.toLowerCase()} è stata eliminata da un altro utente`, 'red', 'white');
        else showSnackbar(`${itemName} modificata`, 'green', 'white');
        updateTable();
    })
    .catch(error => console.error(error));
});

// Funzioni segnaposto per modifica ed eliminazione
function editRow(item) {
    currentId = item.id;
    document.getElementById('overlay').classList.add('active');
    editPopup.classList.add('active');
    for (let key in item) {
        const keyInput = editPopup.querySelector(`#${key}`);
        if (keyInput) keyInput.value = item[key];
    }
}

const deletePopup = document.getElementById('delete-popup');
deletePopup.querySelector('#save-btn').addEventListener('click', () => {
    fetch(`${deleteUrlPath}/${currentId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(res => {
        return {
            "data": res.json(),
            "status": res.status
        }
    })
    .then(res => {
        closePopups(['delete-popup']);
        updateTable();
        if (res.status === 404) showSnackbar(`La ${itemName.toLowerCase()} è stata eliminata da un altro utente`, 'red', 'white');
        else showSnackbar(`${itemName} eliminata`, 'green', 'white');
        return res;
    })
    .catch(error => {
        console.log(error);
        showSnackbar(`${error}`, 'red', 'white');
    });
})

function deleteRow(item) {
    currentId = item.id;
    document.getElementById('overlay').classList.add('active');
    deletePopup.classList.add('active');
    for (key in item) {
        const span = deletePopup.querySelector(`#${key}`);
        if (span) span.innerHTML = item[key];
    }
}

function openPopup(idPopup) {
    document.getElementById(idPopup).classList.add('active');
    document.getElementById('overlay').classList.add('active');
}

function closePopups(idPopups) {
    idPopups.forEach(idPopup => {
        const popup = document.getElementById(idPopup);
        if (popup) {
            popup.classList.remove('active');
        }
        // Disabilita il pulsante "Save"
        const saveBtn = popup.querySelector('save-btn');
        if (saveBtn) {
            saveBtn.disabled = true;
        }
        // Resetta i campi input
        const inputs = popup.querySelectorAll('input');
        inputs.forEach(input => {
            input.value = '';
        });
    });

    document.getElementById('overlay').classList.remove('active');
}