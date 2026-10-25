import logging

from django.contrib.auth import login, logout
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings
from django.middleware.csrf import get_token
from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.accounts.emails import send_login_link
from apps.accounts.models import MagicLinkToken
from apps.accounts.roles import is_known_login, role_of, sync_user_for_email
from apps.audit.models import audit, client_ip
from apps.core.hashing import hash_ip
from apps.passports.models import PassportVersion
from apps.passports.services.snapshot import active_awards

from .serializers import public_awards, version_summary
from .throttles import EmailThrottle, IpThrottle, ScopedThrottle

log = logging.getLogger(__name__)
GENERIC = {"detail": "If this address belongs to a registered BTU student or staff member, a sign-in link is on its way."}


@api_view(["GET"])
@permission_classes([AllowAny])
def csrf(request):
    return Response({"csrfToken": get_token(request)})


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([IpThrottle, EmailThrottle])
def magic_link_request(request):
    email = str(request.data.get("email", "")).strip().lower()
    locale = request.data.get("locale") if request.data.get("locale") in ("en", "ka") else "ka"
    try:
        validate_email(email)
    except ValidationError:
        return Response({"error": "invalid_email", "detail": "Enter a valid email address."}, status=400)
    domain = email.rsplit("@", 1)[1]
    if domain not in settings.ALLOWED_EMAIL_DOMAINS:
        return Response({"error": "domain_not_allowed",
                         "detail": f"Use your university address (@{settings.ALLOWED_EMAIL_DOMAINS[0]})."}, status=400)
    if is_known_login(email):
        token = MagicLinkToken.issue(email, hash_ip(client_ip(request)))
        try:
            send_login_link(email, token, locale)
        except Exception:  # noqa: BLE001 - never reveal delivery problems to the requester
            log.exception("Could not send sign-in email")
        audit("auth.magic_link_requested", actor=f"email:{email}", request=request)
    return Response(GENERIC, status=status.HTTP_202_ACCEPTED)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ScopedThrottle])
def magic_link_consume(request):
    email = MagicLinkToken.consume(str(request.data.get("token", "")))
    if not email:
        return Response({"error": "invalid_token", "detail": "This sign-in link is invalid, expired or already used."},
                        status=400)
    user = sync_user_for_email(email)
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    request.session.cycle_key()
    audit("auth.login", actor=f"user:{email}", request=request)
    return Response({"email": email, "role": role_of(user)})


magic_link_consume.cls.throttle_scope = "auth_consume"


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    audit("auth.logout", request=request)
    logout(request)
    return Response({"ok": True})


@api_view(["GET"])
@permission_classes([AllowAny])
def me(request):
    user = request.user
    if not user.is_authenticated:
        return Response({"authenticated": False, "role": "anon"})
    data = {"authenticated": True, "email": user.email, "role": role_of(user), "student": None, "passport": None}
    student = getattr(user, "student", None)
    if student is not None:
        data["student"] = {
            "student_number": student.student_number,
            "first_name": student.first_name, "last_name": student.last_name,
            "first_name_ka": student.first_name_ka, "last_name_ka": student.last_name_ka,
            "programme": student.programme,
            "pending_stamps": public_awards({"awards": [
                {"skill_name": a.skill.name_en, "skill_name_ka": a.skill.name_ka, "stamp_type": a.skill.stamp_type,
                 "description": a.skill.description_en, "earned_through": a.earned_through,
                 "date_earned": a.date_earned.isoformat()}
                for a in active_awards(student).filter(first_included_version__isnull=True)]}),
        }
        passport = getattr(student, "passport", None)
        if passport is not None:
            versions = passport.versions.select_related("verification", "anchor").order_by("-version_number")
            latest = passport.latest_valid_version
            data["passport"] = {
                "passport_id": passport.passport_id,
                "first_issued_on": passport.first_issued_on.isoformat(),
                "holder": {"first_name": passport.holder_first_name, "last_name": passport.holder_last_name},
                "latest_valid_version": latest.version_number if latest else None,
                "stamps": public_awards(latest.snapshot) if latest else [],
                "versions": [{**version_summary(v), "is_latest_valid": bool(latest and v.pk == latest.pk)}
                             for v in versions],
            }
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_download(request, number: int):
    student = getattr(request.user, "student", None)
    if student is None or not hasattr(student, "passport"):
        raise Http404
    version = PassportVersion.objects.filter(passport=student.passport, version_number=number).first()
    if version is None:
        raise Http404
    audit("pdf.downloaded", request=request, target=version, by="student")
    resp = FileResponse(version.pdf_file.open("rb"), as_attachment=True, filename=version.download_filename,
                        content_type="application/pdf")
    resp["Cache-Control"] = "private, no-store"
    return resp
