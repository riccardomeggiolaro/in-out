// Load navbar
fetch('navbar.html')
.then(response => response.text())
.then(data => {
    // Inserisci l'HTML modificato
    document.getElementById('navbar-container').innerHTML = data;

    // Colora il link attivo
    const currentPath = window.location.pathname;
    document.querySelectorAll('.side-menu-navbar li').forEach(li => {
        const link = li.querySelector('a');
        if (link && link.getAttribute('href') === currentPath) {
            link.classList.add('active-link-navbar');
            if (link.href.includes("/social-reason", "/vehicle", "/material")) {
                document.querySelector('.arrow-dropdown-navbar').classList.toggle('up');
                document.querySelector('.dropdown-navbar').classList.toggle('active');
            }
        }
    })
});

function toggleMenu(element) {
    element.querySelector('.arrow-container-navbar').classList.toggle('up');
    element.nextElementSibling.classList.toggle('active');
    element.previousElementSibling.classList.toggle('active');
}

function removeMenu(element) {
    element.nextElementSibling.querySelector('.arrow-container-navbar').classList.remove('up');
    element.nextElementSibling.nextElementSibling.classList.remove('active');
    element.classList.remove('active');
}

function toggleDropdown(element) {
    element.stopPropagation();
    let dropdown = element.currentTarget.querySelector(".dropdown-navbar");
    let arrow = element.currentTarget.querySelector(".arrow-dropdown-navbar");
    dropdown.classList.toggle("active");
    arrow.classList.toggle("up");
}