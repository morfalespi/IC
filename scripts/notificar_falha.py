import json
import os
from pathlib import Path

from bot_api import chamar, diagnostico_api, diagnostico_excecao
from telegram_ids import tipo_dialogo


def principal():
    marcador = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "notificado"
    chat = os.environ.get("CHAT_ID", "").strip()
    if marcador.exists():
        print("Notificação já confirmada nesta execução; nenhum reenvio solicitado")
        return 0
    if not chat:
        print("Notificação não solicitada: execução sem chat de destino")
        return 0
    if not os.environ.get("BOT_TOKEN"):
        print("Notificação não enviada: BOT_TOKEN ausente")
        return 1
    if (marcador.parent / "bot_api_auth_failed").exists():
        print("Notificação não enviada: autenticação Bot API recusada nesta execução")
        return 1
    if tipo_dialogo(chat) is None:
        print("Notificação: CHAT_ID fora dos intervalos oficiais de peers")
        return 1
    carga = {"chat_id": int(chat), "text": "A busca falhou antes de confirmar a entrega. Execução: " + os.environ.get("RUN_URL", "")}
    resposta = chamar("sendMessage", json.dumps(carga).encode(), {"Content-Type": "application/json"})
    if not resposta.get("ok"):
        print(json.dumps(diagnostico_api(resposta, "sendMessage"), ensure_ascii=False))
        return 1
    mensagem = resposta.get("result")
    identificador = mensagem.get("message_id") if isinstance(mensagem, dict) else None
    if type(identificador) is not int or identificador <= 0:
        print("Notificação aceita sem mensagem editável; entrega pendente")
        return 1
    marcador.touch()
    print("Notificação de falha confirmada pelo Telegram")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(principal())
    except Exception as erro:
        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
        raise SystemExit(1)
