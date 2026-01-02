import os
import time
import json
import random
from datetime import datetime
import pika
from flask import Flask, jsonify

app = Flask(__name__)

MESSAGE_QUEUE_HOST = os.getenv('MESSAGE_QUEUE_HOST', 'localhost')
MESSAGE_QUEUE_PORT = int(os.getenv('MESSAGE_QUEUE_PORT', 5672))
QUEUE_NAME = 'sensor_data'

def publish_message(message):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=MESSAGE_QUEUE_HOST, port=MESSAGE_QUEUE_PORT))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            )
        )
        print(f" [x] Sent '{message}'")
        connection.close()
    except pika.exceptions.AMQPConnectionError as e:
        print(f" [!] Failed to connect to RabbitMQ: {e}. Retrying...")
        time.sleep(5) # Wait before retrying
        # In a real application, you'd want a more robust retry mechanism or circuit breaker

@app.route('/generate_data', methods=['POST'])
def generate_data():
    sensor_id = f"sensor-{random.randint(1, 3)}"
    temperature = round(random.uniform(68.0, 75.0), 2) # Normal range
    timestamp = int(time.time())

    data = {
        'sensor_id': sensor_id,
        'temperature': temperature,
        'timestamp': timestamp,
        'status': 'normal'
    }
    publish_message(data)
    return jsonify({"status": "success", "message": "Data generated and published", "data": data}), 200

@app.route('/health', methods=['GET'])
def health_check():
    # Basic health check: try to connect to RabbitMQ
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=MESSAGE_QUEUE_HOST, port=MESSAGE_QUEUE_PORT, heartbeat=0))
        connection.close()
        return jsonify({"status": "healthy", "message": "Sensor service is operational and connected to message queue"}), 200
    except pika.exceptions.AMQPConnectionError:
        return jsonify({"status": "unhealthy", "message": "Sensor service cannot connect to message queue"}), 500


@app.route('/reading', methods=['GET'])
def get_reading():
    temp = round(random.uniform(68.0, 75.0), 2)
    data = {
        'sensor_id': 'sensor-1',
        'temp_f': temp,
        'status': 'OK',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    return jsonify(data), 200

if __name__ == '__main__':
    # Simulate continuous data generation in a separate thread/process for local testing
    # In a production microservice, this would likely be a scheduled task or triggered externally.
    import threading
    def continuous_generation():
        while True:
            with app.app_context():
                generate_data()
            time.sleep(random.uniform(1, 3)) # Generate data every 1-3 seconds

    threading.Thread(target=continuous_generation, daemon=True).start()

    app.run(host='0.0.0.0', port=os.getenv('PORT', 5000))
