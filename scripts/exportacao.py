import base64
import os
import re


CAMPOS_SIGILOSOS = frozenset({
    "access_hash", "auth_key", "api_hash", "bot_token", "bot_auth_token",
    "authorization", "session", "session_string", "string_session", "password",
    "phone_code", "phone_code_hash", "secret", "credentials", "token",
})
CHAVES_NORMALIZADAS = frozenset(re.sub(r"[^a-z0-9]", "", campo) for campo in CAMPOS_SIGILOSOS)


def texto_exportavel(valor):
    texto = str(valor)
    for nome in ("BOT_TOKEN", "API_HASH", "GH_DISPATCH_TOKEN", "TGCLOUD_TOKEN"):
        segredo = os.environ.get(nome)
        if segredo:
            texto = texto.replace(segredo, "[redigido]")
    texto = re.sub(r"(?:bot)?[0-9]{5,}:[A-Za-z0-9_-]{20,}", "[redigido]", texto)
    return re.sub(r"(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+)", "[redigido]", texto)


def valor_exportavel(valor):
    if hasattr(valor, "to_dict"):
        return valor_exportavel(valor.to_dict())
    if isinstance(valor, dict):
        return {
            texto_exportavel(chave): "[redigido]" if re.sub(r"[^a-z0-9]", "", str(chave).lower()) in CHAVES_NORMALIZADAS
            else valor_exportavel(item) for chave, item in valor.items()
        }
    if isinstance(valor, (list, tuple)):
        return [valor_exportavel(item) for item in valor]
    if isinstance(valor, bytes):
        return {"$bytes_base64": base64.b64encode(valor).decode("ascii")}
    if isinstance(valor, str):
        return texto_exportavel(valor)
    if isinstance(valor, (int, float, bool)) or valor is None:
        return valor
    if hasattr(valor, "isoformat"):
        return valor.isoformat()
    return texto_exportavel(valor)
