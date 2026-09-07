"""One-off diagnostic for the cPanel "Execute Python Script" box. Same
purpose as before (SPF was the first fix; this checks the next most likely
cause — whether outgoing mail is actually DKIM-signed by the server, which a
DNS TXT record existing does NOT by itself guarantee). Delete this file once
you're done diagnosing."""

import os
import smtplib
from email.message import EmailMessage

# Fill in your own personal email here before running, then delete this
# file once you're done diagnosing — it's a one-off, not meant to stay.
TEST_RECIPIENT = ""

print("=== Settings ===")
from config import get_settings

s = get_settings()
print(f"  smtp_host = {s.smtp_host!r}")
print(f"  smtp_port = {s.smtp_port!r}")
print(f"  smtp_user = {s.smtp_user!r}")
print(f"  smtp_from = {s.smtp_from!r}")

if not TEST_RECIPIENT:
    print()
    print("TEST_RECIPIENT is blank — edit this file to add your email, then re-run.")
    raise SystemExit(0)

print()
print(f"=== Sending to {TEST_RECIPIENT} ===")
with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=s.smtp_timeout_seconds) as smtp:
    smtp.set_debuglevel(1)
    if s.smtp_use_tls:
        smtp.starttls()
    if s.smtp_user and s.smtp_password:
        smtp.login(s.smtp_user, s.smtp_password)
    message = EmailMessage()
    message["Subject"] = "BIMS diagnostic test email v2"
    message["From"] = s.smtp_from
    message["To"] = TEST_RECIPIENT
    message.set_content(
        "If you received this, check View Original / Show Original in Gmail and look for the "
        "Authentication-Results header — it will show SPF/DKIM/DMARC pass or fail explicitly."
    )
    result = smtp.send_message(message)
    print(f"send_message result (empty dict = accepted for all recipients): {result!r}")

print()
print("SUCCESS: message handed off to the mail server.")
print("Next: check Gmail inbox AND spam. If it arrives, open it, click the three-dot menu,")
print("'Show original', and look at the Authentication-Results header near the top.")
print("Send that header's exact text back for diagnosis.")
