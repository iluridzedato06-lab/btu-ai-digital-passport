"""Creates passports and new passport versions.

Order matters: the verification code and QR are generated first and printed into the PDF,
then the final PDF bytes are hashed, and only that hash is anchored on chain afterwards.
"""
import logging

from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.utils import timezone

from apps.audit.models import audit
from apps.chain import client as chain_client
from apps.core.codes import generate_code
from apps.core.hashing import keccak_hex, sha256_hex
from apps.passports.models import Passport, PassportVersion, SkillAward, VerificationCode, next_passport_id
from apps.passports.pdf.render import render_passport
from apps.passports.services.snapshot import active_awards, build_snapshot

log = logging.getLogger(__name__)


class NothingToIssue(Exception):
    pass


def get_or_create_passport(student) -> Passport:
    existing = Passport.objects.filter(student=student).first()
    if existing:
        return existing
    today = timezone.localdate()
    pid = next_passport_id(today.year)
    return Passport.objects.create(
        student=student,
        passport_id=pid,
        passport_id_hash=keccak_hex(pid),
        first_issued_on=today,
        holder_first_name=student.first_name,
        holder_last_name=student.last_name,
    )


def _unique_code() -> str:
    for _ in range(10):
        code = generate_code()
        if not VerificationCode.objects.filter(code=code).exists():
            return code
    raise RuntimeError("Could not allocate a unique verification code")


def _issuer_identity() -> tuple[str, str]:
    try:
        contract = chain_client.contract_address() or ""
    except Exception:  # noqa: BLE001
        contract = ""
    try:
        issuer = chain_client.issuer_account().address
    except Exception:  # noqa: BLE001
        issuer = ""
    return contract, issuer


@transaction.atomic
def issue_version(student, *, reason: str, actor: str = "system:worker", sync_run=None) -> PassportVersion:
    if not active_awards(student).exists() and not Passport.objects.filter(student=student).exists():
        raise NothingToIssue(f"{student} has no confirmed skills")
    passport = get_or_create_passport(student)
    passport = Passport.objects.select_for_update().get(pk=passport.pk)
    if passport.status != Passport.Status.ACTIVE:
        raise NothingToIssue(f"Passport {passport.passport_id} is suspended")

    n = (passport.versions.aggregate(m=Max("version_number"))["m"] or 0) + 1
    code = _unique_code()
    code_hash = sha256_hex(code)
    now = timezone.now()
    issued_at_unix = int(now.timestamp())
    contract, issuer_address = _issuer_identity()

    snapshot = build_snapshot(
        passport=passport, version_number=n, code=code, code_hash=code_hash,
        issued_on=timezone.localdate(), issued_at_unix=issued_at_unix,
        contract=contract, issuer_address=issuer_address, reason=reason,
    )
    signature = ""
    if contract and issuer_address:
        from apps.chain.signing import sign_version

        signature = sign_version(contract, passport.passport_id_hash, n, "0x" + code_hash, issued_at_unix)
    snapshot["issuer"]["signature"] = signature

    pdf_bytes = render_passport(snapshot)
    digest = sha256_hex(pdf_bytes)

    version = PassportVersion(
        passport=passport,
        version_number=n,
        trigger_reason=reason,
        snapshot=snapshot,
        pdf_sha256=digest,
        pdf_size=len(pdf_bytes),
        issuer_signature=signature,
        trigger_sync_run=sync_run,
    )
    version.pdf_file.save(version.download_filename, ContentFile(pdf_bytes), save=False)
    try:
        version.save()
    except IntegrityError:
        version.pdf_file.delete(save=False)
        raise
    VerificationCode.objects.create(version=version, code=code, code_hash=code_hash)
    award_ids = [a["award_id"] for a in snapshot["awards"]]
    SkillAward.objects.filter(award_id__in=award_ids, first_included_version__isnull=True).update(
        first_included_version=version
    )
    audit("version.issued", actor=actor, target=version, passport_id=passport.passport_id, version=n,
          reason=reason, awards=len(award_ids), pdf_sha256=digest)
    log.info("Issued %s v%s (%s awards)", passport.passport_id, n, len(award_ids))
    return version
