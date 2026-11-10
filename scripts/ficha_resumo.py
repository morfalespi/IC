"""Ficha curta e entrega conservadora para uma consulta individual.

Rich + foto -> Rich sem foto -> texto. A troca de formato ocorre SOMENTE
após resposta explícita de rejeição HTTP/Bot API 400. Resultado incerto
(timeout, transporte, 5xx) nunca dispara uma segunda tentativa.
"""
import asyncio
from datetime import datetime, timezone
from html import escape
import re

from bot_api import BotAPIRequestError


TIPOS = {
    'user': 'Usuário',
    'bot': 'Bot',
    'basic_group': 'Grupo',
    'supergroup': 'Supergrupo',
    'channel': 'Canal',
}


def _valor(value, limit=240):
    return escape(str(value).strip()[:limit], quote=True)


def _username(value):
    value = str(value or '')
    return value if re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{3,31}', value) else ''


def montar_ficha(data, *, momento=None):
    """Monta uma ficha sem inventar relações, estatísticas ou fontes."""
    entity = data.entity
    tipo = TIPOS.get(data.kind, 'Entidade')
    title = getattr(entity, 'title', None)
    if not title:
        title = ' '.join(v for v in (getattr(entity, 'first_name', None), getattr(entity, 'last_name', None)) if v)
    title = title or ('Perfil ' + str(data.canonical_id))
    principal = _username(getattr(entity, 'username', None))
    outros = []
    for item in getattr(entity, 'usernames', None) or []:
        value = _username(getattr(item, 'username', None))
        if value and getattr(item, 'active', False) and value.lower() != principal.lower():
            if value.lower() not in {x.lower() for x in outros}:
                outros.append(value)

    mtproto = data.full.get('mtproto') if isinstance(data.full, dict) else data.full
    full = getattr(mtproto, 'full_user', None) or getattr(mtproto, 'full_chat', None)
    bio = getattr(full, 'about', None)
    canal_pessoal = getattr(full, 'personal_channel_id', None) if data.kind == 'user' else None

    chat_bot = data.metadata.get('chat_bot_api') if isinstance(data.metadata, dict) else None
    photo = chat_bot.get('photo') if isinstance(chat_bot, dict) else None
    foto_id = (photo.get('big_file_id') or photo.get('small_file_id')) if isinstance(photo, dict) else None
    if not isinstance(foto_id, str) or not foto_id:
        foto_id = None

    consultado = momento or datetime.now(timezone.utc)
    when = consultado.astimezone(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')
    estado = 'parcial, dentro do acesso permitido' if data.partial else 'concluída no escopo consultado'

    def campo(nome, valor):
        return '<p><b>' + _valor(nome) + ':</b> ' + _valor(valor) + '</p>'

    detalhes = [
        'Identificação: MTProto (referência conferida na consulta).',
        'Fotografia: Bot API getChat, quando retornada.',
        'Ausência de vínculos não prova que eles não existem.',
        'Grupos em comum e outros canais não foram enumerados.',
        'Conclusão limitada às permissões da sessão e às categorias consultadas.',
    ]
    lines = [
        '<h2>IC · ' + _valor(tipo) + '</h2>',
        '<h3>' + _valor(title, 160) + '</h3>',
    ]
    if principal:
        lines.append('<p><a href="https://t.me/' + principal + '">@' + principal + '</a></p>')
    lines.append(campo('ID', data.canonical_id))
    if outros:
        lines.append(campo('Outros usernames ativos', ', '.join('@' + v for v in outros[:12])))
    if isinstance(bio, str) and bio.strip():
        lines.append('<p><b>Descrição:</b> ' + _valor(bio, 750) + '</p>')
    if isinstance(canal_pessoal, int) and canal_pessoal > 0:
        lines.append(campo('Canal pessoal vinculado (ID)', canal_pessoal))
    lines.append('<p><b>Estado:</b> ' + _valor(estado) + '</p>')
    lines.append('<details><summary>Fontes e limites</summary><p>' +
                 '</p><p>'.join(_valor(x, 300) for x in detalhes) +
                 '</p><p>Consulta: ' + _valor(when) + '</p></details>')
    sem_foto = ''.join(lines)
    media = None
    completo = sem_foto
    if foto_id:
        # O media.id é um identificador local do RichMessage, não um file_id público.
        completo = lines[0] + '<img src="tg://photo?id=perfil"/>' + ''.join(lines[1:])
        media = [{'id': 'perfil', 'media': {'type': 'photo', 'media': foto_id}}]

    texto = '\n'.join([
        'IC · ' + tipo,
        str(title)[:160],
        ('@' + principal) if principal else '',
        'ID: ' + str(data.canonical_id),
        ('Outros usernames: ' + ', '.join('@' + v for v in outros[:12])) if outros else '',
        ('Descrição: ' + bio.strip()[:750]) if isinstance(bio, str) and bio.strip() else '',
        ('Canal pessoal vinculado (ID): ' + str(canal_pessoal)) if isinstance(canal_pessoal, int) and canal_pessoal > 0 else '',
        'Estado: ' + estado,
        'Origem: MTProto; foto via Bot API quando disponível.',
        'Grupos em comum e demais canais não foram enumerados.',
        'Consulta: ' + when,
    ])
    texto = '\n'.join(l for l in texto.split('\n') if l.strip())[:3900]
    return {'html': completo, 'html_sem_foto': sem_foto, 'media': media, 'texto': texto}


async def entregar_ficha(bot, destination, data, message_id=None):
    """Edita mensagem inicial quando possível; troca formato só após 400.

    A aceitação do servidor não comprova leitura ou entrega no aplicativo.
    """
    ficha = montar_ficha(data)
    destino = int(destination)
    base = {'chat_id': destino}
    metodo = 'editMessageText' if message_id else 'sendRichMessage'
    if message_id:
        base['message_id'] = int(message_id)

    rich = {'html': ficha['html']}
    if ficha['media']:
        rich['media'] = ficha['media']
    candidatos = [(metodo, {**base, 'rich_message': rich})]
    if ficha['media']:
        candidatos.append((metodo, {**base, 'rich_message': {'html': ficha['html_sem_foto']}}))
    candidatos.append(('editMessageText' if message_id else 'sendMessage',
                       {**base, 'text': ficha['texto']}))

    for index, (nome, argumentos) in enumerate(candidatos):
        try:
            resultado = await asyncio.to_thread(bot.call, nome, argumentos)
            return resultado.require()
        except BotAPIRequestError as exc:
            codigo = exc.diagnostic.get('error_code')
            if type(exc) is not BotAPIRequestError or codigo != 400 or index == len(candidatos) - 1:
                raise
    raise AssertionError('Nenhuma tentativa de apresentação restante')
