import asyncio
import json
import os
from pathlib import Path
import sys

from resolver import chamar, coletar, id_peer, registros_telegram
from bot_api import BotAPIRequestError, diagnostico_excecao
from exportacao import CHAVES_NORMALIZADAS
import re


async def principal():
    if os.environ.get("CHAT_ID") or os.environ.get("MESSAGE_ID") or os.environ.get("MODO") != "resumo":
        raise ValueError("A validação exige modo resumo sem chat ou mensagem de destino.")
    headers = {"Content-Type": "application/json"}
    me = await asyncio.to_thread(chamar, "getMe", b"{}", headers)
    if not me.get("ok"):
        raise BotAPIRequestError("getMe", me)
    bot = me.get("result")
    if not me.get("ok") or not isinstance(bot, dict) or bot.get("is_bot") is not True:
        raise RuntimeError("getMe não confirmou uma conta de bot.")
    print("Bot API getMe: identidade do bot confirmada", flush=True)
    response = await asyncio.to_thread(
        chamar, "getChat", json.dumps({"chat_id": "@telegram"}).encode(), headers
    )
    chat = response.get("result")
    if not response.get("ok"):
        raise BotAPIRequestError("getChat", response)
    if (not response.get("ok") or not isinstance(chat, dict)
            or type(chat.get("id")) is not int or chat.get("type") != "channel"):
        raise RuntimeError("getChat não confirmou o canal público de validação.")
    print("Bot API getChat: canal público lido", flush=True)
    dados = await coletar(str(chat["id"]))
    if id_peer(dados["entidade"]) != chat["id"]:
        raise RuntimeError("Bot API e MTProto retornaram entidades diferentes.")
    if dados["completo"] is None or dados["falhas_coleta"]:
        raise RuntimeError("A leitura do perfil completo MTProto não foi confirmada.")
    print("Bot API e MTProto via Telethon: mesmo canal e perfil completo confirmados", flush=True)
    protegidos = 0
    for registro in registros_telegram(dados, "telegram", {"tipo": "canal"}):
        chave = re.sub(r"[^a-z0-9]", "", registro["path"].rsplit(".", 1)[-1].lower())
        if chave in CHAVES_NORMALIZADAS:
            if registro["value"] != "[redigido]":
                raise RuntimeError("Exportação preservou um campo de autenticação")
            protegidos += 1
    if protegidos == 0:
        raise RuntimeError("A consulta não forneceu campos para validar a redação na exportação real")
    print("Exportação das respostas reais: campos de autenticação redigidos", flush=True)
    if os.environ.get("RUNNER_TEMP"):
        caminho = Path(os.environ["RUNNER_TEMP"]) / "telegram_validation.json"
        caminho.write_text(json.dumps({"bot_id": bot["id"], "chat_id": chat["id"]}))
        caminho.chmod(0o600)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(principal()))
    except Exception as erro:
        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False), flush=True)
        sys.exit(1)
