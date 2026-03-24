// ===== TOTEM COMMON - Shared utilities across all totem pages =====

// --- State ---
let currentWeigherPath = localStorage.getItem('currentWeigherPath');
let pathname = '/gateway';
let lastSlashIndex = window.location.pathname.lastIndexOf('/');
pathname = lastSlashIndex !== -1 ? pathname.substring(0, lastSlashIndex) : pathname;

let selectedVehicle = { id: null, plate: '' };
let selectedTypeSubject = 'CUSTOMER';
let selectedSubject = { id: null, social_reason: '' };
let selectedVector = { id: null, social_reason: '' };
let selectedDriver = { id: null, social_reason: '' };
let selectedMaterial = { id: null, description: '' };

let dataInExecution = null;
let selectedIdWeight = null;
let data_weight_realtime = {
    status: undefined,
    net_weight: undefined,
    gross_weight: undefined,
    tare: undefined,
    unite_measure: undefined,
    potential_net_weight: null,
    over_max_theshold: null
};

let return_pdf_copy_after_weighing = false;
let test_mode = false;
let instances = {};
let access_id = null;
let confirmWeighing = null;
let minWeightValue = 0;
let maxThesholdValue = 0;

// WebSocket
let _data;
let isRefreshing = false;
let isReconnecting = false;
let reconnectTimeout;
let reconnectionAttemptTimeout;
let autoReconnectInterval;
let pingInterval;
let pingTimeout;
let currentPopup;
let snackbarTimeout;

// --- Init ---
function initTotemPage() {
    if (!currentWeigherPath) {
        window.location.href = 'dashboard-totem.html';
        return;
    }

    fetch('/api/config-weigher/configuration')
    .then(res => res.json())
    .then(res => {
        return_pdf_copy_after_weighing = res["return_pdf_copy_after_weighing"];
        test_mode = res["test_mode"] || false;
        instances = res["weighers"];
    });

    connectWebSocket(`api/command-weigher/realtime${currentWeigherPath}`, updateUIRealtime);
}

window.onbeforeunload = function() {
    isRefreshing = true;
    clearTimeout(reconnectTimeout);
};

window.onclick = function(event) {
    const popup = document.getElementById(currentPopup);
    if (event.target === popup && currentPopup !== "reconnectionPopup") {
        closePopup();
    }
};

// --- Navigation ---
function goTo(page) {
    window.location.href = page;
}

// --- Pagination state ---
let _paginationState = {};
const GRID_COLS = 2;

function _calcItemsPerPage(containerId, items) {
    const container = document.getElementById(containerId);
    if (!container || items.length === 0) return 12;

    const step = container.closest('.step');
    if (!step) return 12;

    // Calculate height used by sibling elements (h2, buttons, etc.)
    let usedHeight = 0;
    Array.from(step.children).forEach(child => {
        if (child === container) return;
        if (child.id === containerId + '-pagination') return;
        if (!child.offsetHeight) return;
        const style = getComputedStyle(child);
        usedHeight += child.offsetHeight + parseFloat(style.marginTop || 0) + parseFloat(style.marginBottom || 0);
    });

    const availableHeight = step.clientHeight - usedHeight;

    // Temporarily add an item to measure row height
    const tempLi = items[0].li.cloneNode(true);
    container.appendChild(tempLi);
    const itemHeight = tempLi.getBoundingClientRect().height;
    container.removeChild(tempLi);

    const gap = 16;
    const paginationHeight = 64;
    const rowHeight = itemHeight + gap;

    // Calculate max rows without pagination
    let maxRows = Math.floor((availableHeight + gap) / rowHeight);
    if (items.length > maxRows * GRID_COLS) {
        // Need pagination, recalculate with space for arrows
        maxRows = Math.floor((availableHeight - paginationHeight + gap) / rowHeight);
    }

    return Math.max(1, maxRows) * GRID_COLS;
}

