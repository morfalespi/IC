"""Contrato da ficha curta, sem acesso real a Telegram nem impressão de tokens."""
import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
import unittest

from bot_api import BotAPIRequestError
from ficha_resumo import montar_ficha, entregar_ficha
from resolver import Acquisition


def registro(kind='user', with_photo=True):
    if kind == 'user':
        entity = SimpleNamespace(
            first_name='Alice <Exemplo>', last_name='', username='alice_demo',
            usernames=[
                SimpleNamespace(username='alice_extra', active=True),
                SimpleNamespace(username='alice_old', active=False),
            ],
        )
        full = SimpleNamespace(full_user=SimpleNamespace(about='Biografia <teste>', personal_channel_id=45678))
    else:
        entity = SimpleNamespace(title='Meu <Canal>' if kind == 'channel' else 'Meu Grupo',
                                 username='canal_demo' if kind == 'channel' else None, usernames=[])
        full = SimpleNamespace(full_chat=SimpleNamespace(about='Descrição <oficial>'))
    data = Acquisition(123456789 if kind == 'user' else -1000000000010, kind, entity)
    data.full = full
    if with_photo:
        data.metadata['chat_bot_api'] = {'photo': {'big_file_id': 'telegram_file_id_fixture'}}
    return data


class FakeResult:
    def require(self):
        return {'message_id': 77, 'chat': {'id': 42}}


class FakeBot:
    def __init__(self, *, reject_rich=False, reject_photo=False, uncertain=False, rejected_code=400):
        self.calls = []
        self.reject_rich = reject_rich
        self.reject_photo = reject_photo
        self.uncertain = uncertain
        self.rejected_code = rejected_code

    def call(self, name, payload):
        self.calls.append((name, payload))
        if self.uncertain:
            raise OSError('submissão incerta')
        rich = payload.get('rich_message')
        if rich and (self.reject_rich or (self.reject_photo and rich.get('media'))):
            raise BotAPIRequestError(name, {'ok': False, 'error_code': self.rejected_code,
                                            'description': 'formato rejeitado'})
        return FakeResult()


class FichaResumoTests(unittest.TestCase):
    def test_user_profile_and_photo_use_only_observed_fields(self):
        ficha = montar_ficha(registro(), momento=datetime(2026, 11, 10, 12, 30, tzinfo=timezone.utc))
        self.assertIn('Alice &lt;Exemplo&gt;', ficha['html'])
        self.assertIn('@alice_demo', ficha['html'])
        self.assertIn('@alice_extra', ficha['html'])
        self.assertNotIn('@alice_old', ficha['html'])
        self.assertIn('123456789', ficha['html'])
        self.assertIn('Biografia &lt;teste&gt;', ficha['html'])
        self.assertIn('Canal pessoal vinculado (ID)', ficha['html'])
        self.assertIn('10/11/2026 12:30 UTC', ficha['html'])
        self.assertIn('tg://photo?id=perfil', ficha['html'])
        self.assertEqual(ficha['media'][0]['media']['media'], 'telegram_file_id_fixture')
        self.assertNotIn('tg://photo', ficha['html_sem_foto'])
        self.assertNotIn('alice_old', ficha['texto'])

    def test_channel_and_group_are_targets_not_delivery_chats(self):
        for kind in ('channel', 'basic_group'):
            ficha = montar_ficha(registro(kind, with_photo=False))
            self.assertIn('ID', ficha['html'])
            self.assertIsNone(ficha['media'])
            self.assertIn('não foram enumerados', ficha['texto'])
            self.assertIn('Canal' if kind == 'channel' else 'Grupo', ficha['html'])

    def test_photo_explicitly_rejected_keeps_rich_in_same_message(self):
        bot = FakeBot(reject_photo=True)
        result = asyncio.run(entregar_ficha(bot, '42', registro(), '77'))
        self.assertEqual(result['message_id'], 77)
        self.assertEqual([name for name, _ in bot.calls], ['editMessageText', 'editMessageText'])
        self.assertIn('media', bot.calls[0][1]['rich_message'])
        self.assertNotIn('media', bot.calls[1][1]['rich_message'])
        self.assertTrue(all(c['message_id'] == 77 for _, c in bot.calls))

    def test_explicit_rich_rejections_fallback_to_plain_edit(self):
        bot = FakeBot(reject_rich=True)
        asyncio.run(entregar_ficha(bot, '42', registro(), '77'))
        self.assertEqual([name for name, _ in bot.calls],
                         ['editMessageText', 'editMessageText', 'editMessageText'])
        self.assertIn('text', bot.calls[-1][1])
        self.assertTrue(all(c['message_id'] == 77 for _, c in bot.calls))

    def test_no_retry_when_submission_uncertain(self):
        bot = FakeBot(uncertain=True)
        with self.assertRaises(OSError):
            asyncio.run(entregar_ficha(bot, '42', registro(), '77'))
        self.assertEqual(len(bot.calls), 1)

    def test_no_retry_when_forbidden(self):
        bot = FakeBot(reject_rich=True, rejected_code=403)
        with self.assertRaises(BotAPIRequestError):
            asyncio.run(entregar_ficha(bot, '42', registro(), '77'))
        self.assertEqual(len(bot.calls), 1)


if __name__ == '__main__':
    unittest.main()
