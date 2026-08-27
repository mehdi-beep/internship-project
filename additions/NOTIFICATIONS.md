# BIMS — Notification Channels (Task 4)

How assignment notifications work, and how to configure the two optional
external channels (email and WhatsApp).

**Nothing here is required to run BIMS.** With no configuration at all, in-app
notifications work exactly as before; email and WhatsApp simply stay switched
off. No credential is hardcoded anywhere in the codebase — every value below is
read from environment variables.

---

## 1. The rule

When an **Administrator** or **Chef des Techniciens** assigns a planned
intervention to a technician, **only that technician** is notified. It is never
broadcast to all technicians.

| Event | Who is notified | Notification title |
|---|---|---|
| Planning created (normal priority) | the assigned technician only | `New Planning Assignment` |
| Planning created (urgent priority) | the assigned technician only | `Urgent Intervention Assigned` |
| Existing planning escalated to urgent | the assigned technician only | `Urgent Intervention Assigned` |
| Planning edited (same technician) | the assigned technician only | `Planning Modified` |
| Planning **reassigned** to a different technician | the *new* technician | `New Planning Assignment` / `Urgent Intervention Assigned` |
| Planning **reassigned** away from a technician | the *previous* technician | `Assignment Removed` |
| Planning cancelled | the assigned technician only | `Planning Cancelled` |

## 2. Architecture

There is **one** notification system, not two. Every notification is written to
the existing `notifications` table (Ch.46) by `notification_service`, exactly as
before. Task 4 adds a best-effort fan-out of that same content to external
channels:

```
planning_service.create_planning / update_planning / mark_urgent
        │
        ▼
notification_service.notify_*        ← writes the in-app notification (always)
        │
        ▼
notification_service._dispatch_external
        │
        ▼
delivery_service.deliver_external    ← best-effort, never raises
        ├── send_email     (SMTP)
        └── send_whatsapp  (Meta WhatsApp Cloud API)
```

Two guarantees hold throughout:

1. **The in-app notification is always written first**, and is never dependent
   on an external channel succeeding.
2. **An external channel failure never fails the assignment.** Unreachable SMTP
   servers, wrong credentials, expired tokens, timeouts and provider 5xx errors
   are all caught, logged at WARNING level, and swallowed. This is covered by
   tests that deliberately point the app at a dead host and assert the
   assignment still succeeds.

### Notification content

Assignment notifications carry the context the technician needs: client name,
site name and city, planned date and start time, and priority. The email and
WhatsApp copies use the same text plus an absolute link back into the app
(built from `FRONTEND_BASE_URL`).

### In-app navigation

Clicking a notification navigates to the relevant place —
`frontend/src/utils/notificationRouting.ts` resolves the linked planning entry
and deep-links the technician into a pre-filled New Intervention form for that
specific assignment. (`Assignment Removed` is deliberately excluded: the work is
no longer theirs, so it routes to their intervention list instead.)

---

## 3. Email (SMTP) configuration

Set these in `backend/.env` (which is gitignored — never put real credentials in
`.env.example`):

| Variable | Required | Description |
|---|---|---|
| `EMAIL_ENABLED` | yes | `true` to switch the channel on. Default `false`. |
| `SMTP_HOST` | yes | e.g. `smtp.gmail.com` |
| `SMTP_PORT` | no | Default `587`. |
| `SMTP_FROM` | yes | The sender address shown to recipients. |
| `SMTP_USER` | no* | Username for authenticated relays. |
| `SMTP_PASSWORD` | no* | Password / app password. |
| `SMTP_USE_TLS` | no | Default `true` (STARTTLS). |
| `SMTP_TIMEOUT_SECONDS` | no | Default `10`. |
| `FRONTEND_BASE_URL` | no | Used for links inside messages. Default `http://localhost:5173`. |

\* `SMTP_USER`/`SMTP_PASSWORD` are optional because an internal company relay
often accepts unauthenticated mail from inside the network. For Gmail they are
required.

### Gmail specifically

Gmail **will not accept your normal account password**. You must:

