from django.conf import settings
from django.core.management.base import BaseCommand

from apps.chain import client
from apps.chain.services.deploy import deploy_registry


class Command(BaseCommand):
    help = "Deploy the PassportRegistry contract to the configured chain and authorise the issuer key."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Deploy even if a deployment already exists")

    def handle(self, *args, force=False, **opts):
        addr = client.contract_address()
        if addr and client.has_code(addr) and not force:
            self.stdout.write(f"PassportRegistry already deployed at {addr} on chain {settings.CHAIN_ID}")
            return
        dep = deploy_registry()
        self.stdout.write(self.style.SUCCESS(
            f"Deployed PassportRegistry at {dep.contract_address} (chain {dep.chain_id}); issuer {dep.issuer_address}"
        ))
        if settings.CONTRACT_ADDRESS and settings.CONTRACT_ADDRESS.lower() != dep.contract_address.lower():
            self.stdout.write(self.style.WARNING(
                "CONTRACT_ADDRESS in the environment differs from the new deployment; update or clear it."
            ))
