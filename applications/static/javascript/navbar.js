fetch('navbar.html')
.then(response => response.text())
.then(data => {
    const token = localStorage.getItem('token');
    if (!token) window.location.href = '/login';
    fetch('/api/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
    })
    .then(res => res.json())
    .then(res => {
        if (res.level < 2) {
            const users = document.querySelectorAll(".page-of-users");
            users.forEach(user => user.style.display = "none");
        }
        if (res.level < 4) {
            const setups = document.querySelectorAll(".page-of-setup");
            setups.forEach(setup => setup.style.display = "none");
        }
        const p = document.getElementById("hi-session-user");
        p.textContent = `Ciao, ${res.username}`;
        const pDesktop = document.getElementById("hi-session-user-desktop");
        pDesktop.textContent = `Ciao, ${res.username}`;
    });
    // Inserisci l'HTML modificato
    document.getElementById('navbar-container').innerHTML = data;
    // Colora il link attivo
    const currentPath = window.location.pathname;
    document.querySelectorAll('.side-menu-navbar li').forEach(li => {
        const link = li.querySelector('a');
        if (link && link.getAttribute('href') === currentPath) {
            link.classList.add('active-link-navbar');
            if (["/subject", "/vector", "/driver", "/vehicle", "/material"].includes(window.location.pathname)) {
                document.querySelector('.arrow-dropdown-navbar').classList.toggle('up');
                document.querySelector('.dropdown-navbar').classList.toggle('active');
            }
        }
    })
    document.querySelectorAll('.navbar-desktop li').forEach(li => {
        const link = li.querySelector('a');
        if (link && link.getAttribute('href') === currentPath) {
            link.classList.add('active-link-navbar');
            if (["/subject", "/vector", "/driver", "/vehicle", "/material"].includes(window.location.pathname)) {
                document.querySelector('.arrow-dropdown-navbar').classList.toggle('up');
                document.querySelector('.dropdown-navbar').classList.toggle('active');
            }
        }
    });
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