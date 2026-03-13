// ===== TOTEM WIZARD - dashboard-totem.js =====

// --- State ---
let currentStep = 0;
const TOTAL_STEPS = 7;

let currentWeigherPath = null;
let pathname = '/gateway';
let lastSlashIndex = window.location.pathname.lastIndexOf('/');
pathname = lastSlashIndex !== -1 ? pathname.substring(0, lastSlashIndex) : pathname;

// Selected data
let selectedVehicle = { id: null, plate: '' };
let selectedTypeSubject = 'CUSTOMER';
let selectedSubject = { id: null, social_reason: '' };
let selectedVector = { id: null, social_reason: '' };
let selectedDriver = { id: null, social_reason: '' };
let selectedMaterial = { id: null, description: '' };

// Weigher state
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

// Debounce timers
let plateDebounce;
let subjectDebounce;
let vectorDebounce;
let driverDebounce;
let materialDebounce;

// Weigher options cache
let weigherOptions = [];

// --- Init ---
window.addEventListener('load', () => {
    setTimeout(() => {
        document.querySelector('.loading').style.display = 'none';
        document.getElementById('weigherSelection').style.display = 'flex';
    }, 300);
});

document.addEventListener('DOMContentLoaded', () => {
    fetch('/api/config-weigher/configuration')
    .then(res => res.json())
    .then(res => {
        return_pdf_copy_after_weighing = res["return_pdf_copy_after_weighing"];
        test_mode = res["test_mode"] || false;
        instances = res["weighers"];

        // Build weigher options list
        weigherOptions = [];
        for (let instance in res["weighers"]) {
            for (let weigher in res["weighers"][instance]["nodes"]) {
                weigherOptions.push({
                    path: `?instance_name=${instance}&weigher_name=${weigher}`,
                    label: weigher
                });
            }
        }

        // Render weigher selection buttons
        const weigherList = document.getElementById('weigherList');
        weigherList.innerHTML = '';
        weigherOptions.forEach(opt => {
            const btn = document.createElement('button');
            btn.className = 'weigher-option';
            btn.textContent = opt.label;
            btn.addEventListener('click', () => selectWeigher(opt.path));
            weigherList.appendChild(btn);
        });
    });

    // Setup input listeners with debounce
    setupInputListener('plateInput', 'plateSuggestions', 'vehicle', 'plate');
    setupInputListener('subjectInput', 'subjectSuggestions', 'subject', 'social_reason');
    setupInputListener('vectorInput', 'vectorSuggestions', 'vector', 'social_reason');
    setupInputListener('driverInput', 'driverSuggestions', 'driver', 'social_reason');
    setupInputListener('materialInput', 'materialSuggestions', 'material', 'description');
});

