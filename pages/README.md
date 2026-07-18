# Cloudflare Pages deployment

The Pages worker authenticates users with the Telegram Login Widget, verifies
current membership in the configured private supergroup, and proxies the
upstream Hermes dashboard. The browser never receives the origin Basic Auth or
Cloudflare Access service credentials.

Link the bot to the Pages domain in BotFather with `/setdomain` and enter
`tietopolitiikka.pages.dev`. The Login Widget only works on the linked domain.

Create a Pages project named `tietopolitiikka` and set these secrets.

Login phase:

```text
SESSION_SECRET
TELEGRAM_BOT_USERNAME
TELEGRAM_BOT_TOKEN
TELEGRAM_GROUP_ID
```

Dashboard proxy phase:

```text
HERMES_ORIGIN
ORIGIN_BASIC_AUTH_PASSWORD
CF_ACCESS_CLIENT_ID
CF_ACCESS_CLIENT_SECRET
```

`TELEGRAM_BOT_USERNAME` is the dedicated bot's username without the leading `@`.
`TELEGRAM_BOT_TOKEN` is the Bot API token. The worker uses it both to verify the
Login Widget signature (HMAC-SHA256 keyed by `SHA256(token)`) and for the
`getChatMember` membership check. There is no OIDC client secret in this flow.
Production identifiers are stored as Pages secrets instead of `wrangler.toml` so
they stay out of the public repository.

When only the login phase secrets are present, members can sign in and see a
confirmation page. The worker starts proxying the upstream dashboard once the
proxy phase secrets are also present.

Deploy from the repository root with `ops/deploy-pages.sh`. An interactive
`npx wrangler login` OAuth session is enough; a scoped `CLOUDFLARE_API_TOKEN`
with Pages edit rights also works for non-interactive runs.
