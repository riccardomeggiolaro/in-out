// ===== TOTEM COMMON - Shared utilities for totem SPA =====

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
let _reservationHasMaterial = false;
let _reservationHasSubject = false;
let _reservationHasVector = false;
let _reservationHasDriver = false;
let weighers_data_type = "MANUALLY";
let weigherMode = "MANUALLY"; // weigher config mode: MANUALLY, SEMIAUTOMATIC, AUTOMATIC
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
let totemAnagrafiche = { vehicle: true, subject: false, vector: false, driver: false, material: true };
let defaultTypeSubject = "CUSTOMER";
let access_id = null;
let confirmWeighing = null;
let _weighingCompleting = false;
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
// let snackbarTimeout;

// SPA state
let _fromSummary = false;
let _dataLoaded = false;

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
        totemAnagrafiche = res["totem_anagrafiche"] || { card: true, vehicle: true, subject: false, vector: false, driver: false, material: true };
        defaultTypeSubject = res["default_type_subject"] || "CUSTOMER";
        weigherMode = res["mode"] || "MANUALLY";

        connectWebSocket(`api/command-weigher/realtime${currentWeigherPath}`, updateUIRealtime);

        // Show initial view — will be redirected by _resolveStartPage once data loads
        _waitingForStartPage = true;
        showView(totemAnagrafiche.card !== false ? 'card' : 'plate');
    });
}

// Determine the furthest page the user can go based on already-filled data
function _resolveStartPage() {
    if (!_waitingForStartPage) return;
    _waitingForStartPage = false;

    if (!selectedVehicle.plate) return;
    if (weigherMode === "AUTOMATIC") return; // backend handles it, stay on current view

    const dest = _findNextEnabledStep('plate');
    goTo(dest || 'summary');
}
let _waitingForStartPage = false;

// Find the next step with an empty field, starting after the given step
// Skips steps disabled in totem config or already set on the reservation
function _findNextEnabledStep(afterStep) {
    if (weigherMode === "AUTOMATIC") return null; // automatic: skip all anagrafic steps, go to summary
    const isSemiAutomatic = weigherMode === "SEMIAUTOMATIC";
    const steps = [
        { name: 'subject', enabled: totemAnagrafiche.subject && !(isSemiAutomatic && _reservationHasSubject) },
        { name: 'vector', enabled: totemAnagrafiche.vector && !(isSemiAutomatic && _reservationHasVector) },
        { name: 'driver', enabled: totemAnagrafiche.driver && !(isSemiAutomatic && _reservationHasDriver) },
        { name: 'material', enabled: totemAnagrafiche.material && !(isSemiAutomatic && _reservationHasMaterial) },
    ];
    let startIndex = 0;
    if (afterStep === 'plate') startIndex = 0;
    else if (afterStep === 'subject') startIndex = 1;
    else if (afterStep === 'vector') startIndex = 2;
    else if (afterStep === 'driver') startIndex = 3;
    else if (afterStep === 'material') return null;

    for (let i = startIndex; i < steps.length; i++) {
        if (steps[i].enabled) return steps[i].name;
    }
    return null;
}

