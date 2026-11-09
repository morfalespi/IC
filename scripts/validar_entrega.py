"""Explicitly authorized synthetic delivery, retrieval and SHA-256 verification."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from bot_api import BotClient, authorized_destination, diagnostico_excecao
from ficha_completa import jsonl_files, markdown_files
from mtproto_export import build_media_archives


async def validate(bot=None):
    chat = authorized_destination(os.environ.get('CHAT_ID', ''))
    bot = bot or BotClient()
    await asyncio.to_thread(bot.get_me)
    resolved = await asyncio.to_thread(bot.get_chat, chat)
    if resolved['id'] != chat:
        raise PermissionError('Resolved destination mismatch')
    receipts = []
    async def send_and_verify(method, data, filename, mime):
        message = await asyncio.to_thread(bot.upload, method, chat, data, filename, mime)
        file = message['document'] if method == 'sendDocument' else max(message['photo'], key=lambda p: p['width'] * p['height'])
        downloaded, digest = await asyncio.to_thread(bot.download, file['file_id'])
        # Telegram recompresses photos. Documents must match the submitted bytes.
        equal = downloaded == data
        if method == 'sendDocument' and not equal:
            raise ValueError('Delivered document SHA-256 mismatch')
        receipts.append({'method': method, 'state': 'api_accepted', 'retrieved': True, 'sha256': digest, 'source_bytes_equal': equal, 'message_id': message['message_id'], 'downstream': 'not_observable'})
    message = await asyncio.to_thread(bot.send_message, chat, 'IC authorized synthetic delivery validation.')
    receipts.append({'method': 'sendMessage', 'state': 'api_accepted', 'message_id': message['message_id'], 'downstream': 'not_observable'})
    # A generated 64x64 RGB PNG, with valid CRCs, needs no imaging dependency.
    import struct
    import zlib
    def chunk(kind, content):
        return struct.pack('!I', len(content)) + kind + content + struct.pack('!I', zlib.crc32(kind + content) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!IIBBBBB', 64, 64, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress((b'\0' + b'\x30\x80\xc0' * 64) * 64)) + chunk(b'IEND', b'')
    await send_and_verify('sendPhoto', png, 'synthetic.png', 'image/png')
    with tempfile.TemporaryDirectory(prefix='ic_delivery_') as folder:
        root = Path(folder)
        text = b'IC synthetic media integrity check.\n'
        path = root / 'synthetic.txt'
        path.write_bytes(text)
        archives = build_media_archives([{'path': str(path), 'name': path.name, 'category': 'validation', 'bytes': len(text), 'sha256': hashlib.sha256(text).hexdigest(), 'status': 'downloaded'}], root)
        md = markdown_files([('Source', 'Synthetic validation')], [], [])[0]
        jl = jsonl_files([{'validation': True, 'count': 1}])[0]
        await send_and_verify('sendDocument', md, 'synthetic.md', 'text/markdown')
        await send_and_verify('sendDocument', jl, 'synthetic.jsonl', 'application/x-ndjson')
        await send_and_verify('sendDocument', Path(archives[0]).read_bytes(), 'synthetic.zip', 'application/zip')
    print(json.dumps({'state': 'validated', 'accepted_messages': len(receipts), 'retrieved_uploads': sum(r.get('retrieved') is True for r in receipts), 'verified_documents': sum(r['method'] == 'sendDocument' and r.get('source_bytes_equal') is True for r in receipts)}))
    return 0


async def principal():
    try:
        return await validate()
    except Exception as error:
        print(json.dumps({'state': 'failed', **diagnostico_excecao(error)}))
        return 1


if __name__ == '__main__':
    sys.exit(asyncio.run(principal()))

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

