import json
from unittest.mock import patch
from src.sensor-service.app import app


def test_reading_endpoint(client=None):
    app.config['TESTING'] = True
    with app.test_client() as client:
        with patch('src.sensor-service.app.random.uniform', return_value=72.5):
            response = client.get('/reading')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['sensor_id'] == 'sensor-1'
            assert isinstance(data['temp_f'], float)
            assert data['status'] == 'OK'
            assert 'timestamp' in data
