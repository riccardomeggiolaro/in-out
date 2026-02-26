let list_serial_ports = []

let list_printer_names = []

let list_terminal_types = []

let template_report_in = new DataTransfer();

let template_report_out = new DataTransfer();

const editButtonContent = "✏️"

const deleteButtonContent = "🗑️";

const autoWeighingButtonContent = "🔗";

// Creiamo e dispatchiamo l'evento manualmente
const event = new Event('input', {
    bubbles: true,
    cancelable: true,
});

async function getSerialPortsList() {
    await fetch('/api/generic/list/serial-ports')
    .then(res => res.json())
    .then(data => {
        list_serial_ports = data.list_serial_ports;
    })
}

async function getPrintersList() {
    await fetch('/api/printer/list')
    .then(res => res.json())
    .then(data => {
        list_printer_names = data;
    });
}

async function getTerminalTypes() {
    await fetch('/api/config-weigher/terminals')
    .then(res => res.json())
    .then(data => {
        list_terminal_types = data;
    });
}

async function getReportIn() {
    const response = await fetch('/api/generic/report-in');

    if (!response.ok) return;

    const blob = await response.blob();
    
    // Extrair filename do cabeçalho Content-Disposition
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = '';
    
    if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch) {
            filename = filenameMatch[1].replace(/['"]/g, '');
        }
    }
    
    // Criar novo blob com nome
    const namedBlob = new File([blob], filename, { type: blob.type });
    template_report_in.items.add(namedBlob);
}

async function getReportOut() {
    const response = await fetch('/api/generic/report-out');

    if (!response.ok) return;

    const blob = await response.blob();

    // Extrair filename do cabeçalho Content-Disposition
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = '';

    if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch) {
            filename = filenameMatch[1].replace(/['"]/g, '');
        }
    }

    // Criar novo blob com nome   
    const namedBlob = new File([blob], filename, { type: blob.type });
    template_report_out.items.add(namedBlob);
}

function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        // Metodo moderno (HTTPS/localhost)
        navigator.clipboard.writeText(text).then(() => {
            document.body.removeChild(modal);
            showSnackbar("snackbar", "Url copiata correttamente negli appunti", 'rgb(208, 255, 208)', 'black');
        }).catch(err => {
            console.error('Errore nel copiare:', err);
            fallbackCopyTextToClipboard(text);
        });
    } else {
        // Fallback per HTTP
        fallbackCopyTextToClipboard(text);
    }
}

function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.position = "fixed";
    textArea.style.opacity = "0";
    
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        document.body.removeChild(textArea);
        
        if (successful) {
            showSnackbar("snackbar", "Url copiata correttamente negli appunti", 'rgb(208, 255, 208)', 'black');
        } else {
            showSnackbar("snackbar", "Impossibile copiare automaticamente. Seleziona e copia manualmente.", 'rgb(255, 208, 208)', 'black');
        }
    } catch (err) {
        document.body.removeChild(textArea);
        console.error('Fallback: Impossibile copiare', err);
        showSnackbar("snackbar", "Errore nella copia. Riprova manualmente.", 'rgb(255, 208, 208)', 'black');
    }
}

document.addEventListener("DOMContentLoaded", loadSetupWeighers);

