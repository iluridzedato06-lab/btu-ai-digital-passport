from django.db import models

from apps.core.models import BaseModel


class ChainDeployment(BaseModel):
    chain_id = models.PositiveIntegerField()
    contract_address = models.CharField(max_length=42)
    owner_address = models.CharField(max_length=42)
    issuer_address = models.CharField(max_length=42)
    tx_hash = models.CharField(max_length=66)
    block_number = models.PositiveBigIntegerField(null=True)

    class Meta:
        ordering = ["-created_at"]


class AnchorTransaction(BaseModel):
    class Status(models.TextChoices):
        PENDING_SEND = "pending_send", "Waiting to send"
        SENT = "sent", "Sent"
        CONFIRMED = "confirmed", "Confirmed"
        FAILED = "failed", "Failed"

    version = models.OneToOneField("passports.PassportVersion", on_delete=models.CASCADE, related_name="anchor")
    chain_id = models.PositiveIntegerField()
    contract_address = models.CharField(max_length=42)
    issuer_address = models.CharField(max_length=42, blank=True)
    tx_hash = models.CharField(max_length=66, blank=True, null=True, unique=True)
    block_number = models.PositiveBigIntegerField(null=True, blank=True)
    block_timestamp = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING_SEND)
    attempts = models.PositiveIntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    gas_used = models.PositiveBigIntegerField(null=True, blank=True)
    payload = models.JSONField(default=dict)
    revoke_tx_hash = models.CharField(max_length=66, blank=True)


class RevocationTransaction(BaseModel):
    version = models.ForeignKey("passports.PassportVersion", on_delete=models.CASCADE, related_name="revocations")
    tx_hash = models.CharField(max_length=66, blank=True)
    reason = models.CharField(max_length=300)
    status = models.CharField(max_length=16, default="sent")
    last_error = models.TextField(blank=True)
