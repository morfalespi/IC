import asyncio
import html
import json
import os
import re
import sys
import traceback
import time
import urllib.error
import urllib.request
import uuid

import telethon
from ficha_completa import rich_pages, basic_pages, markdown_files
from telethon import TelegramClient, errors, utils
from telethon.sessions import StringSession
from telethon.tl.functions.channels import GetFullChannelRequest, GetChannelsRequest
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.functions.messages import GetChatsRequest
from telethon.tl.functions.users import GetFullUserRequest, GetUsersRequest
from telethon.tl.types import Channel, InputChannel, InputUser, PeerChannel, PeerChat, PeerUser, User

ESPERA_TOTAL = 600
USERNAME_VALIDO = re.compile(r"[A-Za-z0-9_]{1,32}")
ALVO_VALIDO = re.compile(r"(?:[A-Za-z0-9_]{1,32}|-?\d{1,16})")
CHAT_VALIDO = re.compile(r"-?[0-9]{1,16}")
MENSAGEM_ID = os.environ.get("MESSAGE_ID", "").strip()
CHAT_DESTINO = os.environ.get("CHAT_ID", "").strip()
ID_MENSAGEM = int(MENSAGEM_ID) if MENSAGEM_ID.isdigit() and int(MENSAGEM_ID) > 0 else None
MODO = "completo" if os.environ.get("MODO") == "completo" else "resumo"
EXPECTED_ID = os.environ.get("EXPECTED_ID", "").strip()
REFERENCIA = os.environ.get("ORIGEM_ID", "")
ORIGEM_ID = int(REFERENCIA) if REFERENCIA.isdigit() and int(REFERENCIA) > 0 else None



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


def postar(chat_id, texto, formatado, teclado=None):
    carga = {"chat_id": int(chat_id), "text": texto}
    if formatado:
        carga["parse_mode"] = "HTML"
    if teclado:
        carga["reply_markup"] = teclado
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


def editar_ficha_rica(conteudo, foto=None, definitiva=False):
    if not CHAT_DESTINO:
        return False, False
    metodo = "editMessageText" if ID_MENSAGEM else "sendRichMessage"
    dados = {"chat_id": int(CHAT_DESTINO), "rich_message": {"html": conteudo}}
    if ID_MENSAGEM:
        dados["message_id"] = ID_MENSAGEM
    if foto and len(foto) <= 10 * 1024 * 1024:
        resposta = solicitar_bot_api(metodo, dados, foto)
        if resposta.get("ok"):
            if definitiva:
                marcar_notificado()
            print("ficha rica editada; foto incorporada no mesmo bloco")
            return True, True
        print("mídia embutida indisponível:", resposta.get("error_code"), corte(resposta.get("description"), 180))
    resposta = solicitar_bot_api(metodo, dados)
    if resposta.get("ok"):
        if definitiva:
            marcar_notificado()
        print("ficha rica editada; sem foto incorporada")
        return True, False
    print("ficha rica indisponível:", resposta.get("error_code"), corte(resposta.get("description"), 180))
    return False, False


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
            esc(dados) + '">📚 Completo + Markdown</tg-button>') if dados else ""

def resumo_categoria(categorias, maximo=9):
    selecionados, restantes = [], maximo
    for titulo, campos in categorias:
        if restantes <= 0:
            break
        escolhidos = []
        for label, valor in campos[:3]:
            if restantes <= 0:
                break
            bruto = str(valor)
            pequeno = bruto if len(bruto) <= 280 else bruto[:279] + "…"
            escolhidos.append((label, pequeno))
            restantes -= 1
        if escolhidos:
            selecionados.append((titulo, escolhidos))
    return selecionados


def enviar_documento_md(chat, conteudo, id_entidade, indice, total):
    limite = uuid.uuid4().hex
    filename = "infocard_" + str(id_entidade).replace("-", "n") + "_completo"
    if total > 1:
        filename += f"_parte_{indice}_de_{total}"
    filename += ".md"
    campos = {"chat_id": str(int(chat)), "caption": "📄 Relatório MTProto completo" +
              (f" · parte {indice}/{total}" if total > 1 else "")}
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
    if not resposta.get("ok"):
        raise RuntimeError("Envio Markdown recusado: " + str(resposta.get("error_code")) +
                           " " + str(resposta.get("description", ""))[:180])
    print(f"documento Markdown {indice}/{total} enviado: {len(conteudo)} bytes")


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
            + ''.join(linhas) + '</table><footer>Fonte: Telegram MTProto</footer>')


