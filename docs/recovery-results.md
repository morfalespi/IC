# IC recovery: observed results

Validation date: 2026-11-09. Checkout: `morfalespi/IC`, starting commit `bad19f6ce15b4a79124f8e44d0baf213481ed048`. Updated source remains in this workspace. No remote push or deployment was performed.

## Resulting application

The connected local entry point is `scripts/ic.py`; `npm start` runs its continuous polling mode. `scripts/resolver.py` remains the single-run entry point used by GitHub Actions. The replacement core removes hard-coded acceptance, unconditional success exits, fabricated access hashes, raw collection logging, unchecked destination submissions and automatic replay of uncertain sends. Optional metadata operations are explicit categories; automatic cross-chat expansion and inline report disclosure were removed. The previous monolithic Rich Message rendering path was replaced by escaped supported Telegram HTML summaries plus Markdown/JSONL documents. Current Bot API documentation does include Rich Messages; the recovery does not depend on treating that feature as nonexistent.

Dependencies were installed in `.venv` and `node_modules`. Python requirements now resolve through `scripts/requirements-lock.txt`: Telethon 1.45.0, pyaes 1.6.1, pyasn1 0.6.5, rsa 4.9.1. `pip check` reported no broken requirements. The workspace and installed environment are retained.

## Executed validation

| Workflow | Actual observed result |
| --- | --- |
| Configuration check | Exit 1, explicitly names missing `BOT_TOKEN`, `API_ID`, `API_HASH`; no values printed |
| Production single run, `ALVO=telegram` | Exit 1, `BOT_TOKEN is required`; no Telegram request submitted |
| Production polling startup | Exit 1, missing explicit user/chat allowlists; access denied |
| Controlled normal polling entry point | `ic.py bot --once` reached `operational`; authenticated against the local HTTP fixture, handled an authorized export, denied an unauthorized update and suppressed replay |
| MTProto initialization | Actual installed `TelegramClient` and SQLite session constructed; controlled connection/sign-in/getMe methods exercised; session permissions verified as 0600 and mismatched bot identity rejected |
| Entity resolution | User, bot, basic group, supergroup and channel namespaces verified using installed Telethon objects; expected-ID mismatch stopped before metadata retrieval or report delivery |
| Acquisition | Controlled history exhausted with offsets 0 and 4; participant offsets 0 and 2; restricted history exported as partial with exit 2; repeated pages, repeated cursors and interrupted pagination retained accurate successful-page counts |
| Additional metadata | Music, saved gifts, gift catalog, custom emoji, boosts, membership, referenced forum topics and Bot API profile/chat metadata exercised through their connected selectors with installed-version TL response objects |
| Export | Parseable JSONL and Markdown produced by normal workflow; source text/types preserved; disclosure copies redact access hashes, phone numbers, secrets and file capabilities |
| Media | Controlled download produced the expected SHA-256; ZIP contents and manifest verified; tampered source rejected; archive splitting exercised |
| Bot API transport | Real loopback HTTP requests exercised getMe, getChat, sendMessage, sendPhoto, sendDocument and getFile; malformed JSON/envelopes, 401/403, 429 parameters, migration parameters and destination mismatch tested |
| Delivery validation | Text, PNG, Markdown, JSONL and ZIP submitted to local fixture; all four uploads retrieved through getFile; document bytes matched SHA-256; downstream recipient state remained `not_observable` |
| Delivery reliability | Successful duplicate submission suppressed; transport uncertainty not retried; explicit 429 bounded; bot credential namespaces kept separate; operation and per-message acceptance persisted |
| Hosted handlers | Controlled TgCloud SDK checks passed for deny-by-default authorization, dispatch, callback validation, repeated-update suppression, failed dispatch propagation and inline privacy |
| Regression suite | 29 Python integration/regression tests passed; JavaScript handler checks passed |
| Static/runtime compatibility | `npm run check` passed; installed Telethon layer 229 verified 35 imports, 22 constructors and 6 client method signatures; `git diff --check` passed |

These results distinguish local HTTP execution and controlled MTProto responses from external Telegram authentication. No live Telegram account, chat or service was contacted by the integration fixtures.

## Retained executable outputs

The final controlled run is in:

`.ic/controlled/5353ebdb2a85464a84ed153b65b81324/`

It contains `result.json`, `execution.jsonl`, state databases, generated JSONL/Markdown reports, `delivery.json` and `operation.json`. The normal export workflow recorded three accepted messages: a summary and two documents. The separate delivery validator recorded five accepted synthetic messages, with four retrieved uploads. `.ic/validation.txt` contains the final regression output. All these local evidence artifacts are ignored by Git and excluded from source distribution.

Reproduce with `npm test` and `npm run demo`. The demo explicitly reports `external_telegram_contacted: false` and creates a new run directory each time.

## Remaining external prerequisites

No Telegram or TgCloud credentials are present in the environment or configured secret bindings. Consequently, the live bot is **not running**, and live authentication, acquisition and recipient delivery are **not verified**.

| Operation | Required external configuration or permission |
| --- | --- |
| Live getMe and Bot API reads | Valid BotFather `BOT_TOKEN`, HTTPS access to `api.telegram.org`; target must be visible to that bot |
| Live MTProto authentication | Valid `API_ID`/`API_HASH`, token for bot sign-in or already-authorized user `TELETHON_STRING_SESSION`; outbound MTProto connectivity to Telegram data centers |
| Polling operation | Explicit `ALLOWED_USER_IDS` and `ALLOWED_CHAT_IDS`; no active webhook; one polling instance per token |
| History, members, gifts and other restricted metadata | Telegram permits the selected account/API method for that target; a bot cannot acquire methods restricted to user accounts; relevant membership/admin rights where required |
| Live report delivery and verification | Explicit canonical destination `CHAT_ID`; bot may write there and retrieve its returned files; the user has started the bot or appropriate group/channel rights are granted |
| Hosted TgCloud/GitHub execution | TgCloud account/token; repository Actions dispatch token with Actions: write; repository secrets and allowlist variables; authorization to deploy/migrate |

Credentials should be entered in environment secret settings, never in chat or committed source. Live verification can proceed through the same entry points once those prerequisites are supplied. See [README.md](../README.md) for operational instructions and category/limit semantics.
