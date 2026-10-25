"""Human-enterable verification codes.

12 characters of Crockford Base32 (60 bits of entropy), displayed as XXXX-XXXX-XXXX.
The alphabet omits I, L, O and U so codes survive being read aloud or re-typed.
"""
import re
import secrets

ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
CODE_LENGTH = 12
_VALID = re.compile(rf"^[{ALPHABET}]{{{CODE_LENGTH}}}$")
_CONFUSABLE = str.maketrans({"I": "1", "L": "1", "O": "0"})


def generate_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))


def normalize_code(raw: str | None) -> str | None:
    """Return the canonical code, or None when the input cannot be a valid code."""
    if not raw:
        return None
    s = re.sub(r"[\s\-_.]", "", str(raw)).upper().translate(_CONFUSABLE)
    return s if _VALID.match(s) else None


def format_code(code: str) -> str:
    return "-".join(code[i : i + 4] for i in range(0, len(code), 4))
