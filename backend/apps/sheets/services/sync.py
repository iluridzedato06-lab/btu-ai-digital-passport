"""Google Sheets (or local workbook) -> database -> passport versions -> chain -> sheet status.

The sync is idempotent: every run re-validates every row, compares with the database, issues
at most one new version per student, anchors pending versions, and writes the resulting status
back into the ``sys_*`` columns (only cells whose value actually changes are written).
"""
import datetime as dt
import logging
import re
from dataclasses import dataclass, field

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.audit.models import audit
from apps.passports.models import PassportVersion, SkillAward, SkillCatalog, StampType
from apps.passports.services.issuance import NothingToIssue, issue_version
from apps.students.models import Student

from .. import schema as S
from ..adapters.base import CellUpdate, SheetAdapter, SheetRow, get_adapter
from ..models import SyncRow, SyncRun

log = logging.getLogger(__name__)
NAME_RE = re.compile(r"^[^\W\d_]+(?:[ '\-][^\W\d_]+)*$", re.UNICODE)
EARLIEST = dt.date(2016, 9, 16)  # BTU founding date

REASON_PRIORITY = [
    PassportVersion.Reason.NEW_AWARDS,
    PassportVersion.Reason.AWARD_EDITED,
    PassportVersion.Reason.AWARD_WITHDRAWN,
]


@dataclass
class RowResult:
    row: SheetRow
    status: str
    message: str = ""
    extra: dict = field(default_factory=dict)


@dataclass
class Context:
    run: SyncRun
    results: list = field(default_factory=list)
    dirty: dict = field(default_factory=dict)  # student pk -> reason

    def mark_dirty(self, student, reason):
        current = self.dirty.get(student.pk)
        if current is None or REASON_PRIORITY.index(reason) < REASON_PRIORITY.index(current):
            self.dirty[student.pk] = reason

    def result(self, row, status, message="", **extra):
        self.results.append(RowResult(row, status, message, extra))
        if status == SyncRow.Status.ERROR:
            self.run.rows_errors += 1


def _business(row: SheetRow) -> dict:
    return {c: row.get(c) for c in S.TABS[row.tab]["business"]}


def _missing(row: SheetRow) -> str | None:
    for col in S.TABS[row.tab]["required"]:
        if not row.get(col):
            return col
    return None


def _duplicates(rows: list[SheetRow], key: str) -> set[str]:
    seen, dup = set(), set()
    for r in rows:
        k = r.get(key)
        if k in seen:
            dup.add(k)
        seen.add(k)
    return dup


def _parse_date(value: str) -> dt.date | None:
    try:
        d = dt.date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None
    if d < EARLIEST or d > timezone.localdate():
        return None
    return d


# --------------------------------------------------------------------------- catalog
def sync_catalog(rows: list[SheetRow], ctx: Context):
    dup = _duplicates(rows, "skill_code")
    for row in rows:
        code = row.get("skill_code").upper()
        if (col := _missing(row)) is not None:
            ctx.result(row, "ERROR", S.error("E001", field=col))
            continue
        if code in dup:
            ctx.result(row, "ERROR", S.error("E008", value=code))
            continue
        stamp = row.get("stamp_type").upper()
        if stamp not in StampType.values:
            ctx.result(row, "ERROR", S.error("E011"))
            continue
        active = row.get("active") == "" or S.is_truthy(row.get("active"))
        defaults = {
            "name_en": row.get("skill_name_en"),
            "name_ka": row.get("skill_name_ka"),
            "stamp_type": stamp,
            "description_en": row.get("description_en"),
            "description_ka": row.get("description_ka"),
            "default_earned_through": row.get("default_earned_through"),
            "is_active": active,
        }
        obj, created = SkillCatalog.objects.get_or_create(skill_code=code, defaults=defaults)
        if created:
            ctx.run.rows_created += 1
        elif any(getattr(obj, k) != v for k, v in defaults.items()):
            for k, v in defaults.items():
                setattr(obj, k, v)
            obj.save()
            ctx.run.rows_updated += 1
        ctx.result(row, "OK", "" if active else "Inactive: no new awards accepted")


