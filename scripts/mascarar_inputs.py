import json
import os
from pathlib import Path


def principal():
    evento = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    entradas = evento.get("inputs") or {}
    for chave in ("alvo", "expected_id", "chat", "message_id", "origem_id"):
        valor = str(entradas.get(chave) or "")
        if valor:
            escapado = valor.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
            print("::add-mask::" + escapado, flush=True)
    print("Máscaras dos dados de consulta registradas antes de executar o resolver")
    if entradas.get("modo") == "validar_entrega" and str(entradas.get("validar_apis", "")).lower() == "true":
        raise ValueError("Escolha validação de leitura ou de entrega; as rotas não podem ser combinadas")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