// Recalculate pagination on resize
let _resizeTimer;
window.addEventListener('resize', () => {
    clearTimeout(_resizeTimer);
    _resizeTimer = setTimeout(() => {
        Object.keys(_paginationState).forEach(containerId => {
            const state = _paginationState[containerId];
            if (!state || state.items.length === 0) return;
            const newItemsPerPage = _calcItemsPerPage(containerId, state.items);
            if (newItemsPerPage !== state.itemsPerPage) {
                state.itemsPerPage = newItemsPerPage;
                const totalPages = Math.ceil(state.items.length / state.itemsPerPage);
                if (state.currentPage >= totalPages) state.currentPage = Math.max(0, totalPages - 1);
                _renderPage(containerId);
            }
        });
    }, 200);
});

function _renderPage(containerId) {
    const state = _paginationState[containerId];
    if (!state) return;
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';

    const start = state.currentPage * state.itemsPerPage;
    const end = Math.min(start + state.itemsPerPage, state.items.length);
    const pageItems = state.items.slice(start, end);

    pageItems.forEach(({ li }) => {
        container.appendChild(li);
    });

    // Update pagination controls
    const arrows = document.getElementById(containerId + '-pagination');
    if (arrows) {
        const totalPages = Math.ceil(state.items.length / state.itemsPerPage);
        if (totalPages <= 1) {
            arrows.style.display = 'none';
        } else {
            arrows.style.display = 'flex';
            const prevBtn = arrows.querySelector('.pagination-prev');
            const nextBtn = arrows.querySelector('.pagination-next');
            const indicator = arrows.querySelector('.page-indicator');
            if (prevBtn) prevBtn.disabled = state.currentPage === 0;
            if (nextBtn) nextBtn.disabled = state.currentPage >= totalPages - 1;
            if (indicator) indicator.textContent = `${state.currentPage + 1} / ${totalPages}`;
        }
    }
}

function _ensurePaginationArrows(containerId) {
    let arrows = document.getElementById(containerId + '-pagination');
    if (!arrows) {
        arrows = document.createElement('div');
        arrows.id = containerId + '-pagination';
        arrows.className = 'pagination-arrows';
        arrows.innerHTML = `
            <button class="pagination-prev" aria-label="Pagina precedente">&#9664;</button>
            <span class="page-indicator">1 / 1</span>
            <button class="pagination-next" aria-label="Pagina successiva">&#9654;</button>
        `;
        const container = document.getElementById(containerId);
        if (container && container.parentNode) {
            container.parentNode.insertBefore(arrows, container.nextSibling);
        }
        arrows.querySelector('.pagination-prev').addEventListener('click', () => {
            const state = _paginationState[containerId];
            if (state && state.currentPage > 0) {
                state.currentPage--;
                _renderPage(containerId);
            }
        });
        arrows.querySelector('.pagination-next').addEventListener('click', () => {
            const state = _paginationState[containerId];
            if (state) {
                const totalPages = Math.ceil(state.items.length / state.itemsPerPage);
                if (state.currentPage < totalPages - 1) {
                    state.currentPage++;
                    _renderPage(containerId);
                }
            }
        });
    }
    return arrows;
}

