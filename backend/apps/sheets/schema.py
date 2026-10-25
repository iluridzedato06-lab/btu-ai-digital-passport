"""Single source of truth for the Google Sheet layout.

Business columns are filled by people. ``sys_*`` columns are written by the system and are
excluded from change detection.
"""

STUDENTS = "Students"
CATALOG = "SkillCatalog"
AWARDS = "Awards"
README = "README"

TABS = {
    STUDENTS: {
        "key": "student_number",
        "business": [
            "student_number",
            "first_name_en",
            "last_name_en",
            "first_name_ka",
            "last_name_ka",
            "btu_email",
            "programme",
            "consent",
        ],
        "required": ["student_number", "first_name_en", "last_name_en", "btu_email", "consent"],
        "system": ["sys_passport_id", "sys_status", "sys_message", "sys_synced_at"],
    },
    CATALOG: {
        "key": "skill_code",
        "business": [
            "skill_code",
            "skill_name_en",
            "skill_name_ka",
            "stamp_type",
            "description_en",
            "description_ka",
            "default_earned_through",
            "active",
        ],
        "required": ["skill_code", "skill_name_en", "stamp_type", "description_en"],
        "system": ["sys_status", "sys_message"],
    },
    AWARDS: {
        "key": "award_id",
        "business": [
            "award_id",
            "student_number",
            "skill_code",
            "earned_through",
            "date_earned",
            "confirmed",
            "confirmed_by",
            "notes",
        ],
        "required": ["award_id", "student_number", "skill_code", "earned_through", "date_earned"],
        "system": ["sys_status", "sys_message", "sys_passport_version", "sys_synced_at", "sys_row_hash"],
    },
}

SYNC_ORDER = [CATALOG, STUDENTS, AWARDS]


def headers(tab: str) -> list[str]:
    spec = TABS[tab]
    return spec["business"] + spec["system"]


TRUE_VALUES = {"true", "yes", "y", "1", "x", "✓", "კი"}


def is_truthy(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in TRUE_VALUES


ERRORS = {
    "E001": "Missing required value: {field}",
    "E002": "Email must end with @{domains}",
    "E003": "Unknown student_number {value} (add the student to the Students tab first)",
    "E004": "Student {value} has not given consent (consent must be YES)",
    "E005": "Unknown or inactive skill_code {value}",
    "E006": "date_earned must be YYYY-MM-DD, not in the future and not before 2016-09-16",
    "E007": "Student already holds this skill (see {value})",
    "E008": "Duplicate key {value} in this tab",
    "E009": "Name is locked after the first passport was issued; contact the passport office",
    "E010": "confirmed is TRUE but confirmed_by is empty",
    "E011": "stamp_type must be FOCUSED, APPLIED or ADVANCED",
    "E012": "Email {value} is already used by another student",
    "E013": "Name may only contain letters, spaces, hyphens and apostrophes",
}


def error(code: str, **kw) -> str:
    return f"{code}: " + ERRORS[code].format(**kw)
