import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

from bot_api import chamar, estado_mensagem, registrar_notificacao, BotAPIRequestError, APIProtocolError, diagnostico_excecao
from exportacao import valor_exportavel
from mtproto_export import build_media_archives
from ficha_completa import markdown_files, jsonl_files
from resolver import enviar_documento_md, enviar_documento_jsonl, enviar_documento_arquivo, baixar_arquivo_bot_api
from telegram_ids import tipo_dialogo


async def conferir_arquivo(dados, resposta, conteudo, chat):
    if estado_mensagem(resposta, chat) != "confirmed":
        raise APIProtocolError("sendDocument", {"origin": "validation", "error_code": 0,
                                               "description": "Arquivo aceito mas ainda pendente; sem reenvio"})
    documento = resposta["result"].get("document")
    if not isinstance(documento, dict) or not documento.get("file_id"):
        raise APIProtocolError("sendDocument", {"origin": "protocol", "error_code": 0,
                                               "description": "Message sem Document para conferir o arquivo"})
    recebido = await baixar_arquivo_bot_api(dados, documento["file_id"], "validacao", documento.get("file_unique_id"))
    if (not recebido or recebido.get("status") != "downloaded"
            or recebido.get("sha256") != hashlib.sha256(conteudo).hexdigest()):
        raise APIProtocolError("getFile", {"origin": "validation", "error_code": 0,
                                           "description": "Download do arquivo não confirmou os bytes enviados"})


async def principal():
    chat = os.environ.get("CHAT_ID", "").strip()
    if os.environ.get("MODO") != "validar_entrega" or tipo_dialogo(chat) is None:
        raise ValueError("O teste de entrega exige modo explícito validar_entrega e chat autorizado válido")
    headers = {"Content-Type": "application/json"}
    consulta = await asyncio.to_thread(chamar, "getChat", json.dumps({"chat_id": int(chat)}).encode(), headers)
    if not consulta.get("ok"):
        raise BotAPIRequestError("getChat", consulta)
    destino = consulta.get("result")
    if not isinstance(destino, dict) or destino.get("id") != int(chat):
        raise APIProtocolError("getChat", {"origin": "protocol", "error_code": 0,
                                           "description": "Chat de teste não corresponde ao destino solicitado"})
    mensagem = await asyncio.to_thread(chamar, "sendMessage", json.dumps({
        "chat_id": int(chat), "text": "Validação autorizada do Infocard: mensagem e três arquivos sintéticos."
    }).encode(), headers)
    if registrar_notificacao(mensagem, chat) != "confirmed":
        print("Mensagem sintética aceita mas pendente; validação interrompida sem reenvio")
        return 1
    with tempfile.TemporaryDirectory(prefix="infocard_delivery_") as pasta:
        dados = {"midias_dir": pasta, "midias": []}
        markdown = markdown_files([("Origem", "Validação sintética autorizada")],
                                  [("Teste", [("Conteúdo", "Sem dados pessoais ou credenciais")])], [])[0]
        sintetico = valor_exportavel({"access_hash": 123})
        jsonl = jsonl_files([{"path": "metadados.validation", "value": "synthetic"},
                             {"path": "entity.access_hash", "value": sintetico["access_hash"]}])[0]
        texto = b"Arquivo sintetico para validar envio, download e integridade.\n"
        caminho = Path(pasta) / "synthetic.txt"
        caminho.write_bytes(texto)
        arquivos = build_media_archives([{"path": str(caminho), "name": "synthetic.txt", "category": "validation",
                                         "bytes": len(texto), "sha256": hashlib.sha256(texto).hexdigest()}], pasta)
        if len(arquivos) != 1:
            raise RuntimeError("Nao foi gerado o pacote sintetico esperado")
        resposta = enviar_documento_md(chat, markdown, "validacao", 1, 1)
        await conferir_arquivo(dados, resposta, markdown, chat)
        resposta = enviar_documento_jsonl(chat, jsonl, "validacao", 1, 1)
        await conferir_arquivo(dados, resposta, jsonl, chat)
        resposta = enviar_documento_arquivo(chat, arquivos[0], "validacao", 1, 1)
        await conferir_arquivo(dados, resposta, Path(arquivos[0]).read_bytes(), chat)
    print("Validação de entrega: Message confirmada e três documentos conferidos por download e SHA-256")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(principal()))
    except Exception as erro:
        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
        raise SystemExit(1)