// --- Load items into a list/grid ---
async function loadItems(anagrafic, filterField, inputValue, containerId, onItemClick, skipToUrl) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';

    let url = `/api/anagrafic/${anagrafic}/list?`;
    if (inputValue) url += `${filterField}=${inputValue}%`;

    try {
        const response = await fetch(url);
        const data = await response.json();
        const currentId = getCurrentId(anagrafic);
        const items = [];

        data.data.forEach(item => {
            const displayField = filterField === 'plate' ? item.plate :
                                 filterField === 'description' ? item.description :
                                 item.social_reason;
            if (!displayField) return;

            const li = document.createElement('li');
            li.dataset.id = item.id;

            const mainText = inputValue ? highlightText(displayField, inputValue) : displayField;
            let secondaryText = '';

            if (anagrafic === 'vehicle' && item.description) secondaryText = item.description;
            else if (anagrafic === 'subject' && item.cfpiva) secondaryText = item.cfpiva;
            else if (anagrafic === 'vector' && item.cfpiva) secondaryText = item.cfpiva;
            else if (anagrafic === 'driver' && item.telephone) secondaryText = item.telephone;

            li.innerHTML = `<span>${mainText}</span>${secondaryText ? `<span class="secondary">${secondaryText}</span>` : ''}`;

            if (item.id === currentId) li.classList.add('selected');

            li.addEventListener('click', () => onItemClick(item));
            items.push({ li, item });
        });

        // Skip page if list is empty and a skip URL is provided
        if (items.length === 0 && skipToUrl && !inputValue) {
            goTo(skipToUrl);
            return;
        }

        // "Create new" option only if searching (plate page)
        if (inputValue) {
            const li = document.createElement('li');
            li.classList.add('create-new');
            li.textContent = `Crea "${inputValue.toUpperCase()}"`;
            li.addEventListener('click', () => {
                if (typeof onCreateNew === 'function') onCreateNew(inputValue);
            });
            items.push({ li, item: null });
        }

        const itemsPerPage = _calcItemsPerPage(containerId, items);

        // Find the page of the selected item
        const selectedIndex = items.findIndex(({ li }) => li.classList.contains('selected'));
        const startPage = selectedIndex >= 0 ? Math.floor(selectedIndex / itemsPerPage) : 0;

        _paginationState[containerId] = {
            items,
            currentPage: startPage,
            itemsPerPage
        };

        _ensurePaginationArrows(containerId);
        _renderPage(containerId);

        // Recalculate after layout stabilizes (first load may have wrong measurements)
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                const state = _paginationState[containerId];
                if (!state || state.items.length === 0) return;
                const correctedPerPage = _calcItemsPerPage(containerId, state.items);
                if (correctedPerPage !== state.itemsPerPage) {
                    state.itemsPerPage = correctedPerPage;
                    // Recalculate selected page with corrected items per page
                    const selIdx = state.items.findIndex(({ li }) => li.classList.contains('selected'));
                    if (selIdx >= 0) {
                        state.currentPage = Math.floor(selIdx / state.itemsPerPage);
                    }
                    const totalPages = Math.ceil(state.items.length / state.itemsPerPage);
                    if (state.currentPage >= totalPages) state.currentPage = Math.max(0, totalPages - 1);
                    _renderPage(containerId);
                }
            });
        });
    } catch (error) {
        console.error('Error loading items:', error);
    }
}

// --- Select and advance (for grid selection pages) ---
function selectAndAdvance(anagrafic, item, nextPage) {
    const id = parseInt(item.id);

    fetch(`/api/data${currentWeigherPath}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data_in_execution: { [anagrafic]: { id } } })
    })
    .then(res => res.json())
    .then(res => {
        if (res.detail) {
            showSnackbar("snackbar", res.detail, 'rgb(255, 208, 208)', 'black');
        } else {
            showSnackbar("snackbar", `${getAnagraficLabel(anagrafic)} selezionato`, 'rgb(208, 255, 208)', 'black');
            setTimeout(() => goTo(nextPage), 300);
        }
    });
}

// --- Select vehicle (plate page, no auto-advance) ---
function selectVehicle(item) {
    const id = parseInt(item.id);

    fetch(`/api/data${currentWeigherPath}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data_in_execution: { vehicle: { id } } })
    })
    .then(res => res.json())
    .then(res => {
        if (res.detail) {
            showSnackbar("snackbar", res.detail, 'rgb(255, 208, 208)', 'black');
        } else {
            selectedVehicle = { id: item.id, plate: item.plate || '' };
            const plateInput = document.getElementById('plateInput');
            if (plateInput) plateInput.value = item.plate || '';
            showSnackbar("snackbar", "Veicolo selezionato", 'rgb(208, 255, 208)', 'black');
        }
    });
}

