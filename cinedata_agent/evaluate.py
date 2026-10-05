"""Avaliação: perguntas com SQL de referência.

Modos:
  python -m cinedata_agent.evaluate --offline   valida o SQL de referência (não gasta cota do OpenRouter)
  python -m cinedata_agent.evaluate --limit 3   pergunta ao agente e confere se o item esperado aparece na resposta
"""
import argparse
import sys

from . import database

# (pergunta, SQL de referência, índice da coluna que deve aparecer na resposta do agente)
CASES = [
    (
        "Top 10 filmes com maior receita em R$",
        "SELECT m.titulo, f.receita_brl FROM dim_movies m JOIN fact_movies_performance f USING (sk_movie_id) "
        "WHERE f.receita_brl > 0 ORDER BY f.receita_brl DESC LIMIT 10",
        0,
    ),
    (
        "Quais são os 5 filmes mais populares?",
        "SELECT m.titulo, f.popularidade FROM dim_movies m JOIN fact_movies_performance f USING (sk_movie_id) "
        "WHERE f.popularidade IS NOT NULL ORDER BY f.popularidade DESC LIMIT 5",
        0,
    ),
    (
        "Quantos filmes existem por gênero?",
        "SELECT g.nome_genero, COUNT(DISTINCT b.sk_movie_id) n FROM bridge_movie_genre b "
        "JOIN dim_genres g USING (sk_genre_id) GROUP BY 1 ORDER BY n DESC",
        0,
    ),
    (
        "Qual produtora teve o maior lucro total?",
        "SELECT c.nome_produtora, SUM(f.lucro_usd) lucro FROM bridge_movie_company b "
        "JOIN dim_companies c USING (sk_company_id) JOIN fact_movies_performance f USING (sk_movie_id) "
        "WHERE f.receita_usd > 0 AND f.orcamento_usd > 0 GROUP BY 1 ORDER BY lucro DESC LIMIT 1",
        0,
    ),
    (
        "Quais são os filmes mais avaliados pelos usuários?",
        "SELECT m.titulo, r.qtd_avaliacoes_usuarios FROM dim_reviews r JOIN dim_movies m USING (sk_movie_id) "
        "ORDER BY r.qtd_avaliacoes_usuarios DESC LIMIT 5",
        0,
    ),
]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("--offline", action="store_true", help="só executa o SQL de referência")
    p.add_argument("--limit", type=int, default=len(CASES), help="nº de perguntas a enviar ao agente")
    args = p.parse_args()

    agent = None
    if not args.offline:
        from .agent import CineDataAgent
        agent = CineDataAgent()

    hits = 0
    cases = CASES if args.offline else CASES[: args.limit]
    for question, sql, col in cases:
        ref = database.run_query(sql)
        expected = str(ref["rows"][0][col])
        print(f"\n# {question}\n  referência: {expected}")
        if agent:
            # Memória zerada a cada caso para que um não contamine o outro
            agent.agent.messages.clear()
            ok = expected.lower() in agent.ask(question).lower()
            hits += ok
            print(f"  agente: {'OK' if ok else 'DIVERGIU'}")
    if agent:
        print(f"\nAcertos: {hits}/{len(cases)}")


if __name__ == "__main__":
    main()