def atualizar_status(etapa, entidade=None):
    if not ID_MENSAGEM or not CHAT_DESTINO:
        return
    nome = None
    id_entidade = None
    if entidade is not None:
        nome = getattr(entidade, "title", None) or " ".join(
            parte for parte in [getattr(entidade, "first_name", None), getattr(entidade, "last_name", None)] if parte
        )
        id_entidade = utils.get_peer_id(entidade)
    status = status_ficha(etapa, nome, id_entidade)
    sucesso, _ = editar_ficha_rica(status)
    if not sucesso:
        print("atualização intermediária indisponível; a pesquisa continua")


CATEGORIAS = (
    ("👤 Perfil e atividade", (
        "Bio", "Aniversário", "Idioma", "Premium", "Restrições", "Chats em comum",
        "Canal pessoal", "Nome nos encaminhamentos", "Mensagens de voz",
        "Emoji de status", "Fotos de perfil no MTProto",
    )),
    ("🎵 Recursos e presença", (
        "Música destacada no perfil", "Músicas de perfil no MTProto", "Presentes recebidos",
        "Nível Telegram Stars", "Placeholder inline", "Usuários ativos do bot",
        "Mini App principal do bot", "Descrição do bot", "Comandos",
        "Política de privacidade",
    )),
    ("🏢 Informações comerciais", (
        "Intro comercial", "Endereço comercial", "Fuso dos horários comerciais",
        "Intervalos de atendimento registrados",
    )),
    ("📢 Canal ou grupo", (
        "Descrição", "Membros", "Administradores", "Online agora",
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


async def resolver_id(cliente, id_marcado):
    if abs(id_marcado) > 4503599627370495 or id_marcado == 0:
        raise LookupError("ID fora do intervalo aceito pelo Telegram.")

    id_real, tipo = utils.resolve_id(id_marcado)
    try:
        if tipo is PeerUser:
            candidatos = await com_espera(lambda: cliente(GetUsersRequest([InputUser(id_real, 0)])))
            entidade = next((u for u in candidatos if isinstance(u, User) and u.id == id_real), None)
        elif tipo is PeerChannel:
            candidatos = await com_espera(lambda: cliente(GetChannelsRequest([InputChannel(id_real, 0)])))
            entidade = next((c for c in candidatos.chats if isinstance(c, Channel) and c.id == id_real), None)
        elif tipo is PeerChat:
            candidatos = await com_espera(lambda: cliente(GetChatsRequest([id_real])))
            entidade = next((c for c in candidatos.chats if getattr(c, "id", None) == id_real), None)
        else:
            entidade = None
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
    return entidade


async def resolver_alvo(cliente, alvo):
    if re.fullmatch(r"-?\d{1,16}", alvo):
        if EXPECTED_ID:
            raise ValueError("ID esperado exige um username público para a verificação.")
        return await resolver_id(cliente, int(alvo)), "Consulta MTProto por ID, sujeita às permissões do Telegram"
    resultado = await com_espera(lambda: cliente(ResolveUsernameRequest(alvo)))
    entidade = entidade_de(resultado)
    if entidade is None:
        raise LookupError("O Telegram não retornou uma entidade para o username.")
    if EXPECTED_ID:
        if utils.get_peer_id(entidade) != int(EXPECTED_ID):
            raise LookupError("O username foi resolvido, mas o ID retornado pelo Telegram não corresponde ao ID esperado.")
        return entidade, "ID confirmado por contacts.resolveUsername"
    return entidade, "Referência obtida por contacts.resolveUsername"

async def coletar(alvo):
    cliente = TelegramClient(StringSession(), int(os.environ["API_ID"]), os.environ["API_HASH"])
    try:
        await com_espera(lambda: cliente.start(bot_token=os.environ["BOT_TOKEN"]))
        entidade, origem = await resolver_alvo(cliente, alvo)
        atualizar_status("1/2 · Identificação confirmada; buscando campos adicionais", entidade)
        dados = {"entidade": entidade, "completo": None, "foto": None, "notas": [origem], "fotos_info": None, "musicas_info": None}
        try:
            dados["completo"] = await com_espera(lambda: completo(cliente, entidade))
        except Exception as erro:
            dados["notas"].append(f"Dados completos indisponíveis: {type(erro).__name__}: {erro}")
        try:
            dados["foto"] = await com_espera(lambda: cliente.download_profile_photo(entidade, file=bytes))
        except Exception as erro:
            dados["notas"].append(f"Foto não baixada: {type(erro).__name__}: {erro}")
        if isinstance(entidade, User):
            if getattr(entidade, "photo", None) is not None:
                try:
                    from telethon.tl.functions.photos import GetUserPhotosRequest
                    fotos = await com_espera(
                        lambda: cliente(GetUserPhotosRequest(user_id=entidade, offset=0, max_id=0, limit=1))
                    )
                    total = getattr(fotos, "count", None)
                    if isinstance(total, int):
                        dados["fotos_info"] = f"{total} (total acessível informado pelo Telegram)"
                    elif len(getattr(fotos, "photos", []) or []) > 0:
                        dados["fotos_info"] = "pelo menos 1 foto acessível"
                except Exception as erro:
                    dados["notas"].append(f"Contagem de fotos indisponível: {type(erro).__name__}")
            if getattr(dados["completo"], "saved_music", None) is not None:
                try:
                    from telethon.tl.functions.users import GetSavedMusicRequest
                    musicas = await com_espera(
                        lambda: cliente(GetSavedMusicRequest(id=entidade, offset=0, limit=1, hash=0))
                    )
                    total = getattr(musicas, "count", None)
                    if isinstance(total, int):
                        dados["musicas_info"] = f"{total} música(s) acessível(is) no perfil"
                except Exception as erro:
                    dados["notas"].append(f"Contagem de músicas indisponível: {type(erro).__name__}")
        atualizar_status("2/2 · Dados aprofundados processados; consolidando ficha", entidade)
        return dados
    finally:
        await cliente.disconnect()


def campos_presentes(objeto):
    if objeto is None:
        return []
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
        "id": utils.get_peer_id(entidade),
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
            add("Nome nos encaminhamentos", getattr(completo_, "private_forward_name", None))
            add("Mensagens de voz", "bloqueadas" if getattr(completo_, "voice_messages_forbidden", False) else None)
            info_bot = getattr(completo_, "bot_info", None)
            if info_bot:
                add("Descrição do bot", getattr(info_bot, "description", None), 500)
                comandos = [f"/{c.command} — {c.description}" for c in (getattr(info_bot, "commands", None) or [])]
                add("Comandos", "; ".join(comandos))
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
            local = getattr(completo_, "location", None)
            if local:
                add("Localização", getattr(local, "address", None))
    else:
        info["tipo"] = "grupo"
        info["nome"] = getattr(entidade, "title", "")
        marcas = ()
    info["marcas"] = [rotulo for rotulo, atributo in marcas if getattr(entidade, atributo, False)]
    return info


def falha(alvo, motivo):
    entrada = f"{EXPECTED_ID} @{alvo}" if EXPECTED_ID else (alvo if re.fullmatch(r"-?\d{1,16}", alvo) else f"@{alvo}")
    return f"<b>Não foi possível ler</b>\nEntrada: {esc(entrada)}\n{esc(motivo)}"


async def principal():
    print("telethon", telethon.__version__)
    alvo = os.environ.get("ALVO", "").strip().lstrip("@")
    chat = os.environ.get("CHAT_ID", "").strip()
    if chat and not CHAT_VALIDO.fullmatch(chat):
        print("CHAT_ID inválido")
        return 1
    if EXPECTED_ID and (not re.fullmatch(r"-?\d{1,16}", EXPECTED_ID) or
                        int(EXPECTED_ID) == 0 or abs(int(EXPECTED_ID)) > 4503599627370495):
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
            if dados["musicas_info"]:
                info["campos"].append(("Músicas de perfil no MTProto", dados["musicas_info"]))

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
        if codigo == 0:
            identidade = dados_basicos(info)
            categorias = agrupar_campos(info)
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
            secoes = categorias if completo else resumo_categoria(categorias)
            notas_publicadas = notas if completo else notas[:2]
            if not completo:
                visiveis = sum(len(c) for _, c in secoes)
                total_campos = sum(len(c) for _, c in categorias)
                notas_publicadas = list(notas_publicadas) + [
                    f"Resumo: {visiveis}/{total_campos} campos adicionais exibidos. "
                    "Toque em 'Completo + Markdown' para receber tudo."
                ]
            paginas = rich_pages(identidade, secoes, notas_publicadas, controles)
            paginas_html = basic_pages(identidade, secoes, notas_publicadas)
            teclado_fallback = None
            if MODO == "resumo" and callback_data("f", alvo_disparo):
                teclado_fallback = {"inline_keyboard": [[{
                    "text": "📚 Completo + Markdown",
                    "callback_data": callback_data("f", alvo_disparo),
                }]]}
            print("modo:", MODO, "| páginas ricas:", len(paginas),
                  "| páginas HTML:", len(paginas_html), "| campos totais:", len(info["campos"]))
            todas_entregues = True
            foto_incorporada = False
            for indice, pagina in enumerate(paginas):
                if indice > 0:
                    time.sleep(1.1)
                if indice == 0:
                    sucesso, foto_incorporada = editar_ficha_rica(pagina, dados["foto"])
                else:
                    detalhes = {"chat_id": int(chat), "rich_message": {"html": pagina}}
                    resposta_id = ORIGEM_ID if completo else ID_MENSAGEM
                    if resposta_id:
                        detalhes["reply_parameters"] = {"message_id": resposta_id}
                    resposta = solicitar_bot_api("sendRichMessage", detalhes)
                    sucesso = bool(resposta.get("ok"))
                    if not sucesso:
                        print("parte rica", indice + 1, "recusada:",
                              resposta.get("error_code"), corte(resposta.get("description"), 180))
                if not sucesso:
                    todas_entregues = False
                    break
                print("parte rica", indice + 1, "de", len(paginas), "entregue")
            if todas_entregues:
                if dados["foto"] and not foto_incorporada:
                    try:
                        enviar_foto(chat, dados["foto"])
                        print("foto enviada separadamente")
                    except Exception as erro_foto:
                        print("foto indisponível:", type(erro_foto).__name__)
            else:
                print("Rich Message recusada: modo HTML de compatibilidade")
                for indice, pagina in enumerate(paginas_html):
                    if indice > 0:
                        time.sleep(1.1)
                    if indice == 0 and ID_MENSAGEM:
                        resposta = solicitar_bot_api("editMessageText", {
                            "chat_id": int(chat), "message_id": ID_MENSAGEM,
                            "text": pagina, "parse_mode": "HTML",
                            **({"reply_markup": teclado_fallback} if indice == 0 and teclado_fallback else {}),
                        })
                        if not resposta.get("ok"):
                            resposta = postar(chat, pagina, True, teclado_fallback if indice == 0 else None)
                    else:
                        resposta = postar(chat, pagina, True, teclado_fallback if indice == 0 else None)
                    if not resposta.get("ok"):
                        raise RuntimeError("Falha ao entregar HTML parte " + str(indice + 1) +
                                           ": " + str(resposta.get("description")))
                    print("parte HTML", indice + 1, "de", len(paginas_html), "entregue")
                if dados["foto"]:
                    try:
                        enviar_foto(chat, dados["foto"])
                    except Exception as erro_foto:
                        print("foto indisponível:", type(erro_foto).__name__)
            if completo:
                arquivos = markdown_files(identidade, categorias, notas)
                print("documentos Markdown:", len(arquivos))
                for indice, arquivo in enumerate(arquivos, 1):
                    time.sleep(1.1)
                    enviar_documento_md(chat, arquivo, info["id"], indice, len(arquivos))
            marcar_notificado()
        else:
            causa = re.sub(r"<[^>]*>", "", texto)
            ok, _ = editar_ficha_rica(ficha_falha(alvo, causa), definitiva=True)
            if not ok:
                enviar(chat, texto)
                print("erro convencional enviado por fallback")
        print("mensagem final entregue ao chat")
    return codigo


if __name__ == "__main__":
    sys.exit(asyncio.run(principal()))
