"""Telegram HTTPS transport, validated envelopes and conservative send semantics."""
from dataclasses import dataclass
from email.parser import BytesParser
from email.policy import default
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import time
import urllib.error
import urllib.request
import uuid
from typing import Any, TypedDict, NotRequired

class TelegramUser(TypedDict):
    id: int
    is_bot: bool
    first_name: str
    username: NotRequired[str]


class TelegramChat(TypedDict):
    id: int
    type: str
    title: NotRequired[str]


class TelegramMessage(TypedDict):
    message_id: int
    chat: TelegramChat
    date: NotRequired[int]
    photo: NotRequired[list[dict]]
    document: NotRequired[dict]


class TelegramFile(TypedDict):
    file_id: str
    file_unique_id: str
    file_size: NotRequired[int]
    file_path: NotRequired[str]


OPERATION_ID = os.environ.get('IC_OPERATION_ID') or os.environ.get('GITHUB_RUN_ID') or uuid.uuid4().hex
SECRET_KEYS = re.compile(r'token|api_hash|access_hash|auth_key|phone|session|file_reference|file_id|file_unique_id', re.I)


def redact(value):
    if isinstance(value, dict):
        return {str(k): '[REDACTED]' if SECRET_KEYS.search(str(k)) else redact(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v) for v in value]
    if isinstance(value, str):
        for key in ('BOT_TOKEN', 'API_HASH', 'GH_DISPATCH_TOKEN', 'TELETHON_STRING_SESSION'):
            secret = os.environ.get(key)
            if secret:
                value = value.replace(secret, '[REDACTED]')
        return re.sub(r'\b\d{5,}:[A-Za-z0-9_-]{15,}', '[REDACTED]', value)
    return value


class APIError(RuntimeError):
    def __init__(self, metodo, resposta):
        self.diagnostic = diagnostico_api(resposta, metodo)
        super().__init__(json.dumps(self.diagnostic, ensure_ascii=False))


class BotAPIRequestError(APIError):
    pass


class BotAPIAuthenticationError(BotAPIRequestError):
    pass


class APIProtocolError(BotAPIRequestError):
    pass


@dataclass(frozen=True)
class BotResult:
    method: str
    ok: bool
    result: Any = None
    error_code: int | None = None
    description: str | None = None
    parameters: dict | None = None

    @classmethod
    def decode(cls, method, raw):
        if not isinstance(raw, dict) or type(raw.get('ok')) is not bool:
            raise APIProtocolError(method, {'ok': False, 'description': 'Invalid Bot API envelope'})
        if raw['ok']:
            if 'result' not in raw:
                raise APIProtocolError(method, {'ok': False, 'description': 'Missing result'})
            result = raw['result']
            if method in {'getMe', 'getChat', 'getFile', 'sendMessage', 'sendPhoto', 'sendDocument', 'sendRichMessage'}:
                if not isinstance(result, dict):
                    raise APIProtocolError(method, {'ok': False, 'description': 'Expected an object result'})
            if method == 'getMe' and (type(result.get('id')) is not int or result.get('is_bot') is not True):
                raise APIProtocolError(method, {'ok': False, 'description': 'Invalid bot identity'})
            if method == 'getChat' and (type(result.get('id')) is not int or result.get('type') not in {'private', 'group', 'supergroup', 'channel'}):
                raise APIProtocolError(method, {'ok': False, 'description': 'Invalid ChatFullInfo'})
            if method == 'getFile' and not isinstance(result.get('file_id'), str):
                raise APIProtocolError(method, {'ok': False, 'description': 'Invalid File'})
            if method.startswith('send') and estado_mensagem(raw) != 'api_accepted':
                raise APIProtocolError(method, {'ok': False, 'description': 'Invalid returned Message'})
            return cls(method, True, result)
        if type(raw.get('error_code')) is not int or not isinstance(raw.get('description'), str):
            raise APIProtocolError(method, {'ok': False, 'description': 'Invalid error response'})
        parameters = raw.get('parameters', {})
        if not isinstance(parameters, dict) or ('retry_after' in parameters and (type(parameters['retry_after']) is not int or parameters['retry_after'] < 0)) or ('migrate_to_chat_id' in parameters and type(parameters['migrate_to_chat_id']) is not int):
            raise APIProtocolError(method, {'ok': False, 'description': 'Invalid ResponseParameters'})
        return cls(method, False, error_code=raw['error_code'], description=raw['description'], parameters=parameters)

    def envelope(self):
        if self.ok:
            return {'ok': True, 'result': self.result}
        return {'ok': False, 'error_code': self.error_code, 'description': self.description, 'parameters': self.parameters or {}}

    def require(self):
        if not self.ok:
            error = BotAPIAuthenticationError if self.error_code == 401 else BotAPIRequestError
            raise error(self.method, self.envelope())
        return self.result


