const TOKEN_KEY = "cloud_portal_token";

function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
}

async function apiFetch(path, options = {}) {
    const headers = Object.assign({}, options.headers || {});
    const token = getToken();
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    if (options.body && !(options.body instanceof FormData)) {
        headers["Content-Type"] = "application/json";
    }

    const response = await fetch(path, Object.assign({}, options, { headers }));

    if (response.status === 401) {
        clearToken();
        window.location.href = "/login";
        throw new Error("Non autenticato");
    }

    if (!response.ok) {
        let detail = response.statusText;
        try {
            const data = await response.json();
            detail = data.detail || detail;
        } catch (e) {
            // ignore
        }
        throw new Error(detail);
    }

    if (response.status === 204) {
        return null;
    }
    return response.json();
}

async function requireAuth() {
    if (!getToken()) {
        window.location.href = "/login";
        return null;
    }
    try {
        return await apiFetch("/api/auth/me");
    } catch (e) {
        return null;
    }
}

function logout() {
    clearToken();
    window.location.href = "/login";
}

async function renderNav() {
    const nav = document.getElementById("nav");
    if (!nav) return;
    const token = getToken();
    if (!token) {
        nav.innerHTML = `<a href="/login">Accedi</a>`;
        return;
    }
    let me = null;
    try {
        me = await apiFetch("/api/auth/me");
    } catch (e) {
        return;
    }
    const links = [`<a href="/dashboard">Pesate</a>`];
    if (me.is_super_admin) {
        links.push(`<a href="/sites">Siti</a>`);
    }
    links.push(`<span>${me.username}${me.site_name ? " · " + me.site_name : ""}</span>`);
    links.push(`<button id="logout-btn">Esci</button>`);
    nav.innerHTML = links.join("");
    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) logoutBtn.addEventListener("click", logout);
}

document.addEventListener("DOMContentLoaded", renderNav);
