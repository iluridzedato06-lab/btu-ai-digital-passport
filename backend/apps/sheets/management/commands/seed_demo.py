from django.conf import settings
from django.core.management.base import BaseCommand

from apps.accounts.roles import ensure_roles
from apps.sheets.template import build_template, read_csv_dicts


class Command(BaseCommand):
    help = "Create the local demo sheet (template + 3 showcase students) and the staff roles."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Overwrite an existing local sheet")

    def handle(self, *args, reset=False, **opts):
        ensure_roles()
        path = settings.LOCAL_SHEET_PATH
        if path.exists() and not reset:
            self.stdout.write(f"Local sheet already exists at {path} (use --reset to recreate)")
            return
        students = read_csv_dicts(settings.SHOWCASE_DIR / "students.csv")
        awards = read_csv_dicts(settings.SHOWCASE_DIR / "awards.csv")
        build_template(path, students=students, awards=awards)
        self.stdout.write(self.style.SUCCESS(
            f"Local sheet written to {path} with {len(students)} students and {len(awards)} award rows"))
