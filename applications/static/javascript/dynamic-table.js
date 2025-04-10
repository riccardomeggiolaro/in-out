let currentPage = 1;
let rowsPerPage = 10;
let totalRows = 0; // Aggiungi questa variabile per tenere traccia del numero totale di righe
let itemName = null;
let lastChar = 'o';
let canAlwaysDelete = false;
let listUrlPath = null;
let addUrlPath = null;
let setUrlPath = null;
let deleteUrlPath = null;
let websocketUrlPath = null;
let callback_populate_select = null;
let callback_websocket_message = null;
let callback_close_popups = null;
let populate_detail_tr = null;
let currentId = null;
let confirm_exec_funct = null;
let currentRowExtended = null;
let websocket_connection = null;
let isRefreshing = false;
let reconnectTimeout = null;
let typeSelect; // update or delete
let params = {};
let requestIdCounter = 0;
// Track pending requests
const pendingRequests = new Map();
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
    editButton.onclick = (e) => {
        e.preventDefault();
        selectAnagrafic(item.id, "UPDATE", itemName);
        currentId = item.id;
    };
    // Pulsante Elimina
    const deleteButton = document.createElement("button");
    deleteButton.style.visibility = 'hidden';
    deleteButton.textContent = "🗑️";
    deleteButton.onclick = (e) => {
        e.preventDefault();
        selectAnagrafic(item.id, "DELETE", itemName);
    };        
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
        console.log(row);
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
    console.log(row);
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
        if (element.name) {
            const keys = element.name.split('.'); // Suddivide l'ID in base al punto
            let currentObj = formData; // Inizializziamo l'oggetto principale
            // Scorriamo i segmenti dell'ID e creiamo la struttura ad albero
            for (let i = 0; i < keys.length; i++) {
                const key = keys[i];
                // Se siamo nell'ultimo livello, aggiungiamo il valore
                if (i === keys.length - 1) {
                    if (element.type === 'checkbox') currentObj[key] = element.checked;
                    else if (element.type === 'radio') {
                        if (element.checked) currentObj[key] = element.value;
                    } else if (element.type === 'text') currentObj[key] = element.value;
                    else if (element.type === 'number') currentObj[key] = element.value !== "" ? element.value : -1;
                } else {
                    // Se non siamo all'ultimo livello, assicurarsi che l'oggetto esista
                    if (!currentObj[key]) currentObj[key] = {}; // Crea un oggetto vuoto se non esiste
                    currentObj = currentObj[key]; // Scorriamo al livello successivo
                }
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
            showSnackbar(res.data.detail, 'rgb(255, 208, 208)', 'black');
            closePopups(['edit-popup']);
        } else if (res.status === 400) {
            showSnackbar(res.data.detail, 'rgb(255, 208, 208)', 'black');
        } else {
            closePopups(['edit-popup']);
        }
    })
    .catch(error => console.log(error));
});

function triggerEventsForAll(elements) {
    // Seleziona tutti gli elementi input
    const allInputs = document.querySelectorAll(elements);
    
    // Crea gli eventi
    const inputEvent = new Event('input', {
      bubbles: true,
      cancelable: true
    });
    
    const changeEvent = new Event('change', {
      bubbles: true,
      cancelable: true
    });
    
    // Itera su tutti gli elementi
    allInputs.forEach(input => {

      // Lancia input per tutti
      input.dispatchEvent(inputEvent);
      
      // Lancia anche change per radio e checkbox
      if (input.type === 'radio' || input.type === 'checkbox') {
        input.dispatchEvent(changeEvent);
      }
    });
}

