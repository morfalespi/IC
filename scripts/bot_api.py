import json
import os
import re
import time
import urllib.error
import urllib.request
import traceback
from pathlib import Path

from telegram_ids import tipo_dialogo


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
    runner_temp = os.environ.get("RUNNER_TEMP")
    if runner_temp:
        try:
            (Path(runner_temp) / "bot_api_auth_failed").touch()
        except OSError as erro:
            print(json.dumps({"origin": "local", "operation": "record_bot_api_auth_failure",
                              "type": type(erro).__name__}, ensure_ascii=False))
    raise BotAPIAuthenticationError(metodo, resposta)


def chamar(metodo, corpo, cabecalhos):
    migracoes = []
    while True:
        pedido = urllib.request.Request(
            f"https://api.telegram.org/bot{os.environ['BOT_TOKEN']}/{metodo}",
            data=corpo, headers=cabecalhos,
        )
        try:
            with urllib.request.urlopen(pedido, timeout=30) as resposta:
                codigo, bruto = resposta.status, resposta.read()
        except urllib.error.HTTPError as erro:
            codigo, bruto = erro.code, erro.read()
        except (urllib.error.URLError, OSError) as erro:
            return {"ok": False, "error_code": 0, "description": type(erro).__name__, "origin": "transport"}
        try:
            retorno = json.loads(bruto)
        except ValueError:
            retorno = None
        if codigo == 401:
            if not (isinstance(retorno, dict) and retorno.get("ok") is False
                    and retorno.get("error_code") == 401):
                retorno = {"ok": False, "error_code": 401,
                           "description": "HTTP 401: autenticação recusada; corpo sem erro Bot API correspondente",
                           "origin": "http"}
            recusar_autenticacao(metodo, retorno)
        if (not isinstance(retorno, dict) or type(retorno.get("ok")) is not bool
                or (retorno["ok"] and "result" not in retorno)):
            return {"ok": False, "error_code": codigo, "description": "Resposta inválida da Bot API", "origin": "protocol"}
        if retorno["ok"] and not 200 <= codigo < 300:
            return {"ok": False, "error_code": codigo, "description": "Status HTTP de erro incompatível com envelope de sucesso", "origin": "protocol"}
        if migracoes:
            retorno["migrations"] = list(migracoes)
        if retorno["ok"]:
            return retorno
        if codigo == 401 or retorno.get("error_code") == 401:
            recusar_autenticacao(metodo, retorno)
        parametros = retorno.get("parameters")
        parametros = parametros if isinstance(parametros, dict) else {}
        espera = parametros.get("retry_after")
        if type(espera) is int and espera >= 0:
            print("Bot API:", metodo, "aguardando retry_after", espera, "s")
            time.sleep(espera)
            continue
        destino = parametros.get("migrate_to_chat_id")
        if type(destino) is int and tipo_dialogo(destino) == "channel":
            tipo = cabecalhos.get("Content-Type", "")
            origem = None
            novo_corpo = None
            if tipo == "application/json":
                carga = json.loads(corpo)
                origem = carga.get("chat_id") if isinstance(carga, dict) else None
                if tipo_dialogo(str(origem)) == "chat":
                    carga["chat_id"] = destino
                    novo_corpo = json.dumps(carga, ensure_ascii=False).encode("utf-8")
            elif tipo.startswith("multipart/form-data;"):
                campo = re.compile(rb'(Content-Disposition: form-data; name="chat_id"\r\n\r\n)(-?[0-9]+)(\r\n)')
                encontrado = campo.search(corpo)
                origem = int(encontrado[2]) if encontrado else None
                if tipo_dialogo(origem) == "chat":
                    novo_corpo = campo.sub(lambda m: m[1] + str(destino).encode() + m[3], corpo, count=1)
            if novo_corpo is not None and destino not in [m["to"] for m in migracoes]:
                migracoes.append({"from": origem, "to": destino})
                corpo = novo_corpo
                continue
        return retorno



def diagnostico_api(resposta, metodo):
    descricao = str(resposta.get("description", "Falha sem descrição"))
    for nome in ("BOT_TOKEN", "API_HASH", "GH_DISPATCH_TOKEN", "TGCLOUD_TOKEN"):
        segredo = os.environ.get(nome)
        if segredo:
            descricao = descricao.replace(segredo, "[redigido]")
    descricao = re.sub(r"(?:bot)?[0-9]+:[A-Za-z0-9_-]+", "[redigido]", descricao)
    parametros = resposta.get("parameters")
    parametros = parametros if isinstance(parametros, dict) else {}
    return {"method": metodo, "error_code": resposta.get("error_code"),
            "description": descricao, "origin": resposta.get("origin", "telegram"),
            "parameters": {k: v for k, v in parametros.items()
                           if k in ("retry_after", "migrate_to_chat_id") and type(v) is int}}


def diagnostico_excecao(erro):
    if isinstance(erro, APIError):
        return erro.diagnostic
    dados = diagnostico_api({"error_code": getattr(erro, "code", 0),
                            "description": getattr(erro, "message", type(erro).__name__)}, "MTProto/runtime")
    dados["type"] = type(erro).__name__
    dados["stack"] = [{"file": os.path.basename(frame.filename), "line": frame.lineno,
                       "function": frame.name} for frame in traceback.extract_tb(erro.__traceback__)]
    return dados


def estado_mensagem(resposta, chat_id=None):
    if isinstance(resposta, dict) and resposta.get("ok") is False:
        return "rejected"
    mensagem = resposta.get("result") if isinstance(resposta, dict) else None
    identificador = mensagem.get("message_id") if isinstance(mensagem, dict) else None
    chat = mensagem.get("chat") if isinstance(mensagem, dict) else None
    destino = chat.get("id") if isinstance(chat, dict) else None
    data = mensagem.get("date") if isinstance(mensagem, dict) else None
    tipo = chat.get("type") if isinstance(chat, dict) else None
    tipos = {"user": ("private",), "chat": ("group",), "channel": ("supergroup", "channel")}
    if (not isinstance(resposta, dict) or resposta.get("ok") is not True
            or type(identificador) is not int or identificador < 0
            or type(destino) is not int or tipo not in tipos.get(tipo_dialogo(destino), ())
            or type(data) is not int):
        raise APIProtocolError("Message", {"error_code": 0, "origin": "protocol",
                                          "description": "Resposta sem Message com identificador e chat válidos"})
    if chat_id is not None:
        esperado = int(chat_id)
        for migracao in resposta.get("migrations", []):
            if str(migracao.get("from")) != str(esperado):
                raise APIProtocolError("Message", {"error_code": 0, "origin": "protocol",
                                                   "description": "Cadeia de migração divergente do chat solicitado"})
            esperado = migracao["to"]
        if destino != esperado:
            raise APIProtocolError("Message", {"error_code": 0, "origin": "protocol",
                                               "description": "Message retornou chat diferente do destino solicitado"})
    return "pending" if identificador == 0 or data == 0 else "confirmed"


def registrar_notificacao(resposta, chat_id):
    estado = estado_mensagem(resposta, chat_id)
    if estado == "rejected":
        raise BotAPIRequestError("sendMessage", resposta)
    pasta = Path(os.environ.get("RUNNER_TEMP", "/tmp"))
    if estado == "confirmed":
        (pasta / "notificado").touch()
        (pasta / "notificacao_pendente").unlink(missing_ok=True)
    else:
        (pasta / "notificacao_pendente").touch()
    return estado
