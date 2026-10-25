"""Snapshot -> multi-page PDF bytes (WeasyPrint + pikepdf metadata)."""
import datetime as dt
import hashlib
import io
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string

ASSETS_DIR = Path(settings.BASE_DIR) / "templates" / "pdf" / "assets"
GRID_PER_PAGE = 10
TABLE_PER_PAGE = 5
STAMP_FILES = {"FOCUSED": "stamps/focused.svg", "APPLIED": "stamps/applied.svg", "ADVANCED": "stamps/advanced.svg"}


def _fmt_date(iso: str) -> str:
    d = dt.date.fromisoformat(iso)
    return d.strftime("%d.%m.%Y")


def _chunks(items: list, size: int, pad: bool) -> list[list]:
    pages = [items[i : i + size] for i in range(0, len(items), size)] or [[]]
    if pad:
        pages = [p + [None] * (size - len(p)) for p in pages]
    return pages


def _qr_svg(url: str) -> str:
    import segno

    return segno.make(url, error="m").svg_inline(scale=3, dark="#111111", light=None, border=0)


def build_context(snapshot: dict) -> dict:
    awards = []
    for a in snapshot["awards"]:
        awards.append({**a, "date_display": _fmt_date(a["date_earned"]), "stamp_src": STAMP_FILES[a["stamp_type"]]})
    grid_pages = _chunks(awards, GRID_PER_PAGE, pad=True)
    table_pages = _chunks(awards, TABLE_PER_PAGE, pad=False)
    return {
        "s": snapshot,
        "first_issued_display": _fmt_date(snapshot["first_issued_on"]),
        "version_issued_display": _fmt_date(snapshot["version_issued_on"]),
        "grid_pages": [{"rows": [p[:5], p[5:]], "index": i + 1, "count": len(grid_pages)} for i, p in
                       enumerate(grid_pages)],
        "table_pages": [{"rows": p, "index": i + 1, "count": len(table_pages)} for i, p in enumerate(table_pages)],
        "qr_svg": _qr_svg(snapshot["verification"]["url"]),
        "award_count": len(awards),
    }


def render_html(snapshot: dict) -> str:
    return render_to_string("pdf/passport.html", build_context(snapshot))


def _post_process(pdf_bytes: bytes, snapshot: dict) -> bytes:
    import pikepdf

    v = snapshot["verification"]
    issuer = snapshot["issuer"]
    with pikepdf.open(io.BytesIO(pdf_bytes)) as pdf:
        pdf.docinfo["/Title"] = f"BTU AI Skills Digital Passport {snapshot['passport_id']} v{snapshot['version']}"
        pdf.docinfo["/Author"] = issuer["name"]
        pdf.docinfo["/Subject"] = f"Verification code {v['code']} - verify at {v['verify_page']}"
        pdf.docinfo["/Keywords"] = f"passport_id={snapshot['passport_id']};version={snapshot['version']};" \
                                   f"verification_code={v['code']};chain_id={issuer['chain_id']};" \
                                   f"contract={issuer['contract']};issuer={issuer['address']};" \
                                   f"issuer_signature={issuer.get('signature', '')};issued_at={snapshot['issued_at_unix']}"
        pdf.docinfo["/Creator"] = "BTU AI Skills Passport issuance service"
        pdf.docinfo["/Producer"] = "BTU AI Skills Passport"
        for key in ("/CreationDate", "/ModDate"):
            if key in pdf.docinfo:
                del pdf.docinfo[key]
        with pdf.open_metadata(set_pikepdf_as_editor=False, update_docinfo=False) as meta:
            meta["dc:title"] = str(pdf.docinfo["/Title"])
            meta["dc:creator"] = [issuer["name"]]
            meta["pdf:Keywords"] = str(pdf.docinfo["/Keywords"])
        seed = hashlib.sha256(f"{snapshot['passport_id']}|{snapshot['version']}".encode()).digest()[:16]
        pdf.trailer.ID = pikepdf.Array([pikepdf.String(seed), pikepdf.String(seed)])
        out = io.BytesIO()
        pdf.save(out, deterministic_id=False, static_id=True, linearize=False)
        return out.getvalue()


def render_passport(snapshot: dict) -> bytes:
    from weasyprint import HTML
    from weasyprint.text.fonts import FontConfiguration

    html = render_html(snapshot)
    font_config = FontConfiguration()
    pdf = HTML(string=html, base_url=str(ASSETS_DIR) + "/").write_pdf(font_config=font_config)
    return _post_process(pdf, snapshot)
