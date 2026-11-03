from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from applications.middleware.super_admin import is_super_admin
from modules.md_database.md_database import engine
import sqlite3

MAX_ROWS = 1000

class QueryDTO(BaseModel):
    sql: str
    limit: int = 500

def _connect():
    """Apre una connessione SQLite in sola lettura, separata da SQLAlchemy."""
    conn = sqlite3.connect(f"file:{engine.url.database}?mode=ro", uri=True, timeout=5)
    conn.execute("PRAGMA query_only = ON")
    return conn

# Azioni consentite alle query libere: solo lettura, niente ATTACH/PRAGMA/scritture
_ALLOWED_ACTIONS = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, getattr(sqlite3, 'SQLITE_RECURSIVE', 33)}

def _read_only_authorizer(action, arg1, arg2, db_name, trigger):
    return sqlite3.SQLITE_OK if action in _ALLOWED_ACTIONS else sqlite3.SQLITE_DENY

def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

def _table_exists(conn, name: str) -> bool:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name = ?", (name,)).fetchone()
    return row is not None

class DatabaseViewerRouter:
    def __init__(self):
        self.router = APIRouter()

        self.router.add_api_route('/tables', self.getTables, methods=['GET'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('/tables/{name}', self.getTableSchema, methods=['GET'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('/tables/{name}/rows', self.getTableRows, methods=['GET'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('/query', self.runQuery, methods=['POST'], dependencies=[Depends(is_super_admin)])

    async def getTables(self):
        conn = _connect()
        try:
            objects = conn.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
            tables = []
            for name, type_ in objects:
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {_quote(name)}").fetchone()[0]
                except sqlite3.Error:
                    count = None
                tables.append({"name": name, "type": type_, "rows": count})
            return {"path": engine.url.database, "tables": tables}
        finally:
            conn.close()

    async def getTableSchema(self, name: str):
        conn = _connect()
        try:
            if not _table_exists(conn, name):
                raise HTTPException(status_code=404, detail=f"Tabella '{name}' non trovata")
            columns = [
                {"cid": c[0], "name": c[1], "type": c[2], "notnull": bool(c[3]), "default": c[4], "pk": bool(c[5])}
                for c in conn.execute(f"PRAGMA table_info({_quote(name)})").fetchall()
            ]
            indexes = []
            for idx in conn.execute(f"PRAGMA index_list({_quote(name)})").fetchall():
                cols = [c[2] for c in conn.execute(f"PRAGMA index_info({_quote(idx[1])})").fetchall()]
                indexes.append({"name": idx[1], "unique": bool(idx[2]), "origin": idx[3], "columns": cols})
            foreign_keys = [
                {"column": fk[3], "table": fk[2], "to": fk[4]}
                for fk in conn.execute(f"PRAGMA foreign_key_list({_quote(name)})").fetchall()
            ]
            sql = conn.execute("SELECT sql FROM sqlite_master WHERE name = ?", (name,)).fetchone()[0]
            return {"name": name, "columns": columns, "indexes": indexes, "foreign_keys": foreign_keys, "sql": sql}
        finally:
            conn.close()

    async def getTableRows(self, name: str, limit: int = Query(100, ge=1, le=MAX_ROWS), offset: int = Query(0, ge=0), order: str = None, desc: bool = False):
        conn = _connect()
        try:
            if not _table_exists(conn, name):
                raise HTTPException(status_code=404, detail=f"Tabella '{name}' non trovata")
            columns = [c[1] for c in conn.execute(f"PRAGMA table_info({_quote(name)})").fetchall()]
            order_by = ""
            if order:
                if order not in columns:
                    raise HTTPException(status_code=400, detail=f"Colonna '{order}' non valida")
                order_by = f" ORDER BY {_quote(order)} {'DESC' if desc else 'ASC'}"
            total = conn.execute(f"SELECT COUNT(*) FROM {_quote(name)}").fetchone()[0]
            cursor = conn.execute(f"SELECT * FROM {_quote(name)}{order_by} LIMIT ? OFFSET ?", (limit, offset))
            return {
                "columns": [d[0] for d in cursor.description],
                "rows": cursor.fetchall(),
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        finally:
            conn.close()

    async def runQuery(self, body: QueryDTO):
        limit = max(1, min(body.limit, MAX_ROWS))
        conn = _connect()
        conn.set_authorizer(_read_only_authorizer)
        try:
            cursor = conn.execute(body.sql)
            if cursor.description is None:
                return {"columns": [], "rows": [], "truncated": False}
            rows = cursor.fetchmany(limit + 1)
            return {
                "columns": [d[0] for d in cursor.description],
                "rows": rows[:limit],
                "truncated": len(rows) > limit,
            }
        except (sqlite3.Error, sqlite3.Warning) as e:
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            conn.close()