// Funzioni segnaposto per modifica ed eliminazione
function editRow(item) {
    const funct = () => {
        if (callback_populate_select) callback_populate_select('#edit', item);
        currentId = item.id;
        document.getElementById('overlay').classList.add('active');
        editPopup.classList.add('active');
        for (let key in item) {
            let annidate_key = `#${key}`;
            let annidate_value = item[key];
            if (typeof annidate_value === 'object' && annidate_value !== null && !Array.isArray(annidate_value)) {
                Object.entries(annidate_value).forEach(([sub_key, sub_value]) => {
                    annidate_key = `#${key}\\.${sub_key}`;
                    annidate_value = sub_value;
                    const keyInput = editPopup.querySelector(annidate_key);
                    if (keyInput) {
                        keyInput.value = annidate_value;
                    }
                })
            } else {
                const keyInput = editPopup.querySelector(annidate_key);
                if (keyInput) {
                    if (keyInput.type === "radio") {
                        if (annidate_value === "Cliente") annidate_value = "CUSTOMER"
                        else if (annidate_value === "Fornitore") annidate_value = "SUPPLIER"
                        document.querySelectorAll(annidate_key).forEach(input => {
                            if (input.value === annidate_value) {
                                input.checked = true;
                            }
                        });                        
                    } else {
                        keyInput.value = annidate_value;
                    }
                }
            }
        }
        triggerEventsForAll('.id');
    }
    if (item.reservations ? item.reservations.length > 0 : item.weighings.length > 0) {
        const reservations_or_weighings = item.reservations ? "prenotazioni" : "pesate";
        confirm_exec_funct = funct;
        document.querySelector('#confirm-title').textContent = "Attenzione!";
        document.querySelector('#confirm-content').innerHTML = `
            Apportando le modifiche, verranno aggiornati anche i dati correlati alle ${reservations_or_weighings}.
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
            showSnackbar(res.data.detail, 'rgb(255, 208, 208)', 'black');
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
    if (item.reservations ? item.reservations.length > 0 : item.weighings.length > 0 && !canAlwaysDelete) {
        const reservations_or_weighings = item.reservations ? "prenotazioni" : "pesate";
        document.querySelector('#confirm-title').textContent = "Attenzione!";
        document.querySelector('#confirm-content').textContent = `
            Non è possibile procedere con l'eliminazione perchè è associata a delle ${reservations_or_weighings}.
        `;
        openPopup('confirm-popup');
    } else {
        funct();
    }
}

const confirmPopup = document.getElementById('confirm-popup');
confirmPopup.querySelector('#save-btn').addEventListener('click', () => {
    const clone_funct = confirm_exec_funct;
    closePopups(['confirm-popup'], false);
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

function closePopups(idPopups, deselectCurrentId=true) {
    confirm_exec_funct = null;
    if (deselectCurrentId) {
        if (currentId) {
            deselectAnagrafic(currentId);
            currentId = null;
        }    
    }
    if (callback_close_popups) callback_close_popups();
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

function capitalizeFirstLetter(str) {
  if (!str) return str; // If the string is empty or undefined, return it as is
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function determineGender(word) {
    // Convert the word to lowercase to avoid case-sensitive issues
    word = word.toLowerCase();

    // Check the word's ending
    if (word.endsWith('a') || word.endsWith('e')) {
        return 1;
    } else {
        return 0;
    }
}

function connectWebSocket() {
    websocket_connection = new WebSocket(websocketUrlPath);

    websocket_connection.addEventListener('message', async (e) => {
        if (e.data) {
            const data = JSON.parse(e.data);
            if (data.data) {
                const firstKey = Object.keys(data.data)[0];
                data.data[firstKey] = JSON.parse(data.data[firstKey]);
                let specific = '';
                const objectEntriesParams = Object.entries(params);
                for (let [key, value] of objectEntriesParams) {
                    let current = structuredClone(data.data);
                    const keys = value.split(".");
                    for (let i = 0; i < keys.length; i++) {
                        if (current && current.hasOwnProperty(keys[i])) {
                            current = current[keys[i]];
                            if (typeof(current) === 'string' || typeof(current) === 'number') {
                                specific = `${key} "${current}"`;
                            }
                        }
                    }
                    if (specific) {
                        break; // Interrompe il ciclo principale quando si trova una corrispondenza
                    }
                }            
                if (data.action === "add") {
                    await updateTable();
                    const obj = getTableColumns();
                    const li = obj.table.querySelector(`tr[data-id="${data.data[firstKey].id}"]`);
                    if (li) {
                        li.classList.add('added');
                        li.addEventListener('animationend', () => {
                            li.classList.remove('added');
                        }, { once: true });
                    }
                    showSnackbar(capitalizeFirstLetter(`Nuov${lastChar} ${specific} creat${lastChar}`), 'rgb(208, 255, 208)', 'black');
                } else if (data.action === "update") {
                    await updateTable();
                    const obj = getTableColumns();
                    const li = obj.table.querySelector(`[data-id="${data.data[firstKey].id}"]`);
                    if (li) {
                        li.classList.toggle('updated');
                        // Rimuove la classe dopo l'animazione
                        li.addEventListener('animationend', async () => {
                            li.classList.remove('updated');
                        }, { once: true }); // Ascolta solo una volta
                    }
                    let action = `modificat${lastChar}`;
                    if (firstKey === "weighing") action = `effettuat${lastChar}`;
                    showSnackbar(capitalizeFirstLetter(`${specific} ${action}`), 'rgb(255, 240, 208)', 'black');
                } else if (data.action === "delete") {
                    const obj = getTableColumns();
                    const tr = obj.table.querySelector(`[data-id="${data.data[firstKey].id}"]`);
                    if (tr) {
                        if (firstKey === "weighing") {
                            if (currentRowExtended) {
                                try {
                                    currentRowExtended.querySelector('li:first-child').classList.toggle('deleted');
                                    currentRowExtended.querySelector('li:first-child').addEventListener('animationend', async () => {
                                        await updateTable();
                                        toggleExpandRow(obj.table.querySelector(`[data-id="${data.data[firstKey].id}"]`));
                                    }, { once: true });
                                } catch {
                                    await updateTable();
                                }
                            } else {
                                await updateTable();
                            }
                        } else {
                            tr.classList.toggle('deleted');
                            tr.addEventListener('animationend', async () => {
                                await updateTable();
                                toggleExpandRow(obj.table.querySelector(`[data-id="${data.data[firstKey].id}"]`));
                            }, { once: true });
                        }
                    } else {
                        await updateTable();
                    }
                    showSnackbar(capitalizeFirstLetter(`${specific} eliminat${lastChar}`), 'rgb(255, 208, 208)', 'black');
                } else if (data.action === "lock") {
                    if (data.success === true) {
                        if (data.type === "UPDATE") editRow(data.data);
                        else if (data.type === "DELETE") deleteRow(data.data);
                        else if (data.type === "SELECT") {
                            if (pendingRequests.has(data.idRequest)) {
                                const request = pendingRequests.get(data.idRequest);
                                if (request.callback_anagrafic) request.callback_anagrafic();
                                pendingRequests.delete(data.idRequest);
                            }
                        }
                    }
                    else console.log(data)
                } else if (data.action === "unlock") {
                    if (data.success === true) {
                        if (pendingRequests.has(data.idRequest)) {
                            const request = pendingRequests.get(data.idRequest);
                            if (request.callback_anagrafic) request.callback_anagrafic();
                            pendingRequests.delete(data.idRequest);
                        }
                    }
                }
            } else {
                showSnackbar(data.error, 'rgb(255, 208, 208)', 'black');
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

async function sendWebSocketRequest(action, data, callback_anagrafic) {
    return new Promise((resolve, reject) => {
        if (!websocket_connection || websocket_connection.readyState !== WebSocket.OPEN) {
            reject(new Error("WebSocket is not connected"));
            return;
        }

        // Create a unique request ID
        const idRequest = ++requestIdCounter;

        // Store the promise callbacks
        pendingRequests.set(idRequest, { resolve, reject, callback_anagrafic });

        // Send the request with the ID
        const message = { action, ...data, idRequest };
        websocket_connection.send(JSON.stringify(message));
        
        // Set a timeout to clean up if no response comes
        setTimeout(() => {
            if (pendingRequests.has(idRequest)) {
                pendingRequests.delete(idRequest);
                // reject(new Error("Request timed out"));
            }
        }, 10000); // 10 second timeout
    });
}

// Example of using WebSocket for selectAnagrafic
async function selectAnagrafic(idRecord, type, anagrafic=itemName, callback_anagrafic=null) {
    try {
        const response = await sendWebSocketRequest("lock", { idRecord, type, anagrafic }, callback_anagrafic);
        return response.data;
    } catch (error) {
        console.error("Error selecting anagrafic:", error);
        throw error;
    }
}

// Example of using WebSocket for deselectAnagrafic
async function deselectAnagrafic(idRecord, anagrafic=itemName, callback_anagrafic=null) {
    try {
        const type = "";
        const response = await sendWebSocketRequest("unlock", { idRecord, type, anagrafic }, callback_anagrafic);
        return response;
    } catch (error) {
        console.error("Error deselecting anagrafic:", error);
        throw error;
    }
}

function init() {
    connectWebSocket();
}