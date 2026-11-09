def tipo_dialogo(valor):
    try:
        identificador = int(valor)
    except (TypeError, ValueError):
        return None
    if identificador >= 0:
        return "user"
    return "chat" if identificador > -1000000000000 else "channel"
