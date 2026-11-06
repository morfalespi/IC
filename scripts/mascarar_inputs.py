import json
import os
from pathlib import Path


def principal():
    evento = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    print(json.dumps(evento.get("inputs") or {}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
