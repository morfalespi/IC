"""Controlled HTTP integration and installed-Telethon object regression tests.

The local server is a protocol fixture, not the Telegram service. MTProto
responses use installed TL objects; these tests do not claim live authentication.
"""
import asyncio
import contextlib
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import bot_api
from bot_api import BotClient, BotResult, APIProtocolError, BotAPIRequestError
from fixtures import FakeMTProto, TelegramFixture
import ic
import resolver
from exportacao import disclosure, valor_exportavel
from ficha_completa import basic_pages, jsonl_files, markdown_files
from mtproto_export import build_media_archives
from telethon import errors
from telethon.tl.types import User, Chat, Channel, InputPeerUser, InputPeerChat, InputPeerChannel, PeerUser, Message, Photo, ChannelParticipant
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetFullChannelRequest, GetParticipantsRequest
from telethon.tl.functions.messages import GetFullChatRequest, GetHistoryRequest
from telethon.tl.functions.photos import GetUserPhotosRequest


def read_report(records):
    report = {}
    for row in records:
        if 'index' in row:
            report.setdefault(row['category'], []).append(row['value'])
        else:
            report[row['category']] = row['value']
    return report


class SimpleTL:
    def __init__(self, value):
        self.value = value
    def to_dict(self):
        return self.value


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.telegram = TelegramFixture()

    @classmethod
    def tearDownClass(cls):
        cls.telegram.close()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {'BOT_TOKEN': 'fixture-token', 'CHAT_ID': '42', 'ALVO': 'alice', 'EXPECTED_ID': '42', 'IC_STATE_DIR': str(self.root / 'state'), 'IC_OUTPUT_DIR': str(self.root / 'exports'), 'IC_CATEGORIES': '', 'MESSAGE_IDS': '', 'MODO': 'completo', 'ALLOWED_USER_IDS': '42', 'ALLOWED_CHAT_IDS': '42', 'RUNNER_TEMP': str(self.root)}, clear=True)
        self.env.start()
        bot_api.OPERATION_ID = self.id()
        self.telegram.requests.clear()
        self.telegram.files.clear()
        self.telegram.responses.clear()
        self.telegram.updates.clear()
        self.bot = BotClient(opener=self.telegram.open, sleeper=lambda _: None)

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_required_methods_real_http_and_multipart(self):
        self.assertTrue(self.bot.get_me()['is_bot'])
        self.assertEqual(self.bot.get_chat(42)['id'], 42)
        self.assertIn('message_id', self.bot.send_message(42, 'Hello <&>'))
        for method, filename, mime in [('sendPhoto', 'photo.png', 'image/png'), ('sendDocument', 'report.jsonl', 'application/x-ndjson')]:
            content = b'fixture content\n'
            response = self.bot.upload(method, 42, content, filename, mime)
            file = response['document'] if method == 'sendDocument' else response['photo'][0]
            downloaded, digest = self.bot.download(file['file_id'])
            self.assertEqual(downloaded, content)
            self.assertEqual(digest, hashlib.sha256(content).hexdigest())
        self.assertTrue({'getMe', 'getChat', 'sendMessage', 'sendPhoto', 'sendDocument', 'getFile'} <= {m for m, _ in self.telegram.requests})

    def test_complete_normal_entrypoint(self):
        fake = FakeMTProto()
        with patch('resolver.BotClient', return_value=self.bot), patch('resolver.open_client', return_value=fake), contextlib.redirect_stdout(io.StringIO()) as output:
            code = asyncio.run(resolver.principal())
        self.assertEqual(code, 0, output.getvalue())
        self.assertTrue(fake.disconnected)
        self.assertEqual(fake.history_offsets, [0, 4])
        reports = list((self.root / 'exports').glob('*/report_1.jsonl'))
        self.assertEqual(len(reports), 1)
        records = [json.loads(line) for line in reports[0].read_text().splitlines()]
        report = read_report(records)
        self.assertEqual(report['canonical_id'], 42)
        self.assertEqual(report['entity']['access_hash'], '[REDACTED]')
        self.assertEqual(report['entity']['phone'], '[REDACTED]')
        self.assertEqual(report['messages'][0]['message'], 'First <&>')
        self.assertEqual(fake.entity.access_hash, 987654)
        self.assertEqual(report['completeness'], 'complete_available')
        self.assertIn('api_accepted', output.getvalue())
        self.assertNotIn('Alice', output.getvalue())
        print('LOCAL FLOW: synthetic identity, controlled MTProto replies, 2 pages, exports and loopback HTTP receipts')

    def test_partial_restriction_exit_and_export(self):
        fake = FakeMTProto(fail_history=True)
        with patch('resolver.BotClient', return_value=self.bot), patch('resolver.open_client', return_value=fake), contextlib.redirect_stdout(io.StringIO()):
            code = asyncio.run(resolver.principal())
        self.assertEqual(code, 2)
        report = read_report(map(json.loads, next((self.root / 'exports').glob('*/report_1.jsonl')).read_text().splitlines()))
        self.assertEqual(report['collections']['messages']['state'], 'restricted')
        self.assertEqual(report['completeness'], 'partial')

    def test_expected_id_stops_before_acquisition_or_delivery(self):
        fake = FakeMTProto()
        os.environ['EXPECTED_ID'] = '43'
        with patch('resolver.BotClient', return_value=self.bot), patch('resolver.open_client', return_value=fake), contextlib.redirect_stdout(io.StringIO()):
            code = asyncio.run(resolver.principal())
        self.assertEqual(code, 1)
        self.assertFalse(any(isinstance(c, GetFullUserRequest) for c in fake.calls))
        self.assertEqual([m for m, _ in self.telegram.requests], ['getMe'])

    def test_canonical_entity_kinds(self):
        for entity, expected, kind in [
            (User(id=42, access_hash=5, bot=True), 42, 'bot'),
            (Chat(id=7, title='Group', photo=None, participants_count=1, date=None, version=1), -7, 'basic_group'),
            (Channel(id=8, title='Super', photo=None, date=None, access_hash=5, megagroup=True), -1000000000008, 'supergroup'),
            (Channel(id=8, title='Channel', photo=None, date=None, access_hash=5, broadcast=True), -1000000000008, 'channel'),
        ]:
            actual, peer = asyncio.run(resolver.resolver_alvo(FakeMTProto(entity), str(expected), expected))
            self.assertEqual(resolver.entity_kind(actual), kind)
            self.assertEqual(resolver.utils.get_peer_id(peer), expected)

    def test_no_zero_hash_fallback(self):
        fake = FakeMTProto()
        async def unavailable(value):
            raise ValueError('Not in session')
        fake.get_input_entity = unavailable
        with self.assertRaises(LookupError):
            asyncio.run(resolver.resolver_alvo(fake, '-1000000000008'))

    def test_message_ids_inaccessible_are_partial(self):
        fake = FakeMTProto()
        data = resolver.Acquisition(42, 'user', fake.entity)
        asyncio.run(resolver.collect_messages(fake, InputPeerUser(42, 1), data, [5, 999]))
        self.assertEqual(data.collections['messages'].state, 'partial')
        self.assertEqual(data.collections['messages'].records, 1)

    def test_repeated_page_and_interrupt_keep_successful_pages(self):
        for outcome in ('repeat', 'interrupt', 'exhaust'):
            state = resolver.Collection('fixture')
            async def fetch(offset):
                if offset and outcome == 'interrupt':
                    raise OSError('interrupted')
                return SimpleNamespace(count=5, items=[1, 2] if not offset or outcome == 'repeat' else [])
            rows = asyncio.run(resolver.paginated(state, fetch, lambda r: r.items, lambda i: i))
            self.assertEqual(rows, [1, 2])
            self.assertEqual(state.state, 'partial')
            self.assertEqual(state.pages, 1 if outcome == 'interrupt' else 2)

    def test_participants_pagination_actual_request_types(self):
        entity = Channel(id=8, title='Test', photo=None, date=None, access_hash=19, megagroup=True)
        fake = FakeMTProto(entity)
        data = asyncio.run(resolver.acquire(fake, '-1000000000008', self.root, categories={'participants'}))
        self.assertEqual(data.collections['participants'].state, 'complete')
        requests = [c for c in fake.calls if isinstance(c, GetParticipantsRequest)]
        self.assertEqual([r.offset for r in requests], [0, 2] * 5)
        self.assertEqual(requests[0].channel.access_hash, 19)

    def test_invalid_envelopes_and_non_json_never_succeed(self):
        for response in [b'html error', {'result': {}}, {'ok': True}, {'ok': True, 'result': []}, {'ok': False, 'description': 'bad'}]:
            self.telegram.responses.append((200, response))
            with self.assertRaises(APIProtocolError):
                self.bot.get_me()

    def test_401_403_parameters_and_rate_limit(self):
        for code in (401, 403):
            self.telegram.responses.append((code, {'ok': False, 'error_code': code, 'description': 'Denied', 'parameters': {'migrate_to_chat_id': -1000000000088}}))
            result = self.bot.call('getChat', {'chat_id': 42})
            self.assertEqual(result.error_code, code)
            self.assertIn('migrate_to_chat_id', result.parameters)
            with self.assertRaises(BotAPIRequestError):
                result.require()
        self.telegram.responses.append((429, {'ok': False, 'error_code': 429, 'description': 'Wait', 'parameters': {'retry_after': 0}}))
        self.assertTrue(self.bot.get_me()['is_bot'])

    def test_send_retry_only_definite_429(self):
        self.telegram.responses.append((429, {'ok': False, 'error_code': 429, 'description': 'Wait', 'parameters': {'retry_after': 0}}))
        self.bot.send_message(42, 'rate limited')
        self.assertEqual(len(self.telegram.requests), 2)
        self.telegram.responses.append((500, {'ok': False, 'error_code': 500, 'description': 'Internal'}))
        with self.assertRaises(BotAPIRequestError):
            self.bot.send_message(42, 'server failure')
        self.assertEqual(len(self.telegram.requests), 3)

    def test_uncertain_send_and_duplicate_guard(self):
        calls = []
        def failing(request, timeout):
            calls.append(request)
            raise urllib.error.URLError('connection lost')
        bot = BotClient(opener=failing, sleeper=lambda _: None)
        for _ in range(2):
            with self.assertRaises(BotAPIRequestError):
                bot.send_message(42, 'uncertain')
        self.assertEqual(len(calls), 1)
        self.bot.send_message(42, 'certain')
        self.bot.send_message(42, 'certain')
        self.assertEqual(len(self.telegram.requests), 1)

    def test_destination_authorization_and_mismatch(self):
        for destination in ('43', '@alice', '', '42\r\nx'):
            with self.assertRaises(PermissionError):
                self.bot.send_message(destination, 'must not send')
        self.assertEqual(self.telegram.requests, [])
        self.telegram.responses.append((200, {'ok': True, 'result': {'message_id': 1, 'chat': {'id': 43}}}))
        with self.assertRaises(APIProtocolError):
            self.bot.send_message(42, 'wrong returned chat')

    def test_no_delivery_when_destination_absent(self):
        os.environ['CHAT_ID'] = ''
        os.environ['MODO'] = 'resumo'
        with contextlib.redirect_stdout(io.StringIO()):
            code = asyncio.run(resolver.workflow(self.bot, FakeMTProto()))
        self.assertEqual(code, 0)
        self.assertFalse(any(m.startswith('send') for m, _ in self.telegram.requests))
        self.assertTrue(list((self.root / 'exports').glob('*/*.jsonl')))

    def test_delivery_validation_normal_entry(self):
        import validar_entrega
        with patch('validar_entrega.BotClient', return_value=self.bot), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(asyncio.run(validar_entrega.principal()), 0, output.getvalue())
        result = json.loads(output.getvalue())
        self.assertEqual(result['accepted_messages'], 5)
        self.assertEqual(result['retrieved_uploads'], 4)
        self.assertEqual(result['verified_documents'], 3)
        self.assertEqual(sum(m == 'getFile' for m, _ in self.telegram.requests), 4)
        print('CONTROLLED DELIVERY: text, PNG, Markdown, JSONL, ZIP; all 4 uploads retrieved and hashed')

    def test_polling_normal_entry_authorized_and_denied_updates(self):
        self.telegram.updates = [
            {'update_id': 1, 'message': {'from': {'id': 99}, 'chat': {'id': 42}, 'text': '/export alice'}},
            {'update_id': 2, 'message': {'from': {'id': 42}, 'chat': {'id': 42}, 'text': '/info alice 42'}},
        ]
        fake = FakeMTProto()
        with patch('ic.BotClient', return_value=self.bot), patch('resolver.open_client', return_value=fake), patch.object(sys, 'argv', ['ic.py', 'bot', '--once']), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(asyncio.run(ic.main()), 0, output.getvalue())
        self.assertIn('operational', output.getvalue())
        self.assertIn('update_denied', output.getvalue())
        self.assertEqual(sum(isinstance(c, GetFullUserRequest) for c in fake.calls), 1)
        # A replay never reruns acquisition or sends another report.
        count = len(self.telegram.requests)
        with contextlib.redirect_stdout(io.StringIO()):
            asyncio.run(ic.polling(self.bot, fake, once=True))
        self.assertFalse(any(m.startswith('send') for m, _ in self.telegram.requests[count:]))
        store = ic.UpdateStore()
        self.assertEqual(store.offset(), 3)
        store.db.close()
        print('LOCAL STARTUP: ic.py bot --once with injected clients; authorization and replay cases passed')

    def test_archive_integrity_and_split(self):
        items = []
        for i in range(2):
            path = self.root / f'{i}.bin'
            payload = b'12345'
            path.write_bytes(payload)
            items.append({'path': str(path), 'name': path.name, 'category': 'test', 'bytes': 5, 'sha256': hashlib.sha256(payload).hexdigest(), 'status': 'downloaded'})
        archives = build_media_archives(items, self.root, max_batch_bytes=5)
        self.assertEqual(len(archives), 2)
        for path in archives:
            with zipfile.ZipFile(path) as archive:
                self.assertIn('manifest.json', archive.namelist())
        (self.root / '0.bin').write_bytes(b'other')
        with self.assertRaises(ValueError):
            build_media_archives(items, self.root)

    def test_encoders_preserve_values_and_bound_outputs(self):
        original = {'name': '<Alice & Bob>', 'nested': {'phone': '555', 'access_hash': 123}, 'id': -1000000000008, 'flag': False, 'null': None}
        safe = disclosure(valor_exportavel(original))
        self.assertEqual(original['nested']['access_hash'], 123)
        self.assertEqual(safe['nested']['access_hash'], '[REDACTED]')
        records = [json.loads(line) for line in jsonl_files([safe])[0].decode().splitlines()]
        self.assertIs(records[0]['flag'], False)
        self.assertEqual(records[0]['id'], -1000000000008)
        pages = basic_pages([('<key>', '&<>😀' * 3000)], [], [])
        self.assertGreater(len(pages), 1)
        self.assertTrue(all(len(p.encode('utf-16-le')) // 2 <= 4096 for p in pages))
        self.assertNotIn('<key>', ''.join(pages))
        md = markdown_files([('# heading', '```\nvalue\n```')], [], [])[0].decode()
        self.assertIn('````text', md)
        self.assertIn('\\# heading', md)

    def test_diagnostics_redact_and_no_profile_logging(self):
        os.environ['BOT_TOKEN'] = '123456:secret_value_that_must_not_appear'
        diagnostic = bot_api.diagnostico_excecao(RuntimeError('https://api.telegram.org/bot' + os.environ['BOT_TOKEN']))
        self.assertNotIn(os.environ['BOT_TOKEN'], json.dumps(diagnostic))
        diagnostic = bot_api.diagnostico_api({'ok': True, 'result': {'first_name': 'Alice', 'phone': '555'}}, 'getChat')
        self.assertNotIn('Alice', json.dumps(diagnostic))

    def test_optional_metadata_categories_installed_tl_objects(self):
        from metadata import acquire_metadata, acquire_bot_details, cursor_pages
        from telethon.tl import types
        from telethon.tl.functions import users, payments, premium, channels, messages
        from datetime import datetime, timezone
        doc = types.Document(id=9, access_hash=13, file_reference=b'capability', date=datetime.now(timezone.utc), mime_type='audio/mpeg', size=4, dc_id=2, attributes=[])
        gift = types.StarGift(id=10, sticker=doc, stars=5, convert_stars=2)
        saved = types.SavedStarGift(date=datetime.now(timezone.utc), gift=gift)
        requests = []
        async def call(request):
            requests.append(request)
            if isinstance(request, users.GetSavedMusicRequest):
                return types.users.SavedMusic(count=1, documents=[doc] if request.offset == 0 else [])
            if isinstance(request, payments.GetSavedStarGiftsRequest):
                return types.payments.SavedStarGifts(count=1, gifts=[saved], chats=[], users=[])
            if isinstance(request, payments.GetStarGiftsRequest):
                return types.payments.StarGifts(hash=1, gifts=[gift], chats=[], users=[])
            if isinstance(request, premium.GetBoostsStatusRequest):
                return types.premium.BoostsStatus(level=1, current_level_boosts=2, boosts=3, boost_url='https://t.me/boost/test')
            if isinstance(request, premium.GetBoostsListRequest):
                return types.premium.BoostsList(count=0, boosts=[], users=[])
            if isinstance(request, channels.GetParticipantRequest):
                return types.channels.ChannelParticipant(participant=types.ChannelParticipantSelf(user_id=777, inviter_id=42, date=None), chats=[], users=[])
            if isinstance(request, messages.GetCustomEmojiDocumentsRequest):
                return [doc]
            if isinstance(request, messages.GetStickerSetRequest):
                return SimpleTL({'documents': [doc.to_dict()]})
            if isinstance(request, messages.GetForumTopicsByIDRequest):
                return SimpleNamespace(topics=[SimpleTL({'id': 7})])
            raise AssertionError(type(request))
        class Client:
            async def __call__(self, request):
                return await call(request)
        user = User(id=42, access_hash=17, username='alice', emoji_status=types.EmojiStatus(document_id=19))
        data = resolver.Acquisition(42, 'user', user)
        output = asyncio.run(acquire_metadata(Client(), InputPeerUser(42, 17), data, {'music', 'gifts', 'catalog', 'stickers', 'topics'}, 10))
        self.assertEqual(data.collections['music'].records, 1)
        self.assertEqual(data.collections['gifts'].state, 'complete')
        self.assertIn('custom_emoji_0', output)
        self.assertEqual(output['music'][0].id, 9)
        self.assertNotIn('capability', json.dumps(disclosure(valor_exportavel(output))))
        channel = Channel(id=8, title='Forum', photo=None, date=None, access_hash=77, megagroup=True, forum=True)
        data = resolver.Acquisition(-1000000000008, 'supergroup', channel)
        data.messages = [SimpleNamespace(reply_to=SimpleNamespace(forum_topic=True, reply_to_top_id=7, reply_to_msg_id=8))]
        output = asyncio.run(acquire_metadata(Client(), InputPeerChannel(8, 77), data, {'boosts', 'topics'}, 10))
        self.assertEqual(data.collections['boosts'].state, 'complete')
        self.assertEqual(data.collections['topics'].records, 1)
        self.assertEqual(data.collections['bot_membership'].state, 'complete')
        # Both metadata Bot API request families run through the actual HTTP client.
        for entity in [user, channel]:
            data = resolver.Acquisition(resolver.utils.get_peer_id(entity), resolver.entity_kind(entity), entity)
            if isinstance(entity, User):
                self.telegram.responses.extend([(200, {'ok': True, 'result': {'total_count': 0, 'photos': []}}), (200, {'ok': True, 'result': {'total_count': 0, 'audios': []}})])
            else:
                self.telegram.responses.extend([(200, {'ok': True, 'result': []}), (200, {'ok': True, 'result': 3})])
            asyncio.run(acquire_bot_details(self.bot, data, 10))
            self.assertTrue(all(c.state == 'complete' for c in data.collections.values()))
        print('CONTROLLED METADATA: music, saved gifts, catalog, custom emoji, boosts, membership, known topics and Bot API profile/chat metadata')

    def test_cursor_metadata_repetition_and_interruption(self):
        from metadata import cursor_pages
        for interrupted in [True, False]:
            state = resolver.Collection('cursor')
            async def fetch(cursor):
                if cursor and interrupted:
                    raise OSError('network')
                return SimpleNamespace(gifts=[1], count=5, next_offset='repeat')
            pages = asyncio.run(cursor_pages(state, fetch, records_field='gifts', max_pages=10))
            self.assertEqual(state.state, 'partial')
            self.assertEqual(state.pages, 1 if interrupted else 2)
            self.assertEqual(len(pages), state.pages)

    def test_media_download_and_verified_archive(self):
        from telethon.tl.types import Document
        document = Document(id=8, access_hash=9, file_reference=b'x', date=None, mime_type='text/plain', size=7, dc_id=2, attributes=[])
        fake = FakeMTProto()
        async def get_messages(peer, ids):
            from telethon.tl.types import MessageMediaDocument
            return [Message(id=5, peer_id=PeerUser(42), message='attached', media=MessageMediaDocument(document=document))]
        async def download_media(obj, file, progress_callback):
            progress_callback(7, 7)
            Path(file).write_bytes(b'payload')
            return file
        fake.get_messages = get_messages
        fake.download_media = download_media
        data = asyncio.run(resolver.acquire(fake, 'alice', self.root, categories={'messages', 'media'}, message_ids=[5]))
        self.assertEqual(data.media[0]['sha256'], hashlib.sha256(b'payload').hexdigest())
        self.assertFalse(data.partial)
        archives = build_media_archives(data.media, self.root)
        self.assertEqual(len(archives), 1)

    def test_mtproto_authentication_actual_constructor_and_session(self):
        from unittest.mock import AsyncMock
        os.environ.update(API_ID='12345', API_HASH='a' * 32, TELETHON_SESSION_DIR=str(self.root / 'sessions'))
        me = User(id=777, first_name='Bot', bot=True)
        async def run():
            with patch.object(resolver.TelegramClient, 'connect', new_callable=AsyncMock) as connect, \
                 patch.object(resolver.TelegramClient, 'is_user_authorized', new_callable=AsyncMock, return_value=False), \
                 patch.object(resolver.TelegramClient, 'sign_in', new_callable=AsyncMock) as signin, \
                 patch.object(resolver.TelegramClient, 'get_me', new_callable=AsyncMock, return_value=me), \
                 patch.object(resolver.TelegramClient, 'disconnect', new_callable=AsyncMock):
                client = await resolver.open_client(self.bot)
                self.assertIsInstance(client, resolver.TelegramClient)
                connect.assert_awaited_once()
                signin.assert_awaited_once_with(bot_token='fixture-token')
                client.session.close()
        asyncio.run(run())
        sessions = list((self.root / 'sessions').glob('*.session'))
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0].stat().st_mode & 0o777, 0o600)

    def test_mtproto_session_identity_mismatch_is_rejected(self):
        from unittest.mock import AsyncMock
        os.environ.update(API_ID='12345', API_HASH='a' * 32, TELETHON_SESSION_DIR=str(self.root / 'sessions'))
        async def run():
            with patch.object(resolver.TelegramClient, 'connect', new_callable=AsyncMock), \
                 patch.object(resolver.TelegramClient, 'is_user_authorized', new_callable=AsyncMock, return_value=True), \
                 patch.object(resolver.TelegramClient, 'get_me', new_callable=AsyncMock, return_value=User(id=888, bot=True)), \
                 patch.object(resolver.TelegramClient, 'disconnect', new_callable=AsyncMock) as disconnect:
                with self.assertRaises(PermissionError):
                    await resolver.open_client(self.bot)
                disconnect.assert_awaited_once()
        asyncio.run(run())

    def test_delivery_journal_is_scoped_to_bot_credentials(self):
        self.bot.send_message(42, 'same logical request')
        second = BotClient(token='different-local-bot-token', opener=self.telegram.open)
        second.send_message(42, 'same logical request')
        self.assertEqual(len(self.telegram.requests), 2)

    def test_update_throttle_persists_and_invalid_command_gets_feedback(self):
        store = ic.UpdateStore()
        self.assertTrue(store.reserve_command('42'))
        self.assertFalse(store.reserve_command('42'))
        store.db.close()
        self.telegram.updates = [{'update_id': 1, 'message': {'from': {'id': 42}, 'chat': {'id': 42}, 'text': 'invalid'}}]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(asyncio.run(ic.polling(self.bot, FakeMTProto(), once=True)), 1)
        sent = [fields for method, fields in self.telegram.requests if method == 'sendMessage']
        self.assertEqual(len(sent), 1)
        self.assertIn('/info', sent[0]['text'])

    def test_existing_status_message_is_edited_through_workflow(self):
        os.environ.update(MESSAGE_ID='123', MODO='resumo')
        with contextlib.redirect_stdout(io.StringIO()):
            code = asyncio.run(resolver.workflow(self.bot, FakeMTProto()))
        self.assertEqual(code, 0)
        edits = [fields for method, fields in self.telegram.requests if method == 'editMessageText']
        self.assertEqual(len(edits), 1)
        self.assertEqual(edits[0]['message_id'], 123)
        self.assertFalse(any(method == 'sendMessage' for method, _ in self.telegram.requests))

    def test_polling_failed_operation_returns_failure_and_notifies(self):
        self.telegram.updates = [{'update_id': 10, 'message': {'from': {'id': 42}, 'chat': {'id': 42}, 'text': '/export alice'}}]
        fake = FakeMTProto()
        async def unavailable(peer):
            raise ValueError('Unknown entity')
        fake.get_input_entity = unavailable
        with contextlib.redirect_stdout(io.StringIO()):
            code = asyncio.run(ic.polling(self.bot, fake, once=True))
        self.assertEqual(code, 1)
        sent = [fields for method, fields in self.telegram.requests if method == 'sendMessage']
        self.assertEqual(len(sent), 1)
        self.assertIn('não concluiu', sent[0]['text'])

    def test_bot_metadata_media_is_downloaded_and_packaged_in_normal_path(self):
        self.telegram.files['from_profile'] = b'profile audio bytes'
        data = resolver.Acquisition(42, 'user', FakeMTProto().entity)
        data.metadata = {'bot_details': {'getUserProfileAudios': [{'audios': [{'file_id': 'from_profile', 'file_unique_id': 'audio_unique'}]}]}}
        asyncio.run(resolver.collect_bot_media(self.bot, data, self.root))
        self.assertEqual(data.collections['bot_media'].state, 'complete')
        self.assertEqual(Path(data.media[0]['path']).read_bytes(), b'profile audio bytes')
        self.assertEqual(data.media[0]['sha256'], hashlib.sha256(b'profile audio bytes').hexdigest())
        archives = build_media_archives(data.media, self.root)
        self.assertEqual(len(archives), 1)
        self.assertIn('getFile', [m for m, _ in self.telegram.requests])

    def test_full_metadata_wrong_identity_is_fatal(self):
        fake = FakeMTProto()
        original = fake.__class__.__call__
        async def wrong(client, request):
            value = await original(client, request)
            if isinstance(request, GetFullUserRequest):
                value.full_user.id = 43
            return value
        with patch.object(FakeMTProto, '__call__', wrong):
            with self.assertRaises(LookupError):
                asyncio.run(resolver.acquire(fake, 'alice', self.root, categories={'metadata'}))

    def test_bad_getfile_path_and_size(self):
        for file in [dict(file_id='x', file_unique_id='unique', file_path='../secret'), dict(file_id='x', file_unique_id='unique', file_path='files/x', file_size=8)]:
            self.telegram.responses.append((200, {'ok': True, 'result': file}))
            self.telegram.files['x'] = b'bad'
            with self.assertRaises(APIProtocolError):
                self.bot.download('x')


if __name__ == '__main__':
    unittest.main()
