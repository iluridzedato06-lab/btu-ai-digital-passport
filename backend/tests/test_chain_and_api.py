"""Integration tests against the compose Anvil node: sheet -> version -> chain -> public verify."""
import hashlib

import pytest
from django.test import Client

from apps.accounts.models import MagicLinkToken
from apps.chain import client as chain_client
from apps.chain.services.anchor import revoke_version
from apps.chain.services.deploy import deploy_registry
from apps.chain.signing import recover_signer
from apps.passports.models import PassportVersion
from apps.sheets.services.sync import run_sync

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.chain]


@pytest.fixture
def chain(settings):
    settings.CHAIN_ENABLED = True
    settings.CONTRACT_ADDRESS = ""
    if not chain_client.w3().is_connected():
        pytest.skip("no chain node reachable")
    return deploy_registry()  # fresh registry per test


def verify(c, code):
    return c.get(f"/api/public/verify/{code}").json()


def test_full_loop_and_tamper(sheet, chain):
    run = run_sync(sheet())
    assert run.versions_anchored == 1, run.events
    v = PassportVersion.objects.get()
    assert v.status == "anchored"
    c = Client()
    d = verify(c, v.verification.formatted)
    assert d["status"] == "valid_latest"
    assert d["document_authentic"] and d["issuer_authentic"]
    assert all(d["checks"].values()), d["checks"]

    # The PDF on disk is exactly what was anchored
    pdf = v.pdf_file.read()
    rec = chain_client.read_version(v.passport.passport_id_hash, 1)
    assert rec.pdf_hash == hashlib.sha256(pdf).hexdigest()
    # One flipped byte -> different fingerprint -> unknown
    tampered = bytearray(pdf)
    tampered[len(tampered) // 2] ^= 1
    t = c.get(f"/api/public/verify/by-hash/{hashlib.sha256(bytes(tampered)).hexdigest()}").json()
    assert t["status"] == "not_found"
    # Issuer signature in the PDF recovers to the authorised issuer
    signer = recover_signer(chain.contract_address, v.passport.passport_id_hash, 1, "0x" + v.verification.code_hash,
                            v.snapshot["issued_at_unix"], v.issuer_signature)
    assert signer == chain.issuer_address


def test_versions_superseded_and_revoked(sheet, chain):
    from tests.conftest import AWARDS

    run_sync(sheet(awards=AWARDS[:1]))
    run_sync(sheet())
    v1, v2 = PassportVersion.objects.order_by("version_number")
    c = Client()
    assert verify(c, v1.verification.formatted)["status"] == "valid_superseded"
    assert verify(c, v2.verification.formatted)["status"] == "valid_latest"
    rev = revoke_version(v2, "issued in error", "test")
    assert rev.status == "confirmed"
    assert verify(c, v2.verification.formatted)["status"] == "revoked"
    # after revoking v2, v1 is the latest valid version again
    assert verify(c, v1.verification.formatted)["status"] == "valid_latest"


def test_magic_link_and_access_control(sheet, chain, settings):
    run_sync(sheet())
    v = PassportVersion.objects.get()
    c = Client(enforce_csrf_checks=False)
    assert c.get("/api/me/passport/versions/1/download").status_code in (401, 403)
    r = c.post("/api/auth/magic-link/request", {"email": "evil@gmail.com"}, content_type="application/json")
    assert r.status_code == 400
    r = c.post("/api/auth/magic-link/request", {"email": "nobody@btu.edu.ge"}, content_type="application/json")
    assert r.status_code == 202 and not MagicLinkToken.objects.exists()  # no enumeration, no token
    raw = MagicLinkToken.issue("ana.g@btu.edu.ge")
    assert c.post("/api/auth/magic-link/consume", {"token": raw}, content_type="application/json").status_code == 200
    assert c.post("/api/auth/magic-link/consume", {"token": raw}, content_type="application/json").status_code == 400
    dl = c.get("/api/me/passport/versions/1/download")
    assert dl.status_code == 200 and hashlib.sha256(b"".join(dl.streaming_content)).hexdigest() == v.pdf_sha256
    assert c.get("/api/admin/overview").status_code == 403
    # another student cannot fetch Ana's passport: Luka has none, so 404
    c2 = Client()
    raw2 = MagicLinkToken.issue("luka.t@btu.edu.ge")
    c2.post("/api/auth/magic-link/consume", {"token": raw2}, content_type="application/json")
    assert c2.get("/api/me/passport/versions/1/download").status_code == 404
