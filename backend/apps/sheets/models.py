from django.db import models

from apps.core.models import BaseModel


class SyncRun(BaseModel):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        RUNNING = "running", "Running"
        OK = "ok", "Completed"
        PARTIAL = "partial", "Completed with row errors"
        FAILED = "failed", "Failed"

    adapter = models.CharField(max_length=20)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.RUNNING)
    triggered_by = models.CharField(max_length=160)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    rows_seen = models.PositiveIntegerField(default=0)
    rows_created = models.PositiveIntegerField(default=0)
    rows_updated = models.PositiveIntegerField(default=0)
    rows_errors = models.PositiveIntegerField(default=0)
    versions_issued = models.PositiveIntegerField(default=0)
    versions_anchored = models.PositiveIntegerField(default=0)
    events = models.JSONField(default=list, blank=True)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def log(self, message: str, **extra):
        self.events.append({"message": message, **extra})


class SyncRow(BaseModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Waiting for confirmation"
        OK = "OK", "OK"
        QUEUED = "QUEUED", "Queued for issuance"
        ISSUED = "ISSUED", "Issued"
        ERROR = "ERROR", "Error"
        WITHDRAW_PENDING = "WITHDRAW_PENDING", "Withdrawal awaiting approval"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"

    tab = models.CharField(max_length=20)
    row_key = models.CharField(max_length=64)
    last_row_number = models.PositiveIntegerField(default=0)
    last_hash = models.CharField(max_length=64, blank=True)
    last_status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    last_message = models.CharField(max_length=300, blank=True)
    missing_runs = models.PositiveIntegerField(default=0)
    last_seen_run = models.ForeignKey(SyncRun, null=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tab", "row_key"], name="uniq_sync_row")]
        ordering = ["tab", "last_row_number"]
