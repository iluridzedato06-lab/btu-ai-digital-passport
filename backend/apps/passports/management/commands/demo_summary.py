from django.conf import settings
from django.core.management.base import BaseCommand

from apps.passports.models import Passport


class Command(BaseCommand):
    help = "Print every passport with its latest verification link."

    def handle(self, *args, **opts):
        base = settings.PUBLIC_BASE_URL
        for p in Passport.objects.select_related("student").order_by("passport_id"):
            v = p.versions.select_related("verification").first()
            if not v:
                continue
            self.stdout.write(
                f"{p.passport_id}  {p.holder_first_name} {p.holder_last_name:<12} v{v.version_number} "
                f"[{v.status}]  {v.verification.verify_url}  login: {p.student.email}"
            )
        self.stdout.write(f"\nSite: {base}/ka  |  {base}/en   Mail inbox (dev): http://localhost:8025")
