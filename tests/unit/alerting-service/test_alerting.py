import pytest
import json
from unittest.mock import patch, MagicMock
from src.alerting-service.app import app, send_slack_notification, trigger_alert

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch('src.alerting-service.app.requests.post')
def test_send_slack_notification_success(mock_post):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    with patch.dict(os.environ, {'SLACK_WEBHOOK_URL': 'http://mock-slack-webhook.com'}):
        send_slack_notification("Test message")

    mock_post.assert_called_once_with(
        'http://mock-slack-webhook.com',
        headers={'Content-type': 'application/json'},
        data=json.dumps({'text': 'Test message'})
    )

@patch('src.alerting-service.app.requests.post', side_effect=requests.exceptions.RequestException('Network error'))
def test_send_slack_notification_failure(mock_post, capsys):
    with patch.dict(os.environ, {'SLACK_WEBHOOK_URL': 'http://mock-slack-webhook.com'}):
        send_slack_notification("Test message")

    captured = capsys.readouterr()
    assert "Error sending Slack notification" in captured.out

@patch('src.alerting-service.app.send_slack_notification')
def test_trigger_alert_endpoint_success(mock_send_slack_notification, client):
    alert_data = {
        'incident_type': 'High Temperature',
        'sensor_id': 'sensor-1',
        'value': '85.5',
        'severity': 'critical',
        'runbook_link': '/docs/runbooks/high-temp-alarm.md'
    }
    response = client.post('/alert', json=alert_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'Alert processed' in data['message']

    expected_message_part = "*CRITICAL ALERT: High Temperature*"
    mock_send_slack_notification.assert_called_once()
    call_args = mock_send_slack_notification.call_args[0][0]
    assert expected_message_part in call_args
    assert "Component: `sensor-1`" in call_args
    assert "Value: `85.5`" in call_args
    assert "Runbook: </docs/runbooks/high-temp-alarm.md|Click here for guidance>" in call_args

def test_trigger_alert_endpoint_invalid_json(client):
    response = client.post('/alert', data='not json', content_type='text/plain')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == 'Invalid JSON'

def test_health_check_healthy(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'operational' in data['message']
