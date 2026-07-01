let sitesCache = [];

function showNewKey(site) {
    const banner = document.getElementById("new-key-banner");
    banner.classList.remove("hidden");
    banner.innerHTML = `Nuova API key per <strong>${site.name}</strong> (mostrata una sola volta, copiala ora):<br>${site.api_key}`;
}

function renderSites(sites) {
    sitesCache = sites;
    const body = document.getElementById("sites-body");
    body.innerHTML = sites
        .map(
            (s) => `
        <tr>
            <td>${s.name}</td>
            <td>${s.code}</td>
            <td>${s.api_key_prefix}...</td>
            <td>${s.active ? "Sì" : "No"}</td>
            <td>
                <button data-action="rotate" data-id="${s.id}">Rigenera key</button>
                <button data-action="toggle" data-id="${s.id}" data-active="${s.active}">${s.active ? "Disattiva" : "Attiva"}</button>
            </td>
        </tr>`
        )
        .join("");

    const select = document.getElementById("user-site-select");
    select.innerHTML = sites.map((s) => `<option value="${s.id}">${s.name}</option>`).join("");

    body.querySelectorAll("button[data-action='rotate']").forEach((btn) =>
        btn.addEventListener("click", async () => {
            const site = await apiFetch(`/api/sites/${btn.dataset.id}/rotate-key`, { method: "POST" });
            showNewKey(site);
            await loadSites();
        })
    );
    body.querySelectorAll("button[data-action='toggle']").forEach((btn) =>
        btn.addEventListener("click", async () => {
            const active = btn.dataset.active !== "true";
            await apiFetch(`/api/sites/${btn.dataset.id}/active?active=${active}`, { method: "PATCH" });
            await loadSites();
        })
    );
}

async function loadSites() {
    const sites = await apiFetch("/api/sites");
    renderSites(sites);
    if (sites.length) {
        await loadUsers(sites[0].id);
    }
}

async function loadUsers(siteId) {
    const users = await apiFetch(`/api/sites/${siteId}/users`);
    const body = document.getElementById("users-body");
    const site = sitesCache.find((s) => s.id === Number(siteId));
    body.innerHTML = users
        .map(
            (u) => `
        <tr>
            <td>${u.username}</td>
            <td>${site ? site.name : u.site_id}</td>
            <td><button data-action="delete-user" data-site="${siteId}" data-user="${u.id}">Elimina</button></td>
        </tr>`
        )
        .join("");
    body.querySelectorAll("button[data-action='delete-user']").forEach((btn) =>
        btn.addEventListener("click", async () => {
            await apiFetch(`/api/sites/${btn.dataset.site}/users/${btn.dataset.user}`, { method: "DELETE" });
            await loadUsers(btn.dataset.site);
        })
    );
}

async function init() {
    const me = await requireAuth();
    if (!me) return;
    if (!me.is_super_admin) {
        window.location.href = "/dashboard";
        return;
    }

    await loadSites();

    document.getElementById("create-site-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = new FormData(event.target);
        const site = await apiFetch("/api/sites", {
            method: "POST",
            body: JSON.stringify({ name: form.get("name"), code: form.get("code") }),
        });
        showNewKey(site);
        event.target.reset();
        await loadSites();
    });

    document.getElementById("user-site-select").addEventListener("change", (event) => loadUsers(event.target.value));

    document.getElementById("create-user-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = new FormData(event.target);
        const siteId = form.get("site_id");
        await apiFetch(`/api/sites/${siteId}/users`, {
            method: "POST",
            body: JSON.stringify({ username: form.get("username"), password: form.get("password") }),
        });
        event.target.reset();
        await loadUsers(siteId);
    });
}

init();
