import atexit
import asyncio
import html
import hashlib
import json
import mimetypes
import os
import re
import shutil
import tempfile
import sys
import time
import urllib.error
import urllib.request
import uuid

import telethon
from ficha_completa import rich_pages, basic_pages, markdown_files, jsonl_files
from mtproto_export import build_media_archives
from telethon import TelegramClient, errors, utils
from telethon.sessions import SQLiteSession
from telegram_ids import tipo_dialogo
from exportacao import valor_exportavel, CAMPOS_SIGILOSOS
from bot_api import chamar, diagnostico_api, diagnostico_excecao, BotAPIRequestError, BotAPIAuthenticationError, APIProtocolError, estado_mensagem, registrar_notificacao
from telethon.tl.functions.channels import GetFullChannelRequest, GetChannelsRequest, GetParticipantsRequest, GetMessagesRequest as GetChannelMessagesRequest
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.functions.messages import GetChatsRequest, GetFullChatRequest, GetMessagesRequest
from telethon.tl.functions.users import GetFullUserRequest, GetUsersRequest
from telethon.tl.types import Channel, Chat, ChannelParticipantsRecent, ChannelParticipantsAdmins, ChannelParticipantsBots, ChannelParticipantsBanned, ChannelParticipantsKicked, InputChannel, InputPeerChannel, InputPeerChat, InputPeerUser, InputUser, PeerChannel, PeerChat, PeerUser, User, InputMessageID

MENSAGENS_PENDENTES = []
USERNAME_VALIDO = re.compile(r"[A-Za-z0-9_]{1,32}")
ALVO_VALIDO = re.compile(r"(?:[A-Za-z0-9_]{1,32}|-?\d{1,16})")
CHAT_VALIDO = re.compile(r"-?[0-9]{1,16}")
MENSAGEM_ID = os.environ.get("MESSAGE_ID", "").strip()
CHAT_DESTINO = os.environ.get("CHAT_ID", "").strip()
ID_MENSAGEM = int(MENSAGEM_ID) if MENSAGEM_ID.isdigit() and int(MENSAGEM_ID) > 0 else None
MODO = "resumo" if os.environ.get("MODO") == "resumo" else "completo"
FORMATO_MENSAGEM = os.environ.get("FORMATO_MENSAGEM", "rich")
EXPECTED_ID = os.environ.get("EXPECTED_ID", "").strip()
REFERENCIA = os.environ.get("ORIGEM_ID", "")
ORIGEM_ID = int(REFERENCIA) if REFERENCIA.isdigit() and int(REFERENCIA) > 0 else None


class BotAPIEntity:
    def __init__(self, chat):
        self.data = chat
        self.id = chat.get("id")
        self.type = chat.get("type")
        self.title = chat.get("title")
        self.first_name = chat.get("first_name")
        self.last_name = chat.get("last_name")
        self.username = chat.get("username")
        self.photo = chat.get("photo")

    def to_dict(self):
        return self.data


def id_peer(entidade):
    return entidade.id if isinstance(entidade, BotAPIEntity) else utils.get_peer_id(entidade)


def input_usuario_bot(entidade):
    if isinstance(entidade, BotAPIEntity) and entidade.type == "private":
        return InputUser(entidade.id, 0)
    if isinstance(entidade, User):
        try:
            return utils.get_input_user(utils.get_input_peer(entidade))
        except TypeError:
            return InputUser(entidade.id, 0)
    return None


def input_canal_bot(entidade):
    if isinstance(entidade, Channel):
        try:
            return utils.get_input_channel(utils.get_input_peer(entidade))
        except TypeError:
            return InputChannel(entidade.id, 0)
    if isinstance(entidade, BotAPIEntity) and entidade.type in ("supergroup", "channel"):
        id_real, tipo = utils.resolve_id(entidade.id)
        if tipo is PeerChannel:
            return InputChannel(id_real, 0)
    return None


def input_peer_canal_bot(entidade):
    canal = input_canal_bot(entidade)
    if isinstance(canal, InputChannel):
        return InputPeerChannel(canal.channel_id, canal.access_hash)
    return None



def esc(valor):
    return html.escape(str(valor), quote=False)


def corte(valor, limite=400):
    texto = " ".join(str(valor).split())
    return texto if len(texto) <= limite else texto[:limite] + "…"




def aceitacao_mensagem(resposta):
    estado = estado_mensagem(resposta, CHAT_DESTINO or None)
    if estado == "rejected":
        return False
    if estado == "pending":
        MENSAGENS_PENDENTES.append(resposta["result"].get("ephemeral_message_id"))
        print("Bot API aceitou mensagem sem ID editável; entrega permanece pendente")
    return True


def postar(chat_id, texto, formatado, teclado=None):
    carga = {"chat_id": int(chat_id), "text": texto}
    if formatado:
        carga["parse_mode"] = "HTML"
    if teclado:
        carga["reply_markup"] = teclado
    return chamar("sendMessage", json.dumps(carga).encode(), {"Content-Type": "application/json"})


def enviar(chat_id, texto):
    retorno = postar(chat_id, texto, True)
    if not aceitacao_mensagem(retorno):
        raise BotAPIRequestError("sendMessage", retorno)
    registrar_notificacao(retorno, chat_id)


def enviar_foto(chat_id, conteudo):
    limite = uuid.uuid4().hex
    corpo = b"".join([
        f'--{limite}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{int(chat_id)}\r\n'.encode(),
        f'--{limite}\r\nContent-Disposition: form-data; name="photo"; filename="perfil.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode(),
        conteudo,
        f"\r\n--{limite}--\r\n".encode(),
    ])
    retorno = chamar("sendPhoto", corpo, {"Content-Type": f"multipart/form-data; boundary={limite}"})
    if not aceitacao_mensagem(retorno):
        raise BotAPIRequestError("sendPhoto", retorno)


def solicitar_bot_api(metodo, dados, foto=None):
    corpo = dict(dados)
    if foto:
        rich = dict(corpo["rich_message"])
        rich["html"] = rich["html"].replace("</h2>", '</h2><img src="tg://photo?id=perfil"/>', 1)
        rich["media"] = [{"id": "perfil", "media": {"type": "photo", "media": "attach://perfil_file"}}]
        corpo["rich_message"] = rich
        limite = uuid.uuid4().hex
        partes = []
        for chave, valor in corpo.items():
            texto = json.dumps(valor, ensure_ascii=False) if isinstance(valor, (dict, list)) else str(valor)
            partes.append(f'--{limite}\r\nContent-Disposition: form-data; name="{chave}"\r\n\r\n{texto}\r\n'.encode("utf-8"))
        partes.extend([
            f'--{limite}\r\nContent-Disposition: form-data; name="perfil_file"; filename="perfil.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode(),
            foto,
            f'\r\n--{limite}--\r\n'.encode(),
        ])
        return chamar(metodo, b"".join(partes), {"Content-Type": f"multipart/form-data; boundary={limite}"})
    return chamar(metodo, json.dumps(corpo, ensure_ascii=False).encode("utf-8"), {"Content-Type": "application/json"})


def marcar_notificado():
    open(os.path.join(os.environ.get("RUNNER_TEMP", "/tmp"), "notificado"), "w").close()


def mensagem_inalterada(resposta):
    return (resposta.get("error_code") == 400
            and "message is not modified" in str(resposta.get("description", "")).lower())


def editar_ficha_rica(conteudo, foto=None, definitiva=False):
    if not CHAT_DESTINO:
        return False, False, ID_MENSAGEM
    metodo = "editMessageText" if ID_MENSAGEM else "sendRichMessage"
    dados = {"chat_id": int(CHAT_DESTINO), "rich_message": {"html": conteudo}}
    if ID_MENSAGEM:
        dados["message_id"] = ID_MENSAGEM
    incorporar = bool(foto and len(foto) <= 10 * 1024 * 1024)
    resposta = solicitar_bot_api(metodo, dados, foto if incorporar else None)
    if metodo == "editMessageText" and mensagem_inalterada(resposta):
        print("editMessageText: mensagem já está no estado solicitado")
        if definitiva:
            marcar_notificado()
        return True, incorporar, ID_MENSAGEM
    if not aceitacao_mensagem(resposta):
        diagnostico = diagnostico_api(resposta, metodo)
        print(json.dumps(diagnostico, ensure_ascii=False))
        raise BotAPIRequestError(metodo, resposta)
    if definitiva and estado_mensagem(resposta, CHAT_DESTINO) == "confirmed":
        marcar_notificado()
    return True, incorporar, resposta["result"]["message_id"]


def callback_data(acao, alvo):
    if acao not in ("r", "f"):
        return ""
    if re.fullmatch(r"-?\d{1,16}", alvo):
        valor = f"{acao}:i:{alvo}"
    elif USERNAME_VALIDO.fullmatch(alvo):
        valor = f"{acao}:u:{EXPECTED_ID}:{alvo}" if EXPECTED_ID else f"{acao}:n:{alvo}"
    else:
        return ""
    return valor if len(valor.encode("utf-8")) <= 64 else ""


def botao_completo(alvo):
    dados = callback_data("f", alvo)
    return ('<tg-button type="callback_data" style="primary" data="' +
            esc(dados) + '">📥 Exportação completa</tg-button>') if dados else ""

def enviar_documento_md(chat, conteudo, id_entidade, indice, total):
    limite = uuid.uuid4().hex
    filename = "infocard_" + str(id_entidade).replace("-", "n") + "_dados_coletados"
    if total > 1:
        filename += f"_parte_{indice}_de_{total}"
    filename += ".md"
    resumo_hash = hashlib.sha256(conteudo).hexdigest()
    campos = {"chat_id": str(int(chat)), "caption": "📄 Dados coletados nesta consulta" +
              (f" · parte {indice}/{total}" if total > 1 else "") +
              "\nSHA-256: " + resumo_hash}
    if ORIGEM_ID:
        campos["reply_parameters"] = json.dumps({"message_id": ORIGEM_ID})
    partes = []
    for chave, valor in campos.items():
        partes.append((f'--{limite}\r\nContent-Disposition: form-data; name="{chave}"'
                       f'\r\n\r\n{valor}\r\n').encode("utf-8"))
    partes.extend([
        (f'--{limite}\r\nContent-Disposition: form-data; name="document"; '
         f'filename="{filename}"\r\nContent-Type: text/markdown; charset=utf-8'
         f'\r\n\r\n').encode("utf-8"),
        conteudo,
        f'\r\n--{limite}--\r\n'.encode("utf-8"),
    ])
    resposta = chamar("sendDocument", b"".join(partes),
                     {"Content-Type": f"multipart/form-data; boundary={limite}"})
    if not aceitacao_mensagem(resposta):
        raise BotAPIRequestError("sendDocument", resposta)
    print(f"documento Markdown {indice}/{total} confirmado: {len(conteudo)} bytes")






def registrar_midia(dados, categoria, nome, caminho=None, status="downloaded", erro=None):
    item = {"category": categoria, "name": nome, "status": status}
    if erro:
        item["error"] = erro
    if caminho and os.path.isfile(caminho):
        resumo = hashlib.sha256()
        tamanho = 0
        with open(caminho, "rb") as arquivo:
            while True:
                bloco = arquivo.read(1024 * 1024)
                if not bloco:
                    break
                tamanho += len(bloco)
                resumo.update(bloco)
        item["path"] = caminho
        item["bytes"] = tamanho
        item["sha256"] = resumo.hexdigest()
    dados.setdefault("midias", []).append(item)
    return item


def registrar_paginacao_incompleta(dados, metodo, esperado, recebido):
    if isinstance(esperado, int) and recebido < esperado:
        entrada = {"method": metodo, "expected": esperado, "received": recebido}
        dados.setdefault("coletas_incompletas", []).append(entrada)
        dados.setdefault("notas", []).append(
            f"{metodo}: paginação incompleta ({recebido}/{esperado})."
        )


async def bot_api_leitura(dados, metodo, parametros):
    resposta = await asyncio.to_thread(
        chamar, metodo, json.dumps(parametros, ensure_ascii=False).encode("utf-8"),
        {"Content-Type": "application/json"}
    )
    dados.setdefault("respostas_bot_api", {}).setdefault(metodo, []).append(resposta)
    if not resposta.get("ok"):
        dados.setdefault("falhas_bot_api", []).append({
            "method": metodo,
            "error_code": resposta.get("error_code"),
            "description": corte(resposta.get("description", "Resposta sem sucesso"), 300),
        })
    return resposta


async def baixar_arquivo_bot_api(dados, file_id, categoria, file_unique_id=None):
    if not dados.get("midias_dir") or not file_id:
        return None
    hash_nome = hashlib.sha256(str(file_unique_id or file_id).encode("utf-8")).hexdigest()[:20]
    processados = dados.setdefault("_arquivos_bot_api_processados", set())
    if hash_nome in processados:
        return None
    processados.add(hash_nome)
    try:
        retorno = await bot_api_leitura(dados, "getFile", {"file_id": file_id})
        if not retorno.get("ok"):
            return registrar_midia(
                dados, categoria, hash_nome, status="unavailable",
                erro=f"getFile: {retorno.get('error_code')} {corte(retorno.get('description', ''), 160)}"
            )
        arquivo = retorno.get("result") or {}
        caminho_remoto = arquivo.get("file_path")
        if not caminho_remoto:
            return registrar_midia(dados, categoria, hash_nome, status="unavailable",
                                   erro="getFile não retornou file_path")
        tamanho = arquivo.get("file_size")
        if isinstance(tamanho, int) and tamanho > 20 * 1024 * 1024:
            return registrar_midia(dados, categoria, hash_nome, status="unavailable",
                                   erro="Arquivo excede o limite da Bot API (20 MiB)")
        url = "https://api.telegram.org/file/bot" + os.environ["BOT_TOKEN"] + "/" + caminho_remoto
        try:
            with urllib.request.urlopen(urllib.request.Request(url), timeout=60) as resposta:
                conteudo = resposta.read(20 * 1024 * 1024 + 1)
        except errors.UnauthorizedError:
            raise
        except (errors.RPCError, OSError, BotAPIRequestError) as erro:
            print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
            return registrar_midia(dados, categoria, hash_nome, status="failed",
                                   erro=f"download: {type(erro).__name__}")
        if len(conteudo) > 20 * 1024 * 1024:
            return registrar_midia(dados, categoria, hash_nome, status="unavailable",
                                   erro="Arquivo excede o limite da Bot API (20 MiB)")
        extensao = os.path.splitext(caminho_remoto)[1][:12] or ".bin"
        nome = hash_nome + extensao
        caminho_local = os.path.join(dados["midias_dir"], nome)
        with open(caminho_local, "wb") as saida:
            saida.write(conteudo)
        item = registrar_midia(dados, categoria, nome, caminho_local)
        item["source"] = "Bot API"
        return item
    except errors.UnauthorizedError:
        raise
    except (errors.RPCError, OSError, BotAPIRequestError) as erro:
        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
        return registrar_midia(dados, categoria, hash_nome, status="failed",
                               erro=type(erro).__name__)


