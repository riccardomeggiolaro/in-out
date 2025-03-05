let currentPage = 1;
let rowsPerPage = 10;
let totalRows = 0; // Aggiungi questa variabile per tenere traccia del numero totale di righe
let urlPath = null;

function updateTable() {
    const offset = (currentPage - 1) * rowsPerPage; // Calcola l'offset in base alla pagina
    fetch(`${urlPath}?limit=${rowsPerPage}&offset=${offset}`)
    .then(res => res.json())
    .then(res => {
        totalRows = res.total_rows; // Aggiorna il numero totale di righe dalla risposta
        populateTable(res.data); // Popola la tabella con i dati
        updatePageSelect(); // Aggiorna la selezione della pagina
        // Mostra il numero totale di righe
        document.getElementById("total-rows").textContent = `Totale righe: ${totalRows}`;
    });
}

function updatePageSelect() {
    const totalPages = Math.ceil(totalRows / rowsPerPage); // Calcola il numero totale di pagine
    const pageSelect = document.getElementById("page-select");
    const previousPage = document.getElementById("previous-page");
    const nextPage = document.getElementById("next-page");
    pageSelect.innerHTML = "";
    for (let i = 1; i <= totalPages; i++) {
        let option = document.createElement("option");
        option.value = i;
        option.textContent = `Pagina ${i}`;
        if (i === currentPage) option.selected = true;
        pageSelect.appendChild(option);
    }
    if (totalPages === 0) {
        previousPage.disabled = true;
        nextPage.disabled = true;
    } else {
        if (pageSelect.value == totalPages) nextPage.disabled = true;
        else nextPage.disabled = false;
        if (pageSelect.value == 1) previousPage.disabled = true;
        else previousPage.disabled = false;
    }
}

function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        updateTable();
    }
}

function nextPage() {
    const totalPages = Math.ceil(totalRows / rowsPerPage); // Usa `totalRows` per calcolare il numero di pagine
    if (currentPage < totalPages) {
        currentPage++;
        updateTable();
    }
}

function goToPage() {
    currentPage = parseInt(document.getElementById("page-select").value);
    updateTable();
}

function changeRowsPerPage() {
    rowsPerPage = parseInt(document.getElementById("rows-per-page").value);
    currentPage = 1; // Quando cambia il numero di righe per pagina, torna alla prima pagina
    updateTable();
}

function populateTable(data) {
    const table = document.querySelector("tbody");
    table.innerHTML = ""; // Pulisce la tabella esistente
    data.forEach(item => {
        const row = document.createElement("tr");
        Object.entries(item).forEach(([key, value]) => {
            // Salta l'id
            if (key !== "id") {
                const cell = document.createElement("td");
                cell.textContent = value;
                row.appendChild(cell);
            }
        });
        table.appendChild(row);
    });
}