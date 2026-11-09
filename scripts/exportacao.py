import base64
def texto_exportavel(valor):
    return str(valor)


def valor_exportavel(valor):
    if hasattr(valor, "to_dict"):
        return valor_exportavel(valor.to_dict())
    if isinstance(valor, dict):
        return {
            texto_exportavel(chave): valor_exportavel(item) for chave, item in valor.items()
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



PRIVATE_FIELDS = {'access_hash', 'auth_key', 'api_hash', 'bot_token', 'token', 'phone', 'file_reference', 'file_id', 'file_unique_id', 'session', 'string_session'}


def disclosure(value):
    """Copy for export; keep the acquired source objects untouched."""
    if isinstance(value, dict):
        return {key: '[REDACTED]' if key.lower() in PRIVATE_FIELDS or key.lower().endswith(('file_id', 'file_unique_id')) else disclosure(item) for key, item in value.items()}
    if isinstance(value, list):
        return [disclosure(item) for item in value]
    if isinstance(value, str):
        from bot_api import redact
        return redact(value)
    return value
