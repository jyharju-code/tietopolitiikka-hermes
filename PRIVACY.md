# Privacy and consent

This document is an engineering checklist, not legal advice.

## Why this deployment needs special care

The group discusses information policy and may contain identifiable political opinions. Political opinions are a special category of personal data under the GDPR. The assistant also uses a DeepSeek API service whose processing can occur in the People's Republic of China.

The operator should complete and document at least these items before production use:

1. Identify the controller and a contact address.
2. Define the purpose of processing in plain language.
3. Select and document an Article 6 legal basis.
4. Select and document an Article 9 condition for any sensitive personal data.
5. Assess the international transfer and the DeepSeek service terms.
6. Decide whether a data protection impact assessment is required.
7. Obtain explicit, informed agreement from every group member when consent is the chosen basis.
8. Define retention, access, correction, export, and deletion procedures.
9. Record who can administer the server and backups.
10. Revisit the assessment when the model provider, group purpose, or storage behavior changes.

## Data minimization implemented by this repository

1. Direct messages are disabled.
2. Only two exact group IDs are accepted.
3. The main group requires a direct trigger for a visible reply.
4. All messages in both approved groups are archived and indexed locally in OpenViking.
5. Passive main-group messages stop before the agent and are not sent to DeepSeek.
6. Addressed main-group messages and all auxiliary-group messages can be sent to DeepSeek for a conversational answer.
7. Every URL and attachment is archived and indexed automatically without a marker word.
8. Vector embeddings are produced locally with BGE-M3.
9. No public dashboard or API is exposed.
10. WhatsApp sessions receive no terminal or infrastructure tools.
11. Debug logging is off by default.
12. Backups have a defined retention period.

## Suggested group notice

The following text should be adapted with the controller contact and approved by the association before use:

> Ryhmään lisätään oma Hermes-avustaja ja yhteinen hakumuisti. Molempien hyväksyttyjen ryhmien kaikki viestit, URLit ja liitteet tallennetaan sekä indeksoidaan Helsingin palvelimella. Pääryhmässä Hermes vastaa vain, kun se mainitaan, sille vastataan tai viesti alkaa sanalla Hermes. Muut pääryhmän viestit käsitellään vain paikallisella BGE-M3-indeksoinnilla, eikä niitä lähetetä DeepSeekille. Tietopolitiikka.hermes-ryhmässä jokainen viesti tulkitaan avustajalle osoitetuksi ja voidaan lähettää DeepSeekin rajapintaan käsiteltäväksi Kiinassa. Myös Hermekselle osoitetut pääryhmän viestit voidaan lähettää DeepSeekille vastausta varten. Voit pyytää omien tietojesi tarkastusta, korjausta tai poistamista yhteyshenkilöltä [YHTEYSTIETO]. Älä lähetä ryhmiin salassa pidettäviä tai sivullisten arkaluonteisia tietoja.

Consent should be recorded outside the public repository. Never commit member names, phone numbers, WhatsApp group IDs, or consent records here.

## Retention proposal

1. Complete locally indexed conversation records from both groups: 90 days.
2. Automatically archived URL and attachment resources: until deleted by the group or controller.
3. Extracted conversational memories: review every 90 days.
4. Application logs: 14 days.
5. Backups: 14 daily copies.

These are initial technical defaults. The controller should approve or replace them.

## Member commands

The assistant instructions recognize these Finnish phrases:

1. `Mitä muistat minusta?`
2. `Mistä tämä tieto on peräisin?`
3. `Poista muistista tämä tieto: ...`
4. `Unohda dokumentti: ...`

Resource deletion can require administrator confirmation because a broad or ambiguous request could remove shared material belonging to the whole group.
