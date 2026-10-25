import uuid

from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Heartbeat(models.Model):
    """Single-row-per-component liveness record (the worker writes here every tick)."""

    name = models.CharField(max_length=40, primary_key=True)
    last_seen = models.DateTimeField()
    detail = models.JSONField(default=dict, blank=True)
