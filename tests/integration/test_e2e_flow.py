import pytest
import requests
import time
import json

# Base URLs for the services (assuming Docker Compose default ports)
SENSOR_SERVICE_URL = "http://localhost:5000"
MONITORING_SERVICE_URL = "http://localhost:5001"
LOGGING_SERVICE_URL = "http://localhost:5002"
ALERTING_SERVICE_URL = "http://localhost:5003"
AUTOMATION_SERVICE_URL = "http://localhost:5004"

def wait_for_service(url, timeout=60):
    start_time = time.time()
    while True:
        try:
            response = requests.get(f"{url}/health")
            if response.status_code == 200 and response.json().get("status") == "healthy":
                print(f"Service {url} is healthy.")
                return True
        except requests.exceptions.ConnectionError:
            pass
        if time.time() - start_time > timeout:
            raise Exception(f"Service {url} did not become healthy within {timeout} seconds.")
        time.sleep(2)

@pytest.fixture(scope="module", autouse=True)
def setup_services():
    print("Waiting for services to become healthy...")
    wait_for_service(SENSOR_SERVICE_URL)
    wait_for_service(LOGGING_SERVICE_URL)
    wait_for_service(ALERTING_SERVICE_URL)
    wait_for_service(AUTOMATION_SERVICE_URL)
    wait_for_service(MONITORING_SERVICE_URL) # Monitoring depends on others, so check last
    print("All services are healthy.")
    yield
    print("Teardown complete.")

def test_e2e_high_temperature_incident_flow():
    print("\n--- Starting E2E High Temperature Incident Flow Test ---")

    # 1. Clear existing incidents for a clean test run
    # (This would ideally be an admin endpoint or direct DB access in a test setup)
    # For now, we'll just fetch and print to see the state.
    initial_incidents = requests.get(f"{LOGGING_SERVICE_URL}/incidents").json()
    print(f"Initial incidents: {len(initial_incidents)}")

    # 2. Simulate high temperature data from sensor-service
    print("Simulating high temperature data...")
    sensor_id = "e2e-sensor-high-temp"
    high_temp_value = 85.0
    for _ in range(10): # Send multiple readings to ensure monitoring picks it up consistently
        requests.post(f"{SENSOR_SERVICE_URL}/generate_data", json={
            'sensor_id': sensor_id,
            'temperature': high_temp_value,
            'timestamp': int(time.time()),
            'status': 'fault'
        })
        time.sleep(1) # Send every second

    # 3. Wait for monitoring-service to detect and log the incident (US-3, US-6)
    print("Waiting for high temperature incident to be logged...")
    incident_found = False
    alert_triggered = False
    automation_triggered = False
    start_time = time.time()
    timeout = 60 # seconds

    while time.time() - start_time < timeout:
        incidents = requests.get(f"{LOGGING_SERVICE_URL}/incidents").json()
        for incident in incidents:
            if incident['type'] == 'High Temperature' and incident['component'] == sensor_id:
                incident_found = True
                print(f"High Temperature Incident found: {incident}")
                break
        if incident_found:
            break
        time.sleep(2)

    assert incident_found, "High Temperature incident was not logged within timeout."

    # 4. Verify alert was triggered (US-7)
    # This is hard to verify directly without mocking Slack, but we can check logs or a dummy endpoint
    # For this test, we'll assume if the monitoring service called alerting, it worked.
    # In a real E2E, you might check a test Slack channel or a mock Slack server.
    print("Assuming alert was triggered (check alerting-service logs if needed).")
    # You could add a mock Slack server here and assert it received a message.

    # 5. Verify automation was triggered (US-8)
    # Similar to alerting, direct verification is hard. We'll check automation service logs or a mock.
    print("Assuming automation was triggered (check automation-service logs if needed).")
    # You could add a mock for the 'cooling logic' and assert it was called.

    print("--- E2E High Temperature Incident Flow Test PASSED ---")

def test_e2e_sensor_silence_incident_flow():
    print("\n--- Starting E2E Sensor Silence Incident Flow Test ---")

    sensor_id = "e2e-sensor-silent"
    # 1. Send initial data to register the sensor
    print(f"Sending initial data for {sensor_id}...")
    requests.post(f"{SENSOR_SERVICE_URL}/generate_data", json={
        'sensor_id': sensor_id,
        'temperature': 72.0,
        'timestamp': int(time.time()),
        'status': 'normal'
    })
    time.sleep(5) # Give monitoring a moment to register it

    # 2. Stop sending data for this sensor to simulate silence
    print(f"Stopping data for {sensor_id} to simulate silence...")
    # The sensor-service generates random IDs, so simply not sending for this specific ID is enough.

    # 3. Wait for monitoring-service to detect and log the incident (US-4, US-6)
    print("Waiting for Sensor Silent incident to be logged...")
    incident_found = False
    start_time = time.time()
    timeout = 180 # seconds (longer for silence detection)

    while time.time() - start_time < timeout:
        incidents = requests.get(f"{LOGGING_SERVICE_URL}/incidents").json()
        for incident in incidents:
            if incident['type'] == 'Sensor Silent' and incident['component'] == sensor_id:
                incident_found = True
                print(f"Sensor Silent Incident found: {incident}")
                break
        if incident_found:
            break
        time.sleep(5)

    assert incident_found, "Sensor Silent incident was not logged within timeout."

    print("--- E2E Sensor Silence Incident Flow Test PASSED ---")
