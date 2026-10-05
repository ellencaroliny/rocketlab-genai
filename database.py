"""Acesso somente-leitura ao SQLite, com validação de SQL (guardrail)."""
import sqlite3
import time
from datetime import datetime

from . import config

_DENIED = {
    sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE,
    sqlite3.SQLITE_CREATE_TABLE, sqlite3.SQLITE_DROP_TABLE, sqlite3.SQLITE_ALTER_TABLE,
    sqlite3.SQLITE_CREATE_INDEX, sqlite3.SQLITE_DROP_INDEX, sqlite3.SQLITE_ATTACH,
    sqlite3.SQLITE_DETACH, sqlite3.SQLITE_PRAGMA, sqlite3.SQLITE_TRANSACTION,
    sqlite3.SQLITE_CREATE_VIEW, sqlite3.SQLITE_DROP_VIEW, sqlite3.SQLITE_CREATE_TRIGGER,
}


class UnsafeQueryError(ValueError):
    pass


def _authorizer(action, *_):
    return sqlite3.SQLITE_DENY if action in _DENIED else sqlite3.SQLITE_OK


def validate(sql: str) -> str:
    """Aceita apenas uma instrução SELECT/WITH."""
    sql = sql.strip().rstrip(";").strip()
    if not sql:
        raise UnsafeQueryError("Consulta vazia.")
    if ";" in sql:
        raise UnsafeQueryError("Envie apenas uma instrução SQL por vez.")
    if sql.split(None, 1)[0].upper() not in {"SELECT", "WITH"}:
        raise UnsafeQueryError("Apenas consultas de leitura (SELECT/WITH) são permitidas.")
    return sql


def connect() -> sqlite3.Connection:
    if not config.DB_PATH.exists():
        raise FileNotFoundError(f"Banco não encontrado: {config.DB_PATH}")
    # Defesa em profundidade: arquivo aberto como read-only + query_only + authorizer
    conn = sqlite3.connect(f"file:{config.DB_PATH.resolve().as_posix()}?mode=ro", uri=True)
    conn.execute("PRAGMA query_only = ON")
    conn.set_authorizer(_authorizer)
    return conn


def run_query(sql: str) -> dict:
    sql = validate(sql)
    conn = connect()
    deadline = time.monotonic() + config.QUERY_TIMEOUT_S
    conn.set_progress_handler(lambda: 1 if time.monotonic() > deadline else 0, 100_000)
    try:
        cur = conn.execute(sql)
        cols = [d[0] for d in cur.description or []]
        rows = cur.fetchmany(config.MAX_ROWS + 1)
    finally:
        conn.close()
    truncated = len(rows) > config.MAX_ROWS
    return {"columns": cols, "rows": [list(r) for r in rows[: config.MAX_ROWS]], "truncated": truncated}


def current_year() -> int:
    return datetime.now().year
