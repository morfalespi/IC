import asyncio
import html
import json
import os
import re
import sys
import traceback
import urllib.error
import urllib.request
import uuid

import telethon
from telethon import TelegramClient, errors, utils
from telethon.sessions import StringSession
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import Channel, PeerChannel, PeerUser, User

ESPERA_TOTAL = 600
LIMITE_TEXTO = 4000
USERNAME_VALIDO = re.compile(r"[A-Za-z0-9_]{1,32}")
CHAT_VALIDO = re.compile(r"-?[0-9]{1,16}")


def esc(valor):
    return html.escape(str(valor), quote=False)


def corte(valor, limite=400):
    texto = " ".join(str(valor).split())
    return texto if len(texto) <= limite else texto[:limite] + "…"


def chamar(metodo, corpo, cabecalhos):
    pedido = urllib.request.Request(
        f"https://api.telegram.org/bot{os.environ['BOT_TOKEN']}/{metodo}",
        data=corpo,
        headers=cabecalhos,
    )
    try:
        with urllib.request.urlopen(pedido, timeout=30) as resposta:
            codigo, bruto = resposta.status, resposta.read()
    except urllib.error.HTTPError as erro:
        codigo, bruto = erro.code, erro.read()
    except Exception as erro:
        return {"ok": False, "error_code": 0, "description": f"{type(erro).__name__}: {erro}"}
    try:
        return json.loads(bruto)
    except ValueError:
        return {"ok": False, "error_code": codigo, "description": f"resposta não é JSON: {bruto[:200]!r}"}


def postar(chat_id, texto, formatado):
    carga = {"chat_id": int(chat_id), "text": texto}
    if formatado:
        carga["parse_mode"] = "HTML"
    return chamar("sendMessage", json.dumps(carga).encode(), {"Content-Type": "application/json"})


def enviar(chat_id, texto):
    retorno = postar(chat_id, texto, True)
    if not retorno.get("ok"):
        raise RuntimeError(f"sendMessage falhou: {retorno.get('error_code')} {retorno.get('description')}")
    open(os.path.join(os.environ.get("RUNNER_TEMP", "/tmp"), "notificado"), "w").close()


def enviar_foto(chat_id, conteudo):
    limite = uuid.uuid4().hex
    corpo = b"".join([
        f'--{limite}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{int(chat_id)}\r\n'.encode(),
        f'--{limite}\r\nContent-Disposition: form-data; name="photo"; filename="perfil.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode(),
        conteudo,
        f"\r\n--{limite}--\r\n".encode(),
    ])
    retorno = chamar("sendPhoto", corpo, {"Content-Type": f"multipart/form-data; boundary={limite}"})
    if not retorno.get("ok"):
        raise RuntimeError(f"sendPhoto falhou: {retorno.get('error_code')} {retorno.get('description')}")


def entidade_de(resultado):
    peer = resultado.peer
    if isinstance(peer, PeerUser):
        return next((u for u in resultado.users if u.id == peer.user_id), None)
    alvo_id = peer.channel_id if isinstance(peer, PeerChannel) else getattr(peer, "chat_id", None)
    return next((c for c in resultado.chats if getattr(c, "id", None) == alvo_id), None)


async def completo(cliente, entidade):
    if isinstance(entidade, User):
        return (await cliente(GetFullUserRequest(entidade))).full_user
    if isinstance(entidade, Channel):
        return (await cliente(GetFullChannelRequest(entidade))).full_chat
    return None


async def com_espera(operacao):
    gasto = 0
    avisado = False
    while True:
        try:
            return await operacao()
        except errors.FloodWaitError as erro:
            espera = erro.seconds + 1
            if gasto + espera > ESPERA_TOTAL:
                raise
            print("FloodWaitError", erro.seconds, "- aguardando", espera, "s para repetir")
            if not avisado and os.environ.get("CHAT_ID"):
                postar(os.environ["CHAT_ID"], f"O Telegram pediu uma espera de {erro.seconds} s. Vou aguardar e repetir a busca.", False)
                avisado = True
            gasto += espera
            await asyncio.sleep(espera)


async def coletar(alvo):
    cliente = TelegramClient(StringSession(), int(os.environ["API_ID"]), os.environ["API_HASH"])
    try:
        await com_espera(lambda: cliente.start(bot_token=os.environ["BOT_TOKEN"]))
        entidade = entidade_de(await com_espera(lambda: cliente(ResolveUsernameRequest(alvo))))
        if entidade is None:
            raise LookupError("O Telegram não devolveu os dados dessa entrada.")
        dados = {"entidade": entidade, "completo": None, "foto": None, "notas": []}
        try:
            dados["completo"] = await com_espera(lambda: completo(cliente, entidade))
        except errors.RPCError as erro:
            dados["notas"].append(f"Dados completos indisponíveis: {type(erro).__name__}: {erro}")
        try:
            dados["foto"] = await com_espera(lambda: cliente.download_profile_photo(entidade, file=bytes))
        except Exception as erro:
            dados["notas"].append(f"Foto não baixada: {type(erro).__name__}: {erro}")
        return dados
    finally:
        await cliente.disconnect()


