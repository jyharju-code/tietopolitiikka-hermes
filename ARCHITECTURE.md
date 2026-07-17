# Architecture

## Trust boundaries

```text
WhatsApp group
    |
    | encrypted WhatsApp Web session
    v
Hermes container
    |                         |
    | passive local ingest    | addressed conversation
    v                         v
OpenViking container         DeepSeek API
    |
    | local embedding requests
    v
Ollama BGE-M3 container
```

No service publishes an internet facing port. WhatsApp and DeepSeek connections are outbound. Administrative access happens through SSH and Docker on the host.

## Group behavior

### Main group

Every main-group message enters the local archive and OpenViking memory path. A message enters the Hermes conversational agent only when one of these conditions is true:

1. The bot account is explicitly mentioned.
2. The message begins with the configured wake word `Hermes`.
3. The message replies to a Hermes message.
4. The message is an allowed slash command.

For other main-group messages, a fail-closed gateway hook writes the message, URLs, and attachments to a durable local ingest spool. It then returns without creating an agent event. A sequential background worker drains the spool to OpenViking, so slow CPU embedding does not block WhatsApp message routing. DeepSeek does not receive these passive messages.

### Auxiliary group

Only the exact auxiliary group JID is added to `free_response_chats`. Every message in `tietopolitiikka.hermes` is first archived and indexed locally, then reaches Hermes as a normal conversational turn. A five second debounce window combines rapid message fragments for the conversational response.

## Memory scopes

OpenViking uses one shared project identity:

```text
account: tietopolitiikka
user: whatsapp-group
agent: tietopolitiikka-hermes
```

Each WhatsApp group has a separate Hermes session history, while OpenViking provides one shared semantic memory and resource library. This allows either group to retrieve sources added from the other group.

## Storage rules

1. Every URL and attachment becomes a durable resource automatically.
2. A member can store an additional short fact with `muista:`.
3. Every resource keeps its original URL or a local copy of the uploaded source object.
4. Search results should cite the resource title and source URI.
5. A request containing `unohda` or `poista muistista` starts a deletion flow.
6. Broad deletion requires an administrator and is performed through the OpenViking CLI.

## Model routing

Hermes uses the direct DeepSeek provider with a low output cap for addressed main-group messages and auxiliary-group conversations. The passive ingest hook writes directly to OpenViking's content API, so this path does not invoke OpenViking's VLM analysis or DeepSeek. OpenViking creates 1024-dimensional embeddings locally with Ollama and `bge-m3`.

DeepSeek does not provide the vector embeddings in this design. This is intentional because the knowledge index and embedding inputs should remain on the Helsinki server.

## Resource isolation

The stack has its own Compose project, bridge network, data directories, logs, and backup directory. It does not mount the Docker socket. It does not join Verifi networks or mount Verifi volumes. Container memory and CPU limits reduce the effect of a runaway extraction job on neighboring services.

## Recovery

The recoverable state consists of:

1. Hermes state and session database.
2. WhatsApp linked device credentials.
3. OpenViking workspace and vector index.
4. Runtime configuration and encrypted secret backup, if maintained separately.

Ollama model weights are recreated with `ollama pull bge-m3`.
