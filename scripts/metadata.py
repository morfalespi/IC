"""Additional explicit metadata categories, using Telethon 1.45 request contracts."""
import asyncio
from telethon import errors, utils
from telethon.tl.types import User, Channel, InputStickerSetID
from telethon.tl.functions.users import GetSavedMusicRequest
from telethon.tl.functions.payments import GetSavedStarGiftsRequest, GetStarGiftsRequest
from telethon.tl.functions.premium import GetBoostsListRequest, GetBoostsStatusRequest
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.functions.messages import GetCustomEmojiDocumentsRequest, GetStickerSetRequest, GetForumTopicsByIDRequest
from telethon.tl.types import InputPeerSelf

EXTRA_CATEGORIES = {'music', 'gifts', 'catalog', 'boosts', 'stickers', 'topics', 'bot_details'}


async def cursor_pages(state, fetch, *, records_field, max_pages):
    from resolver import interrupted
    pages, seen, cursor = [], set(), ''
    try:
        for _ in range(max_pages):
            result = await fetch(cursor)
            page = getattr(result, records_field)
            pages.append(result)
            state.pages += 1
            state.records += len(page)
            count = getattr(result, 'count', None)
            if isinstance(count, int):
                state.expected = max(state.expected or 0, count)
            next_cursor = getattr(result, 'next_offset', None) or ''
            if not next_cursor:
                state.state = 'partial' if state.expected is not None and state.records < state.expected else 'complete'
                if state.state == 'partial':
                    state.reason = 'Cursor exhausted before advertised count'
                break
            if next_cursor == cursor or next_cursor in seen:
                state.state, state.reason = 'partial', 'Repeated cursor'
                break
            seen.add(cursor)
            cursor = next_cursor
        else:
            state.state, state.reason = 'partial', 'Configured page limit reached'
    except (errors.RPCError, OSError, asyncio.TimeoutError, ValueError) as error:
        interrupted(state, error)
    return pages


