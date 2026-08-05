import bcrypt

# passlib's CryptContext is unmaintained and its bcrypt self-test breaks under
# bcrypt>=4.1 (module '__about__' removed) — using the bcrypt library directly
# avoids that incompatibility while still satisfying Ch.127 "Passwords are hashed".
_BCRYPT_MAX_BYTES = 72


def hash_password(plain_password: str) -> str:
    password_bytes = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    password_bytes = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))
