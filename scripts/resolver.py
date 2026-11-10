"""Authorized Telegram acquisition -> local exports -> optional Bot API delivery."""
import asyncio
from dataclasses import asdict, dataclass, field
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys
import uuid

import telethon
from telethon import TelegramClient, errors, utils
from telethon.sessions import SQLiteSession, StringSession
from telethon.tl.functions.channels import GetFullChannelRequest, GetParticipantsRequest
from telethon.tl.functions.messages import GetFullChatRequest, GetHistoryRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.photos import GetUserPhotosRequest
from telethon.tl.types import User, Chat, Channel, ChannelParticipantsRecent, ChannelParticipantsAdmins, ChannelParticipantsBots, ChannelParticipantsBanned, ChannelParticipantsKicked, PeerUser, PeerChat, PeerChannel

from bot_api import BotClient, BotAPIRequestError, BotAPIAuthenticationError, diagnostico_excecao, authorized_destination, registrar_notificacao
from exportacao import valor_exportavel, disclosure
from ficha_completa import basic_pages, markdown_files, jsonl_files
from ficha_resumo import entregar_ficha
from mtproto_export import build_media_archives


@dataclass
class Collection:
    method: str
    state: str = 'collecting'
    pages: int = 0
    records: int = 0
    expected: int | None = None
    reason: str | None = None


@dataclass
class Acquisition:
    canonical_id: int
    kind: str
    entity: object
    full: object = None
    messages: list = field(default_factory=list)
    participants: list = field(default_factory=list)
    photos: list = field(default_factory=list)
    media: list = field(default_factory=list)
    collections: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    @property
    def partial(self):
        return any(c.state not in {'complete', 'not_requested'} for c in self.collections.values()) or any(m['status'] != 'downloaded' for m in self.media)


def target(value):
    value = str(value).strip()
    if re.fullmatch(r'-?[1-9]\d{0,15}', value):
        return int(value)
    value = value.removeprefix('@')
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{3,31}', value):
        raise ValueError('ALVO must be a canonical numeric ID or Telegram username')
    return value


def entity_kind(entity):
    if isinstance(entity, User):
        return 'bot' if entity.bot else 'user'
    if isinstance(entity, Chat):
        return 'basic_group'
    if isinstance(entity, Channel):
        return 'supergroup' if entity.megagroup else 'channel'
    raise LookupError('Entity is inaccessible or its type is unsupported')


async def resolver_alvo(client, value, expected_id=None):
    requested = target(value)
    # Marked IDs preserve the peer namespace. Never invent an access_hash.
    if isinstance(requested, int):
        real_id, peer_type = utils.resolve_id(requested)
        reference = peer_type(real_id)
    else:
        reference = requested
    try:
        peer = await client.get_input_entity(reference)
        entity = await client.get_entity(peer)
    except (ValueError, TypeError) as error:
        raise LookupError('Entity unavailable: use an accessible username or a session that knows this peer') from error
    entity_kind(entity)
    canonical = utils.get_peer_id(entity)
    if isinstance(requested, int) and canonical != requested:
        raise LookupError('Resolved entity differs from requested canonical ID')
    if expected_id is not None and str(expected_id).strip():
        if canonical != int(expected_id):
            raise LookupError('Resolved entity differs from EXPECTED_ID; operation stopped')
    if isinstance(requested, str):
        usernames = {str(getattr(entity, 'username', '') or '').lower()}
        usernames.update(u.username.lower() for u in getattr(entity, 'usernames', None) or [] if getattr(u, 'active', False))
        if requested.lower() not in usernames:
            raise LookupError('Resolved entity does not own the requested username')
    return entity, peer


