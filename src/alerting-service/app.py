import os
import json
import requests
import time
import threading
from datetime import datetime
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


# Alerting poller state
LAST_ALERT = None
LAST_ALERT_TS = 0.0


def poll_monitoring():
    global LAST_ALERT, LAST_ALERT_TS
    # Environment variables:
    # - MONITORING_STATUS_URL: URL to fetch monitoring status (default: Docker DNS on port 5000)
    # - POLL_INTERVAL_SECONDS: polling interval in seconds (default: 5)
    monitoring_url = os.getenv('MONITORING_STATUS_URL', os.getenv('MONITORING_URL', 'http://monitoring-service:5000/status'))
    interval = float(os.getenv('POLL_INTERVAL_SECONDS', 5))
    while True:
        checked_at = datetime.utcnow().isoformat() + 'Z'
        try:
            resp = requests.get(monitoring_url, timeout=5)
            if resp.status_code != 200:
                print(f"WARN monitoring_unreachable error=HTTP_{resp.status_code}")
                time.sleep(interval)
                continue

            data = resp.json()
            state = data.get('state')
            sensor_id = data.get('sensor_id')
            try:
                temp = float(data.get('temp_f'))
            except (TypeError, ValueError):
                temp = None

            if state == 'ALARM' and temp is not None:
                now = time.time()
                should_alert = False

                if LAST_ALERT is None:
                    should_alert = True
                else:
                    # re-alert if previous state not ALARM
                    if LAST_ALERT.get('state') != 'ALARM':
                        should_alert = True
                    # re-alert if temp changed by >= 1.0
                    elif abs(temp - float(LAST_ALERT.get('temp_f', temp))) >= 1.0:
                        should_alert = True
                    # re-alert if 60s passed since last alert
                    elif now - LAST_ALERT_TS >= 60:
                        should_alert = True

                if should_alert:
                    # Log alert line
                    print(f"ALERT state=ALARM temp_f={temp} sensor_id={sensor_id} checked_at={checked_at}")
                    LAST_ALERT = {
                        'service': 'alerting-service',
                        'state': 'ALARM',
                        'temp_f': temp,
                        'sensor_id': sensor_id,
                        'checked_at': checked_at,
                        'issued_at': datetime.utcnow().isoformat() + 'Z'
                    }
                    LAST_ALERT_TS = now

        except requests.exceptions.RequestException as e:
            print(f"WARN monitoring_unreachable error={e}")
        except Exception as e:
            print(f"WARN monitoring_unreachable error={e}")

        time.sleep(interval)


@app.route('/alerts/latest', methods=['GET'])
def get_latest_alert():
    if LAST_ALERT is None:
        return jsonify({'message': 'no alerts yet'}), 200
    return jsonify(LAST_ALERT), 200

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
    # Start background poller
    poller_thread = threading.Thread(target=poll_monitoring, daemon=True)
    poller_thread.start()

    app.run(host='0.0.0.0', port=os.getenv('PORT', 5003))