async def baixar_arquivos_bot_api(dados, objeto, categoria):
    anexos = []

    def visitar(valor, caminho=()):
        if isinstance(valor, dict):
            if isinstance(valor.get("file_id"), str):
                anexos.append((valor, caminho))
            for chave, item in valor.items():
                if chave in ("file_id", "file_unique_id"):
                    continue
                if isinstance(item, list) and item and all(
                    isinstance(tamanho, dict) and isinstance(tamanho.get("file_id"), str)
                    and isinstance(tamanho.get("width"), int)
                    and isinstance(tamanho.get("height"), int)
                    for tamanho in item
                ):
                    maior = max(item, key=lambda tamanho: (
                        tamanho["width"] * tamanho["height"],
                        tamanho.get("file_size", 0)
                    ))
                    visitar(maior, caminho + (str(chave),))
                else:
                    visitar(item, caminho + (str(chave),))
        elif isinstance(valor, list):
            for indice, item in enumerate(valor):
                visitar(item, caminho + (str(indice),))

    visitar(objeto)
    for item, caminho in anexos:
        rotulo = re.sub(r"[^A-Za-z0-9_-]+", "_", "_".join(caminho))[:80] or "arquivo"
        await baixar_arquivo_bot_api(
            dados, item["file_id"], categoria + "_" + rotulo,
            item.get("file_unique_id")
        )


def ids_participantes_conhecidos(dados):
    ids = set()
    ids_bot = set()
    id_bot = (dados.get("estado_bot_no_chat") or {}).get("bot_id")
    if isinstance(id_bot, int):
        ids_bot.add(id_bot)
    fontes = [dados.get("participantes_mtproto", [])]
    fontes.extend((dados.get("participantes_filtrados_mtproto", {}) or {}).values())
    for paginas in fontes:
        for pagina in paginas or []:
            for usuario in getattr(pagina, "users", []) or []:
                if getattr(usuario, "bot", False):
                    ids_bot.add(getattr(usuario, "id", None))
            for participante in getattr(pagina, "participants", []) or []:
                id_usuario = getattr(participante, "user_id", None)
                if isinstance(id_usuario, int):
                    ids.add(id_usuario)
    resposta_completa = dados.get("resposta_completa")
    for usuario in getattr(resposta_completa, "users", []) or []:
        id_usuario = getattr(usuario, "id", None)
        if getattr(usuario, "bot", False) and isinstance(id_usuario, int):
            ids_bot.add(id_usuario)
    participantes_chat = getattr(dados.get("completo"), "participants", None)
    for participante in getattr(participantes_chat, "participants", []) or []:
        id_usuario = getattr(participante, "user_id", None)
        if isinstance(id_usuario, int):
            ids.add(id_usuario)
    for resposta in (dados.get("respostas_bot_api", {}).get("getChatAdministrators", []) or []):
        if not resposta.get("ok"):
            continue
        for administrador in resposta.get("result") or []:
            usuario = (administrador or {}).get("user") or {}
            id_usuario = usuario.get("id")
            if usuario.get("is_bot"):
                ids_bot.add(id_usuario)
            elif isinstance(id_usuario, int):
                ids.add(id_usuario)
    return sorted(id_usuario for id_usuario in ids if id_usuario not in ids_bot)


def chave_participante_mtproto(participante):
    id_usuario = getattr(participante, "user_id", None)
    if isinstance(id_usuario, int):
        return ("user", id_usuario)
    peer = getattr(participante, "peer", None)
    if peer is not None:
        return ("peer", utils.get_peer_id(peer))
    raise TypeError("Construtor de participante sem user_id ou peer reconhecido.")


def ids_participantes_com_boosts_bot_api(dados):
    ids = set()
    respostas = dados.get("respostas_bot_api", {}).get("getUserChatBoosts", [])
    for entrada in dados.get("boosts_por_participante_bot_api", []) or []:
        id_usuario = entrada.get("user_id")
        indice = entrada.get("response_index")
        if not entrada.get("ok") or not isinstance(id_usuario, int):
            continue
        if not isinstance(indice, int) or indice < 0 or indice >= len(respostas):
            continue
        resposta = respostas[indice]
        if not resposta.get("ok"):
            continue
        resultado = resposta.get("result") or {}
        if isinstance(resultado, dict) and resultado.get("boosts"):
            ids.add(id_usuario)
    return sorted(ids)


def registrar_coleta_participantes_incompleta(dados, metodo, esperado, recebido):
    dados.setdefault("coletas_incompletas", []).append({
        "method": metodo, "expected": esperado, "received": recebido,
    })
    dados.setdefault("notas", []).append(
        f"{metodo}: consulta interrompida após {recebido} respostas bem-sucedidas de {esperado} participantes."
    )


async def coletar_dados_participante_bot_api(dados, entidade, chat_id):
    entidade_bot_api_chat = isinstance(entidade, BotAPIEntity) and entidade.type in (
        "group", "supergroup", "channel"
    )
    if not isinstance(entidade, (Channel, Chat)) and not entidade_bot_api_chat:
        return
    ids_usuarios = ids_participantes_conhecidos(dados)
    if not ids_usuarios:
        return
    consulta_boosts = isinstance(entidade, Channel) or (
        isinstance(entidade, BotAPIEntity) and entidade.type in ("supergroup", "channel")
    )
    estados = dados.setdefault("membros_bot_api_por_participante", [])
    boosts = dados.setdefault("boosts_por_participante_bot_api", []) if consulta_boosts else []
    membros_ok = 0
    boosts_ok = 0
    for indice, id_usuario in enumerate(ids_usuarios):
        respostas_membros = dados.get("respostas_bot_api", {}).get("getChatMember", [])
        indice_membro = len(respostas_membros)
        membro = await bot_api_leitura(
            dados, "getChatMember",
            {"chat_id": chat_id, "user_id": id_usuario}
        )
        estados.append({
            "user_id": id_usuario,
            "response_index": indice_membro,
            "ok": bool(membro.get("ok")),
        })
        if membro.get("ok"):
            membros_ok += 1
        else:
            descricao = str(membro.get("description", "")).upper()
            estado = membro.get("error_code")
            if estado == 429 or (isinstance(estado, int) and estado >= 500) or "CHAT_ADMIN_REQUIRED" in descricao:
                registrar_coleta_participantes_incompleta(
                    dados, "getChatMember", len(ids_usuarios), membros_ok
                )
                if consulta_boosts:
                    registrar_coleta_participantes_incompleta(
                        dados, "getUserChatBoosts", len(ids_usuarios), boosts_ok
                    )
                break

        if not consulta_boosts:
            continue

        respostas_boosts = dados.get("respostas_bot_api", {}).get("getUserChatBoosts", [])
        indice_boost = len(respostas_boosts)
        resposta_boost = await bot_api_leitura(
            dados, "getUserChatBoosts",
            {"chat_id": chat_id, "user_id": id_usuario}
        )
        boosts.append({
            "user_id": id_usuario,
            "response_index": indice_boost,
            "ok": bool(resposta_boost.get("ok")),
        })
        if resposta_boost.get("ok"):
            boosts_ok += 1
            continue
        descricao = str(resposta_boost.get("description", "")).upper()
        estado = resposta_boost.get("error_code")
        if estado == 429 or (isinstance(estado, int) and estado >= 500) or "CHAT_ADMIN_REQUIRED" in descricao:
            registrar_coleta_participantes_incompleta(
                dados, "getUserChatBoosts", len(ids_usuarios), boosts_ok
            )
            break


async def coletar_estado_bot_no_chat(dados, chat_id):
    me = await bot_api_leitura(dados, "getMe", {})
    if not me.get("ok"):
        return
    bot_id = (me.get("result") or {}).get("id")
    if not isinstance(bot_id, int):
        dados.setdefault("notas", []).append(
            "getMe não retornou um ID numérico; status do bot no chat não foi consultado."
        )
        return
    respostas = dados.get("respostas_bot_api", {}).get("getChatMember", [])
    indice = len(respostas)
    membro = await bot_api_leitura(
        dados, "getChatMember", {"chat_id": chat_id, "user_id": bot_id}
    )
    dados["estado_bot_no_chat"] = {
        "bot_id": bot_id,
        "response_index": indice,
        "ok": bool(membro.get("ok")),
    }


async def coletar_stickers_bot_api(dados, objeto):
    nomes_conjuntos = set()
    ids_emojis = set()

    def visitar(valor):
        if isinstance(valor, dict):
            for chave, item in valor.items():
                if chave in ("sticker_set_name", "custom_emoji_sticker_set_name") and isinstance(item, str) and item:
                    nomes_conjuntos.add(item)
                elif chave in ("custom_emoji_id", "emoji_status_custom_emoji_id") and isinstance(item, str) and item:
                    ids_emojis.add(item)
                visitar(item)
        elif isinstance(valor, list):
            for item in valor:
                visitar(item)

    visitar(objeto)
    for nome in sorted(nomes_conjuntos):
        resposta = await bot_api_leitura(dados, "getStickerSet", {"name": nome})
        if resposta.get("ok"):
            await baixar_arquivos_bot_api(dados, resposta.get("result"), "conjunto_stickers_bot_api")
    emojis = sorted(ids_emojis)
    for inicio in range(0, len(emojis), 200):
        resposta = await bot_api_leitura(
            dados, "getCustomEmojiStickers",
            {"custom_emoji_ids": emojis[inicio:inicio + 200]}
        )
        if resposta.get("ok"):
            await baixar_arquivos_bot_api(dados, resposta.get("result"), "emoji_personalizado_bot_api")


async def coletar_catalogo_presentes_bot_api(dados):
    metodo = "getAvailableGifts"
    indice_resposta = len(dados.get("respostas_bot_api", {}).get(metodo, []))
    resposta = await bot_api_leitura(dados, metodo, {})
    resultado = resposta.get("result") or {}
    presentes = resultado.get("gifts") or []
    dados["catalogo_presentes_bot_api"] = {
        "method": metodo,
        "response_index": indice_resposta,
        "ok": bool(resposta.get("ok")),
        "gift_count": len(presentes),
    }
    if resposta.get("ok"):
        await baixar_arquivos_bot_api(dados, resultado, "catalogo_presentes_bot_api")


async def coletar_presentes_bot_api(dados, entidade, chat_id):
    entidade_usuario = isinstance(entidade, User) or (
        isinstance(entidade, BotAPIEntity) and entidade.type == "private"
    )
    metodo = "getUserGifts" if entidade_usuario else "getChatGifts"
    parametros_base = (
        {"user_id": entidade.id}
        if entidade_usuario
        else {"chat_id": chat_id}
    )
    offset = ""
    offsets_vistos = set()
    total = None
    recebidos = 0
    paginas = dados.setdefault("presentes_bot_api", [])
    while True:
        parametros = dict(parametros_base, offset=offset, limit=100)
        indice_resposta = len(dados.get("respostas_bot_api", {}).get(metodo, []))
        resposta = await bot_api_leitura(dados, metodo, parametros)
        if not resposta.get("ok"):
            if isinstance(total, int):
                registrar_paginacao_incompleta(dados, metodo, total, recebidos)
            break
        resultado = resposta.get("result") or {}
        contagem = resultado.get("total_count")
        if isinstance(contagem, int):
            total = contagem if total is None else max(total, contagem)
        presentes = resultado.get("gifts") or []
        paginas.append({
            "method": metodo,
            "response_index": indice_resposta,
            "offset": offset,
            "next_offset": resultado.get("next_offset", ""),
            "total_count": contagem,
            "received": len(presentes),
        })
        recebidos += len(presentes)
        await baixar_arquivos_bot_api(dados, resultado, "presente_" + metodo)
        proximo = resultado.get("next_offset") or ""
        if not proximo:
            break
        if proximo == offset or proximo in offsets_vistos:
            dados.setdefault("coletas_incompletas", []).append({
                "method": metodo,
                "expected": total,
                "received": recebidos,
                "reason": "next_offset repetido; paginação interrompida para evitar ciclo",
            })
            dados.setdefault("notas", []).append(
                f"{metodo}: paginação interrompida porque next_offset repetiu."
            )
            break
        offsets_vistos.add(offset)
        offset = proximo
    registrar_paginacao_incompleta(dados, metodo, total, recebidos)


def objetos_mtproto(valor, visitados=None):
    if visitados is None:
        visitados = set()
    if valor is None or isinstance(valor, (str, bytes, int, float, bool)):
        return
    identidade = id(valor)
    if identidade in visitados:
        return
    visitados.add(identidade)
    yield valor
    if isinstance(valor, dict):
        filhos = valor.values()
    elif isinstance(valor, (list, tuple, set)):
        filhos = valor
    else:
        atributos = dict(vars(valor)) if hasattr(valor, "__dict__") else {}
        for classe in type(valor).__mro__:
            slots = getattr(classe, "__slots__", ())
            if isinstance(slots, str):
                slots = (slots,)
            for nome in slots:
                if not nome.startswith("_") and hasattr(valor, nome):
                    atributos[nome] = getattr(valor, nome)
        filhos = (item for nome, item in atributos.items() if not nome.startswith("_"))
    for filho in filhos:
        yield from objetos_mtproto(filho, visitados)


def documentos_mtproto(valor):
    from telethon.tl.types import Document
    for objeto in objetos_mtproto(valor):
        if isinstance(objeto, Document):
            yield objeto


async def baixar_documentos_presente_mtproto(cliente, presente, dados, categoria, nome):
    if not dados.get("midias_dir"):
        return
    processados = dados.setdefault("_documentos_mtproto_processados", set())
    for indice, documento in enumerate(documentos_mtproto(presente), 1):
        if documento.id in processados:
            continue
        processados.add(documento.id)
        await baixar_midia(
            cliente, documento, dados, categoria,
            f"{nome}_documento_{indice:02d}"
        )


