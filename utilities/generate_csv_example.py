"""
Genera un file CSV di esempio nel formato Sistema di Pesatura.
Il file viene salvato nella cartella WATCH_DIR (default /var/opt/in-out/csv).

Uso:
    python genera_csv_esempio.py
    python genera_csv_esempio.py --righe 5 --out /tmp/test.csv
"""

import os
import csv
import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

# --- Dati di esempio ---
SOGGETTI = [
    ("Cliente", 1, "Baronpesi Srl",       "0444370720", "02331370243"),
    ("Cliente", 2, "Metalli Vicentini",   "0444123456", "01234560243"),
    ("Cliente", 3, "Rottami Nord Est",    "0445987654", "03456780243"),
]

VETTORI = [
    (1, "DHL",          "199199345", "00754800159"),
    (2, "BRT",          "199100100", "01234500159"),
    (3, "Fercam",       "0471123456","02345600159"),
]

AUTISTI = [
    (1, "Marco Ruggero",   "3471234567"),
    (2, "Luca Bianchi",    "3389876543"),
    (3, "Giorgio Ferrari", "3351122334"),
]

TESSERE = [
    (1, "00485", "3C00B4A1AC"),
    (2, "00511", "3C00B3E3EB"),
    (3, "00509", "01154A7BC5"),
]

VEICOLI = [
    (7,  "AB123CD", "Iveco Daily"),
    (12, "FG456HI", "Scania R450"),
    (3,  "ZX789WQ", "Mercedes Actros"),
]

MATERIALI = [
    (1, "Ferro"),
    (2, "Rame"),
    (3, "Alluminio"),
    (4, "Acciaio inox"),
]

NOTE_LIST = [
    "Nota di prova",
    "Consegna urgente",
    "",
    "Materiale certificato",
    "Verifica peso richiesta",
]


PESE = ["P1", "P2"]


def genera_pid(n: int) -> str:
    """Genera un PID nel formato 00000-XXXXX."""
    return f"00000-{n:05d}"


def genera_riga(n: int) -> list:
    """Genera una riga CSV con dati realistici."""
    sogg    = random.choice(SOGGETTI)
    vett    = random.choice(VETTORI)
    aut     = random.choice(AUTISTI)
    tess    = random.choice(TESSERE)
    veic    = random.choice(VEICOLI)
    mat     = random.choice(MATERIALI)
    nota    = random.choice(NOTE_LIST)
    bolla   = f"DDT{datetime.now().strftime('%Y%m%d')}{n:03d}"

    # Prima pesata: ora casuale nelle ultime 8 ore
    now   = datetime.now()
    data1 = now - timedelta(hours=random.randint(1, 8), minutes=random.randint(0, 59))
    data2 = data1 + timedelta(minutes=random.randint(5, 30))

    peso1 = random.randint(8000, 25000)   # veicolo carico
    peso2 = random.randint(3000, 7000)    # veicolo vuoto

    pid1  = genera_pid(n * 2 - 1)
    pid2  = genera_pid(n * 2)

    fmt = "%d/%m/%Y %H:%M"

    return [
        sogg[0],                    #  0 tipo_soggetto
        str(sogg[1]),               #  1 id_soggetto
        sogg[2],                    #  2 ragione_sociale_soggetto
        sogg[3],                    #  3 cell_soggetto
        sogg[4],                    #  4 cfpiva_soggetto
        str(vett[0]),               #  5 id_vettore
        vett[1],                    #  6 ragione_sociale_vettore
        vett[2],                    #  7 cell_vettore
        vett[3],                    #  8 cfpiva_vettore
        str(aut[0]),                #  9 id_autista
        aut[1],                     # 10 ragione_sociale_autista
        aut[2],                     # 11 cell_autista
        str(tess[0]),               # 12 id_tessera
        tess[1],                    # 13 numero_tessera
        tess[2],                    # 14 codice_tessera
        str(veic[0]),               # 15 id_veicolo
        veic[1],                    # 16 targa_veicolo
        veic[2],                    # 17 descrizione_veicolo
        str(mat[0]),                # 18 id_materiale
        mat[1],                     # 19 descrizione_materiale
        nota,                       # 20 note
        bolla,                      # 21 referenza_documento
        data1.strftime(fmt),        # 22 data1
        pid1,                       # 23 pid1
        str(peso1),                 # 24 peso1
        data2.strftime(fmt),        # 25 data2
        pid2,                       # 26 pid2
        str(peso2),                 # 27 peso2
        str(abs(peso1 - peso2)),    # 28 netto
    ]


def main():
    parser = argparse.ArgumentParser(description="Genera CSV di esempio per il sistema di pesatura.")
    parser.add_argument("--righe", type=int, default=3,  help="Numero di righe da generare (default: 3)")
    parser.add_argument("--out",   type=str, default="", help="Cartella di output (default: WATCH_DIR)")
    parser.add_argument("--pesa",  type=str, default="", help="Nome pesa (default: casuale tra P1/P2)")
    args = parser.parse_args()

    # Se --out è specificato, usa quella cartella; altrimenti WATCH_DIR
    if args.out:
        out_dir = Path(args.out)
    else:
        out_dir = Path(os.environ.get("WATCH_DIR", "/var/opt/in-out/csv"))

    out_dir.mkdir(parents=True, exist_ok=True)

    campi = [
        "tipo_soggetto","id_soggetto","ragione_sociale_soggetto","cell_soggetto","cfpiva_soggetto",
        "id_vettore","ragione_sociale_vettore","cell_vettore","cfpiva_vettore",
        "id_autista","ragione_sociale_autista","cell_autista",
        "id_tessera","numero_tessera","codice_tessera",
        "id_veicolo","targa_veicolo","descrizione_veicolo",
        "id_materiale","descrizione_materiale","note","referenza_documento",
        "data1","pid1","peso1","data2","pid2","peso2","netto",
    ]

    for i in range(1, args.righe + 1):
        riga = genera_riga(i)
        # Nome file come lo genera il sistema in uscita: <pesa>_<pid1>_<pid2>.csv
        pesa = args.pesa or random.choice(PESE)
        file_path = out_dir / f"{pesa}_{riga[23]}_{riga[26]}.csv"

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(riga)

        print(f"✓ File {i}/{args.righe}: {file_path.name}")

        # Anteprima solo del primo file
        if i == 1:
            print("\n  Anteprima:")
            for nome, valore in zip(campi, riga):
                print(f"    {nome:<30} = {valore}")
            print()


if __name__ == "__main__":
    main()