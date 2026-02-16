let list_serial_ports = [];
let list_printer_names = [];
let list_terminal_types = [];
const editButtonContent = "✏️";
const deleteButtonContent = "🗑️";

async function fetchData(url) {
    const response = await fetch(url);
    return response.json();
}

async function getSerialPortsList() {
    const data = await fetchData('/api/generic/list/serial-ports');
    list_serial_ports = data.list_serial_ports;
}

async function getPrintersList() {
    const data = await fetchData('/api/printer/list');
    list_printer_names = data;
}

async function getTerminalTypes() {
    const data = await fetchData('/api/config-weigher/terminals');
    list_terminal_types = data;
}

function createModal(title, content, onSave, onCancel) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    
    modal.innerHTML = `
        <div class="modal-content">
            <h3>${title}</h3>
            ${content}
            <div class="errors"></div>
            <div class="container-buttons right">
                <button class="cancel-btn">Annulla</button>
                <button class="save-btn" disabled>Salva</button>
            </div>
        </div>
    `;
    
    const form = modal.querySelector('form') || modal.querySelector('.content');
    const errorsDiv = modal.querySelector('.errors');
    const saveBtn = modal.querySelector('.save-btn');
    const cancelBtn = modal.querySelector('.cancel-btn');
    
    if (form) {
        form.oninput = () => saveBtn.disabled = !form.checkValidity();
    }
    
    saveBtn.addEventListener('click', () => onSave(modal));
    cancelBtn.addEventListener('click', () => {
        modal.style.display = 'none';
        onCancel && onCancel();
    });
    
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
            onCancel && onCancel();
        }
    });
    
    return { modal, errorsDiv, form, saveBtn };
}

function createConnectionUI(type, data, currentTime) {
    const container = document.createElement('div');
    container.className = 'borders';
    
    if (type === 'serial') {
        container.innerHTML = `
            <h3>Connessione Seriale</h3>
            <div class="content"></div>
        `;
        
        const content = container.querySelector('.content');
        if (data.serial_port_name) {
            content.innerHTML = `
                <h4>${data.serial_port_name}</h4>
                <p class="gray"><em>Baudrate: ${data.baudrate} - Timeout: ${data.timeout} - Esegui comando ogni: ${currentTime} secondi</em></p>
            `;
        } else {
            content.innerHTML = '<p>Nessuna connessione configurata</p>';
        }
        
    } else if (type === 'tcp') {
        container.innerHTML = `
            <h3>Connessione TCP</h3>
            <div class="content"></div>
        `;
        
        const content = container.querySelector('.content');
        if (data.ip) {
            content.innerHTML = `
                <p>Indirizzo IP: ${data.ip} - Porta: ${data.port} - Timeout: ${data.timeout}</p>
                <p>Esegui comando ogni: ${currentTime} secondi</p>
            `;
        } else {
            content.innerHTML = '<p>Nessuna connessione configurata</p>';
        }
    }
    
    return container;
}

