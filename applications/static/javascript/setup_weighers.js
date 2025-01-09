const weighers_config = document.getElementById('weighers_config');

fetch('/config_weigher/all/instance')
.then(res => res.json())
.then(data => {
    for (let key in data) {
        const div = document.createElement('div');
        const addWeigherModal = document.createElement('div');
        const ul = document.createElement('ul');

        div.classList.toggle('div_config');
        div.innerHTML = `
            <h3 class="instance">Istanza ${key}</h3>
            <button class="addWeigher">Configura pesa</button>
        `;

        addWeigherModal.classList.toggle('modal');
        
        addWeigherModal.innerHTML = `
            <div class="modal-content">
                <h3>Configura pesa</h3>
                <form class="content" oninput="document.querySelector('#modalAddWeigherConfirm').disabled = !this.checkValidity()">
                </form>
                <div class="errors"></div>
                <div class="container-buttons">
                    <button id="modalAddWeigherCancel" class="modal-cancel-button">Annulla</button>
                    <button id="modalAddWeigherConfirm" class="modal-confirm-button" disabled>Salva</button>
                </div>
            </div>
        `;

        const errorAddWeigher = addWeigherModal.querySelector('.errors');

        const populateAddContent = () => {
            addWeigherModal.querySelector('.content').innerHTML = 
                `Nome:<br>
                <input type="text" name="name" value="" required><br>
                Nodo: (facoltativo)<br>
                <input type="text" name="node" value=""><br>
                Peso massimo:<br>
                <input type="number" name="max_weight" min="1" oninput="this.value = this.value && this.value > 0 ? Math.abs(this.value) : ''" required><br>
                Peso minimo:<br>
                <input type="number" name="min_weight" min="1" oninput="this.value = this.value && this.value > 0 ? Math.abs(this.value) : ''" required><br>
                Divisione:<br>
                <input type="number" name="division" min="1" oninput="this.value = this.value && this.value > 0 ? Math.abs(this.value) : ''" required><br>
                Terminale:<br>
                <select name="terminal" required>
                    <option value="dgt1" selected>dgt1</option>
                </select><br>
                Mantieni sessione realtime dopo comando: <input type="checkbox" name="maintaine_session_realtime_after_command" checked><br>
                Diagnostica prioritaria sul realtime: <input type="checkbox" name="diagnostic_has_priority_than_realtime" checked><br>
                In esecuzione: <input type="checkbox" name="run" checked><br>`;
        
            // Aggiungi validazione in tempo reale per gli input
            const inputs = addWeigherModal.querySelectorAll('input[required]');
            inputs.forEach(input => {
                input.addEventListener('input', () => {
                    // Verifica se il campo è valido o meno
                    if (input.value.trim() === "") {
                        input.setCustomValidity('Questo campo è obbligatorio');
                    } else {
                        input.setCustomValidity('');
                    }
        
                    // Forza il controllo di validità del campo
                    input.reportValidity();
                });
            });

            addWeigherModal.querySelector('.errors').innerHTML = '';
            addWeigherModal.querySelector('#modalAddWeigherConfirm').disabled = true;
        }        
        
        populateAddContent();

        addWeigherModal.querySelector('#modalAddWeigherCancel').addEventListener('click', () => {
            addWeigherModal.style.display = 'none';
            populateAddContent();
        });

        addWeigherModal.querySelector('#modalAddWeigherConfirm').addEventListener('click', () => {
            let data = {};
                
            const inputs = addWeigherModal.querySelectorAll('input');
            inputs.forEach(input => {
                let currentValue;
                
                if (input.type === 'checkbox') {
                    currentValue = input.checked;
                } else if (input.type === 'number') {
                    currentValue = parseInt(input.value);
                } else {
                    currentValue = input.value !== '' ? input.value : null;
                }

                data[input.name] = currentValue;
            });

            const selections = addWeigherModal.querySelectorAll('select');
            selections.forEach(selection => {
                data[selection.name] = selection.value;
            })

            fetch(`/config_weigher/instance/node?name=${key}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(response => {
                if ('node' in response) {
                    addWeigher(response);
                    addWeigherModal.querySelector('.content').innerHTML = '';
                    populateAddContent();
                    addWeigherModal.style.display = 'none';
                } else if ("detail" in response) {
                    errorAddWeigher.innerHTML = '';
                    const errors = document.createElement('div');
                    response.detail.forEach(error => {
                        errors.innerHTML += `${error.msg}<br>`;
                    })
                    errorAddWeigher.appendChild(errors);
                }
            })
            .catch(error => {console.error(error)})
        })

        const addWeigher = (weigher) => {
            const li = document.createElement('li');
            
            const viewMode = document.createElement('div');
            const editMode = document.createElement('div');
            editMode.style.display = 'none';

            viewMode.innerHTML = `
                <div class="content"></div>
                <div class="container-buttons">
                    <button class="delete-btn">Elimina</button>
                    <button class="edit-btn">Modifica</button>
                </div>
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
                <form class="content" oninput="document.querySelector('.save-btn').disabled = !this.checkValidity()">
                </form>
                <div class="container-buttons">                
                    <button class="cancel-btn">Annulla</button>
                    <button class="save-btn">Salva</button><br>
                </div>
                <div class="errors"></div>
            `;

            const populateEditContent = (data) => {
                editMode.querySelector('.content').innerHTML = `
                    <input type="text" name="name" value="${data.name}" class="h4-input" required><br>
                    Nodo: <input type="text" name="node" value="${data.node ? data.node : ''}"><br>
                    Peso massimo: <input type="number" name="max_weight" value="${data.max_weight}" min="1" oninput="this.value = this.value && this.value > 0 ? Math.abs(this.value) : ''" required><br>
                    Peso minimo: <input type="number" name="min_weight" value="${data.min_weight}" min="1" oninput="this.value = this.value && this.value > 0 ? Math.abs(this.value) : ''" required><br>
                    Divisione: <input type="number" name="division" value="${data.division}" min="1" oninput="this.value = this.value && this.value > 0 ? Math.abs(this.value) : ''" required><br>
                    Mantieni sessione realtime dopo comando: <input type="checkbox" name="maintaine_session_realtime_after_command" ${data.maintaine_session_realtime_after_command ? 'checked' : ''} required><br>
                    Diagnostica prioritaria sul realtime: <input type="checkbox" name="diagnostic_has_priority_than_realtime" ${data.diagnostic_has_priority_than_realtime ? 'checked' : ''} required><br>
                    Terminale:<br>
                    <select name="terminal" required>
                        <option value="dgt1" ${data.terminal === "dgt1" ? 'selected': ''}>dgt1</option>
                        </select><br>
                    In esecuzione: <input type="checkbox" name="run" ${data.run ? 'checked' : ''} required><br>
                `;
            }

            populateEditContent(weigher);

            const errorEditWeigher = editMode.querySelector('.errors');

            viewMode.querySelector('.delete-btn').addEventListener('click', () => {
                deleteWeigherModal.style.display = 'block';
            });

            viewMode.querySelector('.edit-btn').addEventListener('click', () => {
                viewMode.style.display = 'none';
                editMode.style.display = 'block';
            });

            editMode.querySelector('.cancel-btn').addEventListener('click', () => {
                populateEditContent(weigher);
                errorEditWeigher.innerHTML = '';
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

                const selections = editMode.querySelectorAll('select');
                selections.forEach(selection => {
                    const originalValue = weigher[selection.name];
                    const currentValue = selection.value;

                    if (currentValue !== originalValue) {
                        changedData[selection.name] = currentValue;
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

                            errorEditWeigher.innerHTML = '';
                            viewMode.style.display = 'block';
                            editMode.style.display = 'none';
                        } else if ("detail" in response) {
                            errorEditWeigher.innerHTML = '';
                            const errors = document.createElement('div');
                            response.detail.forEach(error => {
                                errors.innerHTML += `${error.msg}<br>`;
                            })
                            errorEditWeigher.appendChild(errors);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert(`Errore durante il salvataggio delle modifiche: ${error}`);
                    });
                } else {
                    errorEditWeigher.innerHTML = '';
                    viewMode.style.display = 'block';
                    editMode.style.display = 'none';
                }
            });

            const deleteWeigherModal = document.createElement('div');

            deleteWeigherModal.classList.toggle('modal');

            // Aggiungo il contenuto del modal tramite innerHTML
            deleteWeigherModal.innerHTML = `
                <div class="modal-content">
                    <h3>Conferma eliminazione</h3>
                    <p>Sei sicuro di voler eliminare la configurazione della pesa?</p>
                    <div class="container-buttons right">
                        <button class="modalDeleteWeigherCancel">Annulla</button>
                        <button class="modalDeleteWeigherConfirm delete-btn">Conferma</button>
                    </div>
                </div>
            `;
    
            deleteWeigherModal.querySelector('.modalDeleteWeigherCancel').addEventListener('click', () => {
                deleteWeigherModal.style.display = 'none';
            });

            deleteWeigherModal.querySelector('.modalDeleteWeigherConfirm').addEventListener('click', () => {
                let delete_url = `/config_weigher/instance/node?name=${key}`;
                if (weigher.node !== null) {
                    delete_url += `&node=${weigher.node}`;
                }
                fetch(delete_url, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(response => {
                    if (response.deleted) {
                        li.remove();
                    }
                })
                .catch(error => {
                    alert(`Errore durante l'eliminazione della pesa ${error}`);
                })
                .finally(_ => {
                    deleteWeigherModal.style.display = 'none';
                })
            });

            li.appendChild(editMode);
            li.appendChild(viewMode);
            li.appendChild(deleteWeigherModal);
            ul.appendChild(li);

            // Chiudi il modal se si clicca fuori
            window.addEventListener('click', (event) => {
                if (event.target === deleteWeigherModal) {
                    deleteWeigherModal.style.display = 'none';
                }
            });
        }

        for (let weigher of data[key]['nodes']) {
            addWeigher(weigher);
        }

        div.querySelector('.addWeigher').addEventListener('click', () => {
            addWeigherModal.style.display = 'block';
        });

        div.appendChild(addWeigherModal);
        div.appendChild(ul);
        weighers_config.appendChild(div);

        // Chiudi il modal se si clicca fuori
        window.addEventListener('click', (event) => {
            if (event.target === addWeigher) {
                addWeigher.style.display = 'none';
                populateAddContent();
            }
        });
    }
});