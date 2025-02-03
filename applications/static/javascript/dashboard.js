setTimeout(() => {
    document.querySelector('.loading').style.display = 'none';
    document.querySelector('.container').style.display = 'flex';
}, 1000)

let currentPopup;
let currentInput;

let connected;

let selectedIdVehicle;
let selectedIdCustomer;
let selectedIdSupplier;
let selectedIdMaterial;

let selectedIdWeight;
let dataInExecution;

let isRefreshing = false;

let pathname = '';

pathname = '/gateway';

let lastSlashIndex = window.location.pathname.lastIndexOf('/');

pathname = lastSlashIndex !== -1 ? pathname.substring(0, lastSlashIndex) : pathname;

let snackbarTimeout;

let data = {
    status: undefined,
    type: undefined,
    net_weight: undefined,
    gross_weight: undefined,
    tare: undefined,
    unite_measure: undefined
};

let _data;
let reconnectTimeout;

let url = new URL(window.location.href);
let currentWeigherPath = null;

const buttons = document.querySelectorAll("button");
const myNumberInput = document.getElementById("myNumberInput");
const container = document.querySelector('.ins');
const listIn = document.querySelector('.list-in');
const selectedIdWeigher = document.querySelector('.list-weigher');
// Usa un MutationObserver per rilevare i cambiamenti nei contenuti
const observer = new MutationObserver(() => updateStyle());

document.addEventListener('DOMContentLoaded', async () => {
    updateStyle();
    fetch('/config_weigher/all/instance')
    .then(res => res.json())
    .then(res => {
        const currentWeigherPath = localStorage.getItem('currentWeigherPath');
        let selected = false;
        for (let instance in res) {
            for (let weigher in res[instance]["nodes"]) {
                const option = document.createElement('option');
                option.value = `?instance_name=${instance}&weigher_name=${weigher}`;
                option.innerText = `${weigher}`;
                if (option.value === currentWeigherPath) {
                    option.selected = true
                    selected = true;
                };
                selectedIdWeigher.appendChild(option);
            }
        }
        if (selected === false) selectedIdWeigher.selectedIndex = 0;
        // Innesca l'evento 'change' manualmente
        selectedIdWeigher.dispatchEvent(new Event('change'));
    })
    await populateListIn();
});

selectedIdWeigher.addEventListener('change', (event) => {
    currentWeigherPath = event.target.value;
    if (currentWeigherPath) {
        closeWebSocket();
        document.getElementById('netWeight').innerText = "N/A";
        document.getElementById('uniteMisure').innerText = "N/A";
        document.getElementById('tare').innerText = "N/A";
        document.getElementById('status').innerText = "N/A";
        connectWebSocket(`command_weigher/realtime${currentWeigherPath}`, updateUIRealtime);
        getData(currentWeigherPath);
        localStorage.setItem('currentWeigherPath', currentWeigherPath);
    }
});

// Aggiorna lo stile quando la finestra viene ridimensionata
window.addEventListener('resize', updateStyle);
observer.observe(listIn, { childList: true, subtree: true });

// Aggiungi gli event listener per gli eventi online e offline
window.addEventListener('online', updateOnlineStatus);
window.addEventListener('offline', updateOnlineStatus);

window.onbeforeunload = function() {
    isRefreshing = true; // Imposta il flag prima del refresh
    clearTimeout(reconnectTimeout);
};

// Chiudi il popup quando si fa clic all'esterno
window.onclick = function(event) {
    const popup = document.getElementById(currentPopup);
    if (event.target === popup) {
        closePopup(currentPopup);
    }
};

function updateStyle() {
    // Confronta l'altezza della lista e del contenitore
    if (listIn.scrollHeight > container.clientHeight) {
        listIn.style.justifyContent = 'flex-start'; // Rimuovi il centraggio
    }
}

