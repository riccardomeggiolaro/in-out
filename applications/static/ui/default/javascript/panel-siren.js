// Panel and Siren Configuration Page
// Author: Claude AI
// Description: Dynamic configuration page for panel and siren adapters

// Adapter type descriptions
const ADAPTER_INFO = {
    tcp_custom: 'Protocollo binario custom per pannelli specifici. Include controllo display, durata e ID pannello.',
    tcp_raw: 'Invio di testo semplice via TCP. Supporta encoding personalizzato e terminatori di linea.',
    http_simple: 'Richieste HTTP senza autenticazione. Supporta GET, POST, PUT, PATCH.',
    http_basic: 'Richieste HTTP con autenticazione Basic (username:password in base64).',
    http_digest: 'Richieste HTTP con autenticazione Digest (più sicura di Basic).',
    http_bearer: 'Richieste HTTP con token Bearer nell\'header Authorization.',
};

// Current configurations
let panelConfig = null;
let sirenConfig = null;

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    loadConfigurations();
});

// Load configurations from API
async function loadConfigurations() {
    try {
        // Load panel config
        const panelResponse = await fetch('/api/anagrafic/configuration/panel');
        if (panelResponse.ok) {
            panelConfig = await panelResponse.json();
            populatePanelForm(panelConfig);
        }

        // Load siren config
        const sirenResponse = await fetch('/api/anagrafic/configuration/siren');
        if (sirenResponse.ok) {
            sirenConfig = await sirenResponse.json();
            populateSirenForm(sirenConfig);
        }
    } catch (error) {
        console.error('Error loading configurations:', error);
        showSnackbar('snackbar', 'Errore nel caricamento delle configurazioni', '#f44336', 'white');
    }
}

// Populate panel form with config data
function populatePanelForm(config) {
    const enabled = config.enabled !== undefined ? config.enabled : false;
    document.getElementById('panel-enabled').checked = enabled;

    updateStatusBadge('panel-status', enabled);

    if (enabled && config.type && config.type !== 'disabled') {
        document.getElementById('panel-form').classList.remove('hidden');
        document.getElementById('panel-type').value = config.type;

        // Connection
        if (config.connection) {
            document.getElementById('panel-ip').value = config.connection.ip || '';
            document.getElementById('panel-port').value = config.connection.port || '';
            document.getElementById('panel-timeout').value = config.connection.timeout || 5.0;
        }

        // Trigger type change to show relevant fields
        onPanelTypeChange();

        // Config specific fields
        if (config.config) {
            const cfg = config.config;

            // TCP Custom
            if (config.type === 'tcp_custom') {
                document.getElementById('panel-max-string').value = cfg.max_string_content || 100;
                document.getElementById('panel-id').value = cfg.panel_id || 16;
                document.getElementById('panel-duration').value = cfg.duration || 90;
            }

            // TCP Raw
            if (config.type === 'tcp_raw') {
                document.getElementById('panel-encoding').value = cfg.encoding || 'utf-8';
                document.getElementById('panel-line-ending').value = cfg.line_ending || '\\r\\n';
                document.getElementById('panel-wait-response').checked = cfg.wait_response || false;
            }

            // HTTP configs
            if (config.type.startsWith('http_')) {
                document.getElementById('panel-endpoint').value = cfg.endpoint || '';
                document.getElementById('panel-method').value = cfg.method || 'GET';
                document.getElementById('panel-query-param').value = cfg.query_param || '';

                if (config.type === 'http_basic' || config.type === 'http_digest') {
                    document.getElementById('panel-username').value = cfg.username || '';
                    document.getElementById('panel-password').value = cfg.password || '';
                }

                if (config.type === 'http_bearer') {
                    document.getElementById('panel-token').value = cfg.token || '';
                }
            }
        }
    } else {
        document.getElementById('panel-form').classList.add('hidden');
    }
}

