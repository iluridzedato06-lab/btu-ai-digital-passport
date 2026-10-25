import re

from django.conf import settings
from django.db.models import Count, F
from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.audit.models import audit
from apps.chain import client
from apps.core.codes import normalize_code
from apps.core.models import Heartbeat
from apps.passports.models import Passport, PassportVersion, SkillAward, SkillCatalog, VerificationCode
from apps.passports.services.verify import published_issuer_info, verify_version

from .throttles import ScopedThrottle

SHA_RE = re.compile(r"^[0-9a-fA-F]{64}$")


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def health(request):
    hb = Heartbeat.objects.filter(name="worker").first()
    chain_ok = False
    try:
        chain_ok = client.w3().is_connected()
    except Exception:  # noqa: BLE001
        pass
    return Response({
        "status": "ok",
        "time": timezone.now().isoformat(),
        "worker_last_seen": hb.last_seen.isoformat() if hb else None,
        "chain_reachable": chain_ok,
        "contract": client.contract_address(),
        "sheets_adapter": settings.SHEETS_ADAPTER,
    })


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def issuer(request):
    resp = Response(published_issuer_info())
    resp["Cache-Control"] = "public, max-age=300"
    return resp


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def stats(request):
    return Response({
        "passports": Passport.objects.count(),
        "versions_anchored": PassportVersion.objects.filter(status=PassportVersion.Status.ANCHORED).count(),
        "stamps": SkillAward.objects.filter(withdrawn_at__isnull=True).count(),
        "skills_in_catalog": SkillCatalog.objects.filter(is_active=True).count(),
    })


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def catalog(request):
    rows = (SkillCatalog.objects.filter(is_active=True)
            .annotate(holders=Count("awards", distinct=True)).order_by("stamp_type", "name_en"))
    return Response([
        {"skill_code": s.skill_code, "name_en": s.name_en, "name_ka": s.name_ka, "stamp_type": s.stamp_type,
         "description_en": s.description_en, "description_ka": s.description_ka} for s in rows
    ])


def _lookup_response(request, version, how):
    if version is None:
        audit("verify.lookup", actor="anon", request=request, found=False, how=how)
        return Response({"status": "not_found"})
    VerificationCode.objects.filter(pk=version.verification.pk).update(
        lookup_count=F("lookup_count") + 1, last_lookup_at=timezone.now())
    data = verify_version(version)
    audit("verify.lookup", actor="anon", request=request, target=version, found=True, how=how, status=data["status"])
    return Response(data)


class VerifyThrottle(ScopedThrottle):
    pass


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([ScopedThrottle])
def verify_code(request, code):
    norm = normalize_code(code)
    version = None
    if norm:
        vc = (VerificationCode.objects.filter(code=norm)
              .select_related("version__passport", "version__anchor").first())
        version = vc.version if vc else None
    return _lookup_response(request, version, "code")


verify_code.cls.throttle_scope = "verify"


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([ScopedThrottle])
def verify_hash(request, sha256):
    version = None
    if SHA_RE.match(sha256):
        version = (PassportVersion.objects.filter(pdf_sha256=sha256.lower())
                   .select_related("passport", "verification").first())
    return _lookup_response(request, version, "hash")


verify_hash.cls.throttle_scope = "verify"
