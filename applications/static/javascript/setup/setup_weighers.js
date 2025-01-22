import { list_serial_ports, deleteButtonContent, editButtonContent } from "./setup_utils.js";

const weighers_config = document.getElementById('weighers_config');

fetch('/config_weigher/all/instance')
.then(res => res.json())
.then(data => {
    const addInstance = document.createElement('button');
    addInstance.classList.toggle('container-buttons');
    addInstance.classList.toggle('add-btn');
    addInstance.textContent = 'Aggiungi istanza';
    const addInstanceModal = document.createElement('div');
    addInstanceModal.classList.toggle('modal');

    addInstance.addEventListener('click', () => {
        addInstanceModal.style.display = 'block';
        addInstanceModal.querySelector('.save-btn').disabled = true;
    });

    const populateInstanceModal = () => {
        addInstanceModal.innerHTML = `
            <div class="modal-content">
                <h3>Nome istanza:</h3>
                <form class="content" oninput="document.querySelector('.save-btn').disabled = !this.checkValidity()">
                    <input type="text" name="name" required>
                </form>
                <div class="errors"></div>
                <div class="container-buttons right">                
                    <button class="cancel-btn">Annulla</button>
                    <button class="save-btn" disabled>Salva</button><br>
                </div>
            </div>
        `;

        addInstanceModal.querySelector('.cancel-btn').addEventListener('click', () => {
            addInstanceModal.style.display = 'none';
            addInstanceModal.querySelector('input[type="text"]').value = '';
            addInstanceModal.querySelector('.errors').innerHTML = '';
        })

        addInstanceModal.querySelector('.save-btn').addEventListener('click', () => {
            const errorsDiv = addInstanceModal.querySelector('.errors');
            const name = addInstanceModal.querySelector('input[type="text"]').value;
            fetch(`/config_weigher/instance`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: name,
                    connection: {},
                    time_between_actions: 1
                })
            })
            .then(response => response.json())
            .then(data => {
                errorsDiv.innerHTML = '';
                if ("detail" in data) {
                    data.detail.forEach(error => {
                        errorsDiv.innerHTML += `${error.msg}<br>`;
                    });
                } else {
                    createInstance(name, data);
                    addInstanceModal.style.display = 'none';
                    addInstanceModal.querySelector('input[type="text"]').value = '';
                    addInstanceModal.querySelector('.errors').innerHTML = '';
                }
            })
            .catch(error => {
                alert(`Errore durante l'eliminazione della pesa ${error}`);
            })
        })

        window.addEventListener('click', (event) => {
            if (event.target === addInstanceModal) {
                addInstanceModal.style.display = 'none';
                addInstanceModal.querySelector('input[type="text"]').value = '';
                addInstanceModal.querySelector('.errors').innerHTML = '';
            }
        })
    }

    const createInstance = (key, data) => {
        const div = document.createElement('div');

        let currentTimeBetweenActions = data.time_between_actions;

        div.classList.toggle('div_config');
        div.innerHTML = `
            <h3 class="borders">
                <button class="delete-instance width-fit-content delete-btn">${deleteButtonContent}</button>
                &nbsp;
                <p>Istanza: ${key}</p>
            </h3>
            <div class="containerConnection">
                <div class="borders">
                    <h3>Connessione</h4>
                    <div class="type-connection">
                        <input type="radio" name="connection" value="serial" class="serial"> Seriale &nbsp
                        <input type="radio" name="connection" value="tcp" class="tcp"> Tcp
                    </div>
                    <div class="content-serial"></div>
                    <div class="content-tcp"></div>
                    <div class="container-buttons">
                        <button class="delete-btn">${deleteButtonContent}</button>
                        <button class="edit-btn">${editButtonContent}</button>
                    </div>
                </div>
            </div>
            <button class="addWeigher width-fit-content">Configura pesa</button>
        `;

        const deleteInstanceModal = document.createElement('div');

        deleteInstanceModal.classList.toggle('modal');

        // Aggiungo il contenuto del modal tramite innerHTML
        deleteInstanceModal.innerHTML = `
            <div class="modal-content">
                <h3>Conferma eliminazione</h3>
                <p>Sei sicuro di voler eliminare l'istanza?</p>
                <div class="container-buttons right">
                    <button class="cancel-btn">Annulla</button>
                    <button class="confirm-btn delete-btn">Conferma</button>
                </div>
            </div>
        `;

        deleteInstanceModal.querySelector('.cancel-btn').addEventListener('click', () => {
            deleteInstanceModal.style.display = 'none';
        });

        deleteInstanceModal.querySelector('.confirm-btn').addEventListener('click', () => {
            deleteInstanceModal.style.display = 'none';
            fetch(`/config_weigher/instance?name=${key}`, {
                method: 'DELETE',
            })
            .then(res => res.json())
            .then(data => {
                if (data.deleted) {
                    div.remove();
                }
                else if (data.detail) {
                    alert(`Errore nella cancellazione: ${data.detail}`);
                    console.error(data.detail);
                }
                else {
                    alert(`Errore nella cancellazione: ${data}`);
                    console.error(data);
                }
            })
            .catch(error => {
                alert(`Errore nella cancellazione: ${error}`);
                console.error(error);
            });
        });

        div.querySelector('.delete-instance').addEventListener('click', () => {
            deleteInstanceModal.style.display = 'block';
        });

        window.addEventListener('click', (event) => {
            if (event.target === deleteInstanceModal) {
                deleteInstanceModal.style.display = 'none';
            }
        });

        const deleteConnectionModal = document.createElement('div');

        deleteConnectionModal.classList.toggle('modal');

        // Aggiungo il contenuto del modal tramite innerHTML
        deleteConnectionModal.innerHTML = `
            <div class="modal-content">
                <h3>Conferma eliminazione</h3>
                <p>Sei sicuro di voler eliminare la connessione?</p>
                <div class="container-buttons right">
                    <button class="cancel-btn">Annulla</button>
                    <button class="confirm-btn delete-btn">Conferma</button>
                </div>
            </div>
        `;

        deleteConnectionModal.querySelector('.cancel-btn').addEventListener('click', () => {
            deleteConnectionModal.style.display = 'none';
        });

        deleteConnectionModal.querySelector('.confirm-btn').addEventListener('click', () => {
            deleteConnectionModal.style.display = 'none';
            fetch(`/config_weigher/instance/connection?name=${key}`, {
                method: 'DELETE',
            })
            .then(res => res.json())
            .then(data => {
                if (data.deleted) {
                    containerButtons.querySelector('.delete-btn').style.display = 'none';
                    viewModeSerial.style.display = 'none';
                    viewModeTcp.style.display = 'none';
                    populateEditSerial({"connection": {}});
                    populateEditTcp({"connection": {}});
                } else if (!("deleted" in data)) {
                    alert(`Errore durante l\'eliminazione della connessione: ${data}`);
                }
            })
            .catch(error => {
                alert(`Errore durante l\'eliminazione della connessione: ${error}`);
            });
        });

        window.addEventListener('click', (event) => {
            if (event.target === deleteConnectionModal) {
                deleteConnectionModal.style.display = 'none';
            }
        });

        const containerConnection = div.querySelector('.containerConnection');
        const typeConnection = containerConnection.querySelector('.type-connection');
        const radioSerial = containerConnection.querySelector('.serial');
        const radioTcp = containerConnection.querySelector('.tcp');
        const contentSerial = containerConnection.querySelector('.content-serial');
        const contentTcp = containerConnection.querySelector('.content-tcp');
        const containerButtons = containerConnection.querySelector('.container-buttons');

        typeConnection.style.display = 'none';

        const viewModeSerial = document.createElement('div');
        viewModeSerial.classList.toggle('content');

        const populateViewSerial = (data) => {
            viewModeSerial.innerHTML = `
                Porta seriale: ${data.connection.serial_port_name ? data.connection.serial_port_name : ''}<br>
                Baudrate: ${data.connection.baudrate ? data.connection.baudrate : ''}<br>
                Timeout: ${data.connection.timeout ? data.connection.timeout : ''}<br>
                Esegui comando ogni: ${currentTimeBetweenActions} secondi
            `;
        }

        populateViewSerial(data);

        const editModeSerial = document.createElement('form');
        editModeSerial.oninput = () => {
            editModeSerial.querySelector('.save-btn').disabled = !editModeSerial.checkValidity();
        }
        editModeSerial.classList.toggle('content');
        editModeSerial.style.display = 'none';

        const populateEditSerial = (data) => {
            editModeSerial.innerHTML = `
                <label for="serial_port_name">Porta seriale:</label>
                <select name="serial_port_name" class="selectSerialPort width-50-px" required>
                </select><br>
                <label for="baudrate">Baudrate:</label>
                <select name="baudrate" class="selectBaudrate width-50-px" required>
                    <option></option>
                    <option value="9600" ${data.connection.baudrate === 9600 ? 'selected': ''}>9600</option>
                    <option value="14400" ${data.connection.baudrate === 14400 ? 'selected' : ''}>14400</option>
                    <option value="19200" ${data.connection.baudrate === 19200 ? 'selected' : ''}>19200</option>
                    <option value="38400" ${data.connection.baudrate === 38400 ? 'selected' : ''}>38400</option>
                    <option value="57600" ${data.connection.baudrate === 57600 ? 'selected' : ''}>57600</option>
                    <option value="115200" ${data.connection.baudrate === 115200 ? 'selected' : ''}>115200</option>
                </select><br>
                <label for="timeout">Timeout:</label>
                <input type="number" min="0.1" max="10" step="0.1" name="timeout" class="width-50-px" value="${data.connection.timeout ? data.connection.timeout : ''}" required><br>
                <label for "time_between_actions">Esegui azione ogni:</label>
                <input type="number" min="0.1" max="10" step="0.1" name="time_between_actions" class="width-50-px" value="${currentTimeBetweenActions}" required><br>
                <div class="errors"></div>
                <div class="container-buttons">
                    <button class="cancel-btn">Annulla</button>
                    <button class="save-btn">Salva</button>
                </div>
            `;

            const option = document.createElement('option');
            editModeSerial.querySelector('.selectSerialPort').appendChild(option);

            for (let port of list_serial_ports) {
                const option = document.createElement('option');
                option.value = port.port;
                option.innerHTML = port.port;
                if ("serial_port_name" in data.connection && data.connection.serial_port_name == port.port) {
                    option.selected = true;
                }
                editModeSerial.querySelector('.selectSerialPort').appendChild(option);
            }

            editModeSerial.oninput();

            editModeSerial.querySelector('.cancel-btn').addEventListener('click', (event) => {
                event.preventDefault();
                typeConnection.style.display = 'none';
                editModeSerial.style.display = 'none';
                editModeTcp.style.display = 'none';
                containerButtons.style.display = 'flex';
                radioSerial.checked = false;
                if (!("ip" in data.connection)) {
                    radioSerial.checked = true;
                    if ("serial_port_name" in data.connection) {
                        viewModeSerial.style.display = 'block';
                    }
                } else {
                    radioTcp.checked = true;
                    viewModeTcp.style.display = 'block';
                }
            });

            editModeSerial.querySelector('.save-btn').addEventListener('click', (event) => {
                event.preventDefault();
                editModeSerial.querySelector('.errors').innerHTML = '';
                fetch(`/config_weigher/instance/connection?name=${key}`, {
                    method: 'DELETE',
                })
                .then(res => res.json())
                .then(res => {
                    const newTimeBetweenActions = Number(editModeSerial.querySelector('input[name="time_between_actions"]').value);
                    if (newTimeBetweenActions != currentTimeBetweenActions) {
                        fetch(`/config_weigher/instance/time_between_actions/${newTimeBetweenActions}?name=${key}`, {
                            method: 'PATCH',
                            headers: {
                                'Content-Type': 'application/json'
                            }
                        })
                        .then(res => res.json())
                        .then(res => currentTimeBetweenActions = res.time_between_actions)
                        .catch(error => console.error(error));
                    }
                    return res;
                })
                .then(_ => {
                    fetch(`/config_weigher/instance/connection?name=${key}`, {
                        method: 'PATCH',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            serial_port_name: editModeSerial.querySelector('select[name="serial_port_name"]').value,
                            baudrate: Number(editModeSerial.querySelector('select[name="baudrate"]').value),
                            timeout: Number(editModeSerial.querySelector('input[name="timeout"]').value)
                        })
                    })
                    .then(res => res.json())
                    .then(data => {
                        if ('connected' in data) {
                            typeConnection.style.display = 'none';
                            editModeSerial.style.display = 'none';
                            editModeTcp.style.display = 'none';
                            containerButtons.style.display = 'flex';
                            containerButtons.querySelector('.delete-btn').style.display = 'block';
                            containerButtons.querySelector('.edit-btn').innerHTML = editButtonContent;
                            viewModeSerial.style.display = 'block';
                            populateEditSerial({"connection": data});
                            populateViewSerial({"connection": data});
                            populateEditTcp({"connection": data});
                            if ("ip" in data) {
                                viewModeTcp.style.display = 'block';
                            } else {
                                viewModeSerial.style.display = 'block';
                            }
                        } else if ('detail' in data) {
                            data.detail.forEach(error => {
                                if (error.loc.includes('SerialPort')) {
                                    const message = error.msg.replace('Value error, ', '');
                                    editModeSerial.querySelector('.errors').innerHTML += `${message}<br>`;
                                }
                            })
                        } else {
                            alert(`Errore durante la modifica della connessione: ${data}`);
                        }
                    })
                    .catch(error => {
                        alert(`Errore durante la modifica della connessione: ${error}`);
                    })
                })
            });
        }

        populateEditSerial(data);

        contentSerial.appendChild(viewModeSerial);
        contentSerial.appendChild(editModeSerial);

        const viewModeTcp = document.createElement('div');
        viewModeTcp.classList.toggle('content');

        const populateViewTcp = (data) => {
            viewModeTcp.innerHTML = `
                Indirizzo IP: ${data.connection.ip ? data.connection.ip : ''}<br>
                Porta: ${data.connection.port ? data.connection.port : ''}<br>
                Timeout: ${data.connection.timeout ? data.connection.timeout : ''}<br>
                Esegui comando ogni: ${currentTimeBetweenActions} secondi
            `;
        }

        populateViewTcp(data);

        const editModeTcp = document.createElement('form');
        editModeTcp.oninput = () => {
            editModeTcp.querySelector('.save-btn').disabled = !editModeTcp.checkValidity();
        }
        editModeTcp.classList.toggle('content');
        editModeTcp.style.display = 'none';

        const populateEditTcp = (data) => {
            editModeTcp.innerHTML = `
                <label for="ip">Indirizzo IP:</label>
                <input type="text" name="ip" class="width-50-px" value="${data.connection.ip ? data.connection.ip : ''}" required><br>
                <label for="port">Porta:</label>
                <input type="number" min="1" max="65535" step="1" name="port" class="width-50-px" value="${data.connection.port ? data.connection.port : ''}" oninput="this.value = this.value && this.value > 0 ? Math.abs(this.value) : ''" required><br>
                <label for="timeout">Timeout:</label>
                <input type="number" min="0.1" max="10" step="0.1" name="timeout" class="width-50-px" value="${data.connection.timeout ? data.connection.timeout : ''}" oninput="this.value = this.value && this.value > 0 ? Math.abs(this.value) : ''" required><br>
                <label for="time_between_actions">Esegui comando ogni:</label>
                <input type="number" min="0.1" max="10" step="0.1" name="time_between_actions" class="width-50-px" value="${currentTimeBetweenActions}" required><br>
                <div class="container-buttons">
                    <button class="cancel-btn">Annulla</button>
                    <button class="save-btn">Salva</button>
                </div>
            `;

            editModeTcp.oninput();

            editModeTcp.querySelector('.cancel-btn').addEventListener('click', (event) => {
                event.preventDefault();
                typeConnection.style.display = 'none';
                editModeSerial.style.display = 'none';
                editModeTcp.style.display = 'none';
                containerButtons.style.display = 'flex';
                radioTcp.checked = false;
                if (!("ip" in data.connection)) {
                    radioSerial.checked = true;
                    if ("serial_port_name" in data.connection) {
                        viewModeSerial.style.display = 'block';
                    }
                } else {
                    radioTcp.checked = true;
                    viewModeTcp.style.display = 'block';
                }
            });

            editModeTcp.querySelector('.save-btn').addEventListener('click', (event) => {
                event.preventDefault();
                fetch(`/config_weigher/instance/connection?name=${key}`, {
                    method: 'DELETE',
                })
                .then(res => res.json())
                .then(res => {
                    const newTimeBetweenActions = Number(editModeTcp.querySelector('input[name="time_between_actions"]').value);
                    if (newTimeBetweenActions != currentTimeBetweenActions) {
                        fetch(`/config_weigher/instance/time_between_actions/${newTimeBetweenActions}?name=${key}`, {
                            method: 'PATCH',
                            headers: {
                                'Content-Type': 'application/json'
                            }
                        })
                        .then(res => res.json())
                        .then(res => currentTimeBetweenActions = res.time_between_actions)
                        .catch(error => console.error(error));
                    }
                    return res;
                })
                .then(_ => {
                    fetch(`/config_weigher/instance/connection?name=${key}`, {
                        method: 'PATCH',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            ip: editModeTcp.querySelector('input[name="ip"]').value,
                            port: Number(editModeTcp.querySelector('input[name="port"]').value),
                            timeout: Number(editModeTcp.querySelector('input[name="timeout"]').value)
                        })
                    })
                    .then(res => res.json())
                    .then(data => {
                        if ('connected' in data) {
                            typeConnection.style.display = 'none';
                            editModeSerial.style.display = 'none';
                            editModeTcp.style.display = 'none';
                            containerButtons.style.display = 'flex';
                            containerButtons.querySelector('.delete-btn').style.display = 'block';
                            viewModeTcp.style.display = 'block';
                            populateEditTcp({"connection": data});
                            populateViewTcp({"connection": data});
                            populateEditSerial({"connection": data});
                        } else {
                            alert(`Errore durante la modifica della connessione: ${data}`);}
                    })
                    .catch(error => {
                        alert(`Errore durante la modifica della connessione: ${error}`);
                    })
                })
            });
        }

        populateEditTcp(data);

        contentTcp.appendChild(viewModeTcp);
        contentTcp.appendChild(editModeTcp);

        contentSerial.style.display = 'none';
        contentTcp.style.display = 'none';

        containerButtons.querySelector('.delete-btn').addEventListener('click', () => {
            deleteConnectionModal.style.display = 'block';
        });

        containerButtons.querySelector('.edit-btn').addEventListener('click', () => {
            typeConnection.style.display = 'block';
            containerButtons.style.display = 'none';
            if (viewModeSerial.style.display == 'block') {
                radioSerial.checked = true;
                viewModeSerial.style.display = 'none';
                editModeSerial.style.display = 'block';
            } else if (viewModeTcp.style.display == 'block') {
                radioTcp.checked = true;
                viewModeTcp.style.display = 'none';
                editModeTcp.style.display = 'block';
            } else {
                radioSerial.checked = true;
                editModeSerial.style.display = 'block';
            }
        });

        contentSerial.style.display = 'block';
        contentTcp.style.display = 'block';

        if ('serial_port_name' in data.connection) {
            radioSerial.checked = true;
            viewModeSerial.style.display = 'block';
            viewModeTcp.style.display = 'none';
        } else if ('ip' in data.connection) {
            radioTcp.checked = true;
            viewModeTcp.style.display = 'block';
            viewModeSerial.style.display = 'none';
        } else {
            containerButtons.querySelector('.delete-btn').style.display = 'none';
            radioSerial.checked = true;
            viewModeSerial.style.display = 'none';
            viewModeTcp.style.display = 'none';
        }

        radioSerial.addEventListener('click', () => {
            editModeSerial.style.display = 'block';
            editModeTcp.style.display = 'none';
        });

        radioTcp.addEventListener('click', () => {
            editModeTcp.style.display = 'block';
            editModeSerial.style.display = 'none';
        });

        const addWeigherModal = document.createElement('div');
        const ul = document.createElement('ul');

        addWeigherModal.classList.toggle('modal');
        
        addWeigherModal.innerHTML = `
            <div class="modal-content">
                <h3>Aggiungi pesa</h3>
                <form class="content">
                </form>
                <div class="errors"></div>
                <div class="container-buttons right">
                    <button class="cancel-btn">Annulla</button>
                    <button class="save-btn" disabled>Salva</button>
                </div>
            </div>
        `;

        const addWeigherForm = addWeigherModal.querySelector('form');
        const errorAddWeigher = addWeigherModal.querySelector('.errors');

        addWeigherForm.oninput = () => {
            addWeigherModal.querySelector('.save-btn').disabled = !addWeigherForm.checkValidity();
        }

        const populateAddContent = () => {
            addWeigherForm.innerHTML = 
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
                    <option value="egt-af03">egt-af03</option>
                </select><br>
                In esecuzione: <input type="checkbox" name="run" checked><br>`;
        
            errorAddWeigher.innerHTML = '';
        }        
        
        populateAddContent();

        addWeigherModal.querySelector('.cancel-btn').addEventListener('click', () => {
            addWeigherModal.style.display = 'none';
            populateAddContent();
        });

        addWeigherModal.querySelector('.save-btn').addEventListener('click', () => {
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
            .catch(error => {
                alert(`Errore nella configurazione della pesa: ${error}`);
                console.error(error);
            });
        })

        const addWeigher = (weigher) => {
            const li = document.createElement('li');
            li.classList.toggle('borders');
            const viewMode = document.createElement('div');
            const editMode = document.createElement('div');
            editMode.style.display = 'none';

            viewMode.innerHTML = `
                <div class="content"></div>
                <div class="container-buttons">
                    <button class="delete-btn">${deleteButtonContent}</button>
                    <button class="edit-btn">${editButtonContent}</button>
                </div>
            `;

            const populateViewContent = (data) => {
                viewMode.querySelector('.content').innerHTML = `
                    <h4>${data.name}</h4>
                    Nodo: ${data.node ? data.node : ''}<br>
                    Peso massimo: ${data.max_weight}<br>
                    Peso minimo: ${data.min_weight}<br>
                    Divisione: ${data.division}<br>
                    Terminale: ${data.terminal}<br>
                    In esecuzione: ${data.run}<br>
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
                    Terminale:<br>
                    <select name="terminal" required>
                        <option value="dgt1" ${data.terminal === "dgt1" ? 'selected': ''}>dgt1</option>
                        <option value="egt-af03" ${data.terminal === "egt-af03" ? 'selected': ''}>egt-af03</option>
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

            const br = document.createElement('br');

            li.appendChild(editMode);
            li.appendChild(viewMode);
            li.appendChild(deleteWeigherModal);
            ul.appendChild(li);
            ul.appendChild(br);

            // Chiudi il modal se si clicca fuori
            window.addEventListener('click', (event) => {
                if (event.target === deleteWeigherModal) {
                    deleteWeigherModal.style.display = 'none';
                }
            });
        }

        for (let weigher of data['nodes']) {
            addWeigher(weigher);
        }

        div.querySelector('.addWeigher').addEventListener('click', () => {
            addWeigherModal.style.display = 'block';
        });

        // Chiudi il modal se si clicca fuori
        window.addEventListener('click', (event) => {
            if (event.target === addWeigherModal) {
                addWeigherModal.style.display = 'none';
                populateAddContent();
            }
        });

        div.appendChild(deleteInstanceModal);
        div.appendChild(deleteConnectionModal);
        div.appendChild(addWeigherModal);
        div.appendChild(ul);
        weighers_config.appendChild(div);
    }

    populateInstanceModal();

    weighers_config.appendChild(addInstance);
    weighers_config.appendChild(addInstanceModal);

    for (let key in data) {
        createInstance(key, data[key]);
    }
});