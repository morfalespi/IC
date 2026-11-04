import asyncio
import json
import os
import sys

from resolver import chamar, coletar, id_peer


async def principal():
    if os.environ.get("CHAT_ID") or os.environ.get("MESSAGE_ID") or os.environ.get("MODO") != "resumo":
        raise ValueError("A validação exige modo resumo sem chat ou mensagem de destino.")
    headers = {"Content-Type": "application/json"}
    me = await asyncio.to_thread(chamar, "getMe", b"{}", headers, True)
    bot = me.get("result")
    if not me.get("ok") or not isinstance(bot, dict) or bot.get("is_bot") is not True:
        raise RuntimeError("getMe não confirmou uma conta de bot.")
    token_id = os.environ.get("BOT_TOKEN", "").split(":", 1)[0]
    if str(bot.get("id")) != token_id:
        raise RuntimeError("getMe retornou uma identidade divergente.")
    print("Bot API getMe: identidade do bot confirmada", flush=True)
    response = await asyncio.to_thread(
        chamar, "getChat", json.dumps({"chat_id": "@telegram"}).encode(), headers, True
    )
    chat = response.get("result")
    if (not response.get("ok") or not isinstance(chat, dict)
            or type(chat.get("id")) is not int or chat.get("type") != "channel"):
        raise RuntimeError("getChat não confirmou o canal público de validação.")
    print("Bot API getChat: canal público lido", flush=True)
    dados = await coletar("telegram")
    if id_peer(dados["entidade"]) != chat["id"]:
        raise RuntimeError("Bot API e MTProto retornaram entidades diferentes.")
    if dados["completo"] is None or dados["falhas_coleta"]:
        raise RuntimeError("A leitura do perfil completo MTProto não foi confirmada.")
    print("Bot API e MTProto via Telethon: mesmo canal e perfil completo confirmados", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(principal()))
    except Exception as erro:
        print("Validação das APIs falhou:", type(erro).__name__, flush=True)
        sys.exit(1)
