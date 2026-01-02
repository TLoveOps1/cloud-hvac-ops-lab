import os
import json
import time
import threading
import pika
import requests
from datetime import datetime
from flask import Flask, jsonify, request

app = Flask(__name__)

MESSAGE_QUEUE_HOST = os.getenv('MESSAGE_QUEUE_HOST', 'localhost')
MESSAGE_QUEUE_PORT = int(os.getenv('MESSAGE_QUEUE_PORT', 5672))
SENSOR_QUEUE_NAME = 'sensor_data'

LOGGING_SERVICE_HOST = os.getenv('LOGGING_SERVICE_HOST', 'localhost')
LOGGING_SERVICE_PORT = int(os.getenv('LOGGING_SERVICE_PORT', 5002))

ALERTING_SERVICE_HOST = os.getenv('ALERTING_SERVICE_HOST', 'localhost')
ALERTING_SERVICE_PORT = int(os.getenv('ALERTING_SERVICE_PORT', 5003))

AUTOMATION_SERVICE_HOST = os.getenv('AUTOMATION_SERVICE_HOST', 'localhost')
AUTOMATION_SERVICE_PORT = int(os.getenv('AUTOMATION_SERVICE_PORT', 5004))

# In-memory store for sensor data and last seen timestamps
sensor_readings = {}
last_seen_timestamps = {}

# Fault thresholds
HIGH_TEMP_THRESHOLD = 80.0
HIGH_TEMP_DURATION_SECONDS = 5 * 60 # 5 minutes
SENSOR_SILENCE_THRESHOLD_SECONDS = 2 * 60 # 2 minutes
ERRATIC_CHANGE_THRESHOLD = 10.0 # >10F change in 10 seconds
ERRATIC_WINDOW_SECONDS = 10

def log_incident(incident_type, sensor_id, value, severity='critical', details=None):
    incident_data = {
        'timestamp': int(time.time()),
        'type': incident_type,
        'component': sensor_id,
        'value': value,
        'severity': severity,
        'details': details or {}
    }
    try:
        response = requests.post(f"http://{LOGGING_SERVICE_HOST}:{LOGGING_SERVICE_PORT}/incidents", json=incident_data)
        response.raise_for_status()
        print(f"Incident logged: {incident_data}")
    except requests.exceptions.RequestException as e:
        print(f"Error logging incident: {e}")

def trigger_alert(incident_type, sensor_id, value, severity='critical', runbook_link=None):
    alert_data = {
        'incident_type': incident_type,
        'sensor_id': sensor_id,
        'value': value,
        'severity': severity,
        'runbook_link': runbook_link
    }
    try:
        response = requests.post(f"http://{ALERTING_SERVICE_HOST}:{ALERTING_SERVICE_PORT}/alert", json=alert_data)
        response.raise_for_status()
        print(f"Alert triggered: {alert_data}")
    except requests.exceptions.RequestException as e:
        print(f"Error triggering alert: {e}")

def trigger_automation(incident_type, sensor_id, value):
    automation_data = {
        'incident_type': incident_type,
        'sensor_id': sensor_id,
        'value': value
    }
    try:
        response = requests.post(f"http://{AUTOMATION_SERVICE_HOST}:{AUTOMATION_SERVICE_PORT}/remediate", json=automation_data)
        response.raise_for_status()
        print(f"Automation triggered: {automation_data}")
    except requests.exceptions.RequestException as e:
        print(f"Error triggering automation: {e}")

