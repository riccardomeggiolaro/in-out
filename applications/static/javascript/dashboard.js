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

let reservation_id;

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
        closeWebSocket();
        document.getElementById('netWeight').innerText = "N/A";
        document.getElementById('uniteMisure').innerText = "N/A";
        document.getElementById('tare').innerText = "N/A";
        document.getElementById('status').innerText = "N/A";
        connectWebSocket(`api/command-weigher/realtime${currentWeigherPath}`, updateUIRealtime)
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
        if (!obj.events.weighing.print.in && !obj.events.weighing.print.out) reprint.style.display = 'none';
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
        dataInExecution = res["data_in_execution"];
        const obj = res["data_in_execution"];
        selectedIdVehicle = obj.vehicle.id;
        selectedIdTypeSubject = obj.typeSubject;
        selectedIdSubject = obj.subject.id;
        selectedIdVector = obj.vector.id;
        selectedIdMaterial = obj.material.id;
        document.querySelector('#currentPlateVehicle').value = obj.vehicle.plate ? obj.vehicle.plate : '';
        document.querySelector('#typeSubject').value = obj.typeSubject ? obj.typeSubject : 'CUSTOMER';
        document.querySelector('#currentSocialReasonSubject').value = obj.subject.social_reason ? obj.subject.social_reason : '';
        document.querySelector('#currentSocialReasonVector').value = obj.vector.social_reason ? obj.vector.social_reason : '';
        document.querySelector('#currentDescriptionMaterial').value = obj.material.description ? obj.material.description : '';
        document.querySelector('#currentNote').value = obj.note ? obj.note : '';            
        document.querySelector('#currentDocumentReference').value = obj.document_reference ? obj.document_reference : '';
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

    await fetch('/api/anagrafic/reservation/list?excludeTestWeighing=true&status=NOT_CLOSED')
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
            if (item.vehicle && item.vehicle.plate) content = `${item.vehicle.plate}`;
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
                await fetch(`/api/data${currentWeigherPath}`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(obj)
                })
                .then(res => res.json())
                .then(res => {
                    if (res.detail) showSnackbar(res.detail, 'rgb(255, 208, 208)', 'black');
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
    if (suggestionsList && suggestionsList.children.length === 1 && suggestionsList.children[0].textContent === value) {
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
        if (res.detail) showSnackbar(res.detail, 'rgb(255, 208, 208)', 'black');
        else closePopup();
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

    let url = `/api/anagrafic/${name_list}/list`;

    if (inputValue) url += `?${filter}=${inputValue}%`;

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
                    if (res.detail) showSnackbar(res.detail, 'rgb(255, 208, 208)', 'black');
                    else closePopup();
                });
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
    if (currentPopup) {
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

    closeWebSocket(); // Chiude la connessione WebSocket precedente se esiste

    _data = new WebSocket(websocketUrl);

    _data.addEventListener('message', (e) => {
        exe(e);
    });

    _data.addEventListener('open', () => {
        enableAllElements();
        reconnectionButton.disabled = true;
        closePopup('reconnectionPopup');
    })

    _data.addEventListener('error', () => {
        if (!isRefreshing) {
            closeWebSocket();
            disableAllElements();
            reconnectionButton.disabled = false;
            document.querySelector('#reconnectionPopup .popup-content p').textContent = "Clicca ok per riconnettere...";
            openPopup('reconnectionPopup');
        }
    });

    _data.addEventListener('close', () => {
        if (!isRefreshing) {
            disableAllElements();
            reconnectionButton.disabled = false;
            document.querySelector('#reconnectionPopup .popup-content p').textContent = "Clicca ok per riconnettere...";
            openPopup('reconnectionPopup');
        }
    });
}

function attemptReconnect() {
    reconnectionButton.disabled = true;
    closeWebSocket();
    document.querySelector('#reconnectionPopup .popup-content p').textContent = "Riconnessione in corso...";
    connectWebSocket(`api/command-weigher/realtime${currentWeigherPath}`, updateUIRealtime);
}

function closeWebSocket() {
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
        if (obj.command_in_executing == "TARE") showSnackbar("Tara", 'rgb(208, 255, 208)', 'black');
        if (obj.command_in_executing == "PRESETTARE") showSnackbar("Preset tara", 'rgb(208, 255, 208)', 'black');
        if (obj.command_in_executing == "ZERO") showSnackbar("Zero", 'rgb(208, 255, 208)', 'black');
        if (obj.command_in_executing == "WEIGHING") {
            showSnackbar("Pesando...", 'rgb(208, 255, 208)', 'black');
            buttons.forEach(button => {
                button.disabled = true;
                button.classList.add("disabled-button"); // Aggi
            });
        }                    
    } else if (obj.weight_executed) {
        if (obj.weight_executed.gross_weight != "") {
            let message = `Pesata eseguita! Bilancia: ${obj.weigher_name}.`;
            if (obj.weight_executed.pid != "") {
                message += ` Pid: ${obj.weight_executed.pid}`;
                obj.data_assigned = JSON.parse(obj.data_assigned);
                if (obj.data_assigned.id === reservation_id) {
                    const id_in_out = obj.data_assigned.in_out[obj.data_assigned.in_out.length-1]["id"]
                    fetch(`/api/anagrafic/reservation/in-out/pdf/${id_in_out}`)
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
            showSnackbar(message, 'rgb(208, 255, 208)', 'black');
            populateListIn();
        } else { 
            showSnackbar("Pesata fallita", 'rgb(255, 208, 208)', 'black');
        }
        reservation_id = null;
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
        //     }
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
        document.querySelector('#currentPlateVehicle').value = obj.data_in_execution.vehicle.plate ? obj.data_in_execution.vehicle.plate : '';
        document.querySelector('#typeSubject').value = obj.data_in_execution.typeSubject ? obj.data_in_execution.typeSubject : 'CUSTOMER';
        document.querySelector('#currentSocialReasonSubject').value = obj.data_in_execution.subject.social_reason ? obj.data_in_execution.subject.social_reason : '';
        document.querySelector('#currentSocialReasonVector').value = obj.data_in_execution.vector.social_reason ? obj.data_in_execution.vector.social_reason : '';
        document.querySelector('#currentDescriptionMaterial').value = obj.data_in_execution.material.description ? obj.data_in_execution.material.description : '';
        document.querySelector('#currentNote').value = obj.data_in_execution.note ? obj.data_in_execution.note : '';
        document.querySelector('#currentDocumentReference').value = obj.data_in_execution.document_reference ? obj.data_in_execution.document_reference : '';
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
        } else {
            populateListIn();
        }
        // if (obj.id_selected.id === null) {
        //     // Seleziona tutti i pulsanti e gli input
        //     const buttonsAndInputs = document.querySelectorAll('.anagrafic input, .anagrafic select');
        //     // Disabilita ogni elemento trovato
        //     buttonsAndInputs.forEach(element => {
        //         element.disabled = false;
        //     });
        // } else {
        //     // Seleziona tutti i pulsanti e gli input
        //     const buttonsAndInputs = document.querySelectorAll('.anagrafic input, .anagrafic select');
        //     // Disabilita ogni elemento trovato
        //     buttonsAndInputs.forEach(element => {
        //         element.disabled = true;
        //     });
        // }
    } else if (obj.reservation) {
        populateListIn();       
    } else if (obj.message) {
        showSnackbar(obj.message, 'rgb(208, 255, 208)', 'black');
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
        iframe.style.height = '100%';
        iframe.style.border = 'none';
        iframe.id = 'diagnosticIframe'; // Aggiungi un ID per riferimento
        
        // Svuota il contenuto e aggiungi iframe e pulsante
        popupContent.style.position = 'relative'; // Per posizionare il pulsante
        content.innerHTML = '';
        content.appendChild(iframe);
        
        // Mostra popup
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
    const r = await fetch(`${pathname}/api/anagrafic/reservation/in-out/print-last${currentWeigherPath}`)
    .then(res => res.json())
    .catch(error => console.error('Errore nella fetch:', error));
    if (r.detail || (r.command_details && r.command_details.command_executed === false)) showSnackbar(r.detail || r.command_details.error_message, 'rgb(255, 208, 208)', 'black');
    else showSnackbar(r.message, 'rgb(208, 255, 208)', 'black');
}

async function handleTara() {
    const r = await fetch(`${pathname}/api/command-weigher/tare${currentWeigherPath}`)
    .then(res => res.json())
    .catch(error => console.error('Errore nella fetch:', error));
    if (r.detail || (r.command_details && r.command_details.command_executed === false)) showSnackbar(r.detail || r.command_details.error_message, 'rgb(255, 208, 208)', 'black');
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
    if (r.detail || (r.command_details && r.command_details.command_executed === false)) showSnackbar(r.detail || r.command_details.error_message, 'rgb(255, 208, 208)', 'black');
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
        showSnackbar("Pesando...", 'rgb(208, 255, 208)', 'black');
        if (return_pdf_copy_after_weighing) reservation_id = r.reservation_id;
    } else {
        showSnackbar(r.command_details.error_message, 'rgb(255, 208, 208)', 'black');
        buttons.forEach(button => {
            button.disabled = false;
            button.classList.remove("disabled-button"); // Aggi
        });
    }            
}

async function inWeighing() {
    closePopup();
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
        showSnackbar("Pesando...", 'rgb(208, 255, 208)', 'black');
        if (return_pdf_copy_after_weighing) reservation_id = r.reservation_id;
    } else {
        showSnackbar(r.command_details.error_message, 'rgb(255, 208, 208)', 'black');
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

async function outWeighing () {
    closePopup();
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
        showSnackbar("Pesando...", 'rgb(208, 255, 208)', 'black');
        if (return_pdf_copy_after_weighing) reservation_id = r.reservation_id;
    } else {
        showSnackbar(r.command_details.error_message, 'rgb(255, 208, 208)', 'black');
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

function validatePlate(input) {
    // Convert to uppercase
    input.value = input.value.toUpperCase();
    
    // Show suggestions
    showSuggestions('vehicle', 'plateVehicleInput', 'plate', input.value, 
        ['description', 'date_created'], 'plateVehiclePopup', 'suggestionsListPlateVehicle');
    
    // Validate plate format
    const platePattern = /^[A-Z]{2}\d{3}[A-Z]{2}$/;
    const isValid = platePattern.test(input.value) || input.value === '';

    // Get the submit button
    const submitButton = document.getElementById('plateSubmitButton');
    
    // Enable/disable button based on validation
    submitButton.disabled = !isValid;
}