# Sheet schema

Files in `data/sheet_template/`:

| File | Use |
|---|---|
| `BTU_AI_Passport_Sheet_Template.xlsx` | Official template: README tab, empty Students and Awards, filled SkillCatalog, dropdowns |
| `BTU_AI_Passport_Test_Sheet.xlsx` | Same template with the three showcase students and their awards |
| `Students.csv`, `SkillCatalog.csv`, `Awards.csv` | One CSV per tab for *File → Import* into Google Sheets |

Tab names and header names must match exactly. Column order does not matter. Grey `sys_*` columns
are written by the system; protect them in Google Sheets (*Data → Protect ranges*).

## Students — one row per student

| Column | Required | Rule |
|---|---|---|
| `student_number` | yes | Unique BTU student number |
| `first_name_en`, `last_name_en` | yes | Latin letters, spaces, hyphen, apostrophe. Printed on the passport. **Locked after the first passport is issued** |
| `first_name_ka`, `last_name_ka` | no | Shown in the Georgian portal |
| `btu_email` | yes | Must end with `@btu.edu.ge`; unique; used for sign-in |
| `programme` | no | Study programme |
| `consent` | yes | `YES` to allow a passport to be issued |
| `sys_passport_id`, `sys_status`, `sys_message`, `sys_synced_at` | system | Passport ID once issued; `REGISTERED`, `OK`, `PENDING` or `ERROR` |

## SkillCatalog — maintained by BTU staff

| Column | Required | Rule |
|---|---|---|
| `skill_code` | yes | Unique code, e.g. `PROMPT-ENG` |
| `skill_name_en` | yes | Printed on the passport |
| `skill_name_ka` | no | Shown in the Georgian portal |
| `stamp_type` | yes | `FOCUSED` (AI Skill), `APPLIED` (AI Applied Skill), `ADVANCED` (AI Advanced Skill) |
| `description_en` | yes | Printed in the detailed table |
| `description_ka` | no | |
| `default_earned_through` | no | Suggested activity name |
| `active` | no | `NO` stops new awards of this skill |

## Awards — one row per earned skill

| Column | Required | Rule |
|---|---|---|
| `award_id` | yes | Unique and never reused, e.g. `AW-0001`. The idempotency key |
| `student_number` | yes | Must exist in Students with consent `YES` |
| `skill_code` | yes | Must exist in SkillCatalog and be active |
| `earned_through` | yes | Activity name, max 160 characters |
| `date_earned` | yes | `YYYY-MM-DD`, not in the future |
| `confirmed` | yes | `TRUE` = BTU confirmed it. Only confirmed rows reach the passport |
| `confirmed_by` | when confirmed | Name of the confirming staff member |
| `notes` | no | Free text, ignored |
| `sys_status` | system | `PENDING`, `QUEUED`, `ISSUED`, `ERROR`, `WITHDRAW_PENDING` |
| `sys_message`, `sys_passport_version`, `sys_synced_at`, `sys_row_hash` | system | Details, `v3`, time, change fingerprint |

## Behaviour

- Every pass re-validates every row. Errors never stop the run; they are written next to the row.
- All new or changed awards of one student in one pass produce **one** new version.
- Editing a confirmed row after issuance creates a corrected version.
- Deleting or un-confirming an issued row does **not** remove the stamp automatically. It appears in
  *Passport office → Sheet sync → Withdrawal requests* for approval (or set `SYNC_AUTO_WITHDRAW=true`).

## Error codes

| Code | Meaning |
|---|---|
| E001 | Missing required value |
| E002 | Email not on an allowed domain |
| E003 | Unknown student number |
| E004 | Student has not given consent |
| E005 | Unknown or inactive skill code |
| E006 | Bad date, future date, or before 16.09.2016 |
| E007 | Student already holds this skill |
| E008 | Duplicate key in the tab |
| E009 | Name change after issuance (locked) |
| E010 | Confirmed without `confirmed_by` |
| E011 | Bad stamp type |
| E012 | Email already used by another student |
| E013 | Name contains invalid characters |
