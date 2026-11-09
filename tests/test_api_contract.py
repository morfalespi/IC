"""Negative tests whose required fields come from official tables, not IC code.

This is a limited contract check authored by the same agent. It does not claim
independent review, full-schema validation, or live Telegram execution.
"""
import copy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from bot_api import BotResult, APIProtocolError

GIFTS = {key: False for key in ('unlimited_gifts', 'limited_gifts', 'unique_gifts', 'premium_subscription', 'gifts_from_channels')}
CONTRACT = json.loads((Path(__file__).parent / 'contracts/bot-api-required.json').read_text())
RESULTS = {
    'user': {'id': 42, 'is_bot': True, 'first_name': 'Example'},
    'chat': {'id': 42, 'type': 'private', 'accent_color_id': 1, 'max_reaction_count': 1, 'accepted_gift_types': GIFTS},
    'chatfullinfo': {'id': 42, 'type': 'private', 'accent_color_id': 1, 'max_reaction_count': 1, 'accepted_gift_types': GIFTS},
    'message': {'message_id': 3, 'date': 1700000000, 'chat': {'id': 42, 'type': 'private'}},
    'acceptedgifttypes': GIFTS,
    'file': {'file_id': 'example', 'file_unique_id': 'unique'},
}
METHODS = {'user': ['getMe'], 'chat': ['getChat'], 'chatfullinfo': ['getChat'], 'message': ['sendMessage','sendPhoto','sendDocument','editMessageText'], 'file': ['getFile'], 'acceptedgifttypes': ['getChat']}

class OfficialResultContract(unittest.TestCase):
    def test_required_fields_from_official_tables_cannot_be_omitted(self):
        for kind, fields in CONTRACT['types'].items():
            for field in fields:
                for method in METHODS[kind]:
                    with self.subTest(method=method, missing=field, source=CONTRACT['source']):
                        result = copy.deepcopy(RESULTS[kind]); del result[field]
                        if kind == 'acceptedgifttypes':
                            result = {**RESULTS['chatfullinfo'], 'accepted_gift_types': result}
                        with self.assertRaises(APIProtocolError):
                            BotResult.decode(method, {'ok': True, 'result': result})

    def test_required_field_types_from_official_tables_cannot_be_changed(self):
        wrong = {'Integer': 'not-an-integer', 'Boolean': 'true', 'String': 123, 'Chat': [], 'AcceptedGiftTypes': []}
        for kind, fields in CONTRACT['types'].items():
            for field, expected in fields.items():
                for method in METHODS[kind]:
                    with self.subTest(method=method, field=field, required_type=expected):
                        result = copy.deepcopy(RESULTS[kind]); result[field] = wrong[expected]
                        if kind == 'acceptedgifttypes':
                            result = {**RESULTS['chatfullinfo'], 'accepted_gift_types': result}
                        with self.assertRaises(APIProtocolError):
                            BotResult.decode(method, {'ok': True, 'result': result})

    def test_optional_file_path_is_not_required_for_getfile_metadata(self):
        result = BotResult.decode('getFile', {'ok': True, 'result': RESULTS['file']})
        self.assertEqual(result.result, RESULTS['file'])

if __name__ == '__main__': unittest.main()
