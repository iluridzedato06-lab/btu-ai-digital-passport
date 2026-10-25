import pytest

from apps.sheets.adapters.local_xlsx import LocalXlsxAdapter
from apps.sheets.template import build_template

STUDENTS = [
    {"student_number": "T-1", "first_name_en": "Ana", "last_name_en": "Gelashvili", "btu_email": "ana.g@btu.edu.ge",
     "consent": "YES"},
    {"student_number": "T-2", "first_name_en": "Luka", "last_name_en": "Tsiklauri", "btu_email": "luka.t@btu.edu.ge",
     "consent": "YES"},
]
AWARDS = [
    {"award_id": "AW-1", "student_number": "T-1", "skill_code": "PROMPT-ENG", "earned_through": "Workshop",
     "date_earned": "2026-03-07", "confirmed": "TRUE", "confirmed_by": "Office"},
    {"award_id": "AW-2", "student_number": "T-1", "skill_code": "AI-AGENTS", "earned_through": "Challenge",
     "date_earned": "2026-04-01", "confirmed": "TRUE", "confirmed_by": "Office"},
]


@pytest.fixture(autouse=True)
def _settings(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.ALLOWED_EMAIL_DOMAINS = ["btu.edu.ge"]
    settings.DEPLOYMENTS_DIR = tmp_path / "deployments"
    settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}


@pytest.fixture
def sheet(tmp_path):
    def make(students=None, awards=None):
        path = tmp_path / "sheet.xlsx"
        build_template(path, students=STUDENTS if students is None else students,
                       awards=AWARDS if awards is None else awards)
        return LocalXlsxAdapter(path)

    return make


@pytest.fixture
def no_chain(settings):
    settings.CHAIN_ENABLED = False
    settings.CHAIN_RPC_URL = "http://127.0.0.1:1"
    settings.CONTRACT_ADDRESS = ""
    settings.CHAIN_ISSUER_PRIVATE_KEY = ""
    settings.CHAIN_OWNER_PRIVATE_KEY = ""
