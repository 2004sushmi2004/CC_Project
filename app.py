from flask import Flask, jsonify
import random
import time
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "ok", "message": "Welcome to Log Analytics API"})

@app.route('/users')
def get_users():
    # Simulate some processing time
    time.sleep(random.uniform(0.1, 0.5))
    return jsonify({"users": ["Alice", "Bob", "Charlie"]})

@app.route('/products')
def get_products():
    time.sleep(random.uniform(0.2, 0.8))
    return jsonify({"products": ["Laptop", "Phone", "Tablet"]})

@app.route('/orders')
def get_orders():
    time.sleep(random.uniform(0.3, 1.0))
    if random.random() < 0.1:  # 10% chance of error
        return jsonify({"error": "Database timeout"}), 500
    return jsonify({"orders": [{"id": 1, "item": "Laptop"}, {"id": 2, "item": "Phone"}]})

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/slow')
def slow_endpoint():
    time.sleep(2 + random.random())
    return jsonify({"message": "This was a slow request"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
