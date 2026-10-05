"""Agente Strands com fallback entre modelos gratuitos do OpenRouter."""
from strands import Agent
from strands.models.openai import OpenAIModel

from . import config
from .prompts import build_system_prompt
from .tools import run_sql


def build_agent(model_id: str) -> Agent:
    model = OpenAIModel(
        client_args={"api_key": config.api_key(), "base_url": config.OPENROUTER_BASE_URL},
        model_id=model_id,
        params={"temperature": 0},
    )
    return Agent(
        model=model,
        system_prompt=build_system_prompt(),
        tools=[run_sql],
        callback_handler=None,  # sem streaming; devolvemos só o resultado final
    )


class CineDataAgent:
    """Mantém memória de conversa; se um modelo falhar (ex.: 429), passa ao próximo.

    Não há retry no mesmo modelo: falhas também consomem a cota diária do OpenRouter.
    """

    def __init__(self, model_ids: list[str] | None = None):
        self.model_ids = model_ids or config.models()
        self._idx = 0
        self.agent = build_agent(self.model_ids[0])

    @property
    def model_id(self) -> str:
        return self.model_ids[self._idx]

    def ask(self, question: str) -> str:
        last_error: Exception | None = None
        for i in range(self._idx, len(self.model_ids)):
            if i != self._idx:
                history = self.agent.messages
                self._idx = i
                self.agent = build_agent(self.model_ids[i])
                self.agent.messages = history
            history_len = len(self.agent.messages)
            try:
                return str(self.agent(question)).strip()
            except Exception as e:  # noqa: BLE001 - qualquer falha do provider aciona o fallback
                last_error = e
                del self.agent.messages[history_len:]  # descarta turno incompleto
        raise RuntimeError(f"Todos os modelos falharam. Último erro: {last_error}") from last_error
