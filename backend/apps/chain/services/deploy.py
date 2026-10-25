import json
import logging

from django.conf import settings
from django.utils import timezone

from .. import client
from ..models import ChainDeployment

log = logging.getLogger(__name__)


def deploy_registry() -> ChainDeployment:
    web3 = client.w3()
    if not web3.is_connected():
        raise client.ChainUnavailable(f"Cannot reach chain RPC at {settings.CHAIN_RPC_URL}")
    art = client.load_artifact()
    owner = client.owner_account()
    issuer = client.issuer_account()
    factory = web3.eth.contract(abi=art["abi"], bytecode=art["bytecode"])
    tx_hash = client.send_transaction(web3, owner, factory.constructor())
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=settings.CHAIN_RECEIPT_TIMEOUT)
    address = receipt["contractAddress"]
    reg = web3.eth.contract(address=address, abi=art["abi"])
    set_tx = client.send_transaction(web3, owner, reg.functions.setIssuer(issuer.address, True))
    web3.eth.wait_for_transaction_receipt(set_tx, timeout=settings.CHAIN_RECEIPT_TIMEOUT)
    dep = ChainDeployment.objects.create(
        chain_id=settings.CHAIN_ID,
        contract_address=address,
        owner_address=owner.address,
        issuer_address=issuer.address,
        tx_hash=tx_hash,
        block_number=receipt["blockNumber"],
    )
    try:
        settings.DEPLOYMENTS_DIR.mkdir(parents=True, exist_ok=True)
        (settings.DEPLOYMENTS_DIR / f"{settings.CHAIN_ID}.json").write_text(
            json.dumps(
                {
                    "chainId": settings.CHAIN_ID,
                    "chainName": settings.CHAIN_NAME,
                    "contractAddress": address,
                    "owner": owner.address,
                    "issuer": issuer.address,
                    "deployTx": tx_hash,
                    "block": receipt["blockNumber"],
                    "deployedAt": timezone.now().isoformat(),
                },
                indent=2,
            )
        )
    except OSError as exc:
        log.info("Could not write deployments file: %s", exc)
    return dep


def ensure_deployed(auto: bool | None = None) -> ChainDeployment | None:
    """Return the active deployment, deploying on a local dev chain when allowed."""
    auto = settings.AUTO_DEPLOY_CONTRACT if auto is None else auto
    addr = client.contract_address()
    if addr and client.has_code(addr):
        return client.current_deployment()
    if not auto:
        return None
    if addr and not settings.CONTRACT_ADDRESS:
        log.warning("Recorded contract %s has no code on chain %s (chain reset?). Redeploying.", addr,
                    settings.CHAIN_ID)
    return deploy_registry()
