"""Exercise IC code against controlled inputs; report evidence and missing coverage."""
import os
from pathlib import Path
import sys
import tempfile
import struct
import zlib

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "scripts"), str(Path(__file__).resolve().parent)]
from bot_api import BotClient
from fixtures import TelegramFixture
from official_bot_api_contract import (
    RETURNS, UNKNOWN_TYPES, official, parse_table, request_violations,
    response_violations, capture, coverage_inventory,
)

def exercise():
    fixture = TelegramFixture()
    calls, responses = [], {}
    try:
        with tempfile.TemporaryDirectory(prefix="ic_official_") as tmp:
            saved = {key: os.environ.get(key) for key in ("IC_STATE_DIR", "RUNNER_TEMP", "CHAT_ID")}
            os.environ.update(IC_STATE_DIR=tmp, RUNNER_TEMP=tmp, CHAT_ID="42")
            try:
                def local_opener(req, timeout):
                    capture(req, calls)
                    return fixture.open(req, timeout)
                bot = BotClient(token="synthetic-fixture-token", opener=local_opener)
                responses["getMe"] = bot.get_me()
                responses["getChat"] = bot.get_chat(42)
                responses["sendMessage"] = bot.send_message(42, "synthetic content")
                def png_chunk(kind, body):
                    return struct.pack("!I", len(body)) + kind + body + struct.pack("!I", zlib.crc32(kind + body) & 0xffffffff)
                png = (b"\x89PNG\r\n\x1a\n" +
                       png_chunk(b"IHDR", struct.pack("!IIBBBBB", 64, 64, 8, 2, 0, 0, 0)) +
                       png_chunk(b"IDAT", zlib.compress((b"\0" + b"\x30\x80\xc0" * 64) * 64)) +
                       png_chunk(b"IEND", b""))
                responses["sendPhoto"] = bot.send_photo(42, png, filename="fixture.png", content_type="image/png")
                responses["sendDocument"] = bot.send_document(42, b"synthetic-document", "fixture.txt")
                responses["getFile"] = bot.get_file(responses["sendDocument"]["document"]["file_id"])
                responses["getWebhookInfo"] = bot.call("getWebhookInfo").require()
                fixture.updates = [{
                    "update_id": 19, "message": {
                        "message_id": 4, "date": 123, "chat": {"id": 42, "type": "private"}
                    }
                }]
                responses["getUpdates"] = bot.call("getUpdates", {
                    "offset": 19, "limit": 10, "timeout": 0, "allowed_updates": ["message"]
                }).require()
                fixture.responses.append((200, {"ok": True, "result": {
                    "total_count": 1, "photos": [[{
                        "file_id": "synthetic-photo-id", "file_unique_id": "synthetic-unique-id",
                        "width": 64, "height": 64
                    }]]
                }}))
                responses["getUserProfilePhotos"] = bot.call("getUserProfilePhotos", {
                    "user_id": 777, "offset": 0, "limit": 1
                }).require()
                responses["getChatMemberCount"] = bot.call("getChatMemberCount", {
                    "chat_id": 42
                }).require()
            finally:
                for key, value in saved.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
    finally:
        fixture.close()
    return calls, responses


def main():
    docs = official()
    calls, responses = exercise()
    if len(calls) != len(RETURNS) or {c[0] for c in calls} != set(RETURNS):
        raise RuntimeError("Not all intended BotClient operations were observed")
    failures = []
    unverified = coverage_inventory(docs, {c[0] for c in calls})
    for method, params, transport in calls:
        kind = RETURNS[method]
        errors = request_violations(method, params, docs[method])
        errors += response_violations(responses[method], kind, docs)
        published_return = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", docs[method].split("Parameter")[0])
        published_return = re.sub(r"\s+", " ", published_return)
        if not re.search(r"\b" + re.escape(kind) + r"\b", published_return, flags=re.IGNORECASE):
            errors.append("Official method does not document this response kind")
        official_params = parse_table(docs[method], ["Parameter", "Type", "Required", "Description"]) or []
        mandatory_params = sorted(row["Parameter"] for row in official_params if row["Required"].lower().startswith("yes"))
        official_fields = (parse_table(docs[kind], ["Field", "Type", "Description"]) or []
                           if kind in docs else [])
        mandatory_fields = sorted(row["Field"] for row in official_fields
                                  if not row["Description"].lstrip(" *_").lower().startswith("optional"))
        print("  REGRA DA API:", method, "parametros obrigatorios=", mandatory_params,
              "|", kind, "campos obrigatorios=", mandatory_fields)
        print(("DIVERGENCIA" if errors else "SEM DIVERGENCIA NOS CAMPOS COMPARAVEIS") + ":", method, "[" + transport + "]", "campos enviados=", sorted(params))
        for error in errors:
            print("  DIVERGENCIA:", error)
        failures += errors
    unverified.extend("tipo oficial nao interpretado: " + typ for typ in sorted(UNKNOWN_TYPES))
    # Parsing optional fields does not prove all conditional requirements or semantic constraints.
    unverified.append("condicoes, limites e semantica textual da documentacao nao sao verificados exaustivamente")
    unverified.append("respostas originadas de fixture local; Telegram real nao executado")
    if not request_violations("getFile", {"invalid_parameter": "x"}, docs["getFile"]):
        failures.append("Negative control did not detect invalid request")
    else:
        print("PASSOU: controle negativo detecta parametro nao documentado")
    if not request_violations("sendMessage", {"chat_id": 42}, docs["sendMessage"]):
        failures.append("controle negativo nao detectou ausencia de text exigido pelo contrato")
    for gap in sorted(set(unverified)):
        print("NAO COMPROVADO:", gap)
    print("RESUMO:", len(calls), "operacoes exercitadas localmente;", len(failures),
          "divergencias detectadas;", len(set(unverified)), "lacunas de comprovacao")
    print("RESULTADO:", "DIVERGENCIA" if failures else "INCOMPLETO — NENHUMA CONFORMIDADE INTEGRAL AFIRMADA")
    return 1 if failures else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print("RESULTADO: INCONCLUSIVO; nenhuma conformidade afirmada")
        print("ERRO:", type(error).__name__, str(error)[:240])
        sys.exit(2)