async def coletar_stickers_mtproto(cliente, dados):
    from telethon.tl.functions.messages import GetCustomEmojiDocumentsRequest, GetStickerSetRequest
    from telethon.tl.types import (
        DocumentAttributeCustomEmoji, DocumentAttributeSticker, EmojiStatus,
        EmojiStatusCollectible, InputStickerSetEmpty, InputStickerSetID,
        ForumTopic, MessageActionTopicCreate, MessageActionTopicEdit,
        MessageEntityCustomEmoji, PeerColor, PeerColorCollectible, StickerSet,
    )
    fontes = list(objetos_mtproto(dados))
    ids_emoji = set()
    for objeto in fontes:
        if isinstance(objeto, (MessageEntityCustomEmoji, EmojiStatus, EmojiStatusCollectible)):
            ids_emoji.add(objeto.document_id)
        if isinstance(objeto, EmojiStatusCollectible):
            ids_emoji.add(objeto.pattern_document_id)
        if isinstance(objeto, (PeerColor, PeerColorCollectible)) and objeto.background_emoji_id:
            ids_emoji.add(objeto.background_emoji_id)
        if isinstance(objeto, PeerColorCollectible):
            ids_emoji.add(objeto.gift_emoji_id)
        if isinstance(objeto, (ForumTopic, MessageActionTopicCreate, MessageActionTopicEdit)) and objeto.icon_emoji_id:
            ids_emoji.add(objeto.icon_emoji_id)
    ids_emoji = sorted(ids_emoji)
    respostas_emoji = dados.setdefault("emojis_personalizados_mtproto", [])
    for inicio in range(0, len(ids_emoji), 100):
        lote = ids_emoji[inicio:inicio + 100]
        try:
            resposta = await com_espera(lambda: cliente(GetCustomEmojiDocumentsRequest(document_id=lote)))
            respostas_emoji.append({"request_ids": lote, "response": resposta})
        except errors.UnauthorizedError:
            raise
        except (errors.RPCError, OSError, BotAPIRequestError) as erro:
            print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
            dados.setdefault("falhas_coleta", []).append({
                "method": "messages.getCustomEmojiDocuments", "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro),
                "document_ids": lote,
            })
    fontes.extend(objetos_mtproto(respostas_emoji))
    conjuntos = {}
    for objeto in fontes:
        referencia = None
        if isinstance(objeto, StickerSet):
            referencia = InputStickerSetID(objeto.id, objeto.access_hash)
        elif isinstance(objeto, (DocumentAttributeSticker, DocumentAttributeCustomEmoji)):
            referencia = objeto.stickerset
        if referencia is not None and not isinstance(referencia, InputStickerSetEmpty):
            conjuntos.setdefault(bytes(referencia), referencia)
    respostas_conjuntos = dados.setdefault("conjuntos_stickers_mtproto", [])
    for referencia in conjuntos.values():
        try:
            resposta = await com_espera(lambda: cliente(GetStickerSetRequest(stickerset=referencia, hash=0)))
            respostas_conjuntos.append({"request": referencia, "response": resposta})
        except errors.UnauthorizedError:
            raise
        except (errors.RPCError, OSError, BotAPIRequestError) as erro:
            print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
            dados.setdefault("falhas_coleta", []).append({
                "method": "messages.getStickerSet", "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro),
                "request": referencia,
            })
    await baixar_documentos_presente_mtproto(
        cliente, respostas_emoji, dados, "emoji_personalizado_mtproto", "emoji_personalizado_mtproto"
    )
    await baixar_documentos_presente_mtproto(
        cliente, respostas_conjuntos, dados, "conjunto_stickers_mtproto", "conjunto_stickers_mtproto"
    )
    documentos_referenciados = list(documentos_mtproto(dados))
    await baixar_documentos_presente_mtproto(
        cliente, documentos_referenciados, dados, "documento_referenciado_mtproto", "documento_referenciado_mtproto"
    )


async def coletar_topicos_conhecidos_mtproto(cliente, dados):
    from telethon.tl.functions.messages import GetForumTopicsByIDRequest
    from telethon.tl.types import Message, MessageService, MessageActionTopicCreate
    topicos = {}
    for objeto in objetos_mtproto(dados):
        peer_id = None
        id_topico = None
        if isinstance(objeto, (Message, MessageService)):
            resposta = getattr(objeto, "reply_to", None)
            if getattr(resposta, "forum_topic", False):
                id_topico = getattr(resposta, "reply_to_top_id", None) or getattr(resposta, "reply_to_msg_id", None)
            if isinstance(getattr(objeto, "action", None), MessageActionTopicCreate):
                id_topico = objeto.id
            peer = getattr(objeto, "peer_id", None)
            if not isinstance(getattr(objeto, "action", None), MessageActionTopicCreate):
                peer = getattr(resposta, "reply_to_peer_id", None) or peer
            if peer is not None:
                peer_id = utils.get_peer_id(peer)
        elif isinstance(objeto, dict) and objeto.get("is_topic_message") is True:
            id_topico = objeto.get("message_thread_id")
            peer_id = (objeto.get("chat") or {}).get("id")
        if isinstance(peer_id, int) and isinstance(id_topico, int) and id_topico > 0:
            topicos.setdefault(peer_id, set()).add(id_topico)
    respostas = dados.setdefault("topicos_forum_mtproto", [])
    for peer_id, ids in topicos.items():
        id_real, tipo = utils.resolve_id(peer_id)
        if tipo is PeerChannel:
            peer = InputPeerChannel(id_real, 0)
        elif tipo is PeerChat:
            peer = InputPeerChat(id_real)
        else:
            peer = InputPeerUser(id_real, 0)
        ids = sorted(ids)
        for inicio in range(0, len(ids), 100):
            lote = ids[inicio:inicio + 100]
            try:
                resultado = await com_espera(lambda: cliente(GetForumTopicsByIDRequest(peer=peer, topics=lote)))
                respostas.append({"peer": peer, "topic_ids": lote, "response": resultado})
            except errors.UnauthorizedError:
                raise
            except (errors.RPCError, OSError, BotAPIRequestError) as erro:
                print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
                dados.setdefault("falhas_coleta", []).append({
                    "method": "messages.getForumTopicsByID", "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro),
                    "peer": peer, "topic_ids": lote,
                })


async def coletar_catalogo_presentes_mtproto(cliente, dados):
    metodo = "payments.getStarGifts"
    try:
        from telethon.tl.functions.payments import GetStarGiftsRequest
        resposta = await com_espera(lambda: cliente(GetStarGiftsRequest(hash=0)))
        dados.setdefault("catalogo_presentes_star_gifts_mtproto", []).append(resposta)
        presentes = getattr(resposta, "gifts", []) or []
        if dados.get("midias_dir"):
            for indice, presente in enumerate(presentes, 1):
                await baixar_documentos_presente_mtproto(
                    cliente, presente, dados, "catalogo_presente_mtproto",
                    f"catalogo_presente_mtproto_{indice:04d}"
                )
    except errors.UnauthorizedError:
        raise
    except (errors.RPCError, OSError, BotAPIRequestError) as erro:
        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
        dados.setdefault("falhas_coleta", []).append({
            "method": metodo,
            "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro),
        })
        dados.setdefault("notas", []).append(
            f"{metodo} indisponível nesta sessão: {type(erro).__name__}."
        )


async def coletar_boosts_mtproto(cliente, dados, entidade):
    canal = input_peer_canal_bot(entidade)
    if canal is None:
        return
    metodo = "premium.getUserBoosts"
    try:
        from telethon.tl.functions.premium import GetUserBoostsRequest
    except ImportError as erro:
        dados.setdefault("falhas_coleta", []).append({
            "method": metodo,
            "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro),
        })
        return
    resultados = dados.setdefault("boosts_por_usuario_mtproto", [])
    ids_com_boosts = ids_participantes_com_boosts_bot_api(dados)
    if not ids_com_boosts:
        dados.setdefault("notas", []).append(
            f"{metodo}: sem chamada individual; a Bot API não retornou boosters."
        )
        return
    for id_usuario in ids_com_boosts:
        try:
            try:
                peer_usuario = utils.get_input_user(
                    cliente.session.get_input_entity(PeerUser(id_usuario))
                )
            except ValueError:
                peer_usuario = InputUser(id_usuario, 0)
            resposta = await com_espera(lambda: cliente(
                GetUserBoostsRequest(peer=canal, user_id=peer_usuario)
            ))
            resultados.append({
                "user_id": id_usuario,
                "response": resposta,
            })
        except errors.UnauthorizedError:
            raise
        except (errors.RPCError, OSError, BotAPIRequestError) as erro:
            print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
            dados.setdefault("falhas_coleta", []).append({
                "method": metodo,
                "user_id": id_usuario,
                "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro),
            })


async def coletar_participacao_bot_mtproto(cliente, dados, entidade):
    canal = input_canal_bot(entidade)
    if canal is None:
        return
    metodo = "channels.getParticipant"
    try:
        from telethon.tl.functions.channels import GetParticipantRequest
        from telethon.tl.types import InputPeerSelf
        resposta = await com_espera(lambda: cliente(
            GetParticipantRequest(channel=canal, participant=InputPeerSelf())
        ))
        dados["participacao_bot_mtproto"] = resposta
    except errors.UnauthorizedError:
        raise
    except (errors.RPCError, OSError, BotAPIRequestError) as erro:
        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
        dados.setdefault("falhas_coleta", []).append({
            "method": metodo,
            "participant": "self",
            "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro),
        })
        dados.setdefault("notas", []).append(
            f"{metodo} para o próprio bot indisponível: {type(erro).__name__}."
        )

async def coletar_presentes_mtproto(cliente, dados, entidade):
    metodo = "payments.getSavedStarGifts"
    try:
        from telethon.tl.functions.payments import GetSavedStarGiftsRequest
    except ImportError as erro:
        dados.setdefault("falhas_coleta", []).append({
            "method": metodo,
            "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro),
        })
        dados.setdefault("notas", []).append(
            f"{metodo} indisponível nesta versão do Telethon."
        )
        return
    if isinstance(entidade, BotAPIEntity):
        id_real, tipo = utils.resolve_id(entidade.id)
        if tipo is PeerChat:
            peer = InputPeerChat(id_real)
        elif tipo is PeerChannel:
            peer = InputPeerChannel(id_real, 0)
        elif tipo is PeerUser:
            peer = InputPeerUser(id_real, 0)
        else:
            dados.setdefault("metodos_nao_aplicaveis", []).append({
                "method": metodo,
                "entity_type": entidade.type,
                "reason": "O ID retornado pela Bot API não representa Chat/Channel para esta chamada.",
            })
            return
    elif not isinstance(entidade, (User, Channel, Chat)):
        dados.setdefault("metodos_nao_aplicaveis", []).append({
            "method": metodo,
            "entity_type": type(entidade).__name__,
            "reason": "payments.getSavedStarGifts exige um peer Telegram conhecido",
        })
        return
    else:
        try:
            peer = await cliente.get_input_entity(entidade)
        except ValueError as erro:
            dados.setdefault("falhas_coleta", []).append({
                "method": metodo,
                "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro),
            })
            return
    try:
        offset = ""
        offsets_vistos = set()
        total = None
        recebidos = 0
        indice_gift = 0
        respostas = dados.setdefault("presentes_star_gifts_mtproto", [])
        paginas = dados.setdefault("paginas_presentes_star_gifts_mtproto", [])
        while True:
            resposta = await com_espera(lambda: cliente(
                GetSavedStarGiftsRequest(peer=peer, offset=offset, limit=100)
            ))
            respostas.append(resposta)
            presentes = getattr(resposta, "gifts", []) or []
            contagem = getattr(resposta, "count", None)
            if isinstance(contagem, int):
                total = contagem if total is None else max(total, contagem)
            proximo = getattr(resposta, "next_offset", None) or ""
            paginas.append({
                "method": metodo,
                "offset": offset,
                "next_offset": proximo,
                "count": contagem,
                "received": len(presentes),
            })
            recebidos += len(presentes)
            if dados.get("midias_dir"):
                for presente in presentes:
                    indice_gift += 1
                    gift = getattr(presente, "gift", None)
                    if gift is not None:
                        await baixar_documentos_presente_mtproto(
                            cliente, gift, dados, "presente_mtproto",
                            f"presente_mtproto_{indice_gift:04d}"
                        )
            if not proximo:
                break
            if proximo == offset or proximo in offsets_vistos:
                dados.setdefault("coletas_incompletas", []).append({
                    "method": metodo,
                    "expected": total,
                    "received": recebidos,
                    "reason": "next_offset repetido; paginação interrompida para evitar ciclo",
                })
                dados.setdefault("notas", []).append(
                    f"{metodo}: paginação interrompida porque next_offset repetiu."
                )
                break
            offsets_vistos.add(offset)
            offset = proximo
    except errors.UnauthorizedError:
        raise
    except (errors.RPCError, OSError, BotAPIRequestError) as erro:
        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
        dados.setdefault("falhas_coleta", []).append({
            "method": metodo,
            "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro),
        })
        dados.setdefault("notas", []).append(
            f"{metodo}: coleta interrompida por {type(erro).__name__}."
        )
    registrar_paginacao_incompleta(
        dados, metodo, total if "total" in locals() else None,
        recebidos if "recebidos" in locals() else 0
    )


async def coletar_historico_canal_pessoal(cliente, dados, entidade):
    metodo = "messages.getPersonalChannelHistory"
    try:
        from telethon.tl.functions.messages import GetPersonalChannelHistoryRequest
    except ImportError as erro:
        dados.setdefault("falhas_coleta", []).append({
            "method": metodo,
            "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro),
        })
        dados.setdefault("notas", []).append(
            f"{metodo} indisponível nesta versão do Telethon."
        )
        return
    entidade_usuario_bot_api = isinstance(entidade, BotAPIEntity) and entidade.type == "private"
    if not isinstance(entidade, User) and not entidade_usuario_bot_api:
        dados.setdefault("metodos_nao_aplicaveis", []).append({
            "method": metodo,
            "entity_type": type(entidade).__name__,
            "reason": "O método consulta o canal pessoal associado a um usuário.",
        })
        return
    user_peer = entidade if isinstance(entidade, User) else InputUser(entidade.id, 0)
    perfil_completo = dados.get("completo")
    if perfil_completo is not None and not getattr(perfil_completo, "personal_channel_id", None):
        dados.setdefault("metodos_nao_aplicaveis", []).append({
            "method": metodo,
            "entity_type": type(entidade).__name__,
            "reason": "users.getFullUser não retornou personal_channel_id para este perfil.",
        })
        return

    cursor = 0
    total = None
    total_inexato = False
    recebidos = 0
    ids_vistos = set()
    paginas = dados.setdefault("historico_canal_pessoal_mtproto", [])
    try:
        while True:
            resposta = await com_espera(lambda: cliente(
                GetPersonalChannelHistoryRequest(
                    user_id=user_peer,
                    limit=100,
                    max_id=cursor,
                    min_id=0,
                    hash=0,
                )
            ))
            paginas.append(resposta)
            mensagens = getattr(resposta, "messages", []) or []
            contagem = getattr(resposta, "count", None)
            if getattr(resposta, "inexact", False):
                if not total_inexato:
                    dados.setdefault("notas", []).append(
                        f"{metodo}: count marcado inexact; a paginação segue pelo cursor até resposta vazia."
                    )
                total_inexato = True
            elif isinstance(contagem, int) and not total_inexato:
                total = contagem if total is None else max(total, contagem)
            if not mensagens:
                break

            novas = []
            for mensagem in mensagens:
                id_mensagem = getattr(mensagem, "id", None)
                if isinstance(id_mensagem, int) and id_mensagem not in ids_vistos:
                    ids_vistos.add(id_mensagem)
                    novas.append(mensagem)
            recebidos += len(novas)
            if dados.get("midias_dir"):
                for mensagem in novas:
                    if getattr(mensagem, "media", None):
                        await baixar_midia(
                            cliente,
                            mensagem,
                            dados,
                            "historico_canal_pessoal",
                            f"historico_canal_pessoal_{getattr(mensagem, 'id', recebidos)}",
                        )

            ids_pagina = [
                id_mensagem for id_mensagem in
                (getattr(mensagem, "id", None) for mensagem in mensagens)
                if isinstance(id_mensagem, int) and id_mensagem > 0
            ]
            if not ids_pagina:
                dados.setdefault("coletas_incompletas", []).append({
                    "method": metodo,
                    "expected": total,
                    "received": recebidos,
                    "reason": "A resposta não trouxe IDs de mensagem para avançar a paginação.",
                })
                break
            proximo_cursor = min(ids_pagina)
            if not novas or proximo_cursor <= 0 or (cursor and proximo_cursor >= cursor):
                dados.setdefault("coletas_incompletas", []).append({
                    "method": metodo,
                    "expected": total,
                    "received": recebidos,
                    "reason": "A página não avançou para IDs de mensagem anteriores.",
                })
                break
            if not total_inexato and total is not None and recebidos >= total:
                if recebidos == total:
                    break
                total_inexato = True
                dados.setdefault("notas", []).append(
                    f"{metodo}: count ({total}) menor que mensagens distintas ({recebidos}); a paginação segue pelo cursor."
                )
            cursor = proximo_cursor
    except errors.UnauthorizedError:
        raise
    except (errors.RPCError, OSError, BotAPIRequestError) as erro:
        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
        dados.setdefault("falhas_coleta", []).append({
            "method": metodo,
            "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro),
        })
        dados.setdefault("notas", []).append(
            f"{metodo}: coleta interrompida por {type(erro).__name__}."
        )
    registrar_paginacao_incompleta(
        dados, metodo, None if total_inexato else total, recebidos
    )


