"""Run the normal acquisition/export path without sending report content."""
import asyncio
import os
import sys
from resolver import principal

if __name__ == '__main__':
    os.environ['CHAT_ID'] = ''
    os.environ.setdefault('MODO', 'resumo')
    sys.exit(asyncio.run(principal()))