function selectWeigher(path) {
    currentWeigherPath = path;
    localStorage.setItem('currentWeigherPath', currentWeigherPath);

    // Hide selection, show totem
    document.getElementById('weigherSelection').style.display = 'none';
    document.querySelector('.totem-container').style.display = 'flex';

    // Connect WebSocket
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

// --- Step Navigation ---
function goToStep(step) {
    if (step < 0 || step >= TOTAL_STEPS) return;

    // Hide current step
    const currentEl = document.getElementById(`step-${currentStep}`);
    if (currentEl) currentEl.classList.remove('active');

    // Update progress bar
    document.querySelectorAll('.progress-step').forEach((el, i) => {
        el.classList.remove('active');
        if (i < step) el.classList.add('completed');
        else el.classList.remove('completed');
    });
    document.querySelector(`.progress-step[data-step="${step}"]`).classList.add('active');

    // Show new step
    currentStep = step;
    const newEl = document.getElementById(`step-${step}`);
    if (newEl) newEl.classList.add('active');

    // Focus on input if step has one
    const inputs = { 0: 'plateInput', 2: 'subjectInput', 3: 'vectorInput', 4: 'driverInput', 5: 'materialInput' };
    if (inputs[step]) {
        setTimeout(() => document.getElementById(inputs[step]).focus(), 100);
    }

    // Update summary on step 6
    if (step === 6) updateSummary();

    // Load suggestions for the new step
    if (step === 0) loadSuggestions('vehicle', 'plate', '', 'plateSuggestions');
    if (step === 2) loadSuggestions('subject', 'social_reason', '', 'subjectSuggestions');
    if (step === 3) loadSuggestions('vector', 'social_reason', '', 'vectorSuggestions');
    if (step === 4) loadSuggestions('driver', 'social_reason', '', 'driverSuggestions');
    if (step === 5) loadSuggestions('material', 'description', '', 'materialSuggestions');
}

// --- Type Subject ---
function selectTypeSubject(type) {
    selectedTypeSubject = type;

    document.getElementById('btnCustomer').classList.toggle('active', type === 'CUSTOMER');
    document.getElementById('btnSupplier').classList.toggle('active', type === 'SUPPLIER');

    // Send to API
    fetch(`/api/data${currentWeigherPath}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data_in_execution: { typeSubject: type } })
    })
    .then(res => res.json())
    .then(res => {
        if (res.detail) showSnackbar("snackbar", res.detail, 'rgb(255, 208, 208)', 'black');
    });
}

// --- Input listeners ---
function setupInputListener(inputId, suggestionsId, anagrafic, filterField) {
    const input = document.getElementById(inputId);
    if (!input) return;

    input.addEventListener('input', () => {
        const value = input.value.trim();
        clearTimeout(window[`${anagrafic}Debounce`]);
        window[`${anagrafic}Debounce`] = setTimeout(() => {
            loadSuggestions(anagrafic, filterField, value, suggestionsId);
        }, 250);
    });

    // On Enter, create new if no match
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const value = input.value.trim();
            if (value) {
                createOrSelectAnagrafic(anagrafic, filterField, value);
            }
        }
    });

    // On blur, auto-select matching suggestion or create/set value
    input.addEventListener('blur', () => {
        setTimeout(() => {
            const suggestionsList = document.getElementById(suggestionsId);
            if (!suggestionsList) return;
            const value = input.value.trim();
            if (value) {
                const items = suggestionsList.querySelectorAll('li:not(.create-new)');
                for (const li of items) {
                    const text = li.querySelector('span')?.textContent?.trim().toUpperCase();
                    if (text === value.toUpperCase()) {
                        li.click();
                        return;
                    }
                }
                // No exact match found, set the value via API
                createOrSelectAnagrafic(anagrafic, filterField, value);
            }
            suggestionsList.innerHTML = '';
        }, 200);
    });
}

// --- Load Suggestions ---
async function loadSuggestions(anagrafic, filterField, inputValue, suggestionsListId) {
    const suggestionsList = document.getElementById(suggestionsListId);
    if (!suggestionsList) return;
    suggestionsList.innerHTML = '';

    let url = `/api/anagrafic/${anagrafic}/list?`;
    if (inputValue) url += `${filterField}=${inputValue}%`;

    try {
        const response = await fetch(url);
        const data = await response.json();

        const currentId = getCurrentId(anagrafic);

        data.data.forEach(item => {
            const displayField = filterField === 'plate' ? item.plate :
                                 filterField === 'description' ? item.description :
                                 item.social_reason;
            if (!displayField) return;

            const li = document.createElement('li');
            li.dataset.id = item.id;

            // Main text with highlight
            const mainText = highlightText(displayField, inputValue);
            let secondaryText = '';

            if (anagrafic === 'vehicle' && item.description) {
                secondaryText = item.description;
            } else if (anagrafic === 'subject' && item.cfpiva) {
                secondaryText = item.cfpiva;
            } else if (anagrafic === 'vector' && item.cfpiva) {
                secondaryText = item.cfpiva;
            } else if (anagrafic === 'driver' && item.telephone) {
                secondaryText = item.telephone;
            }

            li.innerHTML = `<span>${mainText}</span>${secondaryText ? `<span class="secondary">${secondaryText}</span>` : ''}`;

            if (item.id === currentId) {
                li.classList.add('selected');
            }

            li.addEventListener('click', () => selectItem(anagrafic, item, filterField));
            suggestionsList.appendChild(li);
        });

        // Add "create new" option if input has value
        if (inputValue) {
            const li = document.createElement('li');
            li.classList.add('create-new');
            li.textContent = `Crea "${inputValue.toUpperCase()}"`;
            li.addEventListener('click', () => createOrSelectAnagrafic(anagrafic, filterField, inputValue));
            suggestionsList.appendChild(li);
        }

    } catch (error) {
        console.error('Error loading suggestions:', error);
    }
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

// --- Select an item from suggestions ---
function selectItem(anagrafic, item, filterField) {
    const id = parseInt(item.id);

    // Hide suggestions immediately on selection
    const suggestionsMap = { vehicle: 'plateSuggestions', subject: 'subjectSuggestions', vector: 'vectorSuggestions', driver: 'driverSuggestions', material: 'materialSuggestions' };
    const suggestionsList = document.getElementById(suggestionsMap[anagrafic]);
    if (suggestionsList) suggestionsList.innerHTML = '';

    fetch(`/api/data${currentWeigherPath}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            data_in_execution: {
                [anagrafic]: { id }
            }
        })
    })
    .then(res => res.json())
    .then(res => {
        if (res.detail) {
            showSnackbar("snackbar", res.detail, 'rgb(255, 208, 208)', 'black');
        } else {
            updateSelectedFromItem(anagrafic, item, filterField);
            showSnackbar("snackbar", `${getAnagraficLabel(anagrafic)} selezionato`, 'rgb(208, 255, 208)', 'black');
        }
    });
}