async def open_client(bot):
    api_id = os.environ.get('API_ID', '')
    api_hash = os.environ.get('API_HASH', '')
    if not api_id.isdigit() or int(api_id) <= 0 or not re.fullmatch(r'[a-fA-F0-9]{32}', api_hash):
        raise ValueError('Valid API_ID and API_HASH are required for MTProto')
    directory = Path(os.environ.get('TELETHON_SESSION_DIR', '.ic/sessions'))
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    session_string = os.environ.get('TELETHON_STRING_SESSION')
    session_path = directory / ('bot_' + hashlib.sha256(bot.token.encode()).hexdigest()[:24])
    session = StringSession(session_string) if session_string else SQLiteSession(str(session_path))
    if not session_string:
        os.chmod(str(session_path) + '.session', 0o600)
    client = TelegramClient(session, int(api_id), api_hash, timeout=20, request_retries=0, connection_retries=1, flood_sleep_threshold=0)
    try:
        await asyncio.wait_for(client.connect(), 45)
        if not await client.is_user_authorized():
            if session_string:
                raise PermissionError('Configured user session is not authorized')
            await asyncio.wait_for(client.sign_in(bot_token=bot.token), 45)
        me = await client.get_me()
        if me is None:
            raise PermissionError('MTProto session is not authenticated')
        if not session_string:
            bot_me = await asyncio.to_thread(bot.get_me)
            if not me.bot or me.id != bot_me['id']:
                raise PermissionError('MTProto session does not match the configured bot')
        return client
    except BaseException:
        await client.disconnect()
        session.close()
        raise


def interrupted(collection, error):
    if isinstance(error, (BotAPIAuthenticationError, errors.UnauthorizedError)):
        raise error
    restricted = isinstance(error, errors.RPCError) or (isinstance(error, BotAPIRequestError) and error.diagnostic.get('error_code') in {400, 403})
    collection.state = 'restricted' if restricted and collection.pages == 0 else 'partial'
    collection.reason = type(error).__name__
    if isinstance(error, errors.FloodWaitError):
        collection.reason += f': retry_after={error.seconds}'


async def paginated(collection, fetch, items, identity, *, max_pages=1000, expected=None):
    """Offset pagination counts server rows; unique records detect repeated pages."""
    rows = []
    seen = set()
    offset = 0
    try:
        for _ in range(max_pages):
            response = await fetch(offset)
            collection.pages += 1
            count = getattr(response, 'count', None)
            if isinstance(count, int):
                collection.expected = max(collection.expected or 0, count)
            page = items(response)
            if not page:
                collection.state = 'partial' if collection.expected is not None and len(rows) < collection.expected else 'complete'
                if collection.state == 'partial':
                    collection.reason = 'API exhausted before advertised count; visibility may be restricted'
                break
            new = []
            for item in page:
                key = identity(item)
                if key not in seen:
                    seen.add(key)
                    new.append(item)
            if not new:
                collection.state, collection.reason = 'partial', 'Repeated page; cursor did not advance'
                break
            rows.extend(new)
            collection.records = len(rows)
            offset += len(page)
            if expected is not None and len(rows) >= expected:
                collection.state = 'complete'
                break
        else:
            collection.state, collection.reason = 'partial', 'Configured page limit reached'
    except (errors.RPCError, OSError, asyncio.TimeoutError, ValueError) as error:
        interrupted(collection, error)
    return rows


