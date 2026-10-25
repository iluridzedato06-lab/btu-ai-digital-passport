"""Anchoring and revocation of passport versions on the PassportRegistry contract."""
import datetime as dt
import logging

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.audit.models import audit
from apps.core.hashing import to_bytes32
from apps.passports.models import PassportVersion

from .. import client
from ..models import AnchorTransaction, RevocationTransaction

log = logging.getLogger(__name__)


def _backoff(attempts: int) -> dt.timedelta:
    return dt.timedelta(seconds=min(15 * (2**attempts), 900))


def ensure_anchor_record(version: PassportVersion) -> AnchorTransaction:
    anchor = getattr(version, "anchor", None)
    if anchor:
        return anchor
    return AnchorTransaction.objects.create(
        version=version,
        chain_id=settings.CHAIN_ID,
        contract_address=client.contract_address() or "",
        payload={
            "passportIdHash": version.passport.passport_id_hash,
            "version": version.version_number,
            "pdfHash": "0x" + version.pdf_sha256,
            "codeHash": "0x" + version.verification.code_hash,
        },
    )


def _mark_anchored(version: PassportVersion, anchor: AnchorTransaction, receipt, web3):
    block = web3.eth.get_block(receipt["blockNumber"])
    ts = dt.datetime.fromtimestamp(block["timestamp"], tz=dt.timezone.utc)
    with transaction.atomic():
        anchor.status = AnchorTransaction.Status.CONFIRMED
        anchor.block_number = receipt["blockNumber"]
        anchor.block_timestamp = ts
        anchor.gas_used = receipt.get("gasUsed")
        anchor.last_error = ""
        anchor.save()
        version.status = PassportVersion.Status.ANCHORED
        version.issued_at = ts
        version.save(update_fields=["status", "issued_at", "updated_at"])
        passport = version.passport
        if version.version_number > passport.latest_version_number:
            passport.latest_version_number = version.version_number
            passport.save(update_fields=["latest_version_number", "updated_at"])
    audit("version.anchored", actor="system:worker", target=version,
          tx_hash=anchor.tx_hash, block=anchor.block_number, passport_id=version.passport.passport_id)
    try:
        from apps.accounts.emails import send_passport_updated

        send_passport_updated(version.passport.student.email, version.passport.passport_id, version.version_number)
    except Exception as exc:  # noqa: BLE001 - email is best effort
        log.info("Update email not sent: %s", exc)


def _reconcile_existing(version: PassportVersion, anchor: AnchorTransaction) -> bool:
    """If the chain already holds this version with our hash, mark it anchored."""
    rec = client.read_version(version.passport.passport_id_hash, version.version_number)
    if not rec.exists:
        return False
    if rec.pdf_hash.lower() != version.pdf_sha256.lower():
        anchor.status = AnchorTransaction.Status.FAILED
        anchor.last_error = "Chain already holds a different document for this version number"
        anchor.save()
        version.status = PassportVersion.Status.ANCHOR_FAILED
        version.save(update_fields=["status", "updated_at"])
        return True
    with transaction.atomic():
        anchor.status = AnchorTransaction.Status.CONFIRMED
        anchor.issuer_address = rec.issuer
        anchor.block_timestamp = dt.datetime.fromtimestamp(rec.issued_at, tz=dt.timezone.utc)
        anchor.save()
        version.status = PassportVersion.Status.ANCHORED
        version.issued_at = anchor.block_timestamp
        version.save(update_fields=["status", "issued_at", "updated_at"])
        p = version.passport
        if version.version_number > p.latest_version_number:
            p.latest_version_number = version.version_number
            p.save(update_fields=["latest_version_number", "updated_at"])
    return True


