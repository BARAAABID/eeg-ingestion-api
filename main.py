import json
from enum import Enum
from typing import List

import aiosqlite
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

DB_PATH = "data_eeg.db"


# ---------- Enums (Fix 5): restrict free-text fields to known valid values ----------
class HealthGroup(str, Enum):
    healthy = "Healthy"
    epileptic = "Epileptic"


class ActivityCategory(str, Enum):
    stationary = "Stationary"
    light_ambulatory = "Light Ambulatory"
    intense_ambulatory = "Intense Ambulatory"


# ---------- Models (Fix 2 + Fix 3) ----------
# EEGRecordCreate: what a client sends in on POST - no id, since the DB assigns it.
# eeg_samples is a list of raw signal values (Fix 3), not a single summary float.
class EEGRecordCreate(BaseModel):
    eeg_samples: List[float]       # e.g. 512 values = 1 second of signal at 512Hz
    sampling_rate: int
    activity_category: ActivityCategory
    health_group: HealthGroup
    activity_code: str


# EEGRecord: what the API returns - inherits everything above, adds the DB-assigned id.
class EEGRecord(EEGRecordCreate):
    id: int


# ---------- Dependency (Fix 4): connection lifecycle managed by FastAPI, not by hand ----------
async def get_db():
    # ADD TIMEOUT HERE
    db = await aiosqlite.connect(DB_PATH, timeout=10.0)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


# ---------- Setup (Fix 1 continued): async startup, since aiosqlite calls must be awaited ----------
async def initialize_db():
    conn = await aiosqlite.connect(DB_PATH)
    
    # ENABLE WAL MODE HERE
    await conn.execute("PRAGMA journal_mode=WAL;")
    
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS eeg_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        eeg_samples TEXT,
        activity_category TEXT,
        sampling_rate INTEGER,
        health_group TEXT,
        activity_code TEXT
    )
    """)
    await conn.commit()
    await conn.close()

async def populate_initial_data():
    conn = await aiosqlite.connect(DB_PATH)
    # only seed if the table is empty, so restarting the app doesn't keep re-inserting rows
    cursor = await conn.execute("SELECT COUNT(*) FROM eeg_records")
    (count,) = await cursor.fetchone()
    if count == 0:
        initial_data = [
            (json.dumps([123.45] * 512), ActivityCategory.stationary, 512, HealthGroup.healthy, "00"),
            (json.dumps([234.56] * 512), ActivityCategory.light_ambulatory, 512, HealthGroup.epileptic, "01"),
            (json.dumps([345.67] * 512), ActivityCategory.intense_ambulatory, 512, HealthGroup.healthy, "02"),
        ]
        await conn.executemany("""
        INSERT INTO eeg_records (eeg_samples, activity_category, sampling_rate, health_group, activity_code)
        VALUES (?, ?, ?, ?, ?)
        """, initial_data)
        await conn.commit()
    await conn.close()


@app.on_event("startup")
async def startup():
    await initialize_db()
    await populate_initial_data()


# ---------- Endpoints ----------
def row_to_record(row) -> dict:
    """Shared helper: decode the JSON-stored samples back into a list for every read."""
    return {
        "id": row["id"],
        "eeg_samples": json.loads(row["eeg_samples"]),
        "activity_category": row["activity_category"],
        "sampling_rate": row["sampling_rate"],
        "health_group": row["health_group"],
        "activity_code": row["activity_code"],
    }


@app.get("/records", response_model=List[EEGRecord])
async def get_records(skip: int = 0, limit: int = 9, db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute("SELECT * FROM eeg_records LIMIT ? OFFSET ?", (limit, skip))
    rows = await cursor.fetchall()
    return [row_to_record(r) for r in rows]


@app.get("/records/{record_id}", response_model=EEGRecord)
async def get_record(record_id: int, db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute("SELECT * FROM eeg_records WHERE id = ?", (record_id,))
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return row_to_record(row)


@app.post("/records", response_model=EEGRecord)
async def create_record(record: EEGRecordCreate, db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute("""
        INSERT INTO eeg_records (eeg_samples, activity_category, sampling_rate, health_group, activity_code)
        VALUES (?, ?, ?, ?, ?)
    """, (json.dumps(record.eeg_samples), record.activity_category, record.sampling_rate,
          record.health_group, record.activity_code))
    await db.commit()
    new_id = cursor.lastrowid
    return {**record.dict(), "id": new_id}


@app.put("/records/{record_id}", response_model=EEGRecord)
async def update_record(record_id: int, updated: EEGRecordCreate, db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute("SELECT id FROM eeg_records WHERE id = ?", (record_id,))
    if await cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="Record not found")

    await db.execute("""
        UPDATE eeg_records
        SET eeg_samples = ?, activity_category = ?, sampling_rate = ?, health_group = ?, activity_code = ?
        WHERE id = ?
    """, (json.dumps(updated.eeg_samples), updated.activity_category, updated.sampling_rate,
          updated.health_group, updated.activity_code, record_id))
    await db.commit()
    return {**updated.dict(), "id": record_id}


@app.delete("/records/{record_id}")
async def delete_record(record_id: int, db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute("SELECT id FROM eeg_records WHERE id = ?", (record_id,))
    if await cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="Record not found")

    await db.execute("DELETE FROM eeg_records WHERE id = ?", (record_id,))
    await db.commit()
    return {"detail": "Record deleted successfully"}