import json
import os
import re
import time
import urllib.error
import urllib.request
import traceback

from telegram_ids import tipo_dialogo


class BotAPIRequestError(RuntimeError):
    def __init__(self, metodo, resposta):
        self.diagnostic = diagnostico_api(resposta, metodo)
        super().__init__(json.dumps(self.diagnostic, ensure_ascii=False))


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
        if (not isinstance(retorno, dict) or type(retorno.get("ok")) is not bool
                or (retorno["ok"] and "result" not in retorno)):
            return {"ok": False, "error_code": codigo, "description": "Resposta inválida da Bot API", "origin": "protocol"}
        if migracoes:
            retorno["migrations"] = list(migracoes)
        if retorno["ok"]:
            return retorno
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
    if isinstance(erro, BotAPIRequestError):
        return erro.diagnostic
    dados = diagnostico_api({"error_code": getattr(erro, "code", 0),
                            "description": getattr(erro, "message", type(erro).__name__)}, "MTProto/runtime")
    dados["type"] = type(erro).__name__
    dados["stack"] = [{"file": os.path.basename(frame.filename), "line": frame.lineno,
                       "function": frame.name} for frame in traceback.extract_tb(erro.__traceback__)]
    return dados
