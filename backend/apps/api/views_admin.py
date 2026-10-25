from django.db.models import Count, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response

from apps.audit.models import AuditLog, actor_for, audit
from apps.chain.models import AnchorTransaction
from apps.chain.services.anchor import anchor_version, revoke_version
from apps.core.models import Heartbeat
from apps.passports.models import Passport, PassportVersion, SkillAward, SkillCatalog
from apps.passports.services.issuance import NothingToIssue, issue_version
from apps.passports.services.verify import published_issuer_info
from apps.sheets.models import SyncRow, SyncRun
from apps.sheets.services.sync import withdraw_award
from apps.students.models import Student

from .permissions import IsAdminRole, IsStaffRole
from .serializers import anchor_info, version_summary
from .throttles import ScopedThrottle


def _scoped(fn):
    fn.cls.throttle_scope = "admin_actions"
    return fn


def _run(r: SyncRun, full=False) -> dict:
    d = {
        "id": str(r.pk), "status": r.status, "adapter": r.adapter, "triggered_by": r.triggered_by,
        "created_at": r.created_at.isoformat(),
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        "rows_seen": r.rows_seen, "rows_created": r.rows_created, "rows_updated": r.rows_updated,
        "rows_errors": r.rows_errors, "versions_issued": r.versions_issued, "versions_anchored": r.versions_anchored,
        "error": r.error,
    }
    if full:
        d["events"] = r.events
    return d


def _student(s: Student) -> dict:
    p = getattr(s, "passport", None)
    return {
        "id": str(s.pk), "student_number": s.student_number, "first_name": s.first_name, "last_name": s.last_name,
        "first_name_ka": s.first_name_ka, "last_name_ka": s.last_name_ka, "email": s.email, "programme": s.programme,
        "consent": bool(s.consent_given_at),
        "passport_id": p.passport_id if p else None,
        "latest_version": p.latest_version_number if p else 0,
        "stamp_count": getattr(s, "stamp_count", None),
    }


@api_view(["GET"])
@permission_classes([IsStaffRole])
def overview(request):
    hb = Heartbeat.objects.filter(name="worker").first()
    last = SyncRun.objects.exclude(status=SyncRun.Status.REQUESTED).first()
    return Response({
        "students": Student.objects.count(),
        "passports": Passport.objects.count(),
        "versions_anchored": PassportVersion.objects.filter(status=PassportVersion.Status.ANCHORED).count(),
        "versions_pending": PassportVersion.objects.filter(
            status__in=[PassportVersion.Status.RENDERED, PassportVersion.Status.ANCHORING]).count(),
        "versions_failed": PassportVersion.objects.filter(status=PassportVersion.Status.ANCHOR_FAILED).count(),
        "stamps": SkillAward.objects.filter(withdrawn_at__isnull=True).count(),
        "sheet_errors": SyncRow.objects.filter(last_status=SyncRow.Status.ERROR).count(),
        "withdrawals_pending": SkillAward.objects.filter(withdraw_requested_at__isnull=False,
                                                         withdrawn_at__isnull=True).count(),
        "last_sync": _run(last) if last else None,
        "worker_last_seen": hb.last_seen.isoformat() if hb else None,
        "issuer": published_issuer_info(),
        "recent_audit": [_audit(a) for a in AuditLog.objects.all()[:12]],
    })


@api_view(["GET", "POST"])
@permission_classes([IsStaffRole])
@throttle_classes([ScopedThrottle])
def sync_runs(request):
    if request.method == "POST":
        pending = SyncRun.objects.filter(status__in=[SyncRun.Status.REQUESTED, SyncRun.Status.RUNNING]).first()
        if pending:
            return Response(_run(pending), status=202)
        run = SyncRun.objects.create(adapter="?", status=SyncRun.Status.REQUESTED, triggered_by=actor_for(request))
        audit("admin.sync_requested", request=request, target=run)
        return Response(_run(run), status=202)
    return Response([_run(r) for r in SyncRun.objects.all()[:50]])


_scoped(sync_runs)


@api_view(["GET"])
@permission_classes([IsStaffRole])
def sync_run_detail(request, pk):
    r = get_object_or_404(SyncRun, pk=pk)
    return Response(_run(r, full=True))