# --------------------------------------------------------------------------- students
def sync_students(rows: list[SheetRow], ctx: Context):
    dup = _duplicates(rows, "student_number")
    domains = settings.ALLOWED_EMAIL_DOMAINS
    for row in rows:
        number = row.get("student_number")
        if (col := _missing(row)) is not None and col != "consent":
            ctx.result(row, "ERROR", S.error("E001", field=col))
            continue
        if number in dup:
            ctx.result(row, "ERROR", S.error("E008", value=number))
            continue
        email = row.get("btu_email").lower()
        if "@" not in email or email.rsplit("@", 1)[1] not in domains:
            ctx.result(row, "ERROR", S.error("E002", domains=", @".join(domains)))
            continue
        first, last = row.get("first_name_en"), row.get("last_name_en")
        if not NAME_RE.match(first) or not NAME_RE.match(last):
            ctx.result(row, "ERROR", S.error("E013"))
            continue
        clash = Student.objects.filter(email=email).exclude(student_number=number).first()
        if clash:
            ctx.result(row, "ERROR", S.error("E012", value=email))
            continue
        consent = S.is_truthy(row.get("consent"))
        student = Student.objects.filter(student_number=number).first()
        message, status = "", "OK"
        if student is None:
            student = Student(student_number=number, first_name=first, last_name=last)
            ctx.run.rows_created += 1
        else:
            if (student.first_name, student.last_name) != (first, last):
                if student.names_locked:
                    status, message = "ERROR", S.error("E009")
                else:
                    student.first_name, student.last_name = first, last
        student.first_name_ka = row.get("first_name_ka")
        student.last_name_ka = row.get("last_name_ka")
        student.email = email
        student.programme = row.get("programme")
        if consent and not student.consent_given_at:
            student.consent_given_at = timezone.now()
        elif not consent:
            student.consent_given_at = None
        student.save()
        if status == "OK" and not consent:
            status, message = "PENDING", "Consent is not YES - no passport will be issued"
        ctx.result(row, status, message, student=student)


# --------------------------------------------------------------------------- awards
def _request_withdrawal(award: SkillAward, ctx: Context, row: SheetRow | None, why: str):
    if award.withdraw_requested_at is None:
        award.withdraw_requested_at = timezone.now()
        award.save(update_fields=["withdraw_requested_at", "updated_at"])
        audit("award.withdraw_requested", actor="system:sync", target=award, award_id=award.award_id, why=why)
    sr, _ = SyncRow.objects.get_or_create(tab=S.AWARDS, row_key=award.award_id)
    sr.missing_runs = sr.missing_runs + 1 if row is None else sr.missing_runs
    sr.last_status = SyncRow.Status.WITHDRAW_PENDING
    sr.last_message = why
    sr.save()
    if settings.SYNC_AUTO_WITHDRAW and (row is not None or sr.missing_runs >= 2):
        withdraw_award(award, actor="system:sync", ctx=ctx)
        return "WITHDRAWN", "Withdrawn automatically"
    return "WITHDRAW_PENDING", why + " - awaiting approval in the admin dashboard"


def withdraw_award(award: SkillAward, *, actor: str, ctx: Context | None = None, issue_now: bool = False):
    award.withdrawn_at = timezone.now()
    award.save(update_fields=["withdrawn_at", "updated_at"])
    SyncRow.objects.filter(tab=S.AWARDS, row_key=award.award_id).update(
        last_status=SyncRow.Status.WITHDRAWN, last_message="Withdrawn")
    audit("award.withdrawn", actor=actor, target=award, award_id=award.award_id)
    if ctx is not None:
        ctx.mark_dirty(award.student, PassportVersion.Reason.AWARD_WITHDRAWN)
    elif issue_now and award.first_included_version_id:
        return issue_version(award.student, reason=PassportVersion.Reason.AWARD_WITHDRAWN, actor=actor)
    return None


