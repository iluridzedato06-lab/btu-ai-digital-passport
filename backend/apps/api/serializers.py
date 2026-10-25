"""Plain-dict serialisers (explicit field lists so nothing private leaks)."""
from apps.chain.client import explorer_tx_url
from apps.passports.models import PassportVersion


def anchor_info(version: PassportVersion) -> dict | None:
    a = getattr(version, "anchor", None)
    if a is None:
        return None
    return {
        "status": a.status,
        "chain_id": a.chain_id,
        "contract": a.contract_address,
        "tx_hash": a.tx_hash,
        "block_number": a.block_number,
        "block_timestamp": a.block_timestamp.isoformat() if a.block_timestamp else None,
        "issuer_address": a.issuer_address,
        "explorer_url": explorer_tx_url(a.tx_hash),
        "attempts": a.attempts,
        "last_error": a.last_error,
    }


def version_summary(v: PassportVersion, *, include_code: bool = True) -> dict:
    data = {
        "id": str(v.pk),
        "version_number": v.version_number,
        "status": v.status,
        "trigger_reason": v.trigger_reason,
        "created_at": v.created_at.isoformat(),
        "issued_at": v.issued_at.isoformat() if v.issued_at else None,
        "pdf_sha256": v.pdf_sha256,
        "pdf_size": v.pdf_size,
        "revoked_at": v.revoked_at.isoformat() if v.revoked_at else None,
        "revoke_reason": v.revoke_reason,
        "award_count": len(v.snapshot.get("awards", [])),
        "anchor": anchor_info(v),
    }
    if include_code and hasattr(v, "verification"):
        data["verification_code"] = v.verification.formatted
        data["verify_url"] = v.verification.verify_url
    return data


def public_awards(snapshot: dict) -> list[dict]:
    return [
        {
            "skill_name": a["skill_name"],
            "skill_name_ka": a.get("skill_name_ka", ""),
            "stamp_type": a["stamp_type"],
            "description": a["description"],
            "earned_through": a["earned_through"],
            "date_earned": a["date_earned"],
        }
        for a in snapshot.get("awards", [])
    ]
