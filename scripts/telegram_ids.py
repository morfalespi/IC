def tipo_dialogo(valor):
    try:
        identificador = int(valor)
    except (TypeError, ValueError):
        return None
    if isinstance(valor, bool) or str(identificador) != str(valor):
        return None
    if 1 <= identificador <= 1099511627775:
        return "user"
    if -999999999999 <= identificador <= -1:
        return "chat"
    if (-1997852516352 <= identificador <= -1000000000001
            or -4000000000000 <= identificador <= -2002147483649):
        return "channel"
    return None
