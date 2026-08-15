from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_records():
    response = client.get("/records?skip=0&limit=5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_record():
    payload = {
        "id": 0,
        "eeg_samples": [405.12, 406.23, 407.34],  # <-- Now it is a valid list
        "activity_category": "Stationary",
        "sampling_rate": 512,
        "health_group": "Healthy",
        "activity_code": "00"
    }
    response = client.post("/records", json=payload)
    
    assert response.status_code == 200, f"Validation Error: {response.text}"
    
    data = response.json()
    assert data["eeg_samples"] == [405.12, 406.23, 407.34]  # <-- Check against the list
    assert "id" in data

def test_read_nonexistent_record():
    response = client.get("/records/999999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Record not found"}