async function loadSetupWeighers() {
    const weighers_config = document.getElementById('config');

    const br = document.createElement("br");

    const settings = weighers_config.querySelector('#settings');

    const instances = weighers_config.querySelector('#instances');

    weighers_config.appendChild(br.cloneNode(true));
    weighers_config.appendChild(settings);
    weighers_config.appendChild(instances);

    await getSerialPortsList();

    await getPrintersList();

    await getTerminalTypes();

    await getReportIn();

    await getReportOut();

    const addCam = (e, classNameForm, className, picture, active) => {
        const form = document.querySelector(classNameForm);

        if (e) e.preventDefault();
        
        const divCam = document.createElement("div");
        divCam.className = "cam";
        divCam.innerHTML = `
            <button class="delete-btn">${deleteButtonContent}</button>
            <input type="url" placeholder="http://0.0.0.0/" value="${picture ? picture : ''}" required>
            <input type="checkbox" ${active === undefined || active === true ? 'checked' : ''}> <span>Attiva</span>
        `;
        
        // Aggiungi l'event listener al pulsante
        const deleteButton = divCam.querySelector('.delete-btn');
        deleteButton.addEventListener('click', (e) => {
            e.preventDefault();
            divCam.remove();
            form.dispatchEvent(event);
        });
        
        document.querySelector(`.${className}`).append(divCam);
        form.dispatchEvent(event);
    }

    const addRele = (e, classNameForm, className, number_rele, status, on_event) => {
        const form = document.querySelector(classNameForm);

        if (e) e.preventDefault();
        
        const divRele = document.createElement("div");
        divRele.className = "rele";
        divRele.innerHTML = `
            <button class="delete-btn">${deleteButtonContent}</button>
            <span>Numero: </span> <input type="number" min="1" value="${number_rele ? number_rele : ''}" style="width: 50px" required>
            <select style="width: 75px">
                <option value="1" ${status === 1 ? 'selected' : ''}>Attiva</option>
                <option value="0" ${status === 0 ? 'selected' : ''}>Disattiva</option>
            </select>
            <select style="width: 150px">
                <option value="weighing" ${on_event === "weighing" ? 'selected' : ''}>Dopo la pesata</option>
                <option value="over_min" ${on_event === "over_min" ? 'selected' : ''}>Sopra peso minimo</option>
                <option value="under_min" ${on_event === "under_min" ? 'selected' : ''}>Sotto peso minimo</option>
            </select>
        `;
        
        // Aggiungi l'event listener al pulsante
        const deleteButton = divRele.querySelector('.delete-btn');
        deleteButton.addEventListener('click', (e) => {
            e.preventDefault();
            divRele.remove();
            form.dispatchEvent(event);
        });
        
        document.querySelector(`.${className}`).append(divRele);
        form.dispatchEvent(event);
    }

    window.addCam = addCam;
    window.addRele = addRele;
    
    await fetch('/api/config-weigher/configuration')
    .then(res => res.json())
    .then(data => {
        const options = [
            {
                "value": "MANUALLY",
                "description": "Manuale"
            },
            {
                "value": "AUTOMATIC",
                "description": "Automatico"
            },
            {
                "value": "SEMIAUTOMATIC",
                "description": "Semiautomatico"
            }
        ];
        const modes = document.createElement('div');
        options.forEach((option, index) => {
            const labelMode = document.createElement('label');
            labelMode.setAttribute('for', `radio-${index}`); 
            labelMode.textContent = ` ${option.description} `;
            const mode = document.createElement('input');
            mode.type = 'radio';
            mode.name = 'option'; // tutti i radio button devono avere lo stesso nome
            mode.value = option.value;
            mode.id = `radio-${index}`;  // Assign a unique ID for each radio button
            if (mode.value === data.mode) mode.checked = true;
            // Aggiungi l'evento onchange per ogni radio button
            mode.onchange = (e) => {
                const selected = e.target.value;
                fetch(`/api/config-weigher/configuration/mode/${selected}`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Risposta ricevuta:', data);
                    // Puoi aggiornare l'interfaccia o fare altro con la risposta
                })
                .catch(error => {
                    console.error('Errore durante la richiesta:', error);
                });
            };
            modes.appendChild(mode);
            modes.appendChild(labelMode);
        });
        const labelAccess = document.createElement('label');
        const access = document.createElement('input');
        labelAccess.innerHTML = "Usa <b><u>prenotazioni</u></b>: ";
        access.type = 'checkbox';
        access.checked = data.use_reservation ? true : false;
        access.onchange = (e) => {
            const checked = e.target.checked;
            fetch(`/api/config-weigher/configuration/use-reservation/${checked}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
        }
        const labelBadge = document.createElement('label');
        const badge = document.createElement('input');
        labelBadge.innerHTML = "Usa <b><u>badge</u></b> per riconoscimento tramite tessere: ";
        badge.type = 'checkbox';
        badge.checked = data.use_badge ? true : false;
        badge.onchange = (e) => {
            const checked = e.target.checked;
            fetch(`/api/config-weigher/configuration/use-badge/${checked}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
        }       
        const labelReturnPdfCopyAfterWeighing = document.createElement('label');
        const returnPdfCopyAfterWeighing = document.createElement('input');
        labelReturnPdfCopyAfterWeighing.textContent = "Ritorna copia del report a chi effettua la pesata: ";
        returnPdfCopyAfterWeighing.type = 'checkbox';
        returnPdfCopyAfterWeighing.checked = data.return_pdf_copy_after_weighing ? true : false;
        returnPdfCopyAfterWeighing.onchange = (e) => {
            const checked = e.target.checked;
            fetch(`/api/config-weigher/configuration/return-pdf-copy-after-weighing/${checked}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(res => res.json())
        }
        const labelUseDeclarativeWeighing = document.createElement('label');
        const useDeclarativeWeighing = document.createElement('input');
        labelUseDeclarativeWeighing.textContent = "Usa peso preimpostato con netto negativo (P.Peso): ";
        useDeclarativeWeighing.type = 'checkbox';
        useDeclarativeWeighing.checked = data.use_declarative_weighing ? true : false;
        useDeclarativeWeighing.onchange = (e) => {
            const checked = e.target.checked;
            fetch(`/api/config-weigher/configuration/use-declarative-weighing/${checked}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(res => res.json())
        }
        const labelReportInt = document.createElement('label');
        const buttonReportDesignerTemplateIn = document.createElement('button');
        labelReportInt.innerHTML = "Report di stampa per l'<b><u>entrata</u></b>: ";
        buttonReportDesignerTemplateIn.textContent = "Apri report designer";
        buttonReportDesignerTemplateIn.onclick = () => window.open('/report-designer/entrata', '_blank');
        const labelReportOut = document.createElement('label');
        const buttonReportDesignerTemplateOut = document.createElement('button');
        labelReportOut.innerHTML = "Report di stampa per l'<b><u>uscita</u></b>: ";
        buttonReportDesignerTemplateOut.textContent = "Apri report designer";
        buttonReportDesignerTemplateOut.onclick = () => window.open('/report-designer/uscita', '_blank');
        const br = document.createElement('br');
        const labelSavePdfPath = document.createElement('label');
        const savePdfPath = document.createElement('input');
        const savePdfPathButton = document.createElement('button');
        let originalPathPdf = data.path_pdf ? data.path_pdf : '';
        labelSavePdfPath.innerHTML = "Directory salvataggio report pesata in <b><u>pdf</u></b>: ";
        savePdfPath.type = 'text';
        savePdfPath.value = data.path_pdf ? data.path_pdf : '';
        savePdfPathButton.textContent = 'Salva';
        savePdfPathButton.disabled = true;
        savePdfPath.oninput = (e) => {
            const value = e.target.value;
            if (value !== originalPathPdf) {
                savePdfPathButton.disabled = false;
            } else {
                savePdfPathButton.disabled = true;
            }
        }
        savePdfPathButton.onclick = (e) => {
            const value = savePdfPath.value;
            fetch(`/api/config-weigher/configuration/path-pdf`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ path: value ? value : null })
            })
            .then(res => {
                if (res.ok) {
                    showSnackbar("snackbar", "Directory salvata correttamente", 'rgb(208, 255, 208)', 'black');
                    savePdfPathButton.disabled = true;
                    originalPathPdf = value;
                } else {
                    showSnackbar("snackbar", "Directory non valida", 'rgb(255, 208, 208)', 'black');
                    savePdfPath.value = originalPathPdf;
                }
            })
        }
        const labelSaveCsvPath = document.createElement('label');
        const saveCsvPath = document.createElement('input');
        const saveCsvPathButton = document.createElement('button');
        let originalPathCsv = data.path_csv ? data.path_csv : '';
        labelSaveCsvPath.innerHTML = "Directory salvataggio pesata in <b><u>csv</u></b>: ";
        saveCsvPath.type = 'text';
        saveCsvPath.value = data.path_csv ? data.path_csv : '';
        saveCsvPathButton.textContent = 'Salva';
        saveCsvPathButton.disabled = true;
        saveCsvPath.oninput = (e) => {
            const value = e.target.value;
            if (value !== originalPathCsv) {
                saveCsvPathButton.disabled = false;
            } else {
                saveCsvPathButton.disabled = true;
            }
        }
        saveCsvPathButton.onclick = (e) => {
            const value = saveCsvPath.value;
            fetch(`/api/config-weigher/configuration/path-csv`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ path: value ? value : null})
            })
            .then(res => {
                if (res.ok) {
                    showSnackbar("snackbar", "Directory salvata correttamente", 'rgb(208, 255, 208)', 'black');
                    saveCsvPathButton.disabled = true;
                    originalPathCsv = value;
                } else {
                    showSnackbar("snackbar", "Directory non valida", 'rgb(255, 208, 208)', 'black');
                    saveCsvPath.value = originalPathCsv;
                }
            })
        }
        const labelSaveImgPath = document.createElement('label');
        const saveImgPath = document.createElement('input');
        const saveImgPathButton = document.createElement('button');
        let originalPathImg = data.path_img ? data.path_img : '';
        labelSaveImgPath.innerHTML = "Directory salvataggio <b><u>immagini</u></b>: ";
        saveImgPath.type = 'text';
        saveImgPath.value = data.path_img ? data.path_img : '';
        saveImgPathButton.textContent = 'Salva';
        saveImgPathButton.disabled = true;
        saveImgPath.oninput = (e) => {
            const value = e.target.value;
            if (value !== originalPathImg) {
                saveImgPathButton.disabled = false;
            } else {
                saveImgPathButton.disabled = true;
            }
        }
        saveImgPathButton.onclick = (e) => {
            const value = saveImgPath.value;
            fetch(`/api/config-weigher/configuration/path-img`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ path: value ? value : null })
            })
            .then(res => {
                if (res.ok) {
                    showSnackbar("snackbar", "Directory salvata correttamente", 'rgb(208, 255, 208)', 'black');
                    saveImgPathButton.disabled = true;
                    originalPathImg = value;
                } else {
                    showSnackbar("snackbar", "Directory non valida", 'rgb(255, 208, 208)', 'black');
                    saveImgPath.value = originalPathImg;
                }
            })
        }
        const labelIp = document.createElement('label');
        labelIp.textContent = "IP: * "
        const ip = document.createElement('input');
        let originalIp = data.sync_folder.remote_folder ? data.sync_folder.remote_folder.ip : '';
        ip.value = originalIp;
        ip.oninput = () => isValidForm();
        const labelDomain = document.createElement('label');
        labelDomain.textContent = "Dominio: "
        const domain = document.createElement('input');
        let originalDomain = data.sync_folder.remote_folder ? data.sync_folder.remote_folder.domain : '';
        domain.value = originalDomain;
        domain.oninput = () => isValidForm();
        const labelShareName = document.createElement('label');
        labelShareName.textContent = "Cartella condivisa: * "
        const shareName = document.createElement('input');
        let originalShareName = data.sync_folder.remote_folder ? data.sync_folder.remote_folder.share_name : '';
        shareName.value = originalShareName;
        shareName.oninput = () => isValidForm();
        const labelSubPath = document.createElement('label');
        labelSubPath.textContent = "Sotto cartella: "
        const subPath = document.createElement('input');
        let originalSubPath = data.sync_folder.remote_folder ? data.sync_folder.remote_folder.sub_path : '';
        subPath.value = originalSubPath;
        subPath.oninput = () => isValidForm();
        const labelUsername = document.createElement('label');
        labelUsername.textContent = "Username: * "
        const username = document.createElement('input');
        let originalUsername = data.sync_folder.remote_folder ? data.sync_folder.remote_folder.username : '';
        username.value = originalUsername;
        username.oninput = () => isValidForm();
        const labelPassword = document.createElement('label');
        labelPassword.textContent = "Password: * "
        const password = document.createElement('input');
        let originalPassword = data.sync_folder.remote_folder ? data.sync_folder.remote_folder.password : '';
        password.value = originalPassword;
        password.oninput = () => isValidForm();
        const testConnectionButton = document.createElement('button');
        testConnectionButton.textContent = "Testa connessione";
        testConnectionButton.disabled = originalIp ? false : true;
        testConnectionButton.onclick = () => {
            fetch('/api/sync-folder/test', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(res => res.json())
            .then(res => {
                const message = res.mounted ? "Connesso correttamente" : "Non connessono";
                const color = res.mounted ? 'rgb(208, 255, 208)' : 'rgb(255, 208, 208)';
                showSnackbar("snackbar", message, color, 'black');
            });
        }
        const deleteRemoteFolderButton = document.createElement('button');
        deleteRemoteFolderButton.textContent = "Elimina";
        deleteRemoteFolderButton.disabled = originalIp ? false : true;
        deleteRemoteFolderButton.onclick = () => {
            fetch('/api/sync-folder', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(res => res.json())
            .then(res => {
                const message = res.deleted ? "Connessione eliminata" : "Errore generico durante l'eliminazione";
                const color = res.deleted ? 'rgb(208, 255, 208)' : 'rgb(255, 208, 208)';
                if (res.deleted) {
                    originalIp = "";
                    ip.value = "";
                    originalShareName = "";
                    domain.value = "";
                    originalDomain = "";
                    shareName.value = "";
                    originalSubPath = "";
                    subPath.value = "";
                    originalUsername = "";
                    username.value = "";
                    originalPassword = "";
                    password.value = "";
                    testConnectionButton.disabled = true;
                    deleteRemoteFolderButton.disabled = true;
                    saveRemoteFolderButton.disabled = true;
                }
                showSnackbar("snackbar", message, color, 'black');
            });
        }
        const saveRemoteFolderButton = document.createElement('button');
        saveRemoteFolderButton.textContent = "Salva";
        saveRemoteFolderButton.disabled = true;
        saveRemoteFolderButton.onclick = () => {
            fetch('/api/sync-folder', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    "ip": ip.value,
                    "domain": domain.value,
                    "share_name": shareName.value,
                    "sub_path": subPath.value,
                    "username": username.value,
                    "password": password.value
                })
            })
            .then(res => res.json())
            .then(res => {
                const message = res.remote_folder ? `Configurazione salvata correttamente` : "Configurazione non salvata";
                const color = res.remote_folder ? 'white' : 'rgb(255, 208, 208)';
                if (res.remote_folder) {
                    originalIp = res.remote_folder.ip;
                    originalDomain = res.remote_folder.domain;
                    originalShareName = res.remote_folder.share_name;
                    originalSubPath = res.remote_folder.sub_path;
                    originalUsername = res.remote_folder.username;
                    originalPassword = res.remote_folder.password;
                    testConnectionButton.disabled = false;
                    deleteRemoteFolderButton.disabled = false;
                    saveRemoteFolderButton.disabled = true;
                }
                showSnackbar("snackbar", message, color, 'black');
            });
        }
        const isValidForm = (() => {
            if (
                ip.value.length > 0 &&
                shareName.value.length > 0 &&
                username.value.length > 0 &&
                password.value.length > 0 &&
                (
                    ip.value !== originalIp ||
                    domain.value !== originalDomain ||
                    shareName.value !== originalShareName || 
                    subPath.value !== originalSubPath ||
                    username.value !== originalUsername ||
                    password.value !== originalPassword
                )
            ) {
                testConnectionButton.disabled = originalIp ? false : true;
                deleteRemoteFolderButton.disabled = originalIp ? false : true;
                saveRemoteFolderButton.disabled = false;
            } else {
                testConnectionButton.disabled = originalIp ? false : true;
                deleteRemoteFolderButton.disabled = originalIp ? false : true;
                saveRemoteFolderButton.disabled = true;
            }
        })
        // CONFIGURAZIONE DEGLI ACCESSI
        const divAccess = document.createElement('div');
        const h1Access = document.createElement('h3');
        divAccess.classList.toggle("borders");
        divAccess.classList.toggle("aliceblue");
        h1Access.textContent = 'Accessi';
        divAccess.appendChild(br.cloneNode(true));
        divAccess.appendChild(h1Access);
        divAccess.appendChild(br.cloneNode(true));
        divAccess.appendChild(modes);
        divAccess.appendChild(br.cloneNode(true));
        divAccess.appendChild(labelAccess);
        divAccess.appendChild(access);
        divAccess.appendChild(br.cloneNode(true));
        divAccess.appendChild(br.cloneNode(true));
        divAccess.appendChild(labelBadge);
        divAccess.appendChild(badge);
        divAccess.appendChild(br.cloneNode(true));
        divAccess.appendChild(br.cloneNode(true));
        settings.appendChild(divAccess);
        //////////////////////////////////////////////////////
        settings.appendChild(br.cloneNode(true));
        // CONFIGURATION OF REPORT
        const divReport = document.createElement('div');
        const h1Report = document.createElement('h3');
        divReport.classList.toggle("borders");
        divReport.classList.toggle("aliceblue");
        h1Report.textContent = 'Report';
        divReport.appendChild(br.cloneNode(true));
        divReport.appendChild(h1Report);
        divReport.appendChild(br.cloneNode(true));
        divReport.appendChild(labelReturnPdfCopyAfterWeighing);
        divReport.appendChild(returnPdfCopyAfterWeighing);
        divReport.appendChild(br.cloneNode(true));
        divReport.appendChild(br.cloneNode(true));
        divReport.appendChild(labelUseDeclarativeWeighing);
        divReport.appendChild(useDeclarativeWeighing);
        divReport.appendChild(br.cloneNode(true));
        divReport.appendChild(br.cloneNode(true));
        divReport.appendChild(labelReportInt);
        divReport.appendChild(buttonReportDesignerTemplateIn);
        divReport.appendChild(br.cloneNode(true));
        divReport.appendChild(br.cloneNode(true));
        divReport.appendChild(labelReportOut);
        divReport.appendChild(buttonReportDesignerTemplateOut);
        divReport.appendChild(br.cloneNode(true));
        divReport.appendChild(br.cloneNode(true));
        settings.appendChild(divReport);
        // //////////////////////////////////////////////////////
        // settings.appendChild(br.cloneNode(true));
        // // CONFIGURATION OF DIRECTORIES
        // const divDirectories = document.createElement('div');
        // const h1Directories = document.createElement('h3');
        // divDirectories.classList.toggle("borders");
        // divDirectories.classList.toggle("aliceblue");
        // h1Directories.textContent = 'Percosi di salvataggio';
        // divDirectories.appendChild(br.cloneNode(true));
        // divDirectories.appendChild(h1Directories);
        // divDirectories.appendChild(br.cloneNode(true));
        // divDirectories.appendChild(labelSavePdfPath);
        // divDirectories.appendChild(savePdfPath);
        // divDirectories.appendChild(savePdfPathButton);
        // divDirectories.appendChild(br.cloneNode(true));
        // divDirectories.appendChild(br.cloneNode(true));
        // divDirectories.appendChild(labelSaveCsvPath);
        // divDirectories.appendChild(saveCsvPath);
        // divDirectories.appendChild(saveCsvPathButton);
        // divDirectories.appendChild(br.cloneNode(true));
        // divDirectories.appendChild(br.cloneNode(true));
        // divDirectories.appendChild(labelSaveImgPath);
        // divDirectories.appendChild(saveImgPath);
        // divDirectories.appendChild(saveImgPathButton);
        // divDirectories.appendChild(br.cloneNode(true));
        // divDirectories.appendChild(br.cloneNode(true));
        // settings.appendChild(divDirectories);
        //////////////////////////////////////////////////////
        settings.appendChild(br.cloneNode(true));
        // CONFIGURATION OF SYNC REMOTE FOLDER
        const divSyncRemoteFolder = document.createElement('div');
        const h1SyncRemoteFolder = document.createElement('h3');
        divSyncRemoteFolder.classList.toggle("borders");
        divSyncRemoteFolder.classList.toggle("aliceblue");
        h1SyncRemoteFolder.textContent = 'Sincronizzazione cartella remota';
        divSyncRemoteFolder.appendChild(br.cloneNode(true));
        divSyncRemoteFolder.appendChild(h1SyncRemoteFolder);
        divSyncRemoteFolder.appendChild(br.cloneNode(true));
        divSyncRemoteFolder.appendChild(labelIp);
        divSyncRemoteFolder.appendChild(ip);
        divSyncRemoteFolder.appendChild(br.cloneNode(true));
        divSyncRemoteFolder.appendChild(br.cloneNode(true));
        divSyncRemoteFolder.appendChild(labelDomain);
        divSyncRemoteFolder.appendChild(domain);
        divSyncRemoteFolder.appendChild(br.cloneNode(true));
        divSyncRemoteFolder.appendChild(br.cloneNode(true));
        divSyncRemoteFolder.appendChild(labelShareName);
        divSyncRemoteFolder.appendChild(shareName);
        divSyncRemoteFolder.appendChild(br.cloneNode(true));
        divSyncRemoteFolder.appendChild(br.cloneNode(true));
        divSyncRemoteFolder.appendChild(labelSubPath);
        divSyncRemoteFolder.appendChild(subPath);
        divSyncRemoteFolder.appendChild(br.cloneNode(true));
        divSyncRemoteFolder.appendChild(br.cloneNode(true));
        divSyncRemoteFolder.appendChild(labelUsername);
        divSyncRemoteFolder.appendChild(username);
        divSyncRemoteFolder.appendChild(br.cloneNode(true));
        divSyncRemoteFolder.appendChild(br.cloneNode(true));
        divSyncRemoteFolder.appendChild(labelPassword);
        divSyncRemoteFolder.appendChild(password);
        divSyncRemoteFolder.appendChild(br.cloneNode(true));
        divSyncRemoteFolder.appendChild(br.cloneNode(true));
        divSyncRemoteFolder.appendChild(testConnectionButton);
        divSyncRemoteFolder.appendChild(br.cloneNode(true));
        divSyncRemoteFolder.appendChild(br.cloneNode(true));
        divSyncRemoteFolder.appendChild(deleteRemoteFolderButton);
        divSyncRemoteFolder.appendChild(saveRemoteFolderButton);
        divSyncRemoteFolder.appendChild(br.cloneNode(true));
        settings.appendChild(divSyncRemoteFolder);
        //////////////////////////////////////////////////////
        settings.appendChild(br.cloneNode(true));
        data = data["weighers"];
        const addInstance = document.createElement('button');
        addInstance.classList.toggle('container-buttons');
        addInstance.classList.toggle('add-btn');
        addInstance.textContent = 'Aggiungi istanza';
        const addInstanceModal = document.createElement('div');
        addInstanceModal.classList.toggle('modal');

        addInstance.addEventListener('click', () => {
            addInstanceModal.style.display = 'block';
            addInstanceModal.querySelector('.save-btn').disabled = true;
        });

        const populateInstanceModal = () => {
            addInstanceModal.innerHTML = `
                <div class="modal-content">
                    <h3>Nome istanza:</h3>
                    <form class="content" oninput="document.querySelector('.save-btn').disabled = !this.checkValidity()">
                        <input type="text" name="name" required>
                    </form>
                    <div class="errors"></div>
                    <div class="container-buttons right">                
                        <button class="cancel-btn">Annulla</button>
                        <button class="save-btn" disabled>Salva</button><br>
                    </div>
                </div>
            `;

            addInstanceModal.querySelector('.cancel-btn').addEventListener('click', () => {
                addInstanceModal.style.display = 'none';
                addInstanceModal.querySelector('input[type="text"]').value = '';
                addInstanceModal.querySelector('.errors').innerHTML = '';
            })

            addInstanceModal.querySelector('.save-btn').addEventListener('click', () => {
                const errorsDiv = addInstanceModal.querySelector('.errors');
                const name = addInstanceModal.querySelector('input[type="text"]').value;
                fetch(`/api/config-weigher/instance`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        name: name,
                        connection: {},
                        time_between_actions: 1
                    })
                })
                .then(response => response.json())
                .then(data => {
                    errorsDiv.innerHTML = '';
                    if ("detail" in data) {
                        data.detail.forEach(error => {
                            errorsDiv.innerHTML += `${error.msg}<br>`;
                        });
                    } else {
                        const key = Object.keys(data)[0];
                        createInstance(key, data[key]);
                        addInstanceModal.style.display = 'none';
                        addInstanceModal.querySelector('input[type="text"]').value = '';
                        addInstanceModal.querySelector('.errors').innerHTML = '';
                    }
                })
                .catch(error => {
                    alert(`Errore durante l'eliminazione della pesa ${error}`);
                })
            })

            window.addEventListener('click', (event) => {
                if (event.target === addInstanceModal) {
                    addInstanceModal.style.display = 'none';
                    addInstanceModal.querySelector('input[type="text"]').value = '';
                    addInstanceModal.querySelector('.errors').innerHTML = '';
                }
            })
        }

        const createInstance = (key, data) => {
            const div = document.createElement('div');

            let currentTimeBetweenActions = data.time_between_actions;

            div.classList.toggle('div_config');
            div.innerHTML = `
                <h3 class="borders">
                    <button class="delete-instance width-fit-content delete-btn">${deleteButtonContent}</button>
                    &nbsp;
                    <p>Istanza: ${key}</p>
                </h3>
                <div class="containerConnection">
                    <div class="borders">
                        <h3>Connessione</h4>
                        <div class="type-connection">
                            <input type="radio" name="connection" value="serial" class="serial"> Seriale &nbsp
                            <input type="radio" name="connection" value="tcp" class="tcp"> Tcp
                        </div>
                        <div class="content-serial"></div>
                        <div class="content-tcp"></div>
                        <div class="container-buttons">
                            <button class="delete-btn">${deleteButtonContent}</button>
                            <button class="edit-btn">${editButtonContent}</button>
                        </div>
                    </div>
                </div>
                <button class="addWeigher width-fit-content">Configura pesa</button>
            `;

            const deleteInstanceModal = document.createElement('div');

            deleteInstanceModal.classList.toggle('modal');

            // Aggiungo il contenuto del modal tramite innerHTML
            deleteInstanceModal.innerHTML = `
                <div class="modal-content">
                    <h3>Conferma eliminazione</h3>
                    <p>Sei sicuro di voler eliminare l'istanza?</p>
                    <div class="container-buttons right">
                        <button class="cancel-btn">Annulla</button>
                        <button class="confirm-btn delete-btn">Conferma</button>
                    </div>
                </div>
            `;

            deleteInstanceModal.querySelector('.cancel-btn').addEventListener('click', () => {
                deleteInstanceModal.style.display = 'none';
            });

            deleteInstanceModal.querySelector('.confirm-btn').addEventListener('click', () => {
                deleteInstanceModal.style.display = 'none';
                fetch(`/api/config-weigher/instance?instance_name=${key}`, {
                    method: 'DELETE',
                })
                .then(res => res.json())
                .then(data => {
                    if (data.deleted) {
                        div.remove();
                    }
                    else if (data.detail) {
                        alert(`Errore nella cancellazione: ${data.detail}`);
                        console.error(data.detail);
                    }
                    else {
                        alert(`Errore nella cancellazione: ${data}`);
                        console.error(data);
                    }
                })
                .catch(error => {
                    alert(`Errore nella cancellazione: ${error}`);
                    console.error(error);
                });
            });

            div.querySelector('.delete-instance').addEventListener('click', () => {
                deleteInstanceModal.style.display = 'block';
            });

            window.addEventListener('click', (event) => {
                if (event.target === deleteInstanceModal) {
                    deleteInstanceModal.style.display = 'none';
                }
            });

            const deleteConnectionModal = document.createElement('div');

            deleteConnectionModal.classList.toggle('modal');

            // Aggiungo il contenuto del modal tramite innerHTML
            deleteConnectionModal.innerHTML = `
                <div class="modal-content">
                    <h3>Conferma eliminazione</h3>
                    <p>Sei sicuro di voler eliminare la connessione?</p>
                    <div class="container-buttons right">
                        <button class="cancel-btn">Annulla</button>
                        <button class="confirm-btn delete-btn">Conferma</button>
                    </div>
                </div>
            `;

            deleteConnectionModal.querySelector('.cancel-btn').addEventListener('click', () => {
                deleteConnectionModal.style.display = 'none';
            });

            deleteConnectionModal.querySelector('.confirm-btn').addEventListener('click', () => {
                deleteConnectionModal.style.display = 'none';
                fetch(`/api/config-weigher/instance/connection?instance_name=${key}`, {
                    method: 'DELETE',
                })
                .then(res => res.json())
                .then(data => {
                    if (data.deleted) {
                        containerButtons.querySelector('.delete-btn').style.display = 'none';
                        viewModeSerial.style.display = 'none';
                        viewModeTcp.style.display = 'none';
                        populateEditSerial({"connection": {}});
                        populateEditTcp({"connection": {}});
                    } else if (!("deleted" in data)) {
                        alert(`Errore durante l\'eliminazione della connessione: ${data}`);
                    }
                })
                .catch(error => {
                    alert(`Errore durante l\'eliminazione della connessione: ${error}`);
                });
            });

            window.addEventListener('click', (event) => {
                if (event.target === deleteConnectionModal) {
                    deleteConnectionModal.style.display = 'none';
                }
            });

            const containerConnection = div.querySelector('.containerConnection');
            const typeConnection = containerConnection.querySelector('.type-connection');
            const radioSerial = containerConnection.querySelector('.serial');
            const radioTcp = containerConnection.querySelector('.tcp');
            const contentSerial = containerConnection.querySelector('.content-serial');
            const contentTcp = containerConnection.querySelector('.content-tcp');
            const containerButtons = containerConnection.querySelector('.container-buttons');

            typeConnection.style.display = 'none';

            const viewModeSerial = document.createElement('div');
            viewModeSerial.classList.toggle('content');

            const populateViewSerial = (data) => {
                viewModeSerial.innerHTML = `
                    <h4>${data.connection.serial_port_name ? data.connection.serial_port_name : ''}</h4>
                    <p class="gray"><em>Baudrate: ${data.connection.baudrate ? data.connection.baudrate : ''} <strong>-</strong> Timeout: ${data.connection.timeout ? data.connection.timeout : ''} <strong>-</strong> Esegui comando ogni: ${currentTimeBetweenActions} secondi</em></p>
                `;
            }

            populateViewSerial(data);

            const editModeSerial = document.createElement('form');
            editModeSerial.oninput = () => {
                editModeSerial.querySelector('.save-btn').disabled = !editModeSerial.checkValidity();
            }
            editModeSerial.classList.toggle('content');
            editModeSerial.style.display = 'none';

            const populateEditSerial = (data) => {
                editModeSerial.innerHTML = `
                    <label for="serial_port_name">Porta seriale:</label>
                    <select name="serial_port_name" class="selectSerialPort width-50-px" required>
                    </select><br>
                    <label for="baudrate">Baudrate:</label>
                    <select name="baudrate" class="selectBaudrate width-50-px" required>
                        <option></option>
                        <option value="9600" ${data.connection.baudrate === 9600 ? 'selected': ''}>9600</option>
                        <option value="14400" ${data.connection.baudrate === 14400 ? 'selected' : ''}>14400</option>
                        <option value="19200" ${data.connection.baudrate === 19200 ? 'selected' : ''}>19200</option>
                        <option value="38400" ${data.connection.baudrate === 38400 ? 'selected' : ''}>38400</option>
                        <option value="57600" ${data.connection.baudrate === 57600 ? 'selected' : ''}>57600</option>
                        <option value="115200" ${data.connection.baudrate === 115200 ? 'selected' : ''}>115200</option>
                    </select><br>
                    <label for="timeout">Timeout:</label>
                    <input type="number" min="0.1" max="10" step="0.1" name="timeout" class="width-50-px" value="${data.connection.timeout ? data.connection.timeout : ''}" required><br>
                    <label for "time_between_actions">Esegui azione ogni:</label>
                    <input type="number" min="0.1" max="10" step="0.1" name="time_between_actions" class="width-50-px" value="${currentTimeBetweenActions}" required><br>
                    <div class="errors"></div>
                    <div class="container-buttons">
                        <button class="cancel-btn">Annulla</button>
                        <button class="save-btn">Salva</button>
                    </div>
                `;

                const option = document.createElement('option');
                editModeSerial.querySelector('.selectSerialPort').appendChild(option);

                for (let port of list_serial_ports) {
                    const option = document.createElement('option');
                    option.value = port.port;
                    option.innerHTML = port.port;
                    if ("serial_port_name" in data.connection && data.connection.serial_port_name == port.port) {
                        option.selected = true;
                    }
                    editModeSerial.querySelector('.selectSerialPort').appendChild(option);
                }

                editModeSerial.oninput();

                editModeSerial.querySelector('.cancel-btn').addEventListener('click', (event) => {
                    event.preventDefault();
                    typeConnection.style.display = 'none';
                    editModeSerial.style.display = 'none';
                    editModeTcp.style.display = 'none';
                    containerButtons.style.display = 'flex';
                    radioSerial.checked = false;
                    if (!("ip" in data.connection)) {
                        radioSerial.checked = true;
                        if ("serial_port_name" in data.connection) {
                            viewModeSerial.style.display = 'block';
                        }
                    } else {
                        radioTcp.checked = true;
                        viewModeTcp.style.display = 'block';
                    }
                });

                editModeSerial.querySelector('.save-btn').addEventListener('click', (event) => {
                    event.preventDefault();
                    editModeSerial.querySelector('.errors').innerHTML = '';
                    fetch(`/api/config-weigher/instance/connection?instance_name=${key}`, {
                        method: 'DELETE',
                    })
                    .then(res => res.json())
                    .then(res => {
                        const newTimeBetweenActions = Number(editModeSerial.querySelector('input[name="time_between_actions"]').value);
                        if (newTimeBetweenActions != currentTimeBetweenActions) {
                            fetch(`/api/config-weigher/instance/time-between-actions/${newTimeBetweenActions}?instance_name=${key}`, {
                                method: 'PATCH',
                                headers: {
                                    'Content-Type': 'application/json'
                                }
                            })
                            .then(res => res.json())
                            .then(res => currentTimeBetweenActions = res.time_between_actions)
                            .catch(error => console.error(error));
                        }
                        return res;
                    })
                    .then(_ => {
                        fetch(`/api/config-weigher/instance/connection?instance_name=${key}`, {
                            method: 'PATCH',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                serial_port_name: editModeSerial.querySelector('select[name="serial_port_name"]').value,
                                baudrate: Number(editModeSerial.querySelector('select[name="baudrate"]').value),
                                timeout: Number(editModeSerial.querySelector('input[name="timeout"]').value)
                            })
                        })
                        .then(res => res.json())
                        .then(data => {
                            if ('connected' in data) {
                                typeConnection.style.display = 'none';
                                editModeSerial.style.display = 'none';
                                editModeTcp.style.display = 'none';
                                containerButtons.style.display = 'flex';
                                containerButtons.querySelector('.delete-btn').style.display = 'block';
                                containerButtons.querySelector('.edit-btn').innerHTML = editButtonContent;
                                viewModeSerial.style.display = 'block';
                                populateEditSerial({"connection": data});
                                populateViewSerial({"connection": data});
                                populateEditTcp({"connection": data});
                                if ("ip" in data) {
                                    viewModeTcp.style.display = 'block';
                                } else {
                                    viewModeSerial.style.display = 'block';
                                }
                            } else if ('detail' in data) {
                                data.detail.forEach(error => {
                                    if (error.loc.includes('SerialPort')) {
                                        const message = error.msg.replace('Value error, ', '');
                                        editModeSerial.querySelector('.errors').innerHTML += `${message}<br>`;
                                    }
                                })
                            } else {
                                alert(`Errore durante la modifica della connessione: ${data}`);
                            }
                        })
                        .catch(error => {
                            alert(`Errore durante la modifica della connessione: ${error}`);
                        })
                    })
                });
            }

            populateEditSerial(data);

            contentSerial.appendChild(viewModeSerial);
            contentSerial.appendChild(editModeSerial);

            const viewModeTcp = document.createElement('div');
            viewModeTcp.classList.toggle('content');

            const populateViewTcp = (data) => {
                viewModeTcp.innerHTML = `
                    <p>Indirizzo IP: ${data.connection.ip ? data.connection.ip : ''} <strong>-</strong> Porta: ${data.connection.port ? data.connection.port : ''} <strong>-</strong> Timeout: ${data.connection.timeout ? data.connection.timeout : ''}<br></p><br>
                    Esegui comando ogni: ${currentTimeBetweenActions} secondi
                `;
            }

            populateViewTcp(data);

            const editModeTcp = document.createElement('form');
            editModeTcp.oninput = () => {
                editModeTcp.querySelector('.save-btn').disabled = !editModeTcp.checkValidity();
            }
            editModeTcp.classList.toggle('content');
            editModeTcp.style.display = 'none';

            const populateEditTcp = (data) => {
                editModeTcp.innerHTML = `
                    <label for="ip">Indirizzo IP:</label>
                    <input type="text" name="ip" class="width-50-px" value="${data.connection.ip ? data.connection.ip : ''}" required><br>
                    <label for="port">Porta:</label>
                    <input type="number" min="1" max="65535" step="1" name="port" class="width-50-px" value="${data.connection.port ? data.connection.port : ''}" oninput="this.value = this.value && this.value > 0 ? Math.abs(this.value) : ''" required><br>
                    <label for="timeout">Timeout:</label>
                    <input type="number" min="0.1" max="10" step="0.1" name="timeout" class="width-50-px" value="${data.connection.timeout ? data.connection.timeout : ''}" oninput="this.value = this.value && this.value > 0 ? Math.abs(this.value) : ''" required><br>
                    <label for="time_between_actions">Esegui comando ogni:</label>
                    <input type="number" min="0.1" max="10" step="0.1" name="time_between_actions" class="width-50-px" value="${currentTimeBetweenActions}" required><br>
                    <div class="container-buttons">
                        <button class="cancel-btn">Annulla</button>
                        <button class="save-btn">Salva</button>
                    </div>
                `;

                editModeTcp.oninput();

                editModeTcp.querySelector('.cancel-btn').addEventListener('click', (event) => {
                    event.preventDefault();
                    typeConnection.style.display = 'none';
                    editModeSerial.style.display = 'none';
                    editModeTcp.style.display = 'none';
                    containerButtons.style.display = 'flex';
                    radioTcp.checked = false;
                    if (!("ip" in data.connection)) {
                        radioSerial.checked = true;
                        if ("serial_port_name" in data.connection) {
                            viewModeSerial.style.display = 'block';
                        }
                    } else {
                        radioTcp.checked = true;
                        viewModeTcp.style.display = 'block';
                    }
                });

                editModeTcp.querySelector('.save-btn').addEventListener('click', (event) => {
                    event.preventDefault();
                    fetch(`/api/config-weigher/instance/connection?instance_name=${key}`, {
                        method: 'DELETE',
                    })
                    .then(res => res.json())
                    .then(res => {
                        const newTimeBetweenActions = Number(editModeTcp.querySelector('input[name="time_between_actions"]').value);
                        if (newTimeBetweenActions != currentTimeBetweenActions) {
                            fetch(`/api/config-weigher/instance/time-between-actions/${newTimeBetweenActions}?instance_name=${key}`, {
                                method: 'PATCH',
                                headers: {
                                    'Content-Type': 'application/json'
                                }
                            })
                            .then(res => res.json())
                            .then(res => currentTimeBetweenActions = res.time_between_actions)
                            .catch(error => console.error(error));
                        }
                        return res;
                    })
                    .then(_ => {
                        fetch(`/api/config-weigher/instance/connection?instance_name=${key}`, {
                            method: 'PATCH',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                ip: editModeTcp.querySelector('input[name="ip"]').value,
                                port: Number(editModeTcp.querySelector('input[name="port"]').value),
                                timeout: Number(editModeTcp.querySelector('input[name="timeout"]').value)
                            })
                        })
                        .then(res => res.json())
                        .then(data => {
                            if ('connected' in data) {
                                typeConnection.style.display = 'none';
                                editModeSerial.style.display = 'none';
                                editModeTcp.style.display = 'none';
                                containerButtons.style.display = 'flex';
                                containerButtons.querySelector('.delete-btn').style.display = 'block';
                                viewModeTcp.style.display = 'block';
                                populateEditTcp({"connection": data});
                                populateViewTcp({"connection": data});
                                populateEditSerial({"connection": data});
                            } else {
                                alert(`Errore durante la modifica della connessione: ${data}`);}
                        })
                        .catch(error => {
                            alert(`Errore durante la modifica della connessione: ${error}`);
                        })
                    })
                });
            }

            populateEditTcp(data);

            contentTcp.appendChild(viewModeTcp);
            contentTcp.appendChild(editModeTcp);

            contentSerial.style.display = 'none';
            contentTcp.style.display = 'none';

            containerButtons.querySelector('.delete-btn').addEventListener('click', () => {
                deleteConnectionModal.style.display = 'block';
            });

            containerButtons.querySelector('.edit-btn').addEventListener('click', () => {
                typeConnection.style.display = 'block';
                containerButtons.style.display = 'none';
                if (viewModeSerial.style.display == 'block') {
                    radioSerial.checked = true;
                    viewModeSerial.style.display = 'none';
                    editModeSerial.style.display = 'block';
                } else if (viewModeTcp.style.display == 'block') {
                    radioTcp.checked = true;
                    viewModeTcp.style.display = 'none';
                    editModeTcp.style.display = 'block';
                } else {
                    radioSerial.checked = true;
                    editModeSerial.style.display = 'block';
                }
            });

            contentSerial.style.display = 'block';
            contentTcp.style.display = 'block';

            if ('serial_port_name' in data.connection) {
                radioSerial.checked = true;
                viewModeSerial.style.display = 'block';
                viewModeTcp.style.display = 'none';
            } else if ('ip' in data.connection) {
                radioTcp.checked = true;
                viewModeTcp.style.display = 'block';
                viewModeSerial.style.display = 'none';
            } else {
                containerButtons.querySelector('.delete-btn').style.display = 'none';
                radioSerial.checked = true;
                viewModeSerial.style.display = 'none';
                viewModeTcp.style.display = 'none';
            }

            radioSerial.addEventListener('click', () => {
                editModeSerial.style.display = 'block';
                editModeTcp.style.display = 'none';
            });

            radioTcp.addEventListener('click', () => {
                editModeTcp.style.display = 'block';
                editModeSerial.style.display = 'none';
            });

            const addWeigherModal = document.createElement('div');
            const ul = document.createElement('ul');

            addWeigherModal.classList.toggle('modal');
            
            addWeigherModal.innerHTML = `
                <div class="modal-content">
                    <h3>Aggiungi pesa</h3>
                    <form class="content" id="add-form" style="width: 950px; max-width: 100%">
                    </form>
                    <div class="errors"></div>
                    <div class="container-buttons right">
                        <button class="cancel-btn">Annulla</button>
                        <button class="save-btn" disabled>Salva</button>
                    </div>
                </div>
            `;

            const addWeigherForm = addWeigherModal.querySelector('form');
            const errorAddWeigher = addWeigherModal.querySelector('.errors');

            addWeigherForm.oninput = () => {
                addWeigherModal.querySelector('.save-btn').disabled = !addWeigherForm.checkValidity();
            }

            const addCamClass = `cams-${key}`;
            const addReleClass = `rele-${key}`;

            const populateAddContent = () => {
                // Genera le option per le stampanti
                let printerOptions = '';
                printerOptions += `<option value="">--- Nessuna ---</button>`;
                for (const printer of list_printer_names) {
                    printerOptions += `<option value="${printer.nome}">${printer.nome}</option>`;
                }

                let addTerminalOptions = '';
                for (const terminal of list_terminal_types) {
                    addTerminalOptions += `<option value="${terminal}">${terminal}</option>`;
                }

                addWeigherForm.innerHTML = `
                    <div style="display: flex; gap: 16px;">
                        <div class="form-group" style="flex: 1;">
                            <label for="name">Nome pesa:</label>
                            <input type="text" name="name" id="name" required>
                        </div>
                        <div class="form-group" style="flex: 1;">
                            <label for="terminal">Terminale:</label>
                            <select name="terminal" id="terminal" required>
                                ${addTerminalOptions}
                            </select>
                        </div>
                        <div class="form-group" style="flex: 1;">
                            <label for="node">Nodo: (facoltativo)</label>
                            <input type="text" name="node" id="node">
                        </div>
                    </div>
                    <div style="display: flex; gap: 16px;">
                        <div class="form-group" style="flex: 1;">
                            <label for="max_weight">Peso massimo:</label>
                            <input type="number" name="max_weight" id="max_weight" min="1" required>
                        </div>
                        <div class="form-group" style="flex: 1;">
                            <label for="min_weight">Peso minimo:</label>
                            <input type="number" name="min_weight" id="min_weight" min="1" required>
                        </div>
                        <div class="form-group" style="flex: 1;">
                            <label for="division">Divisione:</label>
                            <input type="number" name="division" id="division" min="1" required>
                        </div>
                        <div class="form-group" style="flex: 1;">
                            <label for="max_theshold">Soglia massima: (facoltativo)</label>
                            <input type="number" name="max_theshold" id="max_theshold" min="1">
                        </div>
                    </div>
                    <div style="display: flex; gap: 16px; align-items: flex-end;">
                        <div class="form-group" style="flex: 1; text-align: center;">
                            <label>Genera report all'entrata</label><br>
                            <input type="checkbox" name="report_on_in">
                        </div>
                        <div class="form-group" style="flex: 1; text-align: center;">
                            <label>Genera report all'uscita</label><br>
                            <input type="checkbox" name="report_on_out">
                        </div>
                        <div class="form-group" style="flex: 1; text-align: center;">
                            <label>Genera report alla generica</label><br>
                            <input type="checkbox" name="report_on_print" checked>
                        </div>
                        <div class="form-group" style="flex: 2;">
                            <label for="printer_name">Stampa su:</label>
                            <select id="printer_name" name="printer_name">
                                ${printerOptions}
                            </select>
                        </div>
                        <div class="form-group" style="flex: 1;">
                            <label for="number_of_prints">Numero di stampe:</label>
                            <input type="number" name="number_of_prints" id="number_of_prints" min="1" max="5" value="1" required>
                        </div>
                    </div>
                    <div style="display: flex; gap: 16px; align-items: flex-end;">
                        <div class="form-group" style="flex: 1; text-align: center;">
                            <label>Genera CSV all'entrata</label><br>
                            <input type="checkbox" name="csv_on_in">
                        </div>
                        <div class="form-group" style="flex: 1; text-align: center;">
                            <label>Genera CSV all'uscita</label><br>
                            <input type="checkbox" name="csv_on_out">
                        </div>
                    </div>
                    <div class="form-group">
                        <label><input type="checkbox" name="run" checked> In esecuzione</label>
                    </div>
                    <div class="form-group">
                        <label><input type="checkbox" name="need_take_of_weight_before_weighing" checked> Scaricare la pesa dopo pesata effettuata</label>
                    </div>
                    <div class="form-group">
                        <label><input type="checkbox" name="need_take_of_weight_on_startup" checked> Scaricare la pesa dopo l'avvio del programma</label>
                    </div>
                    <div class="form-group">
                        <label><input type="checkbox" name="continuous_transmission"> Trasmissione continua per il peso in tempo reale</label>
                    </div>
                    <div class="form-group">
                        <label>Telecamere: <button onclick="addCam(event, '#add-form', '${addCamClass}')">Aggiungi</button></label>
                        <div class="form-group cams ${addCamClass}"></div>
                    </div>
                    <div class="form-group">
                        <label>Relè: <button onclick="addRele(event, '#add-form', '${addReleClass}')">Aggiungi</button></label>
                        <div class="form-group reles ${addReleClass}"></div>
                    </div>
                `;

                errorAddWeigher.innerHTML = '';

                addWeigherForm.dispatchEvent(event);
            }
            
            populateAddContent();

            // Rimuovi spazi automaticamente dal campo nome
            const addNameInput = addWeigherModal.querySelector('input[name="name"]');
            if (addNameInput) {
                addNameInput.addEventListener('input', (e) => {
                    e.target.value = e.target.value.replace(/\s/g, '');
                });
            }

            addWeigherModal.querySelector('.cancel-btn').addEventListener('click', () => {
                addWeigherModal.style.display = 'none';
                populateAddContent();
            });

            addWeigherModal.querySelector('.save-btn').addEventListener('click', () => {
                let data = {
                    cams: [],
                    over_min: [],
                    under_min: [],
                    weighing: []
                };
                    
                const inputs = addWeigherModal.querySelectorAll('input');
                inputs.forEach(input => {
                    let currentValue;
                    
                    if (input.type === 'checkbox') {
                        currentValue = input.checked;
                    } else if (input.type === 'number') {
                        currentValue = parseInt(input.value);
                    } else {
                        currentValue = input.value !== '' ? input.value : null;
                    }

                    if (input.name) data[input.name] = currentValue;
                });

                const selections = addWeigherModal.querySelectorAll('select');
                selections.forEach(selection => {
                    if (selection.name) data[selection.name] = selection.value !== '' ? selection.value : null;
                })

                document.querySelector(`.${addCamClass}`).querySelectorAll(".cam").forEach(element => {
                    const inputs = element.querySelectorAll("input");
                    const cam = {
                        "picture": inputs[0].value,
                        "active": inputs[1].checked ? true : false
                    }
                    if (cam.picture) data["cams"].push(cam);
                })

                document.querySelector(`.${addReleClass}`).querySelectorAll(".rele").forEach(element => {
                    const input = element.querySelector("input");
                    const selects = element.querySelectorAll("select");
                    const rele = {
                        "rele": input.value,
                        "set": Number(selects[0].value)
                    }
                    if (input.value) data[selects[1].value].push(rele);
                })

                fetch(`/api/config-weigher/instance/node?instance_name=${key}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                })
                .then(response => response.json())
                .then(response => {
                    if (data['name'] in response) {
                        const key = Object.keys(response)[0];
                        const weigher_data = {
                            name: key,
                            ...response[key]
                        };
                        addWeigher(weigher_data);
                        addWeigherModal.querySelector('.content').innerHTML = '';
                        populateAddContent();
                        addWeigherModal.style.display = 'none';
                    } else if ("detail" in response) {
                        errorAddWeigher.innerHTML = '';
                        const errors = document.createElement('div');
                        response.detail.forEach(error => {
                            errors.innerHTML += `${error.msg}<br>`;
                        })
                        errorAddWeigher.appendChild(errors);
                    }
                })
                .catch(error => {
                    alert(`Errore nella configurazione della pesa: ${error}`);
                    console.error(error);
                });
            })

            const addWeigher = (weigher) => {
                const li = document.createElement('li');
                li.classList.toggle('borders');
                li.classList.toggle('margins');
                const viewMode = document.createElement('div');
                const editMode = document.createElement('div');
                editMode.style.display = 'none';

                viewMode.innerHTML = `
                    <div class="content"></div>
                    <div class="container-buttons">
                        <button class="delete-btn">${deleteButtonContent}</button>
                        <button class="edit-btn">${editButtonContent}</button>
                        <button class="auto-weighing-btn">${autoWeighingButtonContent}</button>
                    </div>
                `;

                const populateViewContent = (data) => {
                    const viewModeCFontent = viewMode.querySelector('.content');
                    const cams = data.events.weighing.cams;
                    const over_min = data.events.realtime.over_min.set_rele;
                    const under_min = data.events.realtime.under_min.set_rele;
                    const weighing = data.events.weighing.set_rele;
                    viewModeCFontent.innerHTML = `
                        <h4>${data.name} <span class="gray">${data.terminal}</span></h4>
                        <p class="gray"><em>Nodo: ${data.node ? data.node : 'Nessuno'}</em></p>
                        <p class="gray"><em>Peso massimo: ${data.max_weight}</em> <strong>-</strong> <em>Peso minimo: ${data.min_weight}</em> <strong>-</strong> <em>Divisione: ${data.division}</em><br></p>
                        <p class="gray"><em>Soglia massima: ${data.max_theshold ? data.max_theshold : 'Nessuna'}</em></p>
                        <p class="gray"><em>Genera report all'entrata: ${data.events.weighing.report.in ? 'Si' : 'No'}</em> <strong>-</strong> <em>Genera report all'uscita: ${data.events.weighing.report.out ? 'Si' : 'No'}</em></p>
                        <p class="gray"><em>Genera CSV all'entrata: ${data.events.weighing.csv.in ? 'Si' : 'No'}</em> <strong>-</strong> <em>Genera CSV all'uscita: ${data.events.weighing.csv.out ? 'Si' : 'No'}</em></p>
                        <p class="gray"><em>Stampa su: ${data.printer_name ? data.printer_name : 'Nessuna'}</em></p>
                        <p class="gray"><em>Numero di stampe: ${data.number_of_prints}</em></p>
                        <p class="gray"><em>In esecuzione: ${data.run ? 'Si' : 'No'}</em></p>
                        <p class="gray"><em>Scaricare pesa dopo pesata effettuata: ${data.need_take_of_weight_before_weighing ? 'Si' : 'No'}</em></p>
                        <p class="gray"><em>Scaricare pesa all'avvio: ${data.need_take_of_weight_on_startup ? 'Si' : 'No'}</em></p>
                        <p class="gray"><em>Trasmissione continua per il peso in tempo reale: ${data.continuous_transmission ? 'Si' : 'No'}</em></p>
                    `;
                    if (cams.length > 0) {
                        viewModeCFontent.innerHTML += '<h5 class="gray"><em>TELECAMERE</em></h5>';
                        cams.forEach(cam => {
                            viewModeCFontent.innerHTML += `<p class="gray"><em>${cam.picture}</em> <strong>-</strong> ${cam.active ? '<em>Attiva</em>' : '<em>Disattiva</em>'}</p>`;
                        });
                    }
                    if (over_min.length > 0 || under_min.length > 0 || weighing.length > 0) {
                        viewModeCFontent.innerHTML += '<h5 class="gray"><em>RELE</em></h5>';
                        over_min.forEach(r => {
                            viewModeCFontent.innerHTML += `
                                <p class="gray"><em>${r.set ? 'Attiva' : 'Disattiva'} relè ${r.rele} sopra il peso minimo</em></p>
                            `;
                        });
                        under_min.forEach(r => {
                            viewModeCFontent.innerHTML += `
                                <p class="gray"><em>${r.set ? 'Attiva' : 'Disattiva'} relè ${r.rele} sotto il peso minimo</em></p>
                            `;
                        });
                        weighing.forEach(r => {
                            viewModeCFontent.innerHTML += `
                                <p class="gray"><em>${r.set ? 'Attiva' : 'Disattiva'} relè ${r.rele} dopo la pesata</em></p>
                            `;
                        });
                    }
                }

                populateViewContent(weigher);

                const idEditForm = `edit-form-${key}-${weigher.name}`;

                editMode.innerHTML = `
                    <form id="${idEditForm}" class="content">
                    </form>
                    <div class="container-buttons">                
                        <button class="cancel-btn">Annulla</button>
                        <button class="save-btn">Salva</button><br>
                    </div>
                    <div class="errors"></div>
                `;

                const editWeigherForm = editMode.querySelector('form');

                editWeigherForm.oninput = () => {
                    editMode.querySelector('.save-btn').disabled = !editWeigherForm.checkValidity();
                }

                const addCamWeigher = `cams-${key}-${weigher.name}`;
                const addReleWeigher = `rele-${key}-${weigher.name}`;

                const populateEditContent = (data) => {
                    // Genera le option per le stampanti
                    let printerOptions = '';
                    printerOptions += `<option value="">--- Nessuna ---</button>`;
                    for (const printer of list_printer_names) {
                        printerOptions += `<option value="${printer.nome}" ${data.printer_name === printer.nome ? 'selected' : ''}>${printer.nome}</option>`;
                    }

                    // Genera le option per i terminali
                    let editTerminalOptions = '';
                    for (const terminal of list_terminal_types) {
                        editTerminalOptions += `<option value="${terminal}" ${data.terminal === terminal ? 'selected' : ''}>${terminal}</option>`;
                    }

                    editMode.querySelector('.content').innerHTML = `
                        <div style="display: flex; gap: 16px;">
                            <div class="form-group" style="flex: 1;">
                                <label for="name">Nome pesa:</label><br>
                                <input type="text" name="name" id="name" value="${data.name || ''}" required>
                            </div>
                            <div class="form-group" style="flex: 1;">
                                <label for="terminal">Terminale:</label><br>
                                <select name="terminal" id="terminal" required>
                                    ${editTerminalOptions}
                                </select>
                            </div>
                            <div class="form-group" style="flex: 1;">
                                <label for="node">Nodo: (facoltativo)</label><br>
                                <input type="text" name="node" id="node" value="${data.node || ''}">
                            </div>
                        </div>
                        <div style="display: flex; gap: 16px;">
                            <div class="form-group" style="flex: 1;">
                                <label for="max_weight">Peso massimo:</label><br>
                                <input type="number" name="max_weight" id="max_weight" min="1" value="${data.max_weight || ''}" required>
                            </div>
                            <div class="form-group" style="flex: 1;">
                                <label for="min_weight">Peso minimo:</label><br>
                                <input type="number" name="min_weight" id="min_weight" min="1" value="${data.min_weight || ''}" required>
                            </div>
                            <div class="form-group" style="flex: 1;">
                                <label for="division">Divisione:</label><br>
                                <input type="number" name="division" id="division" min="1" value="${data.division || ''}" required>
                            </div>
                            <div class="form-group" style="flex: 1;">
                                <label for="max_theshold">Soglia massima: (facoltativo)</label><br>
                                <input type="number" name="max_theshold" id="max_theshold" min="1" value="${data.max_theshold || ''}">
                            </div>
                        </div>
                        <div style="display: flex; gap: 16px; align-items: flex-end;">
                            <div class="form-group" style="flex: 1; text-align: center;">
                                <label>Genera report all'entrata</label><br>
                                <input type="checkbox" name="report_on_in" ${data.events?.weighing?.report?.in ? 'checked' : ''}>
                            </div>
                            <div class="form-group" style="flex: 1; text-align: center;">
                                <label>Genera report all'uscita</label><br>
                                <input type="checkbox" name="report_on_out" ${data.events?.weighing?.report?.out ? 'checked' : ''}>
                            </div>
                            <div class="form-group" style="flex: 1; text-align: center;">
                                <label>Genera report alla generica</label><br>
                                <input type="checkbox" name="report_on_print" ${data.events?.weighing?.report?.print ? 'checked' : ''}>
                            </div>
                            <div class="form-group" style="flex: 2;">
                                <label for="printer_name">Stampa su:</label><br>
                                <select id="printer_name" name="printer_name">
                                    ${printerOptions}
                                </select>
                            </div>
                            <div class="form-group" style="flex: 1;">
                                <label for="number_of_prints">Numero di stampe:</label><br>
                                <input type="number" name="number_of_prints" id="number_of_prints" min="1" max="5" value="${data.number_of_prints || 1}" required>
                            </div>
                        </div>
                        <div style="display: flex; gap: 16px; align-items: flex-end;">
                            <div class="form-group" style="flex: 1; text-align: center;">
                                <label>Genera CSV all'entrata</label><br>
                                <input type="checkbox" name="csv_on_in" ${data.events?.weighing?.csv?.in ? 'checked' : ''}>
                            </div>
                            <div class="form-group" style="flex: 1; text-align: center;">
                                <label>Genera CSV all'uscita</label><br>
                                <input type="checkbox" name="csv_on_out" ${data.events?.weighing?.csv?.out ? 'checked' : ''}>
                            </div>
                        </div>
                        <div class="form-group">
                            <label><input type="checkbox" name="run" ${data.run ? 'checked' : ''}> In esecuzione</label>
                        </div>
                        <div class="form-group">
                            <label><input type="checkbox" name="need_take_of_weight_before_weighing" ${data.need_take_of_weight_before_weighing ? 'checked' : ''}> Scaricare la pesa dopo pesata effettuata</label>
                        </div>
                        <div class="form-group">
                            <label><input type="checkbox" name="need_take_of_weight_on_startup" ${data.need_take_of_weight_on_startup ? 'checked' : ''}> Scaricare la pesa dopo l'avvio del programma</label>
                        </div>
                        <div class="form-group">
                            <label><input type="checkbox" name="continuous_transmission" ${data.continuous_transmission ? 'checked' : null}> Trasmissione continua per il peso in tempo reale</label>
                        </div>
                        <div class="form-group">
                            <label>Telecamere: <button onclick="addCam(event, '#${idEditForm}', '${addCamWeigher}')">Aggiungi</button></label>
                            <div class="form-group cams ${addCamWeigher}"></div>
                        </div>
                        <div class="form-group">
                            <label>Relè: <button onclick="addRele(event, '#${idEditForm}', '${addReleWeigher}')">Aggiungi</button></label>
                            <div class="form-group reles ${addReleWeigher}"></div>
                        </div>
                    `;

                    data.events.weighing.cams.forEach(cam => {
                        addCam(null, `#${idEditForm}`, addCamWeigher, cam.picture, cam.active);
                    });

                    data.events.realtime.over_min.set_rele.forEach(rele => {
                        addRele(null, `#${idEditForm}`, addReleWeigher, rele.rele, rele.set, "over_min");
                    })

                    data.events.realtime.under_min.set_rele.forEach(rele => {
                        addRele(null, `#${idEditForm}`, addReleWeigher, rele.rele, rele.set, "under_min");
                    })

                    data.events.weighing.set_rele.forEach(rele => {
                        addRele(null, `#${idEditForm}`, addReleWeigher, rele.rele, rele.set, "weighing");
                    });

                    editWeigherForm.dispatchEvent(event);
                }

                const errorEditWeigher = editMode.querySelector('.errors');

                viewMode.querySelector('.delete-btn').addEventListener('click', () => {
                    deleteWeigherModal.style.display = 'block';
                });

                viewMode.querySelector('.edit-btn').addEventListener('click', () => {
                    viewMode.style.display = 'none';
                    editMode.style.display = 'block';
                    populateEditContent(weigher);

                    // Rimuovi spazi automaticamente dal campo nome
                    const editNameInput = editMode.querySelector('input[name="name"]');
                    if (editNameInput) {
                        editNameInput.addEventListener('input', (e) => {
                            e.target.value = e.target.value.replace(/\s/g, '');
                        });
                    }
                });

                viewMode.querySelector('.auto-weighing-btn').addEventListener('click', () => {
                    fetch(`/api/config-weigher/instance/node/endpoint?instance_name=${key}&weigher_name=${weigher.name}`)
                    .then(res => res.json())
                    .then(res => {
                        // Crea il popup custom
                        const modal = document.createElement('div');
                        modal.classList.add('modal');
                        modal.innerHTML = `
                            <div class="modal-content">
                                <h3>Stringa da copiare</h3>
                                <p style="word-break: break-all;">${res}</p>
                                <div class="container-buttons right">
                                    <button class="close-btn">Chiudi</button>
                                    <button class="copy-btn">Copia</button>
                                </div>
                            </div>
                        `;
                        document.body.appendChild(modal);
                        modal.style.display = 'block';
                        modal.querySelector('.copy-btn').addEventListener('click', () => {
                            copyToClipboard(res);
                            document.body.removeChild(modal);
                            showSnackbar("snackbar", "Url copiata correttamente negli appunti", 'rgb(208, 255, 208)', 'black');
                        });
                        modal.querySelector('.close-btn').addEventListener('click', () => {
                            modal.style.display = 'none';
                            document.body.removeChild(modal);
                        });
                        window.addEventListener('click', (event) => {
                            if (event.target === modal) {
                                modal.style.display = 'none';
                                document.body.removeChild(modal);
                            }
                        });
                    });
                })

                editMode.querySelector('.cancel-btn').addEventListener('click', () => {
                    populateEditContent(weigher);
                    errorEditWeigher.innerHTML = '';
                    viewMode.style.display = 'block';
                    editMode.style.display = 'none';
                });

                editMode.querySelector('.save-btn').addEventListener('click', () => {
                    let changedData = {
                        cams: [],
                        over_min: [],
                        under_min: [],
                        weighing: []
                    };
                    
                    const inputs = editMode.querySelectorAll('input');
                    inputs.forEach(input => {
                        const originalValue = weigher[input.name];
                        let currentValue;
                        
                        if (input.type === 'checkbox') {
                            currentValue = input.checked;
                        } else if (input.type === 'number') {
                            currentValue = parseInt(input.value);
                        } else {
                            currentValue = input.value !== '' ? input.value : null;
                        }

                        if (currentValue !== originalValue) {
                            changedData[input.name] = currentValue;
                        }
                    });

                    const selections = editMode.querySelectorAll('select');
                    selections.forEach(selection => {
                        const currentValue = selection.value;
                        changedData[selection.name] = currentValue !== '' ? currentValue : null;
                    });

                    document.querySelector(`.${addCamWeigher}`).querySelectorAll(".cam").forEach(element => {
                        const inputs = element.querySelectorAll("input");
                        const cam = {
                            "picture": inputs[0].value,
                            "active": inputs[1].checked ? true : false
                        }
                        if (cam.picture) changedData["cams"].push(cam);
                    })

                    document.querySelector(`.${addReleWeigher}`).querySelectorAll(".rele").forEach(element => {
                        const input = element.querySelector("input");
                        const selects = element.querySelectorAll("select");
                        const rele = {
                            "rele": input.value,
                            "set": Number(selects[0].value)
                        }
                        if (input.value) changedData[selects[1].value].push(rele);
                    })
                    
                    if (Object.keys(changedData).length > 0) {
                        let url_patch = `/api/config-weigher/instance/node?instance_name=${key}`;
                        if (weigher.name) url_patch += `&weigher_name=${weigher.name}`;
                        fetch(url_patch, {
                            method: 'PATCH',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(changedData)
                        })
                        .then(res => res.json())
                        .then(response => {
                            const name = Object.keys(response)[0];
                            const response_formatted = {
                                name: name,
                                ...response[name]
                            };
                            if ('node' in response_formatted) {

                                Object.assign(weigher, response_formatted);

                                populateViewContent(response_formatted);
                                populateEditContent(response_formatted);

                                errorEditWeigher.innerHTML = '';
                                viewMode.style.display = 'block';
                                editMode.style.display = 'none';
                            } else if ("detail" in response) {
                                errorEditWeigher.innerHTML = '';
                                const errors = document.createElement('div');
                                response.detail.forEach(error => {
                                    errors.innerHTML += `${error.msg}<br>`;
                                })
                                errorEditWeigher.appendChild(errors);
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            alert(`Errore durante il salvataggio delle modifiche: ${error}`);
                        })
                    } else {
                        errorEditWeigher.innerHTML = '';
                        viewMode.style.display = 'block';
                        editMode.style.display = 'none';
                    }
                });

                const deleteWeigherModal = document.createElement('div');

                deleteWeigherModal.classList.toggle('modal');

                // Aggiungo il contenuto del modal tramite innerHTML
                deleteWeigherModal.innerHTML = `
                    <div class="modal-content">
                        <h3>Conferma eliminazione</h3>
                        <p>Sei sicuro di voler eliminare la configurazione della pesa?</p>
                        <div class="container-buttons right">
                            <button class="modalDeleteWeigherCancel">Annulla</button>
                            <button class="modalDeleteWeigherConfirm delete-btn">Conferma</button>
                        </div>
                    </div>
                `;
        
                deleteWeigherModal.querySelector('.modalDeleteWeigherCancel').addEventListener('click', () => {
                    deleteWeigherModal.style.display = 'none';
                });

                deleteWeigherModal.querySelector('.modalDeleteWeigherConfirm').addEventListener('click', () => {
                    let delete_url = `/api/config-weigher/instance/node?instance_name=${key}`;
                    if (weigher.name !== null) {
                        delete_url += `&weigher_name=${weigher.name}`;
                    }
                    fetch(delete_url, {
                        method: 'DELETE'
                    })
                    .then(response => response.json())
                    .then(response => {
                        if (response.deleted) {
                            li.remove();
                        }
                    })
                    .catch(error => {
                        alert(`Errore durante l'eliminazione della pesa ${error}`);
                    })
                    .finally(_ => {
                        deleteWeigherModal.style.display = 'none';
                    })
                });

                li.appendChild(editMode);
                li.appendChild(viewMode);
                li.appendChild(deleteWeigherModal);
                ul.appendChild(li);

                // Chiudi il modal se si clicca fuori
                window.addEventListener('click', (event) => {
                    if (event.target === deleteWeigherModal) {
                        deleteWeigherModal.style.display = 'none';
                    }
                });
            }

            for (let [name, weigher] of Object.entries(data['nodes'])) {
                const weigher_data = {
                    name,
                    ...weigher
                };
                addWeigher(weigher_data);
            }

            div.querySelector('.addWeigher').addEventListener('click', () => {
                addWeigherModal.style.display = 'block';
            });

            // Chiudi il modal se si clicca fuori
            window.addEventListener('click', (event) => {
                if (event.target === addWeigherModal) {
                    addWeigherModal.style.display = 'none';
                    populateAddContent();
                }
            });

            div.appendChild(deleteInstanceModal);
            div.appendChild(deleteConnectionModal);
            div.appendChild(addWeigherModal);
            div.appendChild(ul);
            instances.appendChild(div);
        }

        populateInstanceModal();

        instances.appendChild(addInstance);
        instances.appendChild(addInstanceModal);

        for (let key in data) {
            createInstance(key, data[key]);
        }
    });
}