async def coletar_bot_api(dados, entidade, info):
    chat_id = info.get("id")
    if not chat_id:
        return
    respostas_chat = dados.get("respostas_bot_api", {}).get("getChat", [])
    chat = None
    if str(dados.get("getChat_alvo_id")) == str(info.get("id")) and dados.get("getChat_alvo_attempted"):
        chat = respostas_chat[-1] if respostas_chat else None
    else:
        chat = next((resposta for resposta in reversed(respostas_chat)
            if resposta.get("ok") and str((resposta.get("result") or {}).get("id")) == str(info.get("id"))), None)
    if chat is None:
        chat = await bot_api_leitura(dados, "getChat", {"chat_id": chat_id})
    if chat.get("ok"):
        dados["chat_bot_api"] = chat.get("result")
        resultado_chat = chat.get("result") or {}
        foto = resultado_chat.get("photo") or {}
        if foto.get("big_file_id"):
            await baixar_arquivo_bot_api(
                dados, foto["big_file_id"], "foto_perfil_bot_api",
                foto.get("big_file_unique_id")
            )
        audio = resultado_chat.get("first_profile_audio") or {}
        if audio.get("file_id"):
            await baixar_arquivo_bot_api(
                dados, audio["file_id"], "audio_perfil_bot_api",
                audio.get("file_unique_id")
            )
        await baixar_arquivos_bot_api(dados, resultado_chat, "chat_bot_api")
        if resultado_chat.get("is_forum"):
            icones_forum = await bot_api_leitura(dados, "getForumTopicIconStickers", {})
            if icones_forum.get("ok"):
                await baixar_arquivos_bot_api(
                    dados, icones_forum.get("result"), "icones_topico_forum_bot_api"
                )
        ids_relacionados = []
        for chave in ("personal_chat", "parent_chat"):
            relacionado = resultado_chat.get(chave)
            id_relacionado = relacionado.get("id") if isinstance(relacionado, dict) else None
            if isinstance(id_relacionado, int):
                ids_relacionados.append(id_relacionado)
        id_vinculado = resultado_chat.get("linked_chat_id")
        if isinstance(id_vinculado, int):
            ids_relacionados.append(id_vinculado)
        id_atual = info.get("id")
        ids_relacionados = list(dict.fromkeys(
            identificador for identificador in ids_relacionados
            if identificador != id_atual
        ))
        for id_relacionado in ids_relacionados:
            resposta_relacionada = await bot_api_leitura(
                dados, "getChat", {"chat_id": id_relacionado}
            )
            if not resposta_relacionada.get("ok"):
                continue
            chat_relacionado = resposta_relacionada.get("result") or {}
            dados.setdefault("chats_relacionados_bot_api", []).append(chat_relacionado)
            foto_relacionada = chat_relacionado.get("photo") or {}
            if foto_relacionada.get("big_file_id"):
                await baixar_arquivo_bot_api(
                    dados, foto_relacionada["big_file_id"], "foto_chat_relacionado_bot_api",
                    foto_relacionada.get("big_file_unique_id")
                )
            audio_relacionado = chat_relacionado.get("first_profile_audio") or {}
            if audio_relacionado.get("file_id"):
                await baixar_arquivo_bot_api(
                    dados, audio_relacionado["file_id"], "audio_chat_relacionado_bot_api",
                    audio_relacionado.get("file_unique_id")
                )
            await baixar_arquivos_bot_api(dados, chat_relacionado, "chat_relacionado_bot_api")

    entidade_usuario = isinstance(entidade, User) or (
        isinstance(entidade, BotAPIEntity) and entidade.type == "private"
    )
    if entidade_usuario:
        id_usuario = entidade.id
        for metodo, lista_chave, categoria in (
            ("getUserProfilePhotos", "photos", "foto_perfil_bot_api"),
            ("getUserProfileAudios", "audios", "audio_perfil_bot_api"),
        ):
            offset = 0
            total = None
            while True:
                resposta = await bot_api_leitura(
                    dados, metodo, {"user_id": id_usuario, "offset": offset, "limit": 100}
                )
                if not resposta.get("ok"):
                    break
                resultado = resposta.get("result") or {}
                contagem = resultado.get("total_count")
                if isinstance(contagem, int):
                    total = contagem if total is None else max(total, contagem)
                itens = resultado.get(lista_chave) or []
                if not itens:
                    break
                for item in itens:
                    if metodo == "getUserProfilePhotos":
                        if not item:
                            continue
                        item = max(item, key=lambda foto: (
                            foto.get("width", 0) * foto.get("height", 0),
                            foto.get("file_size", 0)
                        ))
                    await baixar_arquivo_bot_api(
                        dados, item.get("file_id"), categoria, item.get("file_unique_id")
                    )
                offset += len(itens)
                if total is not None and offset >= total:
                    break
            registrar_paginacao_incompleta(dados, metodo, total, offset)
        mensagens = await bot_api_leitura(
            dados, "getUserPersonalChatMessages", {"user_id": id_usuario, "limit": 20}
        )
        if mensagens.get("ok"):
            for mensagem in mensagens.get("result") or []:
                for categoria, valor in (mensagem or {}).items():
                    if categoria == "photo" and isinstance(valor, list):
                        if valor:
                            foto = max(valor, key=lambda item: (
                                item.get("width", 0) * item.get("height", 0),
                                item.get("file_size", 0)
                            ))
                            await baixar_arquivo_bot_api(
                                dados, foto.get("file_id"), "mensagem_foto_bot_api",
                                foto.get("file_unique_id")
                            )
                    elif categoria in ("audio", "document", "animation", "video", "video_note", "voice", "sticker", "live_photo") and isinstance(valor, dict):
                        await baixar_arquivo_bot_api(
                            dados, valor.get("file_id"), "mensagem_" + categoria + "_bot_api",
                            valor.get("file_unique_id")
                        )
                await baixar_arquivos_bot_api(dados, mensagem, "mensagem_pessoal_bot_api")
    else:
        await coletar_estado_bot_no_chat(dados, chat_id)
        await bot_api_leitura(
            dados, "getChatAdministrators", {"chat_id": chat_id, "return_bots": True}
        )
        await bot_api_leitura(dados, "getChatMemberCount", {"chat_id": chat_id})
        if MODO == "completo":
            await coletar_dados_participante_bot_api(dados, entidade, chat_id)

    await coletar_stickers_bot_api(dados, dados.get("respostas_bot_api", {}))
    if MODO == "completo":
        await coletar_presentes_bot_api(dados, entidade, chat_id)


async def baixar_midia(cliente, objeto, dados, categoria, nome):
    caminho = os.path.join(dados["midias_dir"], nome)
    try:
        retorno = await com_espera(lambda: cliente.download_media(objeto, file=caminho))
        if isinstance(retorno, str) and os.path.isfile(retorno):
            item = registrar_midia(dados, categoria, os.path.basename(retorno), retorno)
            from telethon.tl.types import Document
            if isinstance(objeto, Document):
                dados.setdefault("_documentos_mtproto_processados", set()).add(objeto.id)
            return item
        return registrar_midia(dados, categoria, nome, status="unavailable", erro="Telegram não retornou o arquivo")
    except errors.UnauthorizedError:
        raise
    except (errors.RPCError, OSError, BotAPIRequestError) as erro:
        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
        return registrar_midia(dados, categoria, nome, status="failed", erro=type(erro).__name__)


def enviar_documento_arquivo(chat, caminho, id_entidade, indice, total):
    with open(caminho, "rb") as arquivo:
        conteudo = arquivo.read()
    limite = uuid.uuid4().hex
    filename = "infocard_" + str(id_entidade).replace("-", "n") + "_midias"
    if total > 1:
        filename += f"_parte_{indice}_de_{total}"
    filename += ".zip"
    resumo_hash = hashlib.sha256(conteudo).hexdigest()
    campos = {"chat_id": str(int(chat)), "caption": "🖼️ Mídia Telegram exportada" +
              (f" · parte {indice}/{total}" if total > 1 else "") +
              "\nSHA-256: " + resumo_hash}
    if ORIGEM_ID:
        campos["reply_parameters"] = json.dumps({"message_id": ORIGEM_ID})
    partes = []
    for chave, valor in campos.items():
        partes.append((f'--{limite}\r\nContent-Disposition: form-data; name="{chave}"'
                       f'\r\n\r\n{valor}\r\n').encode("utf-8"))
    partes.extend([
        (f'--{limite}\r\nContent-Disposition: form-data; name="document"; '
         f'filename="{filename}"\r\nContent-Type: application/zip'
         f'\r\n\r\n').encode("utf-8"),
        conteudo,
        f'\r\n--{limite}--\r\n'.encode("utf-8"),
    ])
    resposta = chamar("sendDocument", b"".join(partes),
                     {"Content-Type": f"multipart/form-data; boundary={limite}"})
    if not aceitacao_mensagem(resposta):
        raise BotAPIRequestError("sendDocument", resposta)
    print(f"pacote de mídia {indice}/{total} confirmado: {len(conteudo)} bytes")

def enviar_documento_jsonl(chat, conteudo, id_entidade, indice, total):
    limite = uuid.uuid4().hex
    filename = "infocard_" + str(id_entidade).replace("-", "n") + "_telegram"
    if total > 1:
        filename += f"_parte_{indice}_de_{total}"
    filename += ".jsonl"
    resumo_hash = hashlib.sha256(conteudo).hexdigest()
    campos = {"chat_id": str(int(chat)), "caption": "🧾 Respostas Telegram coletadas (JSONL)" +
              (f" · parte {indice}/{total}" if total > 1 else "") +
              "\nSHA-256: " + resumo_hash}
    if ORIGEM_ID:
        campos["reply_parameters"] = json.dumps({"message_id": ORIGEM_ID})
    partes = []
    for chave, valor in campos.items():
        partes.append((f'--{limite}\r\nContent-Disposition: form-data; name="{chave}"'
                       f'\r\n\r\n{valor}\r\n').encode("utf-8"))
    partes.extend([
        (f'--{limite}\r\nContent-Disposition: form-data; name="document"; '
         f'filename="{filename}"\r\nContent-Type: application/x-ndjson'
         f'\r\n\r\n').encode("utf-8"),
        conteudo,
        f'\r\n--{limite}--\r\n'.encode("utf-8"),
    ])
    resposta = chamar("sendDocument", b"".join(partes),
                     {"Content-Type": f"multipart/form-data; boundary={limite}"})
    if not aceitacao_mensagem(resposta):
        raise BotAPIRequestError("sendDocument", resposta)
    print(f"documento JSONL {indice}/{total} confirmado: {len(conteudo)} bytes")

def botao_atualizar(alvo):
    dados = callback_data("r", alvo)
    return ('<tg-button type="callback_data" style="primary" data="' +
            esc(dados) + '">🔄 Atualizar</tg-button>') if dados else ""


def status_ficha(etapa, nome=None, id_entidade=None):
    linhas = ['<tr><th>Etapa</th><td>' + esc(etapa) + '</td></tr>']
    if nome:
        linhas.append('<tr><th>Nome</th><td>' + esc(corte(nome, 100)) + '</td></tr>')
    if id_entidade is not None:
        linhas.append('<tr><th>ID</th><td><code>' + esc(id_entidade) + '</code></td></tr>')
    return ('<h2>🔎 Infocard</h2><p><b>⏳ Consulta MTProto em andamento</b></p>'
            '<table compact bordered><tr><th>Campo</th><th>Valor</th></tr>'
            + ''.join(linhas) + '</table><footer>Fonte: Telegram Bot API + MTProto</footer>')


def atualizar_status(etapa, entidade=None):
    if not ID_MENSAGEM or not CHAT_DESTINO:
        return
    nome = None
    id_entidade = None
    if entidade is not None:
        nome = getattr(entidade, "title", None) or " ".join(
            parte for parte in [getattr(entidade, "first_name", None), getattr(entidade, "last_name", None)] if parte
        )
        id_entidade = id_peer(entidade)
    if FORMATO_MENSAGEM == "html":
        resposta = solicitar_bot_api("editMessageText", {
            "chat_id": int(CHAT_DESTINO), "message_id": ID_MENSAGEM,
            "text": "<b>Consulta em andamento</b>\n" + esc(etapa), "parse_mode": "HTML",
        })
        if mensagem_inalterada(resposta):
            print("editMessageText: estado HTML já está atualizado")
        elif not aceitacao_mensagem(resposta):
            raise BotAPIRequestError("editMessageText", resposta)
    else:
        editar_ficha_rica(status_ficha(etapa, nome, id_entidade))


CATEGORIAS = (
    ("👤 Perfil e atividade", (
        "Bio", "Bio (Bot API)", "Aniversário", "Aniversário (Bot API)", "Idioma", "Premium", "Restrições", "Chats em comum",
        "Canal pessoal", "Nome nos encaminhamentos", "Mensagens de voz",
        "Emoji de status", "Fotos de perfil no MTProto",
    )),
    ("🎵 Recursos e presença", (
        "Música destacada no perfil", "Músicas de perfil no MTProto", "Fotos de perfil na Bot API",
        "Áudios de perfil na Bot API", "Mensagens no chat pessoal via Bot API",
        "Administradores via Bot API", "Membros via Bot API", "Presentes recebidos",
        "Nível Telegram Stars", "Placeholder inline", "Usuários ativos do bot",
        "Mini App principal do bot", "Descrição do bot", "Comandos",
        "Política de privacidade",
    )),
    ("🏢 Informações comerciais", (
        "Intro comercial", "Endereço comercial", "Fuso dos horários comerciais",
        "Intervalos de atendimento registrados",
    )),
    ("📢 Canal ou grupo", (
        "Descrição", "Descrição (Bot API)", "Intro comercial (Bot API)",
        "Local comercial (Bot API)", "Horários comerciais (Bot API)",
        "Avaliação do chat (Bot API)", "Membros", "Administradores", "Online agora",
        "Chat vinculado", "Modo lento", "Boosts aplicados",
        "Nível de boosts do canal", "Presentes recebidos pelo canal",
        "Limite de reações distintas", "Localização",
    )),
)


