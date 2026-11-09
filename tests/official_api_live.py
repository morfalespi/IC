"""Real, explicitly authorized Telegram Bot API smoke run; never logs credentials or report payloads."""
import hashlib
import os
import re
import struct
import sys
import tempfile
import urllib.request
import zlib

from official_api_conformance import official, capture, request_violations, response_violations
from bot_api import BotClient, authorized_destination


def png_chunk(kind, data):
    return struct.pack("!I", len(data)) + kind + data + struct.pack("!I", zlib.crc32(kind + data) & 0xffffffff)


def test_png():
    return (b"\x89PNG\r\n\x1a\n"
            + png_chunk(b"IHDR", struct.pack("!IIBBBBB", 64, 64, 8, 2, 0, 0, 0))
            + png_chunk(b"IDAT", zlib.compress((b"\x00" + b"\x40\x80\xc0" * 64) * 64))
            + png_chunk(b"IEND", b""))


def main():
    token = os.environ.get("BOT_TOKEN", "")
    target = os.environ.get("IC_TEST_CHAT_ID", "")
    confirmed = os.environ.get("IC_ALLOW_SYNTHETIC_DELIVERY") == "yes"
    if not token or not re.fullmatch(r"-?[1-9]\d{0,15}", target) or not confirmed:
        print("NAO EXECUTADO: credenciais, chat de teste e consentimento explicito sao obrigatorios")
        return 2

    docs = official()
    calls = []
    with tempfile.TemporaryDirectory(prefix="ic_live_") as temp:
        os.environ["IC_STATE_DIR"] = temp
        os.environ["RUNNER_TEMP"] = temp
        os.environ["CHAT_ID"] = target
        def observed_opener(req, timeout):
            if not isinstance(req, str):
                capture(req, calls)
            return urllib.request.urlopen(req, timeout=timeout)
        bot = BotClient(token=token, opener=observed_opener)
        chat_id = authorized_destination(target)
        me = bot.get_me()
        chat = bot.get_chat(chat_id)
        if not me.get("is_bot") or chat.get("id") != chat_id:
            raise ValueError("Identidade do bot ou destino divergente")
        message = bot.send_message(chat_id, "IC: verificacao sintetica autorizada da Bot API")
        photo = bot.send_photo(chat_id, test_png(), filename="verification.png", content_type="image/png")
        payload = b"IC synthetic test document only.\n"
        document = bot.send_document(chat_id, payload, "verification.txt")
        document_id = document["document"]["file_id"]
        file_meta = bot.get_file(document_id)
        retrieved, retrieved_sha = bot.download(document_id)
        if retrieved != payload or retrieved_sha != hashlib.sha256(payload).hexdigest():
            raise ValueError("Documento devolvido pelo Telegram difere dos bytes enviados")
        responses = {"getMe": me, "getChat": chat, "sendMessage": message,
                     "sendPhoto": photo, "sendDocument": document, "getFile": file_meta}
        for method in ("sendMessage", "sendPhoto", "sendDocument"):
            if responses[method]["chat"]["id"] != chat_id:
                raise ValueError("Retorno do Telegram identifica um destino divergente")
        if len(calls) != 7 or [m for m, _, _ in calls].count("getFile") != 2 or {m for m, _, _ in calls} != set(responses):
            raise ValueError("Transporte real nao cobriu os seis metodos previstos")
        failures = []
        for method, params, transport in calls:
            errors = request_violations(method, params, docs[method])
            kind = {"getMe": "User", "getChat": "ChatFullInfo", "sendMessage": "Message",
                    "sendPhoto": "Message", "sendDocument": "Message", "getFile": "File"}[method]
            errors += response_violations(responses[method], kind, docs)
            failures.extend(method + ": " + e for e in errors)
            print(("DIVERGENCIA" if errors else "EXECUCAO_REAL_COM_REGRAS_COMPARADAS") + ": " + method)
        if failures:
            for issue in failures:
                print("PROBLEMA:", issue)
            return 1
        print("DOCUMENTO_REAL_VERIFICADO_SHA256:", hashlib.sha256(payload).hexdigest())
        print("RESULTADO: seis operacoes executadas contra a Bot API real e comparadas com tabelas oficiais atuais")
        print("LIMITES: nao certifica MTProto, coleta de terceiros, recepcao pelo usuario ou todas as regras condicionais")
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print("RESULTADO: INCONCLUSIVO OU FALHA REAL; nao declarar sucesso")
        print("CLASSE_DO_ERRO:", type(error).__name__)
        sys.exit(2)
