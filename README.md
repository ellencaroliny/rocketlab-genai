# CineData Analytics — Agente Text-to-SQL

Agente de linguagem natural sobre a camada Gold do CineData (SQLite), construído com
**[Strands Agents](https://strandsagents.com)** e modelos gratuitos do **OpenRouter**.

## Como funciona

```
pergunta ─► Strands Agent ─► tool run_sql ─► SQLite (somente leitura) ─► resposta em português
              (system prompt com esquema + regras de negócio)
```

- `cinedata_agent/agent.py` — agente Strands (`OpenAIModel` apontando para o OpenRouter), memória de conversa e **fallback** entre modelos gratuitos (sem retry no mesmo modelo, pois falhas também gastam a cota diária).
- `cinedata_agent/prompts.py` — esquema e regras de negócio. Ex.: `lucro_*` vale 0 quando a receita não é informada, então análises de lucro filtram `receita > 0`.
- `cinedata_agent/tools.py` — a única ferramenta, `run_sql`; erros voltam ao modelo para ele corrigir a consulta.
- `cinedata_agent/database.py` — **guardrails**: só `SELECT`/`WITH`, uma instrução por vez, conexão `mode=ro` + `query_only` + *authorizer* do SQLite, limite de 100 linhas e timeout.
- `cinedata_agent/evaluate.py` — conjunto de perguntas com SQL de referência.

## Passo a passo

1. **Python 3.10+** e dependências:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Banco**: coloque `cinerocket.db` (descompactado do `cinerocket-db.zip`) na raiz do projeto.
3. **Chave do OpenRouter**: crie em <https://openrouter.ai/keys> e configure:
   ```bash
   copy .env.example .env        # Linux/macOS: cp .env.example .env
   ```
   Edite `.env` e preencha `OPENROUTER_API_KEY`.
4. **Execute**:
   ```bash
   python -m cinedata_agent "Top 10 filmes com maior receita em R$"   # pergunta única
   python -m cinedata_agent                                           # modo interativo (com memória)
   ```
5. **Avaliação**:
   ```bash
   python -m cinedata_agent.evaluate --offline   # valida o SQL de referência, sem gastar cota
   python -m cinedata_agent.evaluate --limit 3   # testa o agente (≈ 2+ requisições por pergunta)
   ```

## Cota do OpenRouter

Contas gratuitas têm 50 requisições/dia nos modelos `:free` (reset às 21h BRT) e cada pergunta usa
2 ou mais chamadas (gerar SQL + responder). Teste poucas perguntas por vez. Um `429` aciona o próximo modelo de `OPENROUTER_MODELS`.

## Observações sobre os dados

- Receita/orçamento são `NULL` quando não informados; `lucro_*` fica `0` nesses casos.
- Gêneros estão em inglês (`Action`, `Science Fiction`...); a resposta do agente é em português.
- O catálogo inclui filmes até 2029 (ainda não lançados); "últimos 5 anos" considera só `status_filme = 'Lançado'`.