def diagnostico_api(resposta, metodo):
    # A response may contain profiles, messages and credentials. Log status only.
    return redact({'method': metodo, **{k: resposta[k] for k in ('ok', 'error_code', 'description', 'parameters', 'origin') if k in resposta}})


def diagnostico_excecao(erro):
    if isinstance(erro, APIError):
        return erro.diagnostic
    return {'origin': 'runtime', 'type': type(erro).__name__, 'description': redact(str(erro))}


def estado_mensagem(resposta, chat_id=None):
    result = resposta.get('result')
    if resposta.get('ok') is not True or not isinstance(result, dict):
        return 'rejected'
    chat = result.get('chat') or {}
    if type(result.get('message_id')) is not int or type(chat.get('id')) is not int:
        return 'invalid_response'
    if chat_id is not None and str(chat['id']) != str(chat_id):
        return 'destination_mismatch'
    return 'api_accepted'


def authorized_destination(chat_id):
    if not re.fullmatch(r'-?[1-9]\d*', str(chat_id)):
        raise PermissionError('Delivery requires a canonical numeric chat ID')
    allowed = {v.strip() for v in os.environ.get('ALLOWED_CHAT_IDS', '').split(',') if v.strip()}
    explicit = os.environ.get('CHAT_ID', '').strip()
    if explicit:
        allowed.add(explicit)
    if str(chat_id) not in allowed:
        raise PermissionError('Destination is not explicitly authorized')
    return int(chat_id)


def _fields(body, headers):
    content_type = headers.get('Content-Type', 'application/json')
    if content_type.startswith('application/json'):
        return json.loads(body or b'{}')
    message = BytesParser(policy=default).parsebytes(b'Content-Type: ' + content_type.encode() + b'\r\nMIME-Version: 1.0\r\n\r\n' + body)
    result = {}
    for part in message.iter_parts():
        name = part.get_param('name', header='content-disposition')
        payload = part.get_payload(decode=True)
        result[name] = {'filename': part.get_filename(), 'sha256': hashlib.sha256(payload).hexdigest()} if part.get_filename() else payload.decode()
    return result