async function getData(path) {
    await fetch(`/data_in_execution/data_in_execution${path}`)
    .then(res => {
        if (res.status === 404) {
            alert("La pesa selezionata non è presente nella configurazione perché potrebbe essere stata cancellata, è necessario aggiornare la pagina.");
        }
        return res.json();
    })
    .then(res => {
        dataInExecution = res["data_in_execution"];
        const obj = res["data_in_execution"];
        if (obj.vehicle.id) selectedIdVehicle = obj.vehicle.id;
        if (obj.customer.id) selectedIdCustomer = obj.customer.id;
        if (obj.supplier.id) selectedIdSupplier = obj.supplier.id;
        if (obj.material.id) selectedIdMaterial = obj.material.id;
        document.querySelector('#currentDescriptionVehicle').value = obj.vehicle.name ? obj.vehicle.name : '';
        document.querySelector('#currentPlateVehicle').value = obj.vehicle.plate ? obj.vehicle.plate : '';
        document.querySelector('#currentNameSocialReasonCustomer').value = obj.customer.name ? obj.customer.name : '';
        document.querySelector('#currentNameSocialReasonSupplier').value = obj.supplier.name ? obj.supplier.name : '';
        document.querySelector('#currentMaterial').value = obj.material.name ? obj.material.name : '';
        document.querySelector('#currentNote').value = obj.note ? obj.note : '';            
        selectedIdWeight = res["id_selected"]["id"];
    })
    .catch(error => console.error('Errore nella fetch:', error));
}

async function populateListIn() {
    const listIn = document.querySelector('.list-in');
    const items = document.querySelectorAll('.list-in li');

    listIn.innerHTML = '';

    await fetch('/historic_data/weighings/in')
    .then(res => res.json())
    .then(data => {
        data.forEach(item => {
            const li = document.createElement('li');
            if (item.selected == true && item.id !== selectedIdWeight) li.style.background = 'lightgrey';
            li.textContent = `${item.plate || item.customer || item.supplier || item.id} - ${item.weigher}`;
            li.setAttribute('data-id', item.id);
            if (item.id == selectedIdWeight) li.classList.add('selected');
            li.addEventListener('click', async () => {
                let obj =  {
                    data_in_execution: {                                    
                    },
                    id_selected: {
                        id: item.id
                    }
                }
                if (item.id == selectedIdWeight) obj.id_selected.id = -1;
                await fetch(`/data_in_execution/data_in_execution?instance_name=1&weigher_name=P1`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(obj)
                })
                .then(res => res.json())
                .catch(error => console.error(error));
            })
            listIn.appendChild(li);
        })
    })
    .then(() => {
        const selected = document.querySelector('.list-in li.selected');
        if (selected) {
            selected.scrollIntoView({
                behavior: 'instant',
                block: 'nearest',
                inline: 'start'
            });
        }
    })
    .catch(error => console.error('Errore nella fetch:', error));
}

function scrollToSelectedItem() {
    const selectedItem = document.querySelector('.selected');
    if (selectedItem) {
        selectedItem.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
        inline: 'start'
        });
    }
}

function setDataInExecutionOnCLick(anagrafic, key, value) {
    let requestBody;
    if (key) {
        requestBody = JSON.stringify({
            data_in_execution: {
                [anagrafic]: {
                    [key]: value
                }
            }
        })
    } else {
        requestBody = JSON.stringify({
            data_in_execution: {
                [anagrafic]: value
            }
        })
    }
    closePopup();
    fetch(`/data_in_execution/data_in_execution?instance_name=1&weigher_name=P1`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json'
        },
        body: requestBody
    })
    .then(res => res.json())
    .catch(error => console.error('Errore nella fetch:', error));
}

