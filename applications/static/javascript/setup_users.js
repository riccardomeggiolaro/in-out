const users_config = document.getElementById('users_config');

const brLiUsers = document.createElement('br');

setTimeout(() => {
    fetch('/auth/users')
    .then(res => res.json())
    .then(res => {
        const addButton = document.createElement('button');
        addButton.classList.toggle('container-buttons');
        addButton.classList.toggle('add-btn');
        addButton.textContent = 'Aggiungi utente';
        const div = document.createElement('div');
        div.classList.toggle('div_config');
        const ul = document.createElement('ul');
        ul.style.marginLeft = '0px';
        res.forEach(user => {
            const li = document.createElement('li');
            li.classList.toggle('borders');
            li.textContent = user.username;
            ul.appendChild(li);
            ul.appendChild(brLiUsers);
        })
        div.appendChild(addButton);
        div.appendChild(ul);
        users_config.appendChild(div);
    })
}, 1000);