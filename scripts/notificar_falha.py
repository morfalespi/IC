import json
import os
from pathlib import Path
from bot_api import BotClient, diagnostico_excecao


def principal():
    if not os.environ.get('CHAT_ID') or (Path(os.environ.get('RUNNER_TEMP', '/tmp')) / 'notificado').exists():
        return 0
    # The workflow invokes this only on failure; never declare collection complete.
    try:
        BotClient().send_message(os.environ['CHAT_ID'], 'IC operation failed or was interrupted. Check the run diagnostics.')
        return 0
    except Exception as error:
        print(json.dumps(diagnostico_excecao(error)))
        return 1


if __name__ == '__main__':

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
