#!/usr/bin/env python3
"""
Legge da test_as400.db solo le colonne definite in column.txt e le stampa.

Colonne usate (da column.txt):
    FEMRA0  - Anno del carico
    FEE8A0  - Progressivo
    FEA335  - Targa motrice
    FEHCTY  - Targa rimorchio
    FEHBTY  - Nome
    FEJSUS  - Carico/Scarico
    FEG1TY  - Note merce
    FERSCC  - Limite peso
    FER5TS  - Flag stampa peso
    FERSTS  - Tipo automezzo
    FER3CC  - Tara mezzo

Uso (dalla root del progetto):
    python3 as400/load_test.py
"""

import logging
import os
import sqlite3
import sys

TEST_DB_PATH = os.environ.get("TEST_DB_PATH", "as400/test_as400.db")

# Colonne definite in column.txt
COLUMNS = [
    "FEMRA0",   # Anno del carico
    "FEE8A0",   # Progressivo
    "FEA335",   # Targa motrice
    "FEHCTY",   # Targa rimorchio
    "FEHBTY",   # Nome
    "FEJSUS",   # Carico/Scarico
    "FEG1TY",   # Note merce
    "FERSCC",   # Limite peso
    "FER5TS",   # Flag stampa peso
    "FERSTS",   # Tipo automezzo
    "FER3CC",   # Tara mezzo
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("load_test")


def load_from_staging() -> list[dict]:
    """Legge da cararrp solo le colonne di column.txt."""
    col_list = ", ".join(COLUMNS)
    db = sqlite3.connect(TEST_DB_PATH)
    db.row_factory = sqlite3.Row
    try:
        cur = db.execute(f"SELECT {col_list} FROM cararrp")
        rows = cur.fetchall()
        log.info("Lette %d righe da %s", len(rows), TEST_DB_PATH)
        return [dict(r) for r in rows]
    finally:
        db.close()


def main() -> int:
    rows = load_from_staging()
    if not rows:
        log.warning("Nessuna riga trovata nello staging, uscita.")
        return 1

    # Stampa i dati a video
    header = " | ".join(f"{c:<12}" for c in COLUMNS)
    sep    = "-" * len(header)
    print(sep)
    print(header)
    print(sep)
    for r in rows:
        line = " | ".join(f"{str(r.get(c, '') or '').strip():<12}" for c in COLUMNS)
        print(line)
    print(sep)
    print(f"Totale: {len(rows)} righe")
    return 0


if __name__ == "__main__":
    sys.exit(main())
