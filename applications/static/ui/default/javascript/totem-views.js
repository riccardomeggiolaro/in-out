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
            .manual-buttons { display: none; gap: 12px; margin-top: 20px; }
            .manual-buttons.active { display: flex; }
        `,
        html: () => `
            <h2>Targa</h2>
            <div class="license-plate plate-empty" id="plateDisplay">
                <div class="plate-band plate-band-left">
                    <div class="plate-stars">&#9733;</div>
                </div>
                <span class="plate-text" id="plateText">&#8226;&#8226;&#8226;&#8226;&#8226;&#8226;&#8226;</span>
                <input class="plate-input" id="manualPlateInput" type="text" maxlength="10" placeholder="AB123CD" autocomplete="off">
                <div class="plate-band plate-band-right"></div>
            </div>
            <div class="manual-buttons" id="manualButtons">
                <button class="btn btn-secondary" onclick="_plateExitManual()">Annulla</button>
                <button class="btn btn-primary" onclick="_plateConfirmManual()">Conferma</button>
            </div>
            <div class="step-buttons">
                <button class="btn btn-primary btn-next" id="btnNext" style="display:none" onclick="_plateGoToNext()">Avanti</button>
            </div>
        `,
        init: () => {
            window._plateManualMode = false;

            window._plateShowPlate = function(plate) {
                document.getElementById('plateDisplay').classList.remove('plate-empty');
                document.getElementById('plateText').textContent = plate;
                document.getElementById('plateText').style.display = '';
                document.getElementById('manualPlateInput').style.display = 'none';
            };

            window._plateShowEmpty = function() {
                document.getElementById('plateDisplay').classList.add('plate-empty');
                document.getElementById('plateText').innerHTML = '&#8226;&#8226;&#8226;&#8226;&#8226;&#8226;&#8226;';
                document.getElementById('plateText').style.display = '';
                document.getElementById('manualPlateInput').style.display = 'none';
            };

            window._plateGoToNext = function() {
                if (isFromSummary()) { goTo('summary'); return; }
                const hasReservation = selectedIdWeight && selectedIdWeight.id && selectedIdWeight.id !== -1;
                goTo(hasReservation ? 'summary' : 'subject');
            };

            window._plateEnterManual = function() {
                _plateManualMode = true;
                document.getElementById('plateDisplay').classList.remove('plate-empty');
                document.getElementById('plateText').style.display = 'none';
                const input = document.getElementById('manualPlateInput');
                input.classList.add('active');
                input.style.display = 'flex';
                input.value = '';
                input.focus();
                document.getElementById('manualButtons').classList.add('active');
            };

            window._plateExitManual = function() {
                _plateManualMode = false;
                document.getElementById('manualPlateInput').classList.remove('active');
                document.getElementById('manualPlateInput').style.display = 'none';
                document.getElementById('manualButtons').classList.remove('active');
                if (selectedVehicle.plate) _plateShowPlate(selectedVehicle.plate);
                else _plateShowEmpty();
            };

            window._plateConfirmManual = function() {
                const value = document.getElementById('manualPlateInput').value.trim().toUpperCase();
                if (!value) {
                    showSnackbar("snackbar", "Inserisci una targa valida", 'rgb(255, 208, 208)', 'black');
                    return;
                }
                if (value.length > 10) {
                    showSnackbar("snackbar", "La targa può avere massimo 10 caratteri", 'rgb(255, 208, 208)', 'black');
                    return;
                }

                fetch(`/api/data${currentWeigherPath}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ data_in_execution: { vehicle: { plate: value } } })
                })
                .then(res => res.json())
                .then(res => {
                    if (res.detail) {
                        showSnackbar("snackbar", res.detail, 'rgb(255, 208, 208)', 'black');
                    } else {
                        _plateManualMode = false;
                        document.getElementById('manualPlateInput').classList.remove('active');
                        document.getElementById('manualPlateInput').style.display = 'none';
                        document.getElementById('manualButtons').classList.remove('active');
                        _plateShowPlate(value);
                        _plateGoToNext();
                    }
                });
            };

            document.getElementById('plateDisplay').addEventListener('click', () => {
                if (!_plateManualMode) _plateEnterManual();
            });

            document.getElementById('manualPlateInput').addEventListener('keydown', (e) => {
                if (e.key === 'Enter') _plateConfirmManual();
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
        `,
        init: () => {
            window.onDataReady = function() {
                document.getElementById('subjectTitle').textContent =
                    selectedTypeSubject === 'CUSTOMER' ? 'Cliente' : 'Fornitore';

                loadItems('subject', 'social_reason', '', 'subjectGrid', (item) => {
                    selectAndAdvance('subject', item, 'vector');
                }, 'vector');
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
        `,
        init: () => {
            window.onDataReady = function() {
                loadItems('vector', 'social_reason', '', 'vectorGrid', (item) => {
                    selectAndAdvance('vector', item, 'driver');
                }, 'driver');
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
        `,
        init: () => {
            window.onDataReady = function() {
                loadItems('driver', 'social_reason', '', 'driverGrid', (item) => {
                    selectAndAdvance('driver', item, 'material');
                }, 'material');
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
        `,
        init: () => {
            window.onDataReady = function() {
                loadItems('material', 'description', '', 'materialGrid', (item) => {
                    selectAndAdvance('material', item, 'summary');
                }, 'summary');
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
                <button class="btn btn-secondary" id="btnCancel" onclick="goTo('plate')">Annulla</button>
                <button class="btn btn-weighing" onclick="handleGenericWeighing()">Pesatura Generica</button>
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
            }

            function applyReservationMode() {
                const isReservationMode = selectedIdWeight && selectedIdWeight.id && selectedIdWeight.id !== -1;

                ['rowPlate', 'rowSubject', 'rowVector', 'rowDriver'].forEach(id => {
                    const row = document.getElementById(id);
                    if (row) row.classList.toggle('disabled', isReservationMode);
                });

                const btnBack = document.getElementById('btnBack');
                if (btnBack) {
                    btnBack.onclick = () => goTo(isReservationMode ? 'plate' : 'material');
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
