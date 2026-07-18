# Architecture

## Request paths

```text
Private Telegram supergroup
    -> official Telegram Bot API
    -> Hermes Telegram adapter
    -> durable local ingest spool
    -> sequential URL and file extraction
    -> OpenViking
    -> local BGE-M3

Telegram turn
    -> Hermes session and large context assembly
    -> selected DeepSeek or Mistral provider
    -> full Hermes tool catalog inside the isolated Hermes container
    -> reply in the original Telegram topic

Browser
    -> tietopolitiikka.pages.dev
    -> Telegram OIDC and getChatMember authorization
    -> Cloudflare Tunnel
    -> upstream Hermes dashboard
```

## Telegram authorization

The adapter accepts only the exact configured `TELEGRAM_GROUP_ID`. DMs are
disabled and the group policy is allowlist. The bot must be an administrator so
it receives all group messages and `getChatMember` can reliably authorize
dashboard users.

Every group message is a possible conversational turn. Hermes may return
`NO_REPLY` when the message is clearly conversation between members and does
not require an agent response. The message is still archived and indexed.

Telegram forum topics produce separate live sessions. OpenViking remains one
shared knowledge store for the entire group.

The Telegram adapter loads `hermes-telegram`, which contains the complete core
catalog for messaging surfaces, plus every upstream opt-in toolset. This covers
web research, browser automation, terminal and process execution, files, code
execution, delegation, cronjobs, vision, generation, skills, memory, and any
separately configured service integrations. Runtime checks hide a provider tool
when its credentials or executable dependency are absent.

## Durable ingest

The derived Hermes image adds one narrow override to the upstream Telegram
adapter. Before `BasePlatformAdapter.handle_message` receives an accepted
event, the override calls `archive_telegram_event`.

The ingest hook validates the group ID again and writes a mode-600 JSON spool
record. A sequential worker then:

1. writes the message and provenance to OpenViking,
2. downloads public URLs through an SSRF-protected fetcher,
3. copies Telegram-cached attachments to local storage,
4. extracts text from HTML, PDF, DOCX, PPTX, XLSX, text, and images,
5. writes chunked source records through OpenViking `content/write`,
6. lets only the local BGE-M3 service produce embeddings.

Failed jobs remain in the spool and are retried. SHA-256 identifiers prevent
duplicate message, URL, and file resources.

## Large context

The normal model path combines the protected recent transcript with up to 160
OpenViking results and 700,000 characters of memory. Compression begins late
and preserves 160 recent turns. This provides a practical context near 200,000
tokens while remaining portable to Mistral Small 4.

DeepSeek V4 Flash can accept a larger context after a future explicit deep-mode
control is added. The current repository does not pretend that more context is
always better. Retrieval score, provenance, recency, and topic identity still
control assembly order.

## Dashboard security

The upstream dashboard listens only on the private Docker `edge` network. It
requires a random Basic Auth credential known only to the Pages worker and the
Hermes container. No host port is published.

The Pages worker uses Telegram authorization code flow with PKCE and validates
the RS256 ID token against Telegram JWKS. It then calls `getChatMember` for the
exact group. Membership is checked again every 15 minutes. Sessions are signed,
HttpOnly, Secure, SameSite Lax cookies with a 12-hour maximum age.

The worker adds the private origin Basic Auth and optional Cloudflare Access
service token while proxying. Those credentials never reach the browser.

## Eight gigabyte pilot profile

The enforced service limits are approximately:

| Service | Limit |
| --- | ---: |
| Ollama and BGE-M3 | 1600 MB |
| OpenViking | 900 MB |
| Hermes gateway and dashboard | 1024 MB |
| Optional local Bot API | 384 MB |
| Cloudflare Tunnel | 128 MB |

Only one embedding model and one embedding request run concurrently. Document
ingest is sequential. The language model runs remotely. The expected active
Tietopolitiikka footprint stays below about four gigabytes.

## Isolation

The Compose project is named `tietopolitiikka-hermes`. It does not mount the
Docker socket, join Verifi networks, mount Verifi data, or share state with the
other Hermes instance. All application capabilities are dropped except the
minimal user-switching capabilities required by the upstream Hermes image.
