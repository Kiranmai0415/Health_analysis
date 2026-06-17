import os

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database path
DB_PATH = os.path.join(BASE_DIR, "hospital.db")
EXCEL_PATH = os.path.join(BASE_DIR, "hospital_output.xlsx")

print(f"Database will be created/read from: {DB_PATH}")