// --- Create or select by value (plate page) ---
function createOrSelectAnagrafic(anagrafic, filterField, value) {
    const suggestionsMap = { vehicle: 'plateSuggestions' };
    const suggestionsList = document.getElementById(suggestionsMap[anagrafic]);
    if (suggestionsList) suggestionsList.innerHTML = '';

    fetch(`/api/data${currentWeigherPath}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data_in_execution: { [anagrafic]: { [filterField]: value.toUpperCase() } } })
    })
    .then(res => res.json())
    .then(res => {
        if (res.detail) {
            showSnackbar("snackbar", res.detail, 'rgb(255, 208, 208)', 'black');
        } else {
            showSnackbar("snackbar", `${getAnagraficLabel(anagrafic)} impostato`, 'rgb(208, 255, 208)', 'black');
        }
    });
}

function getCurrentId(anagrafic) {
    switch (anagrafic) {
        case 'vehicle': return selectedVehicle.id;
        case 'subject': return selectedSubject.id;
        case 'vector': return selectedVector.id;
        case 'driver': return selectedDriver.id;
        case 'material': return selectedMaterial.id;
        default: return null;
    }
}

function highlightText(text, input) {
    if (!input) return text;
    const regex = new RegExp(`^(${input})`, 'i');
    if (regex.test(text)) {
        return text.replace(regex, '<span class="highlight">$1</span>');
    }
    return text;
}

function getAnagraficLabel(anagrafic) {
    const labels = { vehicle: 'Veicolo', subject: 'Soggetto', vector: 'Vettore', driver: 'Autista', material: 'Materiale' };
    return labels[anagrafic] || anagrafic;
}

function updateInputIfNotFocused(inputId, value) {
    const input = document.getElementById(inputId);
    if (input && document.activeElement !== input) {
        input.value = value || '';
    }
}

// --- Generic Weighing ---
async function handleGenericWeighing() {
    if (data_weight_realtime.over_max_theshold) {
        confirmWeighing = executeGenericWeighing;
        document.getElementById('confirmDescription').innerHTML =
            `Soglia massima di <strong>${maxThesholdValue} kg</strong> superata, procedere con la pesatura?`;
        openPopup('confirmPopup');
    } else {
        await executeGenericWeighing();
    }
}

async function executeGenericWeighing() {
    closePopup();
    const buttons = document.querySelectorAll('.btn-weighing');
    buttons.forEach(b => { b.disabled = true; });

    const url = `${pathname}/api/command-weigher/print${currentWeigherPath}`;
    try {
        const r = await fetch(url).then(res => res.json());
        if (r && r.command_details && r.command_details.command_executed === true) {
            showSnackbar("snackbar", "Pesando...", 'rgb(208, 255, 208)', 'black');
            if (return_pdf_copy_after_weighing) access_id = r.access_id;
        } else {
            showSnackbar("snackbar", r?.command_details?.error_message || "Errore durante la pesatura", 'rgb(255, 208, 208)', 'black');
            buttons.forEach(b => { b.disabled = false; });
        }
    } catch (error) {
        console.error('Weighing error:', error);
        showSnackbar("snackbar", "Errore durante la pesatura", 'rgb(255, 208, 208)', 'black');
        buttons.forEach(b => { b.disabled = false; });
    }
}

function handleNeedToConfirm(plate) {
    confirmWeighing = confirmSemiAutomatic;
    document.getElementById('confirmDescription').innerHTML =
        `Lettura automatica della targa <strong>'${plate}'</strong>. <br> Effettuare la pesatura?`;
    openPopup('confirmPopup');
}

async function confirmSemiAutomatic() {
    const weight1 = selectedIdWeight !== null && selectedIdWeight["weight1"] !== null;
    const hasTare = /[1-9]/.test(String(data_weight_realtime.tare || '').replace("PT", ""));
    if (hasTare || weight1) {
        await outWeighing();
    } else {
        await inWeighing();
    }
}

async function inWeighing() {
    closePopup();
    document.querySelectorAll('.btn-weighing').forEach(b => b.disabled = true);
    try {
        const r = await fetch(`${pathname}/api/command-weigher/in${currentWeigherPath}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data_in_execution: dataInExecution })
        }).then(res => res.json());
        if (r && r.command_details && r.command_details.command_executed === true) {
            showSnackbar("snackbar", "Pesando...", 'rgb(208, 255, 208)', 'black');
            if (return_pdf_copy_after_weighing) access_id = r.access_id;
        } else {
            showSnackbar("snackbar", r?.command_details?.error_message || "Errore durante la pesatura", 'rgb(255, 208, 208)', 'black');
            document.querySelectorAll('.btn-weighing').forEach(b => b.disabled = false);
        }
    } catch (error) {
        console.error('Error in weighing:', error);
        document.querySelectorAll('.btn-weighing').forEach(b => b.disabled = false);
    }
}