def campos_presentes(objeto):
    if objeto is None:
        return []
    return sorted(chave for chave, valor in objeto.to_dict().items() if valor not in (None, False, [], "", 0) and chave not in ("phone", "access_hash"))


def descrever(entidade, completo_, alvo):
    foto = getattr(entidade, "photo", None)
    info = {
        "consultado": f"@{alvo}",
        "id": utils.get_peer_id(entidade),
        "username": getattr(entidade, "username", None),
        "usernames": [u.username for u in (getattr(entidade, "usernames", None) or []) if getattr(u, "active", False)],
        "foto": foto is not None and not type(foto).__name__.endswith("Empty"),
        "campos": [],
    }

    def add(rotulo, valor, limite=400, zero=False):
        if valor is None or valor is False or valor == "" or valor == [] or (valor == 0 and not zero):
            return
        info["campos"].append((rotulo, corte(valor, limite)))

    restricoes = [f"{r.platform}: {r.reason}" for r in (getattr(entidade, "restriction_reason", None) or [])]
    if isinstance(entidade, User):
        info["tipo"] = "bot" if entidade.bot else "usuário"
        info["nome"] = " ".join(p for p in (entidade.first_name, entidade.last_name) if p)
        marcas = (("verificado", "verified"), ("premium", "premium"), ("scam", "scam"), ("fake", "fake"), ("restrito", "restricted"), ("suporte", "support"), ("conta excluída", "deleted"))
        add("Restrições", ", ".join(restricoes))
        add("Idioma", getattr(entidade, "lang_code", None))
        if entidade.bot:
            add("Placeholder inline", getattr(entidade, "bot_inline_placeholder", None))
            add("Usuários ativos do bot", getattr(entidade, "bot_active_users", None))
        if completo_ is not None:
            add("Bio", getattr(completo_, "about", None), 600)
            aniversario = getattr(completo_, "birthday", None)
            if aniversario:
                ano = getattr(aniversario, "year", None)
                add("Aniversário", f"{aniversario.day:02d}/{aniversario.month:02d}" + (f"/{ano}" if ano else ""))
            add("Chats em comum", getattr(completo_, "common_chats_count", None), zero=True)
            canal_pessoal = getattr(completo_, "personal_channel_id", None)
            if canal_pessoal:
                add("Canal pessoal", utils.get_peer_id(PeerChannel(canal_pessoal)))
            intro = getattr(completo_, "business_intro", None)
            if intro:
                add("Intro comercial", " — ".join(p for p in (getattr(intro, "title", None), getattr(intro, "description", None)) if p))
            local = getattr(completo_, "business_location", None)
            if local:
                add("Endereço comercial", getattr(local, "address", None))
            add("Presentes recebidos", getattr(completo_, "stargifts_count", None))
            add("Nome nos encaminhamentos", getattr(completo_, "private_forward_name", None))
            add("Mensagens de voz", "bloqueadas" if getattr(completo_, "voice_messages_forbidden", False) else None)
            info_bot = getattr(completo_, "bot_info", None)
            if info_bot:
                add("Descrição do bot", getattr(info_bot, "description", None), 500)
                comandos = [f"/{c.command} — {c.description}" for c in (getattr(info_bot, "commands", None) or [])]
                add("Comandos", "; ".join(comandos[:10]) + (f"; +{len(comandos) - 10}" if len(comandos) > 10 else ""), 700)
                add("Política de privacidade", getattr(info_bot, "privacy_policy_url", None))
    elif isinstance(entidade, Channel):
        info["tipo"] = "supergrupo" if entidade.megagroup else "canal"
        info["nome"] = entidade.title
        marcas = (("verificado", "verified"), ("scam", "scam"), ("fake", "fake"), ("restrito", "restricted"), ("fórum", "forum"))
        add("Restrições", ", ".join(restricoes))
        if completo_ is not None:
            add("Descrição", getattr(completo_, "about", None), 600)
            add("Membros", getattr(completo_, "participants_count", None), zero=True)
            add("Administradores", getattr(completo_, "admins_count", None))
            add("Online agora", getattr(completo_, "online_count", None))
            vinculado = getattr(completo_, "linked_chat_id", None)
            if vinculado:
                add("Chat vinculado", utils.get_peer_id(PeerChannel(vinculado)))
            lento = getattr(completo_, "slowmode_seconds", None)
            add("Modo lento", f"{lento} s" if lento else None)
            add("Boosts aplicados", getattr(completo_, "boosts_applied", None))
            local = getattr(completo_, "location", None)
            if local:
                add("Localização", getattr(local, "address", None))
    else:
        info["tipo"] = "grupo"
        info["nome"] = getattr(entidade, "title", "")
        marcas = ()
    info["marcas"] = [rotulo for rotulo, atributo in marcas if getattr(entidade, atributo, False)]
    return info