class DeliveryJournal:
    def __init__(self):
        path = Path(os.environ.get('IC_STATE_DIR', '.ic'))
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.db = sqlite3.connect(path / 'delivery.sqlite', timeout=30)
        os.chmod(path / 'delivery.sqlite', 0o600)
        self.db.execute('CREATE TABLE IF NOT EXISTS deliveries (key TEXT PRIMARY KEY, state TEXT, response TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS delivery_events (key TEXT, state TEXT, at REAL)')
        self.db.commit()

    def transition(self, key, state):
        with self.db:
            self.db.execute('UPDATE deliveries SET state=? WHERE key=?', (state, key))
            self.db.execute('INSERT INTO delivery_events VALUES (?, ?, ?)', (key, state, time.time()))

    def prepare(self, key):
        with self.db:
            row = self.db.execute('SELECT state,response FROM deliveries WHERE key=?', (key,)).fetchone()
            if row:
                if row[0] in {'api_accepted', 'api_rejected'}:
                    return json.loads(row[1])
                raise BotAPIRequestError('delivery', {'ok': False, 'error_code': 0, 'description': 'Previous submission is uncertain; reconcile before replay'})
            self.db.execute('INSERT INTO deliveries VALUES (?, ?, NULL)', (key, 'prepared'))
            self.db.execute('INSERT INTO delivery_events VALUES (?, ?, ?)', (key, 'prepared', time.time()))
        return None

    def finish(self, key, response, accepted):
        # Keep only receipt fields; never persist report content in the journal.
        result = response.get('result') or {}
        receipt = {'ok': True, 'result': {k: result[k] for k in ('message_id', 'date', 'chat', 'document', 'photo') if k in result}} if accepted else response
        with self.db:
            self.db.execute('UPDATE deliveries SET state=?,response=? WHERE key=?', ('api_accepted' if accepted else 'api_rejected', json.dumps(receipt), key))
            self.db.execute('INSERT INTO delivery_events VALUES (?, ?, ?)', (key, 'api_accepted' if accepted else 'api_rejected', time.time()))


