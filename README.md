# hermes-session-platform

Standalone **Session** (getsession.org) gateway adapter for [Hermes Agent](https://github.com/NousResearch/hermes-agent).

This is a **community / third-party plugin**, not an in-tree Hermes platform. It was extracted from the approach in [PR #6948](https://github.com/NousResearch/hermes-agent/pull/6948) after maintainers directed Session integrations to the platform-plugin registry (`ctx.register_platform`) instead of core tree changes.

> **Network risk:** Session Foundation funding/status has been uncertain. Use at your own risk; this plugin is optional and does not ship with Hermes.

## Prerequisites

- Hermes Agent with the platform plugin registry (post platform-plugin migration)
- Node.js **≥ 24.12.0** and npm
- A Session account (created by setup, or restored from a 13-word mnemonic)

## Install

### Option A — user plugin directory (recommended)

```bash
git clone <this-repo-url> ~/.hermes/plugins/session-platform
cd ~/.hermes/plugins/session-platform/bridge
npm install

# User plugins are opt-in:
hermes plugins enable session-platform
```

### Option B — pip entry point

```bash
pip install -e /path/to/hermes-session-platform
hermes plugins enable session-platform
```

Entry point group: `hermes_agent.plugins` → `session-platform = adapter:register`.

## Setup

```bash
hermes gateway setup
# pick Session → create or restore account, enter YOUR Session ID
hermes gateway restart
```

Setup will:

1. `npm install` in this plugin’s `bridge/`
2. Run the bridge with `--setup` / `--check`
3. Save `SESSION_BOT_ID`, optional `SESSION_MNEMONIC`, `SESSION_HOME_CHANNEL`, `SESSION_ALLOWED_USERS`, etc. into `~/.hermes/.env`

**Never commit or paste your mnemonic.** Prefer backing it up offline; runtime only needs `SESSION_BOT_ID` + the data directory.

## Environment variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `SESSION_BOT_ID` | yes | Bot public Session ID (`05…`) |
| `SESSION_MNEMONIC` | no | 13-word backup (optional after setup) |
| `SESSION_ALLOWED_USERS` | recommended | Comma-separated user IDs allowed in DMs |
| `SESSION_ALLOW_ALL_USERS` | no | Dev-only open access |
| `SESSION_GROUP_ALLOWED_USERS` | no | Group sender allowlist (**adapter-enforced**) |
| `SESSION_GROUP_ALLOWED_CHATS` | no | Group ID allowlist (`03…`, **adapter-enforced**) |
| `SESSION_HOME_CHANNEL` | for cron | Default deliver target |
| `SESSION_BOT_NAME` | no | Display name (default `Hermes`) |
| `SESSION_DATA_PATH` | no | Absolute path for account data |
| `SESSION_BRIDGE_PORT` | no | Local bridge HTTP port (default `8095`) |
| `SESSION_LOG_LEVEL` | no | Bridge log level (default `warn`) |

Use **absolute paths** for `SESSION_DATA_PATH` (tilde is not expanded in `.env`).

## Display / tool progress

Session does not support message editing. Avoid progress spam:

```yaml
# ~/.hermes/config.yaml
display:
  platform_tool_progress:
    session: off
```

The agent is instructed (via `platform_hint`) to use **plain text only** — no markdown.

## Cron delivery

```text
deliver=session
```

Requires the gateway (and thus the bridge) to be running. `standalone_sender_fn` posts to `http://127.0.0.1:<bridge_port>/send`.

## Architecture

```
Session app  ↔  Node bridge (@bonesgit/session-desktop-library)
                    ↕ HTTP/SSE 127.0.0.1:8095
               SessionAdapter (this plugin)
                    ↕
               Hermes gateway / AIAgent
```

Bridge API (local only): `/health`, `/events` (SSE), `/send`, `/send-typing`, attachments, groups, etc. See `adapter.py` module docstring.

## Development

```bash
cd hermes-session-platform
pytest -q
```

Tests are plugin-local and do not require `Platform.SESSION` in Hermes core.

## Security notes

- Bridge listens on **localhost** only
- Scoped platform lock prevents two profiles from using the same bot ID
- Do not log mnemonics or full env dicts
- Keep `SESSION_ALLOWED_USERS` tight on personal bots

## Troubleshooting

| Symptom | Check |
|---------|--------|
| Plugin not listed | `hermes plugins enable session-platform` |
| Bridge missing | `ls ~/.hermes/plugins/session-platform/bridge/session-bridge.mjs` |
| npm install fails | Node ≥ 24.12; see session-desktop-library CONTRIBUTING |
| Gateway won’t start | `~/.hermes/logs/session-bridge.log`; port conflict on 8095 |
| Duplicate account lock | Another profile/gateway already holds the bot ID lock |

## License

MIT (plugin). `@bonesgit/session-desktop-library` has its own license — see that package.

## Credits

- Original in-tree adapter/bridge work that informed this plugin
- Hermes platform-plugin registry (`gateway/platform_registry.py`, IRC/WhatsApp plugin patterns)
