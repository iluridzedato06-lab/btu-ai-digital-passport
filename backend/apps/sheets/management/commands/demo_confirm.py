"""Demo helper: tick 'confirmed' on an Awards row in the LOCAL sheet, as an administrator would."""
from django.core.management.base import BaseCommand, CommandError

from apps.sheets import schema as S
from apps.sheets.adapters.base import CellUpdate
from apps.sheets.adapters.local_xlsx import LocalXlsxAdapter


class Command(BaseCommand):
    help = "Confirm an award row in the local workbook (e.g. AW-DEMO-0013) to demonstrate a passport update."

    def add_arguments(self, parser):
        parser.add_argument("award_id")
        parser.add_argument("--by", default="Passport Office")

    def handle(self, *args, award_id, by, **opts):
        adapter = LocalXlsxAdapter()
        for row in adapter.read_tab(S.AWARDS):
            if row.get("award_id") == award_id:
                adapter.write_cells([
                    CellUpdate(S.AWARDS, row.row_number, "confirmed", "TRUE"),
                    CellUpdate(S.AWARDS, row.row_number, "confirmed_by", by),
                ])
                self.stdout.write(self.style.SUCCESS(f"{award_id} confirmed; the worker will pick it up."))
                return
        raise CommandError(f"{award_id} not found in the local sheet")
