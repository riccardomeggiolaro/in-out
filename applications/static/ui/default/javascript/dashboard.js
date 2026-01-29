
window.addEventListener('load', () => {
    setTimeout(_ => {
        document.querySelector('.loading').style.display = 'none';
        document.querySelector('.container').style.display = 'flex';
    }, 300);
})

let currentPopup;
let currentInput;

// Variabili per gestire i tab mobili
let anagraficViewed = false;
let insViewed = false;
let lastDataInExecution = null;
let lastInsCount = 0;

let connected;

let selectedIdVehicle;
let selectedIdTypeSubject;
let selectedIdSubject;
let selectedIdVector;
let selectedIdMaterial;

let selectedIdWeight;
let numberInOutSelectedIdWeight;
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
    unite_measure: undefined,
    potential_net_weight: null,
    over_max_theshold: null
};

let _data;
let reconnectTimeout;
let reconnectionAttemptTimeout;
let isReconnecting = false; // Flag per evitare popup durante riconnessione
let autoReconnectInterval; // Intervallo per riconnessione automatica
let pingInterval; // Intervallo per ping
let pingTimeout; // Timeout per risposta pong

let url = new URL(window.location.href);
let currentWeigherPath = null;

let return_pdf_copy_after_weighing = false;

let instances = {};

let firmwareValue;
let modelNameValue;
let serialNumberValue;
let minWeightValue;
let maxWeightValue;
let divisionValue;
let maxThesholdValue;

let confirmWeighing;

let access_id;

let handleClickNeedToConfirm;

const buttons = document.querySelectorAll("button");
const myNumberInput = document.getElementById("myNumberInput");
const container = document.querySelector('.ins');
const listIn = document.querySelector('.list-in');
const reprint = document.querySelector('#reprint');
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
const cams = document.querySelector('#cams');
const reconnectionButton = document.getElementById('reconnectionButton');
// Usa un MutationObserver per rilevare i cambiamenti nei contenuti
const observer = new MutationObserver(() => updateStyle());

document.addEventListener('DOMContentLoaded', async () => {
    updateStyle();
    fetch('/api/config-weigher/configuration')
    .then(res => res.json())
    .then(res => {
        currentWeigherPath = localStorage.getItem('currentWeigherPath');
        return_pdf_copy_after_weighing = res["return_pdf_copy_after_weighing"];
        let selected = false;
        for (let instance in res["weighers"]) {
            for (let weigher in res["weighers"][instance]["nodes"]) {
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
        instances = res["weighers"];
        if (selectedIdWeigher.children.length > 1) {
            selectedIdWeigher.style.visibility = 'visible';
        } 
    });
});

selectedIdWeigher.addEventListener('change', (event) => {
    currentWeigherPath = event.target.value;
    if (currentWeigherPath) {
        localStorage.setItem('currentWeigherPath', currentWeigherPath)

        // Reset dei flag di visualizzazione per il nuovo pesatore
        anagraficViewed = false;
        insViewed = false;
        lastDataInExecution = null;
        lastInsCount = 0;

        isReconnecting = true; // Flag per evitare popup durante cambio pesa
        closeWebSocket();
        document.getElementById('netWeight').innerText = "N/A";
        document.getElementById('uniteMisure').innerText = "N/A";
        document.getElementById('tare').innerText = "N/A";
        document.getElementById('status').innerText = "N/A";
        connectWebSocket(`api/command-weigher/realtime${currentWeigherPath}`, updateUIRealtime)
    }
});

// Aggiorna lo stile quando la finestra viene ridimensionata
window.addEventListener('resize', updateStyle);

// Gestisci il ridimensionamento per i tab mobili
window.addEventListener('resize', () => {
    if (window.innerWidth > 800) {
        // Chiudi i tab se aperti e nascondi i badge
        closeTab('anagrafic');
        closeTab('ins');
        document.getElementById('badgeAnagrafic').classList.remove('show');
        document.getElementById('badgeIns').classList.remove('show');
    }
});
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
    if (event.target === popup && currentPopup !== "reconnectionPopup" && !confirmWeighing) {
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
    await fetch(`/api/config-weigher/instance/node${path}`)
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
        maxThesholdValue = obj.max_theshold;
        if (obj.printer_name === null || !obj.events.weighing.report.in && !obj.events.weighing.report.out) reprint.style.display = 'none';
        else reprint.style.display = 'block';
    })
    .catch(error => console.error('Errore nella fetch:', error));
}

