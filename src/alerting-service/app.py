import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', 'YOUR_SLACK_WEBHOOK_URL_HERE')

def send_slack_notification(message):
    if SLACK_WEBHOOK_URL == 'YOUR_SLACK_WEBHOOK_URL_HERE' or not SLACK_WEBHOOK_URL:
        print("Slack webhook URL not configured. Skipping Slack notification.")
        return

    headers = {'Content-type': 'application/json'}
    payload = {'text': message}
    try:
        response = requests.post(SLACK_WEBHOOK_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        print(f"Slack notification sent: {message}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Slack notification: {e}")

@app.route('/alert', methods=['POST'])
def trigger_alert():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    incident_type = data.get('incident_type', 'Unknown Incident')
    sensor_id = data.get('sensor_id', 'N/A')
    value = data.get('value', 'N/A')
    severity = data.get('severity', 'critical').upper()
    runbook_link = data.get('runbook_link', '#')

    alert_message = f":rotating_light: *{severity} ALERT: {incident_type}* :rotating_light:\n"
    alert_message += f"> *Component:* `{sensor_id}`\n"
    alert_message += f"> *Value:* `{value}`\n"
    alert_message += f"> *Runbook:* <{runbook_link}|Click here for guidance>\n"
    alert_message += f"> *Timestamp:* {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"

    print(f"Received alert: {alert_message}")
    send_slack_notification(alert_message)

    return jsonify({"status": "success", "message": "Alert processed"}), 200

@app.route('/health', methods=['GET'])
def health_check():
    # For a simple alerting service, just being responsive is a health check.
    # More complex checks could involve testing connectivity to Slack API if credentials were provided.
    return jsonify({"status": "healthy", "message": "Alerting service is operational"}), 200

if __name__ == '__main__':
    import time
    app.run(host='0.0.0.0', port=os.getenv('PORT', 5003))
