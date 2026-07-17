# Privacy and member notice

This is an engineering checklist, not legal advice.

## Processing model

The private Telegram supergroup can contain identifiable political opinions.
Every accepted group message, URL, and attachment is copied from Telegram to
the Tietopolitiikka Hermes server and indexed in the shared local memory.

Unlike Telegram Secret Chats, Telegram groups are cloud chats and are not
end-to-end encrypted. A member's data can therefore be processed by Telegram,
the Hetzner-hosted Tietopolitiikka Hermes stack, the selected conversational
model provider, and the encrypted backup destination.

The selected conversational provider receives a large dynamically assembled
context. This can include recent group discussion, historical summaries,
decisions, member-attributed messages, and relevant document excerpts. The
full raw archive and BGE-M3 embeddings remain on the Hetzner server, but this
does not mean that only short excerpts are sent to the model.

## Required organizational decisions

Before inviting members, document at least:

1. controller and contact address,
2. processing purposes,
3. Article 6 legal basis,
4. Article 9 condition for special-category data,
5. model provider and processing region,
6. retention, access, correction, export, and deletion procedures,
7. administrators and backup access,
8. whether a data protection impact assessment is required.

Changing from DeepSeek to Mistral changes the international processing facts
and requires the member notice to be updated.

## Proposed member notice

> Ryhmään on liitetty Tietopolitiikka Hermes, yhteinen keskustelukumppani ja
> hakumuisti. Ryhmän kaikki viestit, URL-osoitteet ja liitteet tallennetaan ja
> indeksoidaan tietopolitiikka.fi:n hallinnoimalla Hetzner-palvelimella.
> Hermeksen vastausmallille voidaan lähettää suuri määrä keskusteluhistoriaa,
> tiivistelmiä ja lähdeaineistoa vastauksen muodostamista varten. Käytössä oleva
> mallipalvelu ja käsittelyalue ilmoitetaan tässä viestissä ennen käyttöönottoa.
> Telegram-ryhmä ei ole päästä päähän salattu. Dashboardiin pääsee vain
> Telegram-ryhmän nykyisellä jäsenyydellä. Omien tietojen tarkastusta, korjausta
> tai poistoa voi pyytää yhteyshenkilöltä [YHTEYSTIETO]. Älä lähetä ryhmään
> salasanoja, tunnistautumiskoodeja tai sivullisten salassa pidettäviä tietoja.

## Technical deletion behavior

Telegram Bot API does not reliably notify a bot when an ordinary group message
is deleted. Removing a Telegram message therefore does not automatically remove
the local archive. A local deletion command and an administrator dashboard flow
must identify and remove the raw source, extracted chunks, and vectors.

## Initial retention proposal

1. Complete group archive: retained until the controller changes the policy or
   an applicable deletion request is completed.
2. Application logs: 14 days.
3. Encrypted backups: 14 daily copies.
4. Failed ingest spool: retained until successfully processed or explicitly
   reviewed by an administrator.
