import hashlib
import json

from eth_utils import keccak


def sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def keccak_hex(text: str) -> str:
    return "0x" + keccak(text=text).hex()


def to_bytes32(hex_str: str) -> bytes:
    h = hex_str[2:] if hex_str.startswith("0x") else hex_str
    b = bytes.fromhex(h)
    if len(b) != 32:
        raise ValueError("expected 32 bytes")
    return b


def canonical_row_hash(values: dict) -> str:
    """Stable hash of a sheet row's business columns."""
    cleaned = {k: ("" if v is None else str(v).strip()) for k, v in sorted(values.items())}
    payload = json.dumps(cleaned, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256_hex(payload)


def hash_ip(ip: str | None) -> str:
    if not ip:
        return ""
    from django.conf import settings

    return sha256_hex(f"{settings.SECRET_KEY}:{ip}")[:24]
