import asyncio
import time
import httpx

URL = "http://127.0.0.1:8000/records"
TOTAL_REQUESTS = 512
CONCURRENCY_LIMIT = 50  # The Semaphore limit to prevent socket exhaustion

# Initialize the Semaphore
sem = asyncio.Semaphore(CONCURRENCY_LIMIT)

async def send_eeg_pulse(client, index):
    async with sem:  # Only 50 requests can enter this block at the same time
        payload = {
            "eeg_samples": [100.0 + index, 101.0 + index, 102.0 + index],
            "activity_category": "Stationary",
            "sampling_rate": 512,
            "health_group": "Healthy",
            "activity_code": "99"
        }
        try:
            # Added a generous timeout just in case the DB queue gets long
            response = await client.post(URL, json=payload, timeout=10.0)
            if response.status_code != 200:
                print(f"Failed Request {index}: {response.text}")
            return response.status_code
        except Exception as e:
            print(f"Exception on Request {index}: {str(e)}")
            return str(e)

async def main():
    print(f"Starting {TOTAL_REQUESTS}Hz Concurrency Load Test with Semaphore...")
    print("-" * 45)
    
    # We use a single client session for connection pooling
    async with httpx.AsyncClient() as client:
        start_time = time.time()
        
        # Build and fire the tasks
        tasks = [send_eeg_pulse(client, i) for i in range(TOTAL_REQUESTS)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        
    execution_time = end_time - start_time
    successful = [r for r in results if r == 200]
    
    print(f"Total Execution Time:  {execution_time:.3f} seconds")
    print(f"Requests Per Second:   {TOTAL_REQUESTS / execution_time:.2f} RPS")
    print(f"Successful Inserts:    {len(successful)} / {TOTAL_REQUESTS}")
    print(f"Failed/Locked Inserts: {TOTAL_REQUESTS - len(successful)}")

if __name__ == "__main__":
    # Required for Windows to handle async socket loops cleanly
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())