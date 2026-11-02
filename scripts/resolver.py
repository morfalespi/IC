import atexit
import asyncio
import base64
import html
import hashlib
import json
import mimetypes
import os
import re
import shutil
import tempfile
import sys
import traceback
import time
import urllib.error
import urllib.request
import uuid

import telethon
from ficha_completa import rich_pages, basic_pages, markdown_files, jsonl_files
from mtproto_export import build_media_archives
from telethon import TelegramClient, errors, utils
from telethon.sessions import StringSession
from telethon.tl.functions.channels import GetFullChannelRequest, GetChannelsRequest, GetParticipantsRequest
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.functions.messages import GetChatsRequest, GetFullChatRequest
from telethon.tl.functions.users import GetFullUserRequest, GetUsersRequest
from telethon.tl.types import Channel, Chat, ChannelParticipantsRecent, InputChannel, InputUser, PeerChannel, PeerChat, PeerUser, User

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


def chamar(metodo, corpo, cabecalhos, repetir_5xx=False):
    pedido = urllib.request.Request(
        f"https://api.telegram.org/bot{os.environ['BOT_TOKEN']}/{metodo}",
        data=corpo,
        headers=cabecalhos,
    )
    for tentativa in range(5):
        try:
            with urllib.request.urlopen(pedido, timeout=30) as resposta:
                codigo, bruto = resposta.status, resposta.read()
        except urllib.error.HTTPError as erro:
            codigo, bruto = erro.code, erro.read()
        except Exception as erro:
            return {"ok": False, "error_code": 0, "description": type(erro).__name__}
        try:
            retorno = json.loads(bruto)
        except ValueError:
            retorno = {"ok": False, "error_code": codigo, "description": "Resposta inválida da Bot API"}
        if retorno.get("ok"):
            return retorno
        estado = retorno.get("error_code", codigo)
        retryable = estado == 429 or (repetir_5xx and estado in (500, 502, 503, 504))
        if tentativa == 4 or not retryable:
            return retorno
        parametros = retorno.get("parameters") or {}
        espera = parametros.get("retry_after") if estado == 429 else None
        espera = espera if isinstance(espera, (int, float)) and espera >= 1 else 2 ** tentativa
        espera = min(120, max(1, espera))
        print("Bot API: nova tentativa", metodo, "status", estado, "após", espera, "s")
        time.sleep(espera)
    return {"ok": False, "error_code": 0, "description": "Tentativas esgotadas"}

def confirmacao_mensagem(resposta):
    mensagem = resposta.get("result") if isinstance(resposta, dict) else None
    return bool(resposta.get("ok")) and isinstance(mensagem, dict) and isinstance(mensagem.get("message_id"), int)


def postar(chat_id, texto, formatado, teclado=None):
    carga = {"chat_id": int(chat_id), "text": texto}
    if formatado:
        carga["parse_mode"] = "HTML"
    if teclado:
        carga["reply_markup"] = teclado
    return chamar("sendMessage", json.dumps(carga).encode(), {"Content-Type": "application/json"})


def enviar(chat_id, texto):
    retorno = postar(chat_id, texto, True)
    if not confirmacao_mensagem(retorno):
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
    if not confirmacao_mensagem(retorno):
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
        if confirmacao_mensagem(resposta):
            if definitiva:
                marcar_notificado()
            print("ficha rica editada; foto incorporada no mesmo bloco")
            return True, True
        print("mídia embutida indisponível:", resposta.get("error_code"), corte(resposta.get("description"), 180))
    resposta = solicitar_bot_api(metodo, dados)
    if confirmacao_mensagem(resposta):
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
            esc(dados) + '">📥 Exportação completa</tg-button>') if dados else ""

