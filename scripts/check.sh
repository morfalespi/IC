#!/usr/bin/env bash
set -euo pipefail

while IFS= read -r -d '' arquivo; do
  node --check "$arquivo"
done < <(find tgcloud scripts -type f \( -name '*.js' -o -name '*.mjs' \) -print0 | sort -z)

python -m compileall -q scripts

python - <<'PY'
from pathlib import Path
esperado = "export const GH_DISPATCH_TOKEN = '';\nexport const GH_REPOSITORY = '';\n"
atual = Path('tgcloud/lib/segredos.js').read_text()
if atual != esperado:
    raise SystemExit('tgcloud/lib/segredos.js deve permanecer apenas com placeholders vazios no Git.')
PY

echo "checks OK"
