import { dataUser } from '../auth.js';
import { editButtonContent, deleteButtonContent } from "./setup_utils.js";

const ssh_config = document.getElementById('ssh_config');

const div = document.createElement('div');
div.classList.toggle('div_config');

const addButton = document.createElement('button');
addButton.classList.toggle('container-buttons');
addButton.classList.toggle('add-btn');
addButton.style.marginLeft = '0px';
addButton.textContent = 'Aggiungi connessione';

const addConnectionModal = document.createElement('div');

addConnectionModal.classList.toggle('modal');

addConnectionModal.innerHTML = `
    <div class="modal-content">
        <h3>Aggiungi connessione</h3>
        <form class="content">
        </form>
        <div class="errors"></div>
        <div class="container-buttons right">
            <button class="cancel-btn">Annulla</button>
            <button class="save-btn" disabled>Salva</button>
        </div>
    </div>
`;

const addSshForm = addConnectionModal.querySelector('form');
const errorAddConnection = addConnectionModal.querySelector('.errors');

addButton.addEventListener('click', () => {
    addConnectionModal.style.display = 'block';
    addConnectionModal.querySelector('.save-btn').disabled = true;
});

addSshForm.oninput = () => {
    addConnectionModal.querySelector('.save-btn').disabled = !addSshForm.checkValidity();
}

const populateAddContent = () => {
    addSshForm.innerHTML = `
        Username: (Min 3 caratteri)<br>
        <input type="text" name="username" value="" minlength="3" required><br>
        Password: (Min 8 caratteri)<br>
        <input type="password" name="password" value="" minlength="8" required><br>
        Livello:<br>
        <select name="level" required></select><br>
        Descrizione:<br>
        <input type="text" name="description" value="" required><br>
        Stampante associata:<br>
        <select name="printer_name">
            <option></option>
        </select><br>
    `;
    errorAddConnection.innerHTML = '';

    const levelSelect = addSshForm.querySelector('select[name="level"]');
    const option1 = document.createElement('option');
    option1.value = 1;
    option1.textContent = 'Utente';
    const option2 = document.createElement('option');
    option2.value = 2;
    option2.textContent = 'Amministratore';
    levelSelect.appendChild(option1);
    if (dataUser.level > 2) {
        levelSelect.appendChild(option2);
    }
}        
populateAddContent();
addConnectionModal.querySelector('.cancel-btn').addEventListener('click', () => {
    addConnectionModal.style.display = 'none';
    populateAddContent();
});

addConnectionModal.querySelector('.save-btn').addEventListener('click', () => {
    let data = {};
        
    const inputs = addSshForm.querySelectorAll('input');
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

    const selections = addSshForm.querySelectorAll('select');
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
            addConnectionModal.style.display = 'none';
            addUser(response);
        } else if ('detail' in response) {
            errorAddConnection.innerHTML = '';
            response.detail.forEach(error => {
                const errorMessage = `${error.msg}<br>`.replace('Value error, ', '');
                errorAddConnection.innerHTML += errorMessage;
            })
        }
    })
    .catch(error => {
        alert(`Errore nella registrazione: ${error}`);
        console.error(error);
    });
})

window.addEventListener('click', (event) => {
    if (event.target === addConnectionModal) {
        addConnectionModal.style.display = 'none';
        populateAddContent();
    }
})

addButton.addEventListener('click', () => {
    addConnectionModal.style.display = 'block';
    addConnectionModal.querySelector('.save-btn').disabled = true;
});

const details = document.createElement('div');
details.classList.toggle('borders');
details.style.marginLeft = '0px';

fetch('/api/tunnel_connections/ssh_reverse_tunneling')
.then(res => res.json())
.then(data => {

})

div.appendChild(details);
div.appendChild(addConnectionModal);

ssh_config.appendChild(addButton);
ssh_config.appendChild(div);