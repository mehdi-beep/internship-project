"""One-off diagnostic for the cPanel "Execute Python Script" box — checks
whether the SMTP environment variables actually reached this process, then
attempts one real send and prints the exact exception if it fails. Safe to
run repeatedly; sends exactly one test email per run to the address passed
as TEST_RECIPIENT below (edit before running), or does nothing destructive
if left blank."""

import os
import smtplib
from email.message import EmailMessage

# Fill in your own personal email here before running, then delete this
# file once you're done diagnosing — it's a one-off, not meant to stay.
TEST_RECIPIENT = ""

print("=== 1. What the process sees in os.environ ===")
for key in ["EMAIL_ENABLED", "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_FROM"]:
    value = os.environ.get(key)
    print(f"  {key} = {value!r}")
password = os.environ.get("SMTP_PASSWORD")
print(f"  SMTP_PASSWORD = {'<set, ' + str(len(password)) + ' chars>' if password else '<NOT SET>'}")

print()
print("=== 2. What config.get_settings() resolves to (same object the app itself uses) ===")
try:
    from config import get_settings

    s = get_settings()
    print(f"  email_enabled = {s.email_enabled!r}")
    print(f"  smtp_host = {s.smtp_host!r}")
    print(f"  smtp_port = {s.smtp_port!r}")
    print(f"  smtp_user = {s.smtp_user!r}")
    print(f"  smtp_from = {s.smtp_from!r}")
    print(f"  smtp_password set = {bool(s.smtp_password)}")
    print(f"  smtp_use_tls = {s.smtp_use_tls!r}")
except Exception as exc:
    print(f"  FAILED to load settings: {type(exc).__name__}: {exc}")
    raise SystemExit(1)

print()
print("=== 3. delivery_service._email_configured() ===")
from app.services import delivery_service

print(f"  _email_configured() = {delivery_service._email_configured()!r}")

if not TEST_RECIPIENT:
    print()
    print("TEST_RECIPIENT is blank — edit this file to add your email, then re-run to attempt a real send.")
    raise SystemExit(0)

print()
print(f"=== 4. Attempting one real send to {TEST_RECIPIENT} ===")
try:
    with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=s.smtp_timeout_seconds) as smtp:
        smtp.set_debuglevel(1)  # prints the full SMTP conversation
        if s.smtp_use_tls:
            smtp.starttls()
        if s.smtp_user and s.smtp_password:
            smtp.login(s.smtp_user, s.smtp_password)
        message = EmailMessage()
        message["Subject"] = "BIMS diagnostic test email"
        message["From"] = s.smtp_from
        message["To"] = TEST_RECIPIENT
        message.set_content("If you received this, SMTP sending works correctly from the live server.")
        smtp.send_message(message)
    print("SUCCESS: send_message() completed without raising.")
except Exception as exc:
    print(f"FAILED: {type(exc).__name__}: {exc}")
    raise
