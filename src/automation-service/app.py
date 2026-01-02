import os
import json
import time
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

SENSOR_SERVICE_HOST = os.getenv('SENSOR_SERVICE_HOST', 'localhost')
SENSOR_SERVICE_PORT = int(os.getenv('SENSOR_SERVICE_PORT', 5000))

@app.route('/remediate', methods=['POST'])
def remediate_incident():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    incident_type = data.get('incident_type')
    sensor_id = data.get('sensor_id')
    value = data.get('value')

    print(f"Received remediation request for {incident_type} on {sensor_id} with value {value}")

    if incident_type == 'High Temperature':
        print(f"Simulating applying cooling logic for {sensor_id}...")
        # In a real system, this would send a command to a thermostat controller
        # For this lab, we'll just log it and assume it helps.
        time.sleep(2) # Simulate work
        print(f"Cooling logic applied for {sensor_id}.")
        return jsonify({"status": "success", "action": "cooling_applied", "details": f"Simulated cooling for {sensor_id}"}), 200

    elif incident_type == 'Sensor Silent' or incident_type == 'Erratic Sensor Data':
        print(f"Attempting to restart sensor service for {sensor_id}...")
        # In a real system, this would trigger a deployment or restart of the specific sensor microservice instance
        # For this lab, we'll simulate a restart by calling a dummy endpoint or just logging.
        try:
            # This is a placeholder. A real restart would be handled by Kubernetes/ECS or a dedicated control plane.
            # For demonstration, we'll just log the action.
            print(f"Simulated restart of sensor service for {sensor_id}.")
            time.sleep(3) # Simulate restart time
            # Optionally, trigger sensor to send data again to verify
            # requests.post(f"http://{SENSOR_SERVICE_HOST}:{SENSOR_SERVICE_PORT}/generate_data", json={'sensor_id': sensor_id, 'force_generate': True})
            return jsonify({"status": "success", "action": "sensor_service_restarted", "details": f"Simulated restart for {sensor_id}"}), 200
        except requests.exceptions.RequestException as e:
            print(f"Failed to simulate sensor service restart: {e}")
            return jsonify({"status": "failed", "action": "sensor_service_restart_failed", "error": str(e)}), 500

    else:
        print(f"No automated remediation defined for incident type: {incident_type}")
        return jsonify({"status": "ignored", "message": "No automated remediation defined for this type"}), 200

@app.route('/health', methods=['GET'])
def health_check():
    # Basic health check
    return jsonify({"status": "healthy", "message": "Automation service is operational"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv('PORT', 5004))
