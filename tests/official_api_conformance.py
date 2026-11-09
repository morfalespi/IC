"""Compare IC's locally executed Bot API HTTP calls with freshly fetched official Telegram tables."""
from email.parser import BytesParser
from email.policy import default
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.request import Request, urlopen

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "scripts"), str(Path(__file__).resolve().parent)]
from bot_api import BotClient
from test_ic import TelegramFixture

SOURCE = "https://core.telegram.org/bots/api.md"
RETURNS = {"getMe": "User", "getChat": "ChatFullInfo", "sendMessage": "Message",
           "sendPhoto": "Message", "sendDocument": "Message", "getFile": "File"}


def parse_sections(document):
    matches = list(re.finditer(r"(?m)^#{2,6}[ \t]+([A-Za-z][A-Za-z0-9]*)[ \t]*$", document))
    return {m.group(1): document[m.end(): matches[i + 1].start() if i + 1 < len(matches) else len(document)]
            for i, m in enumerate(matches)}


def parse_table(section, columns):
    lines = section.splitlines()
    for i, line in enumerate(lines):
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if cells[:len(columns)] == columns:
            rows = []
            for line in lines[i + 1:]:
                if re.fullmatch(r"[-:\s|]+", line):
                    continue
                if not line.strip() or "|" not in line:
                    break
                values = [v.strip() for v in line.strip().strip("|").split("|")]
                if len(values) < len(columns):
                    break
                rows.append(dict(zip(columns, values)))
            if not rows:
                raise ValueError("Empty official table: " + columns[0])
            return rows
    return None


def official():
    def read_page(url):
        with urlopen(Request(url, headers={"User-Agent": "IC-Conformance-Check/1.0"}), timeout=35) as response:
            if response.status != 200:
                raise RuntimeError("Official page failed: " + url)
            raw = response.read(2_000_001)
        if not raw or len(raw) > 2_000_000:
            raise RuntimeError("Official page empty/oversized: " + url)
        print("FONTE OFICIAL:", url, "SHA256:", hashlib.sha256(raw).hexdigest())
        return raw.decode("utf-8")

    from urllib.parse import urljoin
    root = read_page(SOURCE)
    type_index = read_page("https://core.telegram.org/bots/api/types.md")
    documents = {}
    for name in set(RETURNS) | set(RETURNS.values()):
        index = root if name in RETURNS else type_index
        match = re.search(r"\[" + re.escape(name) + r"\]\((/bots/api/(?:methods|types)/[^)\s]+\.md)\)", index)
        if not match:
            raise RuntimeError("No official indexed page for " + name)
        documents[name] = read_page(urljoin(SOURCE, match.group(1)))
    return documents


def ok_type(value, typ):
    typ = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", typ)
    if isinstance(value, bytes):
        return "InputFile" in typ
    if typ.startswith("Integer or String"):
        return type(value) in (int, str)
    if typ.startswith("Integer"):
        return type(value) is int or (isinstance(value, str) and value.lstrip("-").isdigit())
    if typ.startswith("String"):
        return type(value) is str
    if typ.startswith("Boolean"):
        return type(value) is bool
    return True


def request_violations(method, params, doc):
    spec = parse_table(doc, ["Parameter", "Type", "Required", "Description"])
    if spec is None:
        return [] if not params and "Requires no parameters" in doc else ["Official method table missing or unexpected arguments"]
    allowed = {row["Parameter"]: row for row in spec}
    errors = ["Unknown argument: " + p for p in sorted(params.keys() - allowed.keys())]
    for name, row in allowed.items():
        if row["Required"].lower().startswith("yes") and name not in params:
            errors.append("Missing required argument: " + name)
        if name in params and not ok_type(params[name], row["Type"]):
            errors.append("Invalid documented type: " + name + " (" + row["Type"] + ")")
    return errors


def response_violations(obj, kind, docs):
    rows = parse_table(docs[kind], ["Field", "Type", "Description"])
    if rows is None or not isinstance(obj, dict):
        return ["Official response schema unavailable: " + kind]
    errors = []
    for row in rows:
        key = row["Field"]
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            continue
        optional = row["Description"].lower().startswith("optional.")
        if key not in obj and not optional:
            errors.append("Missing official " + kind + " field: " + key)
        if key in obj and not ok_type(obj[key], row["Type"]):
            errors.append("Wrong official " + kind + " field type: " + key)
    return errors


def capture(req, calls):
    if not req.full_url.startswith("https://api.telegram.org/bot") or req.get_method() != "POST":
        raise ValueError("Unexpected HTTP endpoint or verb")
    content_type = req.get_header("Content-type", "")
    if content_type.startswith("application/json"):
        params = json.loads(req.data)
        transport = "JSON"
    elif content_type.startswith("multipart/form-data"):
        msg = BytesParser(policy=default).parsebytes(
            b"Content-Type: " + content_type.encode() + b"\r\nMIME-Version: 1.0\r\n\r\n" + req.data
        )
        if not msg.is_multipart():
            raise ValueError("Invalid multipart body")
        params = {}
        for part in msg.iter_parts():
            key = part.get_param("name", header="content-disposition")
            if not key or key in params:
                raise ValueError("Missing or repeated multipart part")
            params[key] = part.get_payload(decode=True) if part.get_filename() else part.get_payload(decode=True).decode("utf-8")
        transport = "multipart"
    else:
        raise ValueError("Unknown request content type")
    calls.append((req.full_url.rsplit("/", 1)[-1], params, transport))


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
                responses["sendPhoto"] = bot.send_photo(42, b"synthetic-photo")
                responses["sendDocument"] = bot.send_document(42, b"synthetic-document", "fixture.txt")
                responses["getFile"] = bot.get_file(responses["sendDocument"]["document"]["file_id"])
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
    for method, params, transport in calls:
        kind = RETURNS[method]
        errors = request_violations(method, params, docs[method])
        errors += response_violations(responses[method], kind, docs)
        if not re.search(r"\b" + kind + r"\b", docs[method].split("Parameter")[0]):
            errors.append("Official method does not document this response kind")
        print(("FALHOU" if errors else "PASSOU") + ":", method, "[" + transport + "]", "campos=", sorted(params))
        for error in errors:
            print("  DIVERGENCIA:", error)
        failures += errors
    if not request_violations("getFile", {"invalid_parameter": "x"}, docs["getFile"]):
        failures.append("Negative control did not detect invalid request")
    else:
        print("PASSOU: controle negativo detecta parametro nao documentado")
    print("LIMITES: nao testa Telegram real, MTProto, permissões, regras condicionais ou leitura pelo destinatário.")
    print("RESULTADO:", "DIVERGENCIAS" if failures else "CONFORMIDADE PARCIAL (ESCOPO DOCUMENTADO ACIMA)")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print("RESULTADO: INCONCLUSIVO; nenhuma conformidade afirmada")
        print("ERRO:", type(error).__name__, str(error)[:240])
        sys.exit(2)
