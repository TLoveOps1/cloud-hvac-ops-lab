import os
import json
import time
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/hvac_logs')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Incident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(100), nullable=False)
    component = db.Column(db.String(100), nullable=False)
    value = db.Column(db.String(100), nullable=True)
    severity = db.Column(db.String(50), nullable=False)
    details = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(50), default='active') # active, resolved, manual_intervention

    def __repr__(self):
        return f"<Incident {self.id} - {self.type} on {self.component}>"

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp,
            'type': self.type,
            'component': self.component,
            'value': self.value,
            'severity': self.severity,
            'details': self.details,
            'status': self.status
        }

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/incidents', methods=['POST'])
def create_incident():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    new_incident = Incident(
        timestamp=data.get('timestamp', int(time.time())),
        type=data['type'],
        component=data['component'],
        value=data.get('value'),
        severity=data.get('severity', 'critical'),
        details=data.get('details', {})
    )
    db.session.add(new_incident)
    db.session.commit()
    print(f"Incident created: {new_incident.to_dict()}")
    return jsonify(new_incident.to_dict()), 201

@app.route('/incidents', methods=['GET'])
def get_incidents():
    incidents = Incident.query.all()
    return jsonify([incident.to_dict() for incident in incidents]), 200

@app.route('/incidents/<int:incident_id>', methods=['GET'])
def get_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    return jsonify(incident.to_dict()), 200

@app.route('/incidents/<int:incident_id>', methods=['PUT'])
def update_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    data = request.get_json()

    if 'status' in data: incident.status = data['status']
    if 'severity' in data: incident.severity = data['severity']
    if 'details' in data: incident.details = {**incident.details, **data['details']}

    db.session.commit()
    print(f"Incident {incident_id} updated: {incident.to_dict()}")
    return jsonify(incident.to_dict()), 200

@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Try to connect to the database
        db.session.execute(db.text('SELECT 1'))
        return jsonify({"status": "healthy", "message": "Logging service is operational and connected to DB"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "message": f"Logging service DB connection failed: {e}"}), 500

if __name__ == '__main__':
    with app.app_context():
        create_tables()
    app.run(host='0.0.0.0', port=os.getenv('PORT', 5002))
