"""Thin web3.py wrapper around the PassportRegistry contract."""
import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from eth_account import Account
from web3 import Web3

log = logging.getLogger(__name__)
ARTIFACT = Path(__file__).resolve().parent / "artifacts" / "PassportRegistry.json"


class ChainUnavailable(Exception):
    pass


@lru_cache(maxsize=1)
def load_artifact() -> dict:
    data = json.loads(ARTIFACT.read_text())
    bytecode = data["bytecode"]
    if isinstance(bytecode, dict):
        bytecode = bytecode["object"]
    return {"abi": data["abi"], "bytecode": bytecode}


def w3() -> Web3:
    provider = Web3.HTTPProvider(settings.CHAIN_RPC_URL, request_kwargs={"timeout": 20})
    return Web3(provider)


def issuer_account():
    if not settings.CHAIN_ISSUER_PRIVATE_KEY:
        raise ChainUnavailable("CHAIN_ISSUER_PRIVATE_KEY is not configured")
    return Account.from_key(settings.CHAIN_ISSUER_PRIVATE_KEY)


def owner_account():
    key = settings.CHAIN_OWNER_PRIVATE_KEY or settings.CHAIN_ISSUER_PRIVATE_KEY
    if not key:
        raise ChainUnavailable("CHAIN_OWNER_PRIVATE_KEY is not configured")
    return Account.from_key(key)


def contract_address() -> str | None:
    if settings.CONTRACT_ADDRESS:
        return Web3.to_checksum_address(settings.CONTRACT_ADDRESS)
    from .models import ChainDeployment

    dep = ChainDeployment.objects.filter(chain_id=settings.CHAIN_ID).first()
    return Web3.to_checksum_address(dep.contract_address) if dep else None


def current_deployment():
    from .models import ChainDeployment

    addr = contract_address()
    if not addr:
        return None
    return ChainDeployment.objects.filter(chain_id=settings.CHAIN_ID, contract_address__iexact=addr).first()


def registry(web3: Web3 | None = None):
    web3 = web3 or w3()
    addr = contract_address()
    if not addr:
        raise ChainUnavailable("PassportRegistry is not deployed for this chain yet")
    return web3.eth.contract(address=addr, abi=load_artifact()["abi"])


def explorer_tx_url(tx_hash: str | None) -> str:
    if not tx_hash or not settings.EXPLORER_TX_URL:
        return ""
    return settings.EXPLORER_TX_URL.replace("{}", tx_hash)


def explorer_address_url(address: str | None) -> str:
    if not address or not settings.EXPLORER_ADDRESS_URL:
        return ""
    return settings.EXPLORER_ADDRESS_URL.replace("{}", address)


def send_transaction(web3: Web3, account, fn, gas: int | None = None):
    """Sign and send a contract function call from ``account``. Returns tx hash hex."""
    params = {
        "from": account.address,
        "nonce": web3.eth.get_transaction_count(account.address, "pending"),
        "chainId": settings.CHAIN_ID,
    }
    if gas:
        params["gas"] = gas
    tx = fn.build_transaction(params)
    if "gas" not in params:
        tx["gas"] = int(web3.eth.estimate_gas(tx) * 1.25)
    signed = account.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    return "0x" + tx_hash.hex().removeprefix("0x")


@dataclass
class OnChainVersion:
    pdf_hash: str
    code_hash: str
    issued_at: int
    revoked_at: int
    issuer: str

    @property
    def exists(self) -> bool:
        return self.issued_at != 0


def _record(raw) -> OnChainVersion:
    pdf_hash, code_hash, issued_at, revoked_at, issuer = raw
    return OnChainVersion(
        pdf_hash=pdf_hash.hex().removeprefix("0x"),
        code_hash=code_hash.hex().removeprefix("0x"),
        issued_at=int(issued_at),
        revoked_at=int(revoked_at),
        issuer=issuer,
    )


def read_version(passport_id_hash: str, version: int) -> OnChainVersion:
    c = registry()
    return _record(c.functions.getVersion(bytes.fromhex(passport_id_hash[2:]), version).call())


def read_latest(passport_id_hash: str) -> tuple[int, OnChainVersion]:
    c = registry()
    v, rec = c.functions.getLatest(bytes.fromhex(passport_id_hash[2:])).call()
    return int(v), _record(rec)


def is_issuer(address: str) -> bool:
    return bool(registry().functions.isIssuer(Web3.to_checksum_address(address)).call())


def contract_owner() -> str:
    return registry().functions.owner().call()


def has_code(address: str | None) -> bool:
    if not address:
        return False
    try:
        return len(w3().eth.get_code(Web3.to_checksum_address(address))) > 0
    except Exception:  # noqa: BLE001
        return False
