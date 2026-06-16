import pandas as pd
import sqlite3
import random
from datetime import date, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.series import DataPoint

random.seed(42)

DEPARTMENTS = ['Cardiology', 'Neurology', 'Orthopedics', 'General', 'Pediatrics', 'ICU', 'ENT']
DIAGNOSES = {
    'Cardiology':   ['Hypertension', 'Heart Failure', 'Angina', 'Arrhythmia'],
    'Neurology':    ['Stroke', 'Migraine', 'Epilepsy', 'Parkinson'],
    'Orthopedics':  ['Fracture', 'Knee Injury', 'Spine Disorder', 'Arthritis'],
    'General':      ['Typhoid', 'Diabetes', 'Asthma', 'Anemia'],
    'Pediatrics':   ['Dengue', 'Malaria', 'Pneumonia', 'Jaundice'],
    'ICU':          ['Sepsis', 'Respiratory Failure', 'Multi-organ Failure'],
    'ENT':          ['Sinusitis', 'Tonsillitis', 'Hearing Loss'],
}
STATUSES    = ['Admitted', 'Discharged', 'Critical', 'Observation']
GENDERS     = ['Male', 'Female']
BLOOD_GRPS  = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']
FIRST_NAMES = ['Ravi', 'Sunita', 'Mohan', 'Priya', 'Anjali', 'Venkat', 'Lakshmi',
               'Arun', 'Kavitha', 'Ramesh', 'Meena', 'Suresh', 'Deepa', 'Kiran',
               'Sridhar', 'Nandini', 'Prasad', 'Usha', 'Vijay', 'Rekha']
LAST_NAMES  = ['Kumar', 'Rao', 'Das', 'Sharma', 'Singh', 'Reddy', 'Devi',
               'Yadav', 'Nair', 'Babu', 'Kumari', 'Verma', 'Patel', 'Gupta']

def random_date(start_days_ago=365):
    return date.today() - timedelta(days=random.randint(0, start_days_ago))

def gen_patients(n=200):
    rows = []
    for i in range(1, n + 1):
        dept      = random.choice(DEPARTMENTS)
        gender    = random.choice(GENDERS)
        fname     = random.choice(FIRST_NAMES)
        lname     = random.choice(LAST_NAMES)
        admit     = random_date()
        stay      = random.randint(1, 20)
        discharge = admit + timedelta(days=stay) if random.random() > 0.3 else None
        rows.append({
            'patient_id':     f'P{i:04d}',
            'name':           f'{fname} {lname}',
            'age':            random.randint(2, 85),
            'gender':         gender,
            'blood_group':    random.choice(BLOOD_GRPS),
            'department':     dept,
            'diagnosis':      random.choice(DIAGNOSES[dept]),
            'admission_date': admit.isoformat(),
            'discharge_date': discharge.isoformat() if discharge else None,
            'stay_days':      stay,
            'status':         random.choice(STATUSES),
            'doctor':         f'Dr. {random.choice(LAST_NAMES)}',
            'bill_amount':    round(random.uniform(5000, 150000), 2),
        })
    return rows

# ── STEP 1: Generate patients ─────────────────────────────────────────────────
patients = gen_patients(200)
print(f"✅ Step 1: Total patients generated: {len(patients)}")

# ── STEP 2: Save to SQLite database ──────────────────────────────────────────
conn = sqlite3.connect('hospital.db')
cur  = conn.cursor()

cur.execute("DROP TABLE IF EXISTS patients")
cur.execute("""
    CREATE TABLE patients (
        patient_id      TEXT PRIMARY KEY,
        name            TEXT,
        age             INTEGER,
        gender          TEXT,
        blood_group     TEXT,
        department      TEXT,
        diagnosis       TEXT,
        admission_date  TEXT,
        discharge_date  TEXT,
        stay_days       INTEGER,
        status          TEXT,
        doctor          TEXT,
        bill_amount     REAL
    )
""")

cur.executemany("""
    INSERT INTO patients VALUES (
        :patient_id, :name, :age, :gender, :blood_group,
        :department, :diagnosis, :admission_date, :discharge_date,
        :stay_days, :status, :doctor, :bill_amount
    )
""", patients)

conn.commit()
conn.close()
print("✅ Step 2: Database saved: hospital.db")

# ── STEP 3: Analyze with pandas ───────────────────────────────────────────────
df = pd.DataFrame(patients)

print("\n========== DEPARTMENT SUMMARY ==========")
dept = df.groupby('department').agg(
    Total_Patients=('patient_id', 'count'),
    Avg_Bill=('bill_amount', 'mean'),
    Total_Bill=('bill_amount', 'sum')
).reset_index()
print(dept.to_string(index=False))

print("\n========== STATUS COUNT ==========")
print(df['status'].value_counts().to_string())

print("\n========== TOP DIAGNOSES ==========")
print(df['diagnosis'].value_counts().head(5).to_string())

print("✅ Step 3: Analysis complete!")

# ── STEP 4: Save to Excel ─────────────────────────────────────────────────────
df.to_excel('hospital_output.xlsx', index=False)
print("✅ Step 4: Excel saved: hospital_output.xlsx")

print("\n🎉 ALL DONE! Now run: python app.py")