// Populate siren form with config data
function populateSirenForm(config) {
    const enabled = config.enabled !== undefined ? config.enabled : false;
    document.getElementById('siren-enabled').checked = enabled;

    updateStatusBadge('siren-status', enabled);

    if (enabled && config.type && config.type !== 'disabled') {
        document.getElementById('siren-form').classList.remove('hidden');
        document.getElementById('siren-type').value = config.type;

        // Connection
        if (config.connection) {
            document.getElementById('siren-ip').value = config.connection.ip || '';
            document.getElementById('siren-port').value = config.connection.port || '';
            document.getElementById('siren-timeout').value = config.connection.timeout || 5.0;
        }

        // Trigger type change to show relevant fields
        onSirenTypeChange();

        // Config specific fields
        if (config.config) {
            const cfg = config.config;

            // HTTP configs
            if (config.type.startsWith('http_')) {
                document.getElementById('siren-endpoint').value = cfg.endpoint || '';
                document.getElementById('siren-method').value = cfg.method || 'GET';

                if (config.type === 'http_basic' || config.type === 'http_digest') {
                    document.getElementById('siren-username').value = cfg.username || '';
                    document.getElementById('siren-password').value = cfg.password || '';
                }

                if (config.type === 'http_bearer') {
                    document.getElementById('siren-token').value = cfg.token || '';
                }
            }

            // TCP Raw
            if (config.type === 'tcp_raw') {
                document.getElementById('siren-encoding').value = cfg.encoding || 'utf-8';
                document.getElementById('siren-line-ending').value = cfg.line_ending || '\\r\\n';
            }
        }
    } else {
        document.getElementById('siren-form').classList.add('hidden');
    }
}

// Update status badge
function updateStatusBadge(elementId, enabled) {
    const badge = document.getElementById(elementId);
    if (enabled) {
        badge.textContent = 'ABILITATO';
        badge.className = 'status-badge status-enabled';
    } else {
        badge.textContent = 'DISABILITATO';
        badge.className = 'status-badge status-disabled';
    }
}

// Change tab
function changeTab(tabName) {
    // Remove all active classes
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.menu-tab').forEach(btn => btn.classList.remove('selected'));

    // Add active class to selected tab
    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('selected');
}

// Panel enabled change handler
function onPanelEnabledChange() {
    const enabled = document.getElementById('panel-enabled').checked;
    const form = document.getElementById('panel-form');

    if (enabled) {
        form.classList.remove('hidden');
    } else {
        form.classList.add('hidden');
    }

    updateStatusBadge('panel-status', enabled);
}

// Panel type change handler
function onPanelTypeChange() {
    const type = document.getElementById('panel-type').value;

    // Hide all config sections
    document.getElementById('panel-tcp-custom-config').classList.add('hidden');
    document.getElementById('panel-tcp-raw-config').classList.add('hidden');
    document.getElementById('panel-http-config').classList.add('hidden');
    document.getElementById('panel-http-auth').classList.add('hidden');
    document.getElementById('panel-http-bearer').classList.add('hidden');

    // Show adapter info
    const infoDiv = document.getElementById('panel-type-info');
    if (type && ADAPTER_INFO[type]) {
        infoDiv.classList.remove('hidden');
        infoDiv.querySelector('p').textContent = ADAPTER_INFO[type];
    } else {
        infoDiv.classList.add('hidden');
    }

    // Show relevant config section
    if (type === 'tcp_custom') {
        document.getElementById('panel-tcp-custom-config').classList.remove('hidden');
    } else if (type === 'tcp_raw') {
        document.getElementById('panel-tcp-raw-config').classList.remove('hidden');
    } else if (type.startsWith('http_')) {
        document.getElementById('panel-http-config').classList.remove('hidden');

        if (type === 'http_basic' || type === 'http_digest') {
            document.getElementById('panel-http-auth').classList.remove('hidden');
        } else if (type === 'http_bearer') {
            document.getElementById('panel-http-bearer').classList.remove('hidden');
        }
    }
}

// Siren enabled change handler
function onSirenEnabledChange() {
    const enabled = document.getElementById('siren-enabled').checked;
    const form = document.getElementById('siren-form');

    if (enabled) {
        form.classList.remove('hidden');
    } else {
        form.classList.add('hidden');
    }

    updateStatusBadge('siren-status', enabled);
}

