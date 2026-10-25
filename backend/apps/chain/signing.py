"""EIP-712 issuer signature embedded in each passport PDF.

It signs identifiers (not the PDF bytes), so it can be printed inside the document before the
document hash is computed. Anyone can recover the signer and compare it with the issuer
address published at /.well-known/btu-issuer.json.
"""
from django.conf import settings
from eth_account import Account
from eth_account.messages import encode_typed_data

from apps.core.hashing import to_bytes32

TYPES = {
    "PassportVersion": [
        {"name": "passportIdHash", "type": "bytes32"},
        {"name": "version", "type": "uint32"},
        {"name": "codeHash", "type": "bytes32"},
        {"name": "issuedAt", "type": "uint64"},
    ]
}


def domain(contract: str) -> dict:
    return {
        "name": "BTU AI Skills Digital Passport",
        "version": "1",
        "chainId": settings.CHAIN_ID,
        "verifyingContract": contract,
    }


def _message(passport_id_hash: str, version: int, code_hash: str, issued_at: int) -> dict:
    return {
        "passportIdHash": to_bytes32(passport_id_hash),
        "version": version,
        "codeHash": to_bytes32(code_hash),
        "issuedAt": issued_at,
    }


def sign_version(contract: str, passport_id_hash: str, version: int, code_hash: str, issued_at: int) -> str:
    from .client import issuer_account

    msg = encode_typed_data(domain(contract), TYPES, _message(passport_id_hash, version, code_hash, issued_at))
    signed = issuer_account().sign_message(msg)
    return "0x" + signed.signature.hex().removeprefix("0x")


def recover_signer(contract: str, passport_id_hash: str, version: int, code_hash: str, issued_at: int,
                   signature: str) -> str:
    msg = encode_typed_data(domain(contract), TYPES, _message(passport_id_hash, version, code_hash, issued_at))
    return Account.recover_message(msg, signature=signature)