def estado_da_foto(info, enviada, tem_chat):
    if enviada:
        return "enviada junto"
    if not info["foto"]:
        return "não"
    return "existe, mas não foi possível enviar" if tem_chat else "existe"


def relatorio(info, notas, foto):
    topo = [
        "<b>Lido via MTProto</b>",
        f"Consultado: {esc(info['consultado'])}",
        f"Tipo: {esc(info['tipo'])}",
        f"ID: <code>{esc(info['id'])}</code>",
        f"Nome: {esc(info['nome'])}" if info["nome"] else "Nome: (vazio)",
    ]
    if info["username"]:
        topo.append(f"Username principal: @{esc(info['username'])}")
    if info["usernames"]:
        topo.append("Usernames ativos: " + ", ".join(f"@{esc(u)}" for u in info["usernames"]))
    if info["marcas"]:
        topo.append(f"Marcas: {esc(', '.join(info['marcas']))}")
    campos = [f"{esc(rotulo)}: {esc(valor)}" for rotulo, valor in info["campos"]]
    rodape = [f"Foto de perfil: {foto}"]
    if info["tipo"] in ("usuário", "bot"):
        rodape.append(f'<a href="tg://user?id={info["id"]}">Abrir perfil</a>')
    avisos = [esc(corte(nota, 300)) for nota in notas]
    while len("\n".join(topo + campos + rodape + avisos)) > LIMITE_TEXTO and (campos or avisos):
        if campos:
            campos.pop()
        else:
            avisos.pop()
    return "\n".join(topo + campos + rodape + avisos)


def falha(alvo, motivo):
    entrada = f"@{alvo} (username)"
    return f"<b>Não foi possível ler</b>\nEntrada: {esc(entrada)}\n{esc(motivo)}"


async def principal():
    print("telethon", telethon.__version__)
    alvo = os.environ.get("ALVO", "").strip().lstrip("@")
    chat = os.environ.get("CHAT_ID", "").strip()
    if chat and not CHAT_VALIDO.fullmatch(chat):
        print("CHAT_ID inválido")
        return 1
    if not USERNAME_VALIDO.fullmatch(alvo):
        texto = falha(alvo or "(vazio)", "Entrada inválida: use um username (1 a 32 letras, números ou _).")
        print("entrada inválida")
        codigo = 1
    else:
        try:
            dados = await coletar(alvo)
            notas = list(dados["notas"])
            print("campos da entidade:", campos_presentes(dados["entidade"]))
            print("campos do perfil completo:", campos_presentes(dados["completo"]))
            foto_enviada = False
            if chat and dados["foto"]:
                try:
                    enviar_foto(chat, dados["foto"])
                    foto_enviada = True
                    print("foto enviada ao chat")
                except Exception as erro:
                    notas.append(f"Foto não enviada: {erro}")
            info = descrever(dados["entidade"], dados["completo"], alvo)
            texto = relatorio(info, notas, estado_da_foto(info, foto_enviada, bool(chat)))
            print("tipo resolvido:", info["tipo"], "| campos extras:", len(info["campos"]))
            codigo = 0
        except errors.UsernameNotOccupiedError:
            texto = falha(alvo, "Esse username não existe.")
            print("UsernameNotOccupiedError")
            codigo = 1
        except errors.UsernameInvalidError:
            texto = falha(alvo, "Username inválido segundo o Telegram.")
            print("UsernameInvalidError")
            codigo = 1
        except errors.FloodWaitError as erro:
            texto = falha(alvo, f"Limite do Telegram atingido: aguarde {erro.seconds} s.")
            print("FloodWaitError", erro.seconds)
            codigo = 1
        except LookupError as erro:
            texto = falha(alvo, str(erro))
            print("LookupError", erro)
            codigo = 1
        except errors.RPCError as erro:
            texto = falha(alvo, f"O Telegram respondeu {type(erro).__name__}: {erro}")
            print("RPCError", type(erro).__name__, erro)
            codigo = 1
        except Exception as erro:
            traceback.print_exc()
            texto = falha(alvo, f"Erro inesperado: {type(erro).__name__}: {erro}")
            codigo = 1
    if chat:
        enviar(chat, texto)
        print("mensagem enviada ao chat")
    return codigo


if __name__ == "__main__":
    sys.exit(asyncio.run(principal()))