async function outWeighing() {
    closePopup();
    document.querySelectorAll('.btn-weighing').forEach(b => b.disabled = true);
    try {
        const r = await fetch(`${pathname}/api/command-weigher/out${currentWeigherPath}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id_selected: selectedIdWeight["id"] })
        }).then(res => res.json());
        if (r && r.command_details && r.command_details.command_executed === true) {
            showSnackbar("snackbar", "Pesando...", 'rgb(208, 255, 208)', 'black');
            if (return_pdf_copy_after_weighing) access_id = r.access_id;
        } else {
            showSnackbar("snackbar", r?.command_details?.error_message || "Errore durante la pesatura", 'rgb(255, 208, 208)', 'black');
            document.querySelectorAll('.btn-weighing').forEach(b => b.disabled = false);
        }
    } catch (error) {
        console.error('Error out weighing:', error);
        document.querySelectorAll('.btn-weighing').forEach(b => b.disabled = false);
    }
}

// --- WebSocket ---
function connectWebSocket(path, exe) {
    let baseUrl = window.location.origin + pathname;
    baseUrl = baseUrl.replace(/^http/, (match) => match === 'http' ? 'ws' : 'wss');
    const websocketUrl = `${baseUrl}/${path}`;

    const preserve = autoReconnectInterval !== null;
    closeWebSocket(preserve);

    _data = new WebSocket(websocketUrl);

    _data.addEventListener('message', (e) => {
        try {
            const d = JSON.parse(e.data);
            if (d.type === 'pong') {
                if (pingTimeout) { clearTimeout(pingTimeout); pingTimeout = null; }
                return;
            }
        } catch (err) {}
        exe(e);
    });

    _data.addEventListener('open', () => {
        if (reconnectionAttemptTimeout) { clearTimeout(reconnectionAttemptTimeout); reconnectionAttemptTimeout = null; }
        if (autoReconnectInterval) { clearInterval(autoReconnectInterval); autoReconnectInterval = null; }
        isReconnecting = false;
        closePopup();
        startPing();
        getInstanceWeigher(currentWeigherPath);
        getData(currentWeigherPath);
    });

    _data.addEventListener('error', () => {
        if (!isRefreshing && !autoReconnectInterval) {
            closeWebSocket();
            showReconnectionPopup();
        }
    });

    _data.addEventListener('close', () => {
        if (!isRefreshing && !autoReconnectInterval) {
            showReconnectionPopup();
        }
    });
}

function showReconnectionPopup() {
    openPopup('reconnectionPopup');
    startAutoReconnect();
}

function startAutoReconnect() {
    if (autoReconnectInterval) clearInterval(autoReconnectInterval);
    if (reconnectionAttemptTimeout) clearTimeout(reconnectionAttemptTimeout);
    attemptReconnect();
    autoReconnectInterval = setInterval(() => {
        if (!_data || _data.readyState !== WebSocket.OPEN) {
            attemptReconnect();
        } else {
            clearInterval(autoReconnectInterval);
            autoReconnectInterval = null;
        }
    }, 3000);
}

function attemptReconnect() {
    isReconnecting = true;
    closeWebSocket(true);
    connectWebSocket(`api/command-weigher/realtime${currentWeigherPath}`, updateUIRealtime);
    reconnectionAttemptTimeout = setTimeout(() => {
        if (!_data || _data.readyState !== WebSocket.OPEN) isReconnecting = false;
    }, 3000);
}

function startPing() {
    if (pingInterval) clearInterval(pingInterval);
    if (pingTimeout) clearTimeout(pingTimeout);
    pingInterval = setInterval(() => {
        if (_data && _data.readyState === WebSocket.OPEN) {
            _data.send(JSON.stringify({ type: 'ping' }));
            pingTimeout = setTimeout(() => {
                if (_data) _data.close();
                if (!isRefreshing && !autoReconnectInterval) showReconnectionPopup();
            }, 5000);
        }
    }, 3000);
}

function closeWebSocket(preserveReconnectInterval = false) {
    if (pingInterval) { clearInterval(pingInterval); pingInterval = null; }
    if (pingTimeout) { clearTimeout(pingTimeout); pingTimeout = null; }
    if (reconnectionAttemptTimeout) { clearTimeout(reconnectionAttemptTimeout); reconnectionAttemptTimeout = null; }
    if (!preserveReconnectInterval && autoReconnectInterval) { clearInterval(autoReconnectInterval); autoReconnectInterval = null; }
    if (_data) { _data.close(); _data = null; }
}

// --- Fetch data ---
async function getInstanceWeigher(path) {
    try {
        const res = await fetch(`/api/config-weigher/instance/node${path}`).then(r => r.json());
        const obj = Object.values(res)[0];
        minWeightValue = obj.min_weight;
        maxThesholdValue = obj.max_theshold;
    } catch (error) {
        console.error('Error fetching weigher instance:', error);
    }
}

async function getData(path) {
    try {
        const res = await fetch(`/api/data${path}`).then(r => r.json());
        dataInExecution = res["data_in_execution"];
        selectedIdWeight = res["id_selected"];
        const obj = res["data_in_execution"];

        selectedVehicle = { id: obj.vehicle.id, plate: obj.vehicle.plate || '' };
        selectedTypeSubject = obj.typeSubject || 'CUSTOMER';
        selectedSubject = { id: obj.subject.id, social_reason: obj.subject.social_reason || '' };
        selectedVector = { id: obj.vector.id, social_reason: obj.vector.social_reason || '' };
        selectedDriver = { id: obj.driver?.id || null, social_reason: obj.driver?.social_reason || '' };
        selectedMaterial = { id: obj.material.id, description: obj.material.description || '' };

        if (typeof onDataReady === 'function') onDataReady();

        if (res.id_selected.need_to_confirm === true) {
            handleNeedToConfirm(obj.vehicle.plate);
        }
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

// --- Realtime updates ---
function parseMultipleJSON(str) {
    const results = [];
    let depth = 0;
    let start = -1;
    for (let i = 0; i < str.length; i++) {
        if (str[i] === '{') {
            if (depth === 0) start = i;
            depth++;
        } else if (str[i] === '}') {
            depth--;
            if (depth === 0 && start !== -1) {
                try { results.push(JSON.parse(str.substring(start, i + 1))); } catch (e) {}
                start = -1;
            }
        }
    }
    return results;
}

function updateUIRealtime(e) {
    const objects = parseMultipleJSON(e.data);
    objects.forEach(obj => processRealtimeObject(obj));
}

function processRealtimeObject(obj) {
    if (obj.command_in_executing) {
        if (obj.command_in_executing === "WEIGHING") {
            showSnackbar("snackbar", "Pesando...", 'rgb(208, 255, 208)', 'black');
            document.querySelectorAll('.btn-weighing').forEach(b => b.disabled = true);
        } else if (obj.command_in_executing === "TARE") {
            showSnackbar("snackbar", "Tara", 'rgb(208, 255, 208)', 'black');
        } else if (obj.command_in_executing === "ZERO") {
            showSnackbar("snackbar", "Zero", 'rgb(208, 255, 208)', 'black');
        }
    } else if (obj.weight_executed) {
        if (obj.weight_executed.gross_weight !== "") {
            closePopup();
            let message = "Pesata eseguita!";
            if (obj.weight_executed.pid !== "") {
                message += ` Pid: ${obj.weight_executed.pid}`;
                if (return_pdf_copy_after_weighing && obj.data_assigned) {
                    obj.data_assigned.accessId = JSON.parse(obj.data_assigned.accessId);
                    if (obj.data_assigned.accessId.in_out && obj.data_assigned.accessId.in_out.length > 0) {
                        const lastInOut = obj.data_assigned.accessId.in_out[obj.data_assigned.accessId.in_out.length - 1];
                        const id_in_out = lastInOut.id;
                        const isTestAccess = obj.data_assigned.accessId.type === "Test";
                        const typeOfWeight = isTestAccess ? "generic" : (lastInOut.idWeight2 === null ? "in" : "out");
                        const params = getParamsFromQueryString();
                        const inOutPdf = instances[params.instance_name]?.["nodes"]?.[params.weigher_name]?.["events"]?.["weighing"]?.["report"]?.[typeOfWeight];
                        if (inOutPdf) {
                            downloadPdf(id_in_out);
                        }
                    }
                }
            }
            showSnackbar("snackbar", message, 'rgb(208, 255, 208)', 'black');
        } else {
            showSnackbar("snackbar", "Pesata fallita", 'rgb(255, 208, 208)', 'black');
        }
        access_id = null;
        document.querySelectorAll('.btn-weighing').forEach(b => b.disabled = false);
    } else if (obj.tare) {
        data_weight_realtime = obj;
        const el = (id) => document.getElementById(id);
        if (el('tare')) el('tare').innerText = obj.tare !== undefined ? obj.tare : 'N/A';
        if (el('netWeight')) el('netWeight').innerText = obj.net_weight !== undefined ? obj.net_weight : 'N/A';
        if (el('uniteMisure')) el('uniteMisure').innerText = obj.unite_measure !== undefined ? obj.unite_measure : 'N/A';
        if (el('status')) el('status').innerText = obj.status !== undefined ? obj.status : 'N/A';
    } else if (obj.data_in_execution) {
        dataInExecution = obj.data_in_execution;
        selectedIdWeight = obj.id_selected;
        const d = obj.data_in_execution;

        selectedVehicle = { id: d.vehicle.id, plate: d.vehicle.plate || '' };
        if (d.typeSubject === 'Cliente') selectedTypeSubject = 'CUSTOMER';
        else if (d.typeSubject === 'Fornitore') selectedTypeSubject = 'SUPPLIER';
        else selectedTypeSubject = d.typeSubject || 'CUSTOMER';
        selectedSubject = { id: d.subject.id, social_reason: d.subject.social_reason || '' };
        selectedVector = { id: d.vector.id, social_reason: d.vector.social_reason || '' };
        selectedDriver = { id: d.driver?.id || null, social_reason: d.driver?.social_reason || '' };
        selectedMaterial = { id: d.material.id, description: d.material.description || '' };

        if (typeof onDataUpdate === 'function') onDataUpdate();

        if (obj.id_selected && obj.id_selected.need_to_confirm === true) {
            handleNeedToConfirm(d.vehicle.plate);
        }
    } else if (obj.message) {
        showSnackbar("snackbar", obj.message, 'rgb(208, 255, 208)', 'black');
    } else if (obj.error_message) {
        showSnackbar("snackbar", obj.error_message, 'rgb(255, 208, 208)', 'black');
    } else if (obj.cam_message) {
        showSnackbar("snackbar", obj.cam_message, 'white', 'black');
    }
}

// --- PDF ---
function downloadPdf(id_in_out) {
    fetch(`/api/anagrafic/access/in-out/pdf/${id_in_out}`)
    .then(res => {
        const disposition = res.headers.get('Content-Disposition');
        let filename = 'export.pdf';
        if (disposition && disposition.indexOf('filename=') !== -1) {
            filename = disposition.split('filename=')[1].replace(/["']/g, '').trim();
        }
        return res.blob().then(blob => ({ blob, filename }));
    })
    .then(({ blob, filename }) => {
        const link = document.createElement('a');
        link.href = window.URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });
}

function getParamsFromQueryString() {
    const params = new URLSearchParams(currentWeigherPath);
    return {
        instance_name: params.get('instance_name'),
        weigher_name: params.get('weigher_name')
    };
}

// --- Popup ---
function openPopup(name) {
    currentPopup = name;
    const popup = document.getElementById(name);
    if (!popup) return;
    const popupContent = popup.querySelector('.popup-content');
    popup.style.display = 'flex';
    setTimeout(() => popupContent.classList.add('show'), 10);
}

function closePopup() {
    if (currentPopup) {
        confirmWeighing = null;
        const popup = document.getElementById(currentPopup);
        if (!popup) return;
        const popupContent = popup.querySelector('.popup-content');
        popupContent.classList.remove('show');
        setTimeout(() => { popup.style.display = 'none'; }, 300);
        currentPopup = null;
    }
}
