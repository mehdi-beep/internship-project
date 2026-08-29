"""Task 8 — self-service password reset with email verification.

Two-step flow, both endpoints acting only on the CURRENT logged-in user
(never a user id supplied by the caller, so this can never be used to reset
someone else's password):

1. `request_reset` — generates a 6-digit code, stores only its bcrypt hash
   (never the raw code), emails it to the user's own on-file address via the
   existing Task 4 delivery_service (no second email system). If email isn't
   configured, this refuses loudly (a clear error the frontend surfaces
   directly) rather than silently pretending to send something that will
   never arrive — the one deliberate difference from delivery_service's own
   "always best-effort, never fail the caller" stance elsewhere in the app,
   justified because a password reset that appears to succeed but never
   delivers a code would leave a user unable to get back into their account
   with no indication why.
2. `confirm_reset` — checks the submitted code against the stored hash, its
   expiry, and that it hasn't already been used, then updates the password
   and marks the code used. A code is single-use even if still within its
   expiry window.
"""

import random
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.authentication.password import hash_password, verify_password
from app.models.password_reset_code import PasswordResetCode
from app.models.user import User
from app.repositories import user_repository
from app.services import delivery_service
from config import get_settings

_CODE_LENGTH = 6
_CODE_TTL_MINUTES = 10


def is_email_reset_available() -> bool:
    """Surfaced to the frontend (GET /auth/password-reset/availability) so
    the Profile page can show an honest, specific message instead of a
    generic failure when email isn't configured yet — see module docstring."""
    settings = get_settings()
    return bool(settings.email_enabled and settings.smtp_host and settings.smtp_from)


def request_reset(db: Session, user: User) -> None:
    if not is_email_reset_available():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Password reset by email isn't set up yet. Ask an Administrator to reset your password instead.",
        )
    if not user.email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Your account has no email address on file. Ask an Administrator to reset your password instead.",
        )

    code = f"{random.randint(0, 10**_CODE_LENGTH - 1):0{_CODE_LENGTH}d}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=_CODE_TTL_MINUTES)
    db.add(PasswordResetCode(user_id=user.id, code_hash=hash_password(code), expires_at=expires_at))
    db.commit()

    sent = delivery_service.send_email(
        to_address=user.email,
        subject="BIMS — Password reset code",
        body=(
            f"Hello {user.first_name},\n\n"
            f"Your password reset code is: {code}\n\n"
            f"This code expires in {_CODE_TTL_MINUTES} minutes and can only be used once.\n"
            "If you didn't request this, you can ignore this email — your password will not change."
        ),
    )
    if not sent:
        # The code row above is already committed — deliberately left in
        # place rather than rolled back. It simply expires unused like any
        # other code nobody confirms; there's no reason to fail differently
        # here than any other transient send failure would, and rolling back
        # would require a second commit boundary for no real benefit.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not send the reset code email. Please try again shortly, or ask an Administrator to reset your password instead.",
        )


def confirm_reset(db: Session, user: User, code: str, new_password: str) -> None:
    now = datetime.now(timezone.utc)
    # Most-recent-first: if a user requests a new code without confirming an
    # older one, only the latest is meant to be usable — but every
    # still-valid (unused, unexpired) row is checked in order rather than
    # just the newest, so requesting a second code doesn't strand someone
    # who's already reading an earlier email.
    candidates = (
        db.query(PasswordResetCode)
        .filter(PasswordResetCode.user_id == user.id, PasswordResetCode.used_at.is_(None))
        .order_by(PasswordResetCode.created_at.desc())
        .all()
    )
    match = next((c for c in candidates if c.expires_at > now and verify_password(code, c.code_hash)), None)
    if match is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="That code is invalid or has expired.")

    match.used_at = now
    user_repository.set_password(db, user, hash_password(new_password))
