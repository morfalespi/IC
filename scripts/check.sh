#!/usr/bin/env bash
set -euo pipefail

while IFS= read -r -d '' arquivo; do
  node --check "$arquivo"
done < <(find tgcloud -type f -name '*.js' -print0 | sort -z)

python -m compileall -q scripts tests

python - <<'PY'
from pathlib import Path
esperado = "export const GH_DISPATCH_TOKEN = '';\nexport const GH_REPOSITORY = '';\nexport const IC_DISPATCH_PUBLIC_KEY = null;\n"
atual = Path('tgcloud/lib/segredos.js').read_text()
auth = Path('tgcloud/lib/autorizacao.js').read_text()
if 'ALLOWED_USER_IDS = []' not in auth or 'ALLOWED_CHAT_IDS = []' not in auth:
    raise SystemExit('Committed Telegram authorization lists must remain empty; deployment injects configuration.')
if atual != esperado:
    raise SystemExit('tgcloud/lib/segredos.js deve permanecer apenas com placeholders vazios no Git.')
PY

echo "checks OK"
