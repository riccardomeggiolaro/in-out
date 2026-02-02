let dataUser = null;
let config = null;
let currentPage = 1;
let rowsPerPage = 10;
let totalRows = 0; // Aggiungi questa variabile per tenere traccia del numero totale di righe
let itemName = null;
let nextElementSibling = null;
let lastChar = 'o';
let canAlwaysDelete = false;
let listUrlPath = null;
let exportUrlPath = null;
let addUrlPath = null;
let setUrlPath = null;
let closeUrlPath = null;
let deleteUrlPath = null;
let websocketUrlPath = null;
let callback_populate_select = null;
let callback_websocket_message = null;
let callback_close_popups = null;
let callback_populate_table = null;
let callback_call_anagrafic = null;
let populate_detail_tr = null;
let currentId = null;
let currentIdInOut = null;
let confirm_exec_funct = null;
let currentRowExtended = null;
let websocket_connection = null;
let isRefreshing = false;
let reconnectTimeout = null;
let typeSelect; // update or delete
let params = {};
let requestIdCounter = 0;
let buffer = "";
let report = {
    in: false,
    out: false
}
let customQueryParams = "";
let typeUpdate = null;
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

window.onbeforeunload = function () {
    isRefreshing = true; // Imposta il flag prima del refresh
    clearTimeout(reconnectTimeout);
};

document.querySelectorAll('thead th').forEach((th, index) => {
    const columnName = th.attributes["name"];
    if (columnName && columnName.value) {
        columns[columnName.value] = index;
    }
});

async function configuration() {
    const response = await fetch('/api/config-weigher/configuration');
    if (response.ok) {
        response.json()
        .then(res => {
            config = res;
            Object.keys(res.weighers).forEach(i => {
                const instance = res.weighers[i];
                Object.keys(instance.nodes).forEach(weigher => {
                    report.in = instance.nodes[weigher].events.weighing.report.in;
                    report.out = instance.nodes[weigher].events.weighing.report.out;
                });
                if (Object.keys(config.panel).length === 0) document.querySelectorAll(".li-panel-mode").forEach(li => li.style.display = "none");
                if (!res.use_badge) {
                    document.querySelectorAll(".badge").forEach(input => {
                        if (input.previousElementSibling && input.previousElementSibling.tagName === 'LABEL') {
                            input.previousElementSibling.style.display = 'none';
                        }
                        if (input.tagName === 'TH') {
                            // Rimuovi la colonna dalla tabella
                            const th = input;
                            const table = th.closest('table');
                            if (table) {
                                const index = Array.from(th.parentNode.children).indexOf(th);
                                // Rimuovi la cella header
                                th.parentNode.removeChild(th);
                                // Rimuovi tutte le celle della colonna corrispondente
                                table.querySelectorAll('tbody tr').forEach(tr => {
                                    if (tr.children[index]) tr.removeChild(tr.children[index]);
                                });
                                // Decrementa tutti i colspan
                                table.querySelectorAll('[colspan]').forEach(cell => {
                                    let colspan = parseInt(cell.getAttribute('colspan'), 10);
                                    if (colspan > 1) {
                                        cell.setAttribute('colspan', colspan - 1);
                                    }
                                });
                            }
                        } else {
                            input.style.display = 'none';
                        }
                    });
                }
                if (!res.use_white_list) {
                    document.querySelectorAll(".white_list").forEach(input => {
                        if (input.previousElementSibling && input.previousElementSibling.tagName === 'LABEL') {
                            input.previousElementSibling.style.display = 'none';
                        }
                        input.style.display = 'none';
                    });
                }
            });
        });
    }
}

