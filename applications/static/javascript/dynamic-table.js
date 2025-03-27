let currentPage = 1;
let rowsPerPage = 10;
let totalRows = 0; // Aggiungi questa variabile per tenere traccia del numero totale di righe
let itemName = null;
let listUrlPath = null;
let addUrlPath = null;
let setUrlPath = null;
let deleteUrlPath = null;
let callback_populate_select = null;
let populate_detail_tr = null;
let currentId = null;
let confirm_exec_funct = null;
let currentRowExtended = null;
const columns = {};
const options = {
    hour: '2-digit',
    minute: '2-digit',
    day: '2-digit',
    month: 'numeric',
    year: 'numeric'
};
  
document.querySelectorAll('thead th').forEach((th, index) => {
    const columnName = th.attributes["name"];
    if (columnName && columnName.value) {
        columns[columnName.value] = index;
    }
});

function isValidDate(dateStr) {
    // Verifica se la stringa corrisponde al formato ISO 8601
    const regex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:\d{2}|Z)?$/;
    
    if (!regex.test(dateStr)) {
      return false;
    }
    
    const date = new Date(dateStr);
  
    // Verifica se la data è valida
    return date instanceof Date && !isNaN(date.getTime());
}

function updateTable() {
    let queryParams = '';
    const filters = document.querySelector('#filters');
    filters.querySelectorAll('input').forEach(input => {
        if (input.value) queryParams += `${input.name}=${input.value}%&`;
    })
    const offset = (currentPage - 1) * rowsPerPage; // Calcola l'offset in base alla pagina
    fetch(`${listUrlPath}?limit=${rowsPerPage}&offset=${offset}&${queryParams}`)
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
    
    // Extract column names and positions from the headers
    const columns = {};
    const headers = document.querySelectorAll("thead th[name]");
    headers.forEach((header, index) => {
        if (header.getAttribute("name")) {
            columns[header.getAttribute("name")] = index;
        }
    });
  
    data.forEach(item => {
        const row = document.createElement("tr");        
        // Create cells for each column
        for (let i = 0; i < document.querySelectorAll("thead th").length - 1; i++) {
            row.insertCell();
        }
        // Funzione ricorsiva per gestire oggetti annidati a qualsiasi livello
        function populateNestedValues(obj, prefix = '') {
            Object.entries(obj).forEach(([key, value]) => {
                const fullKey = prefix ? `${prefix}.${key}` : key;
                if (fullKey in columns) {
                    row.cells[columns[fullKey]].textContent = isValidDate(value) && typeof(value) !== "number" ? new Date(value).toLocaleString('it-IT', options) : value;
                } 
                // Gestione ricorsiva per gli oggetti annidati
                else if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
                    populateNestedValues(value, fullKey);
                }
            });
        }        
        // Applica la funzione ricorsiva sull'oggetto riga
        populateNestedValues(item);
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
        if (populate_detail_tr) {
            // Crea la riga per i dettagli (inizialmente nascosta)
            const detailRow = document.createElement("tr");
            detailRow.classList.add("detail-row");
            detailRow.style.display = "none"; // Dettagli nascosti inizialmente
            // Crea una cella che si estende per tutta la larghezza della tabella
            const detailCell = document.createElement("td");
            detailCell.colSpan = document.querySelectorAll("thead th").length;
            detailCell.className = "detail-cell";
            // Crea il contenuto dei dettagli
            detailCell.innerHTML = populate_detail_tr(item);
            detailRow.appendChild(detailCell);
            table.appendChild(detailRow);
            row.onclick = () => toggleExpandRow(row);
        }
    });
}

// Funzione per espandere/collassare la riga
function toggleExpandRow(row) {
    if (currentRowExtended && currentRowExtended !== row.nextElementSibling) {
        // Se già espanso, nascondi
        currentRowExtended.style.display = "none";        
    }
    currentRowExtended = row.nextElementSibling; // Dettagli subito dopo la riga
    const isExpanded = currentRowExtended.style.display === "table-row";
    // Se già espanso, nascondi
    currentRowExtended.style.display = isExpanded ? "none" : "table-row";
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
                formData[element.id] = element.value !== "" ? element.value : null;
            }
        }
    }    
    return formData;
}

function removeNullValues(obj) {
    return Object.entries(obj).reduce((acc, [key, value]) => {
        if (value !== null) acc[key] = value;
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
    if (callback_populate_select) callback_populate_select('#register');
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
    const funct = () => {
        if (callback_populate_select) callback_populate_select('#edit', item);
        currentId = item.id;
        document.getElementById('overlay').classList.add('active');
        editPopup.classList.add('active');
        for (let key in item) {
            const keyInput = editPopup.querySelector(`#${key}`);
            if (keyInput) keyInput.value = item[key];
        }
    }
    if (item.reservations ? item.reservations.length > 0 : item.weighings.length > 0) {
        confirm_exec_funct = funct;
        document.querySelector('#confirm-title').textContent = "Attenzione!";
        document.querySelector('#confirm-content').innerHTML = `
            Questa anagrafica è associata a delle pesate salvate.<br>
            Apportando modifiche, verranno aggiornati anche i dati correlati alle pesate.
        `;
        openPopup('confirm-popup');
    } else {
        funct();
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
    const funct = () => {
        if (callback_populate_select) callback_populate_select('#delete', item);
        currentId = item.id;
        document.getElementById('overlay').classList.add('active');
        deletePopup.classList.add('active');
        for (key in item) {
            let annidate_key = `#${key}`;
            let annidate_value = item[key];
            if (typeof annidate_value === 'object' && annidate_value !== null && !Array.isArray(annidate_value)) {
                Object.entries(annidate_value).forEach(([sub_key, sub_value]) => {
                    annidate_key = `#${key}\\.${sub_key}`;
                    annidate_value = sub_value;
                    const span = deletePopup.querySelector(annidate_key);
                    if (span) span.innerHTML = annidate_value;
                })
            } else {
                const span = deletePopup.querySelector(annidate_key);
                if (span) span.innerHTML = annidate_value;
            }
        }
    }
    if (item.reservations ? item.reservations.length > 0 : item.weighings.length > 0) {
        document.querySelector('#confirm-title').textContent = "Attenzione!";
        document.querySelector('#confirm-content').textContent = `Non è possibile eliminare questa anagrafica perchè è associata a delle pesate salvate.`;
        openPopup('confirm-popup');
    } else {
        funct();
    }
}

const confirmPopup = document.getElementById('confirm-popup');
confirmPopup.querySelector('#save-btn').addEventListener('click', () => {
    const clone_funct = confirm_exec_funct;
    closePopups(['confirm-popup']);
    if (typeof(clone_funct) === "function") {
        clone_funct();
    }
})
confirmPopup.querySelector('.cancel-btn').addEventListener('click', () => {
    closePopups(['confirm-popup']);
    confirm_exec_funct = null;
})

function openPopup(idPopup) {
    document.getElementById(idPopup).classList.add('active');
    document.getElementById('overlay').classList.add('active');
}

function closePopups(idPopups) {
    confirm_exec_funct = null;
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
            if (input.type !== 'radio') input.value = '';
            if (input.dataset.id) input.dataset.id = '';
        });
    });

    document.getElementById('overlay').classList.remove('active');
}