async def acquire_metadata(client, peer, data, categories, max_pages):
    from resolver import Collection, paginated, interrupted
    output = {}
    async def single(name, request):
        state = data.collections[name] = Collection(type(request).__name__)
        try:
            result = await client(request)
            state.pages, state.records, state.state = 1, 1, 'complete'
            output[name] = result
            return result
        except (errors.RPCError, OSError, asyncio.TimeoutError, ValueError) as error:
            interrupted(state, error)
            return None
    if 'music' in categories:
        state = data.collections['music'] = Collection('users.getSavedMusic')
        if isinstance(data.entity, User):
            async def fetch(offset):
                return await client(GetSavedMusicRequest(utils.get_input_user(peer), offset, 100, 0))
            output['music'] = await paginated(state, fetch, lambda r: r.documents, lambda d: d.id, max_pages=max_pages)
        else:
            state.state, state.reason = 'not_requested', 'Profile music applies to users'
    if 'gifts' in categories:
        state = data.collections['gifts'] = Collection('payments.getSavedStarGifts')
        async def fetch(cursor):
            return await client(GetSavedStarGiftsRequest(peer, cursor, 100))
        output['gifts'] = await cursor_pages(state, fetch, records_field='gifts', max_pages=max_pages)
    if 'catalog' in categories:
        await single('gift_catalog', GetStarGiftsRequest(hash=0))
    if 'boosts' in categories:
        if isinstance(data.entity, Channel):
            await single('boost_status', GetBoostsStatusRequest(peer))
            state = data.collections['boosts'] = Collection('premium.getBoostsList')
            async def fetch(cursor):
                return await client(GetBoostsListRequest(peer, cursor, 100))
            output['boosts'] = await cursor_pages(state, fetch, records_field='boosts', max_pages=max_pages)
            await single('bot_membership', GetParticipantRequest(utils.get_input_channel(peer), InputPeerSelf()))
        else:
            data.collections['boosts'] = Collection('premium.getBoostsList', 'not_requested', reason='Boosts apply to channels and supergroups')
    if 'topics' in categories:
        ids = sorted({getattr(getattr(m, 'reply_to', None), 'reply_to_top_id', None) or getattr(getattr(m, 'reply_to', None), 'reply_to_msg_id', None) for m in data.messages if getattr(getattr(m, 'reply_to', None), 'forum_topic', False)} - {None})
        state = data.collections['topics'] = Collection('messages.getForumTopicsByID')
        if isinstance(data.entity, Channel) and data.entity.forum and ids:
            pages = []
            try:
                for start in range(0, len(ids), 100):
                    result = await client(GetForumTopicsByIDRequest(peer, ids[start:start + 100]))
                    pages.append(result)
                    state.pages += 1
                    state.records += len(result.topics)
                state.expected = len(ids)
                state.state = 'complete' if state.records == len(ids) else 'partial'
                state.reason = 'Only topic IDs referenced in the collected messages were requested'
            except (errors.RPCError, OSError, asyncio.TimeoutError, ValueError) as error:
                interrupted(state, error)
            output['topics'] = pages
        else:
            state.state, state.reason = 'not_requested', 'No known forum topic IDs in the collected messages'
    if 'stickers' in categories:
        # Only references returned within the authorized target's data are followed.
        from exportacao import valor_exportavel
        serialized = valor_exportavel({'entity': data.entity, 'full': data.full, 'messages': data.messages, 'music': output.get('music', [])})
        emojis, sets = set(), set()
        def visit(value):
            if isinstance(value, dict):
                constructor = value.get('_')
                if constructor in {'MessageEntityCustomEmoji', 'EmojiStatus', 'EmojiStatusCollectible'} and isinstance(value.get('document_id'), int):
                    emojis.add(value['document_id'])
                if constructor == 'InputStickerSetID' and isinstance(value.get('id'), int) and isinstance(value.get('access_hash'), int):
                    sets.add((value['id'], value['access_hash']))
                for item in value.values():
                    visit(item)
            elif isinstance(value, list):
                for item in value:
                    visit(item)
        visit(serialized)
        for index, start in enumerate(range(0, len(emojis), 200)):
            documents = await single(f'custom_emoji_{index}', GetCustomEmojiDocumentsRequest(sorted(emojis)[start:start + 200]))
            if documents is not None:
                visit(valor_exportavel(documents))
        for index, (set_id, access_hash) in enumerate(sorted(sets)):
            await single(f'sticker_set_{index}', GetStickerSetRequest(InputStickerSetID(set_id, access_hash), hash=0))
        if not emojis and not sets:
            data.collections['stickers'] = Collection('getCustomEmojiDocuments/getStickerSet', 'not_requested', reason='No emoji or sticker-set references returned')
    return output


async def acquire_bot_details(bot, data, max_pages):
    """Bot-only metadata, subject to Bot API visibility independently of MTProto."""
    from resolver import Collection, interrupted
    from bot_api import BotAPIRequestError
    output = {}
    async def call(method, payload):
        result = await asyncio.to_thread(bot.call, method, payload)
        return result.require()
    if isinstance(data.entity, User):
        requests = [('getUserProfilePhotos', 'photos'), ('getUserProfileAudios', 'audios')]
        for method, key in requests:
            state = data.collections[method] = Collection(method)
            pages, seen, offset = [], set(), 0
            try:
                for _ in range(max_pages):
                    result = await call(method, {'user_id': data.entity.id, 'offset': offset, 'limit': 100})
                    page = result[key]
                    pages.append(result)
                    state.pages += 1
                    state.expected = result.get('total_count')
                    if not page:
                        state.state = 'partial' if state.expected is not None and offset < state.expected else 'complete'
                        break
                    # File capabilities are stable enough for cycle detection within this request.
                    signature = str(page)
                    if signature in seen:
                        state.state, state.reason = 'partial', 'Repeated page'
                        break
                    seen.add(signature)
                    offset += len(page)
                    state.records = offset
                    if state.expected is not None and offset >= state.expected:
                        state.state = 'complete'
                        break
                else:
                    state.state, state.reason = 'partial', 'Configured page limit reached'
            except (BotAPIRequestError, OSError, ValueError) as error:
                interrupted(state, error)
            output[method] = pages
    else:
        for method in ('getChatAdministrators', 'getChatMemberCount'):
            state = data.collections[method] = Collection(method)
            try:
                result = await call(method, {'chat_id': data.canonical_id, **({'return_bots': True} if method == 'getChatAdministrators' else {})})
                output[method] = result
                state.pages, state.records, state.state = 1, len(result) if isinstance(result, list) else 1, 'complete'
            except (BotAPIRequestError, OSError, ValueError) as error:
                interrupted(state, error)
    output.update(await acquire_bot_records(bot, data, max_pages))
    return output


