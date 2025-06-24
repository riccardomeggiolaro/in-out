import { dataUser } from '../auth.js';
import { recoveryPasswordButtonContent } from "./setup_utils.js";

const profile_config = document.getElementById('profile_config');

const div = document.createElement('div');
div.classList.toggle('div_config');

const details = document.createElement('div');
details.classList.toggle('borders');
details.style.marginLeft = '0px';

const h2 = document.createElement('h2');
h2.textContent = `Benvenuto, ${dataUser.username}!`;
div.appendChild(h2);

const description = document.createElement('p');
description.textContent = `Descrizione: ${dataUser.description}`;

const level = document.createElement('p');
let textLevel;
if (dataUser.level === 3) {
    textLevel = 'Super amministratore';
} else if (dataUser.level === 2) {
    textLevel = 'Amministratore';
} else {
    textLevel = 'Utente';
}
level.textContent = `Livello: ${textLevel}`;

const containerButtons = document.createElement('div');
containerButtons.classList.toggle('container-buttons');

const passwordButton = document.createElement('button');
passwordButton.classList.toggle('edit-btn');
passwordButton.innerHTML = recoveryPasswordButtonContent;

const editPasswordModal = document.createElement('div');

editPasswordModal.classList.toggle('modal');

// Aggiungo il contenuto del modal tramite innerHTML
editPasswordModal.innerHTML = `
    <div class="modal-content">
        <h3>Conferma modifica</h3>
        <p>Inserisci nuova password (Min 8 caratteri):</p>
        <form class="content">
        </form>
        <div class="container-buttons right">
            <button class="cancel-btn">Annulla</button>
            <button class="save-btn" disabled>Salva</button>
        </div>
    </div>
`;

const editUserForm = editPasswordModal.querySelector('form');

const cancelEditBtn = editPasswordModal.querySelector('.cancel-btn');

const saveEditBtn = editPasswordModal.querySelector('.save-btn');

editUserForm.oninput = () => {
    saveEditBtn.disabled = !editUserForm.checkValidity();
}

const populateEditContent = () => {
    editUserForm.innerHTML = `
        <input type="password" name="password" minlength="8" required><br>
    `;
    editPasswordModal.querySelector('.save-btn').disabled = true;
}

populateEditContent();

cancelEditBtn.addEventListener('click', () => {
    editPasswordModal.style.display = 'none';
    populateEditContent();
})

saveEditBtn.addEventListener('click', () => {
    fetch('/api/auth/me', {
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
            editPasswordModal.style.display = 'none';
            
            populateEditContent();
        } else {
            console.error(`Errore nella modifica dell'utente: ${res.status}`);
        }
        return res.json();
    })
    .catch(error => {
        alert(`Errore nella modifica dell'utente: ${error}`);
        console.error(error);
    });
})

passwordButton.addEventListener('click', () => {
    editPasswordModal.style.display = 'block';
});

window.addEventListener('click', (event) => {
    if (event.target === editPasswordModal) {
        editPasswordModal.style.display = 'none';
    }
})

containerButtons.appendChild(passwordButton);

details.appendChild(description);
details.appendChild(level);
details.appendChild(containerButtons);
details.appendChild(editPasswordModal);

div.appendChild(details);

profile_config.appendChild(div);