function updateSelectedFromItem(anagrafic, item, filterField) {
    switch (anagrafic) {
        case 'vehicle':
            selectedVehicle = { id: item.id, plate: item.plate || '' };
            document.getElementById('plateInput').value = item.plate || '';
            break;
        case 'subject':
            selectedSubject = { id: item.id, social_reason: item.social_reason || '' };
            document.getElementById('subjectInput').value = item.social_reason || '';
            updateSelectedDisplay('selectedSubject', item.social_reason);
            break;
        case 'vector':
            selectedVector = { id: item.id, social_reason: item.social_reason || '' };
            document.getElementById('vectorInput').value = item.social_reason || '';
            updateSelectedDisplay('selectedVector', item.social_reason);
            break;
        case 'driver':
            selectedDriver = { id: item.id, social_reason: item.social_reason || '' };
            document.getElementById('driverInput').value = item.social_reason || '';
            updateSelectedDisplay('selectedDriver', item.social_reason);
            break;
        case 'material':
            selectedMaterial = { id: item.id, description: item.description || '' };
            document.getElementById('materialInput').value = item.description || '';
            updateSelectedDisplay('selectedMaterial', item.description);
            break;
    }
}

function updateSelectedDisplay(elementId, value) {
    const el = document.getElementById(elementId);
    if (el) el.textContent = value || '';
}

function getAnagraficLabel(anagrafic) {
    const labels = { vehicle: 'Veicolo', subject: 'Soggetto', vector: 'Vettore', driver: 'Autista', material: 'Materiale' };
    return labels[anagrafic] || anagrafic;
}