class BotClient:
    def __init__(self, token=None, *, opener=None, sleeper=time.sleep):
        self.token = token if token is not None else os.environ.get('BOT_TOKEN', '')
        if not self.token:
            raise ValueError('BOT_TOKEN is required')
        self.opener = opener or urllib.request.urlopen
        self.sleep = sleeper

    def call(self, method: str, payload=None, *, body=None, headers=None) -> BotResult:
        headers = headers or {'Content-Type': 'application/json'}
        body = body if body is not None else json.dumps(payload or {}, ensure_ascii=False).encode()
        fields = _fields(body, headers)
        sending = method.startswith('send') or method.startswith('editMessage')
        journal = None
        key = None
        if sending:
            authorized_destination(fields.get('chat_id'))
            key = hashlib.sha256(json.dumps([hashlib.sha256(self.token.encode()).hexdigest(), OPERATION_ID, method, fields], sort_keys=True).encode()).hexdigest()
            journal = DeliveryJournal()
            try:
                previous = journal.prepare(key)
            except BaseException:
                journal.db.close()
                raise
            if previous:
                journal.db.close()
                return BotResult.decode(method, previous)
        try:
            if journal:
                journal.transition(key, 'submitting')
            for attempt in range(3):
                request = urllib.request.Request(f'https://api.telegram.org/bot{self.token}/{method}', data=body, headers=headers)
                try:
                    try:
                        with self.opener(request, timeout=45) as response:
                            raw = response.read()
                            status = response.status
                    except urllib.error.HTTPError as error:
                        status, raw = error.code, error.read()
                    try:
                        result = BotResult.decode(method, json.loads(raw))
                    except (ValueError, UnicodeError) as error:
                        raise APIProtocolError(method, {'ok': False, 'description': 'Non-JSON Bot API response'}) from error
                    if result.ok and not 200 <= status < 300:
                        raise APIProtocolError(method, {'ok': False, 'description': 'HTTP status conflicts with success envelope'})
                    if not result.ok and result.error_code == 429:
                        delay = (result.parameters or {}).get('retry_after')
                        if type(delay) is int and 0 <= delay <= 30 and attempt < 2:
                            self.sleep(delay)
                            continue
                    if not result.ok and not sending and result.error_code >= 500 and attempt < 2:
                        self.sleep(2 ** attempt)
                        continue
                    if sending and result.ok and estado_mensagem(result.envelope(), fields['chat_id']) != 'api_accepted':
                        raise APIProtocolError(method, {'ok': False, 'description': 'Returned destination differs from authorized destination'})
                    if method.startswith('editMessage') and result.ok and result.result.get('message_id') != int(fields.get('message_id', 0)):
                        raise APIProtocolError(method, {'ok': False, 'description': 'Edited message ID differs from requested message'})
                    if journal:
                        journal.finish(key, result.envelope(), result.ok)
                    return result
                except (urllib.error.URLError, OSError) as error:
                    if sending or attempt == 2:
                        raise BotAPIRequestError(method, {'ok': False, 'error_code': 0, 'origin': 'transport', 'description': 'Transport failed; submission unknown' if sending else 'Transport failed'}) from error
                    self.sleep(2 ** attempt)
            raise AssertionError('Unreachable retry state')
        except BaseException:
            if journal:
                journal.transition(key, 'submission_unknown')
            raise
        finally:
            if journal:
                journal.db.close()

    def get_me(self) -> TelegramUser:
        return self.call('getMe').require()

    def get_chat(self, chat_id) -> TelegramChat:
        return self.call('getChat', {'chat_id': chat_id}).require()

    def send_message(self, chat_id, text: str, **extra) -> TelegramMessage:
        return self.call('sendMessage', {'chat_id': chat_id, 'text': text, **extra}).require()

    def upload(self, method, chat_id, data: bytes, filename: str, content_type: str, **extra) -> TelegramMessage:
        if method not in {'sendPhoto', 'sendDocument'}:
            raise ValueError('Unsupported upload method')
        field = 'photo' if method == 'sendPhoto' else 'document'
        filename = Path(filename).name
        if any(c in filename for c in '\r\n"'):
            raise ValueError('Invalid upload filename')
        boundary = uuid.uuid4().hex
        parts = []
        for name, value in {'chat_id': str(chat_id), **extra}.items():
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
        parts.extend([f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"; filename="{filename}"\r\nContent-Type: {content_type}\r\n\r\n'.encode(), data, f'\r\n--{boundary}--\r\n'.encode()])
        return self.call(method, body=b''.join(parts), headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}).require()

    def send_photo(self, chat_id, data: bytes, filename='photo.jpg', content_type='image/jpeg') -> TelegramMessage:
        return self.upload('sendPhoto', chat_id, data, filename, content_type)

    def send_document(self, chat_id, data: bytes, filename: str, **extra) -> TelegramMessage:
        return self.upload('sendDocument', chat_id, data, filename, 'application/octet-stream', **extra)

    def get_file(self, file_id: str) -> TelegramFile:
        return self.call('getFile', {'file_id': file_id}).require()

    def download(self, file_id: str, max_bytes=20 * 1024 * 1024) -> tuple[bytes, str]:
        info = self.get_file(file_id)
        path = info.get('file_path', '')
        if not isinstance(path, str) or not re.fullmatch(r'[A-Za-z0-9_./-]+', path) or not path or any(p in {'..', ''} for p in path.split('/')) or path.startswith('/') or '?' in path or '#' in path or '\\' in path:
            raise APIProtocolError('getFile', {'ok': False, 'description': 'Missing or unsafe file_path'})
        with self.opener(f'https://api.telegram.org/file/bot{self.token}/{path}', timeout=45) as response:
            data = response.read(max_bytes + 1)
        if len(data) > max_bytes or (info.get('file_size') is not None and len(data) != info['file_size']):
            raise APIProtocolError('getFile', {'ok': False, 'description': 'File size verification failed'})
        return data, hashlib.sha256(data).hexdigest()


def chamar(metodo, corpo, cabecalhos):
    result = BotClient().call(metodo, body=corpo, headers=cabecalhos)
    if metodo.startswith(('send', 'editMessage')) or result.error_code == 401:
        result.require()
    return result.envelope()


def recusar_autenticacao(metodo, resposta):
    BotResult.decode(metodo, resposta).require()
    return resposta


def registrar_notificacao(resposta, chat_id):
    state = estado_mensagem(resposta, chat_id)
    if state != 'api_accepted':
        raise APIProtocolError('delivery', {'ok': False, 'description': state})
    path = Path(os.environ.get('RUNNER_TEMP', '/tmp'))
    (path / 'notificado').touch()
    (path / 'notificacao_pendente').unlink(missing_ok=True)
    return state