def sync_awards(rows: list[SheetRow], ctx: Context):
    dup = _duplicates(rows, "award_id")
    seen: set[str] = set()
    students = {s.student_number: s for s in Student.objects.all()}
    skills = {s.skill_code: s for s in SkillCatalog.objects.all()}
    for row in rows:
        award_id = row.get("award_id")
        seen.add(award_id)
        existing = SkillAward.objects.filter(award_id=award_id).select_related("student", "skill").first()
        if not S.is_truthy(row.get("confirmed")):
            if existing and existing.withdrawn_at is None and existing.first_included_version_id:
                status, msg = _request_withdrawal(existing, ctx, row, "Unconfirmed after issuance")
                ctx.result(row, status, msg)
            elif existing and existing.withdrawn_at is None:
                existing.delete()  # never issued: simply drop it
                ctx.result(row, "PENDING", "Waiting for confirmation")
            else:
                ctx.result(row, "PENDING", "Waiting for confirmation")
            continue
        if (col := _missing(row)) is not None:
            ctx.result(row, "ERROR", S.error("E001", field=col))
            continue
        if award_id in dup:
            ctx.result(row, "ERROR", S.error("E008", value=award_id))
            continue
        if not row.get("confirmed_by"):
            ctx.result(row, "ERROR", S.error("E010"))
            continue
        student = students.get(row.get("student_number"))
        if student is None:
            ctx.result(row, "ERROR", S.error("E003", value=row.get("student_number")))
            continue
        if not student.consent_given_at:
            ctx.result(row, "ERROR", S.error("E004", value=student.student_number))
            continue
        skill = skills.get(row.get("skill_code").upper())
        if skill is None or not skill.is_active:
            ctx.result(row, "ERROR", S.error("E005", value=row.get("skill_code")))
            continue
        date = _parse_date(row.get("date_earned"))
        if date is None:
            ctx.result(row, "ERROR", S.error("E006"))
            continue
        other = (SkillAward.objects.filter(student=student, skill=skill, withdrawn_at__isnull=True)
                 .exclude(award_id=award_id).first())
        if other:
            ctx.result(row, "ERROR", S.error("E007", value=other.award_id))
            continue
        if existing and existing.student_id != student.pk:
            ctx.result(row, "ERROR", f"E008: {award_id} already belongs to student {existing.student.student_number}")
            continue

        fields = {"skill": skill, "earned_through": row.get("earned_through")[:160], "date_earned": date,
                  "confirmed_by": row.get("confirmed_by")[:160]}
        from apps.core.hashing import canonical_row_hash

        row_hash = canonical_row_hash(_business(row))
        if existing is None:
            SkillAward.objects.create(award_id=award_id, student=student, source_row_hash=row_hash, **fields)
            ctx.run.rows_created += 1
            ctx.mark_dirty(student, PassportVersion.Reason.NEW_AWARDS)
        else:
            changed = any(getattr(existing, k) != v for k, v in fields.items() if k != "confirmed_by")
            revived = existing.withdrawn_at is not None
            for k, v in fields.items():
                setattr(existing, k, v)
            existing.source_row_hash = row_hash
            existing.withdraw_requested_at = None
            if revived:
                existing.withdrawn_at = None
            existing.save()
            if revived:
                ctx.mark_dirty(student, PassportVersion.Reason.NEW_AWARDS)
            elif changed:
                ctx.run.rows_updated += 1
                reason = (PassportVersion.Reason.AWARD_EDITED if existing.first_included_version_id
                          else PassportVersion.Reason.NEW_AWARDS)
                ctx.mark_dirty(student, reason)
        ctx.result(row, "OK", "", award_id=award_id, row_hash=row_hash)

    # Awards that disappeared from the sheet
    for award in SkillAward.objects.filter(withdrawn_at__isnull=True).exclude(award_id__in=seen):
        if award.first_included_version_id:
            _request_withdrawal(award, ctx, None, "Row removed from the sheet")
        else:
            award.delete()


# --------------------------------------------------------------------------- issuance + write back
def issue_dirty(ctx: Context):
    for student in Student.objects.filter(pk__in=list(ctx.dirty)):
        reason = ctx.dirty[student.pk]
        try:
            version = issue_version(student, reason=reason, sync_run=ctx.run, actor="system:sync")
            ctx.run.versions_issued += 1
            ctx.run.log(f"Issued {version.passport.passport_id} v{version.version_number}", reason=reason)
        except NothingToIssue as exc:
            ctx.run.log(str(exc))
        except Exception as exc:  # noqa: BLE001
            log.exception("Issuance failed for %s", student)
            ctx.run.log(f"Issuance failed for {student.student_number}: {exc}", level="error")


def _award_status(award_id: str) -> tuple[str, str, str]:
    award = (SkillAward.objects.filter(award_id=award_id)
             .select_related("first_included_version", "student__passport").first())
    if award is None or award.first_included_version is None:
        return "QUEUED", "Accepted; passport version pending", ""
    v = award.first_included_version
    pid = award.student.passport.passport_id
    if v.status == PassportVersion.Status.ANCHORED:
        return "ISSUED", f"In {pid}; anchored on chain", f"v{v.version_number}"
    if v.status == PassportVersion.Status.ANCHOR_FAILED:
        return "QUEUED", f"In {pid}; chain anchoring failed - staff notified", f"v{v.version_number}"
    return "QUEUED", f"In {pid}; waiting for chain confirmation", f"v{v.version_number}"