def enviar_documento_md(chat, conteudo, id_entidade, indice, total):
    limite = uuid.uuid4().hex
    filename = "infocard_" + str(id_entidade).replace("-", "n") + "_completo"
    if total > 1:
        filename += f"_parte_{indice}_de_{total}"
    filename += ".md"
    resumo_hash = hashlib.sha256(conteudo).hexdigest()
    campos = {"chat_id": str(int(chat)), "caption": "📄 Relatório MTProto completo" +
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
    if not confirmacao_mensagem(resposta):
        raise RuntimeError("Envio Markdown recusado: " + str(resposta.get("error_code")) +
                           " " + str(resposta.get("description", ""))[:180])
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


async def bot_api_leitura(dados, metodo, parametros):
    resposta = await asyncio.to_thread(
        chamar, metodo, json.dumps(parametros, ensure_ascii=False).encode("utf-8"),
        {"Content-Type": "application/json"}, True
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
        except Exception as erro:
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
    except Exception as erro:
        return registrar_midia(dados, categoria, hash_nome, status="failed",
                               erro=type(erro).__name__)


async def coletar_bot_api(dados, entidade, info):
    chat_id = "@" + info["username"] if isinstance(entidade, (Channel, Chat)) and info.get("username") else info.get("id")
    if not chat_id:
        return
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

    if isinstance(entidade, User):
        for metodo, lista_chave, categoria in (
            ("getUserProfilePhotos", "photos", "foto_perfil_bot_api"),
            ("getUserProfileAudios", "audios", "audio_perfil_bot_api"),
        ):
            offset = 0
            while True:
                resposta = await bot_api_leitura(
                    dados, metodo, {"user_id": entidade.id, "offset": offset, "limit": 100}
                )
                if not resposta.get("ok"):
                    break
                resultado = resposta.get("result") or {}
                itens = resultado.get(lista_chave) or []
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
                total = resultado.get("total_count")
                if not itens or len(itens) < 100 or (isinstance(total, int) and offset >= total):
                    break
        mensagens = await bot_api_leitura(
            dados, "getUserPersonalChatMessages", {"user_id": entidade.id, "limit": 20}
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
    else:
        await bot_api_leitura(
            dados, "getChatAdministrators", {"chat_id": chat_id, "return_bots": True}
        )
        await bot_api_leitura(dados, "getChatMemberCount", {"chat_id": chat_id})


async def baixar_midia(cliente, objeto, dados, categoria, nome):
    caminho = os.path.join(dados["midias_dir"], nome)
    try:
        retorno = await com_espera(lambda: cliente.download_media(objeto, file=caminho))
        if retorno and os.path.isfile(caminho):
            return registrar_midia(dados, categoria, nome, caminho)
        return registrar_midia(dados, categoria, nome, status="unavailable", erro="Telegram não retornou o arquivo")
    except Exception as erro:
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
    if not confirmacao_mensagem(resposta):
        raise RuntimeError("Envio do pacote de mídia recusado: " + str(resposta.get("error_code")) +
                           " " + str(resposta.get("description", ""))[:180])
    print(f"pacote de mídia {indice}/{total} confirmado: {len(conteudo)} bytes")

def enviar_documento_jsonl(chat, conteudo, id_entidade, indice, total):
    limite = uuid.uuid4().hex
    filename = "infocard_" + str(id_entidade).replace("-", "n") + "_telegram"
    if total > 1:
        filename += f"_parte_{indice}_de_{total}"
    filename += ".jsonl"
    resumo_hash = hashlib.sha256(conteudo).hexdigest()
    campos = {"chat_id": str(int(chat)), "caption": "🧾 Dados Telegram completos (JSONL)" +
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
    if not confirmacao_mensagem(resposta):
        raise RuntimeError("Envio JSONL recusado: " + str(resposta.get("error_code")) +
                           " " + str(resposta.get("description", ""))[:180])
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
        id_entidade = utils.get_peer_id(entidade)
    status = status_ficha(etapa, nome, id_entidade)
    sucesso, _ = editar_ficha_rica(status)
    if not sucesso:
        print("atualização intermediária indisponível; a pesquisa continua")


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
    peer = resultado.peer
    if isinstance(peer, PeerUser):
        return next((u for u in resultado.users if u.id == peer.user_id), None)
    alvo_id = peer.channel_id if isinstance(peer, PeerChannel) else getattr(peer, "chat_id", None)
    return next((c for c in resultado.chats if getattr(c, "id", None) == alvo_id), None)


async def completo(cliente, entidade):
    if isinstance(entidade, User):
        return await cliente(GetFullUserRequest(entidade))
    if isinstance(entidade, Channel):
        return await cliente(GetFullChannelRequest(entidade))
    if isinstance(entidade, Chat):
        return await cliente(GetFullChatRequest(entidade.id))
    return None


def objeto_completo(resposta):
    if resposta is None:
        return None
    return getattr(resposta, "full_user", None) or getattr(resposta, "full_chat", None)


def valor_mtproto(valor):
    if hasattr(valor, "to_dict"):
        return valor_mtproto(valor.to_dict())
    if isinstance(valor, dict):
        return {str(chave): valor_mtproto(item) for chave, item in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [valor_mtproto(item) for item in valor]
    if isinstance(valor, bytes):
        return {"$bytes_base64": base64.b64encode(valor).decode("ascii")}
    if isinstance(valor, (str, int, float, bool)) or valor is None:
        return valor
    if hasattr(valor, "isoformat"):
        return valor.isoformat()
    return str(valor)


def registros_telegram(dados, alvo, info):
    metadados = {
        "formato": "infocard-telegram-jsonl-v2",
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
        "falhas_bot_api": dados.get("falhas_bot_api", []),
        "entidade": dados.get("entidade"),
        "resposta_resolucao": dados.get("resposta_resolucao"),
        "resposta_completa": dados.get("resposta_completa"),
        "fotos_perfil": dados.get("fotos_mtproto", []),
        "musicas_perfil": dados.get("musicas_mtproto", []),
        "participantes": dados.get("participantes_mtproto", []),
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
    return entidade, candidatos


async def resolver_alvo(cliente, alvo):
    if re.fullmatch(r"-?\d{1,16}", alvo):
        if EXPECTED_ID:
            raise ValueError("ID esperado exige um username público para a verificação.")
        entidade, resposta = await resolver_id(cliente, int(alvo))
        return entidade, "Consulta MTProto por ID, sujeita às permissões do Telegram", resposta
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
    cliente = TelegramClient(StringSession(), int(os.environ["API_ID"]), os.environ["API_HASH"])
    try:
        await com_espera(lambda: cliente.start(bot_token=os.environ["BOT_TOKEN"]))
        entidade, origem, resposta_resolucao = await resolver_alvo(cliente, alvo)
        dados = {"entidade": entidade, "completo": None, "resposta_completa": None, "resposta_resolucao": resposta_resolucao, "foto": None, "notas": [origem], "fotos_info": None, "musicas_info": None, "fotos_mtproto": [], "musicas_mtproto": [], "participantes_mtproto": [], "midias": [], "pacotes_midias": [], "falhas_coleta": [], "respostas_bot_api": {}, "falhas_bot_api": [], "midias_dir": tempfile.mkdtemp(prefix="infocard_telegram_") if MODO == "completo" and CHAT_DESTINO else None}
        if dados["midias_dir"]:
            atexit.register(shutil.rmtree, dados["midias_dir"], ignore_errors=True)
        atualizar_status("1/2 · Identificação confirmada; buscando campos adicionais", entidade)
        try:
            dados["resposta_completa"] = await com_espera(lambda: completo(cliente, entidade))
            dados["completo"] = objeto_completo(dados["resposta_completa"])
            if MODO == "completo" and isinstance(entidade, Channel):
                try:
                    offset_participantes = 0
                    while True:
                        pagina_participantes = await com_espera(
                            lambda offset=offset_participantes: cliente(GetParticipantsRequest(
                                channel=entidade,
                                filter=ChannelParticipantsRecent(),
                                offset=offset,
                                limit=100,
                                hash=0,
                            ))
                        )
                        dados["participantes_mtproto"].append(pagina_participantes)
                        lista_participantes = getattr(pagina_participantes, "participants", []) or []
                        if not lista_participantes:
                            break
                        offset_participantes += len(lista_participantes)
                        if len(lista_participantes) < 100:
                            break
                except Exception as erro_participantes:
                    dados["falhas_coleta"].append({"method": "channels.getParticipants", "error": type(erro_participantes).__name__})
                    dados["notas"].append(f"Participantes indisponíveis: {type(erro_participantes).__name__}")
        except Exception as erro:
            dados["falhas_coleta"].append({"method": "getFull", "error": type(erro).__name__})
            dados["notas"].append(f"Dados completos indisponíveis: {type(erro).__name__}: {erro}")
        try:
            dados["foto"] = await com_espera(lambda: cliente.download_profile_photo(entidade, file=bytes))
            if dados["foto"] and dados["midias_dir"]:
                caminho_foto = os.path.join(dados["midias_dir"], "foto_perfil_atual.jpg")
                with open(caminho_foto, "wb") as arquivo_foto:
                    arquivo_foto.write(dados["foto"])
                registrar_midia(dados, "foto_perfil_atual", "foto_perfil_atual.jpg", caminho_foto)
        except Exception as erro:
            dados["notas"].append(f"Foto não baixada: {type(erro).__name__}: {erro}")
        if isinstance(entidade, User):
            try:
                from telethon.tl.functions.photos import GetUserPhotosRequest
                offset = 0
                total = None
                while True:
                    fotos = await com_espera(
                        lambda offset=offset: cliente(GetUserPhotosRequest(
                            user_id=entidade, offset=offset, max_id=0, limit=(100 if MODO == "completo" else 1)
                        ))
                    )
                    dados["fotos_mtproto"].append(fotos)
                    lista_fotos = getattr(fotos, "photos", []) or []
                    contagem = getattr(fotos, "count", None)
                    if total is None and isinstance(contagem, int):
                        total = contagem
                    if not lista_fotos:
                        break
                    offset += len(lista_fotos)
                    if MODO != "completo" or len(lista_fotos) < 100 or (total is not None and offset >= total):
                        break
                obtidas = sum(len(getattr(pagina, "photos", []) or []) for pagina in dados["fotos_mtproto"])
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
            except Exception as erro:
                dados["falhas_coleta"].append({"method": "photos.getUserPhotos", "error": type(erro).__name__})
                dados["notas"].append(f"Contagem de fotos indisponível: {type(erro).__name__}")
            try:
                from telethon.tl.functions.users import GetSavedMusicRequest
                offset = 0
                total = None
                while True:
                    musicas = await com_espera(
                        lambda offset=offset: cliente(GetSavedMusicRequest(
                            id=entidade, offset=offset, limit=(100 if MODO == "completo" else 1), hash=0
                        ))
                    )
                    dados["musicas_mtproto"].append(musicas)
                    documentos = getattr(musicas, "documents", []) or []
                    contagem = getattr(musicas, "count", None)
                    if total is None and isinstance(contagem, int):
                        total = contagem
                    if not documentos:
                        break
                    offset += len(documentos)
                    if MODO != "completo" or len(documentos) < 100 or (total is not None and offset >= total):
                        break
                obtidas = sum(len(getattr(pagina, "documents", []) or []) for pagina in dados["musicas_mtproto"])
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
            except Exception as erro:
                dados["falhas_coleta"].append({"method": "users.getSavedMusic", "error": type(erro).__name__})
                dados["notas"].append(f"Contagem de músicas indisponível: {type(erro).__name__}")
        if MODO == "completo":
            try:
                await coletar_bot_api(dados, entidade, {
                    "id": utils.get_peer_id(entidade),
                    "username": getattr(entidade, "username", None),
                })
            except Exception as erro_api:
                dados["falhas_bot_api"].append({
                    "method": "coleta Bot API",
                    "error_code": 0,
                    "description": type(erro_api).__name__,
                })
                dados["notas"].append(f"Leituras Bot API incompletas: {type(erro_api).__name__}")
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
            add("Pedidos de ingresso pendentes", getattr(completo_, "requests_pending", None), zero=True)
            add("Limite de reações", getattr(completo_, "reactions_limit", None), zero=True)
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
            if dados["participantes_mtproto"]:
                total_participantes = sum(len(getattr(pagina, "participants", []) or []) for pagina in dados["participantes_mtproto"])
                info["campos"].append(("Participantes detalhados acessíveis", str(total_participantes)))
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
            secoes = categorias
            notas_publicadas = notas
            teclado_fallback = None
            if MODO == "resumo" and callback_data("f", alvo_disparo):
                teclado_fallback = {"inline_keyboard": [[{
                    "text": "📥 Exportação completa",
                    "callback_data": callback_data("f", alvo_disparo),
                }]]}
            total_ricos = 0
            entregues_ricos = 0
            foto_incorporada = False
            rich_ok = False
            try:
                paginas = rich_pages(identidade, secoes, notas_publicadas, controles)
                total_ricos = len(paginas)
                print("Rich Messages planejadas:", total_ricos, "| campos adicionais:", len(info["campos"]))
                for indice, pagina in enumerate(paginas):
                    if indice > 0:
                        time.sleep(1.1)
                    if indice == 0:
                        ok, foto_incorporada = editar_ficha_rica(pagina, dados["foto"])
                    else:
                        detalhes = {"chat_id": int(chat), "rich_message": {"html": pagina}}
                        resposta_id = ORIGEM_ID if completo else ID_MENSAGEM
                        if resposta_id:
                            detalhes["reply_parameters"] = {"message_id": resposta_id}
                        retorno = solicitar_bot_api("sendRichMessage", detalhes)
                        ok = confirmacao_mensagem(retorno)
                        if not ok:
                            print("Rich Message recusada:", indice + 1, "status", retorno.get("error_code"))
                    if not ok:
                        continue
                    entregues_ricos += 1
                    print("Rich Message confirmada:", entregues_ricos, "/", total_ricos)
                rich_ok = entregues_ricos == total_ricos
            except Exception as erro_rico:
                print("formatação rica indisponível:", type(erro_rico).__name__)
            html_ok = False
            total_html = 0
            entregues_html = 0
            if not rich_ok:
                try:
                    paginas_html = basic_pages(identidade, secoes, notas_publicadas)
                    total_html = len(paginas_html)
                    for indice, pagina in enumerate(paginas_html):
                        if indice > 0:
                            time.sleep(1.1)
                        retorno = None
                        if indice == 0 and entregues_ricos == 0 and ID_MENSAGEM:
                            retorno = solicitar_bot_api("editMessageText", {
                                "chat_id": int(chat), "message_id": ID_MENSAGEM,
                                "text": pagina, "parse_mode": "HTML",
                                **({"reply_markup": teclado_fallback} if teclado_fallback else {}),
                            })
                        if not retorno or not confirmacao_mensagem(retorno):
                            retorno = postar(chat, pagina, True,
                                             teclado_fallback if indice == 0 else None)
                        if not confirmacao_mensagem(retorno):
                            print("página HTML recusada:", indice + 1, "status", retorno.get("error_code"))
                            continue
                        entregues_html += 1
                        print("página HTML confirmada:", entregues_html, "/", len(paginas_html))
                    html_ok = total_html > 0 and entregues_html == total_html
                except Exception as erro_html:
                    print("HTML indisponível:", type(erro_html).__name__)
            if dados["foto"] and not foto_incorporada:
                try:
                    enviar_foto(chat, dados["foto"])
                    print("foto enviada separadamente")
                except Exception as erro_foto:
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
                    except Exception as erro_pacotes:
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
                        except Exception as erro_parte:
                            print("Documento recusado:", indice, "/", arquivos_previstos,
                                  type(erro_parte).__name__)
                except Exception as erro_md:
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
                        except Exception as erro_parte:
                            print("Documento JSONL recusado:", indice, "/", json_previstos,
                                  type(erro_parte).__name__)
                except Exception as erro_json:
                    print("Exportação JSONL indisponível:", type(erro_json).__name__)
                for indice, caminho_pacote in enumerate(pacotes_midias, 1):
                    time.sleep(1.1)
                    try:
                        enviar_documento_arquivo(chat, caminho_pacote, info["id"], indice, len(pacotes_midias))
                        midias_entregues += 1
                    except Exception as erro_midia:
                        print("Pacote de mídia recusado:", indice, "/", len(pacotes_midias), type(erro_midia).__name__)
            entrega_ok = (rich_ok or html_ok) and (
                not completo or (
                    arquivos_previstos > 0 and arquivos_entregues == arquivos_previstos and
                    json_previstos > 0 and json_entregues == json_previstos and
                    midias_entregues == midias_previstas
                )
            )
            cobertura_ok = not dados.get("falhas_coleta") and not dados.get("falhas_bot_api") and falhas_midias == 0
            sucesso_final = entrega_ok and (not completo or cobertura_ok)
            if sucesso_final:
                marcar_notificado()
                print("RELATÓRIO ENTREGUE:", len(info["campos"]), "campos,",
                      entregues_ricos, "/", total_ricos, "páginas ricas,",
                      entregues_html, "/", total_html, "páginas HTML,",
                      arquivos_entregues, "/", arquivos_previstos, "arquivos Markdown,",
                      json_entregues, "/", json_previstos, "arquivos JSONL,",
                      midias_entregues, "/", midias_previstas, "pacotes de mídia")
            else:
                linhas_aviso = []
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
                if completo and not cobertura_ok:
                    if entrega_ok:
                        linhas_aviso.append("<b>⚠️ Resultado parcial enviado</b>")
                    linhas_aviso.append("Alguns dados disponíveis não puderam ser incluídos nesta consulta.")
                    if falhas_midias:
                        linhas_aviso.append(f"Itens de mídia indisponíveis: {falhas_midias}.")
                    if dados.get("falhas_bot_api"):
                        linhas_aviso.append(f"Leituras Bot API indisponíveis: {len(dados['falhas_bot_api'])}.")
                linhas_aviso.append("As observações no relatório indicam os dados que faltaram.")
                enviar(chat, "\n".join(linhas_aviso))
                codigo = 1
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