def agrupar_campos(info):
    restantes = list(info["campos"])
    grupos = []
    for nome_grupo, rotulos in CATEGORIAS:
        encontrados = [campo for campo in restantes if campo[0] in rotulos]
        if encontrados:
            grupos.append((nome_grupo, encontrados))
            restantes = [campo for campo in restantes if campo[0] not in rotulos]
    if restantes:
        grupos.append(("➕ Outros dados retornados", restantes))
    return grupos


def dados_basicos(info):
    linhas = [
        ("Tipo", info["tipo"]),
        ("ID", str(info["id"])),
        ("Nome", info["nome"] or "Não informado"),
    ]
    if info["username"]:
        linhas.append(("Username", "@" + info["username"]))
    if info["usernames"]:
        linhas.append(("Outros usernames ativos", ", ".join("@" + u for u in info["usernames"])))
    if info["marcas"]:
        linhas.append(("Indicadores públicos", ", ".join(info["marcas"])))
    linhas.append(("Foto de perfil", "Disponível" if info["foto"] else "Não informada"))
    return linhas


def ficha_falha(alvo, motivo):
    linhas = '<tr><th>Consulta</th><td>' + esc(f"{EXPECTED_ID} @{alvo}" if EXPECTED_ID else (alvo if re.fullmatch(r"-?\d{1,16}", alvo) else f"@{alvo}")) + '</td></tr>'
    linhas += '<tr><th>Resultado</th><td>' + esc(corte(motivo, 600)) + '</td></tr>'
    return ('<h2>📇 Infocard</h2><p><b>⚠️ Busca não concluída</b></p>'
            '<table bordered compact><tr><th>Campo</th><th>Valor</th></tr>' + linhas +
            '</table><p><i>Uma referência não encontrada não prova inexistência da conta.</i></p>'
            '<tg-button-row>' + botao_atualizar(alvo) + '</tg-button-row>')


def entidade_de(resultado):
    esperado = utils.get_peer_id(resultado.peer)
    return next((entidade for entidade in [*resultado.users, *resultado.chats]
                 if isinstance(entidade, (User, Channel, Chat)) and utils.get_peer_id(entidade) == esperado), None)


async def completo(cliente, entidade):
    if isinstance(entidade, User):
        return await cliente(GetFullUserRequest(input_usuario_bot(entidade)))
    if isinstance(entidade, Channel):
        return await cliente(GetFullChannelRequest(input_canal_bot(entidade)))
    if isinstance(entidade, Chat):
        return await cliente(GetFullChatRequest(entidade.id))
    if isinstance(entidade, BotAPIEntity):
        usuario = input_usuario_bot(entidade)
        if usuario is not None:
            return await cliente(GetFullUserRequest(usuario))
        canal = input_canal_bot(entidade)
        if canal is not None:
            return await cliente(GetFullChannelRequest(canal))
        if entidade.type == "group":
            id_real, tipo = utils.resolve_id(entidade.id)
            if tipo is PeerChat:
                return await cliente(GetFullChatRequest(id_real))
    return None


def objeto_completo(resposta):
    if resposta is None:
        return None
    return getattr(resposta, "full_user", None) or getattr(resposta, "full_chat", None)


def valor_mtproto(valor):
    return valor_exportavel(valor)


def registros_telegram(dados, alvo, info):
    metadados = {
        "formato": "infocard-telegram-jsonl-v3",
        "redaction": {"marker": "[redigido]", "fields": sorted(CAMPOS_SIGILOSOS)},
        "escopo": "respostas de leitura obtidas pelas APIs do Telegram nesta execução",
        "apis": ["Bot API", "MTProto"],
        "telethon": telethon.__version__,
        "referencia": alvo,
        "tipo": info.get("tipo"),
        "capturado_unix": int(time.time()),
    }
    objetos = {
        "metadados": metadados,
        "respostas_bot_api": dados.get("respostas_bot_api", {}),
        "coletas_incompletas": dados.get("coletas_incompletas", []),
        "chats_relacionados_bot_api": dados.get("chats_relacionados_bot_api", []),
        "estado_bot_no_chat": dados.get("estado_bot_no_chat", {}),
        "falhas_bot_api": dados.get("falhas_bot_api", []),
        "metodos_nao_aplicaveis": dados.get("metodos_nao_aplicaveis", []),
        "entidade": dados.get("entidade"),
        "resposta_resolucao": dados.get("resposta_resolucao"),
        "resposta_completa": dados.get("resposta_completa"),
        "mensagens_fixadas_mtproto": dados.get("mensagens_fixadas_mtproto", []),
        "participacao_bot_mtproto": dados.get("participacao_bot_mtproto"),
        "historico_canal_pessoal_mtproto": dados.get("historico_canal_pessoal_mtproto", []),
        "fotos_perfil": dados.get("fotos_mtproto", []),
        "musicas_perfil": dados.get("musicas_mtproto", []),
        "emojis_personalizados_mtproto": dados.get("emojis_personalizados_mtproto", []),
        "conjuntos_stickers_mtproto": dados.get("conjuntos_stickers_mtproto", []),
        "topicos_forum_mtproto": dados.get("topicos_forum_mtproto", []),
        "participantes": dados.get("participantes_mtproto", []),
        "participantes_filtrados": dados.get("participantes_filtrados_mtproto", {}),
        "membros_bot_api_por_participante": dados.get("membros_bot_api_por_participante", []),
        "boosts_por_participante": dados.get("boosts_por_participante_bot_api", []),
        "presentes_bot_api": dados.get("presentes_bot_api", []),
        "catalogo_presentes_bot_api": dados.get("catalogo_presentes_bot_api", {}),
        "catalogo_presentes_star_gifts_mtproto": dados.get("catalogo_presentes_star_gifts_mtproto", []),
        "paginas_presentes_star_gifts_mtproto": dados.get("paginas_presentes_star_gifts_mtproto", []),
        "respostas_presentes_star_gifts_mtproto": dados.get("presentes_star_gifts_mtproto", []),
        "status_boosts_mtproto": dados.get("status_boosts_mtproto", []),
        "paginas_boosters_mtproto": dados.get("paginas_boosters_mtproto", []),
        "boosters_mtproto": dados.get("boosters_mtproto", []),
        "boosts_por_usuario_mtproto": dados.get("boosts_por_usuario_mtproto", []),
        "midias": [{chave: valor for chave, valor in item.items() if chave != "path"} for item in dados.get("midias", [])],
        "metodos_com_falha": dados.get("falhas_coleta", []),
    }
    def folhas(valor, caminho):
        serializado = valor_mtproto(valor)
        if isinstance(serializado, dict):
            if not serializado:
                yield {"path": caminho, "value": {}}
            for chave in sorted(serializado):
                novo = f"{caminho}.{chave}" if caminho else chave
                yield from folhas(serializado[chave], novo)
        elif isinstance(serializado, list):
            if not serializado:
                yield {"path": caminho, "value": []}
            for indice, item in enumerate(serializado):
                yield from folhas(item, f"{caminho}[{indice}]")
        else:
            yield {"path": caminho, "value": serializado}
    for caminho, valor in objetos.items():
        yield from folhas(valor, caminho)


def secoes_completas_telegram(dados, alvo, info):
    titulos = {
        "metadados": "Metadados da coleta",
        "respostas_bot_api": "Bot API · respostas completas",
        "coletas_incompletas": "Paginação incompleta",
        "chats_relacionados_bot_api": "Bot API · chats relacionados",
        "estado_bot_no_chat": "Bot API · status do bot no chat",
        "falhas_bot_api": "Bot API · erros retornados",
        "metodos_nao_aplicaveis": "Métodos não aplicáveis ao tipo de entidade",
        "entidade": "MTProto · entidade resolvida",
        "resposta_resolucao": "MTProto · resposta da resolução",
        "resposta_completa": "MTProto · perfil completo",
        "mensagens_fixadas_mtproto": "MTProto · mensagens fixadas",
        "participacao_bot_mtproto": "MTProto · participação do próprio bot",
        "historico_canal_pessoal_mtproto": "MTProto · histórico do canal pessoal",
        "fotos_perfil": "MTProto · fotos de perfil",
        "musicas_perfil": "MTProto · músicas de perfil",
        "emojis_personalizados_mtproto": "MTProto · emojis personalizados referenciados",
        "conjuntos_stickers_mtproto": "MTProto · conjuntos de stickers referenciados",
        "topicos_forum_mtproto": "MTProto · tópicos de fórum conhecidos",
        "participantes": "MTProto · participantes recentes",
        "participantes_filtrados": "MTProto · participantes por filtro",
        "membros_bot_api_por_participante": "Bot API · estado de participantes",
        "boosts_por_participante": "Bot API · boosts por participante",
        "presentes_bot_api": "Bot API · paginação de presentes",
        "catalogo_presentes_bot_api": "Bot API · catálogo global de presentes",
        "catalogo_presentes_star_gifts_mtproto": "MTProto · catálogo global de presentes Star",
        "paginas_presentes_star_gifts_mtproto": "MTProto · paginação de presentes Star",
        "respostas_presentes_star_gifts_mtproto": "MTProto · respostas completas de presentes Star",
        "status_boosts_mtproto": "MTProto · status de boosts",
        "paginas_boosters_mtproto": "MTProto · paginação de boosters",
        "boosters_mtproto": "MTProto · lista completa de boosters",
        "boosts_por_usuario_mtproto": "MTProto · respostas de boosts por usuário",
        "midias": "Mídia · arquivos e estado de download",
        "metodos_com_falha": "MTProto · erros retornados",
    }
    grupos = {}
    for registro in registros_telegram(dados, alvo, info):
        caminho = registro["path"]
        raiz = caminho.split(".", 1)[0].split("[", 1)[0]
        titulo = titulos.get(raiz, "Dados completos · " + raiz)
        relativo = caminho[len(raiz):].lstrip(".")
        valor = registro["value"]
        texto = valor if isinstance(valor, str) else json.dumps(
            valor, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        )
        grupos.setdefault(titulo, []).append((relativo or raiz, texto))
    return list(grupos.items())



async def com_espera(operacao):
    while True:
        try:
            return await operacao()
        except errors.FloodWaitError as erro:
            print("MTProto: aguardando FLOOD_WAIT", erro.seconds, "s")
            await asyncio.sleep(erro.seconds)


async def resolver_id(cliente, id_marcado):
    if tipo_dialogo(id_marcado) is None:
        raise LookupError("ID fora do intervalo aceito pelo Telegram.")

    id_real, tipo = utils.resolve_id(id_marcado)
    try:
        if tipo is PeerUser:
            try:
                referencia = utils.get_input_user(cliente.session.get_input_entity(PeerUser(id_real)))
            except ValueError:
                referencia = InputUser(id_real, 0)
            candidatos = await com_espera(lambda: cliente(GetUsersRequest([referencia])))
            entidade = next((u for u in candidatos if isinstance(u, User) and u.id == id_real), None)
        elif tipo is PeerChannel:
            try:
                referencia = utils.get_input_channel(cliente.session.get_input_entity(PeerChannel(id_real)))
            except ValueError:
                referencia = InputChannel(id_real, 0)
            candidatos = await com_espera(lambda: cliente(GetChannelsRequest([referencia])))
            entidade = next((c for c in candidatos.chats if isinstance(c, Channel) and c.id == id_real), None)
        elif tipo is PeerChat:
            candidatos = await com_espera(lambda: cliente(GetChatsRequest([id_real])))
            entidade = next((c for c in candidatos.chats if isinstance(c, Chat) and c.id == id_real), None)
        else:
            entidade = None
    except (errors.FloodWaitError, errors.UnauthorizedError):
        raise
    except errors.RPCError as erro:
        raise LookupError(
            "O Telegram não permitiu resolver este ID sem contexto suficiente "
            f"({type(erro).__name__}). Use 'ID @username' para uma referência pública "
            "verificável ou compartilhe o usuário pelo botão oficial do Telegram."
        ) from erro
    if entidade is None:
        raise LookupError(
            "O Telegram não retornou uma entidade acessível para este ID. "
            "Experimente 'ID @username' ou compartilhe o usuário como referência."
        )
    return entidade, candidatos


async def resolver_alvo(cliente, alvo):
    if re.fullmatch(r"-?\d{1,16}", alvo):
        if tipo_dialogo(str(int(alvo))) is None:
            raise ValueError("ID fora do intervalo aceito pelo Telegram.")
        if EXPECTED_ID:
            raise ValueError("ID esperado exige um username público para a verificação.")
        try:
            entidade, resposta = await resolver_id(cliente, int(alvo))
            return entidade, "Consulta MTProto por ID, sujeita às permissões do Telegram", resposta
        except LookupError as erro_mtproto:
            resposta_bot = await asyncio.to_thread(
                chamar,
                "getChat",
                json.dumps({"chat_id": int(alvo)}).encode("utf-8"),
                {"Content-Type": "application/json"},
            )
            migracoes = resposta_bot.get("migrations") or []
            id_confirmado = migracoes[-1]["to"] if migracoes else int(alvo)
            chat = resposta_bot.get("result")
            chat = chat if isinstance(chat, dict) else {}
            if resposta_bot.get("ok") and (type(chat.get("id")) is not int or chat["id"] != id_confirmado
                                            or chat.get("type") not in ("private", "group", "supergroup", "channel")):
                resposta_bot = {"ok": False, "error_code": 0, "description": "getChat retornou uma entidade inválida ou divergente do ID solicitado."}
                chat = {}
            if resposta_bot.get("ok") and chat.get("id") == id_confirmado and chat.get("type") in (
                "private", "group", "supergroup", "channel"
            ):
                username = chat.get("username")
                if username:
                    try:
                        resolvido = await com_espera(
                            lambda: cliente(ResolveUsernameRequest(username))
                        )
                        entidade = entidade_de(resolvido)
                        if entidade is not None and utils.get_peer_id(entidade) == int(chat["id"]):
                            return entidade, "ID confirmado por Bot API getChat e MTProto username", {
                                "bot_api_getChat": resposta_bot,
                                "mtproto_username_resolution": resolvido,
                            }
                    except errors.UnauthorizedError:
                        raise
                    except (errors.RPCError, OSError) as erro_username:
                        resposta_bot["mtproto_username_error"] = diagnostico_api({
                            "error_code": getattr(erro_username, "code", 0),
                            "description": getattr(erro_username, "message", type(erro_username).__name__),
                        }, "contacts.resolveUsername")
                        print(json.dumps(resposta_bot["mtproto_username_error"], ensure_ascii=False))
                return BotAPIEntity(chat), (
                    "ID confirmado pela Bot API após MTProto não resolver; leituras MTProto compatíveis serão tentadas com access_hash zero: "
                    + str(erro_mtproto)
                ), {"bot_api_getChat": resposta_bot, "bot_api_getChat_attempted": True, "mtproto_error": str(erro_mtproto)}
            diagnostico = diagnostico_api(resposta_bot, "getChat")
            print(json.dumps(diagnostico, ensure_ascii=False))
            raise LookupError(
                "A entidade não foi confirmada pelas APIs. " + str(erro_mtproto) +
                " Bot API: " + str(diagnostico["error_code"]) + " " + diagnostico["description"]
            ) from erro_mtproto
    resultado = await com_espera(lambda: cliente(ResolveUsernameRequest(alvo)))
    entidade = entidade_de(resultado)
    if entidade is None:
        raise LookupError("O Telegram não retornou uma entidade para o username.")
    if EXPECTED_ID:
        if utils.get_peer_id(entidade) != int(EXPECTED_ID):
            raise LookupError("O username foi resolvido, mas o ID retornado pelo Telegram não corresponde ao ID esperado.")
        return entidade, "ID confirmado por contacts.resolveUsername", resultado
    return entidade, "Referência obtida por contacts.resolveUsername", resultado

