fetch('navbar.html')
.then(response => response.text())
.then(async (data) => {
    const token = localStorage.getItem('token');
    if (!token) window.location.href = '/login';
    
    try {
        // Esegui entrambe le chiamate in parallelo e attendi il completamento
        const [userRes, configRes] = await Promise.all([
            fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            }).then(res => res.json()),
            fetch('/api/config-weigher/configuration', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            }).then(res => res.json())
        ]);
        
        // PRIMA inserisci l'HTML nel DOM
        document.getElementById('navbar-container').innerHTML = data;
        
        // POI gestisci i risultati dell'autenticazione
        if (userRes.level < 3) {
            const users = document.querySelectorAll(".page-of-users");
            users.forEach(user => user.style.display = "none");
        }
        if (userRes.level < 4) {
            const configurations = document.querySelectorAll(".page-of-configuration");
            configurations.forEach(configuration => configuration.style.display = "none");
        }
        const p = document.getElementById("hi-session-user");
        if (p) p.textContent = `Ciao, ${userRes.username}`;
        const pDesktop = document.getElementById("hi-session-user-desktop");
        if (pDesktop) pDesktop.textContent = `Ciao, ${userRes.username}`;

        document.querySelector("#ver").textContent = `v${configRes.ver}`;

        // Gestisci i risultati della configurazione
        if (!configRes.use_recordings) {
            const pageOfRecordings = document.querySelectorAll(".page-of-recordings");
            pageOfRecordings.forEach(recordings => recordings.style.display = "none");
        }
        if (!configRes.use_reservation) {
            const pageOfReservation = document.querySelectorAll(".page-of-reservation");
            pageOfReservation.forEach(reservation => reservation.style.display = "none");
        }
        
        // Colora il link attivo
        const currentPath = window.location.pathname;
        document.querySelectorAll('.side-menu-navbar li').forEach(li => {
            const link = li.querySelector('a');
            if (link && link.getAttribute('href') === currentPath) {
                link.classList.add('active-link-navbar');
                if (["/subject", "/vector", "/driver", "/vehicle", "/material"].includes(window.location.pathname)) {
                    const arrow = document.querySelector('.arrow-dropdown-navbar');
                    const dropdown = document.querySelector('.dropdown-navbar');
                    if (arrow) arrow.classList.toggle('up');
                    if (dropdown) dropdown.classList.toggle('active');
                }
            }
        });
        document.querySelectorAll('.navbar-desktop li').forEach(li => {
            const link = li.querySelector('a');
            if (link && link.getAttribute('href') === currentPath) {
                link.classList.add('active-link-navbar');
                if (["/subject", "/vector", "/driver", "/vehicle", "/material"].includes(window.location.pathname)) {
                    const arrow = document.querySelector('.arrow-dropdown-navbar');
                    const dropdown = document.querySelector('.dropdown-navbar');
                    if (arrow) arrow.classList.toggle('up');
                    if (dropdown) dropdown.classList.toggle('active');
                }
            }
        });
        
    } catch (error) {
        console.error('Errore nel caricamento della navbar:', error);
    }
});

function toggleMenu(element) {
    const hamburger = element.querySelector('.hamburger-navbar');
    hamburger.classList.toggle('open');
    element.nextElementSibling.classList.toggle('active');
    element.previousElementSibling.classList.toggle('active');
}

function removeMenu(element) {
    const hamburger = element.nextElementSibling.querySelector('.hamburger-navbar');
    hamburger.classList.remove('open');
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

function logout() {
    localStorage.removeItem('token');
    window.location.href = '/login';
}