1. Enable 2-Step Verification on the Google account.
2. Generate a 16-character **App Password** at
   <https://myaccount.google.com/apppasswords>.
3. Use that as `SMTP_PASSWORD`.

```env
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USER=your.account@gmail.com
SMTP_PASSWORD=abcdefghijklmnop     # 16-char App Password, NOT your login password
SMTP_FROM=your.account@gmail.com
```

Gmail also enforces sending limits (roughly 500 messages/day for free accounts),
which is worth knowing before pointing a production deployment at it.

---

## 4. WhatsApp configuration

BIMS integrates with the **Meta WhatsApp Cloud API**. This requires an external
account that BIMS cannot create for you.

### What you must obtain from Meta

1. A **Meta Business account** and a WhatsApp Business App
   (<https://developers.facebook.com/>).
2. A **registered WhatsApp sender phone number**, which gives you a
   **Phone Number ID**.
3. A **permanent access token** (a system-user token — the temporary tokens in
   the dashboard expire in 24 hours).
4. An **approved message template**. This is not optional: the Cloud API only
   allows free-form text within a 24-hour window after a user messages you.
   Because BIMS notifications are business-initiated, they must use a template.

   Create a template with a single body parameter, for example:

   ```
   Name: bims_assignment
   Category: UTILITY
   Body: BIMS notification: {{1}}
   ```

   Templates require Meta approval before they can be used.

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `WHATSAPP_ENABLED` | yes | `true` to switch the channel on. Default `false`. |
| `WHATSAPP_PHONE_NUMBER_ID` | yes | From the Meta dashboard. |
| `WHATSAPP_ACCESS_TOKEN` | yes | Permanent system-user token. |
| `WHATSAPP_TEMPLATE_NAME` | yes | e.g. `bims_assignment` |
| `WHATSAPP_TEMPLATE_LANGUAGE` | no | Default `en`. |
| `WHATSAPP_API_URL` | no | Default `https://graph.facebook.com/v21.0`. |
| `WHATSAPP_TIMEOUT_SECONDS` | no | Default `10`. |

### Python dependency

WhatsApp sending uses `httpx`, imported lazily so it never becomes a hard
requirement:

```bash
pip install httpx
```

If `httpx` is missing while WhatsApp is enabled, BIMS logs a warning and skips
the send — it does not crash.

### Phone number format

Recipient numbers are taken from `users.phone` and normalised to digits only, as
the Cloud API requires (international format, no `+`, spaces or punctuation).
BIMS deliberately does **not** guess a country code: a number stored without one
will fail visibly upstream rather than being silently delivered to the wrong
recipient. Ensure technician phone numbers are stored in full international
form.

---

## 5. Verifying configuration

```bash
cd backend
python -c "
import os
os.environ.setdefault('DATABASE_URL','sqlite:///./dev.db')
os.environ.setdefault('SECRET_KEY','x')
from app.services import delivery_service
print('email configured :', delivery_service._email_configured())
print('whatsapp configured:', delivery_service._whatsapp_configured())
"
```

To test a real send end-to-end, enable the channel, then create a planning
assignment for a technician whose email/phone you control and watch the backend
log — successful sends log at INFO, failures at WARNING with the provider's own
error message.

---

## 6. Limitations

- **Delivery is synchronous and best-effort.** Sends happen inline during the
  assignment request. A slow SMTP server adds latency (bounded by
  `SMTP_TIMEOUT_SECONDS`); it never fails the request, but a production
  deployment with high volume would want a background queue instead.
- **No retry and no delivery receipts.** A failed send is logged and dropped;
  it is not retried, and there is no record in the database of whether an
  external copy was delivered. The in-app notification remains the durable one.
- **No per-user channel preferences.** If a channel is enabled, it applies to
  every assignment notification. There is no opt-out per technician.
- **WhatsApp requires template approval**, so message wording changes are
  constrained by what Meta has approved rather than being freely editable in
  BIMS.
- **Seeded demo phone numbers are Faker-generated** and are not real, valid
  international numbers — WhatsApp sends against the demo dataset will fail
  upstream by design.
