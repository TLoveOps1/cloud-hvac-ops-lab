import pytest
import json
from unittest.mock import patch, MagicMock
from src.automation-service.app import app, remediate_incident, health_check

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch('src.automation-service.app.time.sleep', return_value=None)
def test_remediate_high_temperature(mock_sleep, client):
    incident_data = {
        'incident_type': 'High Temperature',
        'sensor_id': 'sensor-1',
        'value': '85.0'
    }
    response = client.post('/remediate', json=incident_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['action'] == 'cooling_applied'
    mock_sleep.assert_called_once_with(2)

@patch('src.automation-service.app.time.sleep', return_value=None)
@patch('src.automation-service.app.requests.post') # Mock requests.post if it were called for sensor restart
def test_remediate_sensor_silent(mock_requests_post, mock_sleep, client):
    incident_data = {
        'incident_type': 'Sensor Silent',
        'sensor_id': 'sensor-2',
        'value': 'N/A'
    }
    response = client.post('/remediate', json=incident_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['action'] == 'sensor_service_restarted'
    mock_sleep.assert_called_once_with(3)
    # mock_requests_post.assert_called_once() # Uncomment if you add a real API call for sensor restart

@patch('src.automation-service.app.time.sleep', return_value=None)
@patch('src.automation-service.app.requests.post')
def test_remediate_erratic_sensor_data(mock_requests_post, mock_sleep, client):
    incident_data = {
        'incident_type': 'Erratic Sensor Data',
        'sensor_id': 'sensor-3',
        'value': '70.0 -> 90.0'
    }
    response = client.post('/remediate', json=incident_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['action'] == 'sensor_service_restarted'
    mock_sleep.assert_called_once_with(3)

def test_remediate_unknown_incident_type(client):
    incident_data = {
        'incident_type': 'Unknown Fault',
        'sensor_id': 'sensor-4',
        'value': '100'
    }
    response = client.post('/remediate', json=incident_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ignored'
    assert 'No automated remediation defined' in data['message']

def test_remediate_invalid_json(client):
    response = client.post('/remediate', data='not json', content_type='text/plain')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == 'Invalid JSON'

def test_health_check_healthy(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'operational' in data['message']
