# CineData Analytics — Agente Text-to-SQL

Agente que permite a pessoas **sem conhecimento de SQL** fazer perguntas em português sobre o catálogo de filmes da CineData e receber respostas baseadas em dados reais.

Ele é construído com o framework **[Strands Agents](https://strandsagents.com)** e usa modelos **gratuitos** do **[OpenRouter](https://openrouter.ai)**. Os dados vêm da camada Gold (modelo dimensional) em um banco **SQLite**, acessado somente para leitura.

> Exemplo: `"Qual produtora teve o maior lucro total?"` → o agente escreve o SQL, executa no banco e responde em linguagem natural.

---

## Sumário

1. [Como funciona](#1-como-funciona)
2. [Pré-requisitos](#2-pré-requisitos)
3. [Passo a passo para executar](#3-passo-a-passo-para-executar)
4. [Exemplos de perguntas](#4-exemplos-de-perguntas)
5. [Avaliação do agente](#5-avaliação-do-agente)
6. [Estrutura do projeto](#6-estrutura-do-projeto)
7. [Limites do OpenRouter (cota gratuita)](#7-limites-do-openrouter-cota-gratuita)
8. [Problemas comuns](#8-problemas-comuns)
9. [Decisões de projeto](#9-decisões-de-projeto)

---

## 1. Como funciona

```
 Pergunta do usuário
        │
        ▼
 ┌───────────────┐   system prompt com esquema do banco
 │ Strands Agent │◄── e regras de negócio (prompts.py)
 └───────┬───────┘
         │ o modelo decide chamar a ferramenta
         ▼
 ┌───────────────┐   valida o SQL (só SELECT) e executa
 │ tool: run_sql │──► SQLite somente leitura (cinerocket.db)
 └───────┬───────┘
         │ linhas retornadas (ou mensagem de erro para o modelo corrigir)
         ▼
 Resposta em português, com os critérios usados
```

Em resumo: o **modelo** traduz a pergunta em SQL, a **ferramenta `run_sql`** executa a consulta com segurança, e o modelo **explica o resultado**. Se o SQL der erro, o erro volta ao modelo, que corrige e tenta de novo.

## 2. Pré-requisitos

| O que | Para quê | Como conferir |
|---|---|---|
| **Python 3.10 ou superior** | rodar o projeto | `python --version` |
| **Git** | baixar o projeto | `git --version` |
| **Arquivo `cinerocket.db`** | dados da camada Gold (fornecido na pasta compartilhada da atividade, dentro do `cinerocket-db.zip`) | ~580 MB depois de descompactado |
| **Conta no OpenRouter** | chave de API para usar os modelos gratuitos | gratuita, sem cartão |

## 3. Passo a passo para executar

Os comandos abaixo funcionam no Windows (PowerShell/CMD). Em Linux/macOS, as diferenças estão indicadas.

### Passo 1 — Baixar o projeto

```bash
git clone https://github.com/ellencaroliny/rocketlab-genai.git
cd rocketlab-genai
```

### Passo 2 — Criar e ativar um ambiente virtual

O ambiente virtual isola as dependências do projeto das demais instalações do Python.

```bash
python -m venv .venv
```

Ativar:

```bash
# Windows (PowerShell ou CMD)
.venv\Scripts\activate

# Linux / macOS / Git Bash
source .venv/bin/activate
```

Quando ativo, o terminal mostra `(.venv)` no início da linha.

### Passo 3 — Instalar as dependências

```bash
pip install -r requirements.txt
```

Isso instala o `strands-agents` (com suporte a modelos compatíveis com a API da OpenAI, como o OpenRouter) e o `python-dotenv` (leitura do arquivo `.env`).

### Passo 4 — Colocar o banco de dados na pasta do projeto

1. Descompacte o `cinerocket-db.zip`.
2. Copie o arquivo `.db` para a raiz do projeto (a mesma pasta deste README).
3. Renomeie-o para **`cinerocket.db`**.

> O banco não está no repositório por ser muito grande (~580 MB). Se preferir deixá-lo em outro lugar, informe o caminho em `CINEROCKET_DB` no `.env` (Passo 5).

### Passo 5 — Criar a chave do OpenRouter e configurar o `.env`

1. Acesse <https://openrouter.ai> e crie uma conta (Google, GitHub ou e-mail).
2. Vá em <https://openrouter.ai/keys>, clique em **Create Key** e copie a chave (começa com `sk-or-v1-`). Ela só é exibida uma vez.
3. Crie o seu arquivo de configuração a partir do modelo:

```bash
# Windows (CMD/PowerShell)
copy .env.example .env

# Linux / macOS / Git Bash
cp .env.example .env
```

4. Abra o `.env` e substitua `sk-or-v1-SUA_CHAVE` pela sua chave:

```env
OPENROUTER_API_KEY=sk-or-v1-...sua-chave...
OPENROUTER_MODELS=openrouter/free,nvidia/nemotron-3.5-lightning:free,z-ai/glm-5.2:free,google/gemma-4-26b-a4b-it:free
CINEROCKET_DB=cinerocket.db
```

| Variável | Significado |
|---|---|
| `OPENROUTER_API_KEY` | sua chave de API. **Nunca** a envie para o GitHub (o `.env` já está no `.gitignore`). |
| `OPENROUTER_MODELS` | lista de modelos **gratuitos** separados por vírgula. O primeiro é o principal; se ele falhar (ex.: erro 429), o agente passa automaticamente para o próximo. |
| `CINEROCKET_DB` | caminho do arquivo SQLite. |

### Passo 6 — Fazer uma pergunta

**Pergunta única** (imprime a resposta e encerra):

```bash
python -m cinedata_agent "Top 10 filmes com maior receita em R$"
```

**Modo interativo** (conversa contínua, o agente lembra das perguntas anteriores):

```bash
python -m cinedata_agent
```

```
> Quais são os 5 filmes mais populares?
...resposta...
> E qual deles tem a maior receita?     <- o agente entende "deles" pelo contexto
```

Para sair, deixe a linha vazia e tecle Enter, ou digite `sair`.

## 4. Exemplos de perguntas

| Categoria | Exemplos |
|---|---|
| Bilheteria e finanças | Top 10 filmes com maior receita em R$ · Lucro médio por gênero (só filmes com receita informada) · Filmes com maior margem de lucro |
| Popularidade | Os 5 filmes mais populares · Maior divergência entre nota TMDB e IMDb · Nota média IMDb por ano |
| Elenco e equipe | Ator com mais filmes nos últimos 5 anos · Diretores com maior nota média (mín. 5 filmes) · Dupla ator–diretor que mais trabalhou junta |
| Gêneros e produtoras | Quantidade de filmes por gênero · Produtora com maior lucro total · Gênero com maior margem média |
| Avaliações dos usuários | Filmes mais avaliados pelos usuários · Filmes em que a nota dos usuários mais diverge da nota IMDb |

> A consulta da **dupla ator–diretor** é pesada e pode levar algumas dezenas de segundos.

## 5. Avaliação do agente

O módulo `evaluate.py` contém perguntas com **SQL de referência**. Compara o primeiro item esperado com o que o agente respondeu.

```bash
# Só valida o SQL de referência no banco. NÃO usa o OpenRouter (não gasta cota).
python -m cinedata_agent.evaluate --offline

# Pergunta de verdade ao agente (gasta cota!). Use --limit para controlar quantas.
python -m cinedata_agent.evaluate --limit 3
```

## 6. Estrutura do projeto

```
.
├── cinedata_agent/
│   ├── agent.py       # agente Strands (OpenRouter), memória de conversa e fallback entre modelos
│   ├── prompts.py     # system prompt: esquema do banco + regras de negócio
│   ├── tools.py       # ferramenta run_sql exposta ao modelo
│   ├── database.py    # conexão somente leitura e validação do SQL (guardrails)
│   ├── config.py      # leitura do .env (chave, modelos, caminho do banco, limites)
│   ├── cli.py         # interface de linha de comando (pergunta única / interativo)
│   ├── evaluate.py    # conjunto de perguntas com SQL de referência
│   └── __main__.py    # permite executar com `python -m cinedata_agent`
├── .env.example       # modelo do arquivo de configuração
├── requirements.txt   # dependências
└── README.md
```

## 7. Limites do OpenRouter (cota gratuita)

- Contas sem crédito: **20 requisições/minuto** e **50/dia** nos modelos `:free`.
- **Cada pergunta usa 2 ou mais chamadas** (uma para gerar o SQL e outra para redigir a resposta; mais, se o SQL precisar de correção). Ou seja, dá para fazer cerca de 15–25 perguntas por dia.
- Requisições que falham **também contam** na cota. Por isso o agente **não repete** a chamada no mesmo modelo: ele troca para o próximo da lista.
- O contador zera à meia-noite UTC (**21h no horário de Brasília**). Consulte o uso em <https://openrouter.ai/activity>.

## 8. Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `Defina OPENROUTER_API_KEY no .env` | `.env` ausente ou sem a chave | Refaça o Passo 5. Execute o comando na pasta onde está o `.env`. |
| `Banco não encontrado: cinerocket.db` | banco fora da pasta ou com outro nome | Refaça o Passo 4 ou ajuste `CINEROCKET_DB`. |
| `ModuleNotFoundError: strands` | dependências não instaladas ou ambiente não ativado | Ative o `.venv` (Passo 2) e rode `pip install -r requirements.txt`. |
| `401` | chave inválida | Confirme que a chave começa com `sk-or-v1-` e sem espaços. |
| `429` | modelo gratuito lotado ou cota do dia esgotada | O agente tenta o próximo modelo sozinho. Se todos falharem, aguarde ou consulte a cota (seção 7). |
| `Todos os modelos falharam` | todos os modelos da lista indisponíveis | Troque os modelos em `OPENROUTER_MODELS` (veja <https://openrouter.ai/models?q=:free>). |
| `interrupted` em uma consulta | consulta passou do limite de tempo (90 s) | Reformule a pergunta de forma mais específica. |
| Aviso `reasoningContent is not supported...` | aviso do Strands com modelos que "raciocinam" | Pode ser ignorado; não afeta a resposta. |

## 9. Decisões de projeto

- **Segurança (guardrails).** O agente nunca altera dados. Há quatro camadas: (1) só aceita `SELECT`/`WITH`, uma instrução por vez; (2) o arquivo é aberto em modo somente leitura (`mode=ro`); (3) `PRAGMA query_only`; (4) um *authorizer* do SQLite nega qualquer operação de escrita, `PRAGMA`, `ATTACH`, etc. Há ainda limite de 100 linhas por consulta e timeout.
- **Regras de negócio no prompt.** Nos dados, `lucro_usd`/`lucro_brl` valem `0` quando a receita não foi informada (e não lucro real); por isso, análises de lucro filtram `receita > 0`. Também estão descritos: gêneros em inglês, filmes futuros no catálogo (até 2029), e "receita = faturamento = bilheteria".
- **Respostas transparentes.** O agente informa os critérios assumidos (ex.: "considerei apenas filmes com receita informada").
- **Fallback entre modelos.** Modelos gratuitos ficam lotados com frequência; trocar de modelo é mais barato para a cota do que repetir a chamada.
- **Memória de conversa.** O modo interativo mantém o histórico para perguntas de acompanhamento.
