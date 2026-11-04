# Nuova interfaccia (v2)

Interfaccia nuova, separata da quella attuale (`static/ui/default`).
È servita dal server su **`/v2/`** e usa lo stesso login e le stesse API:
le due interfacce funzionano insieme.

- Nessun passaggio di compilazione e nessuna libreria esterna: HTML, CSS e
  moduli JavaScript (funziona anche senza internet presso il cliente).
- Navigazione con hash (`#/pesa`, `#/accessi`, …): una sola pagina.
- Tema chiaro di default, scuro automatico o dal pulsante in alto.

## Struttura

```
index.html            guscio: menu laterale, barra di stato, area contenuti
css/app.css           token dei colori, layout, componenti comuni
css/pesa.css          schermata Pesa
js/app.js             avvio, navigazione, barra di stato, tema
js/api.js             chiamate alle API con il token, apertura PDF protetti
js/plant.js           stato dell'impianto: configurazione + websocket per pesa,
                      eventi (realtime, data, weighing, report, picture, flash,
                      relays, message, access)
js/ui.js              escape HTML, avvisi, formattazione
js/views/pesa.js      schermata Pesa
js/views/impianto.js  vista 3D (per ora riusa /static/config3d.html)
js/views/placeholder.js  sezioni non ancora pronte
```

## Stato

| Sezione       | Stato |
|---------------|-------|
| Pesa          | pronta: peso, mezzo, entrata/uscita, tara, zero, ristampa, foto, sbarre, attività |
| Impianto      | vista 3D esistente |
| Accessi       | da fare |
| Anagrafiche   | da fare |
| Report        | da fare |
| Impostazioni  | da fare (configurazione guidata) |

## Scorciatoie (schermata Pesa)

F1 pesata entrata · F2 pesata uscita · F3 tara · F4 zero