// Siren type change handler
function onSirenTypeChange() {
    const type = document.getElementById('siren-type').value;

    // Hide all config sections
    document.getElementById('siren-http-config').classList.add('hidden');
    document.getElementById('siren-http-auth').classList.add('hidden');
    document.getElementById('siren-http-bearer').classList.add('hidden');
    document.getElementById('siren-tcp-raw-config').classList.add('hidden');

    // Show adapter info
    const infoDiv = document.getElementById('siren-type-info');
    if (type && ADAPTER_INFO[type]) {
        infoDiv.classList.remove('hidden');
        infoDiv.querySelector('p').textContent = ADAPTER_INFO[type];
    } else {
        infoDiv.classList.add('hidden');
    }

    // Show relevant config section
    if (type.startsWith('http_')) {
        document.getElementById('siren-http-config').classList.remove('hidden');

        if (type === 'http_basic' || type === 'http_digest') {
            document.getElementById('siren-http-auth').classList.remove('hidden');
        } else if (type === 'http_bearer') {
            document.getElementById('siren-http-bearer').classList.remove('hidden');
        }
    } else if (type === 'tcp_raw') {
        document.getElementById('siren-tcp-raw-config').classList.remove('hidden');
    }
}

// Build panel configuration object
function buildPanelConfig() {
    const enabled = document.getElementById('panel-enabled').checked;

    if (!enabled) {
        return {
            enabled: false,
            type: 'disabled',
            connection: {
                ip: '0.0.0.0',
                port: 0,
                timeout: 5.0
            },
            config: {}
        };
    }

    const type = document.getElementById('panel-type').value;
    if (!type) {
        throw new Error('Seleziona un tipo di adapter');
    }

    const config = {
        enabled: true,
        type: type,
        connection: {
            ip: document.getElementById('panel-ip').value,
            port: parseInt(document.getElementById('panel-port').value),
            timeout: parseFloat(document.getElementById('panel-timeout').value)
        },
        config: {}
    };

    // Add type-specific config
    if (type === 'tcp_custom') {
        config.config = {
            max_string_content: parseInt(document.getElementById('panel-max-string').value) || 100,
            panel_id: parseInt(document.getElementById('panel-id').value) || 16,
            duration: parseInt(document.getElementById('panel-duration').value) || 90
        };
    } else if (type === 'tcp_raw') {
        config.config = {
            encoding: document.getElementById('panel-encoding').value || 'utf-8',
            line_ending: document.getElementById('panel-line-ending').value || '\\r\\n',
            wait_response: document.getElementById('panel-wait-response').checked || false
        };
    } else if (type.startsWith('http_')) {
        config.config = {
            endpoint: document.getElementById('panel-endpoint').value,
            method: document.getElementById('panel-method').value || 'GET',
            query_param: document.getElementById('panel-query-param').value || null
        };

        if (type === 'http_basic' || type === 'http_digest') {
            config.config.username = document.getElementById('panel-username').value;
            config.config.password = document.getElementById('panel-password').value;
        } else if (type === 'http_bearer') {
            config.config.token = document.getElementById('panel-token').value;
        }
    }

    return config;
}

// Build siren configuration object
function buildSirenConfig() {
    const enabled = document.getElementById('siren-enabled').checked;

    if (!enabled) {
        return {
            enabled: false,
            type: 'disabled',
            connection: {
                ip: '0.0.0.0',
                port: 0,
                timeout: 5.0
            },
            config: {}
        };
    }

    const type = document.getElementById('siren-type').value;
    if (!type) {
        throw new Error('Seleziona un tipo di adapter');
    }

    const config = {
        enabled: true,
        type: type,
        connection: {
            ip: document.getElementById('siren-ip').value,
            port: parseInt(document.getElementById('siren-port').value),
            timeout: parseFloat(document.getElementById('siren-timeout').value)
        },
        config: {}
    };

    // Add type-specific config
    if (type.startsWith('http_')) {
        config.config = {
            endpoint: document.getElementById('siren-endpoint').value,
            method: document.getElementById('siren-method').value || 'GET'
        };

        if (type === 'http_basic' || type === 'http_digest') {
            config.config.username = document.getElementById('siren-username').value;
            config.config.password = document.getElementById('siren-password').value;
        } else if (type === 'http_bearer') {
            config.config.token = document.getElementById('siren-token').value;
        }
    } else if (type === 'tcp_raw') {
        config.config = {
            encoding: document.getElementById('siren-encoding').value || 'utf-8',
            line_ending: document.getElementById('siren-line-ending').value || '\\r\\n'
        };
    }

    return config;
}