function createWeigherElement(weigherData, instanceName) {
    const li = document.createElement('li');
    li.className = 'borders';
    
    // View Mode
    const viewMode = document.createElement('div');
    viewMode.innerHTML = `
        <div class="content">
            <h4>${weigherData.name} <span class="gray">${weigherData.terminal}</span></h4>
            <p class="gray"><em>Nodo: ${weigherData.node || 'Nessuno'}</em></p>
            <p class="gray"><em>Peso massimo: ${weigherData.max_weight}</em> <strong>-</strong> 
            <em>Peso minimo: ${weigherData.min_weight}</em> <strong>-</strong> 
            <em>Divisione: ${weigherData.division}</em></p>
            <p class="gray"><em>Soglia massima: ${weigherData.max_theshold || 'Nessuna'}</em></p>
            <p class="gray"><em>In esecuzione: ${weigherData.run ? 'Si' : 'No'}</em></p>
            <p class="gray"><em>Scaricare pesa dopo pesata: ${weigherData.need_take_of_weight_before_weighing ? 'Si' : 'No'}</em></p>
            <p class="gray"><em>Scaricare pesa all'avvio: ${weigherData.need_take_of_weight_on_startup ? 'Si' : 'No'}</em></p>
            <p class="gray"><em>Stampante: ${weigherData.printer_name || 'Nessuna'}</em></p>
            <p class="gray"><em>Numero di stampe: ${weigherData.number_of_prints}</em></p>
            <p class="gray"><em>Stampa all'entrata: ${weigherData.events?.weighing?.print?.in ? 'Si' : 'No'} 
            - Stampa all'uscita: ${weigherData.events?.weighing?.print?.out ? 'Si' : 'No'}</em></p>
        </div>
        <div class="container-buttons">
            <button class="delete-btn">${deleteButtonContent}</button>
            <button class="edit-btn">${editButtonContent}</button>
        </div>
    `;
    
    // Edit Mode
    const editMode = document.createElement('div');
    editMode.style.display = 'none';
    editMode.innerHTML = `
        <form class="content"></form>
        <div class="container-buttons">
            <button class="cancel-btn">Annulla</button>
            <button class="save-btn">Salva</button>
        </div>
        <div class="errors"></div>
    `;
    
    // Populate edit form
    const form = editMode.querySelector('form');
    form.innerHTML = generateWeigherFormHTML(weigherData);
    
    // Event handlers
    viewMode.querySelector('.edit-btn').addEventListener('click', () => {
        viewMode.style.display = 'none';
        editMode.style.display = 'block';
    });
    
    viewMode.querySelector('.delete-btn').addEventListener('click', () => {
        const modal = createDeleteModal(
            'Conferma eliminazione', 
            'Sei sicuro di voler eliminare la configurazione della pesa?',
            async () => {
                const url = `/api/config-weigher/instance/node?instance_name=${instanceName}&weigher_name=${weigherData.name}`;
                await fetch(url, { method: 'DELETE' });
                li.remove();
            }
        );
        li.appendChild(modal);
    });
    
    editMode.querySelector('.cancel-btn').addEventListener('click', () => {
        editMode.style.display = 'none';
        viewMode.style.display = 'block';
    });
    
    editMode.querySelector('.save-btn').addEventListener('click', async () => {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        const url = `/api/config-weigher/instance/node?instance_name=${instanceName}&weigher_name=${weigherData.name}`;
        const response = await fetch(url, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (result.detail) {
            editMode.querySelector('.errors').innerHTML = result.detail.map(e => e.msg).join('<br>');
        } else {
            Object.assign(weigherData, result);
            viewMode.querySelector('.content').innerHTML = generateViewContent(weigherData);
            editMode.style.display = 'none';
            viewMode.style.display = 'block';
        }
    });
    
    li.appendChild(viewMode);
    li.appendChild(editMode);
    return li;
}

function generateViewContent(data) {
    return `
        <h4>${data.name} <span class="gray">${data.terminal}</span></h4>
        <p class="gray"><em>Nodo: ${data.node || 'Nessuno'}</em></p>
        <p class="gray"><em>Peso massimo: ${data.max_weight}</em> <strong>-</strong> 
        <em>Peso minimo: ${data.min_weight}</em> <strong>-</strong> 
        <em>Divisione: ${data.division}</em></p>
        <p class="gray"><em>Soglia massima: ${data.max_theshold || 'Nessuna'}</em></p>
        <p class="gray"><em>In esecuzione: ${data.run ? 'Si' : 'No'}</em></p>
        <p class="gray"><em>Scaricare pesa dopo pesata: ${data.need_take_of_weight_before_weighing ? 'Si' : 'No'}</em></p>
        <p class="gray"><em>Scaricare pesa all'avvio: ${data.need_take_of_weight_on_startup ? 'Si' : 'No'}</em></p>
        <p class="gray"><em>Stampante: ${data.printer_name || 'Nessuna'}</em></p>
        <p class="gray"><em>Numero di stampe: ${data.number_of_prints}</em></p>
        <p class="gray"><em>Stampa all'entrata: ${data.events?.weighing?.print?.in ? 'Si' : 'No'} 
        - Stampa all'uscita: ${data.events?.weighing?.print?.out ? 'Si' : 'No'}</em></p>
    `;
}

function generateWeigherFormHTML(data) {
    const printers = list_printer_names.map(p => 
        `<option value="${p.nome}" ${data.printer_name === p.nome ? 'selected' : ''}>${p.nome}</option>`
    ).join('');
    
    return `
        <div style="display: flex; gap: 16px;">
            <div style="flex: 1;">
                <label for="name">Nome pesa:</label>
                <input type="text" name="name" value="${data.name || ''}" required>
            </div>
            <div style="flex: 1;">
                <label for="terminal">Terminale:</label>
                <select name="terminal" required>
                    ${list_terminal_types.map(t => `<option value="${t}" ${(data.terminal || list_terminal_types[0]) === t ? 'selected' : ''}>${t}</option>`).join('')}
                </select>
            </div>
            <div style="flex: 1;">
                <label for="node">Nodo:</label>
                <input type="text" name="node" value="${data.node || ''}">
            </div>
        </div>
        <div style="display: flex; gap: 16px; margin-top: 10px;">
            <div style="flex: 1;">
                <label for="max_weight">Peso massimo:</label>
                <input type="number" name="max_weight" min="1" value="${data.max_weight || ''}" required>
            </div>
            <div style="flex: 1;">
                <label for="min_weight">Peso minimo:</label>
                <input type="number" name="min_weight" min="1" value="${data.min_weight || ''}" required>
            </div>
            <div style="flex: 1;">
                <label for="division">Divisione:</label>
                <input type="number" name="division" min="1" value="${data.division || ''}" required>
            </div>
            <div style="flex: 1;">
                <label for="max_theshold">Soglia massima:</label>
                <input type="number" name="max_theshold" min="1" value="${data.max_theshold || ''}">
            </div>
        </div>
        <div style="display: flex; gap: 16px; margin-top: 10px; align-items: flex-end;">
            <div style="flex: 2;">
                <label for="printer_name">Stampante:</label>
                <select name="printer_name" required>
                    ${printers}
                </select>
            </div>
            <div style="flex: 1;">
                <label for="number_of_prints">Numero di stampe:</label>
                <input type="number" name="number_of_prints" min="1" max="5" value="${data.number_of_prints || 1}" required>
            </div>
            <div style="flex: 1; text-align: center;">
                <label>Stampa all'entrata</label><br>
                <input type="checkbox" name="print_on_in" ${data.events?.weighing?.print?.in ? 'checked' : ''}>
            </div>
            <div style="flex: 1; text-align: center;">
                <label>Stampa all'uscita</label><br>
                <input type="checkbox" name="print_on_out" ${data.events?.weighing?.print?.out ? 'checked' : ''}>
            </div>
        </div>
        <div style="margin-top: 10px;">
            <label><input type="checkbox" name="run" ${data.run ? 'checked' : ''}> In esecuzione</label>
        </div>
        <div>
            <label><input type="checkbox" name="need_take_of_weight_before_weighing" 
                ${data.need_take_of_weight_before_weighing ? 'checked' : ''}> Scaricare dopo pesata</label>
        </div>
        <div>
            <label><input type="checkbox" name="need_take_of_weight_on_startup" 
                ${data.need_take_of_weight_on_startup ? 'checked' : ''}> Scaricare all'avvio</label>
        </div>
    `;
}

function createDeleteModal(title, message, onConfirm) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    
    modal.innerHTML = `
        <div class="modal-content">
            <h3>${title}</h3>
            <p>${message}</p>
            <div class="container-buttons right">
                <button class="cancel-btn">Annulla</button>
                <button class="confirm-btn delete-btn">Conferma</button>
            </div>
        </div>
    `;
    
    modal.querySelector('.cancel-btn').addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    modal.querySelector('.confirm-btn').addEventListener('click', async () => {
        await onConfirm();
        modal.style.display = 'none';
    });
    
    return modal;
}

