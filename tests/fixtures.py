"""Controlled test transport and stand-in MTProto requests."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
from types import SimpleNamespace
import urllib.request

from telethon import errors
from telethon.tl.types import (
    User, Chat, Channel, InputPeerUser, InputPeerChat, InputPeerChannel,
    PeerUser, Message, ChannelParticipant,
)
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetFullChannelRequest, GetParticipantsRequest
from telethon.tl.functions.messages import GetFullChatRequest, GetHistoryRequest
from telethon.tl.functions.photos import GetUserPhotosRequest

class TelegramFixture:
    def __init__(self):
        self.requests = []
        self.files = {}
        self.responses = []
        self.updates = []
        fixture = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                payload = fixture.files[self.path.rsplit('/', 1)[-1]]
                self.send_response(200)
                self.end_headers()
                self.wfile.write(payload)
            def do_POST(self):
                body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
                method = self.path.rsplit('/', 1)[-1]
                # Decode wire fields without calling IC's request parser.
                if self.headers.get_content_type() == 'application/json':
                    fields = json.loads(body)
                else:
                    from email.parser import BytesParser
                    from email.policy import default
                    multipart = BytesParser(policy=default).parsebytes(b'Content-Type: ' + self.headers['Content-Type'].encode() + b'\r\n\r\n' + body)
                    fields = {part.get_param('name', header='content-disposition'): part.get_payload(decode=True).decode() for part in multipart.iter_parts() if not part.get_filename()}
                fixture.requests.append((method, fields))
                status = 200
                if fixture.responses:
                    status, response = fixture.responses.pop(0)
                    if isinstance(response, bytes):
                        encoded = response
                    else:
                        encoded = json.dumps(response).encode()
                else:
                    if method == 'getMe':
                        result = {'id': 777, 'is_bot': True, 'first_name': 'FixtureBot'}
                    elif method == 'getChat':
                        value = int(fields['chat_id'])
                        result = {'id': value, 'type': 'private' if value > 0 else 'supergroup', 'first_name': 'Fixture', 'accent_color_id': 1, 'max_reaction_count': 1, 'accepted_gift_types': {key: False for key in ('unlimited_gifts', 'limited_gifts', 'unique_gifts', 'premium_subscription', 'gifts_from_channels')}}
                    elif method == 'getWebhookInfo':
                        result = {'url': '', 'has_custom_certificate': False, 'pending_update_count': 0}
                    elif method == 'getUpdates':
                        result = fixture.updates
                    elif method == 'getUserProfilePhotos':
                        result = {'total_count': 0, 'photos': []}
                    elif method == 'getUserProfileAudios':
                        result = {'total_count': 0, 'audios': []}
                    elif method == 'getUserPersonalChatMessages' or method == 'getChatAdministrators':
                        result = []
                    elif method in {'getUserGifts', 'getChatGifts'}:
                        result = {'total_count': 0, 'gifts': []}
                    elif method == 'getChatMemberCount':
                        result = 0
                    elif method == 'getChatMember':
                        result = {'status': 'member', 'user': {'id': fields['user_id'], 'is_bot': False, 'first_name': 'Example'}}
                    elif method == 'getUserChatBoosts':
                        result = {'boosts': []}
                    elif method == 'getAvailableGifts':
                        result = {'gifts': []}
                    elif method == 'getFile':
                        file_id = fields['file_id']
                        result = {'file_id': file_id, 'file_unique_id': file_id, 'file_size': len(fixture.files[file_id]), 'file_path': 'files/' + file_id}
                    else:
                        result = {'message_id': int(fields['message_id']) if method.startswith('editMessage') else len(fixture.requests), 'date': 123, 'chat': {'id': int(fields['chat_id']), 'type': 'private'}}
                        if method in {'sendPhoto', 'sendDocument'}:
                            from email.parser import BytesParser
                            from email.policy import default
                            message = BytesParser(policy=default).parsebytes(b'Content-Type: ' + self.headers['Content-Type'].encode() + b'\r\n\r\n' + body)
                            file = next(p for p in message.iter_parts() if p.get_filename())
                            payload = file.get_payload(decode=True)
                            file_id = 'file_' + str(len(fixture.files))
                            fixture.files[file_id] = payload
                            metadata = {'file_id': file_id, 'file_unique_id': file_id, 'file_size': len(payload)}
                            if method == 'sendPhoto':
                                metadata.update(width=64, height=64)
                                result['photo'] = [metadata]
                            else:
                                result['document'] = metadata
                    encoded = json.dumps({'ok': True, 'result': result}).encode()
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(encoded)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = 'http://127.0.0.1:' + str(self.server.server_port)
        self.transport = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def open(self, request, timeout):
        if isinstance(request, str):
            url = self.base + '/file/' + request.rsplit('/', 1)[-1]
            local = urllib.request.Request(url)
        else:
            local = urllib.request.Request(self.base + '/' + request.full_url.rsplit('/', 1)[-1], data=request.data, headers=dict(request.header_items()))
        return self.transport.open(local, timeout=timeout)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()


class FakeMTProto:
    def __init__(self, entity=None, fail_history=False):
        self.entity = entity or User(id=42, first_name='Alice <&>', username='alice', access_hash=987654, phone='5551234')
        self.fail_history = fail_history
        self.calls = []
        self.history_offsets = []
        self.session = SimpleNamespace(close=lambda: None)
        self.disconnected = False

    async def get_input_entity(self, value):
        self.calls.append(value)
        if isinstance(self.entity, Channel):
            return InputPeerChannel(self.entity.id, self.entity.access_hash)
        if isinstance(self.entity, Chat):
            return InputPeerChat(self.entity.id)
        return InputPeerUser(self.entity.id, self.entity.access_hash)

    async def get_entity(self, peer):
        return self.entity

    async def __call__(self, request):
        self.calls.append(request)
        if isinstance(request, (GetFullUserRequest, GetFullChannelRequest, GetFullChatRequest)):
            from telethon.tl import types
            if isinstance(request, GetFullUserRequest):
                full = types.UserFull(id=self.entity.id, settings=types.PeerSettings(), notify_settings=types.PeerNotifySettings(), common_chats_count=0, about='Source <&>\n``` unsafe fence')
                return types.users.UserFull(full_user=full, chats=[], users=[self.entity])
            if isinstance(request, GetFullChannelRequest):
                full = types.ChannelFull(id=self.entity.id, about='', read_inbox_max_id=0, read_outbox_max_id=0, unread_count=0, chat_photo=types.PhotoEmpty(id=1), notify_settings=types.PeerNotifySettings(), bot_info=[], pts=0)
                return types.messages.ChatFull(full_chat=full, chats=[self.entity], users=[])
            full = types.ChatFull(id=self.entity.id, about='', participants=types.ChatParticipants(chat_id=self.entity.id, participants=[], version=1), notify_settings=types.PeerNotifySettings())
            return types.messages.ChatFull(full_chat=full, chats=[self.entity], users=[])
        if isinstance(request, GetHistoryRequest):
            self.history_offsets.append(request.offset_id)
            if self.fail_history:
                raise errors.BotMethodInvalidError(request)
            messages = [Message(id=5, peer_id=PeerUser(42), message='First <&>'), Message(id=4, peer_id=PeerUser(42), message='Second')] if request.offset_id == 0 else []
            return SimpleNamespace(messages=messages, count=2)
        if isinstance(request, GetUserPhotosRequest):
            return SimpleNamespace(photos=[], count=0)
        if isinstance(request, GetParticipantsRequest):
            participants = [ChannelParticipant(user_id=1, date=None), ChannelParticipant(user_id=2, date=None)] if request.offset == 0 else []
            return SimpleNamespace(participants=participants, count=2)
        from telethon.tl import types
        from telethon.tl.functions import users, payments, premium, channels
        if isinstance(request, users.GetSavedMusicRequest):
            return types.users.SavedMusic(count=0, documents=[])
        if isinstance(request, payments.GetSavedStarGiftsRequest):
            return types.payments.SavedStarGifts(count=0, gifts=[], chats=[], users=[])
        if isinstance(request, payments.GetStarGiftsRequest):
            return types.payments.StarGifts(hash=0, gifts=[], chats=[], users=[])
        if isinstance(request, premium.GetBoostsStatusRequest):
            return types.premium.BoostsStatus(level=0, current_level_boosts=0, boosts=0, boost_url='https://t.me/boost/fixture')
        if isinstance(request, premium.GetBoostsListRequest):
            return types.premium.BoostsList(count=0, boosts=[], users=[])
        if isinstance(request, channels.GetParticipantRequest):
            return types.channels.ChannelParticipant(participant=types.ChannelParticipantSelf(user_id=777, inviter_id=42, date=None), chats=[], users=[])
        raise AssertionError(type(request))

    async def get_messages(self, peer, ids):
        return [Message(id=i, peer_id=PeerUser(42), message='by id') if i != 999 else None for i in ids]

    async def download_profile_photo(self, peer, file):
        return None

    async def disconnect(self):
        self.disconnected = True


