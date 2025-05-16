window.addEventListener('load', () => {
    setTimeout(_ => {
        document.querySelector('.loading').style.display = 'none';
        document.querySelector('.container').style.display = 'flex';
    }, 300);
})

let currentPopup;
let currentInput;

let connected;

let selectedIdVehicle;
let selectedIdTypeSubject;
let selectedIdSubject;
let selectedIdVector;
let selectedIdDriver;
let selectedIdMaterial;

let selectedIdWeight;
let dataInExecution;

let isRefreshing = false;

let pathname = '';

pathname = '/gateway';

let lastSlashIndex = window.location.pathname.lastIndexOf('/');

pathname = lastSlashIndex !== -1 ? pathname.substring(0, lastSlashIndex) : pathname;

let snackbarTimeout;

let data_weight_realtime = {
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

let instances = {};

let firmwareValue;
let modelNameValue;
let serialNumberValue;
let minWeightValue;
let maxWeightValue;
let divisionValue;

const buttons = document.querySelectorAll("button");
const myNumberInput = document.getElementById("myNumberInput");
const container = document.querySelector('.ins');
const listIn = document.querySelector('.list-in');
const selectedIdWeigher = document.querySelector('.list-weigher');
const tareButton = document.getElementById('tareButton');
const zeroButton = document.getElementById('zeroButton');
const presetTareButton = document.getElementById('pTareButton');
const inButton = document.getElementById('inButton')
const printButton = document.getElementById('printButton');
const outButton = document.getElementById('outButton');
const firmware = document.getElementById('firmware');
const modelName = document.getElementById('modelName');
const serialNumber = document.getElementById('serialNumber');
const minWeight = document.getElementById('minWeight');
const maxWeight = document.getElementById('maxWeight');
const division = document.getElementById('division');
// Usa un MutationObserver per rilevare i cambiamenti nei contenuti
const observer = new MutationObserver(() => updateStyle());

document.addEventListener('DOMContentLoaded', async () => {
    updateStyle();
    fetch('/config-weigher/all/instance')
    .then(res => res.json())
    .then(res => {
        currentWeigherPath = localStorage.getItem('currentWeigherPath');
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
        instances = res;
        if (selectedIdWeigher.children.length <= 1) {
            selectedIdWeigher.style.visibility = 'hidden';
        } 
    });
});

selectedIdWeigher.addEventListener('change', (event) => {
    currentWeigherPath = event.target.value;
    if (currentWeigherPath) {
        closeWebSocket();
        document.getElementById('netWeight').innerText = "N/A";
        document.getElementById('uniteMisure').innerText = "N/A";
        document.getElementById('tare').innerText = "N/A";
        document.getElementById('status').innerText = "N/A";
        connectWebSocket(`command-weigher/realtime${currentWeigherPath}`, updateUIRealtime)
        getInstanceWeigher(currentWeigherPath)
        getData(currentWeigherPath)
        .then(() => localStorage.setItem('currentWeigherPath', currentWeigherPath))
        .then(() => populateListIn());
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

async function getInstanceWeigher(path) {
    await fetch(`/config-weigher/instance/node${path}`)
    .then(res => {
        if (res.status === 404) {
            alert("La pesa selezionata non è presente nella configurazione perché potrebbe essere stata cancellata, è necessario aggiornare la pagina.");
        }
        return res.json();        
    })
    .then(res => {
        const obj = Object.values(res)[0];
        firmware.textContent = obj.terminal_data.firmware;
        firmwareValue = obj.terminal_data.firmware;
        modelName.textContent = obj.terminal_data.model_name;
        modelNameValue = obj.terminal_data.model_name;
        serialNumber.textContent = obj.terminal_data.serial_number;
        serialNumberValue = obj.terminal_data.serial_number;
        minWeight.textContent = obj.min_weight;
        minWeightValue = obj.min_weight;
        maxWeight.textContent = obj.max_weight;
        maxWeightValue = obj.max_weight;
        division.textContent = obj.division;
        divisionValue = obj.division;
    })
    .catch(error => console.error('Errore nella fetch:', error));
}

async function getData(path) {
    await fetch(`/data${path}`)
    .then(res => {
        if (res.status === 404) {
            alert("La pesa selezionata non è presente nella configurazione perché potrebbe essere stata cancellata, è necessario aggiornare la pagina.");
        }
        return res.json();
    })
    .then(res => {
        dataInExecution = res["data_in_execution"];
        const obj = res["data_in_execution"];
        selectedIdVehicle = obj.vehicle.id;
        selectedIdTypeSubject = obj.typeSubject;
        selectedIdSubject = obj.subject.id;
        selectedIdVector = obj.vector.id;
        selectedIdDriver = obj.driver.id;
        selectedIdMaterial = obj.material.id;
        document.querySelector('#currentDescriptionVehicle').value = obj.vehicle.description ? obj.vehicle.description : '';
        document.querySelector('#currentPlateVehicle').value = obj.vehicle.plate ? obj.vehicle.plate : '';
        document.querySelector('#typeSubject').value = obj.typeSubject ? obj.typeSubject : '';
        document.querySelector('#currentSocialReasonSubject').value = obj.subject.social_reason ? obj.subject.social_reason : '';
        document.querySelector('#currentSocialReasonVector').value = obj.vector.social_reason ? obj.vector.social_reason : '';
        document.querySelector('#currentSocialReasonDriver').value = obj.driver.social_reason ? obj.driver.social_reason : '';
        document.querySelector('#currentDescriptionMaterial').value = obj.material.description ? obj.material.description : '';
        document.querySelector('#currentNote').value = obj.note ? obj.note : '';            
        selectedIdWeight = res["id_selected"]["id"];
        if (res.id_selected.id !== null) {
            // Seleziona tutti i pulsanti e gli input
            const buttonsAndInputs = document.querySelectorAll('.anagrafic input, .anagrafic select');
            // Disabilita ogni elemento trovato
            buttonsAndInputs.forEach(element => {
                element.disabled = true;
            });
        }
    })
    .catch(error => console.error('Errore nella fetch:', error));
}

async function populateListIn() {
    const listIn = document.querySelector('.list-in');

    listIn.innerHTML = '';

    await fetch('/anagrafic/reservation/list?status=NOT_CLOSED')
    .then(res => res.json())
    .then(data => {
        data.data.forEach(item => {
            const li = document.createElement('li');
            if (item.selected == true && item.id !== selectedIdWeight) li.style.background = 'lightgrey';
            let content = item.weighings.length > 0 ? item.weighings[0].pid : item.id;
            if (item.vehicle && item.vehicle.plate) content = `${item.vehicle.plate}`;
            else if (item.vehicle && item.vehicle.description) content = `${item.vehicle.description}`;
            else if (item.subject && item.subject.social_reason) content = `${item.subject.social_reason}`;
            li.textContent = content;
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
                await fetch(`/data${currentWeigherPath}`, {
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
    try {
        closePopup();
    } catch (err) {}
    fetch(`/data${currentWeigherPath}`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json'
        },
        body: requestBody
    })
    .then(res => res.json())
    .catch(error => console.error('Errore nella fetch:', error));
}

function isDate(string) {
    const date = new Date(string);
    return !isNaN(date.getTime());
}

async function showSuggestions(name_list, inputHtml, filter, inputValue, columns_to_obscure, popup, showList, condition = null, valueCondition = null) {
    const suggestionsList = document.getElementById(showList);
    suggestionsList.innerHTML = ""; // Pulisce la lista precedente

    let currentId;
    let anagrafic_to_set;

    // Opzionale: salva l'ID dell'elemento selezionato
    if (showList === 'suggestionsListPlateVehicle' || showList === 'suggestionsListDescriptionVehicle') {
        currentId = selectedIdVehicle;
        anagrafic_to_set = 'vehicle';
    } else if (showList === 'suggestionsListSocialReasonSubject') {
        currentId = selectedIdSubject;
        anagrafic_to_set = 'subject';
    } else if (showList === 'suggestionsListSocialReasonVector') {
        currentId = selectedIdVector;
        anagrafic_to_set = 'vector';
    } else if (showList === 'suggestionsListSocialReasonDriver') {
        currentId = selectedIdDriver;
        anagrafic_to_set = 'driver';
    } else if (showList === 'suggestionsListMaterial') {
        currentId = selectedIdMaterial;
        anagrafic_to_set = 'material';
    }

    let url = `/anagrafic/${name_list}/list`;

    if (inputValue) url += `?${filter}=${inputValue}%`;

    // Eseguire una chiamata HTTP per ottenere la lista
    const response = await fetch(url)
    .then(response => response.json())
    .catch(error => console.error(error)); // Sostituisci con l'URL del tuo endpoint

    response.data.forEach(suggestion => {
        if (suggestion[filter] && suggestion.selected !== true || suggestion.id === currentId) {
            const li = document.createElement("li");

            li.onclick = () => {
                closePopup();
                fetch(`/data${currentWeigherPath}`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        data_in_execution: {
                            [anagrafic_to_set]: {
                                id: parseInt(suggestion.id)
                            }
                        }
                    })
                })
                .then(res => res.json())
                .catch(error => console.error(error));
            };

            let text = highlightText(suggestion, inputValue, filter);
            for (const [key, value] of Object.entries(suggestion)) {
                if (value && typeof(value) !== 'object' && !columns_to_obscure.includes(key) && key !== filter && key !== 'selected' && key !== 'id') text += `  -   ${value}`;
            }

            if (text) {
                li.innerHTML = text; // Evidenzia il testo
                li.dataset.id = suggestion.id
    
                if (suggestion.id == currentId) {
                    li.classList.add('selected');
                }
    
                suggestionsList.appendChild(li);
            }
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

// function highlightText(suggestion, input, filter) {
//     const regex = new RegExp(`(${input})`, 'gi'); // Regex per evidenziare
//     return suggestion[filter] ? suggestion[filter].replace(regex, `<span class="highlight">$1</span>`) : '';
// }

function highlightText(suggestion, input, filter) {
    // Creiamo un'espressione regolare che cerca l'input solo all'inizio della stringa
    const regex = new RegExp(`^(${input})`, 'i');
    if (suggestion[filter]) {
        // Se c'è una corrispondenza all'inizio, evidenziala
        if (regex.test(suggestion[filter])) {
            return suggestion[filter].replace(regex, '<span class="highlight">$1</span>');
        }
        // Altrimenti, restituisci la stringa originale senza evidenziazioni
        return suggestion[filter];
    }
    return '';
}

function changeContent(type, value) {
    document.getElementById('header').innerHTML = `${type} <span class="arrow">▼</span>`;
    isCustomerSupplier = value;
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
    }
}

function isNumeric(value) {
    return !isNaN(value) && value !== "";
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
            showSnackbar(`Pesata eseguita! Bilancia: ${obj.weigher_name}. Pid: ${obj.weight_executed.pid}`);
            populateListIn();
        } else { 
            showSnackbar("Pesata fallita!");
        }
        buttons.forEach(button => {
            button.disabled = false;
            button.classList.remove("disabled-button"); // Aggi
        });
    } else if (obj.tare) {
        data_weight_realtime = obj;
        document.getElementById('tare').innerText = data_weight_realtime.tare !== undefined ? data_weight_realtime.tare : 'N/A';
        document.getElementById('netWeight').innerText = data_weight_realtime.net_weight !== undefined ? data_weight_realtime.net_weight : "N/A";
        document.getElementById('uniteMisure').innerText = data_weight_realtime.unite_measure !== undefined ? data_weight_realtime.unite_measure : 'N/A';
        document.getElementById('status').innerText = data_weight_realtime.status !== undefined ? data_weight_realtime.status : 'N/A';
        const numeric = isNumeric(data_weight_realtime.gross_weight);
        const gross_weight = Number(data_weight_realtime.gross_weight);
        const tare_weight = Number(data_weight_realtime.tare);
        if (numeric && minWeightValue <= gross_weight && gross_weight <= maxWeightValue && data_weight_realtime.status === "ST") {
            if (tare_weight == 0 && selectedIdWeight === null) {
                tareButton.disabled = false;
                zeroButton.disabled = true;
                presetTareButton.disabled = false;
                inButton.disabled = false;
                printButton.disabled = false;
            } else if (tare_weight !== 0 && selectedIdWeight !== null) {
                tareButton.disabled = true;
                zeroButton.disabled = true;
                presetTareButton.disabled = true;
                inButton.disabled = true;
                printButton.disabled = true;
            } else {
                tareButton.disabled = false;
                zeroButton.disabled = true;
                presetTareButton.disabled = false;
                inButton.disabled = true;
                printButton.disabled = false;
                outButton.disabled = false;
            }
        } else if (numeric && minWeightValue >= gross_weight) {
            tareButton.disabled = true;
            zeroButton.disabled = false;
            presetTareButton.disabled = false;
            inButton.disabled = true;
            printButton.disabled = true;
            outButton.disabled = true;
        } else {
            tareButton.disabled = true;
            zeroButton.disabled = true;
            presetTareButton.disabled = true;
            inButton.disabled = true;
            printButton.disabled = true;
            outButton.disabled = true;
        }
    } else if (obj.data_in_execution) {
        dataInExecution = obj.data_in_execution;
        selectedIdVehicle = obj.data_in_execution.vehicle.id;
        selectedIdTypeSubject = obj.data_in_execution.typeSubject;
        selectedIdSubject = obj.data_in_execution.subject.id;
        selectedIdVector = obj.data_in_execution.vector.id;
        selectedIdDriver = obj.data_in_execution.driver.id;
        selectedIdMaterial = obj.data_in_execution.material.id;
        if (obj.data_in_execution.typeSubject === 'Cliente') obj.data_in_execution.typeSubject = 'CUSTOMER';
        else if (obj.data_in_execution.typeSubject === 'Fornitore') obj.data_in_execution.typeSubject = 'SUPPLIER';
        document.querySelector('#currentDescriptionVehicle').value = obj.data_in_execution.vehicle.description ? obj.data_in_execution.vehicle.description : '';
        document.querySelector('#currentPlateVehicle').value = obj.data_in_execution.vehicle.plate ? obj.data_in_execution.vehicle.plate : '';
        document.querySelector('#typeSubject').value = obj.data_in_execution.typeSubject ? obj.data_in_execution.typeSubject : '';
        document.querySelector('#currentSocialReasonSubject').value = obj.data_in_execution.subject.social_reason ? obj.data_in_execution.subject.social_reason : '';
        document.querySelector('#currentSocialReasonVector').value = obj.data_in_execution.vector.social_reason ? obj.data_in_execution.vector.social_reason : '';
        document.querySelector('#currentSocialReasonDriver').value = obj.data_in_execution.driver.social_reason ? obj.data_in_execution.driver.social_reason : '';
        document.querySelector('#currentDescriptionMaterial').value = obj.data_in_execution.material.description ? obj.data_in_execution.material.description : '';
        document.querySelector('#currentNote').value = obj.data_in_execution.note ? obj.data_in_execution.note : '';
        if (obj.id_selected.id != selectedIdWeight) {
            if (selectedIdWeight !== null) document.querySelector(`li[data-id="${selectedIdWeight}"]`).classList.remove('selected');
            selectedIdWeight = obj.id_selected.id;                    
            if (selectedIdWeight !== null) document.querySelector(`li[data-id="${selectedIdWeight}"]`).classList.add('selected');
            const selected = document.querySelector('.list-in li.selected');
            if (selected) {
                selected.scrollIntoView({
                    behavior: 'instant',
                    block: 'nearest',
                    inline: 'start'
                });
            }
        }
        if (obj.id_selected.id === null) {
            // Seleziona tutti i pulsanti e gli input
            const buttonsAndInputs = document.querySelectorAll('.anagrafic input, .anagrafic select');
            // Disabilita ogni elemento trovato
            buttonsAndInputs.forEach(element => {
                element.disabled = false;
            });
        } else {
            // Seleziona tutti i pulsanti e gli input
            const buttonsAndInputs = document.querySelectorAll('.anagrafic input, .anagrafic select');
            // Disabilita ogni elemento trovato
            buttonsAndInputs.forEach(element => {
                element.disabled = true;
            });
        }
    }
}

async function handleTara() {
    await fetch(`${pathname}/command-weigher/tare${currentWeigherPath}`)
    .then(res => res.json())
    .catch(error => console.error('Errore nella fetch:', error));
}

async function handleZero() {
    await fetch(`${pathname}/command-weigher/zero${currentWeigherPath}`)
    .then(res => res.json())
    .catch(error => console.error('Errore nella fetch:', error));
}

async function handlePTara() {
    let preset_tare = 0;
    if (myNumberInput.value) preset_tare = myNumberInput.value;
    await fetch(`${pathname}/command-weigher/tare/preset${currentWeigherPath}&tare=${preset_tare}`)
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
    const r = await fetch(`${pathname}/command-weigher/print${currentWeigherPath}`)
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
    const r = await fetch(`${pathname}/command-weigher/in${currentWeigherPath}`,
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
    buttons.forEach(button => {
        button.disabled = true;
        button.classList.add("disabled-button"); // Aggi
    });
    const r = await fetch(`${pathname}/command-weigher/out${currentWeigherPath}`, {
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
}

function disableAllElements() {
    // Seleziona tutti i pulsanti e gli input
    const buttonsAndInputs = document.querySelectorAll('button, input, select, textarea, [role="button"]');

    // Disabilita ogni elemento trovato
    buttonsAndInputs.forEach(element => {
        element.disabled = true;
    });
}

function enableAllElements() {
    // Seleziona tutti i pulsanti e gli input
    const buttonsAndInputs = document.querySelectorAll('button, input, select, textarea, [role="button"]');

    // Abilita ogni elemento trovato
    buttonsAndInputs.forEach(element => {
        element.disabled = false;
    });
}