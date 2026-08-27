"""Task 4 — outbound delivery of notifications over external channels.

This is deliberately *not* a second notification system. The single source of
truth stays `notification_service` + the `notifications` table (Ch.46): every
notification is always written there first, and this module is a best-effort
fan-out of that same content to email and/or WhatsApp.

Two rules govern everything here:

1. **Never break the triggering action.** Assigning an intervention must
   succeed even if SMTP is down, credentials are wrong, or WhatsApp returns a
   500. Every send is wrapped so a failure is logged and swallowed — the
   in-app notification has already been committed by that point.
2. **Disabled by default.** Both channels are off unless explicitly enabled
   and configured via environment variables (see config.py / NOTIFICATIONS.md).
   No credential is ever hardcoded or defaulted to a real value.
"""

import logging
import smtplib
from email.message import EmailMessage

from config import get_settings

logger = logging.getLogger("bims.delivery")


def _email_configured() -> bool:
    s = get_settings()
    # smtp_user/smtp_password are intentionally NOT required: a local relay or
    # an internal company SMTP server often accepts unauthenticated mail from
    # inside the network. Host + sender are the true minimum.
    return bool(s.email_enabled and s.smtp_host and s.smtp_from)


def _whatsapp_configured() -> bool:
    s = get_settings()
    return bool(
        s.whatsapp_enabled
        and s.whatsapp_phone_number_id
        and s.whatsapp_access_token
        and s.whatsapp_template_name
    )


def send_email(to_address: str, subject: str, body: str) -> bool:
    """Best-effort plain-text email. Returns True only if actually sent.

    Returns False (without raising) when email isn't configured, the
    recipient has no address, or the SMTP conversation fails for any reason.
    """
    if not _email_configured():
        logger.debug("Email not configured — skipping send to %s", to_address)
        return False
    if not to_address:
        logger.debug("No recipient address — skipping email send")
        return False

    s = get_settings()
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = s.smtp_from
    message["To"] = to_address
    message.set_content(body)

    try:
        with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=s.smtp_timeout_seconds) as smtp:
            if s.smtp_use_tls:
                smtp.starttls()
            if s.smtp_user and s.smtp_password:
                smtp.login(s.smtp_user, s.smtp_password)
            smtp.send_message(message)
        logger.info("Notification email sent to %s", to_address)
        return True
    except Exception as exc:  # noqa: BLE001 — deliberately broad: see rule 1 above.
        # Never re-raise. Credentials, DNS, TLS, timeouts and remote 5xx all
        # land here, and none of them should fail the assignment that
        # triggered this notification.
        logger.warning("Email notification to %s failed (%s): %s", to_address, type(exc).__name__, exc)
        return False


def send_whatsapp(to_phone: str, body: str) -> bool:
    """Best-effort WhatsApp message via the Meta WhatsApp Cloud API.

    Returns False (without raising) when WhatsApp isn't configured, the
    recipient has no phone number, `httpx` isn't installed, or the API call
    fails for any reason.

    Note on message shape: the Cloud API only allows free-form text within a
    24-hour customer-service window. A business-initiated notification (which
    this always is) must use a pre-approved template, so this sends a
    `template` message with the notification text as a body parameter. The
    template itself must be created and approved in the Meta Business
    dashboard — see NOTIFICATIONS.md; it cannot be created from here.
    """
    if not _whatsapp_configured():
        logger.debug("WhatsApp not configured — skipping send to %s", to_phone)
        return False
    if not to_phone:
        logger.debug("No recipient phone number — skipping WhatsApp send")
        return False

    s = get_settings()

    try:
        # Imported lazily so the application runs (and this module imports)
        # even when httpx isn't installed — WhatsApp is an optional feature
        # and must not become a hard dependency of the whole backend.
        import httpx
    except ImportError:
        logger.warning("WhatsApp is enabled but `httpx` is not installed — skipping send. Run: pip install httpx")
        return False

    url = f"{s.whatsapp_api_url}/{s.whatsapp_phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": _normalise_phone(to_phone),
        "type": "template",
        "template": {
            "name": s.whatsapp_template_name,
            "language": {"code": s.whatsapp_template_language},
            "components": [{"type": "body", "parameters": [{"type": "text", "text": body}]}],
        },
    }

    try:
        response = httpx.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {s.whatsapp_access_token}"},
            timeout=s.whatsapp_timeout_seconds,
        )
        if response.status_code >= 400:
            # Body is logged (not the token) — Meta returns actionable errors
            # here, e.g. template not approved / number not registered.
            logger.warning("WhatsApp send to %s failed: HTTP %s %s", to_phone, response.status_code, response.text[:300])
            return False
        logger.info("WhatsApp notification sent to %s", to_phone)
        return True
    except Exception as exc:  # noqa: BLE001 — deliberately broad: see rule 1 above.
        logger.warning("WhatsApp notification to %s failed (%s): %s", to_phone, type(exc).__name__, exc)
        return False


def _normalise_phone(phone: str) -> str:
    """The Cloud API wants digits only, in international format, with no '+',
    spaces or punctuation. Seeded demo numbers come from Faker in assorted
    local formats, so this strips them down rather than assuming a shape.
    Any country-code prefixing is deliberately NOT guessed here — a number
    stored without one will simply fail upstream, which is visible in the log
    rather than silently delivered to the wrong recipient."""
    return "".join(ch for ch in phone if ch.isdigit())


def deliver_external(
    *, email_address: str | None, phone: str | None, subject: str, body: str
) -> dict[str, bool]:
    """Fan a single notification out to every configured external channel.

    Always returns a per-channel result map instead of raising, so callers
    (and tests) can see what actually happened without needing to care
    whether a channel is switched on.
    """
    return {
        "email": send_email(email_address or "", subject, body),
        "whatsapp": send_whatsapp(phone or "", body),
    }
