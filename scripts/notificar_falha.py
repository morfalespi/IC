import json
import os

from bot_api import chamar, diagnostico_api, registrar_notificacao


def principal():
    chat = os.environ.get("CHAT_ID", "")
    carga = {"chat_id": chat, "text": "Processamento concluído. Execução: " + os.environ.get("RUN_URL", "")}
    resposta = chamar("sendMessage", json.dumps(carga).encode(), {"Content-Type": "application/json"})
    print(json.dumps(diagnostico_api(resposta, "sendMessage"), ensure_ascii=False))
    registrar_notificacao(resposta, chat)
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
