# Changelog

All notable changes to **hermes-session-platform** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] — 2026-08-03

### Fixed

- **Node resolution under Hermes gateway PATH.** Hermes-managed Node 22
  (`$HERMES_HOME/node/bin`, first on the gateway unit PATH) no longer shadows
  Session's Node ≥ 24.12 requirement. The adapter now resolves Node via:
  1. `SESSION_NODE` (optional override)
  2. pinned NVM install `v24.12.0` (`~/.config/nvm` / `$NVM_DIR` / `~/.nvm`)
  3. first PATH `node` that is ≥ 24.12.0 (skips 22.x)
- Bridge spawn, setup, doctor, and npm install all use the same resolver and
  prepend that Node's `bin` dir to the child `PATH`.

### Added

- `SESSION_NODE` optional env in `plugin.yaml`
- Unit tests for Node resolution preference order

## [0.1.1] — 2026-07-25

First public GitHub release of the standalone Session plugin for Hermes Agent.

Replaces the declined in-tree approach ([NousResearch/hermes-agent#6948](https://github.com/NousResearch/hermes-agent/pull/6948)) with a user-installable platform plugin (`ctx.register_platform` / `gateway.platform_registry`). No Hermes core tree changes required.

### Added

- Session gateway adapter as a Hermes **platform plugin** (`kind: platform`)
- Local Node.js bridge (`bridge/`) using `@bonesgit/session-desktop-library`
- Plugin registration hooks: env enablement, interactive setup, cron `deliver=session`, standalone send, allow-list env vars, platform hint
- Adapter-side group allowlists (`SESSION_GROUP_ALLOWED_USERS` / `SESSION_GROUP_ALLOWED_CHATS`)
- MIT `LICENSE`
- Root `package.json` with `postinstall` → `npm install` in `bridge/`
- Clear startup fingerprint logs (`Session plugin vX … bridge=…`)
- Bridge port-in-use detection on connect (retryable fatal error)
- Unit tests for paths, env enablement, group allowlists, register hooks
- README with install one-liner, badges, cron notes, troubleshooting

### Notes

- Requires Hermes Agent with the platform plugin registry (current `main`)
- Requires Node.js ≥ 24.12.0 (prefers NVM `v24.12.0`; set `SESSION_NODE` to override)
- User plugins must be enabled: `hermes plugins enable session-platform`
- Cron delivery needs the gateway (and bridge) running
- Session network / foundation status is outside this project’s control

### Install

```bash
git clone https://github.com/BonesGit/hermes-session-platform.git ~/.hermes/plugins/session-platform
cd ~/.hermes/plugins/session-platform && npm install
hermes plugins enable session-platform
# then: hermes gateway setup → restart gateway from your service manager
```

[0.1.2]: https://github.com/BonesGit/hermes-session-platform/releases/tag/v0.1.2
[0.1.1]: https://github.com/BonesGit/hermes-session-platform/releases/tag/v0.1.1
