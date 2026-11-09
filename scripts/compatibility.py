import ast
import importlib
import inspect
from pathlib import Path
import telethon
from telethon.tl.alltlobjects import LAYER
from telethon import TelegramClient


def main():
    imports = calls = 0
    for path in [Path('scripts/resolver.py'), Path('scripts/metadata.py')]:
        source = ast.parse(path.read_text())
        imported = {}
        for node in ast.walk(source):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith('telethon'):
                module = importlib.import_module(node.module)
                for alias in node.names:
                    imported[alias.asname or alias.name] = getattr(module, alias.name)
        imports += len(imported)
        for node in ast.walk(source):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in imported:
                if any(isinstance(arg, ast.Starred) for arg in node.args) or any(k.arg is None for k in node.keywords):
                    raise ValueError(f'Dynamic signature requires review: {path}:{node.lineno}')
                inspect.signature(imported[node.func.id]).bind(*([None] * len(node.args)), **{k.arg: None for k in node.keywords})
                calls += 1
    for name, kwargs in [
        ('get_input_entity', {'peer': None}), ('get_entity', {'entity': None}),
        ('get_messages', {'entity': None, 'ids': [1]}),
        ('download_media', {'message': None, 'file': 'output', 'progress_callback': None}),
        ('download_profile_photo', {'entity': None, 'file': bytes}), ('sign_in', {'bot_token': 'placeholder'}),
    ]:
        inspect.signature(getattr(TelegramClient, name)).bind(None, **kwargs)
    importlib.import_module('resolver')
    importlib.import_module('ic')
    print(f'Telethon {telethon.__version__}, layer {LAYER}: {imports} imports, {calls} constructors and 6 client signatures compatible')


if __name__ == '__main__':
    main()