async function showSuggestions(name_list, inputHtml, filter, inputValue, data, popup, showList, condition = null, valueCondition = null) {
    const suggestionsList = document.getElementById(showList);
    suggestionsList.innerHTML = ""; // Pulisce la lista precedente

    let currentId;
    let anagrafic_to_set;

    // Opzionale: salva l'ID dell'elemento selezionato
    if (showList === 'suggestionsListPlateVehicle' || showList === 'suggestionsListDescriptionVehicle') {
        currentId = selectedIdVehicle;
        anagrafic_to_set = 'vehicle';
    } else if (showList === 'suggestionsListNameSocialReasonCustomer') {
        currentId = selectedIdCustomer;
        anagrafic_to_set = 'customer';
    } else if (name_list === 'suggestionsListNameSocialReasonSupplier') {
        currentId = selectedIdSupplier;
        anagrafic_to_set = 'supplier';
    } else if (name_list === 'suggestionsListMaterial') {
        currentId = selectedIdMaterial;
        anagrafic_to_set = 'material';
    }

    let url = `/anagrafic/list/${name_list}`;

    if (inputValue) url += `?${filter}=${inputValue}`;

    // Eseguire una chiamata HTTP per ottenere la lista
    const response = await fetch(url)
    .then(response => response.json())
    .catch(error => console.error(error)); // Sostituisci con l'URL del tuo endpoint

    response.forEach(suggestion => {
        if (suggestion.selected !== true || suggestion.id === currentId) {
            const li = document.createElement("li");

            li.onclick = () => {
                closePopup();
                fetch(`/data_in_execution/data_in_execution?instance_name=1&weigher_name=P1`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        [anagrafic_to_set]: {
                            id: parseInt(suggestion.id)
                        }
                    })
                })
                .then(res => res.json())
                .catch(error => console.error(error));
            };

            let text = highlightText(suggestion, inputValue, filter);
            for (const [key, value] of Object.entries(suggestion)) {
                if (value && key !== filter && key !== 'selected' && key !== 'id') text += `  -   ${value}`;
            }
            li.innerHTML = text; // Evidenzia il testo
            li.dataset.id = suggestion.id

            if (suggestion.id == currentId) {
                li.classList.add('selected');
            }

            suggestionsList.appendChild(li);                    
        }
    });

    const selected = suggestionsList.querySelector('.selected');
    if (selected) {
        selected.scrollIntoView({
            behavior: 'instant',
            block: 'nearest',
            inline: 'start'
        });
    }
}

function highlightText(suggestion, input, filter) {
    const regex = new RegExp(`(${input})`, 'gi'); // Regex per evidenziare
    return suggestion[filter] ? suggestion[filter].replace(regex, `<span class="highlight">$1</span>`) : '';
}

function changeContent(type, value) {
    document.getElementById('header').innerHTML = `${type} <span class="arrow">▼</span>`;
    isCustomerSupplier = value;
    console.log(isCustomerSupplier)
}

function updateOnlineStatus() {
    if (location.protocol === "https:") {
        console.error("WebSocket error. Trying to reconnect...");
        document.querySelector('.loading').style.display = 'flex';
        document.querySelector('.container').style.display = 'none';
        attemptReconnect();
    }
}

myNumberInput.onkeydown = function(event) {
    // Controlla se il tasto premuto è una freccia, Backspace, o altre combinazioni speciali
    const validKeys = [
        'Backspace', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Control', 'Meta', 'Tab'
    ];

    // Permetti la selezione di tutto (Ctrl + A)
    if (event.ctrlKey && event.key === 'a') {
        return; // Non fare nulla, consenti l'azione
    }

    // Permetti anche la combinazione Ctrl (per altri scopi)
    if (event.ctrlKey || event.metaKey) {
        return; // Non fare nulla, consenti l'azione
    }

    // Controlla se il tasto è un numero o una chiave valida
    if (isNaN(event.key) && !validKeys.includes(event.key)) {
        event.preventDefault(); // Blocca il tasto
    }
};

// script.js
function showSnackbar(message) {
    const snackbar = document.getElementById("snackbar");
    snackbar.textContent = message; // Imposta il messaggio
    snackbar.className = "show"; // Aggiungi la classe "show"

    // Cancella il timeout precedente se esiste
    if (snackbarTimeout) {
        clearTimeout(snackbarTimeout);
    }

    // Dopo 5 secondi, nascondi lo snackbar
    snackbarTimeout = setTimeout(() => {
        if (snackbar.className === "show") {
            snackbar.className = snackbar.className.replace("show", ""); // Rimuovi la classe
        }
    }, 5000); // Durata in millisecondi
}

function openPopup(name, input) {
    currentPopup = name;
    currentInput = input;
    const popup = document.getElementById(name);
    const popupContent = popup.querySelector(".popup-content");
    popup.style.display = "flex"; // Mostra il popup
    setTimeout(() => {
        popupContent.classList.add("show"); // Aggiungi la classe per mostrare
    }, 10); // Breve ritardo per assicurarsi che il display sia impostato
}

