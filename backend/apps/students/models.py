from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import BaseModel


def validate_btu_email(value: str):
    domain = value.rsplit("@", 1)[-1].lower()
    if domain not in settings.ALLOWED_EMAIL_DOMAINS:
        raise ValidationError(f"Email must belong to: {', '.join(settings.ALLOWED_EMAIL_DOMAINS)}")


class Student(BaseModel):
    student_number = models.CharField(max_length=32, unique=True)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    first_name_ka = models.CharField(max_length=80, blank=True)
    last_name_ka = models.CharField(max_length=80, blank=True)
    email = models.EmailField(unique=True, validators=[validate_btu_email])
    programme = models.CharField(max_length=160, blank=True)
    consent_given_at = models.DateTimeField(null=True, blank=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="student"
    )

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_number})"

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    @property
    def names_locked(self) -> bool:
        passport = getattr(self, "passport", None)
        return bool(passport and passport.versions.exists())
