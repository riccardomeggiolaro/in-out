#!/usr/bin/env python3
"""
Script per eliminare da terminale tutti gli accessi con hidden=True.

Mostra prima la lista degli accessi da eliminare e chiede conferma
prima di procedere. Elimina anche i record in_out collegati (CASCADE).

Utilizzo:
    python3 delete_hidden_accesses.py
    python3 delete_hidden_accesses.py --db /percorso/database.db
    python3 delete_hidden_accesses.py --status Attesa
    python3 delete_hidden_accesses.py --force
"""

import argparse
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

def open_db(db_path):
    if not Path(db_path).exists():
        print(f"Errore: database non trovato in '{db_path}'", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Abilita i vincoli di chiave esterna per il CASCADE DELETE
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def fetch_hidden(conn, status_filter):
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
    return conn.execute(sql, params).fetchall()

def delete_hidden(conn, ids):
    placeholders = ",".join("?" * len(ids))
    # in_out viene eliminato via CASCADE (PRAGMA foreign_keys = ON)
    conn.execute(f"DELETE FROM access WHERE id IN ({placeholders})", ids)
    conn.commit()

def main():
    parser = argparse.ArgumentParser(
        description="Elimina tutti gli accessi con hidden=True dal database in-out."
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
        help="Elimina solo gli accessi con questo stato (es. Attesa, Entrato, Chiusa)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Elimina senza chiedere conferma",
    )
    args = parser.parse_args()

    conn = open_db(args.db)
    rows = fetch_hidden(conn, args.status)

    title = f"  Accessi con hidden=True — {len(rows)} record da eliminare"
    if args.status:
        title += f" (stato: {args.status})"
    print(title)
    print()

    table_rows = [
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
        for r in rows
    ]
    print_table(table_rows)

    if not rows:
        conn.close()
        return

    if not args.force:
        print()
        try:
            risposta = input(f"Eliminare {len(rows)} accesso/i (e relativi in_out)? [s/N] ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nAnnullato.")
            conn.close()
            sys.exit(0)
        if risposta not in ("s", "si", "sì", "y", "yes"):
            print("Annullato.")
            conn.close()
            return

    ids = [r["id"] for r in rows]
    delete_hidden(conn, ids)
    conn.close()
    print(f"Eliminati {len(ids)} accesso/i con hidden=True.")

if __name__ == "__main__":
    main()
