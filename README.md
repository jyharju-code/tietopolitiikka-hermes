# Tietopolitiikka Hermes

Tietopolitiikka Hermes is a self-hosted group assistant for two private WhatsApp groups:

1. The main group, where Hermes answers only when mentioned, addressed by name, or replied to.
2. The `tietopolitiikka.hermes` group, where every message is treated as a conversation with Hermes.

The stack runs Nous Research Hermes Agent, OpenViking, and a local Ollama embedding model. DeepSeek provides the conversational model and OpenViking text analysis. Embeddings and the complete knowledge store stay on the server.

## Design goals

1. Keep replies short enough for a real WhatsApp conversation.
2. Store only content deliberately addressed to Hermes.
3. Require the word `muistiin` before a document or URL becomes a permanent shared resource.
4. Keep every stored resource traceable to its source.
5. Give WhatsApp sessions no terminal, file editing, browser automation, cron, or infrastructure tools.
6. Run without public HTTP ports.
7. Keep secrets and WhatsApp session credentials outside Git.

## Components

| Component | Purpose |
| --- | --- |
| Hermes Agent | Conversation, group routing, tools, and WhatsApp gateway |
| Baileys bridge | Unofficial WhatsApp Web connection used by Hermes |
| OpenViking | Shared semantic memory and source library |
| Ollama | Local `nomic-embed-text` embeddings |
| DeepSeek API | Short answers and text analysis |

Hermes uses an unofficial WhatsApp Web bridge. A dedicated bot number is required. Account restrictions and temporary protocol breakage remain possible. See [SECURITY.md](SECURITY.md).

## Safe default behavior

The committed configuration blocks all WhatsApp groups until two exact group JIDs are supplied. Direct messages are disabled. The auxiliary group becomes free response only after its exact JID is configured.

Permanent storage is explicit:

```text
muistiin https://example.org/report
```

```text
muistiin
[attached PDF]
```

Other directed conversation can be used for the current discussion and may produce compact conversational memories when a session closes. The bot does not read or index ordinary main group chatter that was not directed to it.

## Local validation

```bash
python3 -m unittest discover -s tests -v
bash -n ops/*.sh images/openviking/*.sh
```

## Deployment outline

1. Copy `.env.example` to `.env.runtime` and fill the secrets and group JIDs.
2. Run `ops/bootstrap.sh`.
3. Run `ops/deploy.sh`.
4. Pair the dedicated WhatsApp account with `ops/pair-whatsapp.sh`.
5. Add the account to both groups and send one message in each group.
6. Discover the group JIDs with `ops/discover-groups.sh`.
7. Put the two approved JIDs in `.env.runtime` and run `ops/deploy.sh` again.

The first deployment can be completed before WhatsApp pairing. Group access remains closed until step 7.

## Operations

```bash
ops/healthcheck.sh
ops/backup.sh
docker compose --env-file .env.runtime logs -f hermes
```

Backups cover Hermes state, WhatsApp session credentials, and OpenViking data. Ollama model files are reproducible and are not included.

## Privacy

This is intended for a political policy discussion group. Messages can reveal political opinions, which are sensitive personal data under European data protection law. The operator must obtain an appropriate legal basis, provide clear information, and document deletion and retention procedures before production use. Read [PRIVACY.md](PRIVACY.md) before pairing WhatsApp.

## Upstream projects

1. [Nous Research Hermes Agent](https://github.com/NousResearch/hermes-agent), MIT license.
2. [OpenViking](https://github.com/volcengine/OpenViking), AGPL 3.0 license.
3. [Ollama](https://github.com/ollama/ollama), MIT license.

This repository contains deployment configuration and project specific instructions. It does not vendor those upstream codebases.