function closePopup() {
    const popup = document.getElementById(currentPopup);
    const popupContent = popup.querySelector(".popup-content");
    
    const input = document.getElementById(currentInput);
    input.value = "";

    // Rimuovi la classe per nascondere
    popupContent.classList.remove("show");
    
    // Aspetta il tempo di transizione prima di nascondere il popup
    setTimeout(() => {
        popup.style.display = "none"; // Nascondi il popup
        myNumberInput.value = "";
    }, 300); // Tempo della transizione
}

function connectWebSocket(path, exe) {
    // Ottieni la base URL del dominio corrente
    let baseUrl = window.location.origin + pathname;

    baseUrl = baseUrl.replace(/^http/, (match) => match === 'http' ? 'ws' : 'wss');

    // Costruisci l'URL WebSocket
    const websocketUrl = `${baseUrl}/${path}`;

    _data = new WebSocket(websocketUrl);

    _data.addEventListener('message', (e) => {
        exe(e);
    });

    _data.addEventListener('open', () => {
        enableAllElements();
    })

    _data.addEventListener('error', () => {
        if (!isRefreshing) {
            attemptReconnect(path);
            disableAllElements();
        }
    });

    _data.addEventListener('close', () => {
        if (!isRefreshing) {
            attemptReconnect(path);
            disableAllElements();
        }
    });
}

function attemptReconnect(path) {
    closeWebSocket();
    reconnectTimeout = setTimeout(() => {
        connectWebSocket(path, updateUIRealtime);
    }, 3000);
}

function closeWebSocket() {
    clearTimeout(reconnectTimeout);
    if (_data) {
        _data.close(); // Chiude la connessione WebSocket
        _data = null;  // Imposta _data a null per indicare che la connessione è chiusa
        console.log('Connessione WebSocket chiusa');
    }
}

function updateUIRealtime(e) {
    const obj = JSON.parse(e.data);
    if (obj.command_in_executing) {
        if (obj.command_in_executing == "TARE") showSnackbar("Tara");
        if (obj.command_in_executing == "PRESETTARE") showSnackbar("Preset tara");
        if (obj.command_in_executing == "ZERO") showSnackbar("Zero");
        if (obj.command_in_executing == "WEIGHING") {
            showSnackbar("Pesando...");
            buttons.forEach(button => {
                button.disabled = true;
                button.classList.add("disabled-button"); // Aggi
            });
        }                    
    } else if (obj.weight_executed) {
        if (obj.weight_executed.pid != "") { 
            showSnackbar("Pesata eseguita! Identificativo: " + obj.weight_executed.pid);
            populateListIn();
        } else { 
            showSnackbar("Pesata fallita!");
        }
        buttons.forEach(button => {
            button.disabled = false;
            button.classList.remove("disabled-button"); // Aggi
        });
    } else if (obj.tare) {
        data = obj;
        document.getElementById('tare').innerText = data.tare !== undefined ? data.tare : 'N/A';
        document.getElementById('netWeight').innerText = data.net_weight !== undefined ? data.net_weight : "N/A";
        document.getElementById('uniteMisure').innerText = data.unite_measure !== undefined ? data.unite_measure : 'N/A';
        document.getElementById('status').innerText = data.status !== undefined ? data.status : 'N/A';
    } else if (obj.data_in_execution) {
        dataInExecution = obj.data_in_execution;
        selectedIdVehicle = obj.data_in_execution.vehicle.id;
        selectedIdCustomer = obj.data_in_execution.customer.id;
        selectedIdSupplier = obj.data_in_execution.supplier.id;
        selectedIdMaterial = obj.data_in_execution.material.id;
        document.querySelector('#currentDescriptionVehicle').value = obj.data_in_execution.vehicle.name ? obj.data_in_execution.vehicle.name : '';
        document.querySelector('#currentPlateVehicle').value = obj.data_in_execution.vehicle.plate ? obj.data_in_execution.vehicle.plate : '';
        document.querySelector('#currentNameSocialReasonCustomer').value = obj.data_in_execution.customer.name ? obj.data_in_execution.customer.name : '';
        document.querySelector('#currentNameSocialReasonSupplier').value = obj.data_in_execution.supplier.name ? obj.data_in_execution.supplier.name : '';
        document.querySelector('#currentMaterial').value = obj.data_in_execution.material.name ? obj.data_in_execution.material.name : '';
        document.querySelector('#currentNote').value = obj.data_in_execution.note ? obj.data_in_execution.note : '';
        if (obj.id_selected.id != selectedIdWeight) {
            console.log(selectedIdWeight);
            if (selectedIdWeight !== null) document.querySelector(`li[data-id="${selectedIdWeight}"]`).classList.remove('selected');
            selectedIdWeight = obj.id_selected.id;                    
            if (selectedIdWeight !== null) document.querySelector(`li[data-id="${selectedIdWeight}"]`).classList.add('selected');
            const selected = document.querySelector('.list-in li.selected');
            console.log(selected);
            if (selected) {
                selected.scrollIntoView({
                    behavior: 'instant',
                    block: 'nearest',
                    inline: 'start'
                });
            }
        }
    }
}

