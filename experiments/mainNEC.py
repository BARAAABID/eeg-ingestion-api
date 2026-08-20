from typing import List
from pydantic import BaseModel
import sqlite3
from fastapi import FastAPI, HTTPException

app = FastAPI()

# Define the EEGRecord model with the necessary fields
class EEGRecord(BaseModel):
    af3: float
    f7: float
    f3: float
    fc5: float
    t7: float
    p7: float
    fc6: float
    f4: float
    f8: float
    o1: float
    o2: float
    p8: float
    t8: float
    af4: float
    eye_state: int  # 1 for eyes open, 0 for eyes closed

# Database connection function
def get_db_connection():
    try:
        conn = sqlite3.connect("eeg_data.db")
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(e)
        raise HTTPException(status_code=500, detail="Database connection failed")

# Initialize the database
def initialize_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Drop the table if it already exists to ensure schema matches code
    cursor.execute("DROP TABLE IF EXISTS eeg_records")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS eeg_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        af3 REAL,
        f7 REAL,
        f3 REAL,
        fc5 REAL,
        t7 REAL,
        p7 REAL,
        fc6 REAL,
        f4 REAL,
        f8 REAL,
        o1 REAL,
        o2 REAL,
        p8 REAL,
        t8 REAL,
        af4 REAL,
        eye_state INTEGER
    )
    """)
    conn.commit()
    conn.close()

# Function to populate initial data with ten records
def populate_initial_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    initial_data = [
        (0.12, -0.25, 0.33, 0.45, -0.50, 0.61, -0.72, 0.83, -0.94, 1.05, -1.16, 1.27, -1.38, 1.49, 1),
        (1.21, 0.22, -0.33, 0.44, -0.55, 0.66, -0.77, 0.88, -0.99, 1.10, -1.21, 1.32, -1.43, 1.54, 0),
        (-0.11, 0.23, -0.34, 0.45, 0.56, -0.67, 0.78, -0.89, 1.00, -1.11, 1.22, -1.33, 1.44, -1.55, 1),
        (1.14, -0.25, 0.36, 0.47, -0.58, 0.69, -0.80, 0.91, -1.02, 1.13, -1.24, 1.35, -1.46, 1.57, 0),
        (0.13, 0.26, -0.39, 0.41, -0.53, 0.64, -0.75, 0.86, -0.97, 1.08, -1.19, 1.30, -1.41, 1.52, 1),
        (-0.34, 0.12, -0.45, 0.56, 0.67, -0.78, 0.89, -1.00, 1.11, -1.22, 1.33, -1.44, 1.55, -1.66, 0),
        (0.24, -0.35, 0.46, -0.57, 0.68, -0.79, 0.80, -0.91, 1.02, -1.13, 1.24, -1.35, 1.46, -1.57, 1),
        (0.14, 0.25, -0.36, 0.47, -0.58, 0.69, -0.80, 0.91, -1.02, 1.13, -1.24, 1.35, -1.46, 1.57, 0),
        (-0.45, 0.35, -0.55, 0.65, 0.75, -0.85, 0.95, -1.05, 1.15, -1.25, 1.35, -1.45, 1.55, -1.65, 1),
        (0.56, -0.12, 0.67, -0.78, 0.89, -0.90, 1.01, -1.12, 1.23, -1.34, 1.45, -1.56, 1.67, -1.78, 0)
    ]
    cursor.executemany("""
    INSERT INTO eeg_records (af3, f7, f3, fc5, t7, p7, fc6, f4, f8, o1, o2, p8, t8, af4, eye_state)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, initial_data)
    conn.commit()
    conn.close()

# Initialize the database and populate data on app start
initialize_db()
populate_initial_data()

# API endpoints remain the same
# Create (C) - Add a new EEG record
@app.post("/records", response_model=EEGRecord)
async def create_record(record: EEGRecord):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO eeg_records (af3, f7, f3, fc5, t7, p7, fc6, f4, f8, o1, o2, p8, t8, af4, eye_state)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record.af3, record.f7, record.f3, record.fc5, record.t7,
        record.p7, record.fc6, record.f4, record.f8, record.o1,
        record.o2, record.p8, record.t8, record.af4, record.eye_state
    ))
    conn.commit()
    new_record_id = cursor.lastrowid
    conn.close()
    return {**record.dict(), "id": new_record_id}

# Read (R) - Get all EEG records
@app.get("/records", response_model=List[EEGRecord])
async def get_records():
    conn = get_db_connection()
    records = conn.execute("SELECT * FROM eeg_records").fetchall()
    conn.close()
    return [dict(record) for record in records]

# Read (R) - Get a single EEG record by ID
@app.get("/records/{record_id}", response_model=EEGRecord)
async def get_record(record_id: int):
    conn = get_db_connection()
    record = conn.execute("SELECT * FROM eeg_records WHERE id = ?", (record_id,)).fetchone()
    conn.close()
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return dict(record)

# Update (U) - Update an existing EEG record by ID
@app.put("/records/{record_id}", response_model=EEGRecord)
async def update_record(record_id: int, updated_record: EEGRecord):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE eeg_records
        SET af3 = ?, f7 = ?, f3 = ?, fc5 = ?, t7 = ?, p7 = ?, fc6 = ?, f4 = ?, f8 = ?, o1 = ?, o2 = ?, p8 = ?, t8 = ?, af4 = ?, eye_state = ?
        WHERE id = ?
    """, (
        updated_record.af3, updated_record.f7, updated_record.f3, updated_record.fc5,
        updated_record.t7, updated_record.p7, updated_record.fc6, updated_record.f4,
        updated_record.f8, updated_record.o1, updated_record.o2, updated_record.p8,
        updated_record.t8, updated_record.af4, updated_record.eye_state, record_id
    ))
    conn.commit()
    conn.close()
    return updated_record

# Delete (D) - Delete a specific EEG record by ID
@app.delete("/records/{record_id}")
async def delete_record(record_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM eeg_records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    return {"detail": "Record deleted successfully"}
