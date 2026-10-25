from django.conf import settings
from django.db import models, transaction

from apps.core.codes import format_code
from apps.core.models import BaseModel


class StampType(models.TextChoices):
    FOCUSED = "FOCUSED", "AI Skill — Focused Learning"
    APPLIED = "APPLIED", "AI Applied Skill — Applied Learning"
    ADVANCED = "ADVANCED", "AI Advanced Skill — Extended Academic Learning"


STAMP_LABELS = {
    "FOCUSED": {"title": "AI Skill", "subtitle": "Focused Learning"},
    "APPLIED": {"title": "AI Applied Skill", "subtitle": "Applied Learning"},
    "ADVANCED": {"title": "AI Advanced Skill", "subtitle": "Extended Academic Learning"},
}


class SkillCatalog(BaseModel):
    skill_code = models.CharField(max_length=32, unique=True)
    name_en = models.CharField(max_length=120)
    name_ka = models.CharField(max_length=160, blank=True)
    description_en = models.TextField()
    description_ka = models.TextField(blank=True)
    stamp_type = models.CharField(max_length=10, choices=StampType.choices)
    default_earned_through = models.CharField(max_length=160, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name_en"]

    def __str__(self):
        return f"{self.name_en} [{self.stamp_type}]"


class PassportIdCounter(models.Model):
    year = models.PositiveIntegerField(primary_key=True)
    last_value = models.PositiveIntegerField(default=0)


def next_passport_id(year: int) -> str:
    """Allocate the next permanent Passport ID for the given year: BTU-AI-YYYY-NNNNN."""
    with transaction.atomic():
        counter, _ = PassportIdCounter.objects.select_for_update().get_or_create(year=year)
        counter.last_value += 1
        counter.save(update_fields=["last_value"])
        return f"BTU-AI-{year}-{counter.last_value:05d}"


class Passport(BaseModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"

    student = models.OneToOneField("students.Student", on_delete=models.PROTECT, related_name="passport")
    passport_id = models.CharField(max_length=24, unique=True, editable=False)
    passport_id_hash = models.CharField(max_length=66, unique=True, editable=False)
    first_issued_on = models.DateField(editable=False)
    holder_first_name = models.CharField(max_length=80, editable=False)
    holder_last_name = models.CharField(max_length=80, editable=False)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    latest_version_number = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.passport_id

    @property
    def latest_valid_version(self):
        return (
            self.versions.filter(status=PassportVersion.Status.ANCHORED, revoked_at__isnull=True)
            .order_by("-version_number")
            .first()
        )

    @property
    def anchored_count(self) -> int:
        return self.versions.filter(status=PassportVersion.Status.ANCHORED).count()


def pdf_upload_to(instance, filename):
    return f"passports/{instance.passport.passport_id}/v{instance.version_number}/{filename}"


class PassportVersion(BaseModel):
    class Status(models.TextChoices):
        RENDERED = "rendered", "Rendered, awaiting anchoring"
        ANCHORING = "anchoring", "Anchoring"
        ANCHORED = "anchored", "Anchored on chain"
        ANCHOR_FAILED = "anchor_failed", "Anchoring failed"

    class Reason(models.TextChoices):
        NEW_AWARDS = "new_awards", "New skills added"
        AWARD_EDITED = "award_edited", "Skill record corrected"
        AWARD_WITHDRAWN = "award_withdrawn", "Skill withdrawn"
        REISSUE = "reissue", "Reissued by staff"
        MANUAL = "manual", "Manual correction"

    passport = models.ForeignKey(Passport, on_delete=models.PROTECT, related_name="versions")
    version_number = models.PositiveIntegerField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.RENDERED)
    trigger_reason = models.CharField(max_length=20, choices=Reason.choices)
    snapshot = models.JSONField()
    pdf_file = models.FileField(upload_to=pdf_upload_to, max_length=255)
    pdf_sha256 = models.CharField(max_length=64, unique=True)
    pdf_size = models.PositiveIntegerField(default=0)
    issuer_signature = models.CharField(max_length=140, blank=True)
    issued_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoke_reason = models.CharField(max_length=300, blank=True)
    revoked_by = models.CharField(max_length=160, blank=True)
    trigger_sync_run = models.ForeignKey("sheets.SyncRun", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["passport", "-version_number"]
        constraints = [
            models.UniqueConstraint(fields=["passport", "version_number"], name="uniq_passport_version"),
        ]

    def __str__(self):
        return f"{self.passport.passport_id} v{self.version_number}"

    @property
    def is_latest_valid(self) -> bool:
        lv = self.passport.latest_valid_version
        return bool(lv and lv.pk == self.pk)

    @property
    def download_filename(self) -> str:
        return f"{self.passport.passport_id}-v{self.version_number}.pdf"


class SkillAward(BaseModel):
    award_id = models.CharField(max_length=32, unique=True)
    student = models.ForeignKey("students.Student", on_delete=models.PROTECT, related_name="awards")
    skill = models.ForeignKey(SkillCatalog, on_delete=models.PROTECT, related_name="awards")
    earned_through = models.CharField(max_length=160)
    date_earned = models.DateField()
    confirmed_by = models.CharField(max_length=160)
    source_row_hash = models.CharField(max_length=64, blank=True)
    first_included_version = models.ForeignKey(
        PassportVersion, null=True, blank=True, on_delete=models.SET_NULL, related_name="new_awards"
    )
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    withdraw_requested_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["date_earned", "skill__name_en"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "skill"],
                condition=models.Q(withdrawn_at__isnull=True),
                name="uniq_active_award_per_skill",
            )
        ]

    def __str__(self):
        return f"{self.award_id}: {self.student.student_number} / {self.skill.skill_code}"


class VerificationCode(BaseModel):
    version = models.OneToOneField(PassportVersion, on_delete=models.CASCADE, related_name="verification")
    code = models.CharField(max_length=12, unique=True)
    code_hash = models.CharField(max_length=64)
    lookup_count = models.PositiveIntegerField(default=0)
    last_lookup_at = models.DateTimeField(null=True, blank=True)

    @property
    def formatted(self) -> str:
        return format_code(self.code)

    @property
    def verify_url(self) -> str:
        return f"{settings.PUBLIC_BASE_URL}/{settings.VERIFY_LOCALE_IN_QR}/verify/{self.formatted}"
