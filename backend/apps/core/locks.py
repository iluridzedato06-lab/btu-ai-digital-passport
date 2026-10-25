"""Cross-process lock so only one sync/anchor pass runs at a time."""
import contextlib
import zlib

from django.db import connection


@contextlib.contextmanager
def advisory_lock(name: str):
    """Yield True if the lock was acquired. Postgres advisory lock; always True elsewhere."""
    if connection.vendor != "postgresql":
        yield True
        return
    key = zlib.crc32(name.encode()) & 0x7FFFFFFF
    with connection.cursor() as cur:
        cur.execute("SELECT pg_try_advisory_lock(%s)", [key])
        got = cur.fetchone()[0]
    try:
        yield got
    finally:
        if got:
            with connection.cursor() as cur:
                cur.execute("SELECT pg_advisory_unlock(%s)", [key])