def build_writeback(ctx: Context) -> list[CellUpdate]:
    updates: list[CellUpdate] = []
    now = timezone.localtime().strftime("%Y-%m-%d %H:%M")
    for res in ctx.results:
        row = res.row
        desired = {"sys_status": res.status, "sys_message": res.message[:300]}
        if row.tab == S.AWARDS:
            if res.status == "OK":
                st, msg, ver = _award_status(res.extra["award_id"])
                desired.update(sys_status=st, sys_message=msg, sys_passport_version=ver,
                               sys_row_hash=res.extra["row_hash"][:16])
        elif row.tab == S.STUDENTS:
            student = res.extra.get("student")
            pp = getattr(student, "passport", None) if student else None
            if student is not None:
                student = Student.objects.filter(pk=student.pk).select_related("passport").first()
                pp = getattr(student, "passport", None)
            desired["sys_passport_id"] = pp.passport_id if pp else ""
            if res.status == "OK":
                desired["sys_status"] = "REGISTERED" if pp else "OK"
                desired["sys_message"] = (f"Latest version v{pp.latest_version_number}" if pp
                                          else "No confirmed skills yet")
        changed = False
        for col, val in desired.items():
            if col not in S.TABS[row.tab]["system"]:
                continue
            if row.get(col) != str(val):
                updates.append(CellUpdate(row.tab, row.row_number, col, str(val)))
                changed = True
        if changed and "sys_synced_at" in S.TABS[row.tab]["system"]:
            updates.append(CellUpdate(row.tab, row.row_number, "sys_synced_at", now))
        _record_sync_row(row, desired.get("sys_status", res.status), desired.get("sys_message", ""), ctx.run)
    return updates


def _record_sync_row(row: SheetRow, status: str, message: str, run: SyncRun):
    key = row.get(S.TABS[row.tab]["key"]) or f"row-{row.row_number}"
    from apps.core.hashing import canonical_row_hash

    valid = {c for c, _ in SyncRow.Status.choices}
    SyncRow.objects.update_or_create(
        tab=row.tab, row_key=key[:64],
        defaults={"last_row_number": row.row_number, "last_hash": canonical_row_hash(_business(row)),
                  "last_status": status if status in valid else SyncRow.Status.OK,
                  "last_message": message[:300], "last_seen_run": run, "missing_runs": 0},
    )


def run_sync(adapter: SheetAdapter | None = None, *, triggered_by: str = "cli", run: SyncRun | None = None,
             anchor: bool = True, dry_run: bool = False) -> SyncRun:
    from apps.chain.services.anchor import process_anchor_queue

    if run is None:
        run = SyncRun.objects.create(adapter="?", triggered_by=triggered_by)
    run.status = SyncRun.Status.RUNNING
    run.started_at = timezone.now()
    run.save()
    try:
        adapter = adapter or get_adapter()
        run.adapter = adapter.name
        data = {tab: adapter.read_tab(tab) for tab in S.SYNC_ORDER}
        run.rows_seen = sum(len(v) for v in data.values())
        ctx = Context(run=run)
        with transaction.atomic():
            sync_catalog(data[S.CATALOG], ctx)
            sync_students(data[S.STUDENTS], ctx)
            sync_awards(data[S.AWARDS], ctx)
            if dry_run:
                transaction.set_rollback(True)
        if not dry_run:
            issue_dirty(ctx)
            if anchor:
                run.versions_anchored = process_anchor_queue()
            updates = build_writeback(ctx)
            adapter.write_cells(updates)
            run.log(f"Wrote {len(updates)} status cells back to {adapter.describe()}")
        run.status = SyncRun.Status.PARTIAL if run.rows_errors else SyncRun.Status.OK
    except Exception as exc:  # noqa: BLE001
        log.exception("Sync failed")
        run.status = SyncRun.Status.FAILED
        run.error = str(exc)[:4000]
    run.finished_at = timezone.now()
    run.save()
    audit("sync.run", actor=f"system:{triggered_by}" if ":" not in triggered_by else triggered_by, target=run,
          status=run.status, rows=run.rows_seen, errors=run.rows_errors, issued=run.versions_issued)
    return run