@api_view(["GET"])
@permission_classes([IsStaffRole])
def sheet_rows(request):
    qs = SyncRow.objects.all()
    status = request.GET.get("status")
    if status:
        qs = qs.filter(last_status=status)
    return Response([
        {"tab": r.tab, "row_key": r.row_key, "row_number": r.last_row_number, "status": r.last_status,
         "message": r.last_message, "updated_at": r.updated_at.isoformat()} for r in qs.order_by("tab", "last_row_number")[:500]
    ])


@api_view(["GET"])
@permission_classes([IsStaffRole])
def withdrawals(request):
    qs = SkillAward.objects.filter(withdraw_requested_at__isnull=False, withdrawn_at__isnull=True).select_related(
        "student", "skill", "first_included_version")
    return Response([
        {"award_id": a.award_id, "student_number": a.student.student_number,
         "student": f"{a.student.first_name} {a.student.last_name}", "skill": a.skill.name_en,
         "requested_at": a.withdraw_requested_at.isoformat(),
         "in_version": a.first_included_version.version_number if a.first_included_version else None}
        for a in qs
    ])


@api_view(["POST"])
@permission_classes([IsAdminRole])
@throttle_classes([ScopedThrottle])
def withdraw(request, award_id):
    award = get_object_or_404(SkillAward, award_id=award_id, withdrawn_at__isnull=True)
    version = withdraw_award(award, actor=actor_for(request), issue_now=True)
    return Response({"ok": True, "new_version": version.version_number if version else None})


_scoped(withdraw)


@api_view(["POST"])
@permission_classes([IsAdminRole])
@throttle_classes([ScopedThrottle])
def keep_award(request, award_id):
    award = get_object_or_404(SkillAward, award_id=award_id, withdrawn_at__isnull=True)
    award.withdraw_requested_at = None
    award.save(update_fields=["withdraw_requested_at", "updated_at"])
    audit("admin.withdrawal_dismissed", request=request, target=award, award_id=award_id)
    return Response({"ok": True})


_scoped(keep_award)


@api_view(["GET"])
@permission_classes([IsStaffRole])
def students(request):
    q = request.GET.get("q", "").strip()
    qs = Student.objects.select_related("passport").annotate(
        stamp_count=Count("awards", filter=Q(awards__withdrawn_at__isnull=True)))
    if q:
        qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q)
                       | Q(student_number__icontains=q) | Q(passport__passport_id__icontains=q)
                       | Q(first_name_ka__icontains=q) | Q(last_name_ka__icontains=q))
    return Response([_student(s) for s in qs.order_by("last_name")[:300]])


@api_view(["GET"])
@permission_classes([IsStaffRole])
def student_detail(request, pk):
    s = get_object_or_404(Student.objects.select_related("passport"), pk=pk)
    data = _student(s)
    data["awards"] = [
        {"award_id": a.award_id, "skill": a.skill.name_en, "stamp_type": a.skill.stamp_type,
         "earned_through": a.earned_through, "date_earned": a.date_earned.isoformat(), "confirmed_by": a.confirmed_by,
         "withdrawn_at": a.withdrawn_at.isoformat() if a.withdrawn_at else None,
         "withdraw_requested": bool(a.withdraw_requested_at),
         "first_version": a.first_included_version.version_number if a.first_included_version else None}
        for a in s.awards.select_related("skill", "first_included_version").order_by("date_earned")
    ]
    p = getattr(s, "passport", None)
    data["versions"] = []
    if p:
        latest = p.latest_valid_version
        data["first_issued_on"] = p.first_issued_on.isoformat()
        data["versions"] = [{**version_summary(v), "is_latest_valid": bool(latest and latest.pk == v.pk)}
                            for v in p.versions.select_related("verification", "anchor")]
    return Response(data)


@api_view(["POST"])
@permission_classes([IsStaffRole])
@throttle_classes([ScopedThrottle])
def reissue(request, pk):
    s = get_object_or_404(Student, pk=pk)
    try:
        v = issue_version(s, reason=PassportVersion.Reason.REISSUE, actor=actor_for(request))
    except NothingToIssue as exc:
        return Response({"error": "nothing_to_issue", "detail": str(exc)}, status=400)
    anchor_version(v)
    v.refresh_from_db()
    return Response(version_summary(v), status=201)


_scoped(reissue)


