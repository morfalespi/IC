# IC

An authorization-aware Telegram bot and local export runner. IC uses the official HTTPS Bot API and Telethon 1.45.0 (MTProto layer 229). Python 3.12+ is supported; Node is needed only for the optional TgCloud host and JavaScript checks.

## Install and run

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r scripts/requirements-lock.txt
npm ci
cp .env.example .env
# Edit .env locally, then load it in your shell:
set -a
. ./.env
set +a
.venv/bin/python scripts/ic.py check
.venv/bin/python scripts/ic.py bot
```

Supply `BOT_TOKEN` from BotFather and your own `API_ID`/`API_HASH` from https://my.telegram.org. Put secrets in environment settings or your local ignored `.env`; do not put them in commands, source, reports or chat. The check command lists missing variable **names**, never values. No credentials are included in the repository.

The bot requires explicit comma-separated `ALLOWED_USER_IDS` and `ALLOWED_CHAT_IDS`. Both the requesting sender and destination chat must be allowed. Collection requests are limited to one per chat per 30 seconds. Empty lists deny access. Commands:

- `/info TARGET [EXPECTED_ID]`: resolve the entity and collect full metadata.
- `/export TARGET [EXPECTED_ID]`: collect metadata, accessible messages, participants, user profile photos and available media; export and send the report to the same authorized chat.
- `/help` or `/start`: command guidance.

`TARGET` is a username or canonical Telegram peer ID: positive user/bot ID, negative basic-group ID, or marked `-100…` supergroup/channel ID. Numeric peers need an access hash already known to the configured session, except basic groups. A public username provides a supported resolution path. IC never fabricates access hashes. `EXPECTED_ID` is enforced before acquisition; mismatches stop the operation.

Polling refuses to start while a webhook is active. Disable the webhook explicitly through your existing deployment before switching hosts. Do not run two polling instances for the same token. The poller emits `operational` only after Bot API and MTProto authentication and webhook checks succeed. Ctrl-C disconnects the client.

## Single runs and delivery validation

```bash
# Read-only acquisition with local exports:
ALVO=telegram CHAT_ID= MODO=resumo .venv/bin/python scripts/ic.py run

# Explicitly choose the destination using its numeric ID:
ALVO=telegram EXPECTED_ID=-1000000000000 CHAT_ID=123456789 \
  .venv/bin/python scripts/ic.py run
# Replace those example IDs with the real, independently verified IDs.

# Supported message-by-ID retrieval where history is unavailable:
ALVO=telegram MESSAGE_IDS=10,11 CHAT_ID= .venv/bin/python scripts/ic.py run

