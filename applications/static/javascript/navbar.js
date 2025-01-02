// Load navbar
fetch('navbar.html')
.then(response => response.text())
.then(data => {
    // Inserisci l'HTML modificato
    document.getElementById('navbar-container').innerHTML = data;

    // Colora il link attivo
    const currentPath = window.location.pathname;
    document.querySelectorAll('.side-menu li').forEach(li => {
        const link = li.querySelector('a');
        if (link && link.getAttribute('href') === currentPath) {
            link.classList.add('active-link');
        }
    })
});

function toggleMenu(element) {
    element.querySelector('.arrow-container').classList.toggle('up');
    element.nextElementSibling.classList.toggle('active');
    element.previousElementSibling.classList.toggle('active');
}

function removeMenu(element) {
    element.nextElementSibling.querySelector('.arrow-container').classList.remove('up');
    element.nextElementSibling.nextElementSibling.classList.remove('active');
    element.classList.remove('active');
}