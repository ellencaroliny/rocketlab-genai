import sqlite3

from strands import tool

from . import database


@tool
def run_sql(query: str) -> str:
    """Executa uma consulta SQL de LEITURA (SQLite) na camada Gold do CineData e devolve as linhas.

    Args:
        query: Uma única instrução SELECT (ou WITH ... SELECT) em dialeto SQLite.
    """
    try:
        res = database.run_query(query)
    except (database.UnsafeQueryError, sqlite3.Error, FileNotFoundError) as e:
        # Devolve o erro ao modelo para que ele corrija a consulta
        return f"ERRO: {e}"
    if not res["rows"]:
        return "Consulta executada com sucesso, mas não retornou linhas."
    lines = [" | ".join(res["columns"])]
    lines += [" | ".join("NULL" if v is None else str(v) for v in r) for r in res["rows"]]
    if res["truncated"]:
        lines.append(f"(resultado truncado em {len(res['rows'])} linhas; use LIMIT/agregações)")
    return "\n".join(lines)