async def acquire_bot_records(bot, data, max_pages):
    from resolver import Collection, interrupted
    from bot_api import BotAPIRequestError, APIProtocolError, validate_result_object
    output = {}
    async def read(method, payload, key=None):
        state = data.collections[key or method] = Collection(method)
        try:
            result = (await asyncio.to_thread(bot.call, method, payload)).require()
            output[key or method] = result
            state.pages, state.records, state.state = 1, len(result) if isinstance(result, list) else 1, 'complete'
            return result
        except (BotAPIRequestError, OSError, asyncio.TimeoutError) as error:
            interrupted(state, error)
            return None
    if isinstance(data.entity, User):
        messages = await read('getUserPersonalChatMessages', {'user_id': data.entity.id, 'limit': 20})
        if messages is not None:
            if not isinstance(messages, list):
                raise APIProtocolError('getUserPersonalChatMessages', {'ok': False, 'description': 'Expected Array of Message'})
            for message in messages:
                validate_result_object(message, 'Message')
            data.collections['getUserPersonalChatMessages'].reason = 'Latest 20 messages requested; this API method has no history cursor'
    else:
        me = await asyncio.to_thread(bot.get_me)
        await read('getChatMember', {'chat_id': data.canonical_id, 'user_id': me['id']}, 'bot_chat_membership')
        known_ids = set()
        for name, pages in data.metadata.items():
            if name.startswith('participants_'):
                for page in pages:
                    for participant in getattr(page, 'participants', []):
                        user_id = getattr(participant, 'user_id', None)
                        if user_id is None:
                            peer = getattr(participant, 'peer', None)
                            from telethon.tl.types import PeerUser
                            if isinstance(peer, PeerUser): user_id = peer.user_id
                        if user_id is not None:
                            known_ids.add(user_id)
        for user_id in sorted(known_ids):
            await read('getChatMember', {'chat_id': data.canonical_id, 'user_id': user_id}, f'chat_member_{user_id}')
            if isinstance(data.entity, Channel):
                await read('getUserChatBoosts', {'chat_id': data.canonical_id, 'user_id': user_id}, f'user_boosts_{user_id}')
    method = 'getUserGifts' if isinstance(data.entity, User) else 'getChatGifts'
    identifier = {'user_id': data.entity.id} if isinstance(data.entity, User) else {'chat_id': data.canonical_id}
    state = data.collections[method] = Collection(method)
    pages, seen, cursor = [], set(), ''
    try:
        for _ in range(max_pages):
            result = (await asyncio.to_thread(bot.call, method, {**identifier, 'offset': cursor, 'limit': 100})).require()
            if not isinstance(result, dict) or not isinstance(result.get('gifts'), list) or type(result.get('total_count')) is not int:
                raise APIProtocolError(method, {'ok': False, 'description': 'Invalid OwnedGifts response'})
            pages.append(result)
            state.pages += 1
            state.records += len(result['gifts'])
            state.expected = max(state.expected or 0, result['total_count'])
            next_cursor = result.get('next_offset', '')
            if not next_cursor:
                state.state = 'complete' if state.records >= state.expected else 'partial'
                if state.state == 'partial': state.reason = 'Gift cursor exhausted before total_count'
                break
            if not isinstance(next_cursor, str) or next_cursor == cursor or next_cursor in seen:
                state.state, state.reason = 'partial', 'Invalid or repeated gift cursor'
                break
            seen.add(cursor)
            cursor = next_cursor
        else:
            state.state, state.reason = 'partial', 'Configured page limit reached'
    except (BotAPIRequestError, OSError, asyncio.TimeoutError) as error:
        interrupted(state, error)
    output[method] = pages
    return output
