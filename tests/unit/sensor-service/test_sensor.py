import pytest
import json
from unittest.mock import patch, MagicMock
from src.sensor-service.app import app, publish_message, generate_data, health_check

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch('src.sensor-service.app.pika.BlockingConnection')
@patch('src.sensor-service.app.time.sleep', return_value=None)
def test_publish_message_success(mock_sleep, mock_connection):
    mock_channel = MagicMock()
    mock_connection.return_value.channel.return_value = mock_channel

    message = {'test': 'data'}
    publish_message(message)

    mock_connection.assert_called_once()
    mock_channel.queue_declare.assert_called_once_with(queue='sensor_data', durable=True)
    mock_channel.basic_publish.assert_called_once()
    mock_connection.return_value.close.assert_called_once()

@patch('src.sensor-service.app.pika.BlockingConnection', side_effect=pika.exceptions.AMQPConnectionError)
@patch('src.sensor-service.app.time.sleep', return_value=None)
def test_publish_message_connection_error(mock_sleep, mock_connection):
    message = {'test': 'data'}
    # The function has a retry mechanism, so we call it once and expect an error print and sleep
    publish_message(message)
    mock_sleep.assert_called_once_with(5)

@patch('src.sensor-service.app.publish_message')
@patch('src.sensor-service.app.random.uniform', return_value=70.0)
@patch('src.sensor-service.app.random.randint', return_value=1)
@patch('src.sensor-service.app.time.time', return_value=1678886400)
def test_generate_data_endpoint(mock_time, mock_randint, mock_uniform, mock_publish_message, client):
    response = client.post('/generate_data')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'data' in data
    assert data['data']['sensor_id'] == 'sensor-1'
    assert data['data']['temperature'] == 70.0
    assert data['data']['timestamp'] == 1678886400
    mock_publish_message.assert_called_once_with({
        'sensor_id': 'sensor-1',
        'temperature': 70.0,
        'timestamp': 1678886400,
        'status': 'normal'
    })

@patch('src.sensor-service.app.pika.BlockingConnection')
def test_health_check_healthy(mock_connection, client):
    mock_connection.return_value.close.return_value = None
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'operational' in data['message']

@patch('src.sensor-service.app.pika.BlockingConnection', side_effect=pika.exceptions.AMQPConnectionError)
def test_health_check_unhealthy(mock_connection, client):
    response = client.get('/health')
    assert response.status_code == 500
    data = json.loads(response.data)
    assert data['status'] == 'unhealthy'
    assert 'cannot connect' in data['message']
