#!/usr/bin/env python3
"""
Script per eliminare da terminale tutti i dati da una o più tabelle del database.

Mostra prima il numero di record da eliminare e chiede conferma
prima di procedere.

Utilizzo:
    python3 delete_table_data.py --tables subject vector
    python3 delete_table_data.py --tables access in_out --db /percorso/database.db
    python3 delete_table_data.py --all
    python3 delete_table_data.py --all --force
    python3 delete_table_data.py --list
"""

import argparse
import sqlite3
import sys
from pathlib import Path

DEFAULT_DB = "/var/opt/in-out/database.db"

# Tutte le tabelle disponibili con nome visualizzato
AVAILABLE_TABLES = [
    "user",
    "subject",
    "vector",
    "driver",
    "vehicle",
    "material",
    "operator",
    "weighing",
    "weighing_picture",
    "card_registry",
    "weighing-terminal",
    "access",
    "in_out",
    "lock_record",
]

# Ordine sicuro di eliminazione (figli prima dei genitori) quando si usa --all
DELETION_ORDER = [
    "lock_record",
    "in_out",
    "weighing_picture",
    "weighing",
    "access",
    "card_registry",
    "subject",
    "vector",
    "driver",
    "vehicle",
    "material",
    "operator",
    "weighing-terminal",
    "user",
]


def open_db(db_path):
    if not Path(db_path).exists():
        print(f"Errore: database non trovato in '{db_path}'", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def count_records(conn, table):
    try:
        row = conn.execute(f'SELECT COUNT(*) AS n FROM "{table}"').fetchone()
        return row["n"]
    except sqlite3.OperationalError as e:
        print(f"Errore accesso tabella '{table}': {e}", file=sys.stderr)
        sys.exit(1)


def print_summary(counts):
    col_table = max(len(t) for t in counts) + 2
    col_count = max(len(str(n)) for n in counts.values()) + 2
    col_table = max(col_table, len("Tabella") + 2)
    col_count = max(col_count, len("Record") + 2)

    sep = f"+-{'-' * col_table}-+-{'-' * col_count}-+"
    print(sep)
    print(f"| {'Tabella'.ljust(col_table)} | {'Record'.ljust(col_count)} |")
    print(sep)
    for table, n in counts.items():
        print(f"| {table.ljust(col_table)} | {str(n).ljust(col_count)} |")
    print(sep)


def delete_tables(conn, tables):
    # Disabilita FK per permettere l'eliminazione in qualsiasi ordine
    conn.execute("PRAGMA foreign_keys = OFF")
    deleted = {}
    for table in tables:
        n = count_records(conn, table)
        conn.execute(f'DELETE FROM "{table}"')
        deleted[table] = n
    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")
    return deleted


def main():
    parser = argparse.ArgumentParser(
        description="Elimina tutti i dati da una o più tabelle del database in-out."
    )
    parser.add_argument(
        "--db",
        default=DEFAULT_DB,
        metavar="PATH",
        help=f"Percorso del file database SQLite (default: {DEFAULT_DB})",
    )
    parser.add_argument(
        "--tables",
        nargs="+",
        metavar="TABELLA",
        help="Una o più tabelle da svuotare (es. --tables subject vector)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="all_tables",
        help="Svuota tutte le tabelle",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Elimina senza chiedere conferma",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Mostra le tabelle disponibili ed esce",
    )
    args = parser.parse_args()

    if args.list:
        print("Tabelle disponibili:")
        for t in AVAILABLE_TABLES:
            print(f"  {t}")
        return

    if not args.tables and not args.all_tables:
        parser.error("Specifica --tables TABELLA [TABELLA ...] oppure --all")

    if args.all_tables:
        selected = list(DELETION_ORDER)
    else:
        selected = args.tables
        invalid = [t for t in selected if t not in AVAILABLE_TABLES]
        if invalid:
            print(f"Errore: tabelle non riconosciute: {', '.join(invalid)}", file=sys.stderr)
            print(f"Usa --list per vedere le tabelle disponibili.", file=sys.stderr)
            sys.exit(1)

    conn = open_db(args.db)

    counts = {table: count_records(conn, table) for table in selected}
    total = sum(counts.values())

    label = "tutte le tabelle" if args.all_tables else f"{len(selected)} tabella/e"
    print(f"\n  Record da eliminare da {label}:\n")
    print_summary(counts)
    print(f"\n  Totale: {total} record\n")

    if total == 0:
        print("Nessun record da eliminare.")
        conn.close()
        return

    if not args.force:
        try:
            risposta = input(f"Eliminare {total} record da {len(selected)} tabella/e? [s/N] ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nAnnullato.")
            conn.close()
            sys.exit(0)
        if risposta not in ("s", "si", "sì", "y", "yes"):
            print("Annullato.")
            conn.close()
            return

    deleted = delete_tables(conn, selected)
    conn.close()

    print()
    for table, n in deleted.items():
        print(f"  {table}: {n} record eliminati")
    print(f"\nTotale: {sum(deleted.values())} record eliminati.")


if __name__ == "__main__":
    main()
