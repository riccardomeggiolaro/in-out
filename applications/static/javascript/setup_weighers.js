const weighers_config = document.getElementById('weighers_config');

// Creo il contenitore principale del modal usando createElement
const modal = document.createElement('div');
modal.id = 'modalDeleteWeigher';
modal.classList.toggle('modal');

// Aggiungo il contenuto del modal tramite innerHTML
modal.innerHTML = `
    <div class="modal-content">
        <h3>Conferma eliminazione</h3>
        <p>Sei sicuro di voler eliminare la configurazione della pesa?</p>
        <div class="modal-buttons">
            <button id="modalDeleteWeigherCancel" class="modal-cancel-button">Annulla</button>
            <button id="modalDeleteWeigherConfirm" class="modal-confirm-button">Elimina</button>
        </div>
    </div>
`;

const addModal = document.createElement('div');
addModal.id = 'modalAddWeigher';
addModal.classList.toggle('modal');

addModal.innerHTML = `
    <div class="modal-content">
        <h3>Configura pesa</h3>
        <div>
                    Nome:<br>
                    <input type="text" name="name" value="" class="h4-input"><br>
                    Nodo:<br>
                    <input type="text" name="node" value=""><br>
                    Peso massimo:<br>
                    <input type="number" name="max_weight" value=""><br>
                    Peso minimo:<br><input type="number" name="min_weight" value=""><br>
                    Divisione:<br>
                    <input type="number" name="division" value=""><br>
                    Terminale:<br>
                    <input type="text" name="terminal" value=""><br>
                    Mantieni sessione realtime dopo comando: <input type="checkbox" name="maintaine_session_realtime_after_command"}><br>
                    Diagnostica prioritaria sul realtime: <input type="checkbox" name="diagnostic_has_priority_than_realtime"}><br>
                    In esecuzione: <input type="checkbox" name="run"><br>                    
        </div>
        <div class="modal-buttons">
            <button id="modalAddWeigherCancel" class="modal-cancel-button">Annulla</button>
            <button id="modalAddWeigherConfirm" class="modal-confirm-button">Elimina</button>
        </div>
    </div>
`;

// Aggiungo il modal al body
document.body.appendChild(modal);
document.body.appendChild(addModal);

// Recupero i riferimenti ai pulsanti per aggiungere gli event listeners (se necessario)
const modalCancel = modal.querySelector('#modalDeleteWeigherCancel');
const modalConfirm = modal.querySelector('#modalDeleteWeigherConfirm');

const modalCancelAdd = addModal.querySelector('#modalAddWeigherCancel');
const modalCobnfirmAdd = addModal.querySelector('#modalAddWeigherConfirm');

