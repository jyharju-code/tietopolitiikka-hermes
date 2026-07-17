# Architecture

## Trust boundaries

```text
WhatsApp group
    |
    | encrypted WhatsApp Web session
    v
Hermes container
    |
    | private Docker network
    v
OpenViking container ---> Ollama embedding container
    |
    | all messages from two approved groups
    v
DeepSeek API
```

No service publishes an internet facing port. WhatsApp and DeepSeek connections are outbound. Administrative access happens through SSH and Docker on the host.

## Group behavior

### Main group

Every main-group message enters the Hermes session and OpenViking memory path. Hermes sends a visible reply only when one of these conditions is true:

1. The bot account is explicitly mentioned.
2. The message begins with the configured wake word `Hermes`.
3. The message replies to a Hermes message.
4. The message is an allowed slash command.

For other main-group messages, Hermes emits `NO_REPLY`. The gateway suppresses that output but retains the turn in the transcript and memory path.

### Auxiliary group

Both exact group JIDs are added to `free_response_chats` so the gateway does not discard unaddressed main-group messages before memory synchronization. Every message in `tietopolitiikka.hermes` reaches Hermes as a normal conversational turn. A five second debounce window combines rapid message fragments into one turn.

## Memory scopes

OpenViking uses one shared project identity:

```text
account: tietopolitiikka
user: whatsapp-group
agent: tietopolitiikka-hermes
```

Each WhatsApp group has a separate Hermes session history, while OpenViking provides one shared semantic memory and resource library. This allows either group to retrieve sources added from the other group.

## Storage rules

1. A URL or attachment becomes a durable resource only when the message contains `muistiin`.
2. A member can store a short fact with `muista:`.
3. Every resource keeps its original URL or uploaded source object.
4. Search results should cite the resource title and source URI.
5. A request containing `unohda` or `poista muistista` starts a deletion flow.
6. Broad deletion requires an administrator and is performed through the OpenViking CLI.

## Model routing

Hermes uses the direct DeepSeek provider with a low output cap. OpenViking uses the same API key for text analysis. OpenViking creates embeddings locally with Ollama and `nomic-embed-text`.

DeepSeek does not provide the vector embeddings in this design. This is intentional because the knowledge index and embedding inputs should remain on the Helsinki server.

## Resource isolation

The stack has its own Compose project, bridge network, data directories, logs, and backup directory. It does not mount the Docker socket. It does not join Verifi networks or mount Verifi volumes. Container memory and CPU limits reduce the effect of a runaway extraction job on neighboring services.

## Recovery

The recoverable state consists of:

1. Hermes state and session database.
2. WhatsApp linked device credentials.
3. OpenViking workspace and vector index.
4. Runtime configuration and encrypted secret backup, if maintained separately.

Ollama model weights are recreated with `ollama pull nomic-embed-text`.
