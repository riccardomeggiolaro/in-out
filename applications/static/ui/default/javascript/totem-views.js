// ===== TOTEM VIEWS - SPA view definitions =====

const totemViews = {

    // ==================== PLATE ====================
    plate: {
        title: 'Totem - Targa',
        style: `
            .license-plate { cursor: pointer; }
            .plate-empty .plate-text { color: #ccc; letter-spacing: 12px; }
            .plate-input { display: none; font-size: 3.5rem; font-weight: 700; font-family: 'Courier New', monospace; letter-spacing: 8px; text-align: center; text-transform: uppercase; border: none; outline: none; background: transparent; width: 100%; height: 100%; padding: 0 8px; box-sizing: border-box; }
            .plate-input.active { display: flex; }
            .virtual-keyboard { display: none; width: 100%; flex: 1; min-height: 0; padding: 4px 16px; box-sizing: border-box; flex-direction: column; gap: 4px; }
            .virtual-keyboard.active { display: flex; }
            .vk-row { display: flex; gap: 4px; flex: 1; justify-content: center; }
            .vk-key { flex: 1; max-width: 10%; background: white; border: 2px solid #e0e0e0; border-radius: clamp(4px, 1vw, 8px); font-size: clamp(0.8rem, 4vh, 2.5rem); font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; font-family: inherit; transition: background 0.1s; user-select: none; -webkit-user-select: none; }
            .vk-key:active { background: #e3effc; }
            .vk-key.vk-wide { max-width: 15%; flex: 1.5; }
            .vk-key.vk-backspace { max-width: 15%; flex: 1.5; font-size: clamp(0.7rem, 3vh, 2rem); }
        `,
        html: () => `
            <h2>Targa</h2>
            <div class="license-plate plate-empty" id="plateDisplay">
                <div class="plate-band plate-band-left">
                    <div class="plate-stars">&#9733;</div>
                </div>
                <span class="plate-text" id="plateText">&#8226;&#8226;&#8226;&#8226;&#8226;&#8226;&#8226;</span>
                <input class="plate-input" id="manualPlateInput" type="text" maxlength="10" placeholder="AB123CD" autocomplete="off" inputmode="none" enterkeyhint="done" readonly>
                <div class="plate-band plate-band-right"></div>
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
                <button class="btn btn-secondary manual-btn" id="btnAnnulla" style="display:none" onclick="_plateExitManual()">Annulla</button>
                <button class="btn btn-primary manual-btn" id="btnConferma" style="display:none" onclick="_plateConfirmManual()">Conferma</button>
                <button class="btn btn-primary btn-next" id="btnNext" style="display:none; grid-column: 2;" onclick="_plateGoToNext()">Avanti</button>
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
                const hasReservation = selectedIdWeight && selectedIdWeight.id && selectedIdWeight.id !== -1;
                if (hasReservation) {
                    goTo(_reservationHasMaterial ? 'summary' : 'material');
                } else {
                    const dest = _findNextEmptyStep('plate');
                    goTo(dest || 'summary');
                }
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
                document.getElementById('btnAnnulla').style.display = '';
                document.getElementById('btnConferma').style.display = '';
                document.getElementById('btnNext').style.display = 'none';
            };

            window._plateExitManual = function() {
                _plateManualMode = false;
                document.getElementById('virtualKeyboard').classList.remove('active');
                document.getElementById('btnAnnulla').style.display = 'none';
                document.getElementById('btnConferma').style.display = 'none';
                if (selectedVehicle.plate) {
                    _plateShowPlate(selectedVehicle.plate);
                    document.getElementById('btnNext').style.display = '';
                } else {
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
                        document.getElementById('btnAnnulla').style.display = 'none';
                        document.getElementById('btnConferma').style.display = 'none';
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
                if (selectedVehicle.plate) {
                    _plateShowPlate(selectedVehicle.plate);
                    document.getElementById('btnNext').style.display = '';
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
        title: 'Totem - Ragione Sociale',
        html: () => `
            <h2 id="subjectTitle">Ragione Sociale</h2>
            <ul class="suggestions-list suggestions-grid" id="subjectGrid"></ul>
            <div class="step-buttons">
                <button class="btn btn-secondary" onclick="goTo(isFromSummary() ? 'summary' : 'plate?back=1')">Indietro</button>
                <button class="btn btn-primary btn-next" id="btnNextPage" onclick="_nextPage('subjectGrid', 'vector')">Altro</button>
            </div>
        `,
        init: () => {
            window.onDataReady = function() {
                document.getElementById('subjectTitle').textContent =
                    selectedTypeSubject === 'CUSTOMER' ? 'Cliente' : 'Fornitore';

                loadItems('subject', 'social_reason', '', 'subjectGrid', (item) => {
                    selectAndAdvance('subject', item, 'vector');
                }, 'vector', 'plate');
            };
            window.onDataUpdate = null;
        }
    },

    // ==================== VECTOR ====================
    vector: {
        title: 'Totem - Vettore',
        html: () => `
            <h2>Vettore</h2>
            <ul class="suggestions-list suggestions-grid" id="vectorGrid"></ul>
            <div class="step-buttons">
                <button class="btn btn-secondary" onclick="goTo(isFromSummary() ? 'summary' : 'subject?back=1')">Indietro</button>
                <button class="btn btn-primary btn-next" id="btnNextPage" onclick="_nextPage('vectorGrid', 'driver')">Altro</button>
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
        title: 'Totem - Autista',
        html: () => `
            <h2>Autista</h2>
            <ul class="suggestions-list suggestions-grid" id="driverGrid"></ul>
            <div class="step-buttons">
                <button class="btn btn-secondary" onclick="goTo(isFromSummary() ? 'summary' : 'vector?back=1')">Indietro</button>
                <button class="btn btn-primary btn-next" id="btnNextPage" onclick="_nextPage('driverGrid', 'material')">Altro</button>
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
        title: 'Totem - Materiale',
        html: () => `
            <h2>Materiale</h2>
            <ul class="suggestions-list suggestions-grid" id="materialGrid"></ul>
            <div class="step-buttons">
                <button class="btn btn-secondary" onclick="goTo(isFromSummary() ? 'summary' : 'driver?back=1')">Indietro</button>
                <button class="btn btn-primary btn-next" id="btnNextPage" onclick="_nextPage('materialGrid', 'summary')">Altro</button>
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
        title: 'Totem - Riepilogo',
        style: `
            .summary-row.disabled { pointer-events: none; opacity: 0.6; cursor: default; }
            .summary-row.disabled .summary-edit { display: none; }
        `,
        html: () => `
            <h2>Riepilogo</h2>
            <div class="summary-card">
                <div class="summary-row" id="rowPlate" onclick="goTo('plate?from=summary')">
                    <span class="summary-label">Targa</span>
                    <span class="summary-value" id="summaryPlate">-</span>
                    <span class="summary-edit">&#9998;</span>
                </div>
                <div class="summary-row" id="rowSubject" onclick="goTo('subject?from=summary')">
                    <span class="summary-label" id="summaryType">-</span>
                    <span class="summary-value" id="summarySubject">-</span>
                    <span class="summary-edit">&#9998;</span>
                </div>
                <div class="summary-row" id="rowVector" onclick="goTo('vector?from=summary')">
                    <span class="summary-label">Vettore</span>
                    <span class="summary-value" id="summaryVector">-</span>
                    <span class="summary-edit">&#9998;</span>
                </div>
                <div class="summary-row" id="rowDriver" onclick="goTo('driver?from=summary')">
                    <span class="summary-label">Autista</span>
                    <span class="summary-value" id="summaryDriver">-</span>
                    <span class="summary-edit">&#9998;</span>
                </div>
                <div class="summary-row" id="rowMaterial" onclick="goTo('material?from=summary')">
                    <span class="summary-label">Materiale</span>
                    <span class="summary-value" id="summaryMaterial">-</span>
                    <span class="summary-edit">&#9998;</span>
                </div>
            </div>
            <div class="step-buttons summary-buttons">
                <button class="btn btn-secondary" id="btnBack" onclick="goTo('material?back=1')">Indietro</button>
                <button class="btn btn-weighing" id="btnWeigh" onclick="handleWeighing()">Entrata</button>
            </div>
        `,
        init: () => {
            function updateSummary() {
                document.getElementById('summaryPlate').textContent = selectedVehicle.plate || '-';
                document.getElementById('summaryType').textContent = selectedTypeSubject === 'CUSTOMER' ? 'Cliente' : 'Fornitore';
                document.getElementById('summarySubject').textContent = selectedSubject.social_reason || '-';
                document.getElementById('summaryVector').textContent = selectedVector.social_reason || '-';
                document.getElementById('summaryDriver').textContent = selectedDriver.social_reason || '-';
                document.getElementById('summaryMaterial').textContent = selectedMaterial.description || '-';
                const btnWeigh = document.getElementById('btnWeigh');
                if (btnWeigh) btnWeigh.textContent = _isSecondWeighing() ? 'Uscita' : 'Entrata';
            }

            function applyReservationMode() {
                const isReservationMode = selectedIdWeight && selectedIdWeight.id && selectedIdWeight.id !== -1;

                // All fields locked except material (if empty) when reservation is selected
                ['rowPlate', 'rowSubject', 'rowVector', 'rowDriver'].forEach(id => {
                    const row = document.getElementById(id);
                    if (row) row.classList.toggle('disabled', isReservationMode);
                });
                // Material: locked if reservation has it OR if in exit mode with material already on in_out
                const rowMaterial = document.getElementById('rowMaterial');
                const materialLockedByReservation = isReservationMode && _reservationHasMaterial;
                const materialLockedByInOut = isReservationMode && _isSecondWeighing() && !!selectedMaterial.id;
                if (rowMaterial) rowMaterial.classList.toggle('disabled', materialLockedByReservation || materialLockedByInOut);

                const btnBack = document.getElementById('btnBack');
                if (btnBack) {
                    btnBack.onclick = () => goTo(isReservationMode ? 'plate?back=1' : 'material?back=1');
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