function createInstanceElement(key, data, container) {
    const div = document.createElement('div');
    div.className = 'div_config';
    
    let currentTimeBetweenActions = data.time_between_actions;
    
    div.innerHTML = `
        <h3 class="borders">
            <button class="delete-instance width-fit-content delete-btn">${deleteButtonContent}</button>
            &nbsp;
            <p>Istanza: ${key}</p>
        </h3>
        <div class="connection-container"></div>
        <button class="addWeigher width-fit-content">Configura pesa</button>
        <ul class="weighers-list"></ul>
    `;
    
    const connectionContainer = div.querySelector('.connection-container');
    const weighersList = div.querySelector('.weighers-list');
    
    // Setup connection UI
    const serialUI = createConnectionUI('serial', data.connection || {}, currentTimeBetweenActions);
    const tcpUI = createConnectionUI('tcp', data.connection || {}, currentTimeBetweenActions);
    connectionContainer.appendChild(serialUI);
    connectionContainer.appendChild(tcpUI);
    
    // Delete instance handler
    div.querySelector('.delete-instance').addEventListener('click', () => {
        const modal = createDeleteModal(
            'Conferma eliminazione', 
            'Sei sicuro di voler eliminare l\'istanza?',
            async () => {
                await fetch(`/api/config-weigher/instance?instance_name=${key}`, { method: 'DELETE' });
                div.remove();
            }
        );
        div.appendChild(modal);
    });
    
    // Add weigher handler
    div.querySelector('.addWeigher').addEventListener('click', () => {
        const { modal } = createModal(
            'Aggiungi pesa',
            `<form>${generateWeigherFormHTML({})}</form>`,
            async (modal) => {
                const formData = new FormData(modal.querySelector('form'));
                const data = Object.fromEntries(formData.entries());
                
                const response = await fetch(`/api/config-weigher/instance/node?instance_name=${key}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                if (result.detail) {
                    modal.querySelector('.errors').innerHTML = result.detail.map(e => e.msg).join('<br>');
                } else {
                    const weigherName = Object.keys(result)[0];
                    const weigher = {
                        name: weigherName,
                        ...result[weigherName]
                    };
                    weighersList.appendChild(createWeigherElement(weigher, key));
                    modal.style.display = 'none';
                }
            },
            () => modal.querySelector('form').reset()
        );
        div.appendChild(modal.modal);
    });
    
    // Add existing weighers
    for (const [name, weigher] of Object.entries(data.nodes || {})) {
        weighersList.appendChild(createWeigherElement(
            { name, ...weigher }, 
            key
        ));
    }
    
    container.appendChild(div);
}

async function loadSetupWeighers() {
    const weighers_config = document.getElementById('config');
    
    await Promise.all([
        getSerialPortsList(),
        getPrintersList(),
        getTerminalTypes()
    ]);
    
    const instances = await fetchData('/api/config-weigher/all/instance');
    
    // Add instance button
    const { modal } = createModal(
        'Aggiungi istanza',
        '<form oninput="document.querySelector(\'.save-btn\').disabled = !this.checkValidity()">' +
            '<input type="text" name="name" required>' +
        '</form>',
        async (modal) => {
            const name = modal.querySelector('input').value;
            const response = await fetch('/api/config-weigher/instance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    name, 
                    connection: {}, 
                    time_between_actions: 1 
                })
            });
            
            const result = await response.json();
            if (result.detail) {
                modal.querySelector('.errors').innerHTML = result.detail.map(e => e.msg).join('<br>');
            } else {
                const instanceName = Object.keys(result)[0];
                createInstanceElement(instanceName, result[instanceName], weighers_config);
                modal.style.display = 'none';
                modal.querySelector('input').value = '';
            }
        }
    );
    
    const addBtn = document.createElement('button');
    addBtn.className = 'container-buttons add-btn';
    addBtn.textContent = 'Aggiungi istanza';
    addBtn.addEventListener('click', () => {
        modal.style.display = 'block';
        modal.querySelector('.save-btn').disabled = true;
    });
    
    weighers_config.appendChild(addBtn);
    weighers_config.appendChild(modal.modal);
    
    // Add existing instances
    for (const [key, data] of Object.entries(instances)) {
        createInstanceElement(key, data, weighers_config);
    }
}

document.addEventListener("DOMContentLoaded", loadSetupWeighers);