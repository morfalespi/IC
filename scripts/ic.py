"""Local entry point: single runs, continuous polling and delivery validation."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sqlite3
import sys
import time

import bot_api
from bot_api import BotClient, diagnostico_excecao
import resolver


def emit(**event):
    print(json.dumps(event), flush=True)


def authorized(message):
    users = {v.strip() for v in os.environ.get('ALLOWED_USER_IDS', '').split(',') if v.strip()}
    chats = {v.strip() for v in os.environ.get('ALLOWED_CHAT_IDS', '').split(',') if v.strip()}
    return str((message.get('from') or {}).get('id')) in users and str((message.get('chat') or {}).get('id')) in chats and not (message.get('from') or {}).get('is_bot', False)


def command(message):
    text = message.get('text', '').strip()
    parts = text.split()
    if not parts:
        raise ValueError('Use /info TARGET, /export TARGET, or /start')
    name = parts[0].split('@')[0]
    if name in {'/start', '/help'}:
        return None
    if name not in {'/info', '/export'} or len(parts) not in {2, 3}:
        raise ValueError('Use /info TARGET [EXPECTED_ID] or /export TARGET [EXPECTED_ID]')
    resolver.target(parts[1])
    expected = parts[2] if len(parts) == 3 else ''
    if expected:
        if not isinstance(resolver.target(expected), int):
            raise ValueError('EXPECTED_ID must be numeric')
    return parts[1], expected, 'resumo' if name == '/info' else 'completo'


class UpdateStore:
    def __init__(self):
        root = Path(os.environ.get('IC_STATE_DIR', '.ic'))
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(root / 'updates.sqlite')
        os.chmod(root / 'updates.sqlite', 0o600)
        self.db.executescript('CREATE TABLE IF NOT EXISTS updates (id INTEGER PRIMARY KEY, state TEXT); CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value INTEGER); CREATE TABLE IF NOT EXISTS throttle (chat TEXT PRIMARY KEY, at REAL);')

    def offset(self):
        row = self.db.execute("SELECT value FROM metadata WHERE key='offset'").fetchone()
        return row[0] if row else 0

    def claim(self, update_id):
        with self.db:
            result = self.db.execute('INSERT OR IGNORE INTO updates VALUES (?, ?)', (update_id, 'processing'))
        return result.rowcount == 1

    def reserve_command(self, chat):
        now = time.time()
        with self.db:
            result = self.db.execute('INSERT INTO throttle VALUES (?, ?) ON CONFLICT(chat) DO UPDATE SET at=excluded.at WHERE throttle.at <= ?', (chat, now, now - 30))
        return result.rowcount == 1

    def finish(self, update_id, state):
        with self.db:
            self.db.execute('UPDATE updates SET state=? WHERE id=?', (state, update_id))
            self.db.execute("INSERT INTO metadata VALUES ('offset', ?) ON CONFLICT(key) DO UPDATE SET value=max(value,excluded.value)", (update_id + 1,))


async def polling(bot=None, client=None, *, once=False):
    if not os.environ.get('ALLOWED_USER_IDS') or not os.environ.get('ALLOWED_CHAT_IDS'):
        raise ValueError('Polling requires ALLOWED_USER_IDS and ALLOWED_CHAT_IDS; access is denied by default')
    bot = bot or BotClient()
    me = await asyncio.to_thread(bot.get_me)
    webhook = (await asyncio.to_thread(bot.call, 'getWebhookInfo')).require()
    if webhook.get('url'):
        raise RuntimeError('A webhook is configured; disable it explicitly before starting polling')
    own_client = client is None
    client = client or await resolver.open_client(bot)
    store = UpdateStore()
    emit(state='operational', entrypoint='polling', authenticated=True)
    failures = 0
    operation_failures = 0
    partial_operations = 0
    try:
        while True:
            try:
                result = await asyncio.to_thread(bot.call, 'getUpdates', {'offset': store.offset(), 'limit': 100, 'timeout': 0 if once else 25, 'allowed_updates': ['message']})
                updates = result.require()
                if not isinstance(updates, list):
                    raise RuntimeError('getUpdates result must be an array')
                failures = 0
            except Exception as error:
                failures += 1
                emit(state='poll_failed', **diagnostico_excecao(error))
                if once or failures >= 5:
                    raise
                await asyncio.sleep(min(2 ** failures, 30))
                continue
            for update in updates:
                update_id = update['update_id']
                if not store.claim(update_id):
                    emit(state='replay_suppressed', reason='Update was previously claimed; reconcile interrupted operations manually')
                    store.finish(update_id, 'replay_suppressed')
                    continue
                message = update.get('message') or {}
                if not authorized(message):
                    store.finish(update_id, 'unauthorized')
                    emit(state='update_denied')
                    continue
                bot_api.OPERATION_ID = 'telegram-update-' + str(me['id']) + '-' + str(update_id)
                chat = str(message['chat']['id'])
                previous_env = {k: os.environ.get(k) for k in ('ALVO', 'EXPECTED_ID', 'MODO', 'CHAT_ID')}
                try:
                    try:
                        requested = command(message)
                    except ValueError as error:
                        await asyncio.to_thread(bot.send_message, chat, str(error))
                        operation_failures += 1
                        store.finish(update_id, 'invalid_request')
                        continue
                    if requested is not None and not store.reserve_command(chat):
                        await asyncio.to_thread(bot.send_message, chat, 'Please wait 30 seconds before another collection request.')
                        store.finish(update_id, 'throttled')
                        continue
                    if requested is None:
                        await asyncio.to_thread(bot.send_message, chat, 'IC: /info TARGET [EXPECTED_ID] for metadata; /export TARGET [EXPECTED_ID] for metadata, available messages, participants, photos and media. Exports are sent only to this authorized chat.')
                        code = 0
                    else:
                        value, expected, mode = requested
                        os.environ.update(ALVO=value, EXPECTED_ID=expected, MODO=mode, CHAT_ID=chat)
                        code = await resolver.workflow(bot=bot, client=client)
                    if code == 2:
                        partial_operations += 1
                    elif code:
                        operation_failures += 1
                    store.finish(update_id, 'completed' if code == 0 else 'partial' if code == 2 else 'failed')
                except Exception as error:
                    emit(state='operation_failed', **diagnostico_excecao(error))
                    operation_failures += 1
                    store.finish(update_id, 'failed')
                    try:
                        await asyncio.to_thread(bot.send_message, chat, 'IC não concluiu esta solicitação. Nenhum resultado completo foi confirmado.')
                    except Exception as notification_error:
                        emit(state='failure_notification_failed', **diagnostico_excecao(notification_error))
                finally:
                    for key, value in previous_env.items():
                        if value is None:
                            os.environ.pop(key, None)
                        else:
                            os.environ[key] = value
            if once:
                return 1 if operation_failures else 2 if partial_operations else 0
    finally:
        store.db.close()
        if own_client:
            await client.disconnect()
            client.session.close()


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['run', 'bot', 'validate-delivery', 'check'], nargs='?', default='bot')
    parser.add_argument('--once', action='store_true', help='Fetch one batch of updates')
    args = parser.parse_args()
    if args.operation == 'check':
        required = ['BOT_TOKEN', 'API_ID', 'API_HASH']
        missing = [key for key in required if not os.environ.get(key)]
        emit(state='configuration_missing' if missing else 'configured', missing=missing, credentials_exposed=False)
        return 1 if missing else 0
    try:
        if args.operation == 'run':
            return await resolver.principal()
        if args.operation == 'validate-delivery':
            from validar_entrega import principal
            return await principal()
        return await polling(once=args.once)
    except Exception as error:
        emit(state='failed', **diagnostico_excecao(error))
        return 1


if __name__ == '__main__':
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        emit(state='stopped')
        sys.exit(130)
