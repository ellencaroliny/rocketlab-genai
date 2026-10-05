import argparse
import sys

from .agent import CineDataAgent


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="CineData Analytics - pergunte em linguagem natural.")
    p.add_argument("pergunta", nargs="?", help="Pergunta única. Sem ela, abre o modo interativo.")
    args = p.parse_args()

    agent = CineDataAgent()
    if args.pergunta:
        print(agent.ask(args.pergunta))
        return

    print("CineData Analytics - digite sua pergunta (vazio ou 'sair' encerra).")
    while True:
        try:
            q = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q or q.lower() in {"sair", "exit", "quit"}:
            break
        try:
            print(f"\n{agent.ask(q)}\n[modelo: {agent.model_id}]")
        except Exception as e:  # noqa: BLE001
            print(f"Erro: {e}")


if __name__ == "__main__":
    main()
