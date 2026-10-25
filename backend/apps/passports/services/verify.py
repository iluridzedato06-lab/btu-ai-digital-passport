"""Public verification: document authenticity + issuer authenticity, checked against the chain."""
import logging

from django.conf import settings

from apps.api.serializers import public_awards
from apps.chain import client
from apps.chain.models import ChainDeployment
from apps.passports.models import PassportVersion

log = logging.getLogger(__name__)


def published_issuer_info() -> dict:
    deployments = list(ChainDeployment.objects.filter(chain_id=settings.CHAIN_ID).order_by("created_at"))
    current = client.contract_address()
    dep = next((d for d in deployments if current and d.contract_address.lower() == current.lower()), None)
    issuers = []
    seen = set()
    for d in deployments:
        if current and d.contract_address.lower() != current.lower():
            continue
        if d.issuer_address.lower() in seen:
            continue
        seen.add(d.issuer_address.lower())
        issuers.append({"address": d.issuer_address, "valid_from": d.created_at.date().isoformat(), "valid_to": None})
    return {
        "issuer": settings.ISSUER_NAME,
        "issuer_ka": settings.ISSUER_NAME_KA,
        "website": settings.ISSUER_WEBSITE,
        "domain": "btu.edu.ge",
        "chain_id": settings.CHAIN_ID,
        "chain_name": settings.CHAIN_NAME,
        "contract_address": current,
        "contract_explorer_url": client.explorer_address_url(current),
        "owner_address": dep.owner_address if dep else None,
        "issuer_addresses": issuers,
        "deploy_tx": dep.tx_hash if dep else None,
        "verify_url": f"{settings.PUBLIC_BASE_URL}/en/verify",
        "well_known_url": f"{settings.PUBLIC_BASE_URL}/.well-known/btu-issuer.json",
        "eip712_domain": {"name": "BTU AI Skills Digital Passport", "version": "1", "chainId": settings.CHAIN_ID,
                          "verifyingContract": current},
        "hash_algorithm": "sha256 over the exact PDF bytes",
    }


def verify_version(version: PassportVersion) -> dict:
    passport = version.passport
    latest_valid = passport.latest_valid_version
    snapshot = version.snapshot
    result = {
        "passport_id": passport.passport_id,
        "holder": snapshot["holder"],
        "version": version.version_number,
        "latest_version": passport.latest_version_number,
        "latest_valid_version": latest_valid.version_number if latest_valid else None,
        "first_issued_on": passport.first_issued_on.isoformat(),
        "version_issued_on": snapshot.get("version_issued_on"),
        "issued_at": version.issued_at.isoformat() if version.issued_at else None,
        "verification_code": version.verification.formatted,
        "pdf_sha256": version.pdf_sha256,
        "stamps": public_awards(snapshot),
        "revocation": None,
        "checks": {},
        "chain": None,
    }
    if version.revoked_at:
        result["revocation"] = {"revoked_at": version.revoked_at.isoformat(), "reason": version.revoke_reason}

    if version.status != PassportVersion.Status.ANCHORED:
        result["status"] = "pending"
        return result

    anchor = getattr(version, "anchor", None)
    chain = {
        "chain_id": settings.CHAIN_ID,
        "chain_name": settings.CHAIN_NAME,
        "contract": anchor.contract_address if anchor else client.contract_address(),
        "tx_hash": anchor.tx_hash if anchor else None,
        "block_number": anchor.block_number if anchor else None,
        "explorer_url": client.explorer_tx_url(anchor.tx_hash if anchor else None),
        "reachable": False,
    }
    result["chain"] = chain
    try:
        rec = client.read_version(passport.passport_id_hash, version.version_number)
        chain_latest, _ = client.read_latest(passport.passport_id_hash)
        chain["reachable"] = True
        chain["issuer_address"] = rec.issuer
        chain["anchored_at"] = rec.issued_at
        chain["latest_version_on_chain"] = chain_latest
        published = {i["address"].lower() for i in published_issuer_info()["issuer_addresses"]}
        checks = {
            "record_on_chain": rec.exists,
            "document_hash_matches": rec.exists and rec.pdf_hash.lower() == version.pdf_sha256.lower(),
            "code_hash_matches": rec.exists and rec.code_hash.lower() == version.verification.code_hash.lower(),
            "issuer_authorised_by_contract": rec.exists and client.is_issuer(rec.issuer),
            "issuer_published_by_btu": rec.exists and rec.issuer.lower() in published,
            "not_revoked_on_chain": rec.exists and rec.revoked_at == 0,
            "chain_consistent": chain_latest == passport.latest_version_number,
        }
        if rec.revoked_at and not result["revocation"]:
            result["revocation"] = {"revoked_at": None, "reason": "Revoked on chain"}
    except Exception as exc:  # noqa: BLE001
        log.warning("Chain read failed: %s", exc)
        result["status"] = "chain_unavailable"
        return result

    result["checks"] = checks
    document_ok = checks["record_on_chain"] and checks["document_hash_matches"] and checks["code_hash_matches"]
    issuer_ok = checks["issuer_authorised_by_contract"] and checks["issuer_published_by_btu"]
    result["document_authentic"] = document_ok
    result["issuer_authentic"] = issuer_ok
    if result["revocation"] or not checks["not_revoked_on_chain"]:
        result["status"] = "revoked"
    elif not (document_ok and issuer_ok):
        result["status"] = "invalid"
    elif latest_valid and latest_valid.version_number > version.version_number:
        result["status"] = "valid_superseded"
    else:
        result["status"] = "valid_latest"
    return result
