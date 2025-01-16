import { dataUser } from '/static/javascript/auth.js';
import { deleteButtonContent, recoveryPasswordButtonContent, list_printer_names } from "./setup_utils.js";

const users_config = document.getElementById('users_config');

setTimeout(() => {
    fetch('/auth/users')
    .then(res => res.json())
    .then(res => {
        const addButton = document.createElement('button');
        addButton.classList.toggle('container-buttons');
        addButton.classList.toggle('add-btn');
        addButton.style.marginLeft = '0px';
        addButton.textContent = 'Aggiungi utente';
        const addUserModal = document.createElement('div');

        addUserModal.classList.toggle('modal');
        
        addUserModal.innerHTML = `
            <div class="modal-content">
                <h3>Aggiungi utente</h3>
                <form class="content">
                </form>
                <div class="errors"></div>
                <div class="container-buttons right">
                    <button class="cancel-btn">Annulla</button>
                    <button class="save-btn" disabled>Salva</button>
                </div>
            </div>
        `;

        const addUserForm = addUserModal.querySelector('form');
        const errorAddUser = addUserModal.querySelector('.errors');

        addButton.addEventListener('click', () => {
            addUserModal.style.display = 'block';
            addUserModal.querySelector('.save-btn').disabled = true;
        });

        addUserForm.oninput = () => {
            addUserModal.querySelector('.save-btn').disabled = !addUserForm.checkValidity();
        }

        const populateAddContent = () => {
            addUserForm.innerHTML = `
                Username: (Min 3 caratteri)<br>
                <input type="text" name="username" value="" minlength="3" required><br>
                Password: (Min 8 caratteri)<br>
                <input type="password" name="password" value="" minlength="8" required><br>
                Livello:<br>
                <select name="level" required>
                    <option value="1">Utente</option>
                    <option value="2">Amministratore</option>
                </select><br>
                Descrizione:<br>
                <input type="text" name="description" value="" required><br>
                Stampante associata:<br>
                <select name="printer_name">
                    <option></option>
                </select><br>
            `;
            errorAddUser.innerHTML = '';

            const printerSelect = addUserForm.querySelector('select[name="printer_name"]');
            list_printer_names.forEach(printer => {
                const option = document.createElement('option');
                option.value = printer.nome;
                option.textContent = printer.nome;
                printerSelect.appendChild(option);
            })
        }        
        populateAddContent();
        addUserModal.querySelector('.cancel-btn').addEventListener('click', () => {
            addUserModal.style.display = 'none';
            populateAddContent();
        });

        addUserModal.querySelector('.save-btn').addEventListener('click', () => {
            let data = {};
                
            const inputs = addUserForm.querySelectorAll('input');
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

            const selections = addUserForm.querySelectorAll('select');
            selections.forEach(selection => {
                if (selection.value !== '') {
                    data[selection.name] = selection.value;   
                }
            })

            fetch(`/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(response => {
                if ('username' in response) {
                    populateAddContent();
                    addUserModal.style.display = 'none';
                    addUser(response);
                } else if ('detail' in response) {
                    errorAddUser.innerHTML = '';
                    response.detail.forEach(error => {
                        const errorMessage = `${error.msg}<br>`.replace('Value error, ', '');
                        errorAddUser.innerHTML += errorMessage;
                    })
                }
            })
            .catch(error => {
                alert(`Errore nella registrazione: ${error}`);
                console.error(error);
            });
        })
        window.addEventListener('click', (event) => {
            if (event.target === addUserModal) {
                addUserModal.style.display = 'none';
                populateAddContent();
            }
        })
        const div = document.createElement('div');
        div.classList.toggle('div_config');
        const ul = document.createElement('ul');
        ul.style.marginLeft = '0px';
        const addUser = (data) => {
            const li = document.createElement('li');
            li.classList.toggle('borders');
            let level;
            if (data.level === 3) {
                level = 'Super amministratore';
            } else if (data.level === 2) {
                level = 'Amministratore';
            } else {
                level = 'Utente';
            }
            li.innerHTML = `
            <h4>${data.username}</h4>
                <p>Livello: ${level}</p>
                <p>Descrizione: ${data.description}</p>
                <p>Stampante associata: ${data.printer_name ? data.printer_name : ''}</p>
            `;

            if (data.username !== dataUser.username) {
                li.innerHTML += `
                    <div class="container-buttons">
                        <button class="delete-btn">${deleteButtonContent}</button>
                        <button class="edit-btn">${recoveryPasswordButtonContent}</button>
                    </div>
                `;

                const deleteUserModal = document.createElement('div');

                deleteUserModal.classList.toggle('modal');
        
                // Aggiungo il contenuto del modal tramite innerHTML
                deleteUserModal.innerHTML = `
                    <div class="modal-content">
                        <h3>Conferma eliminazione</h3>
                        <p>Sei sicuro di voler eliminare l'utente <b>${data.username}?</b></p>
                        <div class="container-buttons right">
                            <button class="cancel-btn">Annulla</button>
                            <button class="confirm-btn">Conferma</button>
                        </div>
                    </div>
                `;

                deleteUserModal.querySelector('.cancel-btn').addEventListener('click', () => {
                    deleteUserModal.style.display = 'none';
                })

                deleteUserModal.querySelector('.confirm-btn').addEventListener('click', () => {
                    fetch(`/auth/user/${data.id}`, {
                        method: 'DELETE',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    })
                    .then(res => {
                        if (res.status === 200 || res.status === 404) {
                            li.remove();
                            br.remove();
                            deleteUserModal.style.display = 'none';
                        } else {
                            const error = res.json();
                            alert(`Errore nell'eliminazione dell'utente: ${error}`);
                            console.error(error);
                        }
                    })
                    .catch(error => {
                        alert(`Errore nell'eliminazione dell'utente: ${error}`);
                        console.error(error);
                    });
                })

                li.querySelector('.delete-btn').addEventListener('click', () => {
                    deleteUserModal.style.display = 'block';
                })

                const editUserModal = document.createElement('div');

                editUserModal.classList.toggle('modal');
        
                // Aggiungo il contenuto del modal tramite innerHTML
                editUserModal.innerHTML = `
                    <div class="modal-content">
                        <h3>Conferma modifica</h3>
                        <p>Nuova password per l'utente <b>${data.username}</b> (Min 8 caratteri):</p>
                        <form class="content">
                        </form>
                        <div class="container-buttons right">
                            <button class="cancel-btn">Annulla</button>
                            <button class="save-btn" disabled>Salva</button>
                        </div>
                    </div>
                `;

                const editUserForm = editUserModal.querySelector('form');

                const cancelEditBtn = editUserModal.querySelector('.cancel-btn');

                const saveEditBtn = editUserModal.querySelector('.save-btn');

                editUserForm.oninput = () => {
                    saveEditBtn.disabled = !editUserForm.checkValidity();
                }

                const populateEditContent = () => {
                    editUserForm.innerHTML = `
                        <input type="password" name="password" minlength="8" required><br>
                    `;
                    editUserModal.querySelector('.save-btn').disabled = true;
                }

                populateEditContent();

                cancelEditBtn.addEventListener('click', () => {
                    editUserModal.style.display = 'none';
                    populateEditContent();
                })

                saveEditBtn.addEventListener('click', () => {
                    fetch(`/auth/user/password/${data.id}`, {
                        method: 'PATCH',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            password: editUserForm.querySelector('input[name="password"]').value
                        })
                    })
                    .then(res => {
                        if (res.status === 200) {
                            editUserModal.style.display = 'none';
                            populateEditContent();
                        } else if (res.status === 404) {
                            const error = res.json();
                            alert(`Errore nella modifica dell'utente: ${error}`);
                            console.error(error);
                            li.remove();
                            br.remove();
                            editUserModal.style.display = 'none';
                            populateEditContent();
                        }
                        return res.json();
                    })
                    .catch(error => {
                        alert(`Errore nella modifica dell'utente: ${error}`);
                        console.error(error);
                    });
                })

                li.querySelector('.edit-btn').addEventListener('click', () => {
                    editUserModal.style.display = 'block';
                });

                window.addEventListener('click', (event) => {
                    if (event.target === deleteUserModal) {
                        deleteUserModal.style.display = 'none';
                    } else if (event.target === editUserModal) {
                        editUserModal.style.display = 'none';
                    }
                })

                li.appendChild(deleteUserModal);    
                li.appendChild(editUserModal);
            }
            const br = document.createElement('br');
            ul.appendChild(li);
            ul.appendChild(br);
        }
        res.forEach(user => {
            addUser(user);
        })
        div.appendChild(ul);
        users_config.appendChild(addButton);
        users_config.appendChild(addUserModal);
        users_config.appendChild(div);
    })
}, 1000);