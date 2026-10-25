# Connecting a real Google Sheet

1. Create the spreadsheet: *File → Import* each CSV from `data/sheet_template/` into its own tab named
   `Students`, `SkillCatalog`, `Awards` (keep the header row). Or upload
   `BTU_AI_Passport_Sheet_Template.xlsx` and open it with Google Sheets.
2. In Google Cloud Console: create a project, enable **Google Sheets API**, create a **service
   account**, and create a JSON key for it.
3. Share the spreadsheet with the service-account email (`…@….iam.gserviceaccount.com`) as **Editor**
   so the system can write the `sys_*` status columns.
4. Protect the grey `sys_*` columns for everyone except the service account (*Data → Protect ranges*).
5. In `.env`:

```bash
SHEETS_ADAPTER=google
GOOGLE_SPREADSHEET_ID=<the long id in the sheet URL>
GOOGLE_SERVICE_ACCOUNT_JSON_B64=<base64 of the JSON key>
#   PowerShell:  [Convert]::ToBase64String([IO.File]::ReadAllBytes("key.json"))
#   bash:        base64 -w0 key.json
```

6. `docker compose up -d` (restart web and worker). The next pass reads the sheet.

The adapter reads each tab with one API call, writes all status cells in one batch, and backs off on
HTTP 429/5xx. It never adds columns to the real sheet; missing `sys_*` columns are simply skipped.