async function getData(path) {
    await fetch(`/api/data${path}`)
    .then(res => {
        if (res.status === 404) {
            alert("La pesa selezionata non è presente nella configurazione perché potrebbe essere stata cancellata, è necessario aggiornare la pagina.");
        }
        return res.json();
    })
    .then(res => {
        const type = res.type;
        const number_in_out = res.number_in_out;
        const weight1 = res.id_selected.weight1;
        dataInExecution = res["data_in_execution"];
        const obj = res["data_in_execution"];
        selectedIdVehicle = obj.vehicle.id;
        selectedIdTypeSubject = obj.typeSubject;
        selectedIdSubject = obj.subject.id;
        selectedIdVector = obj.vector.id;
        selectedIdMaterial = obj.material.id;
        if (type === "RESERVATION" && number_in_out === null && weight1 === null) {
            obj.vehicle.plate += "⭐";
            document.querySelector('.containerPlateVehicle').classList.add('permanent');
        } else {
            document.querySelector('.containerPlateVehicle').classList.remove('permanent');
        }
        document.querySelector('#currentPlateVehicle').value = obj.vehicle.plate ? obj.vehicle.plate : '';
        document.querySelector('#typeSubject').value = obj.typeSubject ? obj.typeSubject : 'CUSTOMER';
        document.querySelector('#currentSocialReasonSubject').value = obj.subject.social_reason ? obj.subject.social_reason : '';
        document.querySelector('#currentSocialReasonVector').value = obj.vector.social_reason ? obj.vector.social_reason : '';
        document.querySelector('#currentDescriptionMaterial').value = obj.material.description ? obj.material.description : '';
        document.querySelector('#currentNote').value = obj.note ? obj.note : '';            
        document.querySelector('#currentDocumentReference').value = obj.document_reference ? obj.document_reference : '';
        selectedIdWeight = res["id_selected"]["id"];
        
        // NUOVO: Controlla need_to_confirm
        if (res.id_selected.need_to_confirm === true) {
            handleNeedToConfirm(obj.vehicle.plate.replace("⭐", ""));
        }
        
        if (res.type !== "MANUALLY" && res.id_selected.id !== null) {
            const buttonsAndInputs = document.querySelectorAll('.anagrafic input, .anagrafic select');
            buttonsAndInputs.forEach(element => {
                element.disabled = true;
            });
        }
    })
    .catch(error => console.error('Errore nella fetch:', error));
}

