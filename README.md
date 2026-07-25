# hermes-session-platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Hermes plugin](https://img.shields.io/badge/Hermes-platform%20plugin-blue)](https://github.com/NousResearch/hermes-agent)
[![GitHub](https://img.shields.io/badge/GitHub-BonesGit%2Fhermes--session--platform-181717?logo=github)](https://github.com/BonesGit/hermes-session-platform)

Standalone **Session** ([getsession.org](https://getsession.org)) messaging gateway for [Hermes Agent](https://github.com/NousResearch/hermes-agent).

> **Not in-tree Hermes.** Session was declined as a core platform ([PR #6948](https://github.com/NousResearch/hermes-agent/pull/6948)) under the third-party product policy. This repo is the supported shape: a user plugin via `ctx.register_platform` / `gateway.platform_registry`.

**One-liner install:**
```bash
git clone https://github.com/BonesGit/hermes-session-platform.git ~/.hermes/plugins/session-platform \
  && cd ~/.hermes/plugins/session-platform && npm install \
  && hermes plugins enable session-platform && hermes gateway setup && hermes gateway restart
```

> **Network risk:** Session network / foundation status has been uncertain. Optional plugin; use at your own risk.

## Prerequisites

- Hermes Agent with the platform plugin registry (current `main`)
- Node.js **≥ 24.12.0** and npm
- A Session account (created by setup, or restored from a 13-word mnemonic)

## Install

### Option A — user plugin directory (recommended)

```bash
git clone https://github.com/BonesGit/hermes-session-platform.git ~/.hermes/plugins/session-platform
cd ~/.hermes/plugins/session-platform
npm install          # installs bridge/ deps via root postinstall (or: cd bridge && npm install)

hermes plugins enable session-platform
```

### Option B — pip entry point

```bash
pip install -e /path/to/hermes-session-platform
hermes plugins enable session-platform
```

Entry point group: `hermes_agent.plugins` → `session-platform = adapter:register`.

### Confirm you’re on the plugin (not old in-tree code)

After `hermes gateway restart`:

```bash
rg "spawning bridge|Session plugin" ~/.hermes/logs/gateway.log | tail -5
```

Expect:
- Logger: `hermes_plugins.session_platform.adapter`
- Bridge path under this plugin’s `bridge/session-bridge.mjs`
- A line like: `Session plugin v0.1.1 … bridge=…/bridge/session-bridge.mjs`

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

Uses `SESSION_HOME_CHANNEL` (via `cron_deliver_env_var`) and the plugin’s `standalone_sender_fn`, which POSTs to `http://127.0.0.1:<bridge_port>/send`.

**Requirement:** the Hermes **gateway must be running** so the Node bridge is up on `SESSION_BRIDGE_PORT` (default `8095`). Cron in a separate process does not spawn its own bridge.

Example one-shot test (gateway up, home channel set):

```bash
hermes cron add --name "session-ping" --schedule "1m" --repeat 1 \
  --deliver session \
  --prompt "Reply with exactly: session cron ok"
```

If the bridge is down you get a send error (connection refused to localhost), not silent success.

**Port conflicts:** if something else already listens on the bridge port, connect fails with a clear log:
`Session: port 8095 already in use …` — free the port or set `SESSION_BRIDGE_PORT`.

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
npm install          # bridge deps
pytest -q            # needs Hermes on PYTHONPATH or installed
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
| `npm install` at repo root | Supported — runs `postinstall` → `bridge/` |
| npm install fails | Node ≥ 24.12; see session-desktop-library CONTRIBUTING |
| Port already in use | `ss -ltnp \| rg 8095` or change `SESSION_BRIDGE_PORT` |
| Gateway won’t start | `~/.hermes/logs/session-bridge.log`; look for `Session plugin v…` in gateway.log |
| Still on old core adapter? | Logger must be `hermes_plugins.session_platform.adapter`, not `gateway.platforms.session` |

## License

MIT — see [LICENSE](LICENSE).  
`@bonesgit/session-desktop-library` has its own license — see that package.

See also [CHANGELOG.md](CHANGELOG.md) for release history.

## Credits

- Original Session gateway work that informed this plugin ([PR #6948](https://github.com/NousResearch/hermes-agent/pull/6948))
- Hermes platform-plugin registry (`gateway/platform_registry.py`, IRC/WhatsApp plugin patterns)
