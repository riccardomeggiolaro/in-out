#!/usr/bin/env python3
"""
Script per visualizzare da terminale tutti gli accessi con hidden=True.

Utilizzo:
    python3 list_hidden_accesses.py
    python3 list_hidden_accesses.py --db /percorso/database.db
    python3 list_hidden_accesses.py --status Attesa
    python3 list_hidden_accesses.py --limit 50
    python3 list_hidden_accesses.py --json
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

DEFAULT_DB = "/var/opt/in-out/database.db"

COL_WIDTHS = {
    "ID":       5,
    "Stato":    10,
    "Tipo":     14,
    "Soggetto": 22,
    "Vettore":  22,
    "Autista":  22,
    "Veicolo":  12,
    "Materiale":16,
    "Creato":   20,
}

def pad(text, width):
    text = str(text) if text is not None else "-"
    if len(text) > width:
        text = text[: width - 1] + "…"
    return text.ljust(width)

def print_table(rows):
    headers = list(COL_WIDTHS.keys())
    sep = "+-" + "-+-".join("-" * w for w in COL_WIDTHS.values()) + "-+"
    header_row = "| " + " | ".join(pad(h, COL_WIDTHS[h]) for h in headers) + " |"

    print(sep)
    print(header_row)
    print(sep)
    if not rows:
        total_width = sum(COL_WIDTHS.values()) + 3 * len(COL_WIDTHS) + 1
        print("|" + " Nessun accesso con hidden=True trovato ".center(total_width) + "|")
    else:
        for r in rows:
            print("| " + " | ".join(pad(r[h], COL_WIDTHS[h]) for h in headers) + " |")
    print(sep)

def fetch_hidden_accesses(db_path, status_filter=None, limit=None):
    if not Path(db_path).exists():
        print(f"Errore: database non trovato in '{db_path}'", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    sql = """
        SELECT
            a.id,
            a.status,
            a.type,
            a.date_created,
            s.social_reason  AS subject,
            v.social_reason  AS vector,
            d.social_reason  AS driver,
            vh.plate         AS vehicle,
            m.description    AS material
        FROM access a
        LEFT JOIN subject  s  ON s.id  = a.idSubject
        LEFT JOIN vector   v  ON v.id  = a.idVector
        LEFT JOIN driver   d  ON d.id  = a.idDriver
        LEFT JOIN vehicle  vh ON vh.id = a.idVehicle
        LEFT JOIN material m  ON m.id  = a.idMaterial
        WHERE a.hidden = 1
    """
    params = []

    if status_filter:
        sql += " AND a.status = ?"
        params.append(status_filter)

    sql += " ORDER BY a.date_created DESC"

    if limit:
        sql += " LIMIT ?"
        params.append(limit)

    cur.execute(sql, params)
    raw = cur.fetchall()
    conn.close()
    return raw

def main():
    parser = argparse.ArgumentParser(
        description="Mostra tutti gli accessi con hidden=True nel database in-out."
    )
    parser.add_argument(
        "--db",
        default=DEFAULT_DB,
        metavar="PATH",
        help=f"Percorso del file database SQLite (default: {DEFAULT_DB})",
    )
    parser.add_argument(
        "--status",
        metavar="STATO",
        help="Filtra per stato (es. Attesa, Entrato, Chiusa)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        metavar="N",
        help="Numero massimo di righe da mostrare",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output in formato JSON invece che tabellare",
    )
    args = parser.parse_args()

    raw_rows = fetch_hidden_accesses(args.db, args.status, args.limit)

    if args.as_json:
        data = [
            {
                "id":        r["id"],
                "stato":     r["status"],
                "tipo":      r["type"],
                "soggetto":  r["subject"],
                "vettore":   r["vector"],
                "autista":   r["driver"],
                "veicolo":   r["vehicle"],
                "materiale": r["material"],
                "creato":    r["date_created"],
            }
            for r in raw_rows
        ]
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    rows = [
        {
            "ID":       r["id"],
            "Stato":    r["status"],
            "Tipo":     r["type"],
            "Soggetto": r["subject"],
            "Vettore":  r["vector"],
            "Autista":  r["driver"],
            "Veicolo":  r["vehicle"],
            "Materiale":r["material"],
            "Creato":   r["date_created"],
        }
        for r in raw_rows
    ]

    title = f"  Accessi con hidden=True — {len(rows)} record"
    if args.status:
        title += f" (stato: {args.status})"
    if args.limit:
        title += f" (max: {args.limit})"
    print(title)
    print()
    print_table(rows)


if __name__ == "__main__":
    main()
