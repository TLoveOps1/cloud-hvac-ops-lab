import pytest
import json
from unittest.mock import patch, MagicMock
from src.logging-service.app import app, db, Incident

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # Use in-memory SQLite for testing
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

def test_create_incident_success(client):
    incident_data = {
        'type': 'High Temperature',
        'component': 'sensor-1',
        'value': '85.5',
        'severity': 'critical',
        'details': {'threshold': 80.0}
    }
    response = client.post('/incidents', json=incident_data)
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['type'] == 'High Temperature'
    assert data['component'] == 'sensor-1'
    assert data['status'] == 'active'
    assert Incident.query.count() == 1

def test_create_incident_invalid_json(client):
    response = client.post('/incidents', data='not json', content_type='text/plain')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == 'Invalid JSON'

def test_get_incidents_empty(client):
    response = client.get('/incidents')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 0

def test_get_incidents_with_data(client):
    incident1 = Incident(timestamp=1, type='High Temp', component='s1', value='85', severity='critical')
    incident2 = Incident(timestamp=2, type='Sensor Silent', component='s2', value='N/A', severity='warning')
    with app.app_context():
        db.session.add(incident1)
        db.session.add(incident2)
        db.session.commit()

    response = client.get('/incidents')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[0]['type'] == 'High Temp'
    assert data[1]['type'] == 'Sensor Silent'

def test_get_single_incident(client):
    incident = Incident(timestamp=1, type='High Temp', component='s1', value='85', severity='critical')
    with app.app_context():
        db.session.add(incident)
        db.session.commit()
        incident_id = incident.id

    response = client.get(f'/incidents/{incident_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == incident_id
    assert data['type'] == 'High Temp'

def test_get_single_incident_not_found(client):
    response = client.get('/incidents/999')
    assert response.status_code == 404

def test_update_incident_status(client):
    incident = Incident(timestamp=1, type='High Temp', component='s1', value='85', severity='critical')
    with app.app_context():
        db.session.add(incident)
        db.session.commit()
        incident_id = incident.id

    update_data = {'status': 'resolved', 'details': {'resolution_notes': 'Cooling applied'}}
    response = client.put(f'/incidents/{incident_id}', json=update_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == incident_id
    assert data['status'] == 'resolved'
    assert data['details']['resolution_notes'] == 'Cooling applied'

    with app.app_context():
        updated_incident = Incident.query.get(incident_id)
        assert updated_incident.status == 'resolved'
        assert updated_incident.details['resolution_notes'] == 'Cooling applied'

def test_health_check_healthy(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'operational' in data['message']

@patch('src.logging-service.app.db.session.execute', side_effect=Exception('DB Error'))
def test_health_check_unhealthy(mock_execute, client):
    response = client.get('/health')
    assert response.status_code == 500
    data = json.loads(response.data)
    assert data['status'] == 'unhealthy'
    assert 'DB connection failed' in data['message']
