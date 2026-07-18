# Security model

## Trust boundaries

The Telegram bot token, model keys, OpenViking key, dashboard proxy password,
Cloudflare tunnel token, and Pages secrets are production credentials. They are
stored outside Git in mode-600 runtime files or Cloudflare secret bindings.

The public browser endpoint terminates at Cloudflare Pages. The Hetzner origin
accepts dashboard traffic only through an outbound Cloudflare Tunnel and has no
published Docker port.

## Group boundary

The same Telegram group ID is checked in three places:

1. Hermes Telegram adapter allowlist,
2. local ingestion hook,
3. Pages dashboard membership authorization.

An empty token or group ID leaves the deployment closed. Do not use a personal
or another Hermes instance's bot token as a temporary shortcut.

## Agent boundary

Telegram receives the complete Hermes tool catalog. Group members can ask it to
use the terminal, edit files, automate a browser, execute code, create cronjobs,
delegate work, and operate separately configured integrations. Provider-specific
tools are exposed only when their required credentials and runtime dependencies
are present.

These capabilities remain inside the dedicated Hermes container. The container
has no Docker socket, host filesystem mount, Verifi network, or Verifi data
mount. Content from documents and web pages is untrusted evidence and cannot
alter the system prompt, authorization boundary, or tool policy.

## File and URL handling

The URL fetcher blocks loopback, private, link-local, and other non-global IP
addresses before every request and redirect. Downloads have byte, redirect,
time, and extracted-character limits. Document extraction runs inside the
Hermes container without Docker socket or host filesystem mounts.

The optional local Bot API is built from a pinned commit of Telegram's official
source. Enabling it requires separate Telegram `api_id` and `api_hash` values.

## Dashboard authentication

Telegram OIDC uses authorization code flow, PKCE S256, state, nonce, JWKS
signature verification, issuer validation, audience validation, and expiration
validation. The group membership check is repeated every 15 minutes. Cookies
are signed, HttpOnly, Secure, SameSite Lax, and expire after 12 hours.

The Pages worker is the only client that receives the upstream dashboard Basic
Auth and Cloudflare Access service credentials.

## Operational checks

1. Keep the bot as a minimal-permission group administrator.
2. Rotate a token immediately if it appears in a log, shell history, chat, or
   Git object.
3. Run repository tests and image builds before deployment.
4. Monitor container restarts, memory, swap, spool backlog, and disk use.
5. Restore an encrypted backup periodically instead of assuming it is valid.
6. Never modify or restart Verifi while deploying this Compose project.