@api_view(["GET"])
@permission_classes([IsStaffRole])
def version_detail(request, pk):
    v = get_object_or_404(PassportVersion.objects.select_related("passport__student", "verification"), pk=pk)
    data = version_summary(v)
    data.update({
        "passport_id": v.passport.passport_id,
        "student_id": str(v.passport.student_id),
        "holder": v.snapshot.get("holder"),
        "snapshot": v.snapshot,
        "issuer_signature": v.issuer_signature,
        "revoked_by": v.revoked_by,
        "is_latest_valid": v.is_latest_valid,
        "revocations": [{"tx_hash": r.tx_hash, "status": r.status, "reason": r.reason, "error": r.last_error,
                         "created_at": r.created_at.isoformat()} for r in v.revocations.all()],
    })
    return Response(data)


@api_view(["GET"])
@permission_classes([IsStaffRole])
def version_download(request, pk):
    v = get_object_or_404(PassportVersion, pk=pk)
    if not v.pdf_file:
        raise Http404
    audit("pdf.downloaded", request=request, target=v, by="staff")
    resp = FileResponse(v.pdf_file.open("rb"), as_attachment=True, filename=v.download_filename,
                        content_type="application/pdf")
    resp["Cache-Control"] = "private, no-store"
    return resp


@api_view(["POST"])
@permission_classes([IsAdminRole])
@throttle_classes([ScopedThrottle])
def reanchor(request, pk):
    v = get_object_or_404(PassportVersion, pk=pk)
    if v.status == PassportVersion.Status.ANCHORED:
        return Response({"error": "already_anchored", "detail": "This version is already anchored."}, status=400)
    anchor = getattr(v, "anchor", None)
    if anchor:
        anchor.attempts = 0
        anchor.next_attempt_at = None
        if anchor.status == AnchorTransaction.Status.FAILED:
            anchor.status = AnchorTransaction.Status.PENDING_SEND
        anchor.save()
    v.status = PassportVersion.Status.RENDERED
    v.save(update_fields=["status", "updated_at"])
    audit("admin.reanchor", request=request, target=v)
    anchor_version(v)
    v.refresh_from_db()
    return Response({"status": v.status, "anchor": anchor_info(v)})


_scoped(reanchor)


@api_view(["POST"])
@permission_classes([IsAdminRole])
@throttle_classes([ScopedThrottle])
def revoke(request, pk):
    v = get_object_or_404(PassportVersion, pk=pk)
    reason = str(request.data.get("reason", "")).strip()
    if len(reason) < 5:
        return Response({"error": "reason_required", "detail": "Give a reason of at least 5 characters."}, status=400)
    if v.revoked_at:
        return Response({"error": "already_revoked", "detail": "Already revoked."}, status=400)
    if v.status != PassportVersion.Status.ANCHORED:
        return Response({"error": "not_anchored", "detail": "Only anchored versions can be revoked."}, status=400)
    rev = revoke_version(v, reason, actor_for(request))
    audit("version.revoked", request=request, target=v, reason=reason, tx_hash=rev.tx_hash, status=rev.status)
    if rev.status != "confirmed":
        return Response({"error": "chain_error", "detail": rev.last_error or "Revocation transaction failed"},
                        status=502)
    return Response({"ok": True, "tx_hash": rev.tx_hash})


_scoped(revoke)


def _audit(a: AuditLog) -> dict:
    return {"id": str(a.pk), "created_at": a.created_at.isoformat(), "actor": a.actor, "action": a.action,
            "target_type": a.target_type, "target_id": a.target_id, "metadata": a.metadata}


@api_view(["GET"])
@permission_classes([IsStaffRole])
def audit_log(request):
    qs = AuditLog.objects.all()
    if action := request.GET.get("action"):
        qs = qs.filter(action__startswith=action)
    if actor := request.GET.get("actor"):
        qs = qs.filter(actor__icontains=actor)
    return Response([_audit(a) for a in qs[:300]])


@api_view(["GET"])
@permission_classes([IsStaffRole])
def admin_catalog(request):
    rows = SkillCatalog.objects.annotate(holders=Count("awards", filter=Q(awards__withdrawn_at__isnull=True)))
    return Response([
        {"skill_code": s.skill_code, "name_en": s.name_en, "name_ka": s.name_ka, "stamp_type": s.stamp_type,
         "description_en": s.description_en, "default_earned_through": s.default_earned_through,
         "is_active": s.is_active, "holders": s.holders} for s in rows.order_by("stamp_type", "name_en")
    ])