def anchor_version(version: PassportVersion) -> AnchorTransaction:
    anchor = ensure_anchor_record(version)
    if anchor.status == AnchorTransaction.Status.CONFIRMED:
        return anchor
    web3 = client.w3()
    try:
        if not anchor.contract_address:
            anchor.contract_address = client.contract_address() or ""
        # A previously sent transaction: look for its receipt first.
        if anchor.tx_hash and anchor.status == AnchorTransaction.Status.SENT:
            try:
                receipt = web3.eth.get_transaction_receipt(anchor.tx_hash)
            except Exception:  # noqa: BLE001 - not mined / dropped
                receipt = None
            if receipt is not None:
                if receipt["status"] == 1:
                    _mark_anchored(version, anchor, receipt, web3)
                    return anchor
            elif anchor.updated_at > timezone.now() - dt.timedelta(seconds=settings.CHAIN_RECEIPT_TIMEOUT):
                return anchor  # still waiting

        if _reconcile_existing(version, anchor):
            return anchor

        # Previous versions must be on chain first (contract enforces strict ordering).
        on_chain_latest, _ = client.read_latest(version.passport.passport_id_hash)
        if on_chain_latest != version.version_number - 1:
            raise RuntimeError(
                f"Chain is at v{on_chain_latest}; waiting for v{version.version_number - 1} before v{version.version_number}"
            )

        account = client.issuer_account()
        reg = client.registry(web3)
        fn = reg.functions.anchorVersion(
            to_bytes32(version.passport.passport_id_hash),
            version.version_number,
            to_bytes32(version.pdf_sha256),
            to_bytes32(version.verification.code_hash),
        )
        version.status = PassportVersion.Status.ANCHORING
        version.save(update_fields=["status", "updated_at"])
        tx_hash = client.send_transaction(web3, account, fn)
        anchor.tx_hash = tx_hash
        anchor.issuer_address = account.address
        anchor.status = AnchorTransaction.Status.SENT
        anchor.attempts += 1
        anchor.save()
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=settings.CHAIN_RECEIPT_TIMEOUT)
        if receipt["status"] != 1:
            raise RuntimeError("Anchoring transaction reverted")
        _mark_anchored(version, anchor, receipt, web3)
    except Exception as exc:  # noqa: BLE001
        log.warning("Anchoring %s failed: %s", version, exc)
        anchor.refresh_from_db()
        anchor.attempts = max(anchor.attempts, 1) if anchor.tx_hash else anchor.attempts + 1
        anchor.last_error = str(exc)[:2000]
        anchor.next_attempt_at = timezone.now() + _backoff(anchor.attempts)
        if anchor.status != AnchorTransaction.Status.SENT:
            anchor.status = AnchorTransaction.Status.PENDING_SEND
        if anchor.attempts >= settings.MAX_ANCHOR_ATTEMPTS:
            anchor.status = AnchorTransaction.Status.FAILED
            version.status = PassportVersion.Status.ANCHOR_FAILED
        else:
            version.status = PassportVersion.Status.RENDERED
        version.save(update_fields=["status", "updated_at"])
        anchor.save()
    return anchor


def process_anchor_queue(limit: int = 200, force: bool = False) -> int:
    """Anchor every rendered version, oldest first. Returns number anchored."""
    if not settings.CHAIN_ENABLED or not client.contract_address():
        return 0
    now = timezone.now()
    qs = (
        PassportVersion.objects.filter(
            status__in=[PassportVersion.Status.RENDERED, PassportVersion.Status.ANCHORING]
        )
        .select_related("passport", "verification")
        .order_by("passport_id", "version_number")
    )
    if not force:
        qs = qs.filter(Q(anchor__isnull=True) | Q(anchor__next_attempt_at__isnull=True) | Q(anchor__next_attempt_at__lte=now))
    done = 0
    blocked_passports = set()
    for version in qs[:limit]:
        if version.passport_id in blocked_passports:
            continue
        anchor = anchor_version(version)
        if anchor.status == AnchorTransaction.Status.CONFIRMED:
            done += 1
        else:
            blocked_passports.add(version.passport_id)
    return done


def revoke_version(version: PassportVersion, reason: str, actor: str) -> RevocationTransaction:
    rev = RevocationTransaction.objects.create(version=version, reason=reason)
    try:
        web3 = client.w3()
        fn = client.registry(web3).functions.revoke(
            to_bytes32(version.passport.passport_id_hash), version.version_number, reason[:200]
        )
        tx_hash = client.send_transaction(web3, client.issuer_account(), fn)
        rev.tx_hash = tx_hash
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=settings.CHAIN_RECEIPT_TIMEOUT)
        rev.status = "confirmed" if receipt["status"] == 1 else "reverted"
    except Exception as exc:  # noqa: BLE001
        rev.status = "failed"
        rev.last_error = str(exc)[:2000]
    rev.save()
    if rev.status == "confirmed":
        version.revoked_at = timezone.now()
        version.revoke_reason = reason
        version.revoked_by = actor
        version.save(update_fields=["revoked_at", "revoke_reason", "revoked_by", "updated_at"])
    return rev