async def collect_messages(client, peer, data, ids=None, max_pages=1000):
    collection = data.collections['messages'] = Collection('messages.getMessages' if ids else 'messages.getHistory')
    seen = set()
    cursor = 0
    try:
        if ids:
            for start in range(0, len(ids), 100):
                page = await client.get_messages(peer, ids=ids[start:start + 100])
                collection.pages += 1
                for message in page:
                    if message is not None and getattr(message, 'peer_id', None) is not None:
                        if utils.get_peer_id(message.peer_id) != data.canonical_id:
                            raise LookupError('Message peer differs from authorized entity')
                        data.messages.append(message)
                collection.records = len(data.messages)
            collection.expected = len(ids)
            collection.state = 'complete' if len(data.messages) == len(ids) else 'partial'
            if collection.state == 'partial':
                collection.reason = 'Some requested messages are absent or inaccessible'
            return
        for _ in range(max_pages):
            response = await client(GetHistoryRequest(peer=peer, offset_id=cursor, offset_date=None, add_offset=0, limit=100, max_id=0, min_id=0, hash=0))
            collection.pages += 1
            count = getattr(response, 'count', None)
            if isinstance(count, int) and not getattr(response, 'inexact', False):
                collection.expected = count
            page = response.messages
            if not page:
                collection.state = 'partial' if collection.expected is not None and collection.records < collection.expected else 'complete'
                if collection.state == 'partial':
                    collection.reason = 'History exhausted before advertised count'
                break
            fresh = []
            for message in page:
                if message.id not in seen:
                    if getattr(message, 'peer_id', None) is not None and utils.get_peer_id(message.peer_id) != data.canonical_id:
                        raise LookupError('Message peer differs from authorized entity')
                    seen.add(message.id)
                    fresh.append(message)
            next_cursor = min(m.id for m in page)
            if not fresh or (cursor and next_cursor >= cursor):
                collection.state, collection.reason = 'partial', 'History cursor repeated'
                break
            data.messages.extend(fresh)
            collection.records = len(data.messages)
            cursor = next_cursor
        else:
            collection.state, collection.reason = 'partial', 'Configured page limit reached'
    except (errors.RPCError, OSError, asyncio.TimeoutError, ValueError) as error:
        interrupted(collection, error)


def collection_categories(mode, requested=None):
    from metadata import EXTRA_CATEGORIES
    if mode not in {'resumo', 'completo'}:
        raise ValueError('MODO must be resumo or completo')
    selected = requested or ({'metadata'} if mode == 'resumo' else {'metadata', 'messages', 'participants', 'photos', 'media'} | EXTRA_CATEGORIES)
    unknown = selected - ({'metadata', 'messages', 'participants', 'photos', 'media'} | EXTRA_CATEGORIES)
    if unknown:
        raise ValueError('Unknown collection categories: ' + ','.join(sorted(unknown)))
    return selected


async def collect_bot_media(bot, data, directory):
    files = {}
    def visit(value):
        if isinstance(value, dict):
            if isinstance(value.get('big_file_id'), str):
                files.setdefault(value.get('big_file_unique_id') or value['big_file_id'], value['big_file_id'])
            if isinstance(value.get('file_id'), str):
                files.setdefault(value.get('file_unique_id') or value['file_id'], value['file_id'])
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            if value and all(isinstance(v, dict) and 'file_id' in v and 'width' in v and 'height' in v for v in value):
                visit(max(value, key=lambda v: v['width'] * v['height']))
            else:
                for item in value:
                    visit(item)
    visit(data.metadata.get('bot_details', {}))
    visit(data.metadata.get('bot_catalog', {}))
    visit(data.metadata.get('chat_bot_api', {}))
    state = data.collections['bot_media'] = Collection('getFile/downloadFile', expected=len(files))
    root = directory / 'media'
    root.mkdir(mode=0o700, exist_ok=True)
    for unique, file_id in files.items():
        name = 'bot_' + hashlib.sha256(str(unique).encode()).hexdigest()[:24] + '.bin'
        try:
            content, digest = await asyncio.to_thread(bot.download, file_id)
            path = root / name
            path.write_bytes(content)
            data.media.append({'category': 'bot_api', 'name': name, 'path': str(path), 'bytes': len(content), 'sha256': digest, 'status': 'downloaded'})
            state.pages += 1
            state.records += 1
        except (BotAPIRequestError, OSError, asyncio.TimeoutError) as error:
            interrupted(state, error)
            data.media.append({'category': 'bot_api', 'name': name, 'status': 'failed', 'error': type(error).__name__})
    if state.state == 'collecting':
        state.state = 'complete'
    elif state.records:
        state.state = 'partial'


