"""
Script per generare un PDF semplificato dell'architettura di BARON IN-OUT
destinato a un pubblico non tecnico.
"""

from weasyprint import HTML

html_content = """
<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<style>
  @page {
    size: A4;
    margin: 2cm;
  }

  body {
    font-family: Helvetica, Arial, sans-serif;
    color: #2c3e50;
    font-size: 13px;
    line-height: 1.6;
  }

  /* ---- COVER ---- */
  .cover {
    text-align: center;
    padding-top: 120px;
    page-break-after: always;
  }
  .cover h1 {
    font-size: 38px;
    color: #1a5276;
    margin-bottom: 10px;
  }
  .cover .subtitle {
    font-size: 20px;
    color: #5d6d7e;
    margin-bottom: 40px;
  }
  .cover .version {
    font-size: 14px;
    color: #7f8c8d;
    margin-top: 60px;
  }
  .cover .logo-box {
    width: 120px;
    height: 120px;
    background: #1a5276;
    border-radius: 24px;
    margin: 0 auto 30px auto;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 48px;
    font-weight: bold;
  }

  /* ---- HEADINGS ---- */
  h2 {
    color: #1a5276;
    border-bottom: 3px solid #2980b9;
    padding-bottom: 6px;
    margin-top: 30px;
    font-size: 22px;
  }
  h3 {
    color: #2980b9;
    font-size: 16px;
    margin-top: 20px;
  }

  /* ---- CARDS ---- */
  .card {
    background: #f4f6f9;
    border-left: 5px solid #2980b9;
    border-radius: 6px;
    padding: 14px 18px;
    margin: 14px 0;
    break-inside: avoid;
  }
  .card.green  { border-left-color: #27ae60; background: #f0faf3; }
  .card.orange { border-left-color: #e67e22; background: #fef5ec; }
  .card.purple { border-left-color: #8e44ad; background: #f5eef8; }
  .card.red    { border-left-color: #c0392b; background: #fdf2f2; }

  .card strong {
    display: block;
    font-size: 14px;
    margin-bottom: 4px;
  }

  /* ---- FLOW DIAGRAM (CSS) ---- */
  .flow {
    text-align: center;
    margin: 20px 0;
  }
  .flow-step {
    display: inline-block;
    background: #2980b9;
    color: white;
    padding: 10px 18px;
    border-radius: 8px;
    margin: 6px;
    font-weight: bold;
    font-size: 13px;
    min-width: 120px;
  }
  .flow-step.alt { background: #27ae60; }
  .flow-step.highlight { background: #e67e22; }
  .flow-arrow {
    display: inline-block;
    font-size: 22px;
    color: #7f8c8d;
    vertical-align: middle;
    margin: 0 2px;
  }

  /* ---- VERTICAL FLOW ---- */
  .vflow {
    margin: 14px auto;
    width: 80%;
  }
  .vflow-step {
    background: #2980b9;
    color: white;
    padding: 8px 16px;
    border-radius: 8px;
    margin: 0 auto;
    text-align: center;
    font-weight: bold;
    font-size: 12px;
    max-width: 380px;
  }
  .vflow-step.alt { background: #27ae60; }
  .vflow-step.highlight { background: #e67e22; }
  .vflow-step.purple { background: #8e44ad; }
  .vflow-arrow {
    text-align: center;
    font-size: 18px;
    color: #7f8c8d;
    margin: 2px 0;
  }

  /* ---- TABLE ---- */
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0;
    font-size: 12px;
    break-inside: avoid;
  }
  th {
    background: #1a5276;
    color: white;
    padding: 10px 12px;
    text-align: left;
  }
  td {
    padding: 8px 12px;
    border-bottom: 1px solid #dce1e6;
  }
  tr:nth-child(even) { background: #f4f6f9; }

  /* ---- UTILITIES ---- */
  .page-break { page-break-before: always; }
  .highlight-box {
    background: #eaf2f8;
    border: 2px solid #2980b9;
    border-radius: 8px;
    padding: 16px;
    margin: 16px 0;
    text-align: center;
    break-inside: avoid;
  }
  .two-col {
    display: flex;
    gap: 16px;
    break-inside: avoid;
  }
  .two-col > div { flex: 1; }

  ul { padding-left: 20px; }
  li { margin-bottom: 4px; }

  .footer-note {
    color: #7f8c8d;
    font-size: 11px;
    text-align: center;
    margin-top: 40px;
    border-top: 1px solid #dce1e6;
    padding-top: 10px;
  }
</style>
</head>
<body>

<!-- ================================================================ -->
<!--                          COPERTINA                               -->
<!-- ================================================================ -->
<div class="cover">
  <div class="logo-box">B</div>
  <h1>BARON IN-OUT</h1>
  <div class="subtitle">Come Funziona il Sistema di Pesatura</div>
  <p style="font-size: 16px; color: #7f8c8d; max-width: 460px; margin: 20px auto;">
    Una guida semplice per capire come funziona il software
    che gestisce le operazioni di pesatura dei veicoli.
  </p>
  <div class="version">Versione 3.0.1 &mdash; Febbraio 2026</div>
</div>

<!-- ================================================================ -->
<!--                       COS'È BARON IN-OUT                         -->
<!-- ================================================================ -->
<h2>1. Cos'è BARON IN-OUT?</h2>

<div class="highlight-box">
  <strong style="font-size: 16px;">BARON IN-OUT è un software che gestisce la pesatura
  dei veicoli in entrata e in uscita da un impianto.</strong>
</div>

<p>Immagina un camion che arriva in un'azienda per caricare o scaricare materiale.
Il sistema BARON IN-OUT si occupa di:</p>

<div class="two-col">
  <div class="card">
    <strong>Identificare il veicolo</strong>
    Riconosce chi arriva tramite badge RFID o inserimento manuale
    (targa, autista, trasportatore, cliente).
  </div>
  <div class="card green">
    <strong>Pesare il veicolo</strong>
    Registra il peso in entrata e in uscita per calcolare
    il peso netto del materiale trasportato.
  </div>
</div>
<div class="two-col">
  <div class="card orange">
    <strong>Generare documenti</strong>
    Crea automaticamente report PDF e fogli Excel
    con tutti i dati della pesatura.
  </div>
  <div class="card purple">
    <strong>Controllare l'accesso</strong>
    Gestisce barriere, pannelli informativi e sirene
    per guidare il veicolo durante le operazioni.
  </div>
</div>

<!-- ================================================================ -->
<!--                    COME FUNZIONA IN PRATICA                      -->
<!-- ================================================================ -->
<div class="page-break"></div>
<h2>2. Come Funziona in Pratica?</h2>

<p>Ecco cosa succede quando un veicolo arriva all'impianto, passo dopo passo:</p>

<div class="vflow">
  <div class="vflow-step">1. Il veicolo arriva e viene identificato<br><small>(badge RFID o inserimento manuale)</small></div>
  <div class="vflow-arrow">&#x25BC;</div>
  <div class="vflow-step alt">2. Il pannello mostra la targa e la posizione</div>
  <div class="vflow-arrow">&#x25BC;</div>
  <div class="vflow-step highlight">3. Prima pesatura &mdash; peso in ENTRATA</div>
  <div class="vflow-arrow">&#x25BC;</div>
  <div class="vflow-step purple">4. Il veicolo carica o scarica il materiale</div>
  <div class="vflow-arrow">&#x25BC;</div>
  <div class="vflow-step highlight">5. Seconda pesatura &mdash; peso in USCITA</div>
  <div class="vflow-arrow">&#x25BC;</div>
  <div class="vflow-step">6. Il sistema calcola il peso netto<br><small>(differenza tra le due pesature)</small></div>
  <div class="vflow-arrow">&#x25BC;</div>
  <div class="vflow-step alt">7. Viene generato il documento PDF e stampato</div>
</div>

<div class="card">
  <strong>Esempio pratico</strong>
  Un camion entra e pesa <strong>15.000 kg</strong> (vuoto).
  Dopo il carico pesa <strong>40.000 kg</strong>.
  Il sistema calcola: il materiale caricato pesa <strong>25.000 kg</strong>.
</div>

<!-- ================================================================ -->
<!--                    I COMPONENTI DEL SISTEMA                       -->
<!-- ================================================================ -->
<div class="page-break"></div>
<h2>3. I Componenti del Sistema</h2>

<p>Il sistema è composto da diverse parti che lavorano insieme,
come gli ingranaggi di un orologio:</p>

<h3>Il "Cervello" &mdash; Il Server</h3>
<div class="card">
  <strong>Cosa fa?</strong>
  È il computer centrale che gestisce tutte le operazioni. Riceve i dati dalle bilance,
  salva le informazioni, genera i documenti e comunica con tutti gli altri dispositivi.
</div>

<h3>L'Interfaccia Web &mdash; La Schermata</h3>
<div class="card green">
  <strong>Cosa fa?</strong>
  È la pagina che gli operatori vedono sul loro computer o tablet.
  Da qui possono registrare i veicoli, avviare le pesature,
  consultare lo storico e stampare i report.
  Funziona come un sito web accessibile dal browser.
</div>

<h3>Le Bilance &mdash; Gli "Occhi" del Sistema</h3>
<div class="card orange">
  <strong>Cosa fa?</strong>
  Sono le piattaforme fisiche su cui sale il veicolo.
  Inviano il peso rilevato al server in tempo reale.
  Il sistema supporta più bilance contemporaneamente.
</div>

<h3>Il Lettore RFID &mdash; Il "Riconoscitore"</h3>
<div class="card purple">
  <strong>Cosa fa?</strong>
  Legge il badge del veicolo o dell'autista per identificarlo automaticamente,
  senza bisogno di digitare dati manualmente.
</div>

<h3>Pannelli e Sirene &mdash; I "Segnalatori"</h3>
<div class="card red">
  <strong>Cosa fa?</strong>
  I pannelli mostrano informazioni al conducente (es. "posizionarsi sulla bilancia").
  Le sirene avvisano in caso di situazioni particolari.
</div>

<!-- ================================================================ -->
<!--                  COME COMUNICANO I COMPONENTI                     -->
<!-- ================================================================ -->
<div class="page-break"></div>
<h2>4. Come Comunicano tra Loro?</h2>

<p>Tutti i componenti sono collegati al server centrale,
che fa da "direttore d'orchestra":</p>

<div class="highlight-box" style="max-width: 520px; margin: 20px auto;">
  <table style="border: none; margin: 0;">
    <tr><td style="text-align: center; border: none; padding: 10px;">
      <div style="background: #e67e22; color: white; padding: 8px; border-radius: 6px; display: inline-block; margin: 4px;">Bilance</div>
      <div style="background: #8e44ad; color: white; padding: 8px; border-radius: 6px; display: inline-block; margin: 4px;">Lettore RFID</div>
      <div style="background: #c0392b; color: white; padding: 8px; border-radius: 6px; display: inline-block; margin: 4px;">Pannelli</div>
    </td></tr>
    <tr><td style="text-align: center; border: none; font-size: 20px; color: #7f8c8d;">&#x25BC; &#x25B2;</td></tr>
    <tr><td style="text-align: center; border: none; padding: 10px;">
      <div style="background: #1a5276; color: white; padding: 14px 30px; border-radius: 10px; display: inline-block; font-size: 16px; font-weight: bold;">
        SERVER CENTRALE
      </div>
    </td></tr>
    <tr><td style="text-align: center; border: none; font-size: 20px; color: #7f8c8d;">&#x25BC; &#x25B2;</td></tr>
    <tr><td style="text-align: center; border: none; padding: 10px;">
      <div style="background: #27ae60; color: white; padding: 8px; border-radius: 6px; display: inline-block; margin: 4px;">Schermata Operatore</div>
      <div style="background: #2980b9; color: white; padding: 8px; border-radius: 6px; display: inline-block; margin: 4px;">Stampante</div>
      <div style="background: #7f8c8d; color: white; padding: 8px; border-radius: 6px; display: inline-block; margin: 4px;">Server Remoto</div>
    </td></tr>
  </table>
</div>

<div class="card">
  <strong>Aggiornamenti in tempo reale</strong>
  Quando la bilancia rileva un cambiamento di peso, il dato appare
  immediatamente sullo schermo dell'operatore &mdash; senza bisogno
  di ricaricare la pagina. Più operatori possono lavorare
  contemporaneamente e vedono tutti gli stessi dati aggiornati.
</div>

<!-- ================================================================ -->
<!--                     DOVE FINISCONO I DATI                         -->
<!-- ================================================================ -->
<div class="page-break"></div>
<h2>5. Dove Finiscono i Dati?</h2>

<p>Tutte le informazioni vengono salvate in modo sicuro:</p>

<table>
  <tr>
    <th>Tipo di Dato</th>
    <th>Dove Viene Salvato</th>
    <th>Formato</th>
  </tr>
  <tr>
    <td>Pesature e anagrafiche</td>
    <td>Database locale sul server</td>
    <td>Archivio digitale</td>
  </tr>
  <tr>
    <td>Documenti di pesatura</td>
    <td>Cartella PDF sul server</td>
    <td>PDF</td>
  </tr>
  <tr>
    <td>Esportazioni dati</td>
    <td>Cartella CSV sul server</td>
    <td>Excel / CSV</td>
  </tr>
  <tr>
    <td>Foto dei carichi</td>
    <td>Cartella immagini sul server</td>
    <td>Immagine</td>
  </tr>
</table>

<div class="card green">
  <strong>Sincronizzazione remota</strong>
  I documenti possono essere copiati automaticamente
  su un server remoto, così sono accessibili anche dall'esterno
  e c'è sempre una copia di sicurezza.
</div>

<!-- ================================================================ -->
<!--                     SICUREZZA E ACCESSI                           -->
<!-- ================================================================ -->
<div class="page-break"></div>
<h2>6. Sicurezza e Controllo Accessi</h2>

<p>Il sistema protegge i dati con diversi livelli di sicurezza:</p>

<table>
  <tr>
    <th>Livello</th>
    <th>Chi È</th>
    <th>Cosa Può Fare</th>
  </tr>
  <tr>
    <td><strong>Consultazione</strong></td>
    <td>Utente base</td>
    <td>Può solo visualizzare i dati</td>
  </tr>
  <tr>
    <td><strong>Operatore</strong></td>
    <td>Addetto alla pesa</td>
    <td>Può pesare veicoli e creare record</td>
  </tr>
  <tr>
    <td><strong>Amministratore</strong></td>
    <td>Responsabile</td>
    <td>Può gestire utenti e configurazioni</td>
  </tr>
  <tr>
    <td><strong>Super Admin</strong></td>
    <td>Tecnico di sistema</td>
    <td>Accesso completo a tutte le funzionalità</td>
  </tr>
</table>

<div class="card">
  <strong>Come funziona?</strong>
  Ogni operatore accede con il proprio nome utente e password.
  Il sistema registra chi ha effettuato ogni operazione,
  garantendo la tracciabilità completa.
</div>

<div class="card orange">
  <strong>Blocco dei record</strong>
  Quando un operatore sta modificando un dato, il sistema lo
  "blocca" per evitare che un altro operatore possa modificarlo
  contemporaneamente, prevenendo errori e conflitti.
</div>

<!-- ================================================================ -->
<!--                     FUNZIONALITÀ PRINCIPALI                       -->
<!-- ================================================================ -->
<h2>7. Le Funzionalità Principali</h2>

<div class="two-col">
  <div>
    <div class="card">
      <strong>Pesatura Veicoli</strong>
      Gestione completa del ciclo entrata/uscita
      con calcolo automatico del peso netto.
    </div>
    <div class="card green">
      <strong>Gestione Anagrafiche</strong>
      Archivio di clienti, trasportatori, autisti,
      veicoli e materiali sempre aggiornato.
    </div>
    <div class="card orange">
      <strong>Report e Stampe</strong>
      Generazione automatica di documenti PDF
      personalizzabili e fogli Excel.
    </div>
  </div>
  <div>
    <div class="card purple">
      <strong>Prenotazioni</strong>
      I veicoli possono essere prenotati in anticipo
      per velocizzare le operazioni all'arrivo.
    </div>
    <div class="card red">
      <strong>Assistenza Remota</strong>
      Il tecnico può collegarsi da remoto per
      manutenzione e supporto, senza essere in sede.
    </div>
    <div class="card">
      <strong>Multi-bilancia</strong>
      Supporto per più bilance collegate
      contemporaneamente allo stesso sistema.
    </div>
  </div>
</div>

<!-- ================================================================ -->
<!--                         RIEPILOGO                                 -->
<!-- ================================================================ -->
<div class="page-break"></div>
<h2>8. Riepilogo Visivo</h2>

<p>Ecco una visione d'insieme di come tutto si collega:</p>

<div style="background: #f4f6f9; border-radius: 12px; padding: 20px; margin: 20px 0;">

  <div style="text-align: center; margin-bottom: 16px;">
    <span style="background: #1a5276; color: white; padding: 10px 30px; border-radius: 8px; font-weight: bold; font-size: 15px;">
      IL VEICOLO ARRIVA ALL'IMPIANTO
    </span>
  </div>

  <div style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-bottom: 16px;">
    <div style="background: white; border: 2px solid #8e44ad; border-radius: 8px; padding: 12px; width: 140px; text-align: center;">
      <strong style="color: #8e44ad;">Identificazione</strong><br>
      <small>Badge RFID o manuale</small>
    </div>
    <div style="font-size: 24px; align-self: center; color: #7f8c8d;">&#x25B6;</div>
    <div style="background: white; border: 2px solid #e67e22; border-radius: 8px; padding: 12px; width: 140px; text-align: center;">
      <strong style="color: #e67e22;">Pesatura 1</strong><br>
      <small>Peso in entrata</small>
    </div>
    <div style="font-size: 24px; align-self: center; color: #7f8c8d;">&#x25B6;</div>
    <div style="background: white; border: 2px solid #27ae60; border-radius: 8px; padding: 12px; width: 140px; text-align: center;">
      <strong style="color: #27ae60;">Carico/Scarico</strong><br>
      <small>Operazioni materiale</small>
    </div>
  </div>

  <div style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
    <div style="background: white; border: 2px solid #e67e22; border-radius: 8px; padding: 12px; width: 140px; text-align: center;">
      <strong style="color: #e67e22;">Pesatura 2</strong><br>
      <small>Peso in uscita</small>
    </div>
    <div style="font-size: 24px; align-self: center; color: #7f8c8d;">&#x25B6;</div>
    <div style="background: white; border: 2px solid #2980b9; border-radius: 8px; padding: 12px; width: 140px; text-align: center;">
      <strong style="color: #2980b9;">Calcolo Netto</strong><br>
      <small>Differenza peso</small>
    </div>
    <div style="font-size: 24px; align-self: center; color: #7f8c8d;">&#x25B6;</div>
    <div style="background: white; border: 2px solid #1a5276; border-radius: 8px; padding: 12px; width: 140px; text-align: center;">
      <strong style="color: #1a5276;">Documento</strong><br>
      <small>PDF + stampa</small>
    </div>
  </div>

  <div style="text-align: center; margin-top: 16px;">
    <span style="background: #27ae60; color: white; padding: 10px 30px; border-radius: 8px; font-weight: bold; font-size: 15px;">
      IL VEICOLO ESCE &mdash; OPERAZIONE COMPLETATA
    </span>
  </div>
</div>

<!-- ================================================================ -->
<!--                         GLOSSARIO                                 -->
<!-- ================================================================ -->
<h2>9. Glossario</h2>

<table>
  <tr>
    <th>Termine</th>
    <th>Significato</th>
  </tr>
  <tr>
    <td><strong>Peso Lordo</strong></td>
    <td>Il peso totale del veicolo con il carico</td>
  </tr>
  <tr>
    <td><strong>Tara</strong></td>
    <td>Il peso del veicolo vuoto</td>
  </tr>
  <tr>
    <td><strong>Peso Netto</strong></td>
    <td>La differenza tra peso lordo e tara (= peso del solo materiale)</td>
  </tr>
  <tr>
    <td><strong>RFID</strong></td>
    <td>Tecnologia che permette di leggere un badge senza contatto fisico</td>
  </tr>
  <tr>
    <td><strong>Server</strong></td>
    <td>Il computer centrale che gestisce tutte le operazioni</td>
  </tr>
  <tr>
    <td><strong>Soggetto</strong></td>
    <td>Il cliente o fornitore coinvolto nell'operazione</td>
  </tr>
  <tr>
    <td><strong>Vettore</strong></td>
    <td>L'azienda di trasporto che porta il materiale</td>
  </tr>
  <tr>
    <td><strong>Accesso</strong></td>
    <td>Una singola operazione di entrata/uscita di un veicolo</td>
  </tr>
</table>

<div class="footer-note">
  BARON IN-OUT v3.0.1 &mdash; Documento generato automaticamente &mdash; Febbraio 2026
</div>

</body>
</html>
"""


def generate_pdf(output_path="docs/architettura_semplificata.pdf"):
    """Genera il PDF dell'architettura semplificata."""
    html = HTML(string=html_content)
    html.write_pdf(output_path)
    print(f"PDF generato con successo: {output_path}")


if __name__ == "__main__":
    generate_pdf()
