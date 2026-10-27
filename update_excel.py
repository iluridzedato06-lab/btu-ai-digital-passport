import pandas as pd

file_path = 'data/showcase/BTU AI Skills Digital Passport Hackathon_Test Data 2.xlsx'

# Load the excel file starting at header row 3
df = pd.read_excel(file_path, header=3)

# Update emails to firstname.lastname@btu.edu.ge
df['BTU Email (Test)'] = (
    df['First Name'].str.strip().str.lower() + '.' +
    df['Last Name'].str.strip().str.lower() + '@btu.edu.ge'
)

# Save back to file
df.to_excel(file_path, sheet_name='Passport Skill Records', index=False)
print("Successfully updated all 60 Excel emails!")