let currentOffset = 0;
const pageSize = 50;
let sitesById = {};
let me = null;

function fmtDate(value) {
    if (!value) return "";
    return new Date(value).toLocaleString("it-IT");
}

function fmtWeight(value) {
    if (value === null || value === undefined) return "";
    return `${value} kg`;
}

function buildQuery(offset) {
    const form = document.getElementById("filters");
    const data = new FormData(form);
    const params = new URLSearchParams();
    for (const [key, value] of data.entries()) {
        if (value) params.set(key, value);
    }
    params.set("limit", pageSize);
    params.set("offset", offset);
    return params.toString();
}

function renderRows(rows) {
    const body = document.getElementById("weighings-body");
    body.innerHTML = rows
        .map(
            (row) => `
        <tr>
            <td>${fmtDate(row.date_created)}</td>
            <td class="site-col ${me && me.is_super_admin ? "" : "hidden"}">${sitesById[row.site_id] || row.site_id}</td>
            <td>${row.plate || ""}</td>
            <td>${row.subject_name || ""}</td>
            <td>${row.material || ""}</td>
            <td>${fmtWeight(row.weight1)}</td>
            <td>${fmtWeight(row.weight2)}</td>
            <td>${fmtWeight(row.net_weight)}</td>
            <td>${row.status || ""}</td>
        </tr>`
        )
        .join("");
}

async function loadWeighings(offset = 0) {
    currentOffset = offset;
    const query = buildQuery(offset);
    const result = await apiFetch(`/api/weighings?${query}`);
    renderRows(result.data);
    const page = Math.floor(offset / pageSize) + 1;
    const totalPages = Math.max(1, Math.ceil(result.total / pageSize));
    document.getElementById("page-info").textContent = `Pagina ${page} di ${totalPages} (${result.total} pesate)`;
    document.getElementById("prev-page").disabled = offset === 0;
    document.getElementById("next-page").disabled = offset + pageSize >= result.total;
}

async function init() {
    me = await requireAuth();
    if (!me) return;

    if (me.is_super_admin) {
        document.querySelectorAll(".site-col").forEach((el) => el.classList.remove("hidden"));
        const siteFilter = document.getElementById("site-filter");
        siteFilter.classList.remove("hidden");
        try {
            const sites = await apiFetch("/api/sites");
            sitesById = Object.fromEntries(sites.map((s) => [s.id, s.name]));
            siteFilter.innerHTML =
                `<option value="">Tutti i siti</option>` +
                sites.map((s) => `<option value="${s.id}">${s.name}</option>`).join("");
        } catch (e) {
            // non super admin fallback silenzioso
        }
    }

    document.getElementById("filters").addEventListener("submit", (event) => {
        event.preventDefault();
        loadWeighings(0);
    });
    document.getElementById("prev-page").addEventListener("click", () => loadWeighings(Math.max(0, currentOffset - pageSize)));
    document.getElementById("next-page").addEventListener("click", () => loadWeighings(currentOffset + pageSize));

    await loadWeighings(0);
}

init();
