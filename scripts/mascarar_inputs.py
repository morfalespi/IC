import json
import os
from pathlib import Path


def principal():
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    # Mask before any other workflow step can echo user inputs.
    for key, value in (event.get('inputs') or {}).items():
        if key in {'alvo', 'expected_id', 'chat', 'message_id', 'origem_id'} and value:
            escaped = str(value).replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
            print('::add-mask::' + escaped)
    print(json.dumps({'state': 'inputs_masked'}))
    evento = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    print(json.dumps(evento.get("inputs") or {}, ensure_ascii=False), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(principal())