async function handleTara() {
    await fetch(`${pathname}/command_weigher/tare?instance_name=1&weigher_name=P1`)
    .then(res => res.json())
    .catch(error => console.error('Errore nella fetch:', error));
}

async function handleZero() {
    await fetch(`${pathname}/command_weigher/zero?instance_name=1&weigher_name=P1`)
    .then(res => res.json())
    .catch(error => console.error('Errore nella fetch:', error));
}

async function handlePTara() {
    let preset_tare = 0;
    if (myNumberInput.value) preset_tare = myNumberInput.value;
    await fetch(`${pathname}/command_weigher/preset_tare?instance_name=1&weigher_name=P1&tare=${preset_tare}`)
    .then(res => {
        closePopup();
        return res.json();
    })
    .catch(error => console.error('Errore nella fetch:', error));
}

async function handleStampa() {
    buttons.forEach(button => {
        button.disabled = true;
        button.classList.add("disabled-button"); // Aggi
    });
    const r = await fetch(`${pathname}/command_weigher/weighing?instance_name=1&weigher_name=P1`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
    })
    .then(res => {
        return res.json();
    })
    .catch(error => console.error('Errore nella fetch:', error));
    if (r.command_details.command_executed == true) {
        showSnackbar("Pesando...");
    } else {
        showSnackbar(r.command_details.error_message);
        buttons.forEach(button => {
            button.disabled = false;
            button.classList.remove("disabled-button"); // Aggi
        });
    }            
}

async function handlePesata() {
    buttons.forEach(button => {
        button.disabled = true;
        button.classList.add("disabled-button"); // Aggi
    });
    const r = await fetch(`${pathname}/command_weigher/weighing?instance_name=1&weigher_name=P1`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                data_in_execution: dataInExecution
            })
        }
    )
    .then(res => {
        return res.json();
    })
    .catch(error => console.error('Errore nella fetch:', error));
    if (r.command_details.command_executed == true) {
        showSnackbar("Pesando...");
    } else {
        showSnackbar(r.command_details.error_message);
        buttons.forEach(button => {
            button.disabled = false;
            button.classList.remove("disabled-button"); // Aggi
        });
    }
}

async function handlePesata2() {
    if (selectedIdWeight) {
        buttons.forEach(button => {
            button.disabled = true;
            button.classList.add("disabled-button"); // Aggi
        });
        const r = await fetch(`${pathname}/command_weigher/weighing?instance_name=1&weigher_name=P1`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                id_selected: selectedIdWeight
            })
        })
        .then(res => {
            return res.json();
        })
        .catch(error => console.error('Errore nella fetch:', error));
        if (r.command_details.command_executed == true) {
            showSnackbar("Pesando...");
        } else {
            showSnackbar(r.command_details.error_message);
            buttons.forEach(button => {
                button.disabled = false;
                button.classList.remove("disabled-button"); // Aggi
            });
        }                
    } else {
        showSnackbar("Nessun peso selezionato");
    }
}

function disableAllElements() {
    // Seleziona tutti i pulsanti e gli input (inclusi select, textarea, ecc.)
    const buttonsAndInputs = document.querySelectorAll('button, input, textarea, [role="button"]');

    // Disabilita ogni elemento trovato
    buttonsAndInputs.forEach(element => {
        element.disabled = true;
    });
}

function enableAllElements() {
    // Seleziona tutti i pulsanti e gli input
    const buttonsAndInputs = document.querySelectorAll('button, input, textarea, [role="button"]');

    // Abilita ogni elemento trovato
    buttonsAndInputs.forEach(element => {
        element.disabled = false;
    });
}