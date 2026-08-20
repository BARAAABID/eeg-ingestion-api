from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3

app = FastAPI()

class EEGRecord(BaseModel):
    id: int
    eeg_data: float
    activity_category: str
    sampling_rate: int
    health_group: str
    activity_code: str

# Function to get the database connection
def get_db_connection():
    try:
        conn = sqlite3.connect("data_eeg.db")
        conn.row_factory = sqlite3.Row  # This allows accessing columns by name
        return conn
    except sqlite3.Error as e:
        print(e)
        raise HTTPException(status_code=500, detail="Database connection failed")

# Function to initialize the database and create the table
def initialize_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS eeg_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_eeg REAL,
        activity_category TEXT,
        sampling_rate INTEGER,
        health_group TEXT,
        activity_code TEXT
    )
    """)
    conn.commit()
    conn.close()

# Function to populate initial data
def populate_initial_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    initial_data = [
        (123.45, 'Stationary', 512, 'Healthy', '00'),
        (234.56, 'Light Ambulatory', 512, 'Epileptic', '01'),
        (345.67, 'Intense Ambulatory', 512, 'Healthy', '02'),
        (456.78, 'Stationary', 512, 'Epileptic', '00'),
        (567.89, 'Light Ambulatory', 512, 'Healthy', '01'),
        (678.90, 'Intense Ambulatory', 512, 'Epileptic', '02'),
        (789.01, 'Stationary', 512, 'Healthy', '00'),
        (890.12, 'Light Ambulatory', 512, 'Epileptic', '01'),
        (901.23, 'Intense Ambulatory', 512, 'Healthy', '02'),
        (101.34, 'Stationary', 512, 'Epileptic', '00')
    ]
    cursor.executemany("""
    INSERT INTO eeg_records (data_eeg, activity_category, sampling_rate, health_group, activity_code)
    VALUES (?, ?, ?, ?, ?)
    """, initial_data)
    conn.commit()
    conn.close()

# Function to clear all records (Delete all rows but keep the table structure)
def clear_all_records():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM eeg_records")  # This will delete all records
    conn.commit()
    conn.close()

# Function to drop the table (Delete the table and all its data)
def drop_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS eeg_records")  # This will delete the table
    conn.commit()
    conn.close()

# Function to fix existing records and assign ids if necessary
def fix_existing_records():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT rowid, * FROM eeg_records")
    records = cursor.fetchall()
    
    for record in records:
        if not record['id']:
            cursor.execute("UPDATE eeg_records SET id = ? WHERE rowid = ?", (record['rowid'], record['rowid']))
    
    conn.commit()
    conn.close()

# Initialize the database, populate data, and optionally clear or drop the table
initialize_db()
populate_initial_data()
fix_existing_records()

# Call the following functions as needed:
# clear_all_records()  # Clears all records
# drop_table()  # Drops the table

@app.get("/records", response_model=List[EEGRecord])
async def get_records():
    conn = get_db_connection()
    records = conn.execute("SELECT * FROM eeg_records").fetchall()
    conn.close()
    # Convert the rows to dictionaries
    return [{"id": record["id"], "eeg_data": record["data_eeg"], "activity_category": record["activity_category"],
             "sampling_rate": record["sampling_rate"], "health_group": record["health_group"],
             "activity_code": record["activity_code"]} for record in records]

@app.get("/records/{record_id}", response_model=EEGRecord)
async def get_record(record_id: int):
    conn = get_db_connection()
    record = conn.execute("SELECT * FROM eeg_records WHERE id = ?", (record_id,)).fetchone()
    conn.close()
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"id": record["id"], "eeg_data": record["data_eeg"], "activity_category": record["activity_category"],
            "sampling_rate": record["sampling_rate"], "health_group": record["health_group"],
            "activity_code": record["activity_code"]}

@app.post("/records", response_model=EEGRecord)
async def create_record(record: EEGRecord):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO eeg_records (data_eeg, activity_category, sampling_rate, health_group, activity_code)
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
        SET data_eeg = ?, activity_category = ?, sampling_rate = ?, health_group = ?, activity_code = ?
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