fetch('/config_weigher/all/instance')
.then(res => res.json())
.then(data => {
    for (let key in data) {
        const div = document.createElement('div');
        div.classList.toggle('div_config');
        const h3 = document.createElement('h3');
        const ul = document.createElement('ul');
        h3.style.border = '1px solid #ddd';
        h3.style.borderRadius = '3px';
        h3.style.padding = '10px';
        h3.style.backgroundColor = 'whitesmoke';
        h3.style.width = '100%';
        h3.textContent = `Istanza: ${key}`;
        const addButton = document.createElement('button');
        addButton.textContent = 'Configura pesa';

        addButton.addEventListener('click', () => {
            addModal.style.display = 'block';
        });

        modalCancelAdd.addEventListener('click', () => {
            addModal.style.display = 'none';
        });

        for (let weigher of data[key]['nodes']) {
            const li = document.createElement('li');
            
            const viewMode = document.createElement('div');
            const editMode = document.createElement('div');
            editMode.style.display = 'none';

            viewMode.innerHTML = `
                <div class="content"></div>
                <button class="delete-btn">Elimina</button>
                <button class="edit-btn">Modifica</button>
            `;

            const populateViewContent = (data) => {
                viewMode.querySelector('.content').innerHTML = `
                    <h4>${data.name}</h4>
                    Nodo: ${data.node ? data.node : ''}<br>
                    Peso massimo: ${data.max_weight}<br>
                    Peso minimo: ${data.min_weight}<br>
                    Divisione: ${data.division}<br>
                    Mantieni sessione realtime dopo comando: ${data.maintaine_session_realtime_after_command}<br>
                    Diagnostica prioritaria sul realtime: ${data.diagnostic_has_priority_than_realtime}<br>
                    Terminale: ${data.terminal}<br>
                    In esecuzione: ${data.run}<br>
                    Stato: ${data.status}<br>
                    Firmware: ${data.terminal_data.firmware ? data.terminal_data.firmware : ''}<br>
                    Nome modello: ${data.terminal_data.model_name ? data.terminal_data.model_name : ''}<br>
                    Numero seriale: ${data.terminal_data.serial_number ? data.terminal_data.serial_number : ''}<br>
                `;
            }

            populateViewContent(weigher);

            editMode.innerHTML = `
                <div class="content"></div>
                <button class="cancel-btn">Annulla</button>
                <button class="save-btn">Salva</button><br>
                <div class="errors"></div>
            `;

            const populateEditContent = (data) => {
                editMode.querySelector('.content').innerHTML = `
                    <input type="text" name="name" value="${data.name}" class="h4-input"><br>
                    Nodo: <input type="text" name="node" value="${data.node ? data.node : ''}"><br>
                    Peso massimo: <input type="number" name="max_weight" value="${data.max_weight}"><br>
                    Peso minimo: <input type="number" name="min_weight" value="${data.min_weight}"><br>
                    Divisione: <input type="number" name="division" value="${data.division}"><br>
                    Mantieni sessione realtime dopo comando: <input type="checkbox" name="maintaine_session_realtime_after_command" ${data.maintaine_session_realtime_after_command ? 'checked' : ''}><br>
                    Diagnostica prioritaria sul realtime: <input type="checkbox" name="diagnostic_has_priority_than_realtime" ${data.diagnostic_has_priority_than_realtime ? 'checked' : ''}><br>
                    Terminale: <input type="text" name="terminal" value="${data.terminal || 'dgt1'}"><br>
                    In esecuzione: <input type="checkbox" name="run" ${data.run ? 'checked' : ''}><br>                    
                `;
            }

            populateEditContent(weigher);

            const errorDiv = editMode.querySelector('.errors');

            viewMode.querySelector('.delete-btn').addEventListener('click', () => {
                modal.style.display = 'block';
                
                // Rimuovo eventuali vecchi listener
                const newModalConfirm = modalConfirm.cloneNode(true);
                const newModalCancel = modalCancel.cloneNode(true);
                modalConfirm.parentNode.replaceChild(newModalConfirm, modalConfirm);
                modalCancel.parentNode.replaceChild(newModalCancel, modalCancel);

                // Aggiungo i nuovi listener
                newModalConfirm.addEventListener('click', () => {
                    let url_delete = `/config_weigher/instance/node?name=${key}`;
                    if (weigher.node) url_delete += `&node=${weigher.node}`;
                    
                    fetch(url_delete, {
                        method: 'DELETE',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    })
                    .then(res => res.json())
                    .then(response => {
                        if (response.deleted) {
                            li.remove();
                        } else {
                            alert('Errore durante l\'eliminazione');
                        }
                        modal.style.display = 'none';
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('Errore durante l\'eliminazione');
                        modal.style.display = 'none';
                    });
                });

                newModalCancel.addEventListener('click', () => {
                    modal.style.display = 'none';
                });
            });

            viewMode.querySelector('.edit-btn').addEventListener('click', () => {
                viewMode.style.display = 'none';
                editMode.style.display = 'block';
            });

            editMode.querySelector('.cancel-btn').addEventListener('click', () => {
                populateEditContent(weigher);
                errorDiv.innerHTML = '';
                viewMode.style.display = 'block';
                editMode.style.display = 'none';
            });

            editMode.querySelector('.save-btn').addEventListener('click', () => {
                let changedData = {};
                
                const inputs = editMode.querySelectorAll('input');
                inputs.forEach(input => {
                    const originalValue = weigher[input.name];
                    let currentValue;
                    
                    if (input.type === 'checkbox') {
                        currentValue = input.checked;
                    } else if (input.type === 'number') {
                        currentValue = parseInt(input.value);
                    } else {
                        currentValue = input.value !== '' ? input.value : null;
                    }

                    if (currentValue !== originalValue) {
                        changedData[input.name] = currentValue;
                    }
                });

                if (Object.keys(changedData).length > 0) {
                    let url_patch = `/config_weigher/instance/node?name=${key}`;
                    if (weigher.node) url_patch += `&node=${weigher.node}`;
                    fetch(url_patch, {
                        method: 'PATCH',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(changedData)
                    })
                    .then(res => res.json())
                    .then(response => {
                        if ('node' in response) {
                            Object.assign(weigher, response);

                            populateViewContent(response);

                            errorDiv.innerHTML = '';
                            viewMode.style.display = 'block';
                            editMode.style.display = 'none';
                        } else if ("detail" in response) {
                            errorDiv.innerHTML = '';
                            const errors = document.createElement('div');
                            response.detail.forEach(error => {
                                errors.textContent += `${error.msg}\n`;
                            })
                            errorDiv.appendChild(errors);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert(`Errore durante il salvataggio delle modifiche: ${error}`);
                    });
                } else {
                    errorDiv.innerHTML = '';
                    viewMode.style.display = 'block';
                    editMode.style.display = 'none';
                }
            });

            li.appendChild(editMode);
            li.appendChild(viewMode);
            ul.appendChild(li);
        }

        div.appendChild(h3);
        div.appendChild(addButton);
        div.appendChild(ul);
        weighers_config.appendChild(div);
    }
});

// Chiudi il modal se si clicca fuori
window.addEventListener('click', (event) => {
    if (event.target === modal) {
        modal.style.display = 'none';
    } else if (event.target === addModal) {
        addModal.style.display = 'none';
    }
});