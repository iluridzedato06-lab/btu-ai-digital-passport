import io

import pikepdf
import pytest

from apps.passports.models import Passport, PassportVersion, SkillAward
from apps.passports.pdf.render import render_passport
from apps.sheets import schema as S
from apps.sheets.models import SyncRow
from apps.sheets.services.sync import run_sync
from apps.students.models import Student

pytestmark = pytest.mark.django_db


def statuses(adapter, tab):
    return {r.get(S.TABS[tab]["key"]): (r.get("sys_status"), r.get("sys_message")) for r in adapter.read_tab(tab)}


def test_sync_creates_one_passport_per_student(sheet, no_chain):
    adapter = sheet()
    run = run_sync(adapter, anchor=False)
    assert run.status == "ok", run.error
    assert Student.objects.count() == 2
    assert Passport.objects.count() == 1  # T-2 has no confirmed skill yet
    p = Passport.objects.get()
    assert p.passport_id.startswith("BTU-AI-")
    v = p.versions.get()
    assert len(v.snapshot["awards"]) == 2
    # write-back
    st = statuses(adapter, S.AWARDS)
    assert st["AW-1"][0] == "QUEUED"
    assert statuses(adapter, S.STUDENTS)["T-1"][0] == "REGISTERED"


def test_sync_is_idempotent(sheet, no_chain):
    adapter = sheet()
    run_sync(adapter, anchor=False)
    run_sync(adapter, anchor=False)
    assert PassportVersion.objects.count() == 1


def test_new_award_adds_version_and_keeps_identity(sheet, no_chain):
    adapter = sheet()
    run_sync(adapter, anchor=False)
    p = Passport.objects.get()
    first = (p.passport_id, p.first_issued_on, p.holder_first_name)
    adapter2 = sheet(awards=[*__import__("tests.conftest", fromlist=["AWARDS"]).AWARDS,
                             {"award_id": "AW-3", "student_number": "T-1", "skill_code": "DATA-AI",
                              "earned_through": "Course", "date_earned": "2026-06-01", "confirmed": "TRUE",
                              "confirmed_by": "Office"}])
    run_sync(adapter2, anchor=False)
    p.refresh_from_db()
    assert (p.passport_id, p.first_issued_on, p.holder_first_name) == first
    v2 = p.versions.order_by("-version_number").first()
    assert v2.version_number == 2
    assert [a["award_id"] for a in v2.snapshot["awards"]] == ["AW-1", "AW-2", "AW-3"]
    assert v2.verification.code != p.versions.get(version_number=1).verification.code


def test_validation_errors_are_reported(sheet, no_chain):
    bad = [
        {"award_id": "E-1", "student_number": "NOPE", "skill_code": "PROMPT-ENG", "earned_through": "x",
         "date_earned": "2026-01-01", "confirmed": "TRUE", "confirmed_by": "x"},
        {"award_id": "E-2", "student_number": "T-1", "skill_code": "UNKNOWN", "earned_through": "x",
         "date_earned": "2026-01-01", "confirmed": "TRUE", "confirmed_by": "x"},
        {"award_id": "E-3", "student_number": "T-1", "skill_code": "PROMPT-ENG", "earned_through": "x",
         "date_earned": "2999-01-01", "confirmed": "TRUE", "confirmed_by": "x"},
        {"award_id": "E-4", "student_number": "T-1", "skill_code": "PROMPT-ENG", "earned_through": "x",
         "date_earned": "2026-01-01", "confirmed": "TRUE", "confirmed_by": ""},
        {"award_id": "E-5", "student_number": "T-1", "skill_code": "AI-ETHICS", "earned_through": "x",
         "date_earned": "2026-01-01", "confirmed": "FALSE", "confirmed_by": ""},
    ]
    students = [{"student_number": "T-1", "first_name_en": "Ana", "last_name_en": "G", "btu_email": "a@gmail.com",
                 "consent": "YES"}]
    adapter = sheet(students=students, awards=bad)
    run = run_sync(adapter, anchor=False)
    assert run.status == "partial"
    st = statuses(adapter, S.AWARDS)
    assert statuses(adapter, S.STUDENTS)["T-1"][1].startswith("E002")
    assert st["E-1"][1].startswith("E003")
    assert st["E-2"][1].startswith("E003") or st["E-2"][1].startswith("E005")
    assert st["E-3"][1].startswith("E003") or st["E-3"][1].startswith("E006")
    assert st["E-5"][0] == "PENDING"
    assert PassportVersion.objects.count() == 0
    assert SyncRow.objects.filter(last_status="ERROR").exists()


def test_name_locked_after_issuance(sheet, no_chain):
    run_sync(sheet(), anchor=False)
    from tests.conftest import STUDENTS

    renamed = [dict(STUDENTS[0], first_name_en="Anna"), STUDENTS[1]]
    adapter = sheet(students=renamed)
    run_sync(adapter, anchor=False)
    assert statuses(adapter, S.STUDENTS)["T-1"][1].startswith("E009")
    assert Passport.objects.get().holder_first_name == "Ana"


def test_removed_row_requests_withdrawal(sheet, no_chain):
    from tests.conftest import AWARDS

    run_sync(sheet(), anchor=False)
    run_sync(sheet(awards=AWARDS[:1]), anchor=False)
    a = SkillAward.objects.get(award_id="AW-2")
    assert a.withdraw_requested_at is not None and a.withdrawn_at is None
    assert PassportVersion.objects.count() == 1  # no automatic change without approval
    from apps.sheets.services.sync import withdraw_award

    v = withdraw_award(a, actor="test", issue_now=True)
    assert v.version_number == 2 and len(v.snapshot["awards"]) == 1


def test_pdf_has_pages_metadata_and_is_deterministic(sheet, no_chain):
    run_sync(sheet(), anchor=False)
    v = PassportVersion.objects.get()
    pdf = v.pdf_file.read()
    with pikepdf.open(io.BytesIO(pdf)) as doc:
        assert len(doc.pages) == 4
        kw = str(doc.docinfo["/Keywords"])
        assert v.passport.passport_id in kw and v.verification.formatted in kw
    assert render_passport(v.snapshot) == pdf  # same snapshot -> same bytes
