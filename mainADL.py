from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3
import os

app = FastAPI()

class EEGRecord(BaseModel):
    id: int = None  # Allow id to be optional for creation
    eeg_data: float
    activity_category: str
    sampling_rate: int
    health_group: str
    activity_code: str

def get_db_connection():
    try:
        conn = sqlite3.connect("eeg_data.db")
        conn.row_factory = sqlite3.Row  # Allows row access as dictionaries
        return conn
    except sqlite3.Error as e:
        print(e)
        raise HTTPException(status_code=500, detail="Database connection failed")

def initialize_db():
    if not os.path.exists("eeg_data.db"):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS eeg_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eeg_data REAL,
            activity_category TEXT,
            sampling_rate INTEGER,
            health_group TEXT,
            activity_code TEXT
        )
        """)
        conn.commit()
        conn.close()

def populate_initial_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    initial_data = [
        (123.45, 'Stationary', 512, 'Healthy', '00'),
        # Additional sample data as needed
    ]
    cursor.executemany("""
    INSERT INTO eeg_records (eeg_data, activity_category, sampling_rate, health_group, activity_code)
    VALUES (?, ?, ?, ?, ?)
    """, initial_data)
    conn.commit()
    conn.close()

# Initialize database only if it does not exist
initialize_db()
populate_initial_data()

@app.get("/records", response_model=List[EEGRecord])
async def get_records():
    conn = get_db_connection()
    records = conn.execute("SELECT * FROM eeg_records").fetchall()
    conn.close()
    return [dict(record) for record in records]

@app.get("/records/{record_id}", response_model=EEGRecord)
async def get_record(record_id: int):
    conn = get_db_connection()
    record = conn.execute("SELECT * FROM eeg_records WHERE id = ?", (record_id,)).fetchone()
    conn.close()
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return dict(record)

@app.post("/records", response_model=EEGRecord)
async def create_record(record: EEGRecord):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO eeg_records (eeg_data, activity_category, sampling_rate, health_group, activity_code)
        VALUES (?, ?, ?, ?, ?)
    """, (record.eeg_data, record.activity_category, record.sampling_rate, record.health_group, record.activity_code))
    conn.commit()
    new_record_id = cursor.lastrowid
    conn.close()
    return {**record.dict(), "id": new_record_id}

@app.put("/records/{record_id}", response_model=EEGRecord)
async def update_record(record_id: int, updated_record: EEGRecord):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE eeg_records
        SET eeg_data = ?, activity_category = ?, sampling_rate = ?, health_group = ?, activity_code = ?
        WHERE id = ?
    """, (updated_record.eeg_data, updated_record.activity_category, updated_record.sampling_rate,
          updated_record.health_group, updated_record.activity_code, record_id))
    conn.commit()
    conn.close()
    return updated_record

@app.delete("/records/{record_id}")
async def delete_record(record_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM eeg_records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    return {"detail": "Record deleted successfully"}
