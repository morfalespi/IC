"""Persistent, explicitly labeled local integration evidence. No Telegram connection."""
import asyncio
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch
import uuid

from fixtures import TelegramFixture, FakeMTProto
import bot_api
from bot_api import BotClient
import ic
import validar_entrega


async def main():
    root = Path(__file__).resolve().parents[1] / '.ic' / 'controlled' / uuid.uuid4().hex
    root.mkdir(parents=True, mode=0o700)
    fixture = TelegramFixture()
    client = FakeMTProto()
    values = {'BOT_TOKEN': 'local-fixture-only', 'ALLOWED_USER_IDS': '42', 'ALLOWED_CHAT_IDS': '42', 'CHAT_ID': '42', 'IC_STATE_DIR': str(root / 'state'), 'IC_OUTPUT_DIR': str(root / 'exports'), 'RUNNER_TEMP': str(root)}
    fixture.updates = [{'update_id': 1, 'message': {'from': {'id': 42}, 'chat': {'id': 42}, 'text': '/export alice 42'}}]
    output = io.StringIO()
    try:
        with patch.dict(os.environ, values, clear=True):
            bot = BotClient(opener=fixture.open, sleeper=lambda _: None)
            with patch('ic.BotClient', return_value=bot), patch('resolver.open_client', return_value=client), patch.object(sys, 'argv', ['ic.py', 'bot', '--once']), redirect_stdout(output):
                startup = await ic.main()
            bot_api.OPERATION_ID = 'controlled-validation-' + root.name
            with patch('validar_entrega.BotClient', return_value=bot), redirect_stdout(output):
                delivery = await validar_entrega.principal()
        (root / 'execution.jsonl').write_text(output.getvalue())
        result = {'mode': 'controlled_local_fixture', 'external_telegram_contacted': False, 'normal_bot_entrypoint_exit': startup, 'delivery_validation_exit': delivery, 'http_methods_exercised': sorted({method for method, _ in fixture.requests}), 'mtproto': 'Installed Telethon types with controlled responses', 'exports': [str(p.relative_to(root)) for p in root.glob('exports/*/report*')], 'run_directory': str(root)}
        (root / 'result.json').write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        return startup or delivery
    finally:
        fixture.close()


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
