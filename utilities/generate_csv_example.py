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


def genera_pid(n: int) -> str:
    """Genera un PID nel formato 00000-XXXXXX."""
    return f"00000-{n:06d}"


def genera_riga(n: int) -> list:
    """Genera una riga CSV con dati realistici."""
    sogg    = random.choice(SOGGETTI)
    vett    = random.choice(VETTORI)
    aut     = random.choice(AUTISTI)
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
        str(veic[0]),               # 12 id_veicolo
        veic[1],                    # 13 targa_veicolo
        veic[2],                    # 14 descrizione_veicolo
        str(mat[0]),                # 15 id_materiale
        mat[1],                     # 16 descrizione_materiale
        nota,                       # 17 note
        bolla,                      # 18 referenza_documento
        data1.strftime(fmt),        # 19 data1
        pid1,                       # 20 pid1
        str(peso1),                 # 21 peso1
        data2.strftime(fmt),        # 22 data2
        pid2,                       # 23 pid2
        str(peso2),                 # 24 peso2
    ]


def main():
    parser = argparse.ArgumentParser(description="Genera CSV di esempio per il sistema di pesatura.")
    parser.add_argument("--righe", type=int, default=3,  help="Numero di righe da generare (default: 3)")
    parser.add_argument("--out",   type=str, default="", help="Cartella di output (default: WATCH_DIR)")
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
        "id_veicolo","targa_veicolo","descrizione_veicolo",
        "id_materiale","descrizione_materiale","note","referenza_documento",
        "data1","pid1","peso1","data2","pid2","peso2",
    ]

    for i in range(1, args.righe + 1):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = out_dir / f"pesatura_{timestamp}_{i:03d}.csv"
        riga = genera_riga(i)

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