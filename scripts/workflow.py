"""Decrypt private dispatch inputs in memory; never echo request values."""
import asyncio
import base64
import json
import os
from pathlib import Path
import sys
import time

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from bot_api import diagnostico_excecao


def decode(value):
    if not isinstance(value, str) or len(value) > 100000:
        raise ValueError('Invalid encrypted field')
    return base64.b64decode(value + '=' * (-len(value) % 4), altchars=b'-_', validate=True)


def decrypt_request(payload, private_pem, *, now=None):
    if not isinstance(payload, str) or len(payload) > 100000:
        raise ValueError('Invalid encrypted payload')
    envelope = json.loads(payload)
    if not isinstance(envelope, dict) or envelope.get('v') != 1 or set(envelope) != {'v', 'key', 'iv', 'data'}:
        raise ValueError('Unsupported encrypted envelope')
    private = serialization.load_pem_private_key(private_pem.encode(), password=None)
    if not isinstance(private, rsa.RSAPrivateKey) or private.key_size < 2048:
        raise ValueError('Invalid dispatch key')
    key = private.decrypt(decode(envelope['key']), padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    iv = decode(envelope['iv'])
    if len(key) != 32 or len(iv) != 12:
        raise ValueError('Invalid encryption parameters')
    request = json.loads(AESGCM(key).decrypt(iv, decode(envelope['data']), b'IC-dispatch-v1'))
    allowed = {'alvo', 'expected_id', 'chat', 'message_id', 'modo', 'origem_id', 'issued_at'}
    if not isinstance(request, dict) or set(request) != allowed:
        raise ValueError('Invalid request fields')
    timestamp = request['issued_at']
    current = time.time() if now is None else now
    if type(timestamp) is not int or not current - 21600 <= timestamp <= current + 60:
        raise ValueError('Expired dispatch')
    if any(not isinstance(request[k], str) or len(request[k]) > 128 for k in allowed - {'issued_at'}):
        raise ValueError('Invalid request values')
    if request['modo'] not in {'resumo', 'completo', 'validar_entrega'}:
        raise ValueError('Invalid operation')
    from resolver import target
    if request['modo'] != 'validar_entrega':
        target(request['alvo'])
    return request


async def main():
    try:
        if int(os.environ.get('GITHUB_RUN_ATTEMPT', '1')) > 1:
            raise PermissionError('Workflow replay is blocked to prevent duplicate delivery')
        event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
        inputs = event.get('inputs') or {}
        if set(inputs) - {'payload', 'healthcheck'}:
            raise ValueError('Plaintext workflow inputs are forbidden')
        request = decrypt_request(inputs.get('payload'), os.environ.get('IC_DISPATCH_PRIVATE_KEY', ''))
        mappings = {'alvo': 'ALVO', 'expected_id': 'EXPECTED_ID', 'chat': 'CHAT_ID', 'message_id': 'MESSAGE_ID', 'modo': 'MODO', 'origem_id': 'ORIGEM_ID'}
        os.environ.update({destination: request[source] for source, destination in mappings.items()})
        # GitHub reruns are blocked above: runner-local receipts do not survive jobs.
        if request['modo'] == 'validar_entrega':
            from validar_entrega import principal
        else:
            from resolver import principal
        result = await principal()
        if result == 1 and os.environ.get('CHAT_ID'):
            from notificar_falha import principal as notify_failure
            await asyncio.to_thread(notify_failure)
        return result
    except Exception as error:
        print(json.dumps({'state': 'failed', **diagnostico_excecao(error)}))
        return 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