# Sends synthetic text, a PNG, Markdown, JSONL and ZIP, then retrieves all uploads:
CHAT_ID=123456789 .venv/bin/python scripts/ic.py validate-delivery
```

An explicit `CHAT_ID` authorizes delivery for a trusted local run. An absent destination performs no send. Optional `MESSAGE_ID` edits the existing status message with the final summary; report documents are still sent separately. `getChat` must return that exact numeric destination before report submission. Telegram must allow the bot to write there (for example, the user has started the bot, or the bot has the necessary group/channel rights).

Entry-point compatibility is retained: `scripts/resolver.py`, `scripts/validar_apis.py` and `scripts/validar_entrega.py` execute the corresponding normal workflows. `validar_apis.py` needs an explicit `ALVO` and never delivers a report.

Exit codes: **0** completed within the requested scope; **1** configuration, identity, protocol, authentication or delivery failure; **2** local acquisition/export completed with partial or restricted categories; **130** interrupted. Successful Bot API submissions mean **API acceptance**. Telegram does not expose recipient read/delivery receipts to bots; IC never claims those states.

## Collection scope and export

`MODO=resumo` requests metadata; `MODO=completo` requests `metadata,messages,participants,photos,media`. `IC_CATEGORIES` replaces that selection explicitly. Additional connected categories are `music,gifts,catalog,boosts,stickers,topics,bot_details`:

- `music`: profile music via `users.getSavedMusic`, offset pagination.
- `gifts`: saved gifts via `payments.getSavedStarGifts`, cursor pagination.
- `catalog`: the available MTProto gift catalog.
- `boosts`: channel/supergroup boost status/list and current bot membership.
- `stickers`: referenced custom emoji and sticker-set metadata, with batched requests.
- `topics`: known forum topics referenced by the collected messages, not a claim to enumerate every forum topic.
- `bot_details`: Bot API user photo/audio pagination or group administrator/member-count metadata.

Example: `IC_CATEGORIES=metadata,music,gifts,stickers,media`. Downloadable MTProto documents referenced in the selected extra metadata are included when `media` is selected. Full gift/boost catalogs and other users' personal-channel histories are not fetched implicitly. Query another chat explicitly as a separate target to authorize its history. Every category's status, successful pages, record count, known expected count and restriction/interruption reason are recorded. `complete_available` means the requested API scope exhausted successfully under the session's visibility; it does not prove access to all Telegram records.

Bots cannot use some history/member APIs. Telegram privacy, membership, administrator rights and account type determine availability. Such responses remain explicit `restricted`/`partial` states; they are never replaced by synthetic data. Supply an already-authorized `TELETHON_STRING_SESSION` to use a user account when that account has the required access. IC does not prompt for login codes or create user sessions interactively.

Exports are written under `.ic/exports/<run-id>/` (override `IC_OUTPUT_DIR`). JSONL uses one independently parseable record per line: `category`, `value`, and an `index` for members of a top-level list. Sort indexed records by index to reconstruct a list. Empty lists and objects remain explicit. Integers, booleans, null, source text and timestamps retain their canonical serialization. Markdown uses escaped headings and collision-safe fenced blocks; Telegram messages use escaped supported HTML. Source objects stay unchanged; disclosure copies remove access hashes, phone numbers, credentials and file capabilities. Reports may still contain the explicitly requested messages and profile data: keep the output directory private and delete reports when no longer needed.

Media is SHA-256 verified before packaging and checked against the ZIP contents. Uploads are split into bounded archives with manifests. `IC_MAX_PAGES` bounds collection; reaching it marks the result partial. `IC_MAX_MEDIA_BYTES` defaults to 40 MiB per file; larger downloads are interrupted and recorded. Oversized individual export records fail explicitly. Bot API hosted file download is limited to 20 MiB; validation reports larger downloads as unavailable. Photos may be recompressed by Telegram, so photo validation hashes the retrieved image; documents must match the submitted bytes exactly.

`.ic/delivery.sqlite` records preparation, submission, rejection/acceptance and uncertain outcomes. Read requests have bounded retries; sends retry only Telegram's explicit `429` refusal with `retry_after <= 30` seconds. Transport/5xx/malformed send responses are never blindly retried. A stable `IC_OPERATION_ID` identifies retries of the same logical local run; GitHub runs use their run ID and polling uses update IDs. Persistent claimed updates suppress replay after a crash. This favors avoiding duplicate disclosures: an interrupted claimed update can remain unprocessed. Reconcile it manually before issuing a new operation. Do not delete state databases to retry an uncertain send.

## Hosted TgCloud workflow

The optional hosted handlers dispatch `.github/workflows/resolver.yml`. They deny unlisted users/chats, enforce callback validation, suppress repeated update IDs and bound dispatch frequency. Inline queries return a private-chat link and never initiate collection or disclose reports inline.

Configure repository secrets `BOT_TOKEN`, `API_ID`, `API_HASH`, `TGCLOUD_TOKEN`, `GH_DISPATCH_TOKEN`, plus repository variables `ALLOWED_USER_IDS` and `ALLOWED_CHAT_IDS`. The dispatch token needs **Actions: write** for this repository. The deployment workflow validates allowlists and injects configuration into the private deployed modules; committed placeholders remain empty. TgCloud account access and migration/deployment authorization are required. No deployment or GitHub push is performed by local validation. GitHub logs contain status summaries, not report payloads; reports are not uploaded as workflow artifacts automatically. Without a destination, hosted runner exports disappear when its workspace is removed.

Telethon requires outbound MTProto connectivity to Telegram data centers; ordinary HTTPS proxy access alone does not provide that TCP route. Configure the execution environment's permitted TCP path before live MTProto runs. Never disable TLS verification for Bot API access.

## Verify

```bash
npm run check
.venv/bin/python scripts/compatibility.py
npm test
npm run demo
```

`npm test` uses a real loopback HTTP server and controlled installed-version Telethon objects. It exercises normal entry points, exports, multipart delivery/retrieval, pagination, authorization, protocol errors, throttling and uncertain-send safeguards. These are **local controlled integrations, not live Telegram success**. `npm run demo` retains generated reports and a labeled execution record under `.ic/controlled/`. Local sockets must be permitted by the execution sandbox.

See [the recovery report](docs/recovery-results.md) for observed outcomes. Older documents under `docs/` describe previous implementations and are historical, not the current runtime contract.

Technical contracts: [Telegram Bot API](https://core.telegram.org/bots/api), [MTProto peer IDs and access hashes](https://core.telegram.org/api/peers), [MTProto authorization](https://core.telegram.org/api/auth), [Telethon client reference](https://docs.telethon.dev/en/stable/modules/client.html). Installed-version constructors and client signatures are also verified by `scripts/compatibility.py`.