async def coletar(alvo):
    temporaria = None
    pasta_sessao = os.environ.get("TELETHON_SESSION_DIR")
    if not pasta_sessao:
        temporaria = tempfile.TemporaryDirectory(prefix="infocard_session_")
        pasta_sessao = temporaria.name
    os.makedirs(pasta_sessao, mode=0o700, exist_ok=True)
    os.chmod(pasta_sessao, 0o700)
    bot_token = os.environ["BOT_TOKEN"]
    nome_sessao = hashlib.sha256(bot_token.encode()).hexdigest()
    sessao = SQLiteSession(os.path.join(pasta_sessao, nome_sessao))
    cliente = None
    try:
        cliente = TelegramClient(sessao, int(os.environ["API_ID"]), os.environ["API_HASH"])
        await com_espera(lambda: cliente.start(bot_token=bot_token))
        print("Autenticação concluída pelo Telethon")
        entidade, origem, resposta_resolucao = await resolver_alvo(cliente, alvo)
        dados = {"entidade": entidade, "completo": None, "resposta_completa": None, "resposta_resolucao": resposta_resolucao, "foto": None, "notas": [origem], "fotos_info": None, "musicas_info": None, "fotos_mtproto": [], "musicas_mtproto": [], "participantes_mtproto": [], "participantes_filtrados_mtproto": {}, "midias": [], "pacotes_midias": [], "falhas_coleta": [], "coletas_incompletas": [], "respostas_bot_api": {}, "falhas_bot_api": [], "mensagens_fixadas_mtproto": [], "midias_dir": tempfile.mkdtemp(prefix="infocard_telegram_") if MODO == "completo" and (CHAT_DESTINO or os.environ.get("COLETAR_MIDIA") == "true") else None}
        if isinstance(entidade, BotAPIEntity) and resposta_resolucao.get("mtproto_error"):
            resposta_chat_bot = resposta_resolucao.get("bot_api_getChat")
            if resposta_chat_bot:
                dados["respostas_bot_api"]["getChat"] = [resposta_chat_bot]
                dados["chat_bot_api"] = resposta_chat_bot.get("result") or {}
            dados["getChat_alvo_attempted"] = bool(resposta_resolucao.get("bot_api_getChat_attempted"))
            dados["getChat_alvo_id"] = entidade.id
            dados["notas"].append(
                "A Bot API confirmou o peer após a resolução MTProto por ID falhar; métodos compatíveis de bot continuam com access_hash zero e cada resposta ou recusa é registrada."
            )
        if dados["midias_dir"]:
            atexit.register(shutil.rmtree, dados["midias_dir"], ignore_errors=True)
        atualizar_status("1/2 · Identificação confirmada; buscando campos adicionais", entidade)
        try:
            dados["resposta_completa"] = await com_espera(lambda: completo(cliente, entidade))
            dados["completo"] = objeto_completo(dados["resposta_completa"])
            if dados["completo"] is None:
                raise APIProtocolError("MTProto getFull", {
                    "error_code": 0, "description": "Resposta sem o perfil completo exigido pelo método",
                    "origin": "protocol",
                })
            mensagem_fixada_id = getattr(dados["completo"], "pinned_msg_id", None)
            if MODO == "completo" and mensagem_fixada_id:
                try:
                    canal = input_canal_bot(entidade)
                    if canal is not None:
                        fixadas = await com_espera(lambda: cliente(GetChannelMessagesRequest(
                            channel=canal, id=[InputMessageID(mensagem_fixada_id)]
                        )))
                    else:
                        fixadas = await com_espera(lambda: cliente(GetMessagesRequest(
                            id=[InputMessageID(mensagem_fixada_id)]
                        )))
                    dados["mensagens_fixadas_mtproto"].append(fixadas)
                    if dados["midias_dir"]:
                        for mensagem in getattr(fixadas, "messages", []) or []:
                            if getattr(mensagem, "media", None):
                                await baixar_midia(
                                    cliente, mensagem, dados, "mensagem_fixada",
                                    f"mensagem_fixada_{getattr(mensagem, 'id', mensagem_fixada_id)}"
                                )
                except errors.UnauthorizedError:
                    raise
                except (errors.RPCError, OSError, BotAPIRequestError) as erro_fixadas:
                    print(json.dumps(diagnostico_excecao(erro_fixadas), ensure_ascii=False))
                    dados["falhas_coleta"].append({
                        "method": "messages.getMessages" if isinstance(entidade, Chat) else "channels.getMessages",
                        "error": type(erro_fixadas).__name__, "diagnostic": diagnostico_excecao(erro_fixadas),
                    })
                    dados["notas"].append(f"Mensagem fixada indisponível: {type(erro_fixadas).__name__}")
        except errors.UnauthorizedError:
            raise
        except (errors.RPCError, OSError, BotAPIRequestError) as erro:
            print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
            dados["falhas_coleta"].append({"method": "getFull", "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro)})
            dados["notas"].append(f"Dados completos indisponíveis: {type(erro).__name__}: {erro}")

        canal = input_canal_bot(entidade)
        if MODO == "completo" and canal is not None:
            filtros_participantes = (
                ("recent", ChannelParticipantsRecent()),
                ("admins", ChannelParticipantsAdmins()),
                ("bots", ChannelParticipantsBots()),
                ("restritos", ChannelParticipantsBanned(q="")),
                ("banidos", ChannelParticipantsKicked(q="")),
            )
            for nome_filtro, filtro_participantes in filtros_participantes:
                offset_participantes = 0
                total_participantes = None
                ids_participantes_vistos = set()
                respostas_filtro = []
                while True:
                    try:
                        pagina_participantes = await com_espera(
                            lambda offset=offset_participantes: cliente(GetParticipantsRequest(
                                channel=canal,
                                filter=filtro_participantes,
                                offset=offset,
                                limit=100,
                                hash=0,
                            ))
                        )
                    except errors.UnauthorizedError:
                        raise
                    except (errors.RPCError, OSError, BotAPIRequestError) as erro_participantes:
                        print(json.dumps(diagnostico_excecao(erro_participantes), ensure_ascii=False))
                        dados["falhas_coleta"].append({
                            "method": "channels.getParticipants",
                            "filter": nome_filtro,
                            "error": type(erro_participantes).__name__, "diagnostic": diagnostico_excecao(erro_participantes),
                        })
                        dados["notas"].append(
                            f"Participantes ({nome_filtro}) indisponíveis: {type(erro_participantes).__name__}"
                        )
                        break
                    respostas_filtro.append(pagina_participantes)
                    contagem = getattr(pagina_participantes, "count", None)
                    if isinstance(contagem, int):
                        total_participantes = contagem if total_participantes is None else max(total_participantes, contagem)
                    lista_participantes = getattr(pagina_participantes, "participants", []) or []
                    if not lista_participantes:
                        break
                    novos = {
                        chave_participante_mtproto(participante)
                        for participante in lista_participantes
                    } - ids_participantes_vistos
                    if not novos:
                        dados["coletas_incompletas"].append({
                            "method": "channels.getParticipants[" + nome_filtro + "]",
                            "expected": total_participantes,
                            "received": len(ids_participantes_vistos),
                            "reason": "A página repetiu participantes sem avançar o conjunto de IDs.",
                        })
                        break
                    ids_participantes_vistos.update(novos)
                    offset_participantes += len(lista_participantes)
                    if total_participantes is not None and len(ids_participantes_vistos) >= total_participantes:
                        if len(ids_participantes_vistos) == total_participantes:
                            break
                        total_participantes = None
                        dados.setdefault("notas", []).append(
                            "channels.getParticipants[" + nome_filtro + "]: count menor que participantes distintos; paginação segue até página vazia."
                        )
                if nome_filtro == "recent":
                    dados["participantes_mtproto"] = respostas_filtro
                else:
                    dados["participantes_filtrados_mtproto"][nome_filtro] = respostas_filtro
                registrar_paginacao_incompleta(
                    dados, "channels.getParticipants[" + nome_filtro + "]",
                    total_participantes, len(ids_participantes_vistos)
                )
        if not isinstance(entidade, BotAPIEntity):
            try:
                dados["foto"] = await com_espera(lambda: cliente.download_profile_photo(entidade, file=bytes))
                if dados["foto"] and dados["midias_dir"]:
                    caminho_foto = os.path.join(dados["midias_dir"], "foto_perfil_atual.jpg")
                    with open(caminho_foto, "wb") as arquivo_foto:
                        arquivo_foto.write(dados["foto"])
                    registrar_midia(dados, "foto_perfil_atual", "foto_perfil_atual.jpg", caminho_foto)
            except errors.UnauthorizedError:
                raise
            except (errors.RPCError, OSError, BotAPIRequestError) as erro:
                print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
                dados["falhas_coleta"].append({"method": "download_profile_photo", "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro)})
                dados["notas"].append(f"Foto não baixada: {type(erro).__name__}: {erro}")
        usuario = input_usuario_bot(entidade)
        if usuario is not None:
            try:
                from telethon.tl.functions.photos import GetUserPhotosRequest
                offset = 0
                total = None
                while True:
                    fotos = await com_espera(
                        lambda offset=offset: cliente(GetUserPhotosRequest(
                            user_id=usuario, offset=offset, max_id=0, limit=(100 if MODO == "completo" else 1)
                        ))
                    )
                    dados["fotos_mtproto"].append(fotos)
                    lista_fotos = getattr(fotos, "photos", []) or []
                    contagem = getattr(fotos, "count", None)
                    if isinstance(contagem, int):
                        total = contagem if total is None else max(total, contagem)
                    if not lista_fotos:
                        break
                    offset += len(lista_fotos)
                    if MODO != "completo":
                        break
                    if total is not None and offset >= total:
                        break
                obtidas = sum(len(getattr(pagina, "photos", []) or []) for pagina in dados["fotos_mtproto"])
                if MODO == "completo":
                    registrar_paginacao_incompleta(dados, "photos.getUserPhotos", total, obtidas)
                if dados["midias_dir"]:
                    fotos_itens = [
                        foto
                        for pagina in dados["fotos_mtproto"]
                        for foto in (getattr(pagina, "photos", []) or [])
                    ]
                    for indice, foto_mtproto in enumerate(fotos_itens, 1):
                        await baixar_midia(
                            cliente, foto_mtproto, dados, "foto_perfil",
                            f"foto_perfil_{indice:04d}.jpg"
                        )
                if total is not None:
                    dados["fotos_info"] = f"{obtidas} de {total} (fotos acessíveis informadas pelo Telegram)"
                elif obtidas:
                    dados["fotos_info"] = f"{obtidas} foto(s) acessível(is)"
            except errors.UnauthorizedError:
                raise
            except (errors.RPCError, OSError, BotAPIRequestError) as erro:
                print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
                dados["falhas_coleta"].append({"method": "photos.getUserPhotos", "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro)})
                dados["notas"].append(f"Contagem de fotos indisponível: {type(erro).__name__}")
            try:
                from telethon.tl.functions.users import GetSavedMusicRequest
                offset = 0
                total = None
                while True:
                    musicas = await com_espera(
                        lambda offset=offset: cliente(GetSavedMusicRequest(
                            id=usuario, offset=offset, limit=(100 if MODO == "completo" else 1), hash=0
                        ))
                    )
                    dados["musicas_mtproto"].append(musicas)
                    documentos = getattr(musicas, "documents", []) or []
                    contagem = getattr(musicas, "count", None)
                    if isinstance(contagem, int):
                        total = contagem if total is None else max(total, contagem)
                    if not documentos:
                        break
                    offset += len(documentos)
                    if MODO != "completo":
                        break
                    if total is not None and offset >= total:
                        break
                obtidas = sum(len(getattr(pagina, "documents", []) or []) for pagina in dados["musicas_mtproto"])
                if MODO == "completo":
                    registrar_paginacao_incompleta(dados, "users.getSavedMusic", total, obtidas)
                if dados["midias_dir"]:
                    musicas_itens = [
                        documento
                        for pagina in dados["musicas_mtproto"]
                        for documento in (getattr(pagina, "documents", []) or [])
                    ]
                    for indice, documento in enumerate(musicas_itens, 1):
                        extensao = mimetypes.guess_extension(getattr(documento, "mime_type", "") or "") or ".bin"
                        await baixar_midia(
                            cliente, documento, dados, "musica_perfil",
                            f"musica_perfil_{indice:04d}{extensao}"
                        )
                if total is not None:
                    dados["musicas_info"] = f"{obtidas} de {total} música(s) acessível(is) no perfil"
                elif obtidas:
                    dados["musicas_info"] = f"{obtidas} música(s) acessível(is) no perfil"
            except errors.UnauthorizedError:
                raise
            except (errors.RPCError, OSError, BotAPIRequestError) as erro:
                print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
                dados["falhas_coleta"].append({"method": "users.getSavedMusic", "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro)})
                dados["notas"].append(f"Contagem de músicas indisponível: {type(erro).__name__}")
        if MODO == "completo":
            try:
                await coletar_bot_api(dados, entidade, {
                    "id": id_peer(entidade),
                    "username": getattr(entidade, "username", None),
                })
            except errors.UnauthorizedError:
                raise
            except (errors.RPCError, OSError, BotAPIRequestError) as erro_api:
                print(json.dumps(diagnostico_excecao(erro_api), ensure_ascii=False))
                dados["falhas_bot_api"].append({
                    "method": "coleta Bot API",
                    "error_code": 0,
                    "description": type(erro_api).__name__,
                })
                dados["notas"].append(f"Leituras Bot API incompletas: {type(erro_api).__name__}")
            await coletar_catalogo_presentes_bot_api(dados)
            await coletar_catalogo_presentes_mtproto(cliente, dados)
            await coletar_boosts_mtproto(cliente, dados, entidade)
            await coletar_participacao_bot_mtproto(cliente, dados, entidade)
            await coletar_presentes_mtproto(cliente, dados, entidade)
            await coletar_historico_canal_pessoal(cliente, dados, entidade)
            await coletar_topicos_conhecidos_mtproto(cliente, dados)
            await coletar_stickers_mtproto(cliente, dados)
        atualizar_status("2/2 · Tentativas de coleta encerradas; consolidando ficha", entidade)
        resumo = {
            "bot_api": {
                metodo: {
                    "responses": len(respostas),
                    "ok": sum(resposta.get("ok") is True for resposta in respostas),
                }
                for metodo, respostas in dados.get("respostas_bot_api", {}).items()
            },
            "mtproto_errors": [
                {chave: falha[chave] for chave in ("method", "filter", "error") if chave in falha}
                for falha in dados.get("falhas_coleta", [])
            ],
            "bot_api_errors": [
                {chave: falha[chave] for chave in ("method", "error_code") if chave in falha}
                for falha in dados.get("falhas_bot_api", [])
            ],
            "incomplete_pagination": len(dados.get("coletas_incompletas", [])),
            "mtproto_references": {
                "custom_emoji_batches": len(dados.get("emojis_personalizados_mtproto", [])),
                "sticker_sets": len(dados.get("conjuntos_stickers_mtproto", [])),
                "forum_topic_batches": len(dados.get("topicos_forum_mtproto", [])),
            },
            "media": {
                categoria: {
                    estado: sum(item.get("category") == categoria and item.get("status") == estado
                                for item in dados.get("midias", []))
                    for estado in sorted({item.get("status") for item in dados.get("midias", [])
                                          if item.get("category") == categoria})
                }
                for categoria in sorted({item.get("category") for item in dados.get("midias", [])})
            },
            "media_error_types": sorted({
                item["error"] for item in dados.get("midias", [])
                if isinstance(item.get("error"), str)
                and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", item["error"])
            }),
        }
        print("Resumo das leituras: " + json.dumps(resumo, ensure_ascii=False, sort_keys=True))
        return dados
    finally:
        try:
            if cliente is not None:
                await cliente.disconnect()
        finally:
            sessao.close()
            if temporaria:
                temporaria.cleanup()


def campos_presentes(objeto):
    if objeto is None:
        return []
    if isinstance(objeto, dict):
        return sorted(chave for chave, valor in objeto.items() if valor not in (None, False, [], "", 0))
    return sorted(chave for chave, valor in objeto.to_dict().items() if valor not in (None, False, [], "", 0) and chave not in ("phone", "access_hash"))


def descricao_musica(documento):
    for atributo in getattr(documento, "attributes", []) or []:
        if type(atributo).__name__ == "DocumentAttributeAudio":
            titulo = getattr(atributo, "title", None)
            artista = getattr(atributo, "performer", None)
            if titulo or artista:
                return " — ".join(str(parte) for parte in (titulo, artista) if parte)
    return None


def descrever(entidade, completo_, alvo):
    foto = getattr(entidade, "photo", None)
    info = {
        "consultado": f"{EXPECTED_ID} @{alvo}" if EXPECTED_ID else (alvo if re.fullmatch(r"-?\d{1,16}", alvo) else f"@{alvo}"),
        "id": id_peer(entidade),
        "username": getattr(entidade, "username", None),
        "usernames": [u.username for u in (getattr(entidade, "usernames", None) or []) if getattr(u, "active", False)],
        "foto": foto is not None and not type(foto).__name__.endswith("Empty"),
        "campos": [],
    }

    def add(rotulo, valor, limite=400, zero=False):
        if valor is None or valor is False or valor == "" or valor == [] or (valor == 0 and not zero):
            return
        info["campos"].append((rotulo, str(valor)))

    restricoes = [f"{r.platform}: {r.reason}" for r in (getattr(entidade, "restriction_reason", None) or [])]
    if isinstance(entidade, User):
        info["tipo"] = "bot" if entidade.bot else "usuário"
        info["nome"] = " ".join(p for p in (entidade.first_name, entidade.last_name) if p)
        marcas = (("verificado", "verified"), ("premium", "premium"), ("scam", "scam"), ("fake", "fake"), ("restrito", "restricted"), ("suporte", "support"), ("conta excluída", "deleted"))
        add("Restrições", ", ".join(restricoes))
        add("Idioma", getattr(entidade, "lang_code", None))
        add("Mini App principal do bot", "sim" if getattr(entidade, "bot_has_main_app", False) else None)
        add("Emoji de status", "configurado" if getattr(entidade, "emoji_status", None) else None)
        add("Bot com localização inline", "sim" if getattr(entidade, "bot_inline_geo", False) else None)
        add("Bot sem participação em grupos", "sim" if getattr(entidade, "bot_nochats", False) else None)
        add("Bot com menu de anexos", "sim" if getattr(entidade, "bot_attach_menu", False) else None)
        add("Bot com modo visitante", "sim" if getattr(entidade, "bot_guestchat", False) else None)
        add("Bot com tópicos", "sim" if getattr(entidade, "bot_forum_view", False) else None)
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
            avaliacao = getattr(completo_, "stars_rating", None)
            if avaliacao:
                add("Nível Telegram Stars", getattr(avaliacao, "level", None), zero=True)
                add("Stars no nível atual", getattr(avaliacao, "current_level_stars", None), zero=True)
                add("Pontuação Stars", getattr(avaliacao, "stars", None), zero=True)
                add("Stars para o próximo nível", getattr(avaliacao, "next_level_stars", None), zero=True)
            musica = getattr(completo_, "saved_music", None)
            if musica:
                add("Música destacada no perfil", descricao_musica(musica) or "disponível, sem título informado")
            horario = getattr(completo_, "business_work_hours", None)
            if horario:
                add("Fuso dos horários comerciais", getattr(horario, "timezone_id", None))
                periodos = getattr(horario, "weekly_open", None)
                if periodos:
                    add("Intervalos de atendimento registrados", len(periodos), zero=True)

            add("Mensagens pagas (Stars)", getattr(completo_, "send_paid_messages_stars", None), zero=True)
            add("Mensagem automática de boas-vindas", "configurada" if getattr(completo_, "business_greeting_message", None) else None)
            add("Mensagem comercial de ausência", "configurada" if getattr(completo_, "business_away_message", None) else None)
            add("Observação de privacidade das leituras", "datas exatas restritas" if getattr(completo_, "read_dates_private", False) else None)
            add("Recebe chamadas de voz", "disponível" if getattr(completo_, "phone_calls_available", False) else None)
            add("Recebe chamadas de vídeo", "disponível" if getattr(completo_, "video_calls_available", False) else None)
            add("Permite agendamento de mensagens", "sim" if getattr(completo_, "has_scheduled", False) else None)
            add("Exige Premium para novo contato", "sim" if getattr(completo_, "contact_require_premium", False) else None)
            add("Stories fixados acessíveis", "sim" if getattr(completo_, "stories_pinned_available", False) else None)
            add("Chamadas privadas", "sim" if getattr(completo_, "phone_calls_private", False) else None)
            add("Traduções desativadas", "sim" if getattr(completo_, "translations_disabled", False) else None)
            add("Autodestruição do chat", getattr(completo_, "ttl_period", None))
            add("Perfil com botão de presentes", "sim" if getattr(completo_, "display_gifts_button", False) else None)
            add("Perfil com proteção contra encaminhamento", "sim" if getattr(completo_, "noforwards_peer_enabled", False) else None)
            add("Nome nos encaminhamentos", getattr(completo_, "private_forward_name", None))
            add("Mensagens de voz", "bloqueadas" if getattr(completo_, "voice_messages_forbidden", False) else None)
            info_bot = getattr(completo_, "bot_info", None)
            if info_bot:
                add("Descrição do bot", getattr(info_bot, "description", None), 500)
                comandos = [f"/{c.command} — {c.description}" for c in (getattr(info_bot, "commands", None) or [])]
                add("Comandos", "; ".join(comandos))
                add("Política de privacidade", getattr(info_bot, "privacy_policy_url", None))
    elif isinstance(entidade, BotAPIEntity):
        info["tipo"] = {
            "private": "usuário",
            "group": "grupo",
            "supergroup": "supergrupo",
            "channel": "canal",
        }.get(entidade.type, entidade.type or "chat")
        info["nome"] = entidade.title or " ".join(
            parte for parte in (entidade.first_name, entidade.last_name) if parte
        )
        marcas = ()
        campos_bot_api = (
            ("first_name", "Nome"), ("last_name", "Sobrenome"),
            ("bio", "Bio"), ("description", "Descrição"),
            ("invite_link", "Link de convite"), ("active_usernames", "Usernames ativos"),
            ("birthdate", "Aniversário"), ("business_intro", "Intro comercial"),
            ("business_location", "Local comercial"),
            ("business_opening_hours", "Horários comerciais"),
            ("rating", "Avaliação do chat"), ("is_forum", "Fórum"),
            ("has_visible_history", "Histórico visível"),
            ("has_protected_content", "Conteúdo protegido"),
            ("slow_mode_delay", "Modo lento (segundos)"),
            ("linked_chat_id", "Chat vinculado"), ("parent_chat", "Chat pai"),
            ("personal_chat", "Chat pessoal associado"),
        )
        for chave, rotulo in campos_bot_api:
            valor = entidade.data.get(chave)
            if isinstance(valor, (dict, list)):
                valor = json.dumps(valor, ensure_ascii=False)
            add(rotulo + " (Bot API)", valor, 600)
        if completo_ is not None and entidade.type == "group":
            participantes = getattr(completo_, "participants", None)
            lista = getattr(participantes, "participants", None)
            add("Participantes acessíveis (MTProto)", len(lista) if lista is not None else None, zero=True)
            add("Mensagem fixada", getattr(completo_, "pinned_msg_id", None))
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
            add("Nível de boosts do canal", getattr(entidade, "level", None))
            add("Presentes recebidos pelo canal", getattr(completo_, "stargifts_count", None))
            add("Limite de reações distintas", getattr(completo_, "reactions_limit", None))
            add("Lista de membros visualizável", "sim" if getattr(completo_, "can_view_participants", False) else None)
            add("Estatísticas acessíveis", "sim" if getattr(completo_, "can_view_stats", False) else None)
            add("Lista de membros oculta", "sim" if getattr(completo_, "participants_hidden", False) else None)
            add("Antispam nativo", "ativo" if getattr(completo_, "antispam", False) else None)
            add("Mensagens agendadas disponíveis", "sim" if getattr(completo_, "has_scheduled", False) else None)
            add("Histórico anterior oculto", "sim" if getattr(completo_, "hidden_prehistory", False) else None)
            add("Stories fixados", "disponíveis" if getattr(completo_, "stories_pinned_available", False) else None)
            add("Contas expulsas", getattr(completo_, "kicked_count", None), zero=True)
            add("Contas banidas", getattr(completo_, "banned_count", None), zero=True)
            add("Solicitações pendentes", getattr(completo_, "requests_pending", None), zero=True)
            add("Mensagem fixada", getattr(completo_, "pinned_msg_id", None))
            add("Tema do chat", getattr(completo_, "theme_emoticon", None))
            add("Tempo de autodestruição", getattr(completo_, "ttl_period", None))
            add("Agendamento de mensagens", "disponível" if getattr(completo_, "has_scheduled", False) else None)
            add("Mensagens pagas disponíveis", "sim" if getattr(completo_, "paid_messages_available", False) else None)
            local = getattr(completo_, "location", None)
            if local:
                add("Localização", getattr(local, "address", None))
    else:
        info["tipo"] = "grupo"
        info["nome"] = getattr(entidade, "title", "")
        marcas = ()
        add("Membros informados", getattr(entidade, "participants_count", None), zero=True)
        add("Data de criação (Unix)", getattr(entidade, "date", None))
        add("Chamada ativa", "sim" if getattr(entidade, "call_active", False) else None)
        add("Encaminhamentos bloqueados", "sim" if getattr(entidade, "noforwards", False) else None)
        if completo_ is not None:
            add("Descrição", getattr(completo_, "about", None))
            participantes = getattr(completo_, "participants", None)
            if participantes is not None:
                lista = getattr(participantes, "participants", None)
                if lista is not None:
                    add("Participantes acessíveis", len(lista), zero=True)
            add("Mensagem fixada", getattr(completo_, "pinned_msg_id", None))
    info["marcas"] = [rotulo for rotulo, atributo in marcas if getattr(entidade, atributo, False)]
    return info


def falha(alvo, motivo):
    entrada = f"{EXPECTED_ID} @{alvo}" if EXPECTED_ID else (alvo if re.fullmatch(r"-?\d{1,16}", alvo) else f"@{alvo}")
    return f"<b>Não foi possível ler</b>\nEntrada: {esc(entrada)}\n{esc(motivo)}"


async def principal():
    print("telethon", telethon.__version__)
    if FORMATO_MENSAGEM not in ("rich", "html"):
        raise ValueError("FORMATO_MENSAGEM deve ser rich ou html.")
    alvo = os.environ.get("ALVO", "").strip().lstrip("@")
    chat = os.environ.get("CHAT_ID", "").strip()
    if chat and (not CHAT_VALIDO.fullmatch(chat) or tipo_dialogo(str(int(chat))) is None):
        print("CHAT_ID inválido")
        return 1
    if EXPECTED_ID and (not re.fullmatch(r"-?\d{1,16}", EXPECTED_ID) or
                        tipo_dialogo(str(int(EXPECTED_ID))) is None):
        texto = falha(alvo or "(vazio)", "ID esperado inválido; envie ID @username válido.")
        print("EXPECTED_ID inválido")
        codigo = 1
    elif not ALVO_VALIDO.fullmatch(alvo):
        texto = falha(alvo or "(vazio)", "Entrada inválida: use @username, ID numérico ou ID @username.")
        print("entrada inválida")
        codigo = 1
    else:
        try:
            atualizar_status("Autenticando no Telegram e resolvendo a referência")
            dados = await coletar(alvo)
            notas = list(dados["notas"])
            print("campos da entidade:", campos_presentes(dados["entidade"]))
            print("campos do perfil completo:", campos_presentes(dados["completo"]))
            foto_enviada = False
            info = descrever(dados["entidade"], dados["completo"], alvo)
            if dados["fotos_info"]:
                info["campos"].append(("Fotos de perfil no MTProto", dados["fotos_info"]))
            if dados["participantes_mtproto"]:
                total_participantes = sum(len(getattr(pagina, "participants", []) or []) for pagina in dados["participantes_mtproto"])
                info["campos"].append(("Participantes recentes consultados (MTProto)", str(total_participantes)))
            for nome_filtro, respostas_filtro in dados["participantes_filtrados_mtproto"].items():
                if respostas_filtro:
                    quantidade = sum(len(getattr(pagina, "participants", []) or []) for pagina in respostas_filtro)
                    rotulo = {
                        "admins": "Administradores",
                        "bots": "Bots participantes",
                        "restritos": "Membros restritos",
                        "banidos": "Membros banidos",
                    }.get(nome_filtro, nome_filtro)
                    info["campos"].append((rotulo + " consultados (MTProto)", str(quantidade)))
            if dados["musicas_info"]:
                info["campos"].append(("Músicas de perfil no MTProto", dados["musicas_info"]))
            for metodo, respostas in dados.get("respostas_bot_api", {}).items():
                resultado_api = next((item.get("result") for item in reversed(respostas) if item.get("ok")), None)
                if metodo == "getUserProfilePhotos" and isinstance(resultado_api, dict):
                    info["campos"].append(("Fotos de perfil na Bot API", str(resultado_api.get("total_count", 0))))
                elif metodo == "getUserProfileAudios" and isinstance(resultado_api, dict):
                    info["campos"].append(("Áudios de perfil na Bot API", str(resultado_api.get("total_count", 0))))
                elif metodo == "getUserPersonalChatMessages" and isinstance(resultado_api, list):
                    info["campos"].append(("Mensagens no chat pessoal via Bot API", str(len(resultado_api))))
                elif metodo == "getChatAdministrators" and isinstance(resultado_api, list):
                    info["campos"].append(("Administradores via Bot API", str(len(resultado_api))))
                elif metodo == "getChatMemberCount" and resultado_api is not None:
                    info["campos"].append(("Membros via Bot API", str(resultado_api)))
            chat_bot = dados.get("chat_bot_api") or {}
            rotulos_bot = {
                "bio": "Bio (Bot API)", "description": "Descrição (Bot API)",
                "birthdate": "Aniversário (Bot API)", "business_intro": "Intro comercial (Bot API)",
                "business_location": "Local comercial (Bot API)",
                "business_opening_hours": "Horários comerciais (Bot API)",
                "rating": "Avaliação do chat (Bot API)",
            }
            for chave, rotulo in rotulos_bot.items():
                valor = chat_bot.get(chave)
                if valor not in (None, "", [], {}):
                    texto_valor = json.dumps(valor, ensure_ascii=False) if isinstance(valor, (dict, list)) else str(valor)
                    info["campos"].append((rotulo, texto_valor[:600]))

            print("tipo resolvido:", info["tipo"], "| campos extras:", len(info["campos"]))
            codigo = 0
            if not chat:
                coleta_parcial = bool(
                    dados.get("falhas_coleta") or dados.get("falhas_bot_api")
                    or dados.get("coletas_incompletas")
                    or any(item.get("status") != "downloaded" for item in dados.get("midias", []))
                )
                print("Coleta sem destino: " + ("parcial" if coleta_parcial else "sem falhas registradas")
                      + "; entrega de mensagens e arquivos não executada.")
                codigo = 1 if coleta_parcial else 0
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
            diagnostico = diagnostico_api({"error_code": erro.code, "description": erro.message}, "MTProto")
            texto = falha(alvo, f"Telegram {erro.code}: {diagnostico['description']}")
            print(json.dumps(diagnostico, ensure_ascii=False))
            codigo = 1
        except BotAPIAuthenticationError as erro:
            print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
            return 1
        except APIProtocolError as erro:
            print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
            texto = falha(alvo, erro.diagnostic["description"])
            codigo = 1
        except Exception as erro:
            print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
            texto = falha(alvo, f"Falha na consulta: {type(erro).__name__}. Verifique a configuração e tente novamente.")
            codigo = 1
    if chat:
        if codigo == 0:
            identidade = valor_exportavel(dados_basicos(info))
            categorias = valor_exportavel(agrupar_campos(info))
            if MODO == "completo":
                categorias.extend(secoes_completas_telegram(dados, alvo, info))
            alvo_disparo = os.environ.get("ALVO", "").strip().lstrip("@")
            controles = '<tg-button-row align="center">'
            controles += botao_atualizar(alvo_disparo)
            controles += ('<tg-button type="copy_text" text="' + esc(info["id"]) +
                          '">📋 Copiar ID</tg-button>')
            username = info["username"]
            if username and re.fullmatch(r"[A-Za-z0-9_]{1,32}", username):
                controles += ('<tg-button type="url" url="https://t.me/' + esc(username) +
                              '">🔗 Abrir perfil</tg-button>')
            if MODO == "resumo":
                controles += botao_completo(alvo_disparo)
            controles += '</tg-button-row>'
            completo = MODO == "completo"
            secoes = categorias
            notas_publicadas = valor_exportavel(notas)
            teclado_html = None
            if MODO == "resumo" and callback_data("f", alvo_disparo):
                teclado_html = {"inline_keyboard": [[{
                    "text": "📥 Exportação completa",
                    "callback_data": callback_data("f", alvo_disparo),
                }]]}
            total_ricos = 0
            entregues_ricos = 0
            foto_incorporada = False
            rich_ok = False
            try:
                paginas = rich_pages(identidade, secoes, notas_publicadas, controles) if FORMATO_MENSAGEM == "rich" else []
                total_ricos = len(paginas) if FORMATO_MENSAGEM == "rich" else 0
                total_campos_visiveis = sum(len(linhas) for _, linhas in secoes)
                print("Rich Messages planejadas:", total_ricos, "| campos exibidos:", total_campos_visiveis)
                for indice, pagina in enumerate(paginas if FORMATO_MENSAGEM == "rich" else []):
                    if indice > 0:
                        time.sleep(1.1)
                    if indice == 0:
                        ok, foto_incorporada, primeira_rica_id = editar_ficha_rica(pagina, dados["foto"])
                    else:
                        detalhes = {"chat_id": int(chat), "rich_message": {"html": pagina}}
                        resposta_id = ORIGEM_ID if completo else ID_MENSAGEM
                        if resposta_id:
                            detalhes["reply_parameters"] = {"message_id": resposta_id}
                        retorno = solicitar_bot_api("sendRichMessage", detalhes)
                        ok = aceitacao_mensagem(retorno)
                        if not ok:
                            print("Rich Message recusada:", indice + 1, "status", retorno.get("error_code"))
                    if not ok:
                        break
                    entregues_ricos += 1
                    print("Rich Message aceita:", entregues_ricos, "/", total_ricos)
                rich_ok = total_ricos > 0 and entregues_ricos == total_ricos
            except errors.UnauthorizedError:
                raise
            except (errors.RPCError, OSError, BotAPIRequestError) as erro_rico:
                print(json.dumps(diagnostico_excecao(erro_rico), ensure_ascii=False))
                print("formatação rica indisponível:", type(erro_rico).__name__)
            html_ok = False
            total_html = 0
            entregues_html = 0
            if FORMATO_MENSAGEM == "html":
                paginas_html = basic_pages(identidade, secoes, notas_publicadas)
                total_html = len(paginas_html)
                for indice, pagina in enumerate(paginas_html):
                    if indice > 0:
                        time.sleep(1.1)
                    if indice == 0 and ID_MENSAGEM:
                        retorno = solicitar_bot_api("editMessageText", {
                            "chat_id": int(chat), "message_id": ID_MENSAGEM,
                            "text": pagina, "parse_mode": "HTML",
                            **({"reply_markup": teclado_html} if teclado_html else {}),
                        })
                    else:
                        retorno = postar(chat, pagina, True, teclado_html if indice == 0 else None)
                    inalterada = bool(indice == 0 and ID_MENSAGEM and mensagem_inalterada(retorno))
                    if not aceitacao_mensagem(retorno) and not inalterada:
                        print(json.dumps(diagnostico_api(retorno, "editMessageText" if indice == 0 and ID_MENSAGEM else "sendMessage"), ensure_ascii=False))
                        break
                    entregues_html += 1
                html_ok = total_html > 0 and entregues_html == total_html
            foto_entrega_ok = True
            if dados["foto"] and not foto_incorporada:
                try:
                    enviar_foto(chat, dados["foto"])
                    print("foto enviada separadamente")
                except errors.UnauthorizedError:
                    raise
                except (errors.RPCError, OSError, BotAPIRequestError) as erro_foto:
                    print(json.dumps(diagnostico_excecao(erro_foto), ensure_ascii=False))
                    foto_entrega_ok = False
                    print("foto indisponível:", type(erro_foto).__name__)
            arquivos_previstos = 0
            arquivos_entregues = 0
            json_previstos = 0
            json_entregues = 0
            pacotes_midias = []
            midias_previstas = 0
            midias_entregues = 0
            falhas_midias = 0
            if completo:
                if dados.get("midias_dir"):
                    try:
                        pacotes_midias = build_media_archives(dados.get("midias", []), dados["midias_dir"])
                        dados["pacotes_midias"] = pacotes_midias
                    except errors.UnauthorizedError:
                        raise
                    except (errors.RPCError, OSError, BotAPIRequestError) as erro_pacotes:
                        print(json.dumps(diagnostico_excecao(erro_pacotes), ensure_ascii=False))
                        notas.append(f"Pacotes de mídia indisponíveis: {type(erro_pacotes).__name__}")
                    falhas_midias = sum(1 for item in dados.get("midias", []) if item.get("status") != "packaged")
                    midias_previstas = len(pacotes_midias)
                try:
                    arquivos = markdown_files(identidade, categorias, notas)
                    arquivos_previstos = len(arquivos)
                    print("documentos Markdown planejados:", arquivos_previstos)
                    for indice, arquivo in enumerate(arquivos, 1):
                        time.sleep(1.1)
                        try:
                            enviar_documento_md(chat, arquivo, info["id"], indice, arquivos_previstos)
                            arquivos_entregues += 1
                        except errors.UnauthorizedError:
                            raise
                        except (errors.RPCError, OSError, BotAPIRequestError) as erro_parte:
                            print(json.dumps(diagnostico_excecao(erro_parte), ensure_ascii=False))
                            print("Documento recusado:", indice, "/", arquivos_previstos,
                                  type(erro_parte).__name__)
                except errors.UnauthorizedError:
                    raise
                except (errors.RPCError, OSError, BotAPIRequestError) as erro_md:
                    print(json.dumps(diagnostico_excecao(erro_md), ensure_ascii=False))
                    print("Markdown indisponível:", type(erro_md).__name__)
                try:
                    arquivos_json = jsonl_files(registros_telegram(dados, alvo, info))
                    json_previstos = len(arquivos_json)
                    print("documentos JSONL planejados:", json_previstos)
                    for indice, arquivo in enumerate(arquivos_json, 1):
                        time.sleep(1.1)
                        try:
                            enviar_documento_jsonl(chat, arquivo, info["id"], indice, json_previstos)
                            json_entregues += 1
                        except errors.UnauthorizedError:
                            raise
                        except (errors.RPCError, OSError, BotAPIRequestError) as erro_parte:
                            print(json.dumps(diagnostico_excecao(erro_parte), ensure_ascii=False))
                            print("Documento JSONL recusado:", indice, "/", json_previstos,
                                  type(erro_parte).__name__)
                except errors.UnauthorizedError:
                    raise
                except (errors.RPCError, OSError, BotAPIRequestError) as erro_json:
                    print(json.dumps(diagnostico_excecao(erro_json), ensure_ascii=False))
                    print("Exportação JSONL indisponível:", type(erro_json).__name__)
                for indice, caminho_pacote in enumerate(pacotes_midias, 1):
                    time.sleep(1.1)
                    try:
                        enviar_documento_arquivo(chat, caminho_pacote, info["id"], indice, len(pacotes_midias))
                        midias_entregues += 1
                    except errors.UnauthorizedError:
                        raise
                    except (errors.RPCError, OSError, BotAPIRequestError) as erro_midia:
                        print(json.dumps(diagnostico_excecao(erro_midia), ensure_ascii=False))
                        print("Pacote de mídia recusado:", indice, "/", len(pacotes_midias), type(erro_midia).__name__)
            apresentacao_ok = rich_ok if FORMATO_MENSAGEM == "rich" else html_ok
            entrega_ok = apresentacao_ok and foto_entrega_ok and (
                not completo or (
                    arquivos_previstos > 0 and arquivos_entregues == arquivos_previstos and
                    json_previstos > 0 and json_entregues == json_previstos and
                    midias_entregues == midias_previstas
                )
            )
            coleta_sem_falhas = not dados.get("falhas_coleta") and not dados.get("falhas_bot_api") and not dados.get("coletas_incompletas") and falhas_midias == 0
            entrega_ok = entrega_ok and not MENSAGENS_PENDENTES
            relatorio_aceito = entrega_ok and coleta_sem_falhas
            if relatorio_aceito:
                marcar_notificado()
                print("ENVIOS DO RELATÓRIO ACEITOS PELO TELEGRAM:", len(info["campos"]), "campos,",
                      entregues_ricos, "/", total_ricos, "páginas ricas,",
                      entregues_html, "/", total_html, "páginas HTML,",
                      arquivos_entregues, "/", arquivos_previstos, "arquivos Markdown,",
                      json_entregues, "/", json_previstos, "arquivos JSONL,",
                      midias_entregues, "/", midias_previstas, "pacotes de mídia")
            else:
                linhas_aviso = []
                if MENSAGENS_PENDENTES:
                    linhas_aviso.append("O Telegram aceitou mensagens sem ID editável; a entrega dessas mensagens ainda não foi confirmada.")
                if not entrega_ok:
                    linhas_aviso.extend([
                        "<b>⚠️ Entrega incompleta</b>",
                        "Algumas partes do relatório não foram confirmadas pelo Telegram.",
                        f"Rich Messages: {entregues_ricos}/{total_ricos}.",
                        f"HTML: {entregues_html}/{total_html}.",
                        f"Arquivos Markdown: {arquivos_entregues}/{arquivos_previstos}.",
                        f"Arquivos JSONL: {json_entregues}/{json_previstos}.",
                        f"Pacotes de mídia enviados: {midias_entregues}/{midias_previstas}.",
                    ])
                if not coleta_sem_falhas:
                    if entrega_ok:
                        linhas_aviso.append("<b>⚠️ Resultado parcial enviado</b>")
                    linhas_aviso.append("Algumas leituras tentadas falharam, ficaram abaixo da contagem informada ou tiveram mídia indisponível.")
                    if falhas_midias:
                        linhas_aviso.append(f"Itens de mídia indisponíveis: {falhas_midias}.")
                    if dados.get("falhas_bot_api"):
                        linhas_aviso.append(f"Chamadas Bot API com erro: {len(dados['falhas_bot_api'])}.")
                    if dados.get("falhas_coleta"):
                        linhas_aviso.append(f"Chamadas MTProto com erro: {len(dados['falhas_coleta'])}.")
                    if dados.get("coletas_incompletas"):
                        linhas_aviso.append(f"Paginação abaixo do total informado: {len(dados['coletas_incompletas'])} método(s).")
                linhas_aviso.append("As observações no relatório indicam os dados que faltaram.")
                enviar(chat, "\n".join(linhas_aviso))
                codigo = 1
        else:
            causa = re.sub(r"<[^>]*>", "", texto)
            enviar(chat, texto)
            print("Notificação explícita de falha enviada")
        print("processamento do relatório encerrado")
    return codigo


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(principal()))
    except Exception as erro:
        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
        sys.exit(1)