async function exportReportWeighing(idWeighing) {
    const response = await fetch(`/api/anagrafic/access/in-out/pdf/${idWeighing}`);
    if (response.ok) {
        const blob = await response.blob();
        // Prendi il nome file dall'header Content-Disposition
        const disposition = response.headers.get('Content-Disposition');
        let filename = 'report.pdf';
        if (disposition && disposition.indexOf('filename=') !== -1) {
            filename = disposition
                .split('filename=')[1]
                .replace(/["']/g, '')
                .trim();
        }
        // Download con nome corretto
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setTimeout(() => URL.revokeObjectURL(link.href), 10000);
    } else {
        showSnackbar("snackbar", "Errore nella generazione del PDF", 'rgb(255, 208, 208)', 'black');
    }
}

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
    if (itemName === "access") queryParams += customQueryParams;
    const filters = document.querySelector('#filters');
    filters.querySelectorAll('input').forEach(input => {
        if (input.name && input.type != "checkbox" && input.value || input.name && input.type == "checkbox" && input.checked) {
            if (input.type == 'text') queryParams += `${input.name}=${input.value}%&`;
            else if (input.type == 'number') queryParams += `${input.name}=${input.value}&`;
            else if (input.type == 'date') queryParams += `${input.name}=${input.value}&`;
            else if (input.type == 'checkbox') queryParams += `${input.name}=${input.checked}&`;
        }
    })
    filters.querySelectorAll('select').forEach(select => {
        if (select.name === "access.status" && select.value === "ENTERED") queryParams += "onlyInOutWithoutWeight2=true&";
        else if (select.name === "access.status" && select.value === "CLOSED") queryParams += "onlyInOutWithWeight2=true&";
        else if (select.value) {
            queryParams += `${select.name}=${select.value}&`;
        }
    })
    const offset = (currentPage - 1) * rowsPerPage;
    const res = await fetch(`${listUrlPath}?limit=${rowsPerPage}&offset=${offset}&${queryParams}`);
    const data = await res.json();

    totalRows = data.total_rows;
    if (data.buffer) buffer = data.buffer;
    populateTable(data.data);
    updatePageSelect();
    document.getElementById("total-rows").textContent = `Totale righe: ${totalRows}`;

    return data;
}

async function exportTable(type) {
    let queryParams = 'excludeTestWeighing=true&filterDateAccess=true&onlyInOutWithWeight2=true&';
    const filters = document.querySelector('#filters');
    let name;
    filters.querySelectorAll('input').forEach(input => {
        if (input.name && input.value) {
        name = itemName === "access" && !input.name.includes("access") ? `${itemName}.${input.name}` : input.name;
            if (input.type == 'text') queryParams += `${name}=${input.value}%&`;
            else if (input.type == 'number') queryParams += `${name}=${input.value}&`;
            else if (input.type == 'date') queryParams += `${name}=${input.value}&`;
        }
    })
    filters.querySelectorAll('select').forEach(select => {
        name = itemName === "access" && !select.name.includes("access") ? `${itemName}.${select.name}` : select.name;
        if (name === "access.status" && select.value === "ENTERED") queryParams += "onlyInOutWithoutWeight2=true&";
        else if (select.name === "access.status" && select.value === "CLOSED") queryParams += "onlyInOutWithWeight2=true&";
        else if (select.value) {
            queryParams += `${name}=${select.value}&`;
        }
    })
    const offset = (currentPage - 1) * rowsPerPage;
    
    const response = await fetch(`${exportUrlPath}/${type}?${queryParams}`);
    const blob = await response.blob();
    
    // Create a link element
    const downloadLink = document.createElement('a');
    downloadLink.href = window.URL.createObjectURL(blob);
    
    // Set the file name to save in Downloads
    downloadLink.download = `export_${new Date().toISOString().slice(0,10)}.${type}`;
    
    // Append to the document, click it, and remove it
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
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
    if (dataUser.level === 1) {
        const registerButton = document.querySelector(".register-button");
        if (registerButton) registerButton.style.display = 'none';
    }
    const obj = getTableColumns();
    obj.table.innerHTML = ""; // Pulisce la tabella esistente
    data.forEach(item => {
        let date1;
        let date2;
        let idInOut;
        if (item.in_out && "number_in_out" in item) {
            if (item.number_in_out) item.number_in_out = `/${item.number_in_out}`;
            item.number_in_out = item.in_out.length + item.number_in_out;
            item.in_out.forEach(in_out => {
                if (!in_out.weight1 && in_out.weight2) {
                    in_out.weight1 = {
                        "weight": in_out.weight2.is_preset_tare ? `PT ${in_out.weight2.tare}` : `TARE ${in_out.weight2.tare}`,
                        "date": in_out.weight2.date,
                        "pid": "",
                        "weighing_pictures": []
                    }
                }
            })
        }
        if (item.weight1 && item.weight1.date && isValidDate(item.weight1.date)) {
            date1 = new Date(item.weight1.date).toLocaleString('it-IT', options);
            item.access.date_created = date1;
        }
        if (item.weight2 && item.weight2.date && isValidDate(item.weight2.date)) {
            date2 = new Date(item.weight2.date).toLocaleString('it-IT', options);
            if (date1 && date2) item.access.date_created += ` - ${date2}`;
            else if (!date1 && date2) item.access.date_created = date2;
        }
        if (!item.weight1 && item.weight2) {
            item.weight1 = {
                weight: item.weight2.tare
            };
        }
        if (item.access && item.access.id) {
            idInOut = item.id;
            item.id = item.access.id;
        }
        if (item.log) item.pid = item.log;
        createRow(obj.table, obj.columns, item, idInOut);
    });
    if (callback_populate_table) callback_populate_table();
}

function formatTime(totalSeconds) {
    const days = Math.floor(totalSeconds / 86400);
    const hours = Math.floor((totalSeconds % 86400) / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    
    if (hours < 1) {
        return `${minutes} m`;
    } else if (hours < 24) {
        return `${hours}:${minutes} h`;
    } else {
        return `${days} d`;
    }
}

function startTimer(row, index, initialTimestamp) {
    // Converte il timestamp in oggetto Date
    const startTime = new Date(initialTimestamp);

    const now = new Date();
    // Calcola la differenza in millisecondi e converte in secondi
    const elapsedSeconds = Math.floor((now - startTime) / 1000);
    
    row.cells[index].textContent = formatTime(elapsedSeconds);
    
    const timer = setInterval(() => {
        const now = new Date();
        // Calcola la differenza in millisecondi e converte in secondi
        const elapsedSeconds = Math.floor((now - startTime) / 1000);
        
        row.cells[index].textContent = formatTime(elapsedSeconds);
    }, 60000);
    
    return timer;
}

function createRow(table, columns, item, idInout) {
    const row = document.createElement("tr");
    row.dataset.id = item.id;
    if (idInout) row.dataset.idInOut = idInout;
    // Create cells for each column
    for (let i = 0; i < document.querySelectorAll("thead th").length - 1; i++) {
        row.insertCell();
    }
    // Funzione ricorsiva per gestire oggetti annidati a qualsiasi livello
    function populateNestedValues(obj, prefix = '') {
        Object.entries(obj).forEach(([key, value]) => {
            const fullKey = prefix ? `${prefix}.${key}` : key;
            if (fullKey in columns) {
                // Se la colonna è "status" e la targa è nel buffer, mostra "Chiamato"
                let displayValue = value;
                if (fullKey === "status" && item.vehicle && item.vehicle.plate && buffer.includes(item.vehicle.plate)) {
                    displayValue = "Chiamato";
                }
                row.cells[columns[fullKey]].textContent = isValidDate(displayValue) && typeof (displayValue) !== "number" ? new Date(displayValue).toLocaleString('it-IT', options) : displayValue;
                row.cells[columns[fullKey]].dataset.value = value;
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
    let callButton;
    if (item.vehicle && item.vehicle.plate && item.status && item.status !== "Chiusa") {
        // Pulsante chiamata
        callButton = document.createElement("button");
        const textContent = !buffer.includes(item["vehicle"]["plate"]) ? "📢" : "🚫📢";
        const action = !buffer.includes(item["vehicle"]["plate"]) ? "CALL" : "CANCEL_CALL";
        callButton.textContent = textContent;
        callButton.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (!currentRowExtended 
                || currentRowExtended !== row.nextElementSibling
                || (currentRowExtended === row.nextElementSibling && currentRowExtended.style.display === "none")
            ) toggleExpandRow(row);
            selectAnagrafic(item.id, action, itemName);
            currentId = item.id;
        }
        callButton.style.visibility = "hidden";
        actionsCell.appendChild(callButton);
    }
    let pdfButton;
    if (itemName === "access" && "status" in item && item.status === "Attesa") {
        const th = document.querySelector('th[name="waiting"]');
        const index = Array.from(th.parentNode.children).indexOf(th);
        startTimer(row, index, item.date_created);
    } else if (itemName === "access" && idInout) {
        if (!item.weight2 && report.in || item.weight2 && report.out) {
            pdfButton = document.createElement("button");
            pdfButton.style.visibility = 'hidden';
            pdfButton.textContent = "📄";
            pdfButton.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                exportReportWeighing(idInout);
            }
            actionsCell.appendChild(pdfButton);
        }
    }
    // Pulsante Chiudi
    const closeButton = document.createElement("button");
    closeButton.style.visibility = 'hidden';
    closeButton.textContent = "🚫";
    closeButton.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!currentRowExtended 
            || currentRowExtended !== row.nextElementSibling
            || (currentRowExtended === row.nextElementSibling && currentRowExtended.style.display === "none")
        ) toggleExpandRow(row);
        selectAnagrafic(item.id, "UPDATE", itemName);
        currentId = item.id;
        currentIdInOut = idInout;
        typeUpdate = "CLOSE";
    };
    // Pulsante Modifica
    const editButton = document.createElement("button");
    editButton.style.visibility = 'hidden';
    editButton.textContent = "✏️";
    editButton.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!currentRowExtended 
            || currentRowExtended !== row.nextElementSibling
            || (currentRowExtended === row.nextElementSibling && currentRowExtended.style.display === "none")
        ) toggleExpandRow(row);
        selectAnagrafic(item.id, "UPDATE", itemName);
        currentId = item.id;
        currentIdInOut = idInout;
        typeUpdate = "UPDATE";
    };
    // Pulsante Elimina
    const deleteButton = document.createElement("button");
    deleteButton.style.visibility = 'hidden';
    deleteButton.textContent = "🗑️";
    deleteButton.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!currentRowExtended 
            || currentRowExtended !== row.nextElementSibling
            || (currentRowExtended === row.nextElementSibling && currentRowExtended.style.display === "none")
        ) toggleExpandRow(row);
        selectAnagrafic(item.id, "DELETE", itemName);
        currentId = item.id;
    };
    const permanentAccess = document.createElement("span");
    permanentAccess.textContent = "⭐";
    if (itemName !== "pid") {
        if (itemName === "access" && item.in_out && item.status !== "Chiusa" && item.in_out.length > 0 && item.in_out[item.in_out.length-1].idWeight2 !== null) actionsCell.appendChild(closeButton);
        actionsCell.appendChild(editButton);
        if (idInout && item.is_last) actionsCell.appendChild(deleteButton);
        else if (item.in_out && item.in_out.length === 0 || item.weighings && item.weighings.length === 0) actionsCell.appendChild(deleteButton);
        else if (!idInout && !item.in_out && !item.weighings) actionsCell.appendChild(deleteButton);
        if (itemName === "access" && "in_out" in item && !String(item.number_in_out).includes("/")) actionsCell.appendChild(permanentAccess);
    }
    row.appendChild(actionsCell);
    // Mostra i pulsanti solo all'hover della riga
    row.addEventListener("mouseenter", () => {
        row.style.backgroundColor = 'whitesmoke';
        if (closeButton) closeButton.style.visibility = 'inherit';
        if (dataUser.level > 1) editButton.style.visibility = 'inherit';
        if (dataUser.level > 1) deleteButton.style.visibility = 'inherit';
        if (Object.keys(config.panel).length !== 0 && callButton) callButton.style.visibility = 'inherit';
        if (pdfButton) pdfButton.style.visibility = 'inherit';
    });
    row.addEventListener("mouseleave", () => {
        row.style.backgroundColor = 'white';
        if (closeButton) closeButton.style.visibility = 'hidden';
        editButton.style.visibility = 'hidden';
        deleteButton.style.visibility = 'hidden';
        if (callButton) callButton.style.visibility = 'hidden';
        if (pdfButton) pdfButton.style.visibility = 'hidden';
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
                row.cells[columns[fullKey]].textContent = isValidDate(value) && typeof (value) !== "number" ? new Date(value).toLocaleString('it-IT', options) : value;
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

function isExpandedRow() {
    return currentRowExtended && currentRowExtended.style.display === "table-row";
}

// Funzione per espandere/collassare la riga
function toggleExpandRow(row) {
    if (!nextElementSibling || !row.nextElementSibling) return;
    if (currentRowExtended && currentRowExtended !== row.nextElementSibling) {
        // Se già espanso, nascondi
        currentRowExtended.style.display = "none";
    }
    currentRowExtended = row.nextElementSibling; // Dettagli subito dopo la riga
    const isExpanded = currentRowExtended.style.display === "table-row";
    currentRowExtended.style.display = isExpanded ? "none" : "table-row";
    currentRowExtended.style.backgroundColor = isExpanded ? "white" : "aliceblue";
    currentId = isExpanded ? null : row.dataset.id;
}

function getFormData(form, set_minus_one) {
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
                    else if (element.type === 'radio' && element.checked) currentObj[key] = element.value;
                    else if (element.type === 'text') currentObj[key] = element.value;
                    else if (element.type === 'number') currentObj[key] = element.value !== "" ? Number(element.value) : set_minus_one ? -1 : null;
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
    const data = getFormData(addPopup.querySelector('form'), false);
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
        if (res.status === 404 || res.status === 403) {
            showSnackbar("snackbar", res.data.detail, 'rgb(255, 208, 208)', 'black');
            closePopups(['add-popup'], false);
        } else if (res.status === 400) {
            showSnackbar("snackbar", res.data.detail, 'rgb(255, 208, 208)', 'black');
        } else {
            closePopups(['add-popup'], false);
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
    const data = getFormData(editPopup.querySelector('form'), true);
    let queryParamasIdInOut = currentIdInOut ? `?idInOut=${currentIdInOut}` : '';
    fetch(`${setUrlPath}/${currentId}${queryParamasIdInOut}`, {
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
        if (res.status === 404 || res.status === 403) {
            showSnackbar("snackbar", res.data.detail, 'rgb(255, 208, 208)', 'black');
            closePopups(['edit-popup'], false);
        } else if (res.status === 400) {
            showSnackbar("snackbar", res.data.detail, 'rgb(255, 208, 208)', 'black');
        } else {
            closePopups(['edit-popup'], false);
        }
    })
    .catch(error => console.error(error));
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

function closeRow(item) {
    const funct = () => {
        fetch(`${closeUrlPath}/${currentId}`, {
            method: 'GET',
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
            if (res.status === 404 || res.status === 403) {
                showSnackbar("snackbar", res.data.detail, 'rgb(255, 208, 208)', 'black');
                closePopups(['edit-popup'], false);
            } else if (res.status === 400) {
                showSnackbar("snackbar", res.data.detail, 'rgb(255, 208, 208)', 'black');
            } else {
                closePopups(['edit-popup'], false);
            }
        })
        .catch(error => console.error(error));
    }
    confirm_exec_funct = funct;
    document.querySelector('#confirm-title').textContent = "Attenzione!";
    document.querySelector('#confirm-content').innerHTML = `
        Sei sicuro di voler chiudere questo accesso?
    `;
    openPopup('confirm-popup');
}

// Funzioni segnaposto per modifica ed eliminazione
function editRow(item) {
    const funct = () => {
        if (callback_populate_select) callback_populate_select('#edit', item);
        currentId = item.id;
        if (currentIdInOut) {
            let current_in_out = item.in_out.find(in_out => in_out.id === currentIdInOut);
            console.log(currentIdInOut, current_in_out);
            console.log(item);
            item.material = current_in_out ? current_in_out.material : '';
            if (item.in_out.length > 0) {
                const in_out = item.in_out.find(obj => obj.id === currentIdInOut);
                item.operator1 = in_out.weight1 ? in_out.weight1.operator : null;
                item.operator2 = in_out.weight2 ? in_out.weight2.operator : null;
            }
            console.log(item);
        }
        document.getElementById('overlay').classList.add('active');
        editPopup.classList.add('active');
        if ("number_in_out" in item) {
            item["permanent"] = item["number_in_out"] !== null ? false : true;
        }
        for (let key in item) {
            let annidate_key = `#${key}`;
            let annidate_value = item[key];
            console.log(annidate_key);
            if (typeof annidate_value === 'object' && annidate_value !== null && !Array.isArray(annidate_value)) {
                Object.entries(annidate_value).forEach(([sub_key, sub_value]) => {
                    annidate_key = `#${key}\\.${sub_key}`;
                    annidate_value = sub_value;
                    const keyInput = editPopup.querySelector(annidate_key);
                    if (keyInput) {
                        if (keyInput.type === "radio") {
                            if (annidate_value === "Cliente") annidate_value = "CUSTOMER";
                            else if (annidate_value === "Fornitore") annidate_value = "SUPPLIER";
                            document.querySelectorAll(annidate_key).forEach(input => {
                                if (input.value === annidate_value) {
                                    input.checked = true;
                                }
                            });
                        } else if (keyInput.type === "checkbox") {
                            keyInput.checked = annidate_value;
                        } else {
                            keyInput.value = annidate_value;
                        }
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
                    } else if (keyInput.type === "checkbox") {
                        keyInput.checked = annidate_value;
                    } else {
                        if (keyInput.id === "number_in_out") {
                            const length = item["in_out"].length;
                            keyInput.min = length > 0 ? length : 1;
                            keyInput.dataset.in_out = length;
                            if (item["permanent"] == true) {
                                keyInput.required = false;
                                keyInput.disabled = true;
                            } else keyInput.dataset.default_value = annidate_value;
                        }
                        keyInput.value = annidate_value;
                    }
                }
            }
        }
        if ("is_latest_for_vehicle" in item && item["is_latest_for_vehicle"] === false || "permanent" in item && item["permanent"] === true || item.type === "Manuale") {
            document.querySelectorAll('#edit [name="number_in_out"]').forEach(element => element.style.display = "none");
            document.querySelectorAll('#edit [name="permanent"]').forEach(element => element.style.display = "none");
        } else {
            document.querySelectorAll('#edit [name="number_in_out"]').forEach(element => element.style.display = "block");
            document.querySelectorAll('#edit [name="permanent"]').forEach(element => element.style.display = "none");
        }
        triggerEventsForAll('.id');
    }
    if (item.accesses ? item.accesses.length > 0 : (item.in_out ? item.in_out.length > 0 : item.weighings.length > 0)) {
        const accesses_or_weighings = item.accesses ? "prenotazioni" : "pesate";
        confirm_exec_funct = funct;
        document.querySelector('#confirm-title').textContent = "Attenzione!";
        document.querySelector('#confirm-content').innerHTML = `
            Apportando le modifiche, verranno aggiornati anche i dati correlati alle ${accesses_or_weighings}.
        `;
        openPopup('confirm-popup');
    } else {
        funct();
    }
}

const deletePopup = document.getElementById('delete-popup');
deletePopup.querySelector('#save-btn').addEventListener('click', () => {
    let queryParams = !nextElementSibling && itemName === "access" ? 'deleteAccessIfislastInOut=true' : '';
    fetch(`${deleteUrlPath}/${currentId}?${queryParams}`, {
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
        if (res.status !== 200) {
            showSnackbar("snackbar", res.data.detail ? res.data.detail : res.data, 'rgb(255, 208, 208)', 'black');
        }
        closePopups(['delete-popup'], false);
    })
    .catch(error => showSnackbar("snackbar", `${error}`, 'red', 'white'));
})

function deleteRow(item) {
    const funct = () => {
        if (callback_populate_select) callback_populate_select('#delete', item);
        currentId = item.id;
        if (currentIdInOut) item.material = item.in_out.find(in_out => in_out.id === currentIdInOut).material;
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
    if (item.accesses ? item.accesses.length > 0 : (item.in_out ? item.in_out.length > 0 : item.weighings.length > 0) && !canAlwaysDelete) {
        const accesses_or_weighings = item.accesses ? "prenotazioni" : "pesate";
        document.querySelector('#confirm-title').textContent = "Attenzione!";
        document.querySelector('#confirm-content').textContent = `
            Non è possibile procedere con l'eliminazione perchè è associata a delle ${accesses_or_weighings}.
        `;
        openPopup('confirm-popup');
    } else {
        funct();
    }
}

const confirmPopup = document.getElementById('confirm-popup');
confirmPopup.querySelector('#save-btn').addEventListener('click', () => {
    const clone_funct = confirm_exec_funct;
    closePopups(['confirm-popup'], clone_funct ? false : true);
    if (typeof (clone_funct) === "function") {
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

function closePopups(idPopups, deselectCurrentId = true) {
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
        const saveBtn = popup.querySelector('.save-btn');
        if (saveBtn) {
            saveBtn.disabled = true;
        }
        // Resetta i campi input
        const inputs = popup.querySelectorAll('input');
        inputs.forEach(input => {
            if (input.disabled) input.disabled = false;
            if (input.type !== 'radio') input.value = '';
            if (input.type === 'checkbox') input.checked = false;
            if (input.dataset.id) input.dataset.id = '';
            if (idPopup == "add-popup" && itemName == "access") {
                document.querySelector(`#${idPopup} #number_in_out`).required = true;
                document.querySelector(`#${idPopup} #number_in_out`).color = 'black';
            }
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
    const token = localStorage.getItem('token');
    websocket_connection = new WebSocket(`${websocketUrlPath}?token=${encodeURIComponent(token)}`);

    websocket_connection.addEventListener('message', async (e) => {
        if (e.data) {
            const data = JSON.parse(e.data);
            if (data.data) {
                const firstKey = Object.keys(data.data)[0];
                data.data[firstKey] = data.data[firstKey] && isJsonString(data.data[firstKey]) ? JSON.parse(data.data[firstKey]) : data.data[firstKey];
                let specific = '';
                const objectEntriesParams = Object.entries(params);
                for (let [key, value] of objectEntriesParams) {
                    let current = structuredClone(data.data);
                    const keys = value.split(".");
                    if (keys[0] == firstKey) {
                        for (let i = 0; i < keys.length; i++) {
                            if (current && current.hasOwnProperty(keys[i])) {
                                current = current[keys[i]];
                                if (typeof (current) === 'string' || typeof (current) === 'number') {
                                    specific = `${key} "${current}"`;
                                }
                            }
                        }
                    }
                    else if (specific) {
                        break; // Interrompe il ciclo principale quando si trova una corrispondenza
                    }
                }
                if (data.action === "add") {
                    await updateTable();
                    const obj = getTableColumns();
                    const tr = obj.table.querySelector(`[data-id="${data.data[firstKey].id}"]`);
                    const currentRow = obj.table.querySelector(`[data-id="${currentId}"]`);
                    if (tr || currentRow) {
                        if (firstKey === "weighing") {
                            if (isExpandedRow() && data.data["weighing"].id == currentId) {
                                toggleExpandRow(currentRow);
                                currentRow.nextElementSibling.querySelector('li:first-child p').classList.toggle('soft-added');
                            } else {
                                if (tr) tr.classList.toggle('soft-added');
                                if (isExpandedRow()) {
                                    toggleExpandRow(currentRow);
                                }
                            }
                        } else {
                            tr.classList.toggle('added');
                            if (isExpandedRow()) {
                                toggleExpandRow(currentRow);
                            }
                        }
                    }
                    let action = `creat${lastChar}`;
                    if (firstKey === "weighing") action = `effettuat${lastChar}`;
                    showSnackbar("snackbar", capitalizeFirstLetter(`Nuov${lastChar} ${specific} ${action}`), 'rgb(208, 255, 208)', 'black');
                } else if (data.action === "update") {
                    await updateTable();
                    const obj = getTableColumns();
                    const tr = obj.table.querySelector(`[data-id="${data.data[firstKey].id}"]`);
                    const currentRow = obj.table.querySelector(`[data-id="${currentId}"]`);
                    if (tr) {
                        if (isExpandedRow()) {
                            toggleExpandRow(currentRow);
                        }
                        tr.classList.toggle('updated');
                    }
                    showSnackbar("snackbar", capitalizeFirstLetter(`${specific} modificat${lastChar}`), 'rgb(255, 240, 208)', 'black');
                } else if (data.action === "delete") {
                    const obj = getTableColumns();
                    let tr = obj.table.querySelector(`[data-id="${data.data[firstKey].id}"]`);
                    let currentRow = obj.table.querySelector(`[data-id="${currentId}"]`);
                    if (tr) {
                        if (firstKey === "weighing") {
                            if (isExpandedRow() && data.data["weighing"].id == currentId) {
                                currentRowExtended.querySelector('li:first-child p').classList.toggle('deleted');
                                currentRowExtended.querySelector('li:first-child p').addEventListener('animationend', async () => {
                                    await updateTable()
                                    .then(_ => {
                                        currentRow = obj.table.querySelector(`[data-id="${currentId}"]`);
                                        if (isExpandedRow())  {
                                            toggleExpandRow(currentRow);
                                        }
                                    })
                                }, { once: true });
                            } else {
                                tr.classList.toggle('soft-deleted');
                                tr.addEventListener('animationend', async () => {
                                    await updateTable()
                                    .then(_ => {
                                        currentRow = obj.table.querySelector(`[data-id="${currentId}"]`);
                                        if (isExpandedRow())  {
                                            toggleExpandRow(currentRow);
                                        }
                                    })
                                }, { once: true });
                            }
                        } else {
                            tr.classList.toggle('deleted');
                            tr.addEventListener('animationend', async () => {
                                await updateTable()
                                .then(_ => {
                                    currentRow = obj.table.querySelector(`[data-id="${currentId}"]`);
                                    if (isExpandedRow())  {
                                        toggleExpandRow(currentRow);
                                    }
                                })
                            }, { once: true });
                        }
                    } else {
                        await updateTable();
                    }
                    showSnackbar("snackbar", capitalizeFirstLetter(`${specific} eliminat${lastChar}`), 'rgb(255, 208, 208)', 'black');
                } else if (data.action === "call") {
                    await updateTable();
                    const obj = getTableColumns();
                    const tr = obj.table.querySelector(`[data-id="${data.data[firstKey].id}"]`);
                    if (tr) {
                        tr.classList.toggle('updated');
                        // Rimuove la classe dopo l'animazione
                        tr.addEventListener('animationend', async () => {
                            tr.classList.remove('updated');
                        }, { once: true }); // Ascolta solo una volta
                    }
                    if (data.data.panel_error) {
                        showSnackbar("snackbar", `Errore pannello: ${data.data.panel_error}`, 'rgb(255, 208, 208)', 'black');
                    } else {
                        showSnackbar("snackbar", capitalizeFirstLetter(`${specific} chiamat${lastChar}`), 'rgb(255, 240, 208)', 'black');
                    }
                } else if (data.action === "cancel_call") {
                    await updateTable();
                    const obj = getTableColumns();
                    const tr = obj.table.querySelector(`[data-id="${data.data[firstKey].id}"]`);
                    if (tr) {
                        tr.classList.toggle('updated');
                        // Rimuove la classe dopo l'animazione
                        tr.addEventListener('animationend', async () => {
                            tr.classList.remove('updated');
                        }, { once: true }); // Ascolta solo una volta
                    }
                    if (data.data.panel_error) {
                        showSnackbar("snackbar", `Errore pannello: ${data.data.panel_error}`, 'rgb(255, 208, 208)', 'black');
                    } else {
                        showSnackbar("snackbar", capitalizeFirstLetter(`Chiamata del ${specific} annullat${lastChar}`), 'rgb(255, 240, 208)', 'black');
                    } 
                } else if (data.action === "lock") {
                    if (data.success === true) {
                        if (data.type === "UPDATE") {
                            request = getWebSocketRequest(data.idRequest);
                            removeWebSocketRequest(data.idRequest);
                            if (request.custom_execute_callback) {
                                if (data.anagrafic === "access") openPopup("edit-inout-popup");
                                else openPopup("confirm-popup");
                            } else {
                                if (typeUpdate == "CLOSE") closeRow(data.data);
                                else editRow(data.data);
                            };
                        } else if (data.type === "DELETE") {
                            request = getWebSocketRequest(data.idRequest);
                            removeWebSocketRequest(data.idRequest);
                            if (request.custom_execute_callback) openPopup("confirm-popup");
                            else deleteRow(data.data)
                        } else if (data.type === "CALL") {
                            currentId = data.data.id;
                            removeWebSocketRequest(data.idRequest);
                            if (callback_call_anagrafic) callback_call_anagrafic(data.type, data.data);
                        } else if (data.type === "CANCEL_CALL") {
                            currentId = data.data.id;
                            removeWebSocketRequest(data.idRequest);
                            if (callback_call_anagrafic) callback_call_anagrafic(data.type, data.data);
                        } else if (data.type === "SELECT") removeWebSocketRequest(data.idRequest);
                    }
                } else if (data.action === "unlock") {
                    if (data.success === true) removeWebSocketRequest(data.idRequest);
                }
            } else {
                showSnackbar("snackbar", data.error, 'rgb(255, 208, 208)', 'black');
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

function getWebSocketRequest(id) {
    return pendingRequests.has(id) ? pendingRequests.get(id) : null;
}

function removeWebSocketRequest(id) {
    if (pendingRequests.has(id)) {
        const request = pendingRequests.get(id);
        if (request.callback_anagrafic) request.callback_anagrafic();
        pendingRequests.delete(id);
    }
}

async function sendWebSocketRequest(action, data, callback_anagrafic, custom_execute_callback = false) {
    return new Promise((resolve, reject) => {
        if (!websocket_connection || websocket_connection.readyState !== WebSocket.OPEN) {
            reject(new Error("WebSocket is not connected"));
            return;
        }

        // Create a unique request ID
        const idRequest = ++requestIdCounter;

        // Store the promise callbacks
        pendingRequests.set(idRequest, { resolve, reject, callback_anagrafic, custom_execute_callback });

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
async function selectAnagrafic(idRecord, type, anagrafic = itemName, callback_anagrafic = null, custom_execute_callback = false) {
    try {
        const response = await sendWebSocketRequest("lock", { idRecord, type, anagrafic }, callback_anagrafic, custom_execute_callback);
        return response.data;
    } catch (error) {
        console.error("Error selecting anagrafic:", error);
        throw error;
    }
}

// Example of using WebSocket for deselectAnagrafic
async function deselectAnagrafic(idRecord, anagrafic = itemName, callback_anagrafic = null, custom_execute_callback = false) {
    try {
        const type = "";
        const response = await sendWebSocketRequest("unlock", { idRecord, type, anagrafic }, callback_anagrafic, custom_execute_callback);
        return response;
    } catch (error) {
        console.error("Error deselecting anagrafic:", error);
        throw error;
    }
}

function isJsonString(str) {
    try {
        const parsed = JSON.parse(str);
        return typeof parsed === "object" || Array.isArray(parsed);
    } catch (e) {
        return false;
    }
}

function init() {
    const token = localStorage.getItem('token');
    fetch('/api/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
    })
    .then(res => res.json())
    .then(res => dataUser = res)
    .then(() => configuration())
    .then(() => connectWebSocket());
}