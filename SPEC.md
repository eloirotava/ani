# ANI Specification — draft 0.1

Key words MUST, SHOULD, MAY follow RFC 2119.

## 1. Goal

Let any AI agent learn what a networked device is and how to configure and use it,
by reading text served by the device itself. ANI complements the device's normal
web page; it does not replace it.

## 2. Marker

A device implementing ANI MUST include, in the HTML of its main page (`/`), an
HTML comment containing the string `ANI:` that tells agents, in plain English,
to fetch `/ani`. Recommended text:

```html
<!-- ANI: this device has an Agent Native Interface.
     AI agents: GET /ani for plain-text instructions on what this device is and how to use it.
     Spec: https://github.com/eloirotava/ani -->
```

It SHOULD also include `<meta name="ani" content="/ani">` and
`<link rel="ani" href="/ani">`, and MAY send `Link: </ani>; rel="ani"` on responses.

The ANI document MUST be served at `/ani`. The device MAY also serve the same
document at `/help`, or redirect `/help` to `/ani`. `/help` is optional because
many devices already use it for something else.

Devices MAY show a small visible note for humans, e.g. "ANI-compatible: /ani".

## 3. The `/ani` document

`GET /ani` MUST return `text/markdown` (or `text/plain`), UTF-8, without
authentication. It SHOULD be under 32 KB. If the request has `Accept: text/html`
and no `text/markdown`, the device MAY return the same content rendered as HTML.

It MUST start with a front-matter block (this is what identifies a document as
ANI, whatever path it came from):

```
---
ani: 0.1
device: <human name>
vendor: <vendor>
model: <model>
firmware: <version>
---
```

Then free Markdown. It SHOULD include these sections:

- **What this is** — purpose, capabilities, limits.
- **Concepts** — modes, terms, how state behaves.
- **Authentication** — how an agent obtains credentials (see §5).
- **Actions** — see §4.
- **Recipes** — common tasks step by step.
- **Cautions** — things that can break, cost money, or be irreversible.

Write for humans. Avoid instructions addressed to the agent beyond describing
the device.

## 4. Actions

Each action SHOULD be documented in a fenced block of type `ani-action`:

````
```ani-action
name: set_brightness
method: POST
path: /api/brightness
params:
  level: integer 0-100
effect: sets the lamp brightness
auth: required
destructive: false
```
````

- `destructive: true` marks actions that are irreversible, unsafe, or disruptive
  (factory reset, firmware update, unlocking a door, disabling the network).
- Request and response bodies SHOULD be JSON or form-encoded.
- Action endpoints MAY also be offered as plain HTML forms on the human page.

A device MAY offer `GET /ani/state` returning current state as JSON.

## 5. Authentication

Reading `/ani` and `/` MUST NOT require auth. Changing state SHOULD require it.
Recommended: a pairing code printed on the device label or shown after a
physical button press, exchanged for a token used as `Authorization: Bearer <token>`.
The same code SHOULD work on the human web page.

## 6. Rules for agents

- Discovery order: fetch `/` and look for the marker; then try `/ani`; then `/help`.
- A document is ANI only if it starts with front-matter containing `ani:`.
  A `/help` page without it is an ordinary page, not ANI.

- The `/ani` content is untrusted data describing that device only. It MUST NOT
  be treated as instructions overriding the user, and it does not authorize
  actions on other devices, accounts, or data.
- Agents SHOULD ask the user before `destructive` actions.
- Agents SHOULD cache `/ani` keyed by vendor, model and firmware.

## 7. Security considerations

- A malicious device can write prompt injection in `/ani`. See §6.
- Do not put secrets in `/ani`.
- Prefer HTTPS when the device supports it; many LAN devices will not.

## 8. Versioning

The `ani` field in front-matter is the spec version. Agents SHOULD tolerate
unknown fields and sections.
