from django.core.management.base import BaseCommand, CommandError

from apps.core.locks import advisory_lock
from apps.sheets.adapters.base import get_adapter
from apps.sheets.services.sync import run_sync


class Command(BaseCommand):
    help = "Run one sheet -> passport -> chain synchronisation pass."

    def add_arguments(self, parser):
        parser.add_argument("--adapter", choices=["local_xlsx", "google"])
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--no-anchor", action="store_true")

    def handle(self, *args, adapter=None, dry_run=False, no_anchor=False, **opts):
        with advisory_lock("btu_sync") as got:
            if not got:
                raise CommandError("Another sync is running")
            run = run_sync(get_adapter(adapter), triggered_by="cli", anchor=not no_anchor, dry_run=dry_run)
        self.stdout.write(
            f"Sync {run.status}: rows={run.rows_seen} created={run.rows_created} updated={run.rows_updated} "
            f"errors={run.rows_errors} versions_issued={run.versions_issued} anchored={run.versions_anchored}"
        )
        for e in run.events:
            self.stdout.write(f"  - {e['message']}")
        if run.error:
            raise CommandError(run.error)