// Find the previous enabled step before the given step
function _findPrevEnabledStep(beforeStep) {
    const isSemiAutomatic = weigherMode === "SEMIAUTOMATIC";
    const steps = [
        { name: 'card', enabled: totemAnagrafiche.card !== false },
        { name: 'plate', enabled: totemAnagrafiche.vehicle },
        { name: 'subject', enabled: totemAnagrafiche.subject && !(isSemiAutomatic && _reservationHasSubject) },
        { name: 'vector', enabled: totemAnagrafiche.vector && !(isSemiAutomatic && _reservationHasVector) },
        { name: 'driver', enabled: totemAnagrafiche.driver && !(isSemiAutomatic && _reservationHasDriver) },
        { name: 'material', enabled: totemAnagrafiche.material && !(isSemiAutomatic && _reservationHasMaterial) },
    ];
    const idx = steps.findIndex(s => s.name === beforeStep);
    const startIdx = idx === -1 ? steps.length - 1 : idx - 1;
    for (let i = startIdx; i >= 0; i--) {
        if (steps[i].enabled) return steps[i].name;
    }
    return 'plate';
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

// --- SPA Navigation ---
let _navigatingBack = false;

function isFromSummary() {
    return _fromSummary;
}

function goTo(page) {
    // Parse view name: 'plate', 'totem-plate.html', 'plate?from=summary'
    let viewName = page.replace(/^totem-/, '').replace(/\.html.*$/, '').split('?')[0];
    _fromSummary = page.includes('from=summary');
    _navigatingBack = page.includes('back=1');

    if (viewName === 'dashboard-totem') {
        window.location.href = 'dashboard-totem.html';
        return;
    }

    showView(viewName);
}

function showView(name) {
    const view = totemViews[name];
    if (!view) {
        console.error('Unknown view:', name);
        return;
    }

    // Track current view for language switching
    _currentViewName = name;

    // Clean up pagination state
    _paginationState = {};

    // Update title
    document.title = view.title || 'Totem';

    // Update view-specific styles
    document.getElementById('viewStyle').textContent = view.style || '';

    // Render content
    const step = document.querySelector('#pageContent .step');
    step.innerHTML = view.html();

    // Wrap content between h2 and step-buttons in step-content
    const h2 = step.querySelector('h2');
    const stepButtons = step.querySelector('.step-buttons');
    const middleElements = [];
    let sibling = h2 ? h2.nextElementSibling : step.firstElementChild;
    while (sibling && sibling !== stepButtons) {
        middleElements.push(sibling);
        sibling = sibling.nextElementSibling;
    }
    if (middleElements.length > 0) {
        const wrapper = document.createElement('div');
        wrapper.className = 'step-content';
        if (h2) {
            h2.after(wrapper);
        } else if (stepButtons) {
            step.insertBefore(wrapper, stepButtons);
        } else {
            step.appendChild(wrapper);
        }
        middleElements.forEach(el => wrapper.appendChild(el));
    }

    // Inject topbar with language switcher (right)
    const topbar = document.createElement('div');
    topbar.className = 'step-topbar';
    const flagIT = `<svg viewBox="0 0 120 120"><clipPath id="cIt"><circle cx="60" cy="60" r="60"/></clipPath><g clip-path="url(#cIt)"><rect x="0" y="0" width="40" height="120" fill="#009246"/><rect x="40" y="0" width="40" height="120" fill="#fff"/><rect x="80" y="0" width="40" height="120" fill="#ce2b37"/></g></svg>`;
    const flagEN = `<svg viewBox="0 0 120 120"><clipPath id="cEn"><circle cx="60" cy="60" r="60"/></clipPath><g clip-path="url(#cEn)"><rect width="120" height="120" fill="#012169"/><path d="M0,0 L120,120 M120,0 L0,120" stroke="#fff" stroke-width="20"/><path d="M0,0 L120,120 M120,0 L0,120" stroke="#C8102E" stroke-width="12"/><path d="M60,0 V120 M0,60 H120" stroke="#fff" stroke-width="28"/><path d="M60,0 V120 M0,60 H120" stroke="#C8102E" stroke-width="16"/></g></svg>`;
    topbar.innerHTML = `
        <div class="lang-switcher">
            <button class="lang-btn ${currentLang === 'it' ? 'active' : ''}" data-lang="it" onclick="switchLang('it')">${flagIT}</button>
            <button class="lang-btn ${currentLang === 'en' ? 'active' : ''}" data-lang="en" onclick="switchLang('en')">${flagEN}</button>
        </div>
    `;
    if (h2) topbar.insertBefore(h2, topbar.querySelector('.lang-switcher'));
    step.prepend(topbar);

    // Inject logo into center of step-buttons
    if (stepButtons) {
        const logoDiv = document.createElement('div');
        logoDiv.className = 'step-logo';
        logoDiv.innerHTML = `<img src="/static/content/baronpesi_logo.png" alt="Logo">`;
        const firstBtn = stepButtons.firstElementChild;
        if (firstBtn) {
            firstBtn.after(logoDiv);
        } else {
            logoDiv.style.gridColumn = '1 / -1';
            stepButtons.appendChild(logoDiv);
        }
    }

    // Re-trigger fade animation
    step.style.animation = 'none';
    void step.offsetWidth;
    step.style.animation = '';

    // Clear previous view callbacks
    window.onDataReady = null;
    window.onDataUpdate = null;

    // Initialize view (sets onDataReady/onDataUpdate)
    if (view.init) view.init();

    // If data already loaded, trigger onDataReady for the new view
    if (_dataLoaded && typeof onDataReady === 'function') {
        onDataReady();
    }
}

// --- Pagination state ---
let _paginationState = {};
const GRID_COLS = 2;

const ITEMS_PER_PAGE = 10;

function _calcItemsPerPage(containerId, items) {
    return ITEMS_PER_PAGE;
}

// Re-render on resize (items per page is fixed, but layout may need refresh)
let _resizeTimer;
window.addEventListener('resize', () => {
    clearTimeout(_resizeTimer);
    _resizeTimer = setTimeout(() => {
        Object.keys(_paginationState).forEach(containerId => {
            const state = _paginationState[containerId];
            if (!state || state.items.length === 0) return;
            _renderPage(containerId);
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

    // Fill remaining slots with empty placeholders
    const remaining = state.itemsPerPage - pageItems.length;
    for (let i = 0; i < remaining; i++) {
        const placeholder = document.createElement('li');
        placeholder.classList.add('placeholder');
        placeholder.innerHTML = '&nbsp;';
        container.appendChild(placeholder);
    }

    // Update "Altro"/"Avanti" button
    _updateNextPageButton(containerId);
}

function _updateNextPageButton(containerId) {
    const btn = document.getElementById('btnNextPage');
    if (!btn) return;
    const state = _paginationState[containerId];
    if (!state) return;

    const totalPages = Math.ceil(state.items.length / state.itemsPerPage);

    if (state.items.length === 0) {
        // No items — show "Next" to skip to next step
        btn.textContent = t('next');
        btn.style.display = '';
    } else if (totalPages > 1) {
        // Multiple pages — show "More" to paginate
        btn.textContent = t('more');
        btn.style.display = '';
    } else {
        // Single page with items — hide button, must click item
        btn.style.display = 'none';
    }
}

function _nextPage(containerId, skipToUrl) {
    const state = _paginationState[containerId];
    if (!state) return;

    // If no items, go to next step
    if (state.items.length === 0) {
        goTo(isFromSummary() ? 'summary' : skipToUrl);
        return;
    }

    // Paginate: go to next page, loop back to first
    const totalPages = Math.ceil(state.items.length / state.itemsPerPage);
    state.currentPage = (state.currentPage + 1) % totalPages;
    _renderPage(containerId);
}

// --- Load items into a list/grid ---
async function loadItems(anagrafic, filterField, inputValue, containerId, onItemClick, skipToUrl, backToUrl) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';

    const alphabeticalField = anagrafic === 'vehicle' ? 'plate'
                             : anagrafic === 'material' || anagrafic === 'operator' ? 'description'
                             : 'social_reason';
    let url = `/api/anagrafic/${anagrafic}/list?order_by=${alphabeticalField}&order_direction=asc`;
    if (inputValue) url += `&${filterField}=${inputValue}%`;

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

        // No items available
        if (items.length === 0 && skipToUrl && !inputValue) {
            if (_navigatingBack) {
                // Going back — skip to previous step automatically
                goTo(backToUrl ? backToUrl + '?back=1' : 'plate');
            } else {
                // Going forward — skip to next step automatically
                goTo(isFromSummary() ? 'summary' : skipToUrl);
            }
            return;
        }

        // "Create new" option only if searching (plate page)
        if (inputValue) {
            const li = document.createElement('li');
            li.classList.add('create-new');
            li.textContent = `${t('create_new')} "${inputValue.toUpperCase()}"`;
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

        _renderPage(containerId);

    } catch (error) {
        console.error('Error loading items:', error);
    }
}

// --- Full-page success/failure message after weighing ---
function showWeighingSuccess(isError = false, message = null) {
    const container = document.querySelector('#pageContent .step');
    if (!container) return;
    const color = isError ? '#d32f2f' : '#2e7d32';
    const icon = isError ? '&#10008;' : '&#10004;';
    const text = message || (isError ? t('weighing_error') : t('weighing_success'));
    const header = document.querySelector('.totem-header');
    if (header) header.style.display = 'none';
    container.innerHTML = `
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;text-align:center;padding:2rem;cursor:pointer;">
            <div style="font-size:5rem;color:${color};">${icon}</div>
            <h2 style="color:${color};font-size:2rem;margin-top:1rem;">${text}</h2>
        </div>
    `;

    let dismissed = false;
    const dismiss = () => {
        if (dismissed) return;
        dismissed = true;
        clearTimeout(timer);
        if (header) header.style.display = '';
        if (isError) {
            goTo('summary');
        } else {
            cancelTotem();
        }
    };

    const timer = setTimeout(dismiss, 3000);
    if (isError) {
        container.addEventListener('click', dismiss, { once: true });
    }
}

// --- Cancel / reset all data ---
function cancelTotem() {
    fetch(`/api/data${currentWeigherPath}`, {
        method: 'DELETE'
    })
    .then(res => res.json())
    .then(() => {
        selectedVehicle = { id: null, plate: '' };
        selectedTypeSubject = defaultTypeSubject;
        selectedSubject = { id: null, social_reason: '' };
        selectedVector = { id: null, social_reason: '' };
        selectedDriver = { id: null, social_reason: '' };
        selectedMaterial = { id: null, description: '' };
        selectedIdWeight = null;
        dataInExecution = null;
        goTo(totemAnagrafiche.card !== false ? 'card' : 'plate');
    })
    .catch(() => {
        goTo(totemAnagrafiche.card !== false ? 'card' : 'plate');
    });
}

// --- Select and advance (for grid selection pages) ---
function selectAndAdvance(anagrafic, item, nextPage) {
    const id = parseInt(item.id);

    fetch(`/api/data${currentWeigherPath}&keep_selected=true`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data_in_execution: { [anagrafic]: { id } } })
    })
    .then(res => res.json())
    .then(res => {
        if (res.detail) {
            // showSnackbar("snackbar", res.detail, 'rgb(255, 208, 208)', 'black');
        } else {
            // Update local state from response
            if (res.data_in_execution) {
                const d = res.data_in_execution;
                if (d.subject) selectedSubject = { id: d.subject.id, social_reason: d.subject.social_reason || '' };
                if (d.vector) selectedVector = { id: d.vector.id, social_reason: d.vector.social_reason || '' };
                if (d.driver) selectedDriver = { id: d.driver?.id || null, social_reason: d.driver?.social_reason || '' };
                if (d.material) selectedMaterial = { id: d.material.id, description: d.material.description || '' };
            }
            let dest;
            if (isFromSummary()) {
                dest = 'summary';
            } else {
                dest = _findNextEnabledStep(anagrafic) || 'summary';
            }
            setTimeout(() => goTo(dest), 300);
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
            // showSnackbar("snackbar", res.detail, 'rgb(255, 208, 208)', 'black');
        } else {
            selectedVehicle = { id: item.id, plate: item.plate || '' };
            const plateInput = document.getElementById('plateInput');
            if (plateInput) plateInput.value = item.plate || '';
            // showSnackbar("snackbar", "Veicolo selezionato", 'rgb(208, 255, 208)', 'black');
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
            // showSnackbar("snackbar", res.detail, 'rgb(255, 208, 208)', 'black');
        } else {
            // showSnackbar("snackbar", `${getAnagraficLabel(anagrafic)} impostato`, 'rgb(208, 255, 208)', 'black');
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
    const labels = { vehicle: t('label_vehicle'), subject: t('label_subject'), vector: t('label_vector'), driver: t('label_driver'), material: t('label_material') };
    return labels[anagrafic] || anagrafic;
}

function updateInputIfNotFocused(inputId, value) {
    const input = document.getElementById(inputId);
    if (input && document.activeElement !== input) {
        input.value = value || '';
    }
}

// --- Weighing ---
function _isSecondWeighing() {
    if (selectedIdWeight && selectedIdWeight.weight1 !== null) return true;
    if (dataInExecution && dataInExecution.vehicle && dataInExecution.vehicle.tare) return true;
    if (data_weight_realtime.tare && Number(data_weight_realtime.tare) !== 0) return true;
    return false;
}

async function handleWeighing() {
    if (data_weight_realtime.over_max_theshold) {
        confirmWeighing = executeWeighing;
        document.getElementById('confirmDescription').innerHTML =
            t('max_threshold_exceeded').replace('{value}', maxThesholdValue);
        openPopup('confirmPopup');
    } else {
        await executeWeighing();
    }
}

async function executeWeighing() {
    closePopup();
    const btns = document.querySelectorAll('.btn-weighing');
    btns.forEach(b => { b.disabled = true; });

    const isOut = _isSecondWeighing();
    const url = isOut
        ? `${pathname}/api/command-weigher/out${currentWeigherPath}`
        : `${pathname}/api/command-weigher/in${currentWeigherPath}`;
    const body = isOut
        ? JSON.stringify({ id_selected: selectedIdWeight["id"] })
        : JSON.stringify({ data_in_execution: dataInExecution });

    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body
        });
        if (!res.ok) {
            const data = await res.json().catch(() => null);
            const msg = (data && data.detail) || `${t('weighing_generic_error')} (${res.status})`;
            showWeighingSuccess(true, msg);
            btns.forEach(b => { b.disabled = false; });
            return;
        }
        const r = await res.json();
        if (r && r.command_details && r.command_details.command_executed === true) {
            _weighingCompleting = true;
            if (return_pdf_copy_after_weighing) access_id = r.access_id;
        } else {
            const msg = r?.command_details?.error_message || t('weighing_generic_error');
            showWeighingSuccess(true, msg);
            btns.forEach(b => { b.disabled = false; });
        }
    } catch (error) {
        console.error('Weighing error:', error);
        showWeighingSuccess(true, t('weighing_generic_error'));
        btns.forEach(b => { b.disabled = false; });
    }
}

function handleNeedToConfirm(plate) {
    confirmWeighing = confirmSemiAutomatic;
    document.getElementById('confirmDescription').innerHTML =
        t('auto_plate_confirm').replace('{plate}', plate);
    openPopup('confirmPopup');
}

async function confirmSemiAutomatic() {
    await executeWeighing();
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
            _weighingCompleting = true;
            if (return_pdf_copy_after_weighing) access_id = r.access_id;
        } else {
            // showSnackbar("snackbar", r?.command_details?.error_message || "Errore durante la pesatura", 'rgb(255, 208, 208)', 'black');
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
            _weighingCompleting = true;
            if (return_pdf_copy_after_weighing) access_id = r.access_id;
        } else {
            // showSnackbar("snackbar", r?.command_details?.error_message || "Errore durante la pesatura", 'rgb(255, 208, 208)', 'black');
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
        _reservationHasMaterial = res.reservation_has_material || false;
        _reservationHasSubject = res.reservation_has_subject || false;
        _reservationHasVector = res.reservation_has_vector || false;
        _reservationHasDriver = res.reservation_has_driver || false;
        weighers_data_type = res.type || "MANUALLY";
        const obj = res["data_in_execution"];

        selectedVehicle = { id: obj.vehicle.id, plate: obj.vehicle.plate || '' };
        selectedTypeSubject = obj.typeSubject || defaultTypeSubject;
        selectedSubject = { id: obj.subject.id, social_reason: obj.subject.social_reason || '' };
        selectedVector = { id: obj.vector.id, social_reason: obj.vector.social_reason || '' };
        selectedDriver = { id: obj.driver?.id || null, social_reason: obj.driver?.social_reason || '' };
        selectedMaterial = { id: obj.material.id, description: obj.material.description || '' };

        _dataLoaded = true;
        _resolveStartPage();
        if (typeof onDataReady === 'function') onDataReady();

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
        return;
    } else if (obj.weight_executed) {
        _weighingCompleting = false;
        if (obj.weight_executed.gross_weight !== "") {
            closePopup();
            showWeighingSuccess();
        } else {
            showWeighingSuccess(true);
        }
        access_id = null;
        document.querySelectorAll('.btn-weighing').forEach(b => b.disabled = false);
    } else if (obj.tare) {
        data_weight_realtime = obj;
        if (!_weighingCompleting) {
        const el = (id) => document.getElementById(id);
        if (el('tare')) el('tare').innerText = obj.tare !== undefined ? obj.tare : 'N/A';
        if (el('netWeight')) el('netWeight').innerText = obj.net_weight !== undefined ? obj.net_weight : 'N/A';
        if (el('uniteMisure')) el('uniteMisure').innerText = obj.unite_measure !== undefined ? obj.unite_measure : 'N/A';
        if (el('status')) el('status').innerText = obj.status !== undefined ? obj.status : 'N/A';
        }
        // Update weighing button text in real-time
        const btnWeighLabel = document.getElementById('btnWeighLabel');
        if (btnWeighLabel) btnWeighLabel.textContent = t('confirm_weigh');
    } else if (obj.data_in_execution) {
        const prevId = selectedIdWeight ? selectedIdWeight.id : null;
        _reservationHasMaterial = obj.reservation_has_material || false;
        _reservationHasSubject = obj.reservation_has_subject || false;
        _reservationHasVector = obj.reservation_has_vector || false;
        _reservationHasDriver = obj.reservation_has_driver || false;
        weighers_data_type = obj.type || "MANUALLY";
        dataInExecution = obj.data_in_execution;
        selectedIdWeight = obj.id_selected;
        const d = obj.data_in_execution;

        selectedVehicle = { id: d.vehicle.id, plate: d.vehicle.plate || '' };
        if (d.typeSubject === 'Cliente') selectedTypeSubject = 'CUSTOMER';
        else if (d.typeSubject === 'Fornitore') selectedTypeSubject = 'SUPPLIER';
        else selectedTypeSubject = d.typeSubject || defaultTypeSubject;
        selectedSubject = { id: d.subject.id, social_reason: d.subject.social_reason || '' };
        selectedVector = { id: d.vector.id, social_reason: d.vector.social_reason || '' };
        selectedDriver = { id: d.driver?.id || null, social_reason: d.driver?.social_reason || '' };
        selectedMaterial = { id: d.material.id, description: d.material.description || '' };

        // If access was deselected, go back to start (unless weighing is completing)
        if (prevId && (!obj.id_selected || obj.id_selected.id === null)) {
            if (!_weighingCompleting) {
                goTo(totemAnagrafiche.card !== false ? 'card' : 'plate');
            }
            return;
        }

        // If a new access was selected (from dashboard), navigate to first empty field or summary
        if (!prevId && obj.id_selected && obj.id_selected.id !== null) {
            if (weigherMode !== "AUTOMATIC") {
                const dest = _findNextEnabledStep('plate');
                goTo(dest || 'summary');
            }
            return;
        }

        if (!_weighingCompleting && typeof onDataUpdate === 'function') onDataUpdate();

    } else if (obj.message) {
        // showSnackbar("snackbar", obj.message, 'rgb(208, 255, 208)', 'black');
    } else if (obj.error_message) {
        // showSnackbar("snackbar", obj.error_message, 'rgb(255, 208, 208)', 'black');
    } else if (obj.cam_message) {
        // showSnackbar("snackbar", obj.cam_message, 'white', 'black');
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
