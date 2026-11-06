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

