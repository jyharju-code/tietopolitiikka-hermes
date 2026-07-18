# Tietopolitiikka Hermes

Tietopolitiikka Hermes is a self-hosted group assistant for one private
Telegram supergroup. Every accepted message, URL, and attachment is archived
and indexed locally with BGE-M3. The same Hermes instance is available through
an authenticated web dashboard at `tietopolitiikka.pages.dev`.

## User surfaces

1. A private Telegram supergroup where every member may direct Hermes.
2. The upstream Hermes dashboard behind the Telegram Login Widget and a current
   group membership check.
3. An optional linked Telegram broadcast channel for announcements. The channel
   is not the conversational surface.

## Components

| Component | Purpose |
| --- | --- |
| Hermes Agent | Conversation, Telegram routing, dashboard, tools, and sessions |
| Telegram adapter | Official Bot API integration with group and topic support |
| Local ingest hook | Durable archive of every accepted message, URL, and file |
| OpenViking | Shared semantic memory and traceable source library |
| Ollama BGE-M3 | Local multilingual embeddings with one-model concurrency |
| DeepSeek or Mistral | Configurable conversational inference provider |
| Cloudflare Pages worker | Telegram Login Widget, membership authorization, dashboard proxy |
| Cloudflare Tunnel | Outbound-only route to the private Hermes dashboard |

## Important defaults

1. The Telegram token and group ID are empty, so a fresh installation is fail
   closed.
2. Direct messages are disabled.
3. Only one exact supergroup ID is accepted.
4. Every accepted message is spooled locally before agent routing.
5. Every URL and cached attachment is archived and indexed automatically.
6. Attachments and generated artifacts are published to one dashboard files
   root, and any of them can be delivered back into the chat as a native
   Telegram attachment.
7. The complete raw archive and BGE-M3 embeddings remain on the server.
8. The response model receives a large dynamically assembled context, including
   recent discussion, summaries, decisions, and retrieved sources.
9. Telegram receives the complete Hermes tool catalog, including web, browser,
   terminal, files, code execution, delegation, cron, skills, and memory. Tools
   that require an unconfigured external account remain unavailable at runtime.
10. No Compose service publishes a host port.
11. The stack has its own networks, volumes, secrets, logs, and backup path.

## Model selection

The pilot defaults to DeepSeek V4 Flash because its one-million-token context
window is inexpensive. Change `LLM_PROVIDER` and `LLM_MODEL` to use Mistral
Small 4 through Mistral's EU endpoint. Telegram, memory, and dashboard code do
not depend on either provider.

The normal configuration protects 160 recent turns and allows OpenViking to
inject up to 700,000 characters of relevant memory. Replies may run up to 8000
output tokens, so Hermes answers at whatever length the task needs while still
keeping short questions short.

## Local validation

```bash
python3 -m unittest discover -s tests -v
bash -n ops/*.sh images/openviking/*.sh
node --check pages/_worker.js
docker compose --env-file .env.example config --quiet
docker compose --env-file .env.example build hermes
```

## Deployment

1. Create a dedicated bot with BotFather.
2. Create a private Telegram supergroup and add the bot as an administrator.
3. Put the dedicated token and exact numeric group ID in `.env.runtime`.
4. Install runtime secrets with mode 600.
5. Run `ops/deploy.sh`.
6. Configure the private Cloudflare Tunnel origin to `http://hermes:9119`.
7. Set the Pages secrets documented in `pages/README.md`.
8. Deploy Pages with `ops/deploy-pages.sh`.
9. Link the Pages domain to the bot in BotFather with `/setdomain`.

The optional local Telegram Bot API is enabled with
`TELEGRAM_LOCAL_API_ENABLED=true`. It is built from the pinned official
Telegram Bot API source and supports Telegram files larger than the public Bot
API download limit.

## Operations

```bash
ops/healthcheck.sh
ops/backup.sh
ops/discover-telegram.sh
docker compose --env-file .env.runtime logs -f hermes
```

Read [ARCHITECTURE.md](ARCHITECTURE.md), [PRIVACY.md](PRIVACY.md), and
[SECURITY.md](SECURITY.md) before inviting members.
