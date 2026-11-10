"""Execute real Node WebCrypto -> Python cryptography -> IC workflow locally."""
import asyncio
import base64
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from fixtures import FakeMTProto, TelegramFixture
from bot_api import BotClient, diagnostico_excecao
from workflow import decrypt_request, main

class WorkflowPrivacy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.private = private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
        numbers = private.public_key().public_numbers()
        def encode(n):
            return base64.urlsafe_b64encode(n.to_bytes((n.bit_length() + 7) // 8, 'big')).rstrip(b'=').decode()
        cls.public = {'kty': 'RSA', 'n': encode(numbers.n), 'e': encode(numbers.e)}

    def setUp(self):
        self.request = {'alvo': 'private_source_account', 'expected_id': '42', 'chat': '86753091234', 'message_id': '', 'modo': 'completo', 'origem_id': ''}
        result = subprocess.run(['node', '--experimental-vm-modules', 'tests/encrypt_payload.cjs'], input=json.dumps({'key': self.public, 'request': self.request}), text=True, capture_output=True, check=True)
        self.payload = result.stdout

    def test_javascript_to_python_encryption_preserves_request_without_cleartext(self):
        for value in (self.request['alvo'], self.request['chat']):
            self.assertNotIn(value, self.payload)
        request = decrypt_request(self.payload, self.private)
        self.assertEqual({k: request[k] for k in self.request}, self.request)

    def test_modified_ciphertext_is_rejected(self):
        envelope = json.loads(self.payload)
        first = envelope['data'][0]
        envelope['data'] = ('A' if first != 'A' else 'B') + envelope['data'][1:]
        with self.assertRaises(InvalidTag):
            decrypt_request(json.dumps(envelope), self.private)

    def test_expired_encrypted_request_is_rejected(self):
        request = decrypt_request(self.payload, self.private)
        with self.assertRaises(ValueError):
            decrypt_request(self.payload, self.private, now=request['issued_at'] + 21601)

    def test_plaintext_inputs_and_replays_do_not_execute_or_echo_values(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'event.json'
            for inputs, attempt in [({'alvo': self.request['alvo'], 'chat': self.request['chat']}, '1'), ({'payload': self.payload}, '2')]:
                path.write_text(json.dumps({'inputs': inputs}))
                output = io.StringIO()
                with patch.dict(os.environ, {'GITHUB_EVENT_PATH': str(path), 'IC_DISPATCH_PRIVATE_KEY': self.private, 'GITHUB_RUN_ATTEMPT': attempt}), patch('resolver.principal') as run, contextlib.redirect_stdout(output):
                    self.assertEqual(asyncio.run(main()), 1)
                    run.assert_not_called()
                self.assertNotIn(self.request['alvo'], output.getvalue())
                self.assertNotIn(self.request['chat'], output.getvalue())
                self.assertNotIn(self.private, output.getvalue())

    def test_normal_workflow_decrypts_and_runs_without_personal_output(self):
        fixture = TelegramFixture()
        try:
            bot = BotClient(token='local-fixture', opener=fixture.open, sleeper=lambda _: None)
            client = FakeMTProto()
            client.entity.username = self.request['alvo']
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / 'event.json'
                path.write_text(json.dumps({'inputs': {'payload': self.payload}}))
                env = {'GITHUB_EVENT_PATH': str(path), 'IC_DISPATCH_PRIVATE_KEY': self.private, 'GITHUB_RUN_ATTEMPT': '1', 'IC_OUTPUT_DIR': str(Path(folder) / 'exports'), 'IC_STATE_DIR': str(Path(folder) / 'state'), 'RUNNER_TEMP': folder}
                output = io.StringIO()
                with patch.dict(os.environ, env, clear=True), patch('resolver.BotClient', return_value=bot), patch('resolver.open_client', return_value=client), contextlib.redirect_stdout(output):
                    self.assertEqual(asyncio.run(main()), 0, output.getvalue())
                for value in (self.request['alvo'], self.request['chat'], 'Alice', '5551234', self.private):
                    self.assertNotIn(value, output.getvalue())
                self.assertTrue(list((Path(folder) / 'exports').glob('*/report_1.jsonl')))
                methods = {method for method, _ in fixture.requests}
                self.assertIn('sendDocument', methods)
                self.assertIn('getUserGifts', methods)
                self.assertIn('getUserPersonalChatMessages', methods)
                self.assertIn('getAvailableGifts', methods)
        finally:
            fixture.close()

    def test_runtime_diagnostics_do_not_echo_arbitrary_personal_strings(self):
        text = 'private_source_account 86753091234 raw secret payload'
        self.assertNotIn(text, json.dumps(diagnostico_excecao(ValueError(text))))

if __name__ == '__main__': unittest.main()
