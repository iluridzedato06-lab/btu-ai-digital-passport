from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class SheetRow:
    tab: str
    row_number: int  # 1-based sheet row (header is row 1)
    values: dict = field(default_factory=dict)

    def get(self, column: str) -> str:
        v = self.values.get(column)
        if v is None:
            return ""
        if isinstance(v, bool):
            return "TRUE" if v else "FALSE"
        if hasattr(v, "isoformat"):
            return v.isoformat()[:10]
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v).strip()


@dataclass
class CellUpdate:
    tab: str
    row_number: int
    column: str
    value: str


class SheetAdapter(Protocol):
    name: str

    def read_tab(self, tab: str) -> list[SheetRow]: ...

    def write_cells(self, updates: list[CellUpdate]) -> None: ...

    def describe(self) -> str: ...


def get_adapter(name: str | None = None) -> SheetAdapter:
    from django.conf import settings

    name = name or settings.SHEETS_ADAPTER
    if name == "google":
        from .google import GoogleSheetsAdapter

        return GoogleSheetsAdapter()
    from .local_xlsx import LocalXlsxAdapter

    return LocalXlsxAdapter()
