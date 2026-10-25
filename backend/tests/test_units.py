import threading

import pytest

from apps.core.codes import ALPHABET, format_code, generate_code, normalize_code
from apps.core.hashing import canonical_row_hash, keccak_hex, sha256_hex


def test_code_alphabet_excludes_confusables():
    for ch in "ILOU":
        assert ch not in ALPHABET
    codes = {generate_code() for _ in range(5000)}
    assert len(codes) == 5000
    assert all(len(c) == 12 and set(c) <= set(ALPHABET) for c in codes)


def test_code_normalisation_round_trip():
    c = generate_code()
    assert normalize_code(format_code(c).lower()) == c
    assert normalize_code("oil0-0000-0000") == "011000000000"
    assert normalize_code("too-short") is None
    assert normalize_code("UUUU-UUUU-UUUU") is None


def test_hashes():
    assert sha256_hex("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert keccak_hex("BTU-AI-2026-00001").startswith("0x") and len(keccak_hex("x")) == 66
    assert canonical_row_hash({"a": " 1 ", "b": None}) == canonical_row_hash({"b": "", "a": "1"})


@pytest.mark.django_db(transaction=True)
def test_passport_ids_are_sequential_and_unique():
    from apps.passports.models import next_passport_id

    ids = [next_passport_id(2026) for _ in range(5)]
    assert ids[0] == "BTU-AI-2026-00001" and ids[-1] == "BTU-AI-2026-00005"
    assert next_passport_id(2027) == "BTU-AI-2027-00001"


@pytest.mark.django_db(transaction=True)
def test_passport_id_counter_under_concurrency():
    from django.db import connection

    from apps.passports.models import next_passport_id

    if connection.vendor != "postgresql":
        pytest.skip("row locking needs postgres")
    out, lock = [], threading.Lock()

    def work():
        from django.db import connection as c

        v = next_passport_id(2030)
        with lock:
            out.append(v)
        c.close()

    threads = [threading.Thread(target=work) for _ in range(10)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert len(set(out)) == 10