def process_sensor_data(ch, method, properties, body):
    try:
        data = json.loads(body)
        sensor_id = data['sensor_id']
        temperature = data['temperature']
        timestamp = data['timestamp']

        print(f"Received data: {data}")

        # Update last seen timestamp
        last_seen_timestamps[sensor_id] = timestamp

        # Store readings for erratic detection
        if sensor_id not in sensor_readings:
            sensor_readings[sensor_id] = []
        sensor_readings[sensor_id].append({'temp': temperature, 'timestamp': timestamp})
        # Keep only recent readings for erratic detection
        sensor_readings[sensor_id] = [r for r in sensor_readings[sensor_id] if r['timestamp'] > timestamp - ERRATIC_WINDOW_SECONDS]

        # --- Detection Logic ---

        # 1. High Temperature Fault Detection (US-3)
        if temperature > HIGH_TEMP_THRESHOLD:
            # Check if it's consistently high for a duration
            # This is a simplified check; a real system would track duration more robustly
            if sensor_id not in app.config:
                app.config[sensor_id] = {'high_temp_start': None}

            if app.config[sensor_id]['high_temp_start'] is None:
                app.config[sensor_id]['high_temp_start'] = timestamp
            elif timestamp - app.config[sensor_id]['high_temp_start'] >= HIGH_TEMP_DURATION_SECONDS:
                log_incident('High Temperature', sensor_id, temperature, details={'threshold': HIGH_TEMP_THRESHOLD})
                trigger_alert('High Temperature', sensor_id, temperature, runbook_link='/docs/runbooks/high-temp-alarm.md')
                trigger_automation('High Temperature', sensor_id, temperature)
                app.config[sensor_id]['high_temp_start'] = None # Reset after triggering
        else:
            if sensor_id in app.config and app.config[sensor_id]['high_temp_start'] is not None:
                print(f"High temperature for {sensor_id} resolved before threshold.")
                app.config[sensor_id]['high_temp_start'] = None

        # 2. Erratic Data Fault Detection (US-5)
        if len(sensor_readings[sensor_id]) >= 2:
            first_reading = sensor_readings[sensor_id][0]
            last_reading = sensor_readings[sensor_id][-1]
            if last_reading['timestamp'] - first_reading['timestamp'] > 0:
                temp_diff = abs(last_reading['temp'] - first_reading['temp'])
                if temp_diff > ERRATIC_CHANGE_THRESHOLD:
                    log_incident('Erratic Sensor Data', sensor_id, temperature, details={'temp_diff': temp_diff, 'window_seconds': ERRATIC_WINDOW_SECONDS})
                    trigger_alert('Erratic Sensor Data', sensor_id, temperature)
                    trigger_automation('Erratic Sensor Data', sensor_id, temperature)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError:
        print(f" [!] Invalid JSON received: {body}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        print(f" [!] Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def monitor_sensor_silence():
    while True:
        current_time = int(time.time())
        for sensor_id, last_seen in list(last_seen_timestamps.items()):
            if current_time - last_seen > SENSOR_SILENCE_THRESHOLD_SECONDS:
                print(f"Sensor {sensor_id} has been silent for {current_time - last_seen} seconds.")
                log_incident('Sensor Silent', sensor_id, 'N/A', details={'last_seen': last_seen})
                trigger_alert('Sensor Silent', sensor_id, 'N/A', runbook_link='/docs/runbooks/sensor-silent-alarm.md')
                trigger_automation('Sensor Silent', sensor_id, 'N/A')
                del last_seen_timestamps[sensor_id] # Remove to avoid repeated alerts for the same silence
        time.sleep(30) # Check every 30 seconds

def start_monitoring_consumer():
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=MESSAGE_QUEUE_HOST, port=MESSAGE_QUEUE_PORT))
            channel = connection.channel()
            channel.queue_declare(queue=SENSOR_QUEUE_NAME, durable=True)
            channel.basic_consume(queue=SENSOR_QUEUE_NAME, on_message_callback=process_sensor_data)

            print(' [*] Monitoring service waiting for messages. To exit press CTRL+C')
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError as e:
            print(f" [!] Monitoring service failed to connect to RabbitMQ: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f" [!] An unexpected error occurred in consumer: {e}. Restarting consumer in 5 seconds...")
            time.sleep(5)

@app.route('/health', methods=['GET'])
def health_check():
    # Check connectivity to RabbitMQ and dependent services
    try:
        pika.BlockingConnection(pika.ConnectionParameters(host=MESSAGE_QUEUE_HOST, port=MESSAGE_QUEUE_PORT, heartbeat=0)).close()
        requests.get(f"http://{LOGGING_SERVICE_HOST}:{LOGGING_SERVICE_PORT}/health").raise_for_status()
        requests.get(f"http://{ALERTING_SERVICE_HOST}:{ALERTING_SERVICE_PORT}/health").raise_for_status()
        requests.get(f"http://{AUTOMATION_SERVICE_HOST}:{AUTOMATION_SERVICE_PORT}/health").raise_for_status()
        return jsonify({"status": "healthy", "message": "Monitoring service operational and connected to dependencies"}), 200
    except (pika.exceptions.AMQPConnectionError, requests.exceptions.RequestException) as e:
        return jsonify({"status": "unhealthy", "message": f"Monitoring service dependency issue: {e}"}), 500


@app.route('/status', methods=['GET'])
def status_check():
    sensor_url = 'http://sensor-service:5000/reading'
    checked_at = datetime.utcnow().isoformat() + 'Z'
    try:
        resp = requests.get(sensor_url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        temp = float(data.get('temp_f'))
        sensor_id = data.get('sensor_id')

        # Determine state
        if 68.0 <= temp <= 75.0:
            state = 'OK'
        elif (65.0 <= temp < 68.0) or (75.0 < temp <= 78.0):
            state = 'WARN'
        else:
            state = 'ALARM'

        return jsonify({
            'service': 'monitoring-service',
            'sensor_url': sensor_url,
            'sensor_id': sensor_id,
            'temp_f': temp,
            'state': state,
            'checked_at': checked_at
        }), 200
    except requests.exceptions.RequestException as e:
        return jsonify({'service': 'monitoring-service', 'state': 'UNKNOWN', 'error': str(e), 'checked_at': checked_at}), 503
    except (ValueError, KeyError) as e:
        return jsonify({'service': 'monitoring-service', 'state': 'UNKNOWN', 'error': f'Invalid sensor response: {e}', 'checked_at': checked_at}), 503

if __name__ == '__main__':
    # Start consumer in a separate thread
    consumer_thread = threading.Thread(target=start_monitoring_consumer, daemon=True)
    consumer_thread.start()

    # Start sensor silence monitor in a separate thread
    silence_monitor_thread = threading.Thread(target=monitor_sensor_silence, daemon=True)
    silence_monitor_thread.start()

    app.run(host='0.0.0.0', port=os.getenv('PORT', 5001))