// Save panel configuration
async function savePanelConfig() {
    try {
        const config = buildPanelConfig();

        const response = await fetch('/api/anagrafic/configuration/panel', {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Errore nel salvataggio della configurazione');
        }

        panelConfig = await response.json();
        showSnackbar('snackbar', 'Configurazione pannello salvata con successo', '#4CAF50', 'white');

        // Reload form to show updated config
        populatePanelForm(panelConfig);

    } catch (error) {
        console.error('Error saving panel config:', error);
        showSnackbar('snackbar', `Errore: ${error.message}`, '#f44336', 'white');
    }
}

// Save siren configuration
async function saveSirenConfig() {
    try {
        const config = buildSirenConfig();

        const response = await fetch('/api/anagrafic/configuration/siren', {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Errore nel salvataggio della configurazione');
        }

        sirenConfig = await response.json();
        showSnackbar('snackbar', 'Configurazione sirena salvata con successo', '#4CAF50', 'white');

        // Reload form to show updated config
        populateSirenForm(sirenConfig);

    } catch (error) {
        console.error('Error saving siren config:', error);
        showSnackbar('snackbar', `Errore: ${error.message}`, '#f44336', 'white');
    }
}

// Disable panel configuration
async function disablePanelConfig() {
    if (!confirm('Sei sicuro di voler disabilitare il pannello?')) {
        return;
    }

    try {
        const response = await fetch('/api/anagrafic/configuration/panel', {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Errore nella disabilitazione del pannello');
        }

        panelConfig = await response.json();
        showSnackbar('snackbar', 'Pannello disabilitato con successo', '#4CAF50', 'white');

        // Reset form
        document.getElementById('panel-enabled').checked = false;
        document.getElementById('panel-form').classList.add('hidden');
        updateStatusBadge('panel-status', false);

    } catch (error) {
        console.error('Error disabling panel:', error);
        showSnackbar('snackbar', `Errore: ${error.message}`, '#f44336', 'white');
    }
}

// Disable siren configuration
async function disableSirenConfig() {
    if (!confirm('Sei sicuro di voler disabilitare la sirena?')) {
        return;
    }

    try {
        const response = await fetch('/api/anagrafic/configuration/siren', {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Errore nella disabilitazione della sirena');
        }

        sirenConfig = await response.json();
        showSnackbar('snackbar', 'Sirena disabilitata con successo', '#4CAF50', 'white');

        // Reset form
        document.getElementById('siren-enabled').checked = false;
        document.getElementById('siren-form').classList.add('hidden');
        updateStatusBadge('siren-status', false);

    } catch (error) {
        console.error('Error disabling siren:', error);
        showSnackbar('snackbar', `Errore: ${error.message}`, '#f44336', 'white');
    }
}

// Test panel
async function testPanel() {
    const text = document.getElementById('panel-test-text').value || 'TEST';

    try {
        const response = await fetch(`/api/anagrafic/message/panel?text=${encodeURIComponent(text)}`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Errore nel test del pannello');
        }

        const result = await response.json();
        showSnackbar('snackbar', `Test pannello inviato con successo! Buffer: ${result.buffer}`, '#4CAF50', 'white');

    } catch (error) {
        console.error('Error testing panel:', error);
        showSnackbar('snackbar', `Errore test: ${error.message}`, '#f44336', 'white');
    }
}

// Test siren
async function testSiren() {
    try {
        const response = await fetch('/api/anagrafic/call/siren');

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Errore nel test della sirena');
        }

        showSnackbar('snackbar', 'Sirena attivata con successo!', '#4CAF50', 'white');

    } catch (error) {
        console.error('Error testing siren:', error);
        showSnackbar('snackbar', `Errore test: ${error.message}`, '#f44336', 'white');
    }
}
