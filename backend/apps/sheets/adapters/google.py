"""Google Sheets adapter (service account).

Setup: create a service account, enable the Google Sheets API, share the spreadsheet with the
service-account email as Editor, then set GOOGLE_SPREADSHEET_ID and either
GOOGLE_SERVICE_ACCOUNT_JSON_B64 or GOOGLE_SERVICE_ACCOUNT_FILE.
"""
import base64
import json
import time

from django.conf import settings

from .base import CellUpdate, SheetRow

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _col_letter(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


class GoogleSheetsAdapter:
    name = "google"

    def __init__(self):
        import gspread
        from google.oauth2.service_account import Credentials

        if not settings.GOOGLE_SPREADSHEET_ID:
            raise RuntimeError("GOOGLE_SPREADSHEET_ID is not set")
        if settings.GOOGLE_SERVICE_ACCOUNT_JSON_B64:
            info = json.loads(base64.b64decode(settings.GOOGLE_SERVICE_ACCOUNT_JSON_B64))
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        elif settings.GOOGLE_SERVICE_ACCOUNT_FILE:
            creds = Credentials.from_service_account_file(settings.GOOGLE_SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        else:
            raise RuntimeError("Set GOOGLE_SERVICE_ACCOUNT_JSON_B64 or GOOGLE_SERVICE_ACCOUNT_FILE")
        self._gc = gspread.authorize(creds)
        self._sh = self._gc.open_by_key(settings.GOOGLE_SPREADSHEET_ID)
        self._headers: dict[str, list[str]] = {}

    def describe(self) -> str:
        return f"Google Sheet {settings.GOOGLE_SPREADSHEET_ID[:10]}…"

    def _retry(self, fn, *args, **kwargs):
        from gspread.exceptions import APIError

        delay = 2
        for attempt in range(5):
            try:
                return fn(*args, **kwargs)
            except APIError as exc:  # 429 / 5xx -> back off
                status = getattr(exc.response, "status_code", 0)
                if status not in (429, 500, 502, 503) or attempt == 4:
                    raise
                time.sleep(delay)
                delay *= 2

    def read_tab(self, tab: str) -> list[SheetRow]:
        import gspread

        try:
            ws = self._sh.worksheet(tab)
        except gspread.WorksheetNotFound:
            return []
        values = self._retry(ws.get_all_values, value_render_option="UNFORMATTED_VALUE",
                             date_time_render_option="FORMATTED_STRING")
        if not values:
            return []
        header = [h.strip() for h in values[0]]
        self._headers[tab] = header
        out = []
        for idx, raw in enumerate(values[1:], start=2):
            row = {h: raw[i] if i < len(raw) else "" for i, h in enumerate(header) if h}
            if all(str(v).strip() == "" for v in row.values()):
                continue
            out.append(SheetRow(tab=tab, row_number=idx, values=row))
        return out

    def write_cells(self, updates: list[CellUpdate]) -> None:
        if not updates:
            return
        data = []
        for u in updates:
            header = self._headers.get(u.tab)
            if header is None:
                header = [h.strip() for h in self._retry(self._sh.worksheet(u.tab).row_values, 1)]
                self._headers[u.tab] = header
            if u.column not in header:
                continue  # never add columns to the real sheet automatically
            col = _col_letter(header.index(u.column) + 1)
            data.append({"range": f"'{u.tab}'!{col}{u.row_number}", "values": [[u.value]]})
        for i in range(0, len(data), 500):
            self._retry(self._sh.values_batch_update,
                        {"valueInputOption": "RAW", "data": data[i : i + 500]})
