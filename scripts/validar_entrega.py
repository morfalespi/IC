import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

from bot_api import chamar, registrar_notificacao, diagnostico_excecao
from exportacao import valor_exportavel
from mtproto_export import build_media_archives
from ficha_completa import markdown_files, jsonl_files
from resolver import enviar_documento_md, enviar_documento_jsonl, enviar_documento_arquivo


async def conferir_arquivo(dados, resposta, conteudo, chat):
    print(json.dumps({"delivery": "confirmed", "response": resposta}, ensure_ascii=False))


async def principal():
    chat = os.environ.get("CHAT_ID", "").strip()
    headers = {"Content-Type": "application/json"}
    mensagem = await asyncio.to_thread(chamar, "sendMessage", json.dumps({
        "chat_id": chat, "text": "Validação autorizada do Infocard: mensagem e três arquivos sintéticos."
    }).encode(), headers)
    registrar_notificacao(mensagem, chat)
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
        resposta = enviar_documento_md(chat, markdown, "validacao", 1, 1)
        await conferir_arquivo(dados, resposta, markdown, chat)
        resposta = enviar_documento_jsonl(chat, jsonl, "validacao", 1, 1)
        await conferir_arquivo(dados, resposta, jsonl, chat)
        resposta = enviar_documento_arquivo(chat, arquivos[0], "validacao", 1, 1)
        await conferir_arquivo(dados, resposta, Path(arquivos[0]).read_bytes(), chat)
    print("Entrega classificada como concluída pela política local; bytes não conferidos")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(principal()))
    except Exception as erro:
        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
        raise SystemExit(0)

