"""Password hashing and verification helpers.

The seeded database stores a `DEV_PASSWORD_HASH:replace-on-first-login` placeholder
for demo users. `verify_password` accepts either:
  * a real bcrypt hash (used for newly registered users), or
  * the dev placeholder matching `DEV_PASSWORD_HASH:*` (when `allow_dev_password_placeholders` is true).

`hash_password` always produces a real bcrypt hash — never the placeholder.

Note: bcrypt limits passwords to 72 bytes. Longer passwords are silently truncated
here (industry-standard behavior); login uses the same truncation so verification
stays consistent.
"""
from __future__ import annotations

import re

import bcrypt

from app.config.settings import get_settings

DEV_PLACEHOLDER_RE = re.compile(r"^DEV_PASSWORD_HASH:(.+)$")
MAX_BCRYPT_BYTES = 72


def _truncate(plain: str) -> bytes:
    return plain.encode("utf-8")[:MAX_BCRYPT_BYTES]


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return bcrypt.hashpw(_truncate(plain_password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """Return True when the plaintext matches the stored hash.

    Handles two cases:
    1. Real bcrypt hash → use bcrypt.checkpw.
    2. DEV placeholder (`DEV_PASSWORD_HASH:<suffix>`) → only matches if the
       plaintext is exactly the placeholder suffix AND the settings flag
       `allow_dev_password_placeholders` is true. This is a dev-only escape
       hatch for the seeded demo users; remove or set to false in production.
    """
    settings = get_settings()

    match = DEV_PLACEHOLDER_RE.match(stored_hash)
    if match and settings.allow_dev_password_placeholders:
        return plain_password == match.group(1)

    try:
        return bcrypt.checkpw(_truncate(plain_password), stored_hash.encode("utf-8"))
    except ValueError:
        return False
