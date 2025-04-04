from kafka import KafkaProducer
import requests
import time
import random
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_kafka_producer():
    """Create and return a Kafka producer with proper connection testing"""
    for attempt in range(5):
        try:
            producer = KafkaProducer(
                bootstrap_servers=['kafka:29092'],
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                api_version=(2, 8, 1),
                retry_backoff_ms=5000,
                request_timeout_ms=30000
            )
            
            # Test connection with a proper JSON message instead of raw bytes
            test_msg = {"test": "connection_check", "timestamp": datetime.now().isoformat()}
            future = producer.send('connection-test', value=test_msg)
            future.get(timeout=10)
            logger.info("✅ Successfully connected to Kafka")
            return producer
            
        except Exception as e:
            logger.warning(f"⚠️ Connection attempt {attempt + 1} failed: {str(e)}")
            if attempt == 4:
                raise
            time.sleep(5)
    return None

def generate_log(endpoint, status_code, response_time):
    return {
        "timestamp": datetime.now().isoformat(),
        "endpoint": endpoint,
        "status_code": status_code,
        "response_time": response_time,
        "method": "GET",
        "host": "api-server"
    }

def make_request(url):
    start_time = time.time()
    try:
        response = requests.get(url, timeout=5)
        elapsed_time = time.time() - start_time
        return response.status_code, elapsed_time
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Request failed: {str(e)}")
        return 500, elapsed_time

def simulate_traffic():
    base_url = "http://api-server:5000"
    endpoints = ['/', '/users', '/products', '/orders', '/health', '/slow']
    
    producer = create_kafka_producer()
    if not producer:
        logger.error("Failed to create Kafka producer after retries")
        return

    while True:
        try:
            endpoint = random.choice(endpoints)
            url = f"{base_url}{endpoint}"
            
            status_code, response_time = make_request(url)
            log_entry = generate_log(endpoint, status_code, response_time)
            
            # Send the properly formatted JSON message
            future = producer.send('api-logs', value=log_entry)
            future.get(timeout=10)
            
            logger.info(f"📤 Sent log: {log_entry}")
            time.sleep(random.uniform(0.1, 1.0))
            
        except KeyboardInterrupt:
            logger.info("Shutting down producer...")
            producer.close()
            break
        except Exception as e:
            logger.error(f"Error in traffic simulation: {str(e)}")
            time.sleep(5)

if __name__ == "__main__":
    simulate_traffic()