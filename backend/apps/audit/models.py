from django.db import models

from apps.core.models import BaseModel


class AuditLog(BaseModel):
    actor = models.CharField(max_length=160)
    action = models.CharField(max_length=60, db_index=True)
    target_type = models.CharField(max_length=60, blank=True)
    target_id = models.CharField(max_length=80, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_hash = models.CharField(max_length=32, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["target_type", "target_id"])]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise RuntimeError("Audit log entries are append-only")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("Audit log entries are append-only")


def actor_for(request) -> str:
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        return f"user:{user.email or user.username}"
    return "anon"


def client_ip(request) -> str:
    fwd = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if fwd:
        return fwd.split(",")[-1].strip()
    return request.META.get("REMOTE_ADDR", "")


def audit(action: str, *, actor: str = "system", target=None, request=None, **metadata) -> AuditLog:
    from apps.core.hashing import hash_ip

    target_type = target_id = ""
    if target is not None:
        target_type = target._meta.model_name
        target_id = str(getattr(target, "pk", ""))
    ip_hash = ""
    if request is not None:
        if actor == "system":
            actor = actor_for(request)
        ip_hash = hash_ip(client_ip(request))
    return AuditLog.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata=metadata,
        ip_hash=ip_hash,
    )
