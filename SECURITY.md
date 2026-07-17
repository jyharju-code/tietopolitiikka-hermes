# Security

## Supported deployment

The supported deployment is one Linux host with Docker Compose, no public application ports, and SSH administration using keys. Report private vulnerabilities directly to the repository owner instead of opening a public issue containing sensitive details.

## WhatsApp bridge risk

Hermes uses Baileys to emulate a linked WhatsApp Web device. This is not the official WhatsApp Business API. The account can be restricted, the bridge can break after protocol changes, and re-pairing can be required.

Use these controls:

1. Use a dedicated number that is not a personal account.
2. Keep traffic conversational and low volume.
3. Do not send unsolicited or bulk messages.
4. Add only the two approved group IDs.
5. Replace the temporary `*` sender allowance with the approved member numbers after discovery.
6. Protect the linked device session directory like a password.

## Agent permissions

WhatsApp receives only the `skills` toolset. The memory provider adds its own narrow memory tools and can ingest an explicitly marked URL. The following capabilities are intentionally absent:

1. Shell and process execution.
2. General file reading and writing.
3. Browser automation.
4. Cron creation.
5. Cross-platform message sending.
6. Docker socket access.
7. Host filesystem mounts.
8. General web search.

## Secret handling

Secrets live in `.env.runtime` on the deployment host with mode `600`. The file is ignored by Git. Never print `docker compose config` in CI or support logs because interpolated output can include secrets.

The following values are secret:

1. `DEEPSEEK_API_KEY`.
2. `OPENVIKING_API_KEY`.
3. WhatsApp session credentials under the Hermes data directory.
4. SSH keys and any offsite backup credentials.

Group IDs and phone numbers are personal operational data. They are not API secrets, but they must not be committed to this public repository.

## Incident response

If the bot behaves unexpectedly:

1. Stop the Hermes container.
2. Unlink the device from WhatsApp on the bot phone.
3. Preserve logs and timestamps for review.
4. Rotate the DeepSeek API key if exposure is possible.
5. Review OpenViking resources and memory writes.
6. Notify affected members when required.
7. Restore from a known good backup only after the cause is understood.
