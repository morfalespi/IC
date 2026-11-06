import asyncio
import json
import sys

from resolver import chamar, coletar
from bot_api import diagnostico_excecao
from exportacao import valor_exportavel


async def principal():
    for metodo, carga in (("getMe", {}), ("getChat", {"chat_id": "@telegram"})):
        resposta = await asyncio.to_thread(chamar, metodo, json.dumps(carga).encode(), {"Content-Type": "application/json"})
        print(json.dumps({"method": metodo, "response": resposta}, ensure_ascii=False))
    dados = await coletar("telegram")
    print(json.dumps(valor_exportavel(dados), ensure_ascii=False))
    print("Verificação encerrada sob a política de aceitação local")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(principal()))
    except Exception as erro:
        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
        sys.exit(0)
