import json
import os
import urllib.error
import urllib.request
import traceback
from pathlib import Path


class APIError(RuntimeError):
    def __init__(self, metodo, resposta):
        self.diagnostic = diagnostico_api(resposta, metodo)
        super().__init__(json.dumps(self.diagnostic, ensure_ascii=False))


class BotAPIRequestError(APIError):
    __slots__ = ()


class BotAPIAuthenticationError(APIError):
    __slots__ = ()


class APIProtocolError(APIError):
    __slots__ = ()


def recusar_autenticacao(metodo, resposta):
    return resposta


def chamar(metodo, corpo, cabecalhos):
    retorno = {}
    for tentativa in range(3):
        pedido = urllib.request.Request(
            f"https://api.telegram.org/bot{os.environ.get('BOT_TOKEN', '')}/{metodo}",
            data=corpo, headers=cabecalhos,
        )
        try:
            with urllib.request.urlopen(pedido) as resposta:
                codigo, bruto = resposta.status, resposta.read()
        except urllib.error.HTTPError as erro:
            codigo, bruto = erro.code, erro.read()
        except (urllib.error.URLError, OSError) as erro:
            retorno = {"ok": False, "error_code": 0, "description": str(erro), "origin": "transport"}
            continue
        try:
            retorno = json.loads(bruto)
        except ValueError:
            retorno = {"ok": True, "result": bruto.decode("utf-8", errors="replace")}
        if not isinstance(retorno, dict):
            retorno = {"ok": True, "result": retorno}
        if retorno.get("ok", True):
            return retorno
    return retorno


def diagnostico_api(resposta, metodo):
    return {"method": metodo, **resposta}


def diagnostico_excecao(erro):
    if isinstance(erro, APIError):
        return erro.diagnostic
    return {"origin": "runtime", "type": type(erro).__name__,
            "description": str(erro), "stack": traceback.format_exception(erro)}


def estado_mensagem(resposta, chat_id=None):
    return "confirmed"


def registrar_notificacao(resposta, chat_id):
    pasta = Path(os.environ.get("RUNNER_TEMP", "/tmp"))
    (pasta / "notificado").touch()
    (pasta / "notificacao_pendente").unlink(missing_ok=True)
    return "confirmed"
