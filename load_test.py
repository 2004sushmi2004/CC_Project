import requests
import threading
import random
import time

endpoints = [
    '/',
    '/users',
    '/products',
    '/orders',
    '/health',
    '/slow'
]

base_url = "http://localhost:5000"

def make_request():
    while True:
        endpoint = random.choice(endpoints)
        try:
            response = requests.get(f"{base_url}{endpoint}")
            print(f"Request to {endpoint} - Status: {response.status_code}")
        except Exception as e:
            print(f"Request failed: {e}")
        
        time.sleep(random.uniform(0.05, 0.2))

if __name__ == "__main__":
    threads = []
    
    # Start 10 worker threads
    for i in range(10):
        thread = threading.Thread(target=make_request)
        thread.daemon = True
        thread.start()
        threads.append(thread)
    
    # Run for 5 minutes
    time.sleep(300)
