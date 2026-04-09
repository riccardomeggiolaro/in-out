// ===== TOTEM VIEWS - SPA view definitions =====

const totemViews = {

    // ==================== CARD ====================
    card: {
        get title() { return 'Totem - ' + t('card_title'); },
        style: `
            .card-hint { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; min-height: 0; gap: clamp(8px, 2vh, 20px); color: #FFFFFF; }
            .card-icon { width: clamp(100px, 24vh, 200px); height: clamp(100px, 24vh, 200px); }
            .card-label { font-size: clamp(1.4rem, 5.5vh, 3rem); font-weight: 600; letter-spacing: 2px; text-transform: uppercase; text-align: center; }
            .card-net { font-size: clamp(1.2rem, 4vh, 2.5rem); font-weight: 700; color: #FFFF00; letter-spacing: 1px; text-align: center; margin-top: 8px; }
        `,
        html: () => `
            <div class="card-hint">
                <svg class="card-icon" viewBox="0 0 120 100" xmlns="http://www.w3.org/2000/svg" fill="currentColor">
                    <!-- Reader base -->
                    <rect x="10" y="70" width="100" height="22" rx="6" ry="6" fill="currentColor" opacity="0.5"/>
                    <rect x="20" y="75" width="80" height="8" rx="3" ry="3" fill="currentColor" opacity="0.3"/>
                    <circle cx="90" cy="79" r="4" fill="currentColor" opacity="0.9"/>
                    <!-- Card resting on reader (slightly tilted) -->
                    <g transform="rotate(-8, 60, 50)">
                        <rect x="18" y="20" width="74" height="48" rx="5" ry="5" fill="none" stroke="currentColor" stroke-width="4"/>
                        <rect x="24" y="28" width="18" height="26" rx="2" ry="2" fill="currentColor" opacity="0.7"/>
                        <line x1="50" y1="32" x2="82" y2="32" stroke="currentColor" stroke-width="3" stroke-linecap="round" opacity="0.6"/>
                        <line x1="50" y1="42" x2="82" y2="42" stroke="currentColor" stroke-width="3" stroke-linecap="round" opacity="0.4"/>
                        <line x1="50" y1="52" x2="72" y2="52" stroke="currentColor" stroke-width="3" stroke-linecap="round" opacity="0.4"/>
                    </g>
                </svg>
                <span class="card-label">${t('card_instruction')}</span>
                <span class="card-net" id="cardNetWeight"></span>
            </div>
            <div class="step-buttons"></div>
        `,
        init: () => {
            window.onDataReady = function() {
                if (selectedVehicle.plate) {
                    goTo('plate');
                }
            };
            window.onDataUpdate = function() {
                if (selectedVehicle.plate) {
                    goTo('plate');
                }
            };
        }
    },

    // ==================== PLATE ====================
    plate: {
        get title() { return 'Totem - ' + t('plate_title'); },
        style: `
            .step-content { justify-content: center; }
            .step-content.keyboard-active { justify-content: flex-start; }
            .license-plate { cursor: pointer; }
            .plate-empty .plate-text { color: #AAAAAA; letter-spacing: 12px; }
            .plate-input { display: none; font-size: 3.5rem; font-weight: 700; font-family: 'Courier New', monospace; letter-spacing: 8px; text-align: center; text-transform: uppercase; border: none; outline: none; background: transparent; width: 100%; height: 100%; padding: 0 8px; box-sizing: border-box; }
            .plate-input.active { display: flex; }
            .virtual-keyboard { display: none; width: 100%; flex: 1; min-height: 0; padding: 4px 16px; box-sizing: border-box; flex-direction: column; gap: 4px; }
            .virtual-keyboard.active { display: flex; }
            .vk-row { display: flex; gap: 4px; flex: 1; justify-content: center; }
            .vk-key { flex: 1; max-width: 10%; background: #FFFFFF; color: #111111; border: 2px solid #CCCCCC; border-radius: clamp(4px, 1vw, 8px); font-size: clamp(0.8rem, 4vh, 2.5rem); font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; font-family: inherit; transition: background 0.1s; user-select: none; -webkit-user-select: none; }
            .vk-key:active { background: #E0E0E0; }
            .vk-key.vk-wide { max-width: 15%; flex: 1.5; }
            .vk-key.vk-backspace { max-width: 15%; flex: 1.5; font-size: clamp(0.7rem, 3vh, 2rem); }
            .rfid-hint { display: none; }
        `,
        html: () => `
            <h2>${t('plate_title')}</h2>
            <div class="plate-container">
                <div class="license-plate plate-empty" id="plateDisplay">
                    <div class="plate-band plate-band-left">
                        <div class="plate-stars">&#9733;</div>
                    </div>
                    <span class="plate-text" id="plateText">&#8226;&#8226;&#8226;&#8226;&#8226;&#8226;&#8226;</span>
                    <input class="plate-input" id="manualPlateInput" type="text" maxlength="10" placeholder="AB123CD" autocomplete="off" inputmode="none" enterkeyhint="done" readonly>
                    <div class="plate-band plate-band-right"></div>
                </div>
            </div>

            <div class="virtual-keyboard" id="virtualKeyboard">
                <div class="vk-row">
                    <button class="vk-key" data-key="1">1</button>
                    <button class="vk-key" data-key="2">2</button>
                    <button class="vk-key" data-key="3">3</button>
                    <button class="vk-key" data-key="4">4</button>
                    <button class="vk-key" data-key="5">5</button>
                    <button class="vk-key" data-key="6">6</button>
                    <button class="vk-key" data-key="7">7</button>
                    <button class="vk-key" data-key="8">8</button>
                    <button class="vk-key" data-key="9">9</button>
                    <button class="vk-key" data-key="0">0</button>
                </div>
                <div class="vk-row">
                    <button class="vk-key" data-key="Q">Q</button>
                    <button class="vk-key" data-key="W">W</button>
                    <button class="vk-key" data-key="E">E</button>
                    <button class="vk-key" data-key="R">R</button>
                    <button class="vk-key" data-key="T">T</button>
                    <button class="vk-key" data-key="Y">Y</button>
                    <button class="vk-key" data-key="U">U</button>
                    <button class="vk-key" data-key="I">I</button>
                    <button class="vk-key" data-key="O">O</button>
                    <button class="vk-key" data-key="P">P</button>
                </div>
                <div class="vk-row">
                    <button class="vk-key" data-key="A">A</button>
                    <button class="vk-key" data-key="S">S</button>
                    <button class="vk-key" data-key="D">D</button>
                    <button class="vk-key" data-key="F">F</button>
                    <button class="vk-key" data-key="G">G</button>
                    <button class="vk-key" data-key="H">H</button>
                    <button class="vk-key" data-key="J">J</button>
                    <button class="vk-key" data-key="K">K</button>
                    <button class="vk-key" data-key="L">L</button>
                </div>
                <div class="vk-row">
                    <button class="vk-key" data-key="Z">Z</button>
                    <button class="vk-key" data-key="X">X</button>
                    <button class="vk-key" data-key="C">C</button>
                    <button class="vk-key" data-key="V">V</button>
                    <button class="vk-key" data-key="B">B</button>
                    <button class="vk-key" data-key="N">N</button>
                    <button class="vk-key" data-key="M">M</button>
                    <button class="vk-key vk-backspace" data-key="BACKSPACE">&#9003;</button>
                </div>
            </div>
            <div class="step-buttons">
                <button class="btn btn-secondary" id="btnCancelPlate" style="visibility:hidden" onclick="cancelTotem()">${t('cancel')}</button>
                <button class="btn btn-primary btn-next" id="btnNext" style="visibility:hidden" onclick="_plateGoToNext()">${t('next')}</button>
            </div>
        `,
        init: () => {
            window._plateManualMode = false;

            window._plateFitText = function(el) {
                if (!el || !el.parentElement) return;
                const parent = el.parentElement;
                const bands = parent.querySelectorAll('.plate-band');
                const bandsWidth = Array.from(bands).reduce((sum, b) => sum + b.offsetWidth, 0);
                const availW = parent.offsetWidth - bandsWidth;
                const availH = parent.offsetHeight;
                if (availW <= 0 || availH <= 0) return;

                // Get text length for width calculation
                // Input always sizes for max 10 chars so it doesn't jump around
                const isInput = el.value !== undefined;
                const charCount = isInput ? 10 : (el.textContent || 'XXXXXXX').length || 7;

                // Font height = available height * 0.8 (margin)
                const fontByHeight = availH * 0.8;
                // Font width = available width / chars * factor (monospace ~0.6 ratio)
                const fontByWidth = (availW / (charCount * 0.65));
                // Use the smaller of the two
                const fontSize = Math.max(12, Math.min(fontByHeight, fontByWidth));

                el.style.fontSize = fontSize + 'px';
                el.style.transform = '';
            };

            window._plateResizeObserver = new ResizeObserver(() => {
                const plateText = document.getElementById('plateText');
                const plateInput = document.getElementById('manualPlateInput');
                if (plateText && plateText.style.display !== 'none') _plateFitText(plateText);
                if (plateInput && plateInput.style.display !== 'none') _plateFitText(plateInput);
            });
            const plateDisplay = document.getElementById('plateDisplay');
            if (plateDisplay) window._plateResizeObserver.observe(plateDisplay);

            window._plateShowPlate = function(plate) {
                document.getElementById('plateDisplay').classList.remove('plate-empty');
                const plateText = document.getElementById('plateText');
                plateText.textContent = plate;
                plateText.style.display = '';
                document.getElementById('manualPlateInput').style.display = 'none';
                _plateFitText(plateText);
            };

            window._plateShowEmpty = function() {
                document.getElementById('plateDisplay').classList.add('plate-empty');
                const plateText = document.getElementById('plateText');
                plateText.innerHTML = '&#8226;&#8226;&#8226;&#8226;&#8226;&#8226;&#8226;';
                plateText.style.display = '';
                document.getElementById('manualPlateInput').style.display = 'none';
                _plateFitText(plateText);
            };

            window._plateGoToNext = function() {
                if (isFromSummary()) { goTo('summary'); return; }
                const dest = _findNextEnabledStep('plate');
                goTo(dest || 'summary');
            };

            window._manualPlateValue = '';

            window._plateUpdateDisplay = function() {
                const plateText = document.getElementById('plateText');
                if (_manualPlateValue) {
                    plateText.textContent = _manualPlateValue;
                    document.getElementById('plateDisplay').classList.remove('plate-empty');
                } else {
                    plateText.innerHTML = '&#8226;&#8226;&#8226;&#8226;&#8226;&#8226;&#8226;';
                    document.getElementById('plateDisplay').classList.add('plate-empty');
                }
                plateText.style.display = '';
                _plateFitText(plateText);
            };

            window._plateEnterManual = function() {
                _plateManualMode = true;
                _manualPlateValue = '';
                _plateUpdateDisplay();
                document.getElementById('virtualKeyboard').classList.add('active');
                const sc = document.querySelector('.step-content');
                if (sc) sc.classList.add('keyboard-active');
                const btnCancel = document.getElementById('btnCancelPlate');
                const btnNext = document.getElementById('btnNext');
                btnCancel.textContent = t('undo');
                btnCancel.onclick = _plateExitManual;
                btnCancel.style.visibility = '';
                btnNext.textContent = t('confirm');
                btnNext.onclick = _plateConfirmManual;
                btnNext.style.visibility = '';
            };

            function _plateRestoreButtons() {
                const btnCancel = document.getElementById('btnCancelPlate');
                const btnNext = document.getElementById('btnNext');
                btnCancel.textContent = t('cancel');
                btnCancel.onclick = cancelTotem;
                btnNext.textContent = t('next');
                btnNext.onclick = _plateGoToNext;
            }

            window._plateExitManual = function() {
                _plateManualMode = false;
                document.getElementById('virtualKeyboard').classList.remove('active');
                const sc = document.querySelector('.step-content');
                if (sc) sc.classList.remove('keyboard-active');
                _plateRestoreButtons();
                if (selectedVehicle.plate) {
                    document.getElementById('btnCancelPlate').style.visibility = '';
                    document.getElementById('btnNext').style.visibility = '';
                    _plateShowPlate(selectedVehicle.plate);
                } else {
                    document.getElementById('btnCancelPlate').style.visibility = 'hidden';
                    document.getElementById('btnNext').style.visibility = 'hidden';
                    _plateShowEmpty();
                }
            };

            // Virtual keyboard handler
            document.getElementById('virtualKeyboard').addEventListener('click', (e) => {
                const key = e.target.closest('.vk-key');
                if (!key) return;
                const val = key.dataset.key;
                if (val === 'BACKSPACE') {
                    _manualPlateValue = _manualPlateValue.slice(0, -1);
                } else if (_manualPlateValue.length < 10) {
                    _manualPlateValue += val;
                }
                _plateUpdateDisplay();
            });

            window._plateConfirmManual = function() {
                const value = _manualPlateValue.trim().toUpperCase();
                if (!value) return;

                // Deselect current access first, then set new plate with auto_select
                const hasAccess = selectedIdWeight && selectedIdWeight.id;
                const doSetPlate = () => {
                    fetch(`/api/data${currentWeigherPath}&auto_select=true`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ data_in_execution: { vehicle: { plate: value } } })
                    })
                    .then(res => res.json())
                    .then(res => {
                        if (res.detail) {
                            // error
                        } else {
                            // Update state from PATCH response
                            if (res.id_selected) selectedIdWeight = res.id_selected;
                            if (res.data_in_execution) {
                                dataInExecution = res.data_in_execution;
                                const d = res.data_in_execution;
                                selectedVehicle = { id: d.vehicle.id, plate: d.vehicle.plate || '' };
                                if (d.typeSubject) selectedTypeSubject = d.typeSubject;
                                selectedSubject = { id: d.subject.id, social_reason: d.subject.social_reason || '' };
                                selectedVector = { id: d.vector.id, social_reason: d.vector.social_reason || '' };
                                selectedDriver = { id: d.driver?.id || null, social_reason: d.driver?.social_reason || '' };
                                selectedMaterial = { id: d.material.id, description: d.material.description || '' };
                        }

                        _plateManualMode = false;
                        document.getElementById('virtualKeyboard').classList.remove('active');
                        const sc = document.querySelector('.step-content');
                        if (sc) sc.classList.remove('keyboard-active');
                        _plateRestoreButtons();
                        _plateShowPlate(selectedVehicle.plate || value);
                        _plateGoToNext();
                    }
                });
                };

                if (hasAccess) {
                    // Deselect current access before setting new plate
                    fetch(`/api/data${currentWeigherPath}`, {
                        method: 'DELETE'
                    }).then(() => doSetPlate());
                } else {
                    doSetPlate();
                }
            };

            document.getElementById('plateDisplay').addEventListener('click', () => {
                if (!_plateManualMode) _plateEnterManual();
            });

            window.onDataReady = function() {
                if (_navigatingBack && totemAnagrafiche.card !== false) {
                    cancelTotem();
                    return;
                }
                if (selectedVehicle.plate) {
                    _plateShowPlate(selectedVehicle.plate);
                    document.getElementById('btnCancelPlate').style.visibility = '';
                    document.getElementById('btnNext').style.visibility = '';
                } else {
                    _plateShowEmpty();
                }
            };

            window.onDataUpdate = function() {
                if (_plateManualMode) return;
                if (selectedVehicle.plate) {
                    _plateShowPlate(selectedVehicle.plate);
                    _plateGoToNext();
                }
            };
        }
    },

    // ==================== SUBJECT ====================
    subject: {
        get title() { return 'Totem - ' + t('subject_title'); },
        html: () => `
            <h2 id="subjectTitle">${t('subject_title')}</h2>
            <ul class="suggestions-list suggestions-grid" id="subjectGrid"></ul>
            <div class="step-buttons">
                <button class="btn btn-secondary" onclick="goTo(isFromSummary() ? 'summary' : _findPrevEnabledStep('subject') + '?back=1')">${t('back')}</button>
                <button class="btn btn-primary btn-next" id="btnNextPage" onclick="_nextPage('subjectGrid', 'vector')">${t('more')}</button>
            </div>
        `,
        init: () => {
            window.onDataReady = function() {
                document.getElementById('subjectTitle').textContent =
                    selectedTypeSubject === 'CUSTOMER' ? t('customer') : t('supplier');

                loadItems('subject', 'social_reason', '', 'subjectGrid', (item) => {
                    selectAndAdvance('subject', item, 'vector');
                }, 'vector', 'plate');
            };
            window.onDataUpdate = null;
        }
    },

    // ==================== VECTOR ====================
    vector: {
        get title() { return 'Totem - ' + t('vector_title'); },
        html: () => `
            <h2>${t('vector_title')}</h2>
            <ul class="suggestions-list suggestions-grid" id="vectorGrid"></ul>
            <div class="step-buttons">
                <button class="btn btn-secondary" onclick="goTo(isFromSummary() ? 'summary' : _findPrevEnabledStep('vector') + '?back=1')">${t('back')}</button>
                <button class="btn btn-primary btn-next" id="btnNextPage" onclick="_nextPage('vectorGrid', 'driver')">${t('more')}</button>
            </div>
        `,
        init: () => {
            window.onDataReady = function() {
                loadItems('vector', 'social_reason', '', 'vectorGrid', (item) => {
                    selectAndAdvance('vector', item, 'driver');
                }, 'driver', 'subject');
            };
            window.onDataUpdate = null;
        }
    },

    // ==================== DRIVER ====================
    driver: {
        get title() { return 'Totem - ' + t('driver_title'); },
        html: () => `
            <h2>${t('driver_title')}</h2>
            <ul class="suggestions-list suggestions-grid" id="driverGrid"></ul>
            <div class="step-buttons">
                <button class="btn btn-secondary" onclick="goTo(isFromSummary() ? 'summary' : _findPrevEnabledStep('driver') + '?back=1')">${t('back')}</button>
                <button class="btn btn-primary btn-next" id="btnNextPage" onclick="_nextPage('driverGrid', 'material')">${t('more')}</button>
            </div>
        `,
        init: () => {
            window.onDataReady = function() {
                loadItems('driver', 'social_reason', '', 'driverGrid', (item) => {
                    selectAndAdvance('driver', item, 'material');
                }, 'material', 'vector');
            };
            window.onDataUpdate = null;
        }
    },

    // ==================== MATERIAL ====================
    material: {
        get title() { return 'Totem - ' + t('material_title'); },
        html: () => `
            <h2>${t('material_title')}</h2>
            <ul class="suggestions-list suggestions-grid" id="materialGrid"></ul>
            <div class="step-buttons">
                <button class="btn btn-secondary" onclick="goTo(isFromSummary() ? 'summary' : _findPrevEnabledStep('material') + '?back=1')">${t('back')}</button>
                <button class="btn btn-primary btn-next" id="btnNextPage" onclick="_nextPage('materialGrid', 'summary')">${t('more')}</button>
            </div>
        `,
        init: () => {
            window.onDataReady = function() {
                loadItems('material', 'description', '', 'materialGrid', (item) => {
                    selectAndAdvance('material', item, 'summary');
                }, 'summary', 'driver');
            };
            window.onDataUpdate = null;
        }
    },

    // ==================== SUMMARY ====================
    summary: {
        get title() { return 'Totem - ' + t('summary_title'); },
        style: `
            .summary-row.disabled { pointer-events: none; cursor: default; }
            .summary-row.disabled .summary-edit { display: none; }
        `,
        html: () => `
            <h2>${t('summary_title')}</h2>
            <div class="summary-card">
                <div class="summary-row" id="rowPlate" onclick="goTo('plate?from=summary')">
                    <span class="summary-label">${t('plate_title')}</span>
                    <div class="summary-value-row">
                        <span class="summary-value" id="summaryPlate">-</span>
                        <span class="summary-edit">&#9998;</span>
                    </div>
                </div>
                <div class="summary-row" id="rowSubject" onclick="goTo('subject?from=summary')">
                    <span class="summary-label" id="summaryType">-</span>
                    <div class="summary-value-row">
                        <span class="summary-value" id="summarySubject">-</span>
                        <span class="summary-edit">&#9998;</span>
                    </div>
                </div>
                <div class="summary-row" id="rowVector" onclick="goTo('vector?from=summary')">
                    <span class="summary-label">${t('vector_title')}</span>
                    <div class="summary-value-row">
                        <span class="summary-value" id="summaryVector">-</span>
                        <span class="summary-edit">&#9998;</span>
                    </div>
                </div>
                <div class="summary-row" id="rowDriver" onclick="goTo('driver?from=summary')">
                    <span class="summary-label">${t('driver_title')}</span>
                    <div class="summary-value-row">
                        <span class="summary-value" id="summaryDriver">-</span>
                        <span class="summary-edit">&#9998;</span>
                    </div>
                </div>
                <div class="summary-row" id="rowMaterial" onclick="goTo('material?from=summary')">
                    <span class="summary-label">${t('material_title')}</span>
                    <div class="summary-value-row">
                        <span class="summary-value" id="summaryMaterial">-</span>
                        <span class="summary-edit">&#9998;</span>
                    </div>
                </div>
                <div class="summary-row disabled" id="rowNet">
                    <span class="summary-label">${t('net')}</span>
                    <div class="summary-value-row">
                        <span class="summary-value" id="summaryNetWeight">-</span>
                    </div>
                </div>
            </div>
            <div class="step-buttons summary-buttons">
                <button class="btn btn-secondary" id="btnBack" onclick="goTo(_findPrevEnabledStep('summary') + '?back=1')">${t('back')}</button>
                <button class="btn btn-weighing" id="btnWeigh" onclick="handleWeighing()">${t('confirm_weigh')}</button>
            </div>
        `,
        init: () => {
            function updateSummary() {
                document.getElementById('summaryPlate').textContent = selectedVehicle.plate || '-';
                document.getElementById('summaryType').textContent = selectedTypeSubject === 'CUSTOMER' ? t('customer') : t('supplier');
                document.getElementById('summarySubject').textContent = selectedSubject.social_reason || '-';
                document.getElementById('summaryVector').textContent = selectedVector.social_reason || '-';
                document.getElementById('summaryDriver').textContent = selectedDriver.social_reason || '-';
                document.getElementById('summaryMaterial').textContent = selectedMaterial.description || '-';

                // Hide rows for disabled anagrafiche
                const rowVisibility = {
                    rowPlate: totemAnagrafiche.vehicle,
                    rowSubject: totemAnagrafiche.subject,
                    rowVector: totemAnagrafiche.vector,
                    rowDriver: totemAnagrafiche.driver,
                    rowMaterial: totemAnagrafiche.material,
                };
                Object.entries(rowVisibility).forEach(([id, visible]) => {
                    const row = document.getElementById(id);
                    if (row) row.style.display = visible ? '' : 'none';
                });
            }

            function applyReservationMode() {
                const isReservationMode = weighers_data_type && weighers_data_type !== "MANUALLY" && selectedIdWeight && selectedIdWeight.id && selectedIdWeight.id !== -1;
                const isExit = _isSecondWeighing();

                // Plate always locked with reservation
                const rowPlate = document.getElementById('rowPlate');
                if (rowPlate) rowPlate.classList.toggle('disabled', isReservationMode);

                // Each field: locked only if reservation has it
                const rowSubject = document.getElementById('rowSubject');
                if (rowSubject) rowSubject.classList.toggle('disabled', isReservationMode && _reservationHasSubject);
                const rowVector = document.getElementById('rowVector');
                if (rowVector) rowVector.classList.toggle('disabled', isReservationMode && _reservationHasVector);
                const rowDriver = document.getElementById('rowDriver');
                if (rowDriver) rowDriver.classList.toggle('disabled', isReservationMode && _reservationHasDriver);
                const rowMaterial = document.getElementById('rowMaterial');
                if (rowMaterial) rowMaterial.classList.toggle('disabled', isReservationMode && _reservationHasMaterial);

                const btnBack = document.getElementById('btnBack');
                if (btnBack) {
                    btnBack.onclick = () => goTo(_findPrevEnabledStep('summary') + '?back=1');
                }
            }

            window.onDataReady = function() {
                updateSummary();
                applyReservationMode();
            };

            window.onDataUpdate = function() {
                updateSummary();
                applyReservationMode();
            };
        }
    }
};
