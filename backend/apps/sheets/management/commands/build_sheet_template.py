from django.conf import settings
from django.core.management.base import BaseCommand

from apps.sheets.template import build_template, export_csvs, read_csv_dicts


class Command(BaseCommand):
    help = ("Write the official sheet template (empty Students/Awards, catalogue filled) and a test sheet with the "
            "showcase students, as .xlsx plus one CSV per tab for Google Sheets import.")

    def handle(self, *args, **opts):
        path = build_template(settings.SHEET_TEMPLATE_PATH)
        export_csvs(path, path.parent)
        test_path = path.with_name("BTU_AI_Passport_Test_Sheet.xlsx")
        build_template(
            test_path,
            students=read_csv_dicts(settings.SHOWCASE_DIR / "students.csv"),
            awards=read_csv_dicts(settings.SHOWCASE_DIR / "awards.csv"),
        )
        self.stdout.write(self.style.SUCCESS(f"Template and test sheet written to {path.parent}"))
