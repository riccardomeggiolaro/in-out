let list_serial_ports = []

let list_printer_names = []

let template_report_in = new DataTransfer();

let template_report_out = new DataTransfer();

const editButtonContent = "✏️"

const deleteButtonContent = "🗑️";

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

async function getReportIn() {
    const response = await fetch('/api/generic/report-in');
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

document.addEventListener("DOMContentLoaded", loadSetupWeighers);

async function loadSetupWeighers() {
    const weighers_config = document.getElementById('config');

    await getSerialPortsList();

    await getPrintersList();

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
        console.log(status);
        const form = document.querySelector(classNameForm);

        if (e) e.preventDefault();
        
        const divRele = document.createElement("div");
        divRele.className = "rele";
        divRele.innerHTML = `
            <button class="delete-btn">${deleteButtonContent}</button>
            <span>Numero: </span> <input type="number" min="1" value="${number_rele ? number_rele : ''}" style="width: 50px" required>
            <select style="width: 75px">
                <option value="1" ${status === 1 ? 'selected' : ''}>Apri</option>
                <option value="0" ${status === 0 ? 'selected' : ''}>Chiudi</option>
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
        const labelReturnPdfCopyAfterWeighing = document.createElement('label');
        labelReturnPdfCopyAfterWeighing.textContent = "Ritorna copia pdf all'utente che effettua la pesata ";
        const returnPdfCopyAfterWeighing = document.createElement('input');
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
        const br = document.createElement('br');
        const labelSavePdfPath = document.createElement('label');
        const savePdfPath = document.createElement('input');
        const savePdfPathButton = document.createElement('button');
        let originalPathPdf = data.path_pdf ? data.path_pdf : '';
        labelSavePdfPath.textContent = "Directory salvataggio pesata in pdf: ";
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
                    showSnackbar("Directory salvata correttamente", 'rgb(208, 255, 208)', 'black');
                    savePdfPathButton.disabled = true;
                    originalPathPdf = value;
                } else {
                    showSnackbar("Directory non valida", 'rgb(255, 208, 208)', 'black');
                    savePdfPath.value = originalPathPdf;
                }
            })
        }
        const labelSaveCsvPath = document.createElement('label');
        const saveCsvPath = document.createElement('input');
        const saveCsvPathButton = document.createElement('button');
        let originalPathCsv = data.path_csv ? data.path_csv : '';
        labelSaveCsvPath.textContent = "Directory salvataggio pesata in csv: ";
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
                    showSnackbar("Directory salvata correttamente", 'rgb(208, 255, 208)', 'black');
                    saveCsvPathButton.disabled = true;
                    originalPathCsv = value;
                } else {
                    showSnackbar("Directory non valida", 'rgb(255, 208, 208)', 'black');
                    saveCsvPath.value = originalPathCsv;
                }
            })
        }
        const labelSaveImgPath = document.createElement('label');
        const saveImgPath = document.createElement('input');
        const saveImgPathButton = document.createElement('button');
        let originalPathImg = data.path_img ? data.path_img : '';
        labelSaveImgPath.textContent = "Directory salvataggio immagini: ";
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
                    showSnackbar("Directory salvata correttamente", 'rgb(208, 255, 208)', 'black');
                    saveImgPathButton.disabled = true;
                    originalPathImg = value;
                } else {
                    showSnackbar("Directory non valida", 'rgb(255, 208, 208)', 'black');
                    saveImgPath.value = originalPathImg;
                }
            })
        }
        const labelReportInt = document.createElement('label');
        const reportIn = document.createElement('input');
        const deleteReportIn = document.createElement('button');
        const downloadReportIn = document.createElement('a');
        const previewReportIn = document.createElement('a');
        labelReportInt.textContent = "Template di stampa alla pesata di entrata: ";
        reportIn.type = 'file';
        reportIn.accept = '.html';
        reportIn.files = template_report_in.files;
        reportIn.onchange = (e) => {
            if (e.target.files.length === 0) {
                reportIn.files = template_report_in.files;
            } else {
                const formData = new FormData();
                const file = e.target.files[0];
                template_report_in.items.remove(0);
                template_report_in.items.add(file);
                reportIn.files = template_report_in.files;
                formData.append('file', reportIn.files[0]);
                console.log(formData.get('file'));
                fetch('/api/generic/report-in', {
                    method: 'POST',
                    body: formData
                })
                .then(res => {
                    if (res.ok) {
                        console.log("ihbweibdeib");
                    }
                })
            }
        }
        deleteReportIn.textContent = '🗑️';
        deleteReportIn.onclick = (e) => {
            const removeReportIn = (e) => {
                fetch('/api/generic/report-in', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(res => {
                    if (res.ok) {
                        template_report_in = new DataTransfer();
                        reportIn.files = template_report_in.files;
                    } else {
                        res = res.json();
                        showSnackbar(res.detail, 'rgb(255, 208, 208)', 'black');
                    }
                })
            }
            if (confirm("Vuoi rimuovere il template di pesata all'entrata?")) {
                removeReportIn();
            }
        }
        downloadReportIn.style.textDecoration = "underline";
        downloadReportIn.style.color = "blue";
        downloadReportIn.style.marginLeft = "10px";
        downloadReportIn.style.marginRight = "10px";
        downloadReportIn.textContent = 'Scarica';
        downloadReportIn.onmouseover = (e) => {
            downloadReportIn.style.cursor = "pointer";
        }
        downloadReportIn.onclick = (e) => {
            if (template_report_in.files.length > 0) {
                const file = template_report_in.files[0];
                const url = URL.createObjectURL(file);
                const a = document.createElement('a');
                a.href = url;
                a.download = file.name;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            } else {
                showSnackbar("Nessun file da scaricare", 'rgb(255, 208, 208)', 'black');
            }
        };
        previewReportIn.style.textDecoration = "underline";
        previewReportIn.style.color = "blue";
        previewReportIn.textContent = 'Anteprima';
        previewReportIn.onmouseover = (e) => {
            previewReportIn.style.cursor = "pointer";
        }
        previewReportIn.onclick = async (e) => {
            if (template_report_in.files.length > 0) {
                // Assicurati che esista un endpoint che accetti il file HTML e restituisca il PDF
                const response = await fetch('/api/generic/report-in/preview');

                if (response.ok) {
                    const blob = await response.blob();
                    const url = URL.createObjectURL(blob);
                    window.open(url, '_blank');
                    // Puoi eventualmente revocare l'URL dopo un timeout
                    setTimeout(() => URL.revokeObjectURL(url), 10000);
                } else {
                    showSnackbar("Errore nella generazione dell'anteprima PDF", 'rgb(255, 208, 208)', 'black');
                }
            } else {
                showSnackbar("Nessun file selezionato", 'rgb(255, 208, 208)', 'black');
            }
        };
        const labelReportOut = document.createElement('label');
        const reportOut = document.createElement('input');
        const deleteReportOut = document.createElement('button');
        const downloadReportOut = document.createElement('a');
        const previewReportOut = document.createElement('a');
        labelReportOut.textContent = "Template di stampa alla pesata di uscita: ";
        reportOut.type = 'file';
        reportOut.accept = '.html';
        reportOut.files = template_report_out.files;
        deleteReportOut.textContent = '🗑️';
        deleteReportOut.onclick = (e) => {
            const removeReportOut = (e) => {
                fetch('/api/generic/report-out', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(res => {
                    if (res.ok) {
                        template_report_out = new DataTransfer();
                        reportOut.files = template_report_out.files;
                    } else {
                        res = res.json();
                        showSnackbar(res.detail, 'rgb(255, 208, 208)', 'black');
                    }
                })
            }
            if (confirm("Vuoi eliminare il template di pesata all'uscita?")) {
                removeReportOut();
            }
        }
        downloadReportOut.style.textDecoration = "underline";
        downloadReportOut.style.color = "blue";
        downloadReportOut.style.marginLeft = "10px";
        downloadReportOut.style.marginRight = "10px";
        downloadReportOut.textContent = ' Scarica ';
        downloadReportOut.onmouseover = (e) => {
            downloadReportOut.style.cursor = "pointer";
        }
        downloadReportOut.onclick = (e) => {
            if (template_report_out.files.length > 0) {
                const file = template_report_out.files[0];
                const url = URL.createObjectURL(file);
                const a = document.createElement('a');
                a.href = url;
                a.download = file.name;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            } else {
                showSnackbar("Nessun file da scaricare", 'rgb(255, 208, 208)', 'black');
            }
        };
        previewReportOut.style.textDecoration = "underline";
        previewReportOut.style.color = "blue";
        previewReportOut.textContent = 'Anteprima';
        previewReportOut.onmouseover = (e) => {
            previewReportOut.style.cursor = "pointer";
        }
        previewReportOut.onclick = async (e) => {
            if (template_report_in.files.length > 0) {
                // Assicurati che esista un endpoint che accetti il file HTML e restituisca il PDF
                const response = await fetch('/api/generic/report-out/preview');

                if (response.ok) {
                    const blob = await response.blob();
                    const url = URL.createObjectURL(blob);
                    window.open(url, '_blank');
                    // Puoi eventualmente revocare l'URL dopo un timeout
                    setTimeout(() => URL.revokeObjectURL(url), 10000);
                } else {
                    showSnackbar("Errore nella generazione dell'anteprima PDF", 'rgb(255, 208, 208)', 'black');
                }
            } else {
                showSnackbar("Nessun file selezionato", 'rgb(255, 208, 208)', 'black');
            }
        };
        weighers_config.appendChild(br.cloneNode(true));
        weighers_config.appendChild(labelReturnPdfCopyAfterWeighing);
        weighers_config.appendChild(returnPdfCopyAfterWeighing);
        weighers_config.appendChild(br.cloneNode(true));
        weighers_config.appendChild(br.cloneNode(true));
        weighers_config.appendChild(labelSavePdfPath);
        weighers_config.appendChild(savePdfPath);
        weighers_config.appendChild(savePdfPathButton);
        weighers_config.appendChild(br.cloneNode(true));
        weighers_config.appendChild(br.cloneNode(true));
        weighers_config.appendChild(labelSaveCsvPath);
        weighers_config.appendChild(saveCsvPath);
        weighers_config.appendChild(saveCsvPathButton);
        weighers_config.appendChild(br.cloneNode(true));
        weighers_config.appendChild(br.cloneNode(true));
        weighers_config.appendChild(labelSaveImgPath);
        weighers_config.appendChild(saveImgPath);
        weighers_config.appendChild(saveImgPathButton);
        weighers_config.appendChild(br.cloneNode(true));
        weighers_config.appendChild(br.cloneNode(true));
        weighers_config.appendChild(labelReportInt);
        weighers_config.appendChild(reportIn);
        weighers_config.appendChild(deleteReportIn);
        weighers_config.appendChild(downloadReportIn);
        weighers_config.appendChild(previewReportIn);
        weighers_config.appendChild(br.cloneNode(true));
        weighers_config.appendChild(br.cloneNode(true));
        weighers_config.appendChild(labelReportOut);
        weighers_config.appendChild(reportOut);
        weighers_config.appendChild(deleteReportOut);
        weighers_config.appendChild(downloadReportOut);
        weighers_config.appendChild(previewReportOut);
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
                        console.log(res)
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
                    <form class="content" id="add-form">
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
                for (const printer of list_printer_names) {
                    printerOptions += `<option value="${printer.nome}">${printer.nome}</option>`;
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
                                <option value="dgt1" selected>dgt1</option>
                                <option value="egt-af03">egt-af03</option>
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
                        <div class="form-group" style="flex: 2;">
                            <label for="printer_name">Stampante:</label>
                            <select id="printer_name" name="printer_name" required>
                                ${printerOptions}
                            </select>
                        </div>
                        <div class="form-group" style="flex: 1;">
                            <label for="number_of_prints">Numero di stampe:</label>
                            <input type="number" name="number_of_prints" id="number_of_prints" min="1" max="5" value="1" required>
                        </div>
                        <div class="form-group" style="flex: 1; text-align: center;">
                            <label>Stampa all'entrata</label><br>
                            <input type="checkbox" name="print_on_in">
                        </div>
                        <div class="form-group" style="flex: 1; text-align: center;">
                            <label>Stampa all'uscita</label><br>
                            <input type="checkbox" name="print_on_out">
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
                    if (selection.name) data[selection.name] = selection.value;
                })

                document.querySelector(`.${addCamClass}`).querySelectorAll(".cam").forEach(element => {
                    const inputs = element.querySelectorAll("input");
                    console.log(inputs[1])
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
                const viewMode = document.createElement('div');
                const editMode = document.createElement('div');
                editMode.style.display = 'none';

                viewMode.innerHTML = `
                    <div class="content"></div>
                    <div class="container-buttons">
                        <button class="delete-btn">${deleteButtonContent}</button>
                        <button class="edit-btn">${editButtonContent}</button>
                    </div>
                `;

                const populateViewContent = (data) => {
                    console.log(data);
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
                        <p class="gray"><em>In esecuzione: ${data.run ? 'Si' : 'No'}</em></p>
                        <p class="gray"><em>Scaricare pesa dopo pesata effettuata: ${data.need_take_of_weight_before_weighing ? 'Si' : 'No'}</em></p>
                        <p class="gray"><em>Scaricare pesa all'avvio: ${data.need_take_of_weight_on_startup ? 'Si' : 'No'}</em></p>
                        <p class="gray"><em>Stampante: ${data.printer_name ? data.printer_name : 'Nessuna'}</em></p>
                        <p class="gray"><em>Numero di stampe: ${data.number_of_prints}</em></p>
                        <p class="gray"><em>Stampa all'entrata: ${data.events.weighing.print.in ? 'Si' : 'No'}</em> <strong>-</strong> <em>Stampa all'entrata: ${data.events.weighing.print.out ? 'Si' : 'No'}</em></p>
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
                                <p class="gray"><em>${r.set ? 'Apri' : 'Chiudi'} relè ${r.rele} sopra il peso minimo</em></p>
                            `;
                        });
                        under_min.forEach(r => {
                            viewModeCFontent.innerHTML += `
                                <p class="gray"><em>${r.set ? 'Apri' : 'Chiudi'} relè ${r.rele} sotto il peso minimo</em></p>
                            `;
                        });
                        weighing.forEach(r => {
                            viewModeCFontent.innerHTML += `
                                <p class="gray"><em>${r.set ? 'Apri' : 'Chiudi'} relè ${r.rele} dopo la pesata</em></p>
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

                console.log(editWeigherForm)

                editWeigherForm.oninput = () => {
                    editMode.querySelector('.save-btn').disabled = !editWeigherForm.checkValidity();
                }

                const addCamWeigher = `cams-${key}-${weigher.name}`;
                const addReleWeigher = `rele-${key}-${weigher.name}`;

                const populateEditContent = (data) => {
                    // Genera le option per le stampanti
                    let printerOptions = '';
                    for (const printer of list_printer_names) {
                        printerOptions += `<option value="${printer.nome}" ${data.printer_name === printer.nome ? 'selected' : ''}>${printer.nome}</option>`;
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
                                    <option value="dgt1" ${data.terminal === "dgt1" ? 'selected' : ''}>dgt1</option>
                                    <option value="egt-af03" ${data.terminal === "egt-af03" ? 'selected' : ''}>egt-af03</option>
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
                            <div class="form-group" style="flex: 2;">
                                <label for="printer_name">Stampante:</label><br>
                                <select id="printer_name" name="printer_name" required>
                                    ${printerOptions}
                                </select>
                            </div>
                            <div class="form-group" style="flex: 1;">
                                <label for="number_of_prints">Numero di stampe:</label><br>
                                <input type="number" name="number_of_prints" id="number_of_prints" min="1" max="5" value="${data.number_of_prints || 1}" required>
                            </div>
                            <div class="form-group" style="flex: 1; text-align: center;">
                                <label>Stampa all'entrata</label><br>
                                <input type="checkbox" name="print_on_in" ${data.events?.weighing?.print?.in ? 'checked' : ''}>
                            </div>
                            <div class="form-group" style="flex: 1; text-align: center;">
                                <label>Stampa all'uscita</label><br>
                                <input type="checkbox" name="print_on_out" ${data.events?.weighing?.print?.out ? 'checked' : ''}>
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
                });

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
                        const originalValue = weigher[selection.name];
                        const currentValue = selection.value;

                        if (currentValue !== originalValue) {
                            changedData[selection.name] = currentValue;
                        }
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
                    console.log(weigher)
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
            weighers_config.appendChild(div);
        }

        populateInstanceModal();

        weighers_config.appendChild(addInstance);
        weighers_config.appendChild(addInstanceModal);

        for (let key in data) {
            createInstance(key, data[key]);
        }
    });
}