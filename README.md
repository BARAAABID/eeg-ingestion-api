# 🧠 High-Concurrency EEG Ingestion API

![Python](https://img.shields.io/badge/Python-3.13-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Production-009688.svg)
![SQLite](https://img.shields.io/badge/SQLite-WAL_Mode-003B57.svg)

An asynchronous, high-frequency data ingestion backend built for telemedic EEG devices. This API is designed to process and store continuous 512Hz biological sensor data streams with zero packet loss under heavy concurrent load.

## 🏗️ System Architecture & Optimizations

To resolve severe OS-level socket exhaustion and database locking bottlenecks, the pipeline was optimized at both the network and I/O layers:

* **Asynchronous Connection Pooling:** Transitioned to `aiosqlite` to maintain a non-blocking event loop while waiting for disk I/O.
* **Database Concurrency (WAL):** Overrode default SQLite lock-based writing with Write-Ahead Logging (`PRAGMA journal_mode=WAL`), enabling simultaneous read/write operations.
* **Network Layer Throttling:** Implemented `asyncio.Semaphore` to bound concurrent inbound connections to pools of 50, preventing TCP socket exhaustion and stabilizing throughput.
* **Strict Data Validation:** Utilized Pydantic and Enums to instantly drop malformed payloads at the routing layer, protecting database compute resources.

## 📊 Stress Test Performance

*Load testing performed using `asyncio` and `httpx` to simulate 512 simultaneous sensor streams.*

* **Total Payload:** 512 Requests
* **Concurrency Limit:** 50 (Semaphore)
* **Execution Time:** ~4.69 Seconds
* **Throughput:** ~109.10 Requests/Sec
* **Success Rate:** 100.0% (0 Dropped Sockets, 0 DB Locks)

<img width="1480" height="607" alt="Screenshot 2026-08-15 141352" src="https://github.com/user-attachments/assets/112e8215-5846-41e1-a8dd-ec6acabfe628" />

## 🚀 Getting Started

**1. Clone the repository and install dependencies:**
```bash
git clone [https://github.com/BARAAABID/eeg-ingestion-api.git](https://github.com/BARAAABID/eeg-ingestion-api.git)
cd eeg-ingestion-api
pip install fastapi uvicorn aiosqlite pytest httpx