async def acquire(client, value, directory, *, expected_id=None, mode='completo', categories=None, message_ids=None):
    entity, peer = await resolver_alvo(client, value, expected_id)
    data = Acquisition(utils.get_peer_id(entity), entity_kind(entity), entity)
    from metadata import acquire_metadata
    categories = collection_categories(mode, categories)
    max_pages = int(os.environ.get('IC_MAX_PAGES', '1000'))
    if not 1 <= max_pages <= 10000:
        raise ValueError('IC_MAX_PAGES must be between 1 and 10000')
    if 'metadata' in categories:
        state = data.collections['metadata'] = Collection('getFull')
        try:
            if isinstance(entity, User):
                request = GetFullUserRequest(utils.get_input_user(peer))
            elif isinstance(entity, Channel):
                request = GetFullChannelRequest(utils.get_input_channel(peer))
            else:
                request = GetFullChatRequest(entity.id)
            data.full = await client(request)
            full_entity = getattr(data.full, 'full_user' if isinstance(entity, User) else 'full_chat', None)
            if full_entity is None or full_entity.id != entity.id:
                raise LookupError('Full metadata does not identify the authorized entity')
            state.pages, state.records, state.state = 1, 1, 'complete'
        except (errors.RPCError, OSError, asyncio.TimeoutError) as error:
            interrupted(state, error)
    if 'messages' in categories:
        await collect_messages(client, peer, data, message_ids, max_pages)
        full_entity = getattr(data.full, 'full_user', None) or getattr(data.full, 'full_chat', None)
        pinned_id = getattr(full_entity, 'pinned_msg_id', None)
        if pinned_id and not message_ids and pinned_id not in {m.id for m in data.messages}:
            pinned = Acquisition(data.canonical_id, data.kind, entity)
            await collect_messages(client, peer, pinned, [pinned_id], max_pages)
            data.collections['pinned_message'] = pinned.collections['messages']
            data.messages.extend(pinned.messages)
    if 'participants' in categories:
        state = data.collections['participants'] = Collection('channels.getParticipants' if isinstance(entity, Channel) else 'messages.getFullChat')
        if isinstance(entity, Channel):
            filters = [('recent', ChannelParticipantsRecent()), ('admins', ChannelParticipantsAdmins()), ('bots', ChannelParticipantsBots()), ('restricted', ChannelParticipantsBanned('')), ('kicked', ChannelParticipantsKicked(''))]
            for name, participant_filter in filters:
                filter_state = state if name == 'recent' else Collection('channels.getParticipants[' + name + ']')
                if name != 'recent':
                    data.collections['participants_' + name] = filter_state
                pages = []
                async def fetch(offset):
                    response = await client(GetParticipantsRequest(utils.get_input_channel(peer), participant_filter, offset, 100, 0))
                    pages.append(response)
                    return response
                def identity(participant):
                    user_id = getattr(participant, 'user_id', None)
                    return ('user', user_id) if user_id is not None else ('peer', utils.get_peer_id(participant.peer))
                rows = await paginated(filter_state, fetch, lambda r: r.participants, identity, max_pages=max_pages)
                data.metadata['participants_' + name] = pages
                if name == 'recent':
                    data.participants = rows
        elif isinstance(entity, Chat):
            try:
                response = await client(GetFullChatRequest(entity.id))
                state.pages = 1
                participants = getattr(response.full_chat.participants, 'participants', None)
                if participants is None:
                    state.state, state.reason = 'restricted', 'Participant list is not visible'
                else:
                    data.participants = participants
                    state.records, state.state = len(participants), 'complete'
            except (errors.RPCError, OSError, asyncio.TimeoutError) as error:
                interrupted(state, error)
        else:
            state.state, state.reason = 'not_requested', 'Not applicable to users or bots'
    if 'photos' in categories:
        state = data.collections['photos'] = Collection('photos.getUserPhotos' if isinstance(entity, User) else 'download_profile_photo')
        if isinstance(entity, User):
            async def fetch(offset):
                return await client(GetUserPhotosRequest(utils.get_input_user(peer), offset, 0, 100))
            data.photos = await paginated(state, fetch, lambda r: r.photos, lambda p: p.id, max_pages=max_pages)
        else:
            state.state, state.reason = 'not_requested', 'Current chat photo is included in metadata; downloadable with media'
    data.metadata.update(await acquire_metadata(client, peer, data, categories, max_pages))
    if 'media' in categories:
        media_dir = directory / 'media'
        media_dir.mkdir(mode=0o700, exist_ok=True)
        objects = [('message', m) for m in data.messages if getattr(m, 'media', None)]
        objects += [('photo', p) for p in data.photos]
        from telethon.tl.types import Document, Photo
        seen_documents = set()
        def referenced_media(value):
            if isinstance(value, (Document, Photo)):
                key = (type(value).__name__, value.id)
                if key not in seen_documents:
                    seen_documents.add(key)
                    yield value
            elif isinstance(value, dict):
                for child in value.values():
                    yield from referenced_media(child)
            elif isinstance(value, (list, tuple)):
                for child in value:
                    yield from referenced_media(child)
            elif hasattr(value, 'to_dict'):
                yield from referenced_media(vars(value))
        objects += [('metadata', obj) for obj in referenced_media(data.metadata)]
        max_media_bytes = int(os.environ.get('IC_MAX_MEDIA_BYTES', str(40 * 1024 * 1024)))
        if not 1 <= max_media_bytes <= 49 * 1024 * 1024:
            raise ValueError('IC_MAX_MEDIA_BYTES must be between 1 and 51380224')
        def progress(current, total):
            if current > max_media_bytes or (total is not None and total > max_media_bytes):
                raise ValueError('Media exceeds configured byte limit')
        for index, (category, obj) in enumerate(objects):
            name = f'{category}_{index}'
            try:
                # A controlled basename prevents remote filenames escaping the export directory.
                path = await asyncio.wait_for(client.download_media(obj, file=str(media_dir / name), progress_callback=progress), 120)
                if not path:
                    raise OSError('No downloadable media returned')
                resolved = Path(path).resolve()
                if not resolved.is_relative_to(media_dir.resolve()) or not resolved.is_file():
                    raise OSError('Invalid media output path')
                if resolved.stat().st_size > max_media_bytes:
                    raise ValueError('Media exceeds configured byte limit')
                content = resolved.read_bytes()
                data.media.append({'category': category, 'name': resolved.name, 'path': str(resolved), 'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest(), 'status': 'downloaded'})
            except (errors.RPCError, OSError, asyncio.TimeoutError, ValueError) as error:
                data.media.append({'category': category, 'name': name, 'status': 'failed', 'error': type(error).__name__})
        state = data.collections['media'] = Collection('download_media', 'partial' if any(m['status'] == 'failed' for m in data.media) else 'complete', records=sum(m['status'] == 'downloaded' for m in data.media))
        try:
            photo = await client.download_profile_photo(peer, file=bytes)
            if photo:
                path = media_dir / 'profile.jpg'
                path.write_bytes(photo)
                data.media.append({'category': 'profile', 'name': path.name, 'path': str(path), 'bytes': len(photo), 'sha256': hashlib.sha256(photo).hexdigest(), 'status': 'downloaded'})
                state.records += 1
        except (errors.RPCError, OSError, asyncio.TimeoutError) as error:
            state.state, state.reason = 'partial', type(error).__name__
    return data


def export(data, directory):
    snapshot = {
        'schema': 'ic-report-v1', 'canonical_id': data.canonical_id, 'kind': data.kind,
        'completeness': 'partial' if data.partial else 'complete_available',
        'scope': 'Requested categories; API visibility and configured limits apply. This is not proof of all Telegram data.',
        'telethon': telethon.__version__, 'collections': {k: asdict(v) for k, v in data.collections.items()},
        'entity': data.entity, 'full': data.full, 'messages': data.messages, 'participants': data.participants, 'photos': data.photos,
        'media': [{k: v for k, v in m.items() if k != 'path'} for m in data.media],
        'additional_metadata': data.metadata,
        'redaction': 'Credentials, access hashes, phone numbers and file capabilities removed at disclosure boundary',
    }
    safe = disclosure(valor_exportavel(snapshot))
    def records():
        for key, value in safe.items():
            if isinstance(value, list) and value:
                for index, item in enumerate(value):
                    yield {'category': key, 'index': index, 'value': item}
            else:
                yield {'category': key, 'value': value}
    files = []
    for index, content in enumerate(jsonl_files(records()), 1):
        path = directory / f'report_{index}.jsonl'
        path.write_bytes(content)
        files.append(path)
    identity = [('Canonical ID', data.canonical_id), ('Type', data.kind), ('Completeness', safe['completeness'])]
    sections = [(record['category'], [(str(record.get('index', 'Data')), json.dumps(record['value'], ensure_ascii=False, indent=2))]) for record in records() if record['category'] not in {'canonical_id', 'kind'}]
    for index, content in enumerate(markdown_files(identity, sections, []), 1):
        path = directory / f'report_{index}.md'
        path.write_bytes(content)
        files.append(path)
    return files, identity, safe


async def workflow(bot=None, client=None):
    value = os.environ.get('ALVO', '').strip()
    target(value)
    destination = os.environ.get('CHAT_ID', '').strip()
    if destination:
        authorized_destination(destination)
    bot = bot or BotClient()
    identity = await asyncio.to_thread(bot.get_me)
    print(json.dumps({'state': 'bot_authenticated', 'is_bot': identity['is_bot']}), flush=True)
    directory = Path(os.environ.get('IC_OUTPUT_DIR', '.ic/exports')) / uuid.uuid4().hex
    directory.mkdir(mode=0o700, parents=True)
    own_client = client is None
    operation = {'state': 'prepared', 'delivery': 'not_requested', 'accepted_messages': 0}
    def persist_state(**changes):
        operation.update(changes)
        pending = directory / 'operation.json.tmp'
        pending.write_text(json.dumps(operation, indent=2))
        pending.replace(directory / 'operation.json')
    persist_state()
    try:
        client = client or await open_client(bot)
        persist_state(state='acquiring')
        categories = {c.strip() for c in os.environ.get('IC_CATEGORIES', '').split(',') if c.strip()} or None
        ids = list(dict.fromkeys(int(v) for v in os.environ.get('MESSAGE_IDS', '').split(',') if v.strip()))
        if any(v <= 0 for v in ids):
            raise ValueError('MESSAGE_IDS must contain positive integers')
        data = await acquire(client, value, directory, expected_id=os.environ.get('EXPECTED_ID'), mode=os.environ.get('MODO', 'completo'), categories=categories, message_ids=ids or None)
        effective_categories = collection_categories(os.environ.get('MODO', 'completo'), categories)
        if 'bot_details' in effective_categories:
            from metadata import acquire_bot_details
            data.metadata['bot_details'] = await acquire_bot_details(bot, data, int(os.environ.get('IC_MAX_PAGES', '1000')))
        # Bot API visibility is independent of MTProto visibility.
        state = data.collections['bot_chat'] = Collection('getChat')
        try:
            chat = await asyncio.to_thread(bot.get_chat, data.canonical_id)
            if chat['id'] != data.canonical_id:
                raise LookupError('Bot API chat differs from resolved MTProto entity')
            state.pages, state.records, state.state = 1, 1, 'complete'
            # Retain the documented ChatFullInfo alongside MTProto metadata.
            data.metadata['chat_bot_api'] = chat
            data.full = {'mtproto': data.full, 'bot_api': chat}
        except (OSError, RuntimeError) as error:
            interrupted(state, error)
        if 'catalog' in effective_categories:
            catalog_state = data.collections['bot_catalog'] = Collection('getAvailableGifts')
            try:
                catalog = (await asyncio.to_thread(bot.call, 'getAvailableGifts')).require()
                if not isinstance(catalog, dict) or not isinstance(catalog.get('gifts'), list):
                    raise ValueError('Invalid Gifts response')
                data.metadata['bot_catalog'] = catalog
                catalog_state.pages, catalog_state.records, catalog_state.state = 1, len(catalog['gifts']), 'complete'
            except (BotAPIRequestError, OSError, asyncio.TimeoutError) as error:
                interrupted(catalog_state, error)
        if 'media' in effective_categories:
            await collect_bot_media(bot, data, directory)
        archives = build_media_archives(data.media, directory)
        files, report_identity, safe = export(data, directory)
        print(json.dumps({'state': 'exported', 'run_id': directory.name, 'files': len(files) + len(archives), 'completeness': safe['completeness']}), flush=True)
        receipts = []
        persist_state(state='exported', completeness=safe['completeness'])
        def receipt(message):
            receipts.append({'state': 'api_accepted', 'message_id': message['message_id'], 'downstream': 'not_observable'})
            (directory / 'delivery.json').write_text(json.dumps(receipts, indent=2))
            persist_state(accepted_messages=len(receipts))
        if destination:
            persist_state(state='delivering', delivery='submitting')
            # Validate canonical destination before any report content is submitted.
            destination_chat = await asyncio.to_thread(bot.get_chat, int(destination))
            if str(destination_chat['id']) != destination:
                raise PermissionError('Destination resolution changed canonical ID')
            message_id = os.environ.get('MESSAGE_ID', '').strip()
            if message_id and (not message_id.isdigit() or int(message_id) <= 0):
                raise ValueError('MESSAGE_ID must be a positive integer')
            if os.environ.get('MODO', 'completo') == 'resumo':
                # Uma ficha é o produto principal. O operador pode pedir exportação separadamente.
                message = await entregar_ficha(bot, destination, data, message_id or None)
                receipt(message)
            else:
                for index, page in enumerate(basic_pages(report_identity, [], [])):
                    if index == 0 and message_id:
                        response = await asyncio.to_thread(bot.call, 'editMessageText', {'chat_id': int(destination), 'message_id': int(message_id), 'text': page, 'parse_mode': 'HTML'})
                        message = response.require()
                    else:
                        message = await asyncio.to_thread(bot.send_message, int(destination), page, parse_mode='HTML')
                    receipt(message)
                for media in data.media:
                    if media.get('category') == 'profile' and media.get('status') == 'downloaded':
                        message = await asyncio.to_thread(bot.upload, 'sendPhoto', int(destination), Path(media['path']).read_bytes(), 'profile.jpg', 'image/jpeg')
                        receipt(message)
                for path in files + [Path(p) for p in archives]:
                    content = path.read_bytes()
                    message = await asyncio.to_thread(bot.upload, 'sendDocument', int(destination), content, path.name, 'application/octet-stream', caption='SHA-256: ' + hashlib.sha256(content).hexdigest())
                    receipt(message)
            (directory / 'delivery.json').write_text(json.dumps(receipts, indent=2))
            registrar_notificacao({'ok': True, 'result': {'message_id': receipts[-1]['message_id'], 'chat': {'id': int(destination)}}}, destination)
        persist_state(state='partial' if data.partial else 'completed', delivery='api_accepted' if receipts else 'not_requested')
        print(json.dumps({'state': 'partial' if data.partial else 'completed', 'delivery': 'api_accepted' if receipts else 'not_requested', 'accepted_messages': len(receipts)}), flush=True)
        return 2 if data.partial else 0
    except BaseException as error:
        persist_state(state='interrupted' if isinstance(error, (asyncio.CancelledError, KeyboardInterrupt)) else 'failed', diagnostic=diagnostico_excecao(error), delivery='reconcile_required' if operation['delivery'] == 'submitting' else operation['delivery'])
        raise
    finally:
        if own_client and client is not None:
            await client.disconnect()
            client.session.close()


async def principal():
    try:
        return await workflow()
    except Exception as error:
        print(json.dumps({'state': 'failed', **diagnostico_excecao(error)}), flush=True)
        return 1


if __name__ == '__main__':
    sys.exit(asyncio.run(principal()))
