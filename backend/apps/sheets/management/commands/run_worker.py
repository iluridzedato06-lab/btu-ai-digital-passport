"""Long-running worker: periodic sheet sync, admin-requested syncs, anchoring retries, housekeeping."""
import logging
import signal
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.utils import timezone

from apps.accounts.models import MagicLinkToken
from apps.chain.services.anchor import process_anchor_queue
from apps.chain.services.deploy import ensure_deployed
from apps.core.locks import advisory_lock
from apps.core.models import Heartbeat
from apps.sheets.models import SyncRun
from apps.sheets.services.sync import run_sync

log = logging.getLogger("worker")


class Command(BaseCommand):
    help = "Run the background worker loop."

    def add_arguments(self, parser):
        parser.add_argument("--tick", type=float, default=5.0)

    def handle(self, *args, tick=5.0, **opts):
        stop = {"flag": False}

        def _stop(*_):
            stop["flag"] = True

        signal.signal(signal.SIGTERM, _stop)
        signal.signal(signal.SIGINT, _stop)
        last_sync = 0.0
        last_purge = 0.0
        deployed = False
        log.info("Worker started (sync every %ss)", settings.SYNC_INTERVAL_SECONDS)
        while not stop["flag"]:
            close_old_connections()
            detail = {}
            try:
                if settings.CHAIN_ENABLED and not deployed:
                    dep = ensure_deployed()
                    deployed = dep is not None
                    detail["contract"] = dep.contract_address if dep else None
                with advisory_lock("btu_sync") as got:
                    if got:
                        requested = SyncRun.objects.filter(status=SyncRun.Status.REQUESTED).order_by("created_at")
                        due = time.monotonic() - last_sync >= settings.SYNC_INTERVAL_SECONDS
                        if requested.exists() or due:
                            run = requested.first()
                            run = run_sync(run=run, triggered_by=run.triggered_by if run else "worker")
                            requested.filter(status=SyncRun.Status.REQUESTED).update(
                                status=SyncRun.Status.OK, finished_at=timezone.now(), error="Merged into a run")
                            last_sync = time.monotonic()
                            detail["last_sync"] = run.status
                        else:
                            process_anchor_queue()
                if time.monotonic() - last_purge > 3600:
                    MagicLinkToken.objects.filter(expires_at__lt=timezone.now() - timezone.timedelta(days=1)).delete()
                    last_purge = time.monotonic()
            except Exception:  # noqa: BLE001
                log.exception("Worker tick failed")
                detail["error"] = True
            Heartbeat.objects.update_or_create(name="worker", defaults={"last_seen": timezone.now(), "detail": detail})
            for _ in range(int(tick * 10)):
                if stop["flag"]:
                    break
                time.sleep(0.1)
        log.info("Worker stopped")
