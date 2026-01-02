import pytest
import json
from unittest.mock import patch, MagicMock
from src.monitoring-service.app import app, process_sensor_data, monitor_sensor_silence, health_check, sensor_readings, last_seen_timestamps

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def reset_state():
    # Reset in-memory state before each test
    sensor_readings.clear()
    last_seen_timestamps.clear()
    app.config.clear()
    yield

@patch('src.monitoring-service.app.log_incident')
@patch('src.monitoring-service.app.trigger_alert')
@patch('src.monitoring-service.app.trigger_automation')
@patch('src.monitoring-service.app.time.time', return_value=1000)
def test_process_sensor_data_normal(mock_time, mock_automation, mock_alert, mock_log):
    ch = MagicMock()
    method = MagicMock()
    properties = MagicMock()
    body = json.dumps({'sensor_id': 'sensor-1', 'temperature': 70.0, 'timestamp': 1000})

    process_sensor_data(ch, method, properties, body)

    ch.basic_ack.assert_called_once_with(delivery_tag=method.delivery_tag)
    mock_log.assert_not_called()
    mock_alert.assert_not_called()
    mock_automation.assert_not_called()
    assert last_seen_timestamps['sensor-1'] == 1000
    assert sensor_readings['sensor-1'][0]['temp'] == 70.0

@patch('src.monitoring-service.app.log_incident')
@patch('src.monitoring-service.app.trigger_alert')
@patch('src.monitoring-service.app.trigger_automation')
@patch('src.monitoring-service.app.time.time')
def test_process_sensor_data_high_temp_fault(mock_time, mock_automation, mock_alert, mock_log):
    ch = MagicMock()
    method = MagicMock()
    properties = MagicMock()

    sensor_id = 'sensor-1'
    high_temp_threshold = app.config.get('HIGH_TEMP_THRESHOLD', 80.0)
    high_temp_duration = app.config.get('HIGH_TEMP_DURATION_SECONDS', 300)

    # Simulate data over time to trigger high temp fault
    current_timestamp = 1000
    mock_time.return_value = current_timestamp
    body_initial = json.dumps({'sensor_id': sensor_id, 'temperature': high_temp_threshold + 1, 'timestamp': current_timestamp})
    process_sensor_data(ch, method, properties, body_initial)
    mock_log.assert_not_called()

    # Advance time past duration threshold
    current_timestamp += high_temp_duration + 1
    mock_time.return_value = current_timestamp
    body_final = json.dumps({'sensor_id': sensor_id, 'temperature': high_temp_threshold + 1, 'timestamp': current_timestamp})
    process_sensor_data(ch, method, properties, body_final)

    mock_log.assert_called_once_with('High Temperature', sensor_id, high_temp_threshold + 1, details={'threshold': high_temp_threshold})
    mock_alert.assert_called_once_with('High Temperature', sensor_id, high_temp_threshold + 1, runbook_link='/docs/runbooks/high-temp-alarm.md')
    mock_automation.assert_called_once_with('High Temperature', sensor_id, high_temp_threshold + 1)

@patch('src.monitoring-service.app.log_incident')
@patch('src.monitoring-service.app.trigger_alert')
@patch('src.monitoring-service.app.trigger_automation')
@patch('src.monitoring-service.app.time.time')
def test_process_sensor_data_erratic_fault(mock_time, mock_automation, mock_alert, mock_log):
    ch = MagicMock()
    method = MagicMock()
    properties = MagicMock()

    sensor_id = 'sensor-2'
    erratic_change_threshold = app.config.get('ERRATIC_CHANGE_THRESHOLD', 10.0)
    erratic_window_seconds = app.config.get('ERRATIC_WINDOW_SECONDS', 10)

    # Simulate initial reading
    mock_time.return_value = 1000
    body_initial = json.dumps({'sensor_id': sensor_id, 'temperature': 70.0, 'timestamp': 1000})
    process_sensor_data(ch, method, properties, body_initial)

    # Simulate erratic reading within window
    mock_time.return_value = 1000 + erratic_window_seconds - 1 # Still within window
    body_erratic = json.dumps({'sensor_id': sensor_id, 'temperature': 70.0 + erratic_change_threshold + 1, 'timestamp': 1000 + erratic_window_seconds - 1})
    process_sensor_data(ch, method, properties, body_erratic)

    mock_log.assert_called_once_with('Erratic Sensor Data', sensor_id, 70.0 + erratic_change_threshold + 1, details={'temp_diff': erratic_change_threshold + 1, 'window_seconds': erratic_window_seconds})
    mock_alert.assert_called_once_with('Erratic Sensor Data', sensor_id, 70.0 + erratic_change_threshold + 1)
    mock_automation.assert_called_once_with('Erratic Sensor Data', sensor_id, 70.0 + erratic_change_threshold + 1)

@patch('src.monitoring-service.app.log_incident')
@patch('src.monitoring-service.app.trigger_alert')
@patch('src.monitoring-service.app.trigger_automation')
@patch('src.monitoring-service.app.time.time')
@patch('src.monitoring-service.app.time.sleep', return_value=None)
def test_monitor_sensor_silence_fault(mock_sleep, mock_time, mock_automation, mock_alert, mock_log):
    sensor_id = 'sensor-3'
    silence_threshold = app.config.get('SENSOR_SILENCE_THRESHOLD_SECONDS', 120)

    # Simulate a sensor reporting data
    initial_time = 1000
    last_seen_timestamps[sensor_id] = initial_time

    # Advance time past silence threshold
    mock_time.return_value = initial_time + silence_threshold + 1

    # Run the monitor once
    monitor_sensor_silence()

    mock_log.assert_called_once_with('Sensor Silent', sensor_id, 'N/A', details={'last_seen': initial_time})
    mock_alert.assert_called_once_with('Sensor Silent', sensor_id, 'N/A', runbook_link='/docs/runbooks/sensor-silent-alarm.md')
    mock_automation.assert_called_once_with('Sensor Silent', sensor_id, 'N/A')
    assert sensor_id not in last_seen_timestamps # Should be removed after alerting

@patch('src.monitoring-service.app.pika.BlockingConnection')
@patch('src.monitoring-service.app.requests.get')
def test_health_check_healthy(mock_requests_get, mock_pika_connection, client):
    mock_pika_connection.return_value.close.return_value = None
    mock_requests_get.return_value.raise_for_status.return_value = None

    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'operational' in data['message']

@patch('src.monitoring-service.app.pika.BlockingConnection', side_effect=pika.exceptions.AMQPConnectionError)
@patch('src.monitoring-service.app.requests.get')
def test_health_check_unhealthy_rabbitmq(mock_requests_get, mock_pika_connection, client):
    response = client.get('/health')
    assert response.status_code == 500
    data = json.loads(response.data)
    assert data['status'] == 'unhealthy'
    assert 'RabbitMQ' in data['message']

@patch('src.monitoring-service.app.pika.BlockingConnection')
@patch('src.monitoring-service.app.requests.get', side_effect=requests.exceptions.RequestException)
def test_health_check_unhealthy_dependency(mock_requests_get, mock_pika_connection, client):
    mock_pika_connection.return_value.close.return_value = None
    response = client.get('/health')
    assert response.status_code == 500
    data = json.loads(response.data)
    assert data['status'] == 'unhealthy'
    assert 'dependency issue' in data['message']
