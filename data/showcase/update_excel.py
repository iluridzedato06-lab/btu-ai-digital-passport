import openpyxl

file_path = 'data/showcase/BTU AI Skills Digital Passport Hackathon_Test Data 2.xlsx'

# Load workbook
wb = openpyxl.load_workbook(file_path)
ws = wb.active

# Find columns dynamically from header row
first_col, last_col, email_col = None, None, None

for row in ws.iter_rows(values_only=False):
    row_vals = [str(cell.value).strip() if cell.value else '' for cell in row]
    if 'First Name' in row_vals and 'Last Name' in row_vals:
        first_col = row_vals.index('First Name')
        last_col = row_vals.index('Last Name')
        # Look for BTU Email or Email column
        for idx, val in enumerate(row_vals):
            if 'Email' in val:
                email_col = idx
                break
        continue
    
    # Update email for data rows
    if first_col is not None and row[first_col].value and row[last_col].value:
        fn = str(row[first_col].value).strip().lower()
        ln = str(row[last_col].value).strip().lower()
        if fn and ln and fn != 'first name':
            row[email_col].value = f"{fn}.{ln}@btu.edu.ge"

wb.save(file_path)
print("SUCCESS: Updated Excel emails successfully!")