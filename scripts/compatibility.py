import ast
import importlib
import inspect
from pathlib import Path

import telethon
from telethon.tl.alltlobjects import LAYER


def main():
    source = ast.parse(Path("scripts/resolver.py").read_text())
    imported = {}
    for node in ast.walk(source):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("telethon"):
            module = importlib.import_module(node.module)
            for alias in node.names:
                imported[alias.asname or alias.name] = getattr(module, alias.name)
    calls = 0
    for node in ast.walk(source):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in imported:
            if any(isinstance(arg, ast.Starred) for arg in node.args) or any(key.arg is None for key in node.keywords):
                raise ValueError(f"Assinatura dinâmica exige revisão: linha {node.lineno}")
            inspect.signature(imported[node.func.id]).bind(
                *([None] * len(node.args)), **{key.arg: None for key in node.keywords}
            )
            calls += 1
    importlib.import_module("resolver")
    for module in ("bot_api", "telegram_ids", "validar_apis", "notificar_falha", "exportacao", "mascarar_inputs"):
        importlib.import_module(module)
    print(f"Telethon {telethon.__version__}, layer {LAYER}: {len(imported)} imports e {calls} assinaturas compatíveis; resolver importado sem rede.")


if __name__ == "__main__":
    main()
