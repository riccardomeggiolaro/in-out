let currentPage = 1;
let rowsPerPage = 10;
let totalRows = 0; // Aggiungi questa variabile per tenere traccia del numero totale di righe
let itemName = null;
let listUrlPath = null;
let addUrlPath = null;
let setUrlPath = null;
let deleteUrlPath = null;
let websocketUrlPath = null;
let callback_populate_select = null;
let callback_websocket_message = null;
let populate_detail_tr = null;
let currentId = null;
let confirm_exec_funct = null;
let currentRowExtended = null;
let websocket_connection = null;
let isRefreshing = false;
let reconnectTimeout = null;
let params = {};
const columns = {};
const options = {
    hour: '2-digit',
    minute: '2-digit',
    day: '2-digit',
    month: 'numeric',
    year: 'numeric'
};

window.onbeforeunload = function() {
    isRefreshing = true; // Imposta il flag prima del refresh
    clearTimeout(reconnectTimeout);
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

async function updateTable() {
    let queryParams = '';
    const filters = document.querySelector('#filters');
    filters.querySelectorAll('input').forEach(input => {
        if (input.name && input.value) {
            if (input.type == 'text') queryParams += `${input.name}=${input.value}%&`;
            else if (input.type == 'number') queryParams += `${input.name}=${input.value}&`;
            else if (input.type == 'date') queryParams += `${input.name}=${input.value}&`;
        }
    })
    filters.querySelectorAll('select').forEach(select => {
        if (select.value) {
            queryParams += `${select.name}=${select.value}&`;
        }
    })
    const offset = (currentPage - 1) * rowsPerPage;
    const res = await fetch(`${listUrlPath}?limit=${rowsPerPage}&offset=${offset}&${queryParams}`);
    const data = await res.json();
    
    totalRows = data.total_rows;
    populateTable(data.data);
    updatePageSelect();
    document.getElementById("total-rows").textContent = `Totale righe: ${totalRows}`;
    
    return data;
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

function getTableColumns() {
    const table = document.querySelector("tbody");
    
    // Extract column names and positions from the headers
    const columns = {};
    const headers = document.querySelectorAll("thead th[name]");
    headers.forEach((header, index) => {
        if (header.getAttribute("name")) {
            columns[header.getAttribute("name")] = index;
        }
    });    

    return {
        table,
        columns
    }
}

function populateTable(data) {
    const obj = getTableColumns();
    obj.table.innerHTML = ""; // Pulisce la tabella esistente
  
    data.forEach(item => createRow(obj.table, obj.columns, item));
}

function createRow(table, columns, item) {
    const row = document.createElement("tr");        
    row.dataset.id = item.id;
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
}

function updateRow(table, columns, item) {
    const row = table.querySelector(`[data-id="${item.id}"]`)
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
            } else if (element.type === 'text') {
                formData[element.id] = element.value;
            } else if (element.type === 'number') {
                formData[element.id] = element.value !== "" ? element.value : -1;
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
    .then(async res => {
        const [data, status] = await Promise.all([res.json(), Promise.resolve(res.status)]);
        return ({
            data,
            status
        });
    })
    .then(res => {
        if (res.status === 400) {
            showSnackbar(res.data.detail, 'rgb(255, 208, 208)', 'black');
        } else {
            closePopups(['add-popup']);
        }
    })
    .catch(error => console.error(error));
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
    .then(async res => {
        const [data, status] = await Promise.all([res.json(), Promise.resolve(res.status)]);
        return ({
            data,
            status
        });
    })
    .then(res => {
        if (res.status === 404) {
            showSnackbar(`${itemName} non trovato`, 'rgb(255, 208, 208)', 'black');
            closePopups(['edit-popup']);
        } else if (res.status === 400) {
            showSnackbar(res.data.detail, 'rgb(255, 208, 208)', 'black');
        } else {
            closePopups(['edit-popup']);
        }
    })
    .catch(error => console.log(error));
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
    .then(async res => {
        const [data, status] = await Promise.all([res.json(), Promise.resolve(res.status)]);
        return ({
            data,
            status
        });
    })
    .then(res => {
        if (res.status === 404) {
            showSnackbar(`${itemName} non trovato`, 'rgb(255, 208, 208)', 'black');
        }
        closePopups(['delete-popup']);
    })
    .catch(error => showSnackbar(`${error}`, 'red', 'white'));
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

function connectWebSocket() {
    websocket_connection = new WebSocket(websocketUrlPath);

    websocket_connection.addEventListener('message', async (e) => {
        if (e.data) {
            const data = JSON.parse(e.data);
            let specific = null;
            const objectEntriesParams = Object.entries(params);
            objectEntriesParams.forEach(([key, value]) => {
                if (data.data[key]) {
                    specific = `${value} "${data.data[key]}"`;
                    return;
                }
            })
            if (objectEntriesParams.some(([_, value]) => value !== "" && value !== null)) {
                specific = `con ${specific}`;
            }
            if (data.action === "add") {
                await updateTable();
                const obj = getTableColumns();
                const li = obj.table.querySelector(`tr[data-id="${data.data.id}"]`);
                if (li) {
                    li.classList.add('added');
                    li.addEventListener('animationend', () => {
                        li.classList.remove('added');
                    }, { once: true });
                }
                showSnackbar(`Nuovo ${itemName.toLowerCase()} ${specific} creato`, 'rgb(208, 255, 208)', 'black');
            } else if (data.action === "update") {
                await updateTable();
                const obj = getTableColumns();
                const li = obj.table.querySelector(`[data-id="${data.data.id}"]`);
                if (li) {
                    li.classList.toggle('updated');
                    // Rimuove la classe dopo l'animazione
                    li.addEventListener('animationend', async () => {
                        li.classList.remove('updated');
                    }, { once: true }); // Ascolta solo una volta
                }
                showSnackbar(`${itemName} ${specific} modificato`, 'rgb(255, 240, 208)', 'black');
            } else if (data.action === "delete") {
                const obj = getTableColumns();
                const li = obj.table.querySelector(`[data-id="${data.data.id}"]`);
                if (li) {
                    li.classList.toggle('deleted');
                    li.addEventListener('animationend', async () => {
                        await updateTable();
                    }, { once: true });
                } else {
                    await updateTable();
                }
                showSnackbar(`${itemName} ${specific} eliminato`, 'rgb(255, 208, 208)', 'black');
            }
        }
        if (callback_websocket_message) callback_websocket_message(e);
    });

    websocket_connection.addEventListener('open', () => {
        updateTable();
    });

    websocket_connection.addEventListener('error', () => {
        if (!isRefreshing) attemptReconnect();
    });

    websocket_connection.addEventListener('close', () => {
        if (!isRefreshing) attemptReconnect();
    });
}

function attemptReconnect() {
    clearTimeout(reconnectTimeout);
    if (websocket_connection) {
        websocket_connection.close(); // Chiude la connessione WebSocket
        websocket_connection = null;  // Imposta websocket_connection a null per indicare che la connessione è chiusa
    }
    reconnectTimeout = setTimeout(() => {
        connectWebSocket(websocketUrlPath);
    }, 3000);
}

function init() {
    connectWebSocket();
}