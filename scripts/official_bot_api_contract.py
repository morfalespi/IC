"""Read Telegram-published Bot API documents and compare observed request/response data.

Parsing is deliberately narrow: an unsupported structure must not count as proof.
This module does not assert live Telegram execution or complete API conformance.
"""
import ast
from email.parser import BytesParser
from email.policy import default
import hashlib
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

SOURCE = "https://core.telegram.org/bots/api.md"
UNKNOWN_TYPES = set()
RETURNS = {"getMe": "User", "getChat": "ChatFullInfo", "sendMessage": "Message",
           "sendPhoto": "Message", "sendDocument": "Message", "getFile": "File",
           "getWebhookInfo": "WebhookInfo", "getUpdates": "Array of Update",
           "getUserProfilePhotos": "UserProfilePhotos", "getChatMemberCount": "Integer"}

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
    documents = {"_official_index": root}
    references = active_bot_api_references()
    required_types = {kind.removeprefix("Array of ") for kind in RETURNS.values()
                      if kind != "Integer"} | {"Chat", "AcceptedGiftTypes", "Document", "PhotoSize"}
    for name in sorted(set(RETURNS) | required_types | set(references)):
        index = root if name in RETURNS or name in references else type_index
        match = re.search(r"\[" + re.escape(name) + r"\]\((/bots/api/(?:methods|types)/[^)\s]+\.md)\)", index)
        if not match:
            if name in RETURNS or name in required_types:
                raise RuntimeError("Official document not indexed for required method/type: " + name)
            continue
        documents[name] = read_page(urljoin(SOURCE, match.group(1)))
    print("DOCUMENTOS ATUAIS LIDOS:", len(documents) - 1,
          "| REFERENCIAS DE METODOS NO CODIGO:", len(references))
    return documents


def ok_type(value, typ):
    normalized = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", typ).strip().strip("*")
    if normalized == "Integer or String":
        return type(value) in (int, str)
    if normalized == "Integer":
        return type(value) is int or (type(value) is str and value.lstrip("-").isdigit())
    if normalized == "String":
        return isinstance(value, str)
    if normalized == "Boolean":
        return type(value) is bool
    if normalized == "True":
        return value is True
    if normalized == "Float":
        return type(value) in (float, int)
    if normalized == "InputFile or String":
        return isinstance(value, (bytes, str))
    if normalized in {"Chat", "ChatFullInfo", "Message", "User", "File", "AcceptedGiftTypes",
                      "Document", "PhotoSize", "WebhookInfo", "Update", "UserProfilePhotos"}:
        return isinstance(value, dict)
    if normalized.startswith("Array of "):
        return isinstance(value, list) and all(
            ok_type(item, normalized[len("Array of "):]) for item in value
        )
    raise ValueError("Tipo oficial ainda sem validador: " + normalized)


def request_violations(method, params, doc):
    spec = parse_table(doc, ["Parameter", "Type", "Required", "Description"])
    if spec is None:
        return [] if not params and "Requires no parameters" in doc else ["Tabela oficial indisponivel ou argumentos inesperados"]
    allowed = {row["Parameter"]: row for row in spec}
    errors = ["Parametro nao encontrado na API: " + name for name in sorted(params.keys() - allowed.keys())]
    for name, row in allowed.items():
        required = row["Required"].strip().lower()
        description = row["Description"].lower()
        if required not in {"yes", "optional"}:
            errors.append("Marcador oficial nao interpretado: " + name + "=" + row["Required"])
        if required == "yes" and name not in params:
            errors.append("Falta parametro obrigatorio: " + name)
        if name == "chat_id" and "required unless" in description and "ephemeral reply" in description:
            if name not in params and "ephemeral_message_parameters" not in params:
                errors.append("chat_id necessario para envio comum segundo API")
            if "ephemeral_message_parameters" in params:
                errors.append("Modo efemero ainda nao verificado no IC")
        if name in params:
            try:
                valid = ok_type(params[name], row["Type"])
            except ValueError as exc:
                errors.append(str(exc) + " [" + name + "]")
            else:
                if not valid:
                    errors.append("Tipo de parametro incompativel: " + name + " (" + row["Type"] + ")")
    return errors


def response_violations(obj, kind, docs, stack=()):
    if kind == "Integer":
        return [] if type(obj) is int else ["Resposta oficial Integer invalida"]
    if kind.startswith("Array of "):
        if not isinstance(obj, list):
            return ["Resposta oficial nao e array: " + kind]
        nested = kind[len("Array of "):]
        return [issue for item in obj
                for issue in response_violations(item, nested, docs, stack)]
    if kind in stack:
        return ["Referencia circular de tipo: " + kind]
    rows = parse_table(docs[kind], ["Field", "Type", "Description"])
    if rows is None or not isinstance(obj, dict):
        return ["Tabela oficial nao interpretada ou resposta nao estruturada: " + kind]
    errors = []
    for row in rows:
        key = row["Field"]
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            errors.append("Nome de campo nao interpretado: " + kind)
            continue
        optional = row["Description"].lstrip(" *_").lower().startswith("optional")
        if key not in obj:
            if not optional:
                errors.append("Falta campo obrigatorio da API em " + kind + ": " + key)
            continue
        try:
            valid = ok_type(obj[key], row["Type"])
        except ValueError as exc:
            errors.append(str(exc) + " [" + kind + "." + key + "]")
            continue
        if not valid:
            errors.append("Tipo de campo incompativel: " + kind + "." + key)
        normalized = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", row["Type"]).strip()
        if valid and normalized in docs and normalized != "_official_index":
            errors += response_violations(obj[key], normalized, docs, stack + (kind,))
        if valid and normalized.startswith("Array of "):
            errors += response_violations(obj[key], normalized, docs, stack + (kind,))
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


def active_bot_api_references():
    """Inventory method references in active source; references are not verified calls."""
    root = Path(__file__).resolve().parents[1]
    words = set()
    pattern = re.compile(r"^(?:get|send|edit|answer|set|delete|copy|forward|ban|unban|restrict|pin|unpin|approve|decline|refund|stop)[A-Z][A-Za-z0-9]*$")
    paths = sorted((root / "scripts").rglob("*.py")) + sorted((root / "tgcloud").rglob("*.js"))
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".py":
            tree = ast.parse(text, filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) and pattern.fullmatch(node.value):
                    words.add(node.value)
        else:
            for match in re.finditer(r"\bapi\.([A-Za-z][A-Za-z0-9]*)\s*\(", text):
                if pattern.fullmatch(match.group(1)):
                    words.add(match.group(1))
    return sorted(words)


def coverage_inventory(docs, observed):
    methods = active_bot_api_references()
    official_index = docs["_official_index"]
    uncovered = []
    print("ESCOPO INVENTARIADO: referencias de metodos no codigo ativo =", len(methods))
    for method in methods:
        match = re.search(r"\[" + re.escape(method) + r"\]\(/bots/api/methods/[^\s)]+\.md\)", official_index)
        if not match:
            uncovered.append(method + " — nenhuma entrada encontrada no índice atual da Bot API; revisar referência")
            print("NAO VERIFICADO:", method, "| sem correspondência no índice oficial")
        elif method not in observed:
            uncovered.append(method + " — documentado, mas fluxo não executado pelo comparador")
            print("NAO VERIFICADO:", method, "| documentado, sem execução")
        else:
            print("EXECUCAO LOCAL OBSERVADA:", method)
    if len(observed - set(methods)) > 0:
        uncovered.append("métodos exercitados não catalogados no código ativo: " + repr(sorted(observed - set(methods))))
    return uncovered
