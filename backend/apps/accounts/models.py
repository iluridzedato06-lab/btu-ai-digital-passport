import datetime as dt
import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.hashing import sha256_hex
from apps.core.models import BaseModel


class MagicLinkToken(BaseModel):
    email = models.EmailField(db_index=True)
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    requested_ip_hash = models.CharField(max_length=32, blank=True)

    @classmethod
    def issue(cls, email: str, ip_hash: str = "") -> str:
        now = timezone.now()
        cls.objects.filter(email=email, used_at__isnull=True).update(used_at=now)  # invalidate older links
        raw = secrets.token_urlsafe(32)
        cls.objects.create(
            email=email,
            token_hash=sha256_hex(raw),
            expires_at=now + dt.timedelta(minutes=settings.MAGIC_LINK_TTL_MINUTES),
            requested_ip_hash=ip_hash,
        )
        return raw

    @classmethod
    def consume(cls, raw: str) -> str | None:
        """Atomically mark the token used; return the email, or None if invalid/expired/used."""
        if not raw or len(raw) > 128:
            return None
        h = sha256_hex(raw)
        now = timezone.now()
        updated = cls.objects.filter(token_hash=h, used_at__isnull=True, expires_at__gt=now).update(used_at=now)
        if updated != 1:
            return None
        return cls.objects.get(token_hash=h).email
