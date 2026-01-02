import pytest
import json
import os
import requests
import importlib.util
from pathlib import Path
from unittest.mock import patch, MagicMock

# If Flask isn't installed locally, skip these tests to be friendly for devs
try:
    import flask  # noqa: F401
except ModuleNotFoundError:
    pytest.skip("flask not installed", allow_module_level=True)

# Load alerting module from file path because the package folder uses a hyphen
spec = importlib.util.spec_from_file_location(
    "alerting_app",
    str(Path(__file__).resolve().parents[3] / 'src' / 'alerting-service' / 'app.py')
)
alerting_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alerting_app)

# Re-export symbols expected by tests
app = alerting_app.app
send_slack_notification = alerting_app.send_slack_notification
trigger_alert = alerting_app.trigger_alert

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch.object(alerting_app, 'requests')
def test_send_slack_notification_success(mock_requests):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_requests.post.return_value = mock_response

    with patch.dict(os.environ, {'SLACK_WEBHOOK_URL': 'http://mock-slack-webhook.com'}):
        send_slack_notification("Test message")

    mock_requests.post.assert_called_once_with(
        'http://mock-slack-webhook.com',
        headers={'Content-type': 'application/json'},
        data=json.dumps({'text': 'Test message'})
    )

@patch.object(alerting_app.requests, 'post', side_effect=requests.exceptions.RequestException('Network error'))
def test_send_slack_notification_failure(mock_post, capsys):
    with patch.dict(os.environ, {'SLACK_WEBHOOK_URL': 'http://mock-slack-webhook.com'}):
        send_slack_notification("Test message")

    captured = capsys.readouterr()
    assert "Error sending Slack notification" in captured.out

@patch.object(alerting_app, 'send_slack_notification')
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
