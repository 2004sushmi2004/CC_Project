import json
import logging
import time
from kafka import KafkaConsumer
import psycopg2
from psycopg2 import sql, OperationalError
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LogConsumer:
    def __init__(self):  # Fixed: double underscores
        self.conn = None
        self.consumer = None
        self.max_retries = 5
        self.retry_delay = 5

    def create_db_connection(self):
        """Create PostgreSQL connection with retries"""
        for attempt in range(self.max_retries):
            try:
                conn = psycopg2.connect(
                    host="postgres",
                    database="logdb",
                    user="admin",
                    password="admin",
                    connect_timeout=5
                )
                logger.info("✅ Connected to PostgreSQL")
                return conn
            except OperationalError as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"❌ Failed to connect to PostgreSQL after {self.max_retries} attempts")
                    raise
                logger.warning(f"⚠ Connection attempt {attempt + 1} failed: {e}")
                time.sleep(self.retry_delay)

    def create_log_table(self):
        """Create optimized log table with error handling"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS api_logs (
            id BIGSERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ NOT NULL,
            endpoint TEXT NOT NULL,
            status_code INTEGER NOT NULL,
            response_time FLOAT,
            method VARCHAR(10),
            host TEXT,
            processed_at TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_timestamp ON api_logs USING BRIN(timestamp);
        CREATE INDEX IF NOT EXISTS idx_endpoint ON api_logs USING HASH(endpoint);
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(create_table_query)
                self.conn.commit()
                logger.info("✅ Created api_logs table and indexes")
        except Exception as e:
            logger.error(f"❌ Failed to create table: {e}")
            self.conn.rollback()
            raise

    def process_log(self, log):
        """Insert log with comprehensive error handling"""
        insert_query = """
        INSERT INTO api_logs 
            (timestamp, endpoint, status_code, response_time, method, host)
        VALUES 
            (%s, %s, %s, %s, %s, %s)
        """
        try:
            log_timestamp = datetime.fromisoformat(log['timestamp'])
            with self.conn.cursor() as cursor:
                cursor.execute(insert_query, (
                    log_timestamp,
                    log['endpoint'],
                    log['status_code'],
                    log.get('response_time'),
                    log.get('method'),
                    log.get('host')
                ))
                self.conn.commit()
            logger.info(f"📥 Inserted log from {log['endpoint']}")
        except KeyError as e:
            logger.error(f"❌ Missing required field in log: {e}")
            self.conn.rollback()
        except ValueError as e:
            logger.error(f"❌ Invalid timestamp format: {e}")
            self.conn.rollback()
        except Exception as e:
            logger.error(f"❌ Failed to insert log: {e}")
            self.conn.rollback()

    def start_consumer(self):
        """Start Kafka consumer with robust error handling"""
        try:
            self.conn = self.create_db_connection()
            self.create_log_table()

            self.consumer = KafkaConsumer(
                'api-logs',
                bootstrap_servers=['kafka:29092'],
                auto_offset_reset='earliest',
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                consumer_timeout_ms=10000,
                group_id='log-consumer-group'  # Added consumer group
            )

            logger.info("🚀 Consumer started. Waiting for logs...")
            while True:  # Continuous consumption loop
                try:
                    for message in self.consumer:
                        if message.value:
                            self.process_log(message.value)
                except Exception as e:
                    logger.error(f"⚠ Error processing message: {e}")
                    time.sleep(self.retry_delay)
                    continue

        except KeyboardInterrupt:
            logger.info("🛑 Graceful shutdown requested")
        except Exception as e:
            logger.error(f"🔥 Fatal consumer error: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        try:
            if self.conn and not self.conn.closed:
                self.conn.close()
                logger.info("🔌 Closed PostgreSQL connection")
        except Exception as e:
            logger.error(f"⚠ Error closing DB connection: {e}")

        try:
            if self.consumer:
                self.consumer.close()
                logger.info("🔌 Closed Kafka consumer")
        except Exception as e:
            logger.error(f"⚠ Error closing consumer: {e}")

if __name__ == "__main__":
    consumer = LogConsumer()
    consumer.start_consumer()