async function populateListIn() {
    const listIn = document.querySelector('.list-in');

    await fetch('/api/anagrafic/access/list?excludeTestWeighing=true&status=NOT_CLOSED&permanentIfWeight1=true')
    .then(res => res.json())
    .then(data => {
        listIn.innerHTML = '';
        data.data.forEach(item => {
            const li = document.createElement('li');
            if (item.selected == true && item.id !== selectedIdWeight) li.style.background = 'lightgrey';
            let content = item.id;
            if (item.in_out.length > 0) {
                if (item.in_out[0].idWeight1) content = item.in_out[0].weight1.pid;
                else if (item.in_out[0].idWeight2) content = item.in_out[0].weight2.pid;
            }
            if (item.vehicle && item.vehicle.plate) {
                content = `${item.vehicle.plate}`;
            }

            // Add subject and material information (always show if present)
            let additionalInfo = [];
            if (item.subject && item.subject.social_reason) {
                additionalInfo.push(item.subject.social_reason);
            }
            if (item.in_out.length > 0 && item.in_out[0].material && item.in_out[0].material.description) {
                additionalInfo.push(item.in_out[0].material.description);
            }
            if (additionalInfo.length > 0) {
                content += `<br><small style="font-size: 0.85em;">${additionalInfo.join(' - ')}</small>`;
            }
            li.innerHTML = content;
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
                await fetch(`/api/data${currentWeigherPath}`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(obj)
                })
                .then(res => res.json())
                .then(res => {
                    if (res.detail) showSnackbar("snackbar", res.detail, 'rgb(255, 208, 208)', 'black');
                    else numberInOutSelectedIdWeight = item.in_out.length;
                });
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

function setDataInExecutionOnCLick(anagrafic, key, value, showList) {
    let requestBody;
    const suggestionsList = document.getElementById(showList);
    if (suggestionsList && suggestionsList.children.length === 1 && suggestionsList.children[0].textContent.replace("⭐", "") === value) {
        id = suggestionsList.children[0].dataset.id;
        requestBody = JSON.stringify({
            data_in_execution: {
                [anagrafic]: {
                    id
                }
            }
        });
    } else if (key) {
        const data = {
            data_in_execution: {
                [anagrafic]: {
                    [key]: value
                }
            }
        }
        if (key !== "id" && value === "") {
            data.data_in_execution[anagrafic]["id"] = -1;
        }
        requestBody = JSON.stringify(data);
    } else {
        requestBody = JSON.stringify({
            data_in_execution: {
                [anagrafic]: value
            }
        })
    }
    fetch(`/api/data${currentWeigherPath}`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json'
        },
        body: requestBody
    })
    .then(res => res.json())
    .then(res => {
        if (res.detail) showSnackbar("snackbar", res.detail, 'rgb(255, 208, 208)', 'black');
        else {
            closePopup();
            populateListIn();
        }
    });
}

function deleteIdSelected() {
    fetch(`/api/data${currentWeigherPath}`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            "id_selected": {
                "id": -1
            }
        })
    })
    .then(res => res.json())
    .then(res => {
        if (res.detail) showSnackbar("snackbar", res.detail, 'rgb(255, 208, 208)', 'black');
        else document.querySelector('.containerPlateVehicle').classList.remove('permanent');
    });
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
    if (showList === 'suggestionsListPlateVehicle') {
        currentId = selectedIdVehicle;
        anagrafic_to_set = 'vehicle';
    } else if (showList === 'suggestionsListSocialReasonSubject') {
        currentId = selectedIdSubject;
        anagrafic_to_set = 'subject';
    } else if (showList === 'suggestionsListSocialReasonVector') {
        currentId = selectedIdVector;
        anagrafic_to_set = 'vector';
    } else if (showList === 'suggestionsListMaterial') {
        currentId = selectedIdMaterial;
        anagrafic_to_set = 'material';
    }

    let url = `/api/anagrafic/${name_list}/list?`;

    if (anagrafic_to_set === 'vehicle' && selectedIdWeight === null) url += `permanentAssociatedFirstToWeighing1=true&`;

    if (inputValue) url += `${filter}=${inputValue}%`;

    // Eseguire una chiamata HTTP per ottenere la lista
    const response = await fetch(url)
    .then(response => response.json())
    .catch(error => console.error(error)); // Sostituisci con l'URL del tuo endpoint

    response.data.forEach(suggestion => {
        if (suggestion[filter] && suggestion.selected !== true || suggestion.id === currentId) {
            const li = document.createElement("li");

            li.onclick = () => {
                fetch(`/api/data${currentWeigherPath}`, {
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
                .then(res => {
                    if (res.detail) showSnackbar("snackbar", res.detail, 'rgb(255, 208, 208)', 'black');
                    else {
                        closePopup();
                        populateListIn();
                    }
                });
            };

            let text = highlightText(suggestion, inputValue, filter);
            for (const [key, value] of Object.entries(suggestion)) {
                if (value && typeof(value) !== 'object' && !columns_to_obscure.includes(key) && key !== filter && key !== 'selected' && key !== 'id') text += `  -   ${value}`;
            }

            if (text) {
                if (
                    anagrafic_to_set === 'vehicle' && 
                    selectedIdWeight === null && 
                    "accesses" in suggestion && 
                    suggestion.accesses.length > 0 && 
                    suggestion.accesses[suggestion.accesses.length - 1].number_in_out === null &&
                    suggestion.accesses[suggestion.accesses.length - 1].status !== 'Chiusa'
                ) {
                    if (suggestion.accesses[suggestion.accesses.length - 1].in_out.length === 0 ||
                        suggestion.accesses[suggestion.accesses.length - 1].in_out.length > 0 && 
                        suggestion.accesses[suggestion.accesses.length - 1].in_out[suggestion.accesses[suggestion.accesses.length - 1].in_out.length - 1].idWeight2 !== null
                    ) {
                        li.classList.add('permanent-associated');
                        text = `<span>${text}</span><span>⭐</span>`;
                    }
                }
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
    // Rileva quando il browser va offline (es. cavo staccato, wifi perso)
    if (!navigator.onLine && _data && _data.readyState === WebSocket.OPEN) {
        console.log('Browser offline rilevato - chiudo connessione WebSocket');
        closeWebSocket();
        if (!isRefreshing) {
            showReconnectionPopup();
        }
    } else if (location.protocol === "https:") {
        console.error("WebSocket error. Trying to reconnect...");
        document.querySelector('.loading').style.display = 'flex';
        document.querySelector('.container').style.display = 'none';
        startAutoReconnect();
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
function showSnackbarDashboard(message) {
    const snackbar = document.getElementById("snackbar-dashboard");
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
        if (input) popupContent.querySelector("input").focus(); // Imposta il focus sull'input
    }, 10); // Breve ritardo per assicurarsi che il display sia impostato
}

function closePopup() {
    console.log("Closing popup:", currentPopup);
    if (currentPopup) {
        confirmWeighing = null;
        const popup = document.getElementById(currentPopup);
        const popupContent = popup.querySelector(".popup-content");
        const buttons = popup.querySelectorAll("button");
        
        const input = document.getElementById(currentInput);
        if (input) input.value = "";

        // Rimuovi la classe per nascondere
        popupContent.classList.remove("show");
        
        // Aspetta il tempo di transizione prima di nascondere il popup
        setTimeout(() => {
            popup.style.display = "none"; // Nascondi il popup
            myNumberInput.value = "";
            buttons.forEach(button => button.disabled = false);
        }, 300); // Tempo della transizione
    }
}

function connectWebSocket(path, exe) {
    // Ottieni la base URL del dominio corrente
    let baseUrl = window.location.origin + pathname;

    baseUrl = baseUrl.replace(/^http/, (match) => match === 'http' ? 'ws' : 'wss');

    // Costruisci l'URL WebSocket
    const websocketUrl = `${baseUrl}/${path}`;

    // Durante la riconnessione automatica, preserva l'intervallo
    const preserve = autoReconnectInterval !== null;
    closeWebSocket(preserve); // Chiude la connessione WebSocket precedente se esiste

    _data = new WebSocket(websocketUrl);

    _data.addEventListener('message', (e) => {
        // Gestisci pong
        try {
            const data = JSON.parse(e.data);
            if (data.type === 'pong') {
                // Pong ricevuto, cancella il timeout
                if (pingTimeout) {
                    clearTimeout(pingTimeout);
                    pingTimeout = null;
                }
                return;
            }
        } catch (err) {}
        exe(e);
    });

    _data.addEventListener('open', () => {
        // Cancella tutti i timeout e intervalli di riconnessione
        if (reconnectionAttemptTimeout) {
            clearTimeout(reconnectionAttemptTimeout);
            reconnectionAttemptTimeout = null;
        }
        if (autoReconnectInterval) {
            clearInterval(autoReconnectInterval);
            autoReconnectInterval = null;
        }

        // Connessione stabilita con successo
        isReconnecting = false;

        // Chiudi immediatamente il popup
        closePopup('reconnectionPopup');

        // Avvia ping interval
        startPing();

        // Ricarica i dati dopo aver aperto la connessione
        getInstanceWeigher(currentWeigherPath);
        getData(currentWeigherPath)
            .then(() => populateListIn())
            .then(() => {
                // Abilita tutti gli elementi solo dopo aver caricato i dati
                enableAllElements();
            });
    })

    _data.addEventListener('error', () => {
        // Avvia la riconnessione automatica solo se non è già in corso
        if (!isRefreshing && !autoReconnectInterval) {
            closeWebSocket();
            showReconnectionPopup();
        }
    });

    _data.addEventListener('close', () => {
        // Avvia la riconnessione automatica solo se non è già in corso
        if (!isRefreshing && !autoReconnectInterval) {
            showReconnectionPopup();
        }
    });
}

function showReconnectionPopup() {
    disableAllElements();
    document.querySelector('#reconnectionPopup .popup-content p').textContent = "Riconnessione in corso...";
    openPopup('reconnectionPopup');
    startAutoReconnect();
}

function startAutoReconnect() {
    // Ferma eventuali tentativi precedenti
    if (autoReconnectInterval) {
        clearInterval(autoReconnectInterval);
    }
    if (reconnectionAttemptTimeout) {
        clearTimeout(reconnectionAttemptTimeout);
    }

    // Primo tentativo immediato
    attemptReconnect();

    // Riprova automaticamente ogni 3 secondi
    autoReconnectInterval = setInterval(() => {
        if (!_data || _data.readyState !== WebSocket.OPEN) {
            console.log('Nuovo tentativo di riconnessione automatica...');
            attemptReconnect();
        } else {
            // Connessione riuscita, ferma i tentativi
            clearInterval(autoReconnectInterval);
            autoReconnectInterval = null;
        }
    }, 3000);
}

function attemptReconnect() {
    isReconnecting = true;
    closeWebSocket(true); // Preserva l'intervallo di riconnessione automatica

    console.log('Tentativo di riconnessione...');
    connectWebSocket(`api/command-weigher/realtime${currentWeigherPath}`, updateUIRealtime);

    // Timeout di 3 secondi per questo singolo tentativo
    reconnectionAttemptTimeout = setTimeout(() => {
        if (!_data || _data.readyState !== WebSocket.OPEN) {
            console.log('Tentativo di riconnessione fallito, ritenterò...');
            isReconnecting = false;
        }
    }, 3000);
}

function startPing() {
    // Ferma eventuali ping precedenti
    if (pingInterval) {
        clearInterval(pingInterval);
    }
    if (pingTimeout) {
        clearTimeout(pingTimeout);
    }

    // Invia ping ogni 3 secondi
    pingInterval = setInterval(() => {
        if (_data && _data.readyState === WebSocket.OPEN) {
            _data.send(JSON.stringify({type: 'ping'}));

            // Se non ricevo pong entro 5 secondi, considera la connessione persa
            pingTimeout = setTimeout(() => {
                console.log('Ping timeout: nessun pong ricevuto');
                if (_data) {
                    _data.close();
                }
                if (!isRefreshing && !autoReconnectInterval) {
                    showReconnectionPopup();
                }
            }, 5000);
        }
    }, 3000);
}

function closeWebSocket(preserveReconnectInterval = false) {
    // Ferma ping
    if (pingInterval) {
        clearInterval(pingInterval);
        pingInterval = null;
    }
    if (pingTimeout) {
        clearTimeout(pingTimeout);
        pingTimeout = null;
    }

    // Cancella eventuali timeout di riconnessione
    if (reconnectionAttemptTimeout) {
        clearTimeout(reconnectionAttemptTimeout);
        reconnectionAttemptTimeout = null;
    }

    // Cancella intervallo di riconnessione automatica SOLO se non dobbiamo preservarlo
    if (!preserveReconnectInterval && autoReconnectInterval) {
        clearInterval(autoReconnectInterval);
        autoReconnectInterval = null;
    }

    if (_data) {
        _data.close(); // Chiude la connessione WebSocket
        _data = null;  // Imposta _data a null per indicare che la connessione è chiusa
    }
}

function isNumeric(value) {
    return !isNaN(value) && value !== "";
}

function parseMultipleJSON(str) {
    const results = [];
    let depth = 0;
    let start = -1;
    for (let i = 0; i < str.length; i++) {
        if (str[i] === '{') {
            if (depth === 0) start = i;
            depth++;
        } else if (str[i] === '}') {
            depth--;
            if (depth === 0 && start !== -1) {
                try {
                    results.push(JSON.parse(str.substring(start, i + 1)));
                } catch (e) {}
                start = -1;
            }
        }
    }
    return results;
}

function updateUIRealtime(e) {
    const objects = parseMultipleJSON(e.data);
    objects.forEach(obj => processRealtimeObject(obj));
}

function processRealtimeObject(obj) {
    if (obj.command_in_executing) {
        if (obj.command_in_executing == "TARE") showSnackbar("snackbar", "Tara", 'rgb(208, 255, 208)', 'black');
        if (obj.command_in_executing == "PRESETTARE") showSnackbar("snackbar", "Preset tara", 'rgb(208, 255, 208)', 'black');
        if (obj.command_in_executing == "ZERO") showSnackbar("snackbar", "Zero", 'rgb(208, 255, 208)', 'black');
        if (obj.command_in_executing == "WEIGHING") {
            showSnackbar("snackbar", "Pesando...", 'rgb(208, 255, 208)', 'black');
            buttons.forEach(button => {
                button.disabled = true;
                button.classList.add("disabled-button"); // Aggi
            });
        }                    
    } else if (obj.weight_executed) {
        if (obj.weight_executed.gross_weight != "") {
            // Non chiudere il popup se è il confirmPopup del semi-automatico (need_to_confirm)
            // perché la pesata ricevuta potrebbe essere di un'altra operazione (es. No PID)
            if (!(currentPopup === "confirmPopup" && confirmWeighing === confirmSemiAutomatic)) {
                closePopup();
            }
            let message = `Pesata eseguita!`;
            if (obj.data_assigned.userId) {
                obj.data_assigned.userId = JSON.parse(obj.data_assigned.userId);
                message += ` Operatore: ${obj.data_assigned.userId.username || obj.data_assigned.userId.description}.`;
            }
            if (obj.weight_executed.pid != "") {
                message += ` Pid: ${obj.weight_executed.pid}`;
                if (obj.data_assigned && obj.data_assigned.accessId) {
                    obj.data_assigned.accessId = JSON.parse(obj.data_assigned.accessId);
                    if (obj.data_assigned.accessId.id === access_id &&
                        obj.data_assigned.accessId.in_out &&
                        obj.data_assigned.accessId.in_out.length > 0) {
                    const id_in_out = obj.data_assigned.accessId.in_out[obj.data_assigned.accessId.in_out.length-1]["id"]
                    const typeOfWeight = obj.data_assigned.accessId.in_out[obj.data_assigned.accessId.in_out.length-1]["idWeight2"] === null ? "in" : "out";
                    const params = getParamsFromQueryString();
                    const inOutPdf = instances[params.instance_name]["nodes"][params.weigher_name]["events"]["weighing"]["report"][typeOfWeight];
                    if (inOutPdf) {
                        fetch(`/api/anagrafic/access/in-out/pdf/${id_in_out}`)
                        .then(res => {
                            // Prendi il nome file dall'header Content-Disposition
                            const disposition = res.headers.get('Content-Disposition');
                            let filename = 'export.pdf';
                            if (disposition && disposition.indexOf('filename=') !== -1) {
                                filename = disposition
                                    .split('filename=')[1]
                                    .replace(/["']/g, '')
                                    .trim();
                            }
                            return res.blob().then(blob => ({ blob, filename }));
                        })
                        .then(({ blob, filename }) => {
                            const downloadLink = document.createElement('a');
                            downloadLink.href = window.URL.createObjectURL(blob);
                            downloadLink.download = filename;
                            document.body.appendChild(downloadLink);
                            downloadLink.click();
                            document.body.removeChild(downloadLink);
                        });
                    }
                    }
                }
            }
            showSnackbar("snackbar", message, 'rgb(208, 255, 208)', 'black');
            populateListIn();
        } else { 
            showSnackbar("snackbar", "Pesata fallita", 'rgb(255, 208, 208)', 'black');
        }
        access_id = null;
        buttons.forEach(button => {
            button.disabled = false;
            button.classList.remove("disabled-button"); // Aggi
        });
    } else if (obj.tare) {
        data_weight_realtime = obj;
        net = [undefined, '0'].includes(data_weight_realtime.tare);
        document.getElementById('tare').innerText = data_weight_realtime.tare !== undefined ? data_weight_realtime.tare : 'N/A';
        document.getElementById('netWeight').innerText = data_weight_realtime.net_weight !== undefined ? data_weight_realtime.net_weight : "N/A";
        document.getElementById('uniteMisure').innerText = data_weight_realtime.unite_measure !== undefined ? data_weight_realtime.unite_measure : 'N/A';
        document.getElementById('status').innerText = data_weight_realtime.status !== undefined ? data_weight_realtime.status : 'N/A';
        document.getElementById('potential_net_weight').innerHTML = data_weight_realtime.potential_net_weight !== null ? `NET ${data_weight_realtime.potential_net_weight}` : !net ? 'NET' : '';
        if (!net) {
            document.getElementById('potential_net_weight').style.top = '3rem';
            document.getElementById('potential_net_weight').style.fontWeight = 'bold';
        } else {
            document.getElementById('potential_net_weight').style.top = '0';
            document.getElementById('potential_net_weight').style.fontWeight = 'normal';
        }
        const numeric = isNumeric(data_weight_realtime.gross_weight);
        const gross_weight = Number(data_weight_realtime.gross_weight);
        const tare_weight = Number(data_weight_realtime.tare);
        // Chiudi il popup solo se non è il confirmPopup del semi-automatico (need_to_confirm)
        if (gross_weight < minWeightValue && currentPopup === "confirmPopup" && confirmWeighing !== confirmSemiAutomatic) closePopup();
        // if (numeric && minWeightValue <= gross_weight && gross_weight <= maxWeightValue && data_weight_realtime.status === "ST") {
        //     if (tare_weight == 0 && selectedIdWeight === null) {
        //         tareButton.disabled = false;
        //         // zeroButton.disabled = true;
        //         presetTareButton.disabled = false;
        //         inButton.disabled = false;
        //         printButton.disabled = false;
        //     } else if (tare_weight !== 0 && selectedIdWeight !== null) {
        //         tareButton.disabled = true;
        //         // zeroButton.disabled = true;
        //         presetTareButton.disabled = true;
        //         inButton.disabled = true;
        //         printButton.disabled = true;
        //     } else {
        //         tareButton.disabled = false;
        //         // zeroButton.disabled = true;
        //         presetTareButton.disabled = false;
        //         inButton.disabled = true;
        //         outButton.disabled = false;
        //         if (selectedIdWeight !== null) {
        //             printButton.disabled = true;
        //         } else {
        //             printButton.disabled = false;
        //         }
        //      }
        // } else if (numeric && minWeightValue >= gross_weight) {
        //     tareButton.disabled = true;
        //     // zeroButton.disabled = false;
        //     presetTareButton.disabled = false;
        //     inButton.disabled = true;
        //     outButton.disabled = true;
        // } else {
        //     tareButton.disabled = true;
        //     // zeroButton.disabled = true;
        //     presetTareButton.disabled = true;
        //     inButton.disabled = true;
        //     outButton.disabled = true;
        // }
    } else if (obj.data_in_execution) {
        dataInExecution = obj.data_in_execution;
        selectedIdVehicle = obj.data_in_execution.vehicle.id;
        selectedIdTypeSubject = obj.data_in_execution.typeSubject;
        selectedIdSubject = obj.data_in_execution.subject.id;
        selectedIdVector = obj.data_in_execution.vector.id;
        selectedIdMaterial = obj.data_in_execution.material.id;
        if (obj.data_in_execution.typeSubject === 'Cliente') obj.data_in_execution.typeSubject = 'CUSTOMER';
        else if (obj.data_in_execution.typeSubject === 'Fornitore') obj.data_in_execution.typeSubject = 'SUPPLIER';
        if (obj.type === "RESERVATION" && obj.number_in_out === null && obj.id_selected.weight1 === null) {
            obj.data_in_execution.vehicle.plate += "⭐";
            document.querySelector('.containerPlateVehicle').classList.add('permanent');
        } else {
            document.querySelector('.containerPlateVehicle').classList.remove('permanent');
        }
        document.querySelector('#currentPlateVehicle').value = obj.data_in_execution.vehicle.plate ? obj.data_in_execution.vehicle.plate : '';
        document.querySelector('#typeSubject').value = obj.data_in_execution.typeSubject ? obj.data_in_execution.typeSubject : 'CUSTOMER';
        document.querySelector('#currentSocialReasonSubject').value = obj.data_in_execution.subject.social_reason ? obj.data_in_execution.subject.social_reason : '';
        document.querySelector('#currentSocialReasonVector').value = obj.data_in_execution.vector.social_reason ? obj.data_in_execution.vector.social_reason : '';
        document.querySelector('#currentDescriptionMaterial').value = obj.data_in_execution.material.description ? obj.data_in_execution.material.description : '';
        document.querySelector('#currentNote').value = obj.data_in_execution.note ? obj.data_in_execution.note : '';
        document.querySelector('#currentDocumentReference').value = obj.data_in_execution.document_reference ? obj.data_in_execution.document_reference : '';

        if (obj.type === "MANUALLY") {
            document.querySelectorAll('.anagrafic input, .anagrafic select').forEach(element => {
                element.disabled = false;
            });
        } else {
            document.querySelectorAll('.anagrafic input, .anagrafic select').forEach(element => {
                element.disabled = true;
            });
        }

        if (obj.id_selected.id != selectedIdWeight) {
            if (selectedIdWeight !== null) {
                const previouslySelected = document.querySelector(`li[data-id="${selectedIdWeight}"]`);
                if (previouslySelected) previouslySelected.classList.remove('selected');
            }
            selectedIdWeight = obj.id_selected.id;

            // NUOVO: Controlla need_to_confirm dopo aver aggiornato selectedIdWeight
            if (obj.id_selected.need_to_confirm === true) {
                handleNeedToConfirm(obj.data_in_execution.vehicle.plate.replace("⭐", ""));
            } else {
                closePopup("confirmPopup");
            }

            if (selectedIdWeight !== null) {
                const newlySelected = document.querySelector(`li[data-id="${selectedIdWeight}"]`);
                if (newlySelected) newlySelected.classList.add('selected');
            }
            const selected = document.querySelector('.list-in li.selected');
            if (selected) {
                selected.scrollIntoView({
                    behavior: 'instant',
                    block: 'nearest',
                    inline: 'start'
                });
            }
        } else {
            // NUOVO: Controlla need_to_confirm anche quando l'ID non cambia
            if (obj.id_selected.need_to_confirm === true) {
                handleNeedToConfirm(obj.data_in_execution.vehicle.plate.replace("⭐", ""));
            }
        }
        populateListIn();
    } else if (obj.access) {
        populateListIn();
    } else if (obj.message) {
        showSnackbar("snackbar", obj.message, 'rgb(208, 255, 208)', 'black');
    } else if (obj.error_message) {
        showSnackbar("snackbar", obj.error_message, 'rgb(255, 208, 208)', 'black');
    } else if (obj.cam_message) {
        showSnackbar("snackbar2", obj.cam_message, 'white', 'black');
    }
}

async function diagnostic() {
    try {
        const response = await fetch(`${pathname}/diagnostic.html`);
        
        if (response.status === 404) {
            alert("La pagina di diagnostica non è disponibile.");
            return;
        }
        
        const diagnosticPopup = document.getElementById('diagnosticPopup');
        const popupContent = diagnosticPopup.querySelector('.popup-content');
        const content = diagnosticPopup.querySelector('.content');
        
        // Crea iframe
        const iframe = document.createElement('iframe');
        iframe.src = `${pathname}/diagnostic.html`;
        iframe.style.width = '100%';
        iframe.style.border = 'none';
        iframe.style.visibility = 'hidden';
        iframe.id = 'diagnosticIframe';

        iframe.onload = function() {
            setTimeout(() => {
                try {
                    const innerDoc = iframe.contentDocument || iframe.contentWindow.document;
                    iframe.style.height = innerDoc.documentElement.scrollHeight + 'px';
                } catch (e) {
                    iframe.style.height = '100%';
                } finally {
                    iframe.style.visibility = 'visible';
                }
            }, 100); // Attendi 100ms dopo il caricamento
        };

        popupContent.style.position = 'relative';
        content.innerHTML = '';
        content.appendChild(iframe);
        
        diagnosticPopup.style.display = "flex";
        popupContent.classList.add("show");
        
    } catch (error) {
        console.error('Errore nel caricamento della diagnostica:', error);
        alert("Errore nel caricamento della pagina di diagnostica.");
    }
}

function closeDiagnostic() {
    const diagnosticPopup = document.getElementById('diagnosticPopup');
    const popupContent = diagnosticPopup.querySelector('.popup-content');
    const content = diagnosticPopup.querySelector('.content');
    const iframe = document.getElementById('diagnosticIframe');
    
    if (iframe) {
        // Ferma tutti i processi JavaScript nell'iframe
        iframe.src = 'about:blank'; // Carica una pagina vuota per fermare tutto
        
        // Oppure rimuovi completamente l'iframe
        // iframe.remove();
    }
    
    // Rimuovi la classe per nascondere con animazione
    popupContent.classList.remove("show");
    
    // Nascondi il popup dopo l'animazione
    setTimeout(() => {
        diagnosticPopup.style.display = "none";
        content.innerHTML = ''; // Pulisci tutto il contenuto
    }, 300); // Tempo della transizione
}

async function printLastInOut() {
    const r = await fetch(`${pathname}/api/anagrafic/access/in-out/print-last${currentWeigherPath}`)
    .then(res => res.json())
    .catch(error => console.error('Errore nella fetch:', error));
    if (r.detail || (r.command_details && r.command_details.command_executed === false)) showSnackbar("snackbar", r.detail || r.command_details.error_message, 'rgb(255, 208, 208)', 'black');
    else showSnackbar("snackbar", r.message, 'rgb(208, 255, 208)', 'black');
}

async function handleTara() {
    const r = await fetch(`${pathname}/api/command-weigher/tare${currentWeigherPath}`)
    .then(res => res.json())
    .catch(error => console.error('Errore nella fetch:', error));
    if (r.detail || (r.command_details && r.command_details.command_executed === false)) showSnackbar("snackbar", r.detail || r.command_details.error_message, 'rgb(255, 208, 208)', 'black');
}

async function handleZero() {
    await fetch(`${pathname}/api/command-weigher/zero${currentWeigherPath}`)
    .then(res => res.json())
    .catch(error => console.error('Errore nella fetch:', error));
}

async function handlePTara() {
    let preset_tare = 0;
    if (myNumberInput.value) preset_tare = myNumberInput.value;
    const r = await fetch(`${pathname}/api/command-weigher/tare/preset${currentWeigherPath}&tare=${preset_tare}`)
    .then(res => {
        closePopup();
        return res.json();
    })
    .catch(error => console.error('Errore nella fetch:', error));
    if (r.detail || (r.command_details && r.command_details.command_executed === false)) showSnackbar("snackbar", r.detail || r.command_details.error_message, 'rgb(255, 208, 208)', 'black');
}

async function handleStampa() {
    buttons.forEach(button => {
        button.disabled = true;
        button.classList.add("disabled-button"); // Aggi
    });
    const r = await fetch(`${pathname}/api/command-weigher/print${currentWeigherPath}`)
    .then(res => {
        return res.json();
    })
    .catch(error => console.error('Errore nella fetch:', error));
    if (r.command_details.command_executed == true) {
        showSnackbar("snackbar", "Pesando...", 'rgb(208, 255, 208)', 'black');
        if (return_pdf_copy_after_weighing) access_id = r.access_id;
    } else {
        showSnackbar("snackbar", r.command_details.error_message, 'rgb(255, 208, 208)', 'black');
        buttons.forEach(button => {
            button.disabled = false;
            button.classList.remove("disabled-button"); // Aggi
        });
    }            
}

async function inWeighing(close=true) {
    if (close) closePopup();
    buttons.forEach(button => {
        button.disabled = true;
        button.classList.add("disabled-button"); // Aggi
    });
    const r = await fetch(`${pathname}/api/command-weigher/in${currentWeigherPath}`,
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
        showSnackbar("snackbar", "Pesando...", 'rgb(208, 255, 208)', 'black');
        if (return_pdf_copy_after_weighing) access_id = r.access_id;
    } else {
        showSnackbar("snackbar", r.command_details.error_message, 'rgb(255, 208, 208)', 'black');
        buttons.forEach(button => {
            button.disabled = false;
            button.classList.remove("disabled-button"); // Aggi
        });
    }                
}

async function handlePesata() {
    if (data_weight_realtime.over_max_theshold) {
        confirmWeighing = inWeighing;
        document.getElementById("over_max_theshold_description").innerHTML = `Soglia massima di <strong>${maxThesholdValue} kg</strong> superata, procedere con la pesatura?`;
        openPopup('confirmPopup');
    } else await inWeighing();
}

async function outWeighing(close=true) {
    if (close) closePopup();
    buttons.forEach(button => {
        button.disabled = true;
        button.classList.add("disabled-button"); // Aggi
    });
    const r = await fetch(`${pathname}/api/command-weigher/out${currentWeigherPath}`, {
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
        showSnackbar("snackbar", "Pesando...", 'rgb(208, 255, 208)', 'black');
        if (return_pdf_copy_after_weighing) access_id = r.access_id;
    } else {
        showSnackbar("snackbar", r.command_details.error_message, 'rgb(255, 208, 208)', 'black');
        buttons.forEach(button => {
            button.disabled = false;
            button.classList.remove("disabled-button"); // Aggi
        });
    }                
}

async function handlePesata2() {
    if (data_weight_realtime.over_max_theshold) {
        confirmWeighing = outWeighing;
        document.getElementById("over_max_theshold_description").innerHTML = `Soglia massima di <strong>${maxThesholdValue} kg</strong> superata, procedere con la pesatura?`;
        openPopup('confirmPopup');
    } else await outWeighing();
}

async function confirmSemiAutomatic() {
    if (/[0-9]/.test(String(data_weight_realtime.potential_net_weight)) || /[1-9]/.test(String(data_weight_realtime.tare.replace("PT", "")))) outWeighing(false);
    else inWeighing(false);
}

function handleNeedToConfirm(plate) {
    console.log(plate);
    confirmWeighing = confirmSemiAutomatic;
    document.getElementById("over_max_theshold_description").innerHTML = 
        `Lettura automatica della targa <strong>'${plate}'</strong>. <br> Effettuare la pesatura?`;
    openPopup('confirmPopup');
    const closeButton = document.querySelector('#confirmPopup .close-button');
    if (handleClickNeedToConfirm) closeButton.removeEventListener('click', handleClickNeedToConfirm); // Rimuovi il vecchio listener
    handleClickNeedToConfirm = () => {
        fetch(`/api/data${currentWeigherPath}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(res => res.status)
        .then(r => {
            if (r === 200) {
                closePopup();
            }
        });
    };
    closeButton.addEventListener('click', handleClickNeedToConfirm);
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

function getParamsFromQueryString() {
  const params = new URLSearchParams(currentWeigherPath);
  const result = {};

  if (params.has('instance_name')) {
    result.instance_name = params.get('instance_name');
  }

  if (params.has('weigher_name')) {
    result.weigher_name = params.get('weigher_name');
  }

  return result;
}

// ===== FUNZIONI PER GESTIRE I TAB MOBILI =====

function toggleTab(tabName) {
    const anagraficElement = document.querySelector('.anagrafic');
    const insElement = document.querySelector('.ins');
    const overlay = document.getElementById('mobileOverlay');

    if (tabName === 'anagrafic') {
        // Chiudi ins se aperto
        insElement.classList.remove('active');

        // Toggle anagrafic
        const wasActive = anagraficElement.classList.contains('active');
        anagraficElement.classList.toggle('active');

        // Mostra/nascondi overlay
        if (anagraficElement.classList.contains('active')) {
            overlay.classList.add('show');
            anagraficViewed = true;
            document.getElementById('badgeAnagrafic').classList.remove('show');
        } else {
            overlay.classList.remove('show');
        }
    } else if (tabName === 'ins') {
        // Chiudi anagrafic se aperto
        anagraficElement.classList.remove('active');

        // Toggle ins
        const wasActive = insElement.classList.contains('active');
        insElement.classList.toggle('active');

        // Mostra/nascondi overlay
        if (insElement.classList.contains('active')) {
            overlay.classList.add('show');
            insViewed = true;
            document.getElementById('badgeIns').classList.remove('show');
        } else {
            overlay.classList.remove('show');
        }
    }
}

function closeTab(tabName) {
    const element = document.querySelector(`.${tabName}`);
    const overlay = document.getElementById('mobileOverlay');
    if (element) {
        element.classList.remove('active');
        overlay.classList.remove('show');
    }
}

function closeAllTabs() {
    const anagraficElement = document.querySelector('.anagrafic');
    const insElement = document.querySelector('.ins');
    const overlay = document.getElementById('mobileOverlay');

    if (anagraficElement) anagraficElement.classList.remove('active');
    if (insElement) insElement.classList.remove('active');
    if (overlay) overlay.classList.remove('show');
}

function initTabNotifications() {
    // Controlla se ci sono già dati in esecuzione al caricamento della pagina
    checkInitialData();
}

function checkInitialData() {
    // Questa funzione verrà chiamata dopo che getData() ha popolato dataInExecution
    setTimeout(() => {
        if (dataInExecution) {
            // Controlla se ci sono dati compilati in anagrafic
            const hasAnagraficData =
                (dataInExecution.vehicle && dataInExecution.vehicle.plate) ||
                (dataInExecution.subject && dataInExecution.subject.social_reason) ||
                (dataInExecution.vector && dataInExecution.vector.social_reason) ||
                (dataInExecution.material && dataInExecution.material.description) ||
                dataInExecution.note ||
                dataInExecution.document_reference;

            if (hasAnagraficData && window.innerWidth <= 800) {
                document.getElementById('badgeAnagrafic').classList.add('show');
            }

            // Salva lo stato iniziale
            lastDataInExecution = JSON.stringify(dataInExecution);
        }

        // Controlla se ci sono accessi nella lista ins e inizializza il contatore
        const listIn = document.querySelector('.list-in');
        if (listIn) {
            lastInsCount = listIn.children.length;
        }
    }, 1000);
}

function checkInsData() {
    const listIn = document.querySelector('.list-in');
    if (listIn && window.innerWidth <= 800) {
        const currentCount = listIn.children.length;

        // Se il numero di accessi è cambiato o ce ne sono di nuovi
        if (currentCount > 0 && currentCount !== lastInsCount) {
            insViewed = false; // Resetta il flag quando cambiano gli accessi
            document.getElementById('badgeIns').classList.add('show');
        }

        lastInsCount = currentCount;
    }
}

function checkDataChanges() {
    // Controlla solo se siamo su mobile
    if (window.innerWidth > 800) return;

    const currentData = JSON.stringify(dataInExecution);

    // Se i dati sono cambiati
    if (currentData !== lastDataInExecution && !document.querySelector(".anagrafic").classList.contains("active")) {
        // Resetta il flag e mostra il badge quando i dati cambiano
        anagraficViewed = false;
        document.getElementById('badgeAnagrafic').classList.add('show');
    }

    lastDataInExecution = currentData;
}

// Osserva i cambiamenti nella lista ins
const insObserver = new MutationObserver(() => {
    if (window.innerWidth <= 800) {
        const listIn = document.querySelector('.list-in');
        if (listIn) {
            const currentCount = listIn.children.length;

            // Se il numero di accessi è cambiato
            if (currentCount > 0 && currentCount !== lastInsCount) {
                insViewed = false; // Resetta il flag
                document.getElementById('badgeIns').classList.add('show');
                lastInsCount = currentCount;
            }
        }
    }
});

// Inizia ad osservare quando il DOM è pronto
document.addEventListener('DOMContentLoaded', () => {
    const listIn = document.querySelector('.list-in');
    if (listIn) {
        insObserver.observe(listIn, { childList: true, subtree: true });
    }
});