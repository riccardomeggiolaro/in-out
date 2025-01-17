export let list_serial_ports = [];

export let deleteButtonContent = 'Elimina';
await fetch('/static/content/delete.svg')
.then(res => res.text())
.then(data => {
    deleteButtonContent = data;
});

export let editButtonContent = 'Modifica';
await fetch('/static/content/edit.svg')
.then(res => res.text())
.then(data => {
    editButtonContent = data;
});

export let addButtonContent = 'Aggiungi';
await fetch('/static/content/add.svg')
.then(res => res.text())
.then(data => {
    addButtonContent = data;
});

export let recoveryPasswordButtonContent = 'Recupera password';
await fetch('/static/content/recovery_password.svg')
.then(res => res.text())
.then(data => {
    recoveryPasswordButtonContent = data;
});

export let printerButtonContent = 'Stampante';
await fetch('/static/content/printer.svg')
.then(res => res.text())
.then(data => {
    printerButtonContent = data;
});

await fetch('/generic/list_serial_ports')
.then(res => res.json())
.then(data => {
    list_serial_ports = data.list_serial_ports;
})

export let list_printer_names = [];
await fetch('/printer/list')
.then(res => res.json())
.then(data => {
    list_printer_names = data;
})