// --- Create or select by value ---
function createOrSelectAnagrafic(anagrafic, filterField, value) {
    // Hide suggestions immediately
    const suggestionsMap = { vehicle: 'plateSuggestions', subject: 'subjectSuggestions', vector: 'vectorSuggestions', driver: 'driverSuggestions', material: 'materialSuggestions' };
    const suggestionsList = document.getElementById(suggestionsMap[anagrafic]);
    if (suggestionsList) suggestionsList.innerHTML = '';

    const body = {
        data_in_execution: {
            [anagrafic]: {
                [filterField]: value.toUpperCase()
            }
        }
    };

    fetch(`/api/data${currentWeigherPath}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
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

// --- Summary ---
function updateSummary() {
    document.getElementById('summaryPlate').textContent = selectedVehicle.plate || '-';
    document.getElementById('summaryType').textContent = selectedTypeSubject === 'CUSTOMER' ? 'Cliente' : 'Fornitore';
    document.getElementById('summarySubject').textContent = selectedSubject.social_reason || '-';
    document.getElementById('summaryVector').textContent = selectedVector.social_reason || '-';
    document.getElementById('summaryDriver').textContent = selectedDriver.social_reason || '-';
    document.getElementById('summaryMaterial').textContent = selectedMaterial.description || '-';
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

        // Sync local state from server
        selectedVehicle = { id: obj.vehicle.id, plate: obj.vehicle.plate || '' };
        selectedTypeSubject = obj.typeSubject || 'CUSTOMER';
        selectedSubject = { id: obj.subject.id, social_reason: obj.subject.social_reason || '' };
        selectedVector = { id: obj.vector.id, social_reason: obj.vector.social_reason || '' };
        selectedDriver = { id: obj.driver?.id || null, social_reason: obj.driver?.social_reason || '' };
        selectedMaterial = { id: obj.material.id, description: obj.material.description || '' };

        // Update UI
        if (selectedVehicle.plate) document.getElementById('plateInput').value = selectedVehicle.plate;
        document.getElementById('btnCustomer').classList.toggle('active', selectedTypeSubject === 'CUSTOMER');
        document.getElementById('btnSupplier').classList.toggle('active', selectedTypeSubject === 'SUPPLIER');
        if (selectedSubject.social_reason) {
            document.getElementById('subjectInput').value = selectedSubject.social_reason;
            updateSelectedDisplay('selectedSubject', selectedSubject.social_reason);
        }
        if (selectedVector.social_reason) {
            document.getElementById('vectorInput').value = selectedVector.social_reason;
            updateSelectedDisplay('selectedVector', selectedVector.social_reason);
        }
        if (selectedDriver.social_reason) {
            document.getElementById('driverInput').value = selectedDriver.social_reason;
            updateSelectedDisplay('selectedDriver', selectedDriver.social_reason);
        }
        if (selectedMaterial.description) {
            document.getElementById('materialInput').value = selectedMaterial.description;
            updateSelectedDisplay('selectedMaterial', selectedMaterial.description);
        }

        // Handle need_to_confirm
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
        document.getElementById('tare').innerText = obj.tare !== undefined ? obj.tare : 'N/A';
        document.getElementById('netWeight').innerText = obj.net_weight !== undefined ? obj.net_weight : 'N/A';
        document.getElementById('uniteMisure').innerText = obj.unite_measure !== undefined ? obj.unite_measure : 'N/A';
        document.getElementById('status').innerText = obj.status !== undefined ? obj.status : 'N/A';
    } else if (obj.data_in_execution) {
        dataInExecution = obj.data_in_execution;
        selectedIdWeight = obj.id_selected;
        const d = obj.data_in_execution;

        // Sync state
        selectedVehicle = { id: d.vehicle.id, plate: d.vehicle.plate || '' };
        if (d.typeSubject === 'Cliente') selectedTypeSubject = 'CUSTOMER';
        else if (d.typeSubject === 'Fornitore') selectedTypeSubject = 'SUPPLIER';
        else selectedTypeSubject = d.typeSubject || 'CUSTOMER';
        selectedSubject = { id: d.subject.id, social_reason: d.subject.social_reason || '' };
        selectedVector = { id: d.vector.id, social_reason: d.vector.social_reason || '' };
        selectedDriver = { id: d.driver?.id || null, social_reason: d.driver?.social_reason || '' };
        selectedMaterial = { id: d.material.id, description: d.material.description || '' };

        // Update inputs only if not focused
        updateInputIfNotFocused('plateInput', selectedVehicle.plate);
        document.getElementById('btnCustomer').classList.toggle('active', selectedTypeSubject === 'CUSTOMER');
        document.getElementById('btnSupplier').classList.toggle('active', selectedTypeSubject === 'SUPPLIER');
        updateInputIfNotFocused('subjectInput', selectedSubject.social_reason);
        updateSelectedDisplay('selectedSubject', selectedSubject.social_reason);
        updateInputIfNotFocused('vectorInput', selectedVector.social_reason);
        updateSelectedDisplay('selectedVector', selectedVector.social_reason);
        updateInputIfNotFocused('driverInput', selectedDriver.social_reason);
        updateSelectedDisplay('selectedDriver', selectedDriver.social_reason);
        updateInputIfNotFocused('materialInput', selectedMaterial.description);
        updateSelectedDisplay('selectedMaterial', selectedMaterial.description);

        // Update summary if visible
        if (currentStep === 6) updateSummary();

        // Handle need_to_confirm
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

function updateInputIfNotFocused(inputId, value) {
    const input = document.getElementById(inputId);
    if (input && document.activeElement !== input) {
        input.value = value || '';
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

// --- Snackbar (reuse existing) ---
function showSnackbarDashboard(message) {
    const snackbar = document.getElementById("snackbar-dashboard");
    snackbar.textContent = message;
    snackbar.className = "show";
    if (snackbarTimeout) clearTimeout(snackbarTimeout);
    snackbarTimeout = setTimeout(() => {
        if (snackbar.className === "show") snackbar.className = snackbar.className.replace("show", "");
    }, 5000);
}
