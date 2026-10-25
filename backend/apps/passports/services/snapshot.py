"""Builds the frozen, self-contained render input for one passport version."""
import datetime as dt

from django.conf import settings

from apps.core.codes import format_code
from apps.passports.models import STAMP_LABELS, Passport, SkillAward

SNAPSHOT_SCHEMA = 1


def award_entry(a: SkillAward) -> dict:
    return {
        "award_id": a.award_id,
        "skill_code": a.skill.skill_code,
        "skill_name": a.skill.name_en,
        "skill_name_ka": a.skill.name_ka,
        "stamp_type": a.skill.stamp_type,
        "stamp_title": STAMP_LABELS[a.skill.stamp_type]["title"],
        "stamp_subtitle": STAMP_LABELS[a.skill.stamp_type]["subtitle"],
        "description": a.skill.description_en,
        "earned_through": a.earned_through,
        "date_earned": a.date_earned.isoformat(),
    }


def active_awards(student):
    return (
        SkillAward.objects.filter(student=student, withdrawn_at__isnull=True)
        .select_related("skill")
        .order_by("date_earned", "skill__name_en", "award_id")
    )


def build_snapshot(*, passport: Passport, version_number: int, code: str, code_hash: str, issued_on: dt.date,
                   issued_at_unix: int, contract: str, issuer_address: str, reason: str) -> dict:
    formatted = format_code(code)
    return {
        "schema": SNAPSHOT_SCHEMA,
        "passport_id": passport.passport_id,
        "passport_id_hash": passport.passport_id_hash,
        "version": version_number,
        "first_issued_on": passport.first_issued_on.isoformat(),
        "version_issued_on": issued_on.isoformat(),
        "issued_at_unix": issued_at_unix,
        "trigger_reason": reason,
        "holder": {"first_name": passport.holder_first_name, "last_name": passport.holder_last_name},
        "verification": {
            "code": formatted,
            "code_hash": code_hash,
            "url": f"{settings.PUBLIC_BASE_URL}/{settings.VERIFY_LOCALE_IN_QR}/verify/{formatted}",
            "verify_page": f"{settings.PUBLIC_BASE_URL}/{settings.VERIFY_LOCALE_IN_QR}/verify",
        },
        "awards": [award_entry(a) for a in active_awards(passport.student)],
        "issuer": {
            "name": settings.ISSUER_NAME,
            "website": settings.ISSUER_WEBSITE,
            "address": issuer_address,
            "contract": contract,
            "chain_id": settings.CHAIN_ID,
            "chain_name": settings.CHAIN_NAME,
        },
    }
