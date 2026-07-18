# Cloudflare Pages deployment

The Pages advanced worker authenticates users with Telegram OIDC, verifies
current membership in the configured private supergroup, and proxies the
upstream Hermes dashboard. The browser never receives the origin Basic Auth or
Cloudflare Access service credentials.

Create a Pages project named `tietopolitiikka`, configure the BotFather Web
Login allowed URL as `https://tietopolitiikka.pages.dev`, and set these secrets:

```text
SESSION_SECRET
TELEGRAM_CLIENT_SECRET
TELEGRAM_BOT_TOKEN
ORIGIN_BASIC_AUTH_PASSWORD
CF_ACCESS_CLIENT_ID
CF_ACCESS_CLIENT_SECRET
```

The non-secret variables live in `wrangler.toml`. `TELEGRAM_CLIENT_ID` is the
numeric ID of the dedicated bot. `TELEGRAM_CLIENT_SECRET` is the separate OIDC
client secret that BotFather shows when the Web Login allowed URLs are
registered. It is not the Bot API token. `TELEGRAM_BOT_TOKEN` remains the Bot
API token and is used only for the `getChatMember` membership check.

Deploy from the repository root with `ops/deploy-pages.sh` after authenticating
Wrangler with an API token that